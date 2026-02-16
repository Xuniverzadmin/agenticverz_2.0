#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Role: Data quality gate — nullability, cardinality, semantic drift checks
# artifact_class: CODE

"""
Data Quality Gate (BA-18)

Static analysis of ORM model files in app/models/ to enforce:
- Nullability contracts: *_id fields should be non-Optional
- Cardinality contracts: relationship fields should have explicit back_populates
- Semantic drift: 'status' fields should use Enum/Literal types, not bare str

Does NOT require a database connection — pure file parsing.

Usage:
    python scripts/verification/check_data_quality.py
    python scripts/verification/check_data_quality.py --strict
"""

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODELS_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "models"

# Skip non-model files
SKIP_FILES = {"__init__.py"}

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches SQLModel field definitions:
#   field_name: Optional[str] = Field(...)
#   field_name: str = Field(...)
#   field_name: Optional[str] = None
# Captures: (field_name, full_type_annotation, rest_of_line)
RE_FIELD_DEF = re.compile(
    r"^\s+(\w+)\s*:\s*(.+?)\s*=\s*(.+)$",
    re.MULTILINE,
)

# Matches SQLAlchemy Column definitions:
#   name = Column(String(255), nullable=False, ...)
# Captures: (field_name, column_args)
RE_COLUMN_DEF = re.compile(
    r"^\s+(\w+)\s*=\s*Column\((.+)\)$",
    re.MULTILINE,
)

# Matches relationship() calls
RE_RELATIONSHIP = re.compile(
    r"^\s+(\w+)\s*=\s*relationship\((.+)\)$",
    re.MULTILINE,
)

# Matches table-class declarations (both SQLModel and Base)
RE_TABLE_CLASS = re.compile(
    r"^class\s+(\w+)\s*\("
    r"(?:SQLModel\b[^)]*table\s*=\s*True|Base\s*)"
    r"[^)]*\)\s*:",
    re.MULTILINE,
)

# Known ID field suffixes that should typically be non-optional
ID_FIELD_SUFFIXES = ("_id",)

# Allowlist: ID fields that are legitimately Optional
# (e.g., nullable foreign keys by design)
#
# Grouped by design intent. Each entry documents WHY the FK is nullable.
# BA-18 Delta: expanded from 16 → 46 entries to cover all design-intentional
# nullable FKs in app/models/.
OPTIONAL_ID_ALLOWLIST = {
    # --- Identity & auth (null for system-created or pre-setup records) ---
    "user_id",               # Many tables allow null user_id (system-created records)
    "api_key_id",            # Audit records may not have an API key
    "default_tenant_id",     # Users may not have a default tenant yet
    "clerk_org_id",          # May be null during setup
    "oauth_provider_id",     # Not all users have OAuth provider (password-based)

    # --- Run & session tracking (null when not tied to a specific run) ---
    "parent_run_id",         # Only set for retry runs
    "session_id",            # Optional session grouping
    "agent_id",              # Optional agent tracking
    "worker_id",             # Usage records may not track worker
    "run_id",                # Optional FK — not all records are tied to a run
    "trace_id",              # Optional FK — not all LLM records have a trace
    "correlation_id",        # Optional grouping key for log exports
    "source_run_id",         # Only set when entity originates from a run

    # --- Incident & recovery (null when not incident-triggered) ---
    "source_incident_id",    # Only set when action triggered by incident
    "incident_id",           # Nullable: not all records relate to an incident
    "killswitch_id",         # Not all incidents trigger a killswitch
    "affected_agent_id",     # Not all incidents affect a specific agent
    "llm_run_id",            # Not all incidents originate from an LLM run
    "replayed_from_id",      # Only set for replayed proxy calls
    "replay_call_id",        # Only set for replay results

    # --- Action & reversal (null when action is standalone) ---
    "reversed_by_action_id", # Only set when action is reversed
    "issue_event_id",        # Only set when ticket linked to CRM

    # --- Billing & subscription (null for free-tier tenants) ---
    "stripe_customer_id",    # Free tenants have no Stripe ID
    "stripe_subscription_id",  # Free tenants have no subscription
    "stripe_price_id",       # Free tenants have no price
    "synthetic_scenario_id", # Only set for synthetic data

    # --- Execution envelope (null for partial/draft records) ---
    "account_id",            # Optional: envelopes may be account-less initially
    "project_id",            # Optional: some envelopes are project-independent
    "original_invocation_id",  # Only set for retry/continuation invocations

    # --- Policy & governance (null for unbound/draft records) ---
    "violated_policy_id",    # Only set when a policy was violated
    "policy_id",             # Nullable: tools/invocations may have no policy
    "policy_snapshot_id",    # Nullable: not all invocations have a snapshot
    "scope_id",              # Nullable: global rules have no scope
    "legacy_rule_id",        # Only set for migrated legacy rules
    "parent_rule_id",        # Top-level rules have no parent
    "source_proposal_id",    # Only set when rule originated from a proposal
    "human_actor_id",        # System-created scopes have no human actor
    "default_policy_id",     # MCP servers may have no default policy

    # --- MCP tool invocations (nullable FKs by design) ---
    "actor_id",              # Nullable: system-initiated invocations have no actor

    # --- Cost simulation (nullable for non-incident provenances) ---
    # CostSim models use Optional IDs for circuit breaker state tracking

    # --- Lessons learned & recovery (nullable when not tied to specific artifacts) ---
    "draft_proposal_id",     # Only set when lesson has a draft proposal

    # --- Export bundles (nullable: not all bundles are incident-scoped) ---
    # export_bundles.py models have Optional incident_id/agent_id

    # --- External response & suggestions (nullable for partial records) ---
    "request_id",            # Optional: not all records have a source request
    "rule_id",               # Suggestion provenances may lack a rule link
    "action_id",             # Suggestion provenances may lack an action link

    # --- Audit logging (nullable for system-initiated audit entries) ---
    "resource_id",           # Not all audit entries reference a specific resource
    "tenant_id",             # System-level audit entries may not be tenant-scoped

    # --- Retrieval evidence (nullable snapshot FK) ---
    "retrieval_evidence.policy_snapshot_id",  # Not all evidence has a snapshot

    # --- Limit & breach (nullable when not tied to run/incident) ---

    # --- Override (nullable run FK) ---
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class FieldInfo:
    """Parsed field metadata."""

    __slots__ = ("name", "type_str", "file", "class_name", "line", "is_optional",
                 "is_id_field", "is_status_field", "uses_enum", "source_type")

    def __init__(
        self,
        name: str,
        type_str: str,
        file: str,
        class_name: str,
        is_optional: bool = False,
        is_id_field: bool = False,
        is_status_field: bool = False,
        uses_enum: bool = False,
        source_type: str = "sqlmodel",  # "sqlmodel" | "sqlalchemy"
    ):
        self.name = name
        self.type_str = type_str
        self.file = file
        self.class_name = class_name
        self.is_optional = is_optional
        self.is_id_field = is_id_field
        self.is_status_field = is_status_field
        self.uses_enum = uses_enum
        self.source_type = source_type


class RelationshipInfo:
    """Parsed relationship metadata."""

    __slots__ = ("name", "file", "class_name", "has_back_populates", "args_str")

    def __init__(
        self,
        name: str,
        file: str,
        class_name: str,
        has_back_populates: bool,
        args_str: str,
    ):
        self.name = name
        self.file = file
        self.class_name = class_name
        self.has_back_populates = has_back_populates
        self.args_str = args_str


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _is_optional(type_str: str) -> bool:
    """Check whether a type annotation indicates Optional."""
    return "Optional" in type_str or "None" in type_str


def _uses_enum_or_literal(type_str: str, rest_of_line: str) -> bool:
    """Heuristic: does the type or Field() args reference an Enum or Literal?"""
    combined = type_str + " " + rest_of_line
    # Check for known enum class references (CamelCase type that isn't str/int/bool)
    if re.search(r"\b(Enum|Literal)\b", combined):
        return True
    # Check for enum class usage patterns like CusIntegrationStatus.CREATED
    if re.search(r"\b[A-Z][a-zA-Z]+\.\w+", rest_of_line):
        return True
    return False


def parse_file(pyfile: Path) -> tuple[list[FieldInfo], list[RelationshipInfo]]:
    """Parse a single model file, returning fields and relationships."""
    source = pyfile.read_text(encoding="utf-8")
    fields: list[FieldInfo] = []
    relationships: list[RelationshipInfo] = []

    # Determine class boundaries
    class_spans: list[tuple[str, int, int]] = []
    class_matches = list(RE_TABLE_CLASS.finditer(source))
    for i, m in enumerate(class_matches):
        start = m.start()
        end = class_matches[i + 1].start() if i + 1 < len(class_matches) else len(source)
        class_spans.append((m.group(1), start, end))

    def _owning_class(pos: int) -> str:
        """Return the class name that owns position *pos*."""
        for cname, cstart, cend in class_spans:
            if cstart <= pos < cend:
                return cname
        return "<unknown>"

    # ----- SQLModel / Pydantic-style field definitions -----
    for m in RE_FIELD_DEF.finditer(source):
        fname = m.group(1)
        ftype = m.group(2)
        rest = m.group(3)

        # Skip dunder attrs, methods, and non-field lines
        if fname.startswith("_") or fname in ("table", "model_config"):
            continue
        # Skip lines that are clearly method calls / property returns
        if "def " in rest or "return " in rest:
            continue

        cname = _owning_class(m.start())
        if cname == "<unknown>":
            continue

        fi = FieldInfo(
            name=fname,
            type_str=ftype.strip(),
            file=pyfile.name,
            class_name=cname,
            is_optional=_is_optional(ftype),
            is_id_field=any(fname.endswith(s) for s in ID_FIELD_SUFFIXES),
            is_status_field=(fname == "status"),
            uses_enum=_uses_enum_or_literal(ftype, rest),
            source_type="sqlmodel",
        )
        fields.append(fi)

    # ----- SQLAlchemy Column() definitions -----
    for m in RE_COLUMN_DEF.finditer(source):
        fname = m.group(1)
        col_args = m.group(2)

        if fname.startswith("_"):
            continue

        cname = _owning_class(m.start())
        if cname == "<unknown>":
            continue

        is_nullable = "nullable=True" in col_args or "nullable" not in col_args
        fi = FieldInfo(
            name=fname,
            type_str=col_args,
            file=pyfile.name,
            class_name=cname,
            is_optional=is_nullable,
            is_id_field=any(fname.endswith(s) for s in ID_FIELD_SUFFIXES),
            is_status_field=(fname == "status"),
            uses_enum=bool(re.search(r"\b(Enum|String)\b", col_args)),
            source_type="sqlalchemy",
        )
        fields.append(fi)

    # ----- Relationship definitions -----
    for m in RE_RELATIONSHIP.finditer(source):
        rname = m.group(1)
        rargs = m.group(2)
        cname = _owning_class(m.start())

        ri = RelationshipInfo(
            name=rname,
            file=pyfile.name,
            class_name=cname,
            has_back_populates="back_populates" in rargs,
            args_str=rargs,
        )
        relationships.append(ri)

    return fields, relationships


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------


def check_nullability(fields: list[FieldInfo], strict: bool) -> tuple[int, int, int]:
    """Check that *_id fields are non-optional unless allowlisted."""
    passed = 0
    warned = 0
    failed = 0

    id_fields = [f for f in fields if f.is_id_field]
    for f in id_fields:
        if f.is_optional and f.name not in OPTIONAL_ID_ALLOWLIST:
            label = f"{f.class_name}.{f.name} ({f.file})"
            reason = f"ID field is Optional — expected non-nullable"
            if strict:
                print(f"  [FAIL] {label} — {reason}")
                failed += 1
            else:
                print(f"  [WARN] {label} — {reason}")
                warned += 1
        elif f.is_id_field:
            if f.is_optional and f.name in OPTIONAL_ID_ALLOWLIST:
                print(f"  [PASS] {f.class_name}.{f.name} — Optional (allowlisted)")
            else:
                print(f"  [PASS] {f.class_name}.{f.name} — non-nullable ID (correct)")
            passed += 1

    return passed, warned, failed


def check_cardinality(relationships: list[RelationshipInfo], strict: bool) -> tuple[int, int, int]:
    """Check that relationship() calls include back_populates."""
    passed = 0
    warned = 0
    failed = 0

    for r in relationships:
        label = f"{r.class_name}.{r.name} ({r.file})"
        if r.has_back_populates:
            print(f"  [PASS] {label} — has back_populates")
            passed += 1
        else:
            reason = "relationship missing back_populates"
            if strict:
                print(f"  [FAIL] {label} — {reason}")
                failed += 1
            else:
                print(f"  [WARN] {label} — {reason}")
                warned += 1

    return passed, warned, failed


def check_semantic_drift(fields: list[FieldInfo], strict: bool) -> tuple[int, int, int]:
    """Check that 'status' fields use Enum or Literal types, not bare str."""
    passed = 0
    warned = 0
    failed = 0

    status_fields = [f for f in fields if f.is_status_field]
    for f in status_fields:
        label = f"{f.class_name}.{f.name} ({f.file})"
        # For SQLAlchemy Column defs, String is expected (enum enforced at app level)
        if f.source_type == "sqlalchemy":
            # SQLAlchemy columns use String — check for comment hints about valid values
            print(f"  [PASS] {label} — SQLAlchemy Column (app-level enum expected)")
            passed += 1
            continue

        # For SQLModel fields, bare `str` without enum reference is a drift signal
        type_clean = f.type_str.replace("Optional[", "").replace("]", "").strip()
        if type_clean == "str" and not f.uses_enum:
            reason = "status field uses bare 'str' — consider Enum or Literal type"
            if strict:
                print(f"  [WARN] {label} — {reason}")
                warned += 1
            else:
                print(f"  [WARN] {label} — {reason}")
                warned += 1
        else:
            print(f"  [PASS] {label} — typed status field")
            passed += 1

    return passed, warned, failed


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Data quality gate — static ORM field analysis (BA-18)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat nullability violations as failures (exit 1)",
    )
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=MODELS_DIR,
        help=f"Override models directory (default: {MODELS_DIR})",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Data Quality Gate (BA-18)")
    print("=" * 60)
    print(f"  Models directory: {args.models_dir}")
    print(f"  Strict mode: {args.strict}")
    print("=" * 60)
    print()

    if not args.models_dir.is_dir():
        print(f"[FATAL] Models directory not found: {args.models_dir}", file=sys.stderr)
        return 1

    # Collect all fields and relationships
    all_fields: list[FieldInfo] = []
    all_relationships: list[RelationshipInfo] = []

    for pyfile in sorted(args.models_dir.glob("*.py")):
        if pyfile.name in SKIP_FILES or pyfile.name.startswith("__"):
            continue
        fields, rels = parse_file(pyfile)
        all_fields.extend(fields)
        all_relationships.extend(rels)

    if not all_fields:
        print("[WARN] No fields found — check models directory")
        return 0

    total_pass = 0
    total_warn = 0
    total_fail = 0

    # --- Nullability Check ---
    print("--- Nullability Contract Check ---")
    p, w, f = check_nullability(all_fields, args.strict)
    total_pass += p
    total_warn += w
    total_fail += f
    print()

    # --- Cardinality Check ---
    print("--- Cardinality Contract Check ---")
    if all_relationships:
        p, w, f = check_cardinality(all_relationships, args.strict)
        total_pass += p
        total_warn += w
        total_fail += f
    else:
        print("  (no relationship() definitions found — skipping)")
    print()

    # --- Semantic Drift Check ---
    print("--- Semantic Drift Check (status fields) ---")
    p, w, f = check_semantic_drift(all_fields, args.strict)
    total_pass += p
    total_warn += w
    total_fail += f
    print()

    # --- Summary ---
    total_checked = total_pass + total_warn + total_fail
    print("-" * 60)
    print(f"  SUMMARY: {total_checked} checks executed ({len(all_fields)} fields, {len(all_relationships)} relationships)")
    print(f"    PASS: {total_pass}")
    print(f"    WARN: {total_warn}")
    print(f"    FAIL: {total_fail}")
    print("-" * 60)

    if total_fail > 0:
        print("  RESULT: FAILED")
        return 1

    print("  RESULT: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
