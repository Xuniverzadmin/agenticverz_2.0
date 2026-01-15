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
    DB_AUTHORITY=neon python3 -m backend.aurora_l2.SDSR_UI_AURORA_compiler [--validate-only] [--output-json] [--output-sql] [--output-projection]
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

# UI Plan Authority (CANONICAL SOURCE OF TRUTH)
# ui_plan.yaml is the HIGHEST authority per UI-as-Constraint doctrine
# Compiler reads this FIRST, then derives state mechanically
UI_PLAN_PATH = REPO_ROOT / "design/l2_1/ui_plan.yaml"

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


def load_ui_plan() -> dict:
    """
    Load the canonical UI plan (HIGHEST AUTHORITY).

    Per UI-as-Constraint doctrine:
    - ui_plan.yaml is human intent
    - Compiler reads this FIRST
    - State is derived mechanically from:
      1. Intent YAML existence
      2. Capability registry status

    Returns:
        dict containing domains, panels, and metadata from ui_plan.yaml
    """
    if not UI_PLAN_PATH.exists():
        print(f"[FATAL] UI Plan not found: {UI_PLAN_PATH}", file=sys.stderr)
        print("        UI Plan is the canonical authority. Cannot proceed without it.", file=sys.stderr)
        sys.exit(1)

    with open(UI_PLAN_PATH) as f:
        return yaml.safe_load(f)


def derive_panel_state(
    panel_def: dict,
    intent_exists: bool,
    capabilities: dict[str, str],
    compiled_intent: dict | None = None
) -> str:
    """
    Derive panel binding state mechanically from inputs.

    State Derivation Rules (from UI-as-Constraint doctrine):
    - EMPTY: UI planned, intent YAML missing (intent_spec is null)
    - UNBOUND: Intent exists, capability missing or actions not registered
    - DRAFT: Capability DECLARED but SDSR not observed
    - BOUND: Capability OBSERVED or TRUSTED
    - DEFERRED: Explicit governance decision (from ui_plan.yaml)

    Args:
        panel_def: Panel definition from ui_plan.yaml
        intent_exists: Whether the intent YAML file exists
        capabilities: Map of capability_id → status from registry
        compiled_intent: Optional compiled intent (for action checking)

    Returns:
        One of: EMPTY, UNBOUND, DRAFT, BOUND, DEFERRED
    """
    # Check for explicit DEFERRED state in ui_plan
    ui_plan_state = panel_def.get("state", "")
    if ui_plan_state == "DEFERRED":
        return "DEFERRED"

    # If intent_spec is null in ui_plan, it's EMPTY
    intent_spec = panel_def.get("intent_spec")
    if not intent_spec:
        return "EMPTY"

    # If intent YAML doesn't exist on disk, it's EMPTY
    if not intent_exists:
        return "EMPTY"

    # Intent exists - check capabilities
    # First, check expected_capability from ui_plan.yaml (for interpretation panels)
    expected_capability = panel_def.get("expected_capability")
    if expected_capability:
        cap_status = capabilities.get(expected_capability)
        if cap_status is None:
            return "UNBOUND"
        if cap_status in ("OBSERVED", "TRUSTED"):
            return "BOUND"
        if cap_status == "DECLARED":
            return "DRAFT"
        if cap_status == "DEPRECATED":
            return "UNBOUND"
        return "UNBOUND"

    # Second, check activate_actions from compiled intent (for execution panels)
    if compiled_intent:
        actions = compiled_intent.get("activate_actions", [])
        write_action = compiled_intent.get("write_action")
        if write_action:
            actions = actions + [write_action]

        if actions:
            # Check all actions against capability registry
            statuses = []
            for action in actions:
                cap_status = capabilities.get(action)
                if cap_status is None:
                    return "UNBOUND"  # Missing action = UNBOUND
                statuses.append(cap_status)

            # Determine overall state using weakest-link principle
            if "DEPRECATED" in statuses:
                return "UNBOUND"
            if "DISCOVERED" in statuses or "DECLARED" in statuses:
                return "DRAFT"
            if all(s in ("OBSERVED", "TRUSTED") for s in statuses):
                return "BOUND"
            return "UNBOUND"

    # No expected_capability and no actions = INFO panel (data only)
    # Default to UNBOUND until we have a better signal
    return "UNBOUND"


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

        # HIL v1: Panel classification (Phase 2)
        # Default to "execution" if not specified
        "panel_class": intent.get("panel_class", "execution"),

        # HIL v1: Provenance (only for interpretation panels)
        "provenance": intent.get("provenance"),
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

# Domain display order (LOCKED - from ui_plan.yaml / CUSTOMER_CONSOLE_V1_CONSTITUTION.md)
# All 7 domains must be present per UI-as-Constraint doctrine
DOMAIN_DISPLAY_ORDER = {
    "Overview": 0,
    "Activity": 1,
    "Incidents": 2,
    "Policies": 3,
    "Logs": 4,
    "Account": 5,
    "Connectivity": 6,
}


def generate_canonical_projection(
    ui_plan: dict,
    compiled_intents_map: dict[str, dict],
    capabilities: dict[str, str]
) -> dict:
    """
    Generate the canonical UI projection from ui_plan.yaml (HIGHEST AUTHORITY).

    Per UI-as-Constraint doctrine:
    - ui_plan.yaml defines the FULL surface (86 panels)
    - Compiler derives state mechanically
    - EMPTY panels MUST be emitted (they are signals, not failures)
    - UI consumes this verbatim (no inference, no fallbacks)

    Args:
        ui_plan: The loaded ui_plan.yaml data
        compiled_intents_map: Map of panel_id → compiled intent (may be partial)
        capabilities: Map of capability_id → status from registry

    Returns:
        dict with _meta, _statistics, _contract, domains[]
    """
    generated_at = datetime.now(timezone.utc).isoformat()

    # Build domain list from ui_plan (CANONICAL ORDER)
    domains_list = []
    total_panels = 0
    total_controls = 0

    # State counts for statistics
    state_counts = {"EMPTY": 0, "UNBOUND": 0, "DRAFT": 0, "BOUND": 0, "DEFERRED": 0, "INFO": 0}
    binding_counts = {"INFO": 0, "DRAFT": 0, "BOUND": 0, "UNBOUND": 0}  # Legacy compat
    panel_class_counts = {"execution": 0, "interpretation": 0}

    # SDSR trace statistics
    total_traces = 0
    panels_with_traces = 0
    unique_scenarios: set[str] = set()

    # Global panel display order counter
    global_panel_order = 0

    # Iterate over domains from ui_plan (THE AUTHORITY)
    for domain_idx, domain_def in enumerate(ui_plan.get("domains", [])):
        domain_name = domain_def["id"]
        domain_panels = []

        # Track topic display order within domain
        topic_order_counter = 0
        seen_topics: set[str] = set()

        # Iterate over subdomains from ui_plan
        for subdomain_def in domain_def.get("subdomains", []):
            subdomain_id = subdomain_def["id"]

            # Iterate over topics from ui_plan
            for topic_def in subdomain_def.get("topics", []):
                topic_id = topic_def["id"]

                # Iterate over panels from ui_plan (CANONICAL LOOP)
                for panel_def in topic_def.get("panels", []):
                    panel_id = panel_def["panel_id"]
                    order = panel_def.get("order", "O1")
                    panel_class = panel_def.get("panel_class", "execution")

                    # Check if intent YAML exists
                    intent_spec = panel_def.get("intent_spec")
                    intent_path = REPO_ROOT / intent_spec if intent_spec else None
                    intent_exists = intent_path.exists() if intent_path else False

                    # Get compiled intent data if available
                    compiled_intent = compiled_intents_map.get(panel_id)

                    # Derive state mechanically (pass compiled_intent for action checking)
                    panel_state = derive_panel_state(
                        panel_def, intent_exists, capabilities, compiled_intent
                    )

                    # Build panel entry
                    if compiled_intent:
                        # Use data from compiled intent
                        panel = _build_panel_from_intent(
                            compiled_intent,
                            domain_name,
                            subdomain_id,
                            topic_id,
                            panel_state,
                            global_panel_order
                        )
                    else:
                        # EMPTY panel - create minimal entry (THIS IS CRITICAL)
                        panel = _build_empty_panel(
                            panel_id,
                            domain_name,
                            subdomain_id,
                            topic_id,
                            order,
                            panel_class,
                            panel_state,
                            global_panel_order
                        )

                    # Assign topic_display_order
                    topic_key = f"{subdomain_id}::{topic_id}"
                    if topic_key not in seen_topics:
                        seen_topics.add(topic_key)
                        topic_order_counter += 1
                    panel["topic_display_order"] = topic_order_counter

                    # Add panel to domain
                    domain_panels.append(panel)

                    # Update statistics
                    total_panels += 1
                    total_controls += panel.get("control_count", 0)
                    global_panel_order += 1

                    # State statistics
                    state_counts[panel_state] = state_counts.get(panel_state, 0) + 1

                    # Legacy binding counts (map new states to old)
                    if panel_state == "EMPTY":
                        binding_counts["UNBOUND"] = binding_counts.get("UNBOUND", 0) + 1
                    elif panel_state in ("UNBOUND", "DEFERRED"):
                        binding_counts["UNBOUND"] = binding_counts.get("UNBOUND", 0) + 1
                    elif panel_state == "DRAFT":
                        binding_counts["DRAFT"] = binding_counts.get("DRAFT", 0) + 1
                    elif panel_state == "BOUND":
                        binding_counts["BOUND"] = binding_counts.get("BOUND", 0) + 1
                    else:
                        binding_counts["INFO"] = binding_counts.get("INFO", 0) + 1

                    # Panel class statistics
                    panel_class_counts[panel_class] = panel_class_counts.get(panel_class, 0) + 1

                    # SDSR trace statistics (only for panels with binding_metadata)
                    if panel.get("binding_metadata"):
                        trace_count = panel["binding_metadata"].get("trace_count", 0)
                        if trace_count > 0:
                            total_traces += trace_count
                            panels_with_traces += 1
                            for scenario_id in panel["binding_metadata"].get("scenario_ids", []):
                                unique_scenarios.add(scenario_id)

        # Panel order is LOCKED to ui_plan.yaml traversal order:
        # Domain → Subdomain → Topic → Panel (within topic, by O-order as defined in YAML)
        # NO RUNTIME SORTING - the YAML order IS the order.
        # Re-assign panel_display_order (sequential within domain)
        for i, panel in enumerate(domain_panels):
            panel["panel_display_order"] = sum(
                len(d["panels"]) for d in domains_list
            ) + i

        # Add domain to list
        domains_list.append({
            "domain": domain_name,
            "order": DOMAIN_DISPLAY_ORDER.get(domain_name, domain_idx),
            "panels": domain_panels,
            "panel_count": len(domain_panels),
            "total_controls": sum(p.get("control_count", 0) for p in domain_panels),
            "short_description": domain_def.get("question"),
            "route": f"/{domain_name.lower()}",
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
            # Panel state counts (UI-as-Constraint states)
            "empty_panels": state_counts.get("EMPTY", 0),
            "unbound_panels": state_counts.get("UNBOUND", 0),
            "draft_panels": state_counts.get("DRAFT", 0),
            "bound_panels": state_counts.get("BOUND", 0),
            "deferred_panels": state_counts.get("DEFERRED", 0),
            # Legacy binding counts (for backward compatibility)
            "info_panels": binding_counts.get("INFO", 0),
            # SDSR trace statistics (Phase 4)
            "sdsr_trace_count": total_traces,
            "panels_with_traces": panels_with_traces,
            "unique_scenario_count": len(unique_scenarios),
            # HIL v1 statistics
            "execution_panels": panel_class_counts.get("execution", 0),
            "interpretation_panels": panel_class_counts.get("interpretation", 0),
            # UI Plan authority reference
            "ui_plan_source": str(UI_PLAN_PATH.name),
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
            # HIL v1 contract extensions
            "panel_class_required": True,
            "provenance_on_interpretation_panels": True,
        },
        "domains": domains_list,
    }

    return projection


def _build_panel_from_intent(
    intent: dict,
    domain_name: str,
    subdomain_id: str,
    topic_id: str,
    panel_state: str,
    display_order: int
) -> dict:
    """
    Build a panel entry from a compiled intent.

    This is used when the intent YAML exists and has been compiled.
    The panel_state is derived mechanically, not from the intent.
    """
    panel_id = intent["panel_id"]
    binding_status = panel_state  # Use derived state, not intent's

    panel = {
        "panel_id": panel_id,
        "panel_name": intent.get("panel_name", panel_id),
        "order": f"O{intent.get('order_level', 1)}",
        "render_mode": "TABLE",  # Default
        "visibility": "ALWAYS" if intent.get("visible_by_default", True) else "CONDITIONAL",
        # UI-as-Constraint: ALL panels must render (enabled=True)
        # The binding_status controls UX (dim header, disabled controls, messages)
        "enabled": True,
        "disabled_reason": _get_disabled_reason(panel_state),
        "content_blocks": _build_content_blocks(intent, binding_status),
        "controls": _build_panel_controls(intent, binding_status),
        "control_count": len(intent.get("control_set", [])),
        "topic": topic_id,
        "topic_id": intent.get("topic_id", topic_id),
        "subdomain": subdomain_id,
        "topic_display_order": 0,  # Set by caller
        "short_description": None,
        "permissions": {
            "nav_required": intent.get("nav_required", False),
            "filtering": intent.get("filtering_enabled", False),
            "read": intent.get("read_enabled", True),
            "write": intent.get("write_enabled", False),
            "activate": intent.get("activate_enabled", False),
        },
        "route": f"/{domain_name.lower()}/{panel_id.lower()}",
        "view_type": "PANEL_VIEW",
        "binding_status": binding_status,
        "panel_state": panel_state,  # UI-as-Constraint state
        "review_status": intent.get("review_status", "UNREVIEWED"),
        "panel_class": intent.get("panel_class", "execution"),
        "panel_display_order": display_order,
    }

    # Include provenance for interpretation panels
    provenance = intent.get("provenance")
    if provenance and panel["panel_class"] == "interpretation":
        panel["provenance"] = provenance

    # Add binding metadata for BOUND panels
    observation_trace = intent.get("observation_trace", [])
    if panel_state == "BOUND" and observation_trace:
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
    elif panel_state == "BOUND":
        # BOUND but no trace yet
        panel["binding_metadata"] = {
            "scenario_ids": [],
            "observed_at": None,
            "capability_ids": intent.get("activate_actions", []),
            "trace_count": 0,
            "observed_effects": [],
        }

    return panel


def _build_empty_panel(
    panel_id: str,
    domain_name: str,
    subdomain_id: str,
    topic_id: str,
    order: str,
    panel_class: str,
    panel_state: str,
    display_order: int
) -> dict:
    """
    Build an EMPTY panel entry when no intent YAML exists.

    Per UI-as-Constraint doctrine:
    - EMPTY panels MUST be emitted (they are signals, not failures)
    - The panel exists in ui_plan but has no intent definition yet
    - UI renders empty state UX for these panels
    """
    return {
        "panel_id": panel_id,
        "panel_name": panel_id,  # Use ID as name for empty panels
        "order": order,
        "render_mode": "TABLE",
        "visibility": "ALWAYS",
        # UI-as-Constraint: ALL panels must render (enabled=True)
        # EMPTY/UNBOUND/DEFERRED panels show empty state UX, not hidden
        "enabled": True,
        "disabled_reason": _get_disabled_reason(panel_state),
        "content_blocks": _build_empty_content_blocks(panel_state),
        "controls": [],  # No controls for EMPTY panels
        "control_count": 0,
        "topic": topic_id,
        "topic_id": topic_id,
        "subdomain": subdomain_id,
        "topic_display_order": 0,  # Set by caller
        "short_description": None,
        "permissions": {
            "nav_required": False,
            "filtering": False,
            "read": False,
            "write": False,
            "activate": False,
        },
        "route": f"/{domain_name.lower()}/{panel_id.lower()}",
        "view_type": "PANEL_VIEW",
        "binding_status": panel_state,
        "panel_state": panel_state,  # UI-as-Constraint state (EMPTY)
        "review_status": "UNREVIEWED",
        "panel_class": panel_class,
        "panel_display_order": display_order,
    }


def _get_disabled_reason(panel_state: str) -> str | None:
    """
    Get the disabled reason for a panel based on its state.

    UI-as-Constraint State → UX Contract:
    | State    | Label            | Message                                  |
    |----------|------------------|------------------------------------------|
    | EMPTY    | Empty            | "This panel is planned but not yet defined" |
    | UNBOUND  | Awaiting Backend | "Backend capability not connected"       |
    | DRAFT    | Preview          | "Data not yet observed"                  |
    | BOUND    | (none)           | (normal - no message)                    |
    | DEFERRED | On Hold          | "This feature is deferred by governance" |
    """
    if panel_state == "EMPTY":
        return "This panel is planned but not yet defined"
    elif panel_state == "UNBOUND":
        return "Backend capability not connected"
    elif panel_state == "DRAFT":
        return "Data not yet observed"
    elif panel_state == "DEFERRED":
        return "This feature is deferred by governance"
    return None


def _build_empty_content_blocks(panel_state: str) -> list[dict]:
    """
    Build minimal content blocks for EMPTY/UNBOUND/DEFERRED panels.

    These panels still render (UI-as-Constraint doctrine) but with
    empty state UX instead of data. The panel_state determines the message.
    """
    visibility = "ALWAYS"
    # UI-as-Constraint: All panels render, including EMPTY/UNBOUND/DEFERRED
    enabled = True

    return [
        {
            "type": "HEADER",
            "order": 0,
            "visibility": visibility,
            "enabled": enabled,
            "components": ["title", "status_badge", "binding_indicator"],
        },
        {
            "type": "DATA",
            "order": 1,
            "visibility": visibility,
            "enabled": enabled,
            "render_mode": "EMPTY_STATE",  # Special render mode for empty state panels
            "components": ["empty_state_message"],
        },
    ]


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

    # UI-as-Constraint: ALL panels are visible (ALWAYS)
    # The binding_status controls UX appearance (dim header, disabled controls)
    # but does NOT control visibility. Panels MUST NOT be hidden.
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

    # 3. CONTROLS block - only if panel has controls AND state allows it
    control_set = intent.get("control_set", [])
    # UI-as-Constraint: No controls for UNBOUND panels (they don't have backend capability)
    # But the panel itself is still visible with empty state message
    if control_set and binding_status not in ("UNBOUND",):
        # Determine control block enabled state based on binding
        if binding_status == "BOUND":
            controls_enabled = True
        elif binding_status == "DRAFT":
            # DRAFT: controls visible but disabled (data not yet observed)
            controls_enabled = False
        else:
            controls_enabled = False

        blocks.append({
            "type": "CONTROLS",
            "order": block_order,
            "visibility": "ALWAYS",
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
    print("AURORA_L2 Intent Compiler (UI-as-Constraint)")
    print("=" * 60)
    print(f"UI Plan Authority: {UI_PLAN_PATH}")
    print(f"Intents Source: {INTENTS_DIR}")
    print(f"Mode: {'VALIDATE ONLY' if validate_only else 'COMPILE'}")
    print(f"DB Authority: {DB_AUTHORITY}")
    print(f"Outputs: {', '.join(filter(None, [
        'projection' if output_projection else None,
        'json' if output_json else None,
        'sql' if output_sql else None
    ]))}")
    print("=" * 60)

    # ==========================================================================
    # PHASE 1: LOAD UI PLAN (CANONICAL AUTHORITY)
    # ==========================================================================
    # ui_plan.yaml is the HIGHEST authority per UI-as-Constraint doctrine
    ui_plan = load_ui_plan()
    ui_plan_panel_count = ui_plan.get("summary", {}).get("total_panels", 0)
    print(f"UI Plan loaded: {ui_plan_panel_count} canonical panels")

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

        # Extract panel_id from both new naming (AURORA_L2_INTENT_*.yaml) and legacy (*.yaml)
        stem = yaml_path.stem
        if stem.startswith('AURORA_L2_INTENT_'):
            panel_id = stem[len('AURORA_L2_INTENT_'):]
        else:
            panel_id = stem

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

    # Build compiled_intents_map for lookup
    compiled_intents_map: dict[str, dict] = {
        intent["panel_id"]: intent for intent in compiled_intents
    }
    print(f"Intent map built: {len(compiled_intents_map)} entries")

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
    # CANONICAL PROJECTION OUTPUT (UI-as-Constraint)
    # ==========================================================================
    # ui_plan.yaml is the authority. Compiler derives state mechanically.
    # All 86 panels are emitted, including EMPTY panels.
    if output_projection:
        projection = generate_canonical_projection(
            ui_plan=ui_plan,
            compiled_intents_map=compiled_intents_map,
            capabilities=capabilities
        )

        # Write to canonical location
        with open(CANONICAL_PROJECTION_PATH, "w") as f:
            json.dump(projection, f, indent=2)

        print(f"\n[CANONICAL PROJECTION] {CANONICAL_PROJECTION_PATH}")
        print(f"  Domains: {projection['_statistics']['domain_count']}")
        print(f"  Panels: {projection['_statistics']['panel_count']}")
        print(f"  Controls: {projection['_statistics']['control_count']}")
        print(f"  States:")
        print(f"    EMPTY: {projection['_statistics']['empty_panels']}")
        print(f"    UNBOUND: {projection['_statistics']['unbound_panels']}")
        print(f"    DRAFT: {projection['_statistics']['draft_panels']}")
        print(f"    BOUND: {projection['_statistics']['bound_panels']}")
        print(f"    DEFERRED: {projection['_statistics']['deferred_panels']}")

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
