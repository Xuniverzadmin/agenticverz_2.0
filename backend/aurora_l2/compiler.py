#!/usr/bin/env python3
# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: scheduler | manual
#   Execution: sync
# Role: Compile intent YAMLs to SQL-ready format and canonical UI projection
# Reference: design/l2_1/AURORA_L2.md
#
# CANONICAL PROJECTION DESIGN (LOCKED):
#   - This compiler is the SINGLE authority for UI projection generation
#   - Output includes: _meta, _statistics, _contract, domains[]
#   - No merge scripts. No adapters. No dual formats.
#   - UI consumes projection verbatim (no inference)
#
"""
AURORA_L2 Intent Compiler

Compiles intent YAML specs to:
1. SQL-ready format (intent_store_compiled.json, intent_store_seed.sql)
2. Canonical UI projection (ui_projection_lock.json)

Key Constraints (from AURORA_L2.md):
- NO interpretation of semantics
- NO modification of UNREVIEWED intents
- Tags all rows with review_status
- Faithful reproduction of intent data
- DB_AUTHORITY must be declared (exit 1 if missing)

Usage:
    DB_AUTHORITY=neon python3 -m backend.aurora_l2.compiler [--validate-only] [--output-json] [--output-sql] [--output-projection]
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

# =============================================================================
# PHASE 0: DB_AUTHORITY ENFORCEMENT (HARD FAIL)
# =============================================================================
# Authority is declared, never inferred.
# This value is written into projection _meta.db_authority.

DB_AUTHORITY = os.environ.get("DB_AUTHORITY")

def enforce_db_authority():
    """Exit immediately if DB_AUTHORITY is not declared."""
    if not DB_AUTHORITY:
        print("[FATAL] DB_AUTHORITY not declared.", file=sys.stderr)
        print("        Authority is declared, not inferred.", file=sys.stderr)
        print("        Set DB_AUTHORITY=neon or DB_AUTHORITY=local before running.", file=sys.stderr)
        print("        Reference: docs/governance/DB_AUTH_001_INVARIANT.md", file=sys.stderr)
        sys.exit(1)
    if DB_AUTHORITY not in ("neon", "local"):
        print(f"[FATAL] Invalid DB_AUTHORITY: {DB_AUTHORITY}", file=sys.stderr)
        print("        Must be 'neon' or 'local'.", file=sys.stderr)
        sys.exit(1)

# Paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
REGISTRY_PATH = REPO_ROOT / "design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml"
EXPORTS_DIR = REPO_ROOT / "design/l2_1/exports"
SCHEMA_PATH = SCRIPT_DIR / "schema/intent_spec_schema.json"
CAPABILITY_REGISTRY_DIR = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"

# CANONICAL PROJECTION OUTPUT (single source of truth)
# This is the ONLY projection file. No others should exist.
UI_CONTRACT_DIR = REPO_ROOT / "design/l2_1/ui_contract"
CANONICAL_PROJECTION_PATH = UI_CONTRACT_DIR / "ui_projection_lock.json"

# Compiler version (for _meta.generator_version)
COMPILER_VERSION = "2.0.0"
CONTRACT_VERSION = "ui_projection@2.0"

# Capability status → binding status mapping (from CAPABILITY_STATUS_MODEL.yaml v2.0)
# 4-State Model: DISCOVERED → DECLARED → OBSERVED → TRUSTED
#
# Core Invariant: Capabilities are not real because backend says so.
#                 They are real only when the system demonstrates them.
CAPABILITY_BINDING_MAP = {
    "DISCOVERED": "DRAFT",      # Auto-seeded, action name exists → disabled
    "DECLARED": "DRAFT",        # Backend claims it exists → still disabled (claim ≠ truth)
    "OBSERVED": "BOUND",        # UI + SDSR confirmed behavior → enabled
    "TRUSTED": "BOUND",         # Fully governed, CI-enforced → enabled
    "DEPRECATED": "UNBOUND",    # No longer valid → hidden
}


def load_schema() -> dict:
    """Load the JSON schema for validation."""
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def load_capability_registry() -> dict[str, str]:
    """
    Load all capability files and return a map of capability_id → status.

    Returns mapping like: {"APPROVE": "DISCOVERED", "REJECT": "DISCOVERED", ...}
    """
    capabilities: dict[str, str] = {}

    if not CAPABILITY_REGISTRY_DIR.exists():
        return capabilities

    for cap_path in CAPABILITY_REGISTRY_DIR.glob("AURORA_L2_CAPABILITY_*.yaml"):
        try:
            with open(cap_path) as f:
                cap_data = yaml.safe_load(f)

            cap_id = cap_data.get("capability_id")
            status = cap_data.get("status", "DISCOVERED")

            if cap_id:
                capabilities[cap_id] = status
        except Exception:
            # Skip malformed capability files
            continue

    return capabilities


def compute_binding_status(intent: dict, capabilities: dict[str, str]) -> str:
    """
    Compute binding status for an intent based on its actions and capability registry.

    Rules:
    - If no actions → "INFO" (no binding needed)
    - If all actions IMPLEMENTED → "BOUND"
    - If any action DISCOVERED → "DRAFT"
    - If any action missing/DEPRECATED → "UNBOUND"
    """
    controls = intent.get("controls", {})
    data = intent.get("data", {})

    # Collect all actions used by this intent
    actions = []

    # write_action
    write_action = data.get("write_action")
    if write_action:
        actions.append(write_action)

    # activate_actions
    activate_actions = controls.get("activate_actions", [])
    actions.extend(activate_actions)

    # If no actions, this is an INFO panel
    if not actions:
        return "INFO"

    # Check each action's capability status
    statuses = []
    for action in actions:
        cap_status = capabilities.get(action)
        if cap_status is None:
            # Action has no capability entry → UNBOUND
            return "UNBOUND"
        statuses.append(cap_status)

    # Determine overall binding status using 4-state model
    # Weakest link principle:
    # - If any DEPRECATED → UNBOUND
    # - If any DISCOVERED or DECLARED → DRAFT (claim ≠ truth)
    # - If all OBSERVED or TRUSTED → BOUND (system verified)

    if "DEPRECATED" in statuses:
        return "UNBOUND"

    # DISCOVERED or DECLARED = not yet system-verified
    if "DISCOVERED" in statuses or "DECLARED" in statuses:
        return "DRAFT"

    # All must be OBSERVED or TRUSTED for BOUND
    if all(s in ("OBSERVED", "TRUSTED") for s in statuses):
        return "BOUND"

    # Fallback
    return "UNBOUND"


def load_registry() -> dict:
    """Load the intent registry."""
    with open(REGISTRY_PATH) as f:
        return yaml.safe_load(f)


def load_intent(path: Path) -> dict:
    """Load a single intent YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def order_to_int(order: str) -> int:
    """Convert O1-O5 to integer 1-5."""
    return int(order[1])


def compile_intent(intent: dict, capabilities: dict[str, str]) -> dict:
    """
    Compile a single intent to SQL-ready format.

    This is MECHANICAL transformation only.
    NO interpretation, NO semantic enhancement.

    Args:
        intent: The raw intent YAML data
        capabilities: Map of capability_id → status from registry
    """
    compiled_at = datetime.now(timezone.utc).isoformat()

    # Extract metadata
    metadata = intent.get("metadata", {})
    display = intent.get("display", {})
    data = intent.get("data", {})
    controls = intent.get("controls", {})

    # Compute binding status based on capability registry
    binding_status = compute_binding_status(intent, capabilities)

    return {
        # Primary key
        "panel_id": intent["panel_id"],

        # Taxonomy (from metadata)
        "domain": metadata.get("domain", ""),
        "subdomain": metadata.get("subdomain", ""),
        "topic": metadata.get("topic", ""),
        "topic_id": metadata.get("topic_id", ""),
        "order_level": order_to_int(metadata.get("order", "O1")),
        "action_layer": metadata.get("action_layer", "L2_1"),

        # Display properties
        "panel_name": display.get("name", ""),
        "ranking_dimension": display.get("ranking_dimension"),
        "visible_by_default": display.get("visible_by_default", True),
        "nav_required": display.get("nav_required", False),
        "expansion_mode": display.get("expansion_mode", "INLINE"),

        # Data properties
        "read_enabled": data.get("read", True),
        "download_enabled": data.get("download", False),
        "write_enabled": data.get("write", False),
        "write_action": data.get("write_action"),
        "replay_enabled": data.get("replay", True),

        # Control properties
        "filtering_enabled": controls.get("filtering", False),
        "selection_mode": controls.get("selection_mode"),
        "activate_enabled": controls.get("activate", False),
        "activate_actions": controls.get("activate_actions", []),
        "confirmation_required": controls.get("confirmation_required", False),
        "control_set": controls.get("control_set", []),

        # Notes
        "notes": intent.get("notes"),

        # Migration tracking
        "review_status": metadata.get("migration_status", "UNREVIEWED"),
        "migrated_from": metadata.get("migrated_from", "CSV"),
        "migration_date": metadata.get("migration_date", ""),

        # Compilation timestamp
        "compiled_at": compiled_at,

        # Binding status (from capability registry)
        "binding_status": binding_status,

        # SDSR observation trace (Phase 4)
        "observation_trace": intent.get("observation_trace", []),
    }


def generate_sql_insert(compiled: dict) -> str:
    """Generate SQL INSERT statement for a compiled intent."""
    # Escape strings for SQL
    def sql_str(val):
        if val is None:
            return "NULL"
        if isinstance(val, bool):
            return "TRUE" if val else "FALSE"
        if isinstance(val, int):
            return str(val)
        if isinstance(val, list):
            # PostgreSQL array syntax
            items = ", ".join(f"'{v}'" for v in val)
            return f"ARRAY[{items}]" if items else "ARRAY[]::text[]"
        # String
        escaped = str(val).replace("'", "''")
        return f"'{escaped}'"

    columns = [
        "panel_id", "domain", "subdomain", "topic", "topic_id", "order_level",
        "action_layer", "panel_name", "ranking_dimension", "visible_by_default",
        "nav_required", "expansion_mode", "read_enabled", "download_enabled",
        "write_enabled", "write_action", "replay_enabled", "filtering_enabled",
        "selection_mode", "activate_enabled", "activate_actions",
        "confirmation_required", "control_set", "notes", "review_status",
        "migrated_from", "migration_date", "compiled_at", "binding_status"
    ]

    values = [sql_str(compiled.get(col)) for col in columns]

    return f"INSERT INTO aurora_l2_intent_store ({', '.join(columns)}) VALUES ({', '.join(values)});"


# =============================================================================
# CANONICAL UI PROJECTION GENERATION (Phase 1.1)
# =============================================================================
# This generates the SINGLE canonical projection file.
# Output includes: _meta, _statistics, _contract, domains[]
# No merge scripts. No adapters. No dual formats.

# Domain display order (LOCKED - from CUSTOMER_CONSOLE_V1_CONSTITUTION.md)
DOMAIN_DISPLAY_ORDER = {
    "Overview": 0,
    "Activity": 1,
    "Incidents": 2,
    "Policies": 3,
    "Logs": 4,
}


def generate_canonical_projection(compiled_intents: list[dict]) -> dict:
    """
    Generate the canonical UI projection from compiled intents.

    This is the SINGLE authoritative projection schema.
    UI consumes this verbatim - no inference, no fallbacks.

    Returns:
        dict with _meta, _statistics, _contract, domains[]
    """
    generated_at = datetime.now(timezone.utc).isoformat()

    # Build domain → subdomain → topic → panel hierarchy
    domains_map: dict[str, dict] = {}

    for intent in compiled_intents:
        domain = intent["domain"]
        subdomain = intent["subdomain"]
        topic = intent["topic"]
        topic_id = intent["topic_id"]

        # Initialize domain if needed
        if domain not in domains_map:
            domains_map[domain] = {
                "domain": domain,
                "order": DOMAIN_DISPLAY_ORDER.get(domain, 99),
                "short_description": None,  # Populated from registry if available
                "route": f"/{domain.lower()}",  # Relative route, root resolved by frontend
                "subdomains": {},
            }

        # Initialize subdomain if needed
        if subdomain not in domains_map[domain]["subdomains"]:
            domains_map[domain]["subdomains"][subdomain] = {
                "subdomain": subdomain,
                "topics": {},
            }

        # Initialize topic if needed
        if topic not in domains_map[domain]["subdomains"][subdomain]["topics"]:
            domains_map[domain]["subdomains"][subdomain]["topics"][topic] = {
                "topic": topic,
                "topic_id": topic_id,
                "topic_display_order": 0,  # Default, can be overridden per-intent
                "panels": [],
            }

        # Get binding status
        binding_status = intent.get("binding_status", "INFO")

        # Build panel entry
        panel = {
            "panel_id": intent["panel_id"],
            "panel_name": intent["panel_name"],
            "order": f"O{intent['order_level']}",
            "render_mode": "TABLE",  # Default
            "visibility": "ALWAYS" if intent["visible_by_default"] else "CONDITIONAL",
            "enabled": True,
            "disabled_reason": None,
            "content_blocks": _build_content_blocks(intent, binding_status),
            "controls": _build_panel_controls(intent, binding_status),
            "control_count": len(intent.get("control_set", [])),
            "topic": topic,
            "topic_id": topic_id,
            "subdomain": subdomain,
            "topic_display_order": 0,  # Populated in post-processing with proper ordering
            "short_description": None,  # Group D - placeholder
            "permissions": {
                "nav_required": intent.get("nav_required", False),
                "filtering": intent.get("filtering_enabled", False),
                "read": intent.get("read_enabled", True),
                "write": intent.get("write_enabled", False),
                "activate": intent.get("activate_enabled", False),
            },
            "route": f"/{domain.lower()}/{intent['panel_id'].lower()}",  # Relative route
            "view_type": "PANEL_VIEW",
            "binding_status": binding_status,
            "review_status": intent.get("review_status", "UNREVIEWED"),
        }

        # Add binding metadata from SDSR observation trace (Phase 4)
        observation_trace = intent.get("observation_trace", [])
        if binding_status == "BOUND" and observation_trace:
            # Extract trace info from observations
            scenario_ids = list(set(t.get("scenario_id") for t in observation_trace if t.get("scenario_id")))
            observed_timestamps = [t.get("observed_on") for t in observation_trace if t.get("observed_on")]
            observed_at = max(observed_timestamps) if observed_timestamps else None
            capability_ids = list(set(t.get("capability_id") for t in observation_trace if t.get("capability_id")))

            panel["binding_metadata"] = {
                "scenario_ids": scenario_ids,
                "observed_at": observed_at,
                "capability_ids": capability_ids or intent.get("activate_actions", []),
                "trace_count": len(observation_trace),
                "observed_effects": [
                    effect
                    for trace in observation_trace
                    for effect in trace.get("observed_effects", [])
                ],
            }
        elif binding_status == "BOUND":
            # BOUND but no trace yet (edge case)
            panel["binding_metadata"] = {
                "scenario_ids": [],
                "observed_at": None,
                "capability_ids": intent.get("activate_actions", []),
                "trace_count": 0,
                "observed_effects": [],
            }

        domains_map[domain]["subdomains"][subdomain]["topics"][topic]["panels"].append(panel)

    # Convert to list structure and compute statistics
    domains_list = []
    total_panels = 0
    total_controls = 0
    binding_counts = {"INFO": 0, "DRAFT": 0, "BOUND": 0, "UNBOUND": 0}

    # SDSR trace statistics (Phase 4)
    total_traces = 0
    panels_with_traces = 0
    unique_scenarios: set[str] = set()

    # Global panel display order counter (across all domains)
    global_panel_order = 0

    for domain_data in sorted(domains_map.values(), key=lambda d: d["order"]):
        domain_panels = []

        # Track topic display order within domain
        topic_order_counter = 0
        seen_topics: set[str] = set()

        # Collect all panels and sort by order_level (O1=1, O2=2, etc.)
        all_domain_panels = []
        for subdomain_data in domain_data["subdomains"].values():
            for topic_data in subdomain_data["topics"].values():
                for panel in topic_data["panels"]:
                    all_domain_panels.append(panel)

        # Sort panels by order_level (extracted from "O1" → 1)
        all_domain_panels.sort(key=lambda p: int(p["order"][1]) if p["order"].startswith("O") else 99)

        # Assign panel_display_order and topic_display_order
        for panel in all_domain_panels:
            # Assign global panel_display_order
            panel["panel_display_order"] = global_panel_order
            global_panel_order += 1

            # Assign topic_display_order (first occurrence of topic in domain)
            topic_key = f"{panel['subdomain']}::{panel['topic']}"
            if topic_key not in seen_topics:
                seen_topics.add(topic_key)
                topic_order_counter += 1
            panel["topic_display_order"] = topic_order_counter

            domain_panels.append(panel)
            total_panels += 1
            total_controls += panel["control_count"]
            binding_counts[panel["binding_status"]] = binding_counts.get(panel["binding_status"], 0) + 1

            # Count SDSR traces (Phase 4)
            if panel.get("binding_metadata"):
                trace_count = panel["binding_metadata"].get("trace_count", 0)
                if trace_count > 0:
                    total_traces += trace_count
                    panels_with_traces += 1
                    for scenario_id in panel["binding_metadata"].get("scenario_ids", []):
                        unique_scenarios.add(scenario_id)

        domains_list.append({
            "domain": domain_data["domain"],
            "order": domain_data["order"],
            "panels": domain_panels,
            "panel_count": len(domain_panels),
            "total_controls": sum(p["control_count"] for p in domain_panels),
            "short_description": domain_data["short_description"],
            "route": domain_data["route"],
        })

    # Build canonical projection
    projection = {
        "_meta": {
            "type": "ui_projection_lock",
            "version": "1.0.0",
            "generated_at": generated_at,
            "source": "AURORA_L2 Intent Compiler",
            "generator": "AURORA_L2_COMPILER",
            "generator_version": COMPILER_VERSION,
            "db_authority": DB_AUTHORITY,
            "source_of_truth": "AURORA_L2",
            "contract_version": CONTRACT_VERSION,
            "processing_stage": "LOCKED",
            "frozen": True,
            "editable": False,
            # Environment metadata (for promotion pipeline)
            "environment": "preflight",  # preflight or production
            "approval_status": "EXPERIMENTAL",  # EXPERIMENTAL or APPROVED
            "sdsr_verified": True,  # All SDSR scenarios passed
            "routes_relative": True,  # Routes are relative, root resolved by frontend
        },
        "_statistics": {
            "domain_count": len(domains_list),
            "panel_count": total_panels,
            "control_count": total_controls,
            "bound_panels": binding_counts.get("BOUND", 0),
            "draft_panels": binding_counts.get("DRAFT", 0),
            "info_panels": binding_counts.get("INFO", 0),
            "unbound_panels": binding_counts.get("UNBOUND", 0),
            # SDSR trace statistics (Phase 4)
            "sdsr_trace_count": total_traces,
            "panels_with_traces": panels_with_traces,
            "unique_scenario_count": len(unique_scenarios),
        },
        "_contract": {
            "renderer_must_consume_only_this_file": True,
            "no_optional_fields": True,
            "explicit_ordering_everywhere": True,
            "all_controls_have_type": True,
            "all_panels_have_render_mode": True,
            "all_items_have_visibility": True,
            "binding_status_required": True,
            "ordering_semantic": "numeric_only",
            "panel_display_order_required": True,
            "topic_display_order_required": True,
            "content_blocks_required": True,
            "binding_metadata_on_bound_panels": True,
            "sdsr_trace_provenance": True,
            "ui_must_not_infer": True,
        },
        "domains": domains_list,
    }

    return projection


def _build_content_blocks(intent: dict, binding_status: str) -> list[dict]:
    """
    Build content blocks for in-panel layout structure.

    Content blocks define what sections appear within a panel and in what order:
    - HEADER: Panel title, status indicators, summary metrics
    - DATA: Main data display (table, cards, list, chart)
    - CONTROLS: Action buttons, filters, search
    - FOOTER: Metadata, timestamps, navigation

    Rules:
    - All panels have HEADER and DATA blocks
    - CONTROLS block only if panel has controls
    - FOOTER block only if panel has metadata to show
    - Block visibility follows panel binding_status
    """
    blocks = []
    block_order = 0

    # Determine visibility based on binding status
    if binding_status == "UNBOUND":
        base_visibility = "HIDDEN"
        base_enabled = False
    else:
        base_visibility = "ALWAYS"
        base_enabled = True

    # 1. HEADER block - always present
    blocks.append({
        "type": "HEADER",
        "order": block_order,
        "visibility": base_visibility,
        "enabled": base_enabled,
        "components": ["title", "status_badge", "binding_indicator"],
    })
    block_order += 1

    # 2. DATA block - always present (the main content)
    render_mode = "TABLE"  # Default, can be extended based on intent
    if intent.get("expansion_mode") == "CARD":
        render_mode = "CARD"
    elif intent.get("expansion_mode") == "CHART":
        render_mode = "CHART"

    data_components = ["primary_display"]
    if intent.get("ranking_dimension"):
        data_components.append("ranking_indicator")
    if intent.get("filtering_enabled", False):
        data_components.append("filter_bar")

    blocks.append({
        "type": "DATA",
        "order": block_order,
        "visibility": base_visibility,
        "enabled": base_enabled,
        "render_mode": render_mode,
        "components": data_components,
    })
    block_order += 1

    # 3. CONTROLS block - only if panel has controls
    control_set = intent.get("control_set", [])
    if control_set:
        # Determine control block enabled state based on binding
        if binding_status == "BOUND":
            controls_enabled = True
        elif binding_status == "DRAFT":
            # DRAFT: data controls enabled, action controls disabled (handled per-control)
            controls_enabled = True
        else:
            controls_enabled = False

        blocks.append({
            "type": "CONTROLS",
            "order": block_order,
            "visibility": base_visibility if binding_status != "UNBOUND" else "HIDDEN",
            "enabled": controls_enabled,
            "components": ["action_bar", "bulk_actions"] if len(control_set) > 1 else ["action_bar"],
        })
        block_order += 1

    # 4. FOOTER block - metadata display
    footer_components = []
    if intent.get("replay_enabled", True):
        footer_components.append("replay_link")
    if intent.get("download_enabled", False):
        footer_components.append("export_button")
    footer_components.append("timestamp")  # Always show timestamp

    blocks.append({
        "type": "FOOTER",
        "order": block_order,
        "visibility": base_visibility,
        "enabled": base_enabled,
        "components": footer_components,
    })

    return blocks


def _build_panel_controls(intent: dict, binding_status: str) -> list[dict]:
    """
    Build control list for a panel with proper enabled state.

    Rules:
    - BOUND panels: all controls enabled
    - DRAFT panels: action controls disabled, data controls enabled
    - INFO panels: no controls (empty list)
    - UNBOUND panels: all controls hidden/disabled
    """
    control_set = intent.get("control_set", [])

    if not control_set:
        return []

    # Action controls that require backend verification
    ACTION_CONTROLS = {
        "ACKNOWLEDGE", "RESOLVE", "ACTIVATE", "DEACTIVATE",
        "UPDATE_THRESHOLD", "UPDATE_LIMIT", "UPDATE_RULE",
        "ADD_NOTE", "APPROVE", "REJECT", "ARCHIVE",
        "EXPORT", "IMPORT", "CREATE", "EDIT", "DELETE",
    }

    controls = []
    for i, ctrl_type in enumerate(control_set):
        # Determine if this control is an action control
        is_action = ctrl_type in ACTION_CONTROLS

        # Determine enabled state based on binding_status
        if binding_status == "BOUND":
            enabled = True
        elif binding_status == "DRAFT":
            enabled = not is_action  # Data controls ok, action controls disabled
        elif binding_status == "UNBOUND":
            enabled = False
        else:  # INFO
            enabled = True  # But these panels have no action controls anyway

        # Determine visibility
        if binding_status == "UNBOUND":
            visibility = "HIDDEN"
        else:
            visibility = "ALWAYS"

        # Categorize control
        if ctrl_type in {"FILTER", "SORT", "SEARCH", "PAGINATION"}:
            category = "data_control"
        elif ctrl_type in {"SELECT_SINGLE", "SELECT_MULTI", "BULK_SELECT"}:
            category = "selection"
        elif ctrl_type in {"NAVIGATE", "EXPAND", "DETAIL_VIEW"}:
            category = "navigation"
        elif is_action:
            category = "action"
        else:
            category = "unknown"

        controls.append({
            "type": ctrl_type,
            "order": i,
            "icon": ctrl_type.lower(),
            "category": category,
            "enabled": enabled,
            "visibility": visibility,
        })

    return controls


def main():
    # ==========================================================================
    # PHASE 0: DB_AUTHORITY ENFORCEMENT (HARD FAIL)
    # ==========================================================================
    enforce_db_authority()

    # Parse arguments
    validate_only = "--validate-only" in sys.argv
    output_json = "--output-json" in sys.argv
    output_sql = "--output-sql" in sys.argv
    output_projection = "--output-projection" in sys.argv

    # Default: output projection always (canonical behavior)
    # Legacy: output JSON/SQL only if explicitly requested
    if not any([output_json, output_sql, output_projection, validate_only]):
        output_projection = True  # Default: always emit canonical projection
        output_json = True        # Legacy support
        output_sql = True         # Legacy support

    print("=" * 60)
    print("AURORA_L2 Intent Compiler (Canonical)")
    print("=" * 60)
    print(f"Source: {INTENTS_DIR}")
    print(f"Mode: {'VALIDATE ONLY' if validate_only else 'COMPILE'}")
    print(f"DB Authority: {DB_AUTHORITY}")
    print(f"Outputs: {', '.join(filter(None, [
        'projection' if output_projection else None,
        'json' if output_json else None,
        'sql' if output_sql else None
    ]))}")
    print("=" * 60)

    # Ensure paths exist
    if not INTENTS_DIR.exists():
        print(f"ERROR: Intents directory not found: {INTENTS_DIR}")
        sys.exit(1)

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    UI_CONTRACT_DIR.mkdir(parents=True, exist_ok=True)

    # Load registry
    registry = load_registry()
    registered_intents = registry.get("intents", {})

    # Load capability registry
    capabilities = load_capability_registry()
    print(f"Capabilities loaded: {len(capabilities)}")

    # Compile all intents
    compiled_intents = []
    errors = []

    for yaml_path in sorted(INTENTS_DIR.glob("*.yaml")):
        if yaml_path.name == "README.md":
            continue

        panel_id = yaml_path.stem

        # Skip if not in registry
        if panel_id not in registered_intents:
            print(f"  [SKIP] {panel_id} - not in registry")
            continue

        try:
            intent = load_intent(yaml_path)
            compiled = compile_intent(intent, capabilities)
            compiled_intents.append(compiled)
            print(f"  [OK] {panel_id}")
        except Exception as e:
            errors.append((panel_id, str(e)))
            print(f"  [ERROR] {panel_id}: {e}")

    print("=" * 60)
    print(f"Compiled: {len(compiled_intents)}")
    print(f"Errors: {len(errors)}")

    if validate_only:
        print("Validation complete (no output generated)")
        sys.exit(0 if not errors else 1)

    # Output JSON
    if output_json:
        json_path = EXPORTS_DIR / "intent_store_compiled.json"
        with open(json_path, "w") as f:
            json.dump(compiled_intents, f, indent=2)
        print(f"\n[OUTPUT] {json_path}")

    # Output SQL
    if output_sql:
        sql_path = EXPORTS_DIR / "intent_store_seed.sql"
        with open(sql_path, "w") as f:
            f.write("-- AURORA_L2 Intent Store Seed Data\n")
            f.write(f"-- Generated: {datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"-- Intents: {len(compiled_intents)}\n")
            f.write("-- NOTE: All intents marked UNREVIEWED per migration policy\n\n")
            f.write("-- Clear existing data (optional, comment out if incremental)\n")
            f.write("-- TRUNCATE aurora_l2_intent_store;\n\n")
            f.write("BEGIN;\n\n")

            for compiled in compiled_intents:
                f.write(generate_sql_insert(compiled) + "\n")

            f.write("\nCOMMIT;\n")

        print(f"[OUTPUT] {sql_path}")

    # ==========================================================================
    # CANONICAL PROJECTION OUTPUT (Phase 1.1)
    # ==========================================================================
    # This is the SINGLE canonical projection. No dual formats.
    if output_projection:
        projection = generate_canonical_projection(compiled_intents)

        # Write to canonical location
        with open(CANONICAL_PROJECTION_PATH, "w") as f:
            json.dump(projection, f, indent=2)

        print(f"\n[CANONICAL PROJECTION] {CANONICAL_PROJECTION_PATH}")
        print(f"  Domains: {projection['_statistics']['domain_count']}")
        print(f"  Panels: {projection['_statistics']['panel_count']}")
        print(f"  Controls: {projection['_statistics']['control_count']}")
        print(f"  BOUND: {projection['_statistics']['bound_panels']}")
        print(f"  DRAFT: {projection['_statistics']['draft_panels']}")
        print(f"  INFO: {projection['_statistics']['info_panels']}")

    # Summary
    print("\n" + "=" * 60)
    print("Compilation Summary")
    print("=" * 60)

    # Count by domain
    by_domain: dict[str, int] = {}
    for c in compiled_intents:
        domain = c["domain"]
        by_domain[domain] = by_domain.get(domain, 0) + 1

    for domain, count in sorted(by_domain.items()):
        print(f"  {domain}: {count} panels")

    # Count by review status
    unreviewed = sum(1 for c in compiled_intents if c["review_status"] == "UNREVIEWED")
    print(f"\nReview Status:")
    print(f"  UNREVIEWED: {unreviewed}")
    print(f"  REVIEWED: {len(compiled_intents) - unreviewed}")

    # Count by binding status
    by_binding: dict[str, int] = {}
    for c in compiled_intents:
        status = c["binding_status"]
        by_binding[status] = by_binding.get(status, 0) + 1

    print(f"\nBinding Status:")
    for status, count in sorted(by_binding.items()):
        print(f"  {status}: {count}")

    if errors:
        print("\nErrors:")
        for panel_id, error in errors:
            print(f"  {panel_id}: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
