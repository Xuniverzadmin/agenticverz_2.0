#!/usr/bin/env python3
"""
DEPRECATED - DO NOT USE (2026-01-15)

Reason: Contains hardcoded ENDPOINT_MAP with semantically incorrect mappings.
        - Activity panels mapped to Founder Console endpoints (/api/v1/discovery)
        - Activity panels mapped to wrong domains (/api/v1/agents, /health)

SDSR verifies TECHNICAL correctness (endpoint exists, returns 200).
SDSR does NOT verify SEMANTIC correctness (is this the RIGHT endpoint for this panel?).

The ENDPOINT_MAP was manually curated and contains errors that SDSR cannot detect.

Replacement: Use manual HISAR panel-by-panel with human-verified endpoints:
    1. Human curates capability.endpoint in Intent YAML
    2. aurora_intent_scaffold.py --panel <id> --endpoint <correct_endpoint>
    3. run_hisar.sh <panel_id>

DO NOT IMPORT THIS FILE.
DO NOT USE ENDPOINT_MAP.
DO NOT RUN aurora_full_sweep.py.

Reference: Session 2026-01-15, ENDPOINT_MAP curation problem discovery.

=============================================================================
ORIGINAL DOCSTRING (preserved for reference):
AURORA L2 Full HISAR Sweep
Runs HISAR pipeline for all panels in ui_plan.yaml
=============================================================================
"""

import sys
print("=" * 70, file=sys.stderr)
print("DEPRECATED: aurora_full_sweep.py", file=sys.stderr)
print("This script contains hardcoded ENDPOINT_MAP with incorrect mappings.", file=sys.stderr)
print("Use manual HISAR panel-by-panel instead.", file=sys.stderr)
print("=" * 70, file=sys.stderr)
sys.exit(1)

import os
import sys
import yaml
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Paths
SCRIPT_DIR = Path(__file__).parent
ROOT_DIR = SCRIPT_DIR.parent.parent.parent
DESIGN_DIR = ROOT_DIR / "design" / "l2_1"
INTENTS_DIR = DESIGN_DIR / "intents"
UI_PLAN = DESIGN_DIR / "ui_plan.yaml"

# Panel to endpoint mapping (based on routes cache analysis)
ENDPOINT_MAP = {
    # OVERVIEW - Cost Intelligence
    "OVR-SUM-CI-O1": ("/cost/summary", "overview.cost_summary"),
    "OVR-SUM-CI-O2": ("/cost/by-feature", "overview.cost_by_feature"),
    "OVR-SUM-CI-O3": ("/cost/by-model", "overview.cost_by_model"),
    "OVR-SUM-CI-O4": ("/cost/anomalies", "overview.cost_anomalies"),
    # OVERVIEW - Decisions
    "OVR-SUM-DC-O1": ("/founder/timeline/decisions", "overview.decisions_list"),
    "OVR-SUM-DC-O2": ("/founder/timeline/count", "overview.decisions_count"),
    "OVR-SUM-DC-O3": ("/api/v1/recovery/stats", "overview.recovery_stats"),
    "OVR-SUM-DC-O4": ("/api/v1/feedback/stats/summary", "overview.feedback_summary"),
    # ACTIVITY - Completed
    "ACT-LLM-COMP-O1": ("/api/v1/activity/runs", "activity.runs_list"),
    "ACT-LLM-COMP-O2": ("/api/v1/activity/summary", "activity.summary"),
    "ACT-LLM-COMP-O3": ("/api/v1/tenants/runs", "activity.tenant_runs"),
    "ACT-LLM-COMP-O4": ("/api/v1/customer/activity", "activity.customer_activity"),
    "ACT-LLM-COMP-O5": ("/api/v1/runtime/traces", "activity.runtime_traces"),
    # ACTIVITY - Live
    "ACT-LLM-LIVE-O1": ("/api/v1/activity/runs", "activity.live_runs"),  # filtered
    "ACT-LLM-LIVE-O2": ("/api/v1/agents/agents", "activity.live_agents"),
    "ACT-LLM-LIVE-O3": ("/api/v1/agents/jobs", "activity.jobs_list"),
    "ACT-LLM-LIVE-O4": ("/api/v1/workers/business-builder/runs", "activity.worker_runs"),
    "ACT-LLM-LIVE-O5": ("/health", "activity.health_status"),
    # ACTIVITY - Signals
    "ACT-LLM-SIG-O1": ("/api/v1/feedback", "activity.feedback_list"),
    "ACT-LLM-SIG-O2": ("/api/v1/predictions", "activity.predictions_list"),
    "ACT-LLM-SIG-O3": ("/api/v1/predictions/stats/summary", "activity.predictions_summary"),
    "ACT-LLM-SIG-O4": ("/api/v1/discovery", "activity.discovery_list"),
    "ACT-LLM-SIG-O5": ("/api/v1/discovery/stats", "activity.discovery_stats"),
    # INCIDENTS - Active
    "INC-EV-ACT-O1": ("/api/v1/incidents", "incidents.list"),
    "INC-EV-ACT-O2": ("/api/v1/incidents/summary", "incidents.summary"),
    "INC-EV-ACT-O3": ("/api/v1/incidents/metrics", "incidents.metrics"),
    "INC-EV-ACT-O4": ("/api/v1/ops/incidents/patterns", "incidents.patterns"),
    "INC-EV-ACT-O5": ("/api/v1/ops/incidents/infra-summary", "incidents.infra_summary"),
    # INCIDENTS - Historical
    "INC-EV-HIST-O1": ("/api/v1/incidents", "incidents.historical_list"),
    "INC-EV-HIST-O2": ("/api/v1/guard/incidents", "incidents.guard_list"),
    "INC-EV-HIST-O3": ("/v1/incidents", "incidents.v1_list"),
    "INC-EV-HIST-O4": ("/api/v1/ops/incidents", "incidents.ops_list"),
    "INC-EV-HIST-O5": ("/integration/stats", "incidents.integration_stats"),
    # INCIDENTS - Resolved
    "INC-EV-RES-O1": ("/api/v1/incidents", "incidents.resolved_list"),
    "INC-EV-RES-O2": ("/api/v1/recovery/actions", "incidents.recovery_actions"),
    "INC-EV-RES-O3": ("/api/v1/recovery/candidates", "incidents.recovery_candidates"),
    "INC-EV-RES-O4": ("/integration/graduation", "incidents.graduation_list"),
    "INC-EV-RES-O5": ("/replay/{incident_id}/summary", "incidents.replay_summary"),
    # POLICIES - Active
    "POL-GOV-ACT-O1": ("/api/v1/policy-proposals", "policies.proposals_list"),
    "POL-GOV-ACT-O2": ("/api/v1/policy-proposals/stats/summary", "policies.proposals_summary"),
    "POL-GOV-ACT-O3": ("/api/v1/policies/requests", "policies.requests_list"),
    "POL-GOV-ACT-O4": ("/policy-layer/state", "policies.layer_state"),
    "POL-GOV-ACT-O5": ("/policy-layer/metrics", "policies.layer_metrics"),
    # POLICIES - Drafts
    "POL-GOV-DFT-O1": ("/api/v1/policy-proposals", "policies.drafts_list"),
    "POL-GOV-DFT-O2": ("/policy-layer/versions", "policies.versions_list"),
    "POL-GOV-DFT-O3": ("/policy-layer/versions/current", "policies.current_version"),
    "POL-GOV-DFT-O4": ("/policy-layer/conflicts", "policies.conflicts_list"),
    "POL-GOV-DFT-O5": ("/policy-layer/dependencies", "policies.dependencies_list"),
    # POLICIES - Library
    "POL-GOV-LIB-O1": ("/policy-layer/safety-rules", "policies.safety_rules"),
    "POL-GOV-LIB-O2": ("/policy-layer/ethical-constraints", "policies.ethical_constraints"),
    "POL-GOV-LIB-O3": ("/v1/policies/active", "policies.active_policies"),
    "POL-GOV-LIB-O4": ("/guard/policies", "policies.guard_policies"),
    "POL-GOV-LIB-O5": ("/policy-layer/temporal-policies", "policies.temporal_policies"),
    # POLICIES - Thresholds
    "POL-LIM-THR-O1": ("/policy-layer/risk-ceilings", "policies.risk_ceilings"),
    "POL-LIM-THR-O2": ("/cost/budgets", "policies.budgets_list"),
    "POL-LIM-THR-O3": ("/api/v1/tenants/tenant/quota/runs", "policies.quota_runs"),
    "POL-LIM-THR-O4": ("/api/v1/tenants/tenant/quota/tokens", "policies.quota_tokens"),
    "POL-LIM-THR-O5": ("/policy-layer/cooldowns", "policies.cooldowns_list"),
    # POLICIES - Usage
    "POL-LIM-USG-O1": ("/api/v1/tenants/tenant/usage", "policies.tenant_usage"),
    "POL-LIM-USG-O2": ("/cost/dashboard", "policies.cost_dashboard"),
    "POL-LIM-USG-O3": ("/cost/by-user", "policies.cost_by_user"),
    "POL-LIM-USG-O4": ("/cost/projection", "policies.cost_projection"),
    "POL-LIM-USG-O5": ("/billing/status", "policies.billing_status"),
    # POLICIES - Violations
    "POL-LIM-VIO-O1": ("/policy-layer/violations", "policies.violations_list"),
    "POL-LIM-VIO-O2": ("/guard/costs/incidents", "policies.cost_incidents"),
    "POL-LIM-VIO-O3": ("/costsim/v2/incidents", "policies.simulated_incidents"),
    "POL-LIM-VIO-O4": ("/cost/anomalies", "policies.anomalies_list"),
    "POL-LIM-VIO-O5": ("/costsim/divergence", "policies.divergence_report"),
    # LOGS - Audit
    "LOG-REC-AUD-O1": ("/api/v1/traces", "logs.traces_list"),
    "LOG-REC-AUD-O2": ("/api/v1/rbac/audit", "logs.rbac_audit"),
    "LOG-REC-AUD-O3": ("/ops/actions/audit", "logs.ops_audit"),
    "LOG-REC-AUD-O4": ("/status_history", "logs.status_history"),
    "LOG-REC-AUD-O5": ("/status_history/stats", "logs.status_stats"),
    # LOGS - LLM Runs
    "LOG-REC-LLM-O1": ("/api/v1/runtime/traces", "logs.runtime_traces"),
    "LOG-REC-LLM-O2": ("/api/v1/activity/runs", "logs.activity_runs"),
    "LOG-REC-LLM-O3": ("/api/v1/customer/activity", "logs.customer_runs"),
    "LOG-REC-LLM-O4": ("/api/v1/tenants/runs", "logs.tenant_runs"),
    "LOG-REC-LLM-O5": ("/api/v1/traces/mismatches/bulk-report", "logs.mismatch_report"),
    # LOGS - System
    "LOG-REC-SYS-O1": ("/guard/logs", "logs.guard_logs"),
    "LOG-REC-SYS-O2": ("/health", "logs.health_check"),
    "LOG-REC-SYS-O3": ("/health/ready", "logs.ready_check"),
    "LOG-REC-SYS-O4": ("/health/adapters", "logs.adapters_health"),
    "LOG-REC-SYS-O5": ("/health/skills", "logs.skills_health"),
}

# Panel metadata templates
PANEL_NAMES = {
    # Overview
    "OVR-SUM-CI-O1": "Cost Summary",
    "OVR-SUM-CI-O2": "Cost by Feature",
    "OVR-SUM-CI-O3": "Cost by Model",
    "OVR-SUM-CI-O4": "Cost Anomalies",
    "OVR-SUM-DC-O1": "Decisions List",
    "OVR-SUM-DC-O2": "Decisions Count",
    "OVR-SUM-DC-O3": "Recovery Stats",
    "OVR-SUM-DC-O4": "Feedback Summary",
    # Activity
    "ACT-LLM-COMP-O1": "Completed Runs List",
    "ACT-LLM-COMP-O2": "Activity Summary",
    "ACT-LLM-COMP-O3": "Tenant Runs",
    "ACT-LLM-COMP-O4": "Customer Activity",
    "ACT-LLM-COMP-O5": "Runtime Traces",
    "ACT-LLM-LIVE-O1": "Live Runs",
    "ACT-LLM-LIVE-O2": "Active Agents",
    "ACT-LLM-LIVE-O3": "Jobs Queue",
    "ACT-LLM-LIVE-O4": "Worker Runs",
    "ACT-LLM-LIVE-O5": "Health Status",
    "ACT-LLM-SIG-O1": "Feedback List",
    "ACT-LLM-SIG-O2": "Predictions List",
    "ACT-LLM-SIG-O3": "Predictions Summary",
    "ACT-LLM-SIG-O4": "Discovery List",
    "ACT-LLM-SIG-O5": "Discovery Stats",
    # Incidents
    "INC-EV-ACT-O1": "Active Incidents",
    "INC-EV-ACT-O2": "Incidents Summary",
    "INC-EV-ACT-O3": "Incidents Metrics",
    "INC-EV-ACT-O4": "Incident Patterns",
    "INC-EV-ACT-O5": "Infrastructure Summary",
    "INC-EV-HIST-O1": "Historical Incidents",
    "INC-EV-HIST-O2": "Guard Incidents",
    "INC-EV-HIST-O3": "V1 Incidents",
    "INC-EV-HIST-O4": "Ops Incidents",
    "INC-EV-HIST-O5": "Integration Stats",
    "INC-EV-RES-O1": "Resolved Incidents",
    "INC-EV-RES-O2": "Recovery Actions",
    "INC-EV-RES-O3": "Recovery Candidates",
    "INC-EV-RES-O4": "Graduation List",
    "INC-EV-RES-O5": "Replay Summary",
    # Policies
    "POL-GOV-ACT-O1": "Policy Proposals",
    "POL-GOV-ACT-O2": "Proposals Summary",
    "POL-GOV-ACT-O3": "Policy Requests",
    "POL-GOV-ACT-O4": "Policy Layer State",
    "POL-GOV-ACT-O5": "Policy Metrics",
    "POL-GOV-DFT-O1": "Draft Proposals",
    "POL-GOV-DFT-O2": "Policy Versions",
    "POL-GOV-DFT-O3": "Current Version",
    "POL-GOV-DFT-O4": "Policy Conflicts",
    "POL-GOV-DFT-O5": "Policy Dependencies",
    "POL-GOV-LIB-O1": "Safety Rules",
    "POL-GOV-LIB-O2": "Ethical Constraints",
    "POL-GOV-LIB-O3": "Active Policies",
    "POL-GOV-LIB-O4": "Guard Policies",
    "POL-GOV-LIB-O5": "Temporal Policies",
    "POL-LIM-THR-O1": "Risk Ceilings",
    "POL-LIM-THR-O2": "Budget List",
    "POL-LIM-THR-O3": "Run Quotas",
    "POL-LIM-THR-O4": "Token Quotas",
    "POL-LIM-THR-O5": "Cooldowns",
    "POL-LIM-USG-O1": "Tenant Usage",
    "POL-LIM-USG-O2": "Cost Dashboard",
    "POL-LIM-USG-O3": "Cost by User",
    "POL-LIM-USG-O4": "Cost Projection",
    "POL-LIM-USG-O5": "Billing Status",
    "POL-LIM-VIO-O1": "Violations List",
    "POL-LIM-VIO-O2": "Cost Incidents",
    "POL-LIM-VIO-O3": "Simulated Incidents",
    "POL-LIM-VIO-O4": "Anomalies List",
    "POL-LIM-VIO-O5": "Divergence Report",
    # Logs
    "LOG-REC-AUD-O1": "Execution Traces",
    "LOG-REC-AUD-O2": "RBAC Audit",
    "LOG-REC-AUD-O3": "Ops Audit",
    "LOG-REC-AUD-O4": "Status History",
    "LOG-REC-AUD-O5": "Status Stats",
    "LOG-REC-LLM-O1": "Runtime Traces",
    "LOG-REC-LLM-O2": "Activity Runs",
    "LOG-REC-LLM-O3": "Customer Runs",
    "LOG-REC-LLM-O4": "Tenant Runs",
    "LOG-REC-LLM-O5": "Mismatch Report",
    "LOG-REC-SYS-O1": "Guard Logs",
    "LOG-REC-SYS-O2": "Health Check",
    "LOG-REC-SYS-O3": "Ready Check",
    "LOG-REC-SYS-O4": "Adapters Health",
    "LOG-REC-SYS-O5": "Skills Health",
}


def load_ui_plan() -> Dict:
    """Load ui_plan.yaml"""
    with open(UI_PLAN) as f:
        return yaml.safe_load(f)


def get_all_panels(ui_plan: Dict) -> List[str]:
    """Extract all panel IDs from ui_plan"""
    panels = []
    for domain in ui_plan.get("domains", []):
        for subdomain in domain.get("subdomains", []):
            for topic in subdomain.get("topics", []):
                for panel in topic.get("panels", []):
                    panels.append(panel["panel_id"])
    return panels


def get_panel_state(ui_plan: Dict, panel_id: str) -> str:
    """Get current state of a panel"""
    for domain in ui_plan.get("domains", []):
        for subdomain in domain.get("subdomains", []):
            for topic in subdomain.get("topics", []):
                for panel in topic.get("panels", []):
                    if panel["panel_id"] == panel_id:
                        return panel.get("state", "EMPTY")
    return "UNKNOWN"


def load_env_vars() -> Dict[str, str]:
    """Load environment variables from .env file"""
    env = os.environ.copy()
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key] = value
    return env


def run_command(cmd: List[str], cwd: str = None) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr"""
    try:
        # Load env vars including AOS_API_KEY
        env = load_env_vars()
        result = subprocess.run(
            cmd,
            cwd=cwd or str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)


def create_intent_yaml(panel_id: str) -> bool:
    """Create intent YAML if it doesn't exist"""
    intent_file = INTENTS_DIR / f"{panel_id}.yaml"
    if intent_file.exists():
        return True

    if panel_id not in ENDPOINT_MAP:
        print(f"  ⚠️  No endpoint mapping for {panel_id}")
        return False

    endpoint, capability_id = ENDPOINT_MAP[panel_id]
    panel_name = PANEL_NAMES.get(panel_id, f"Panel {panel_id}")

    # Parse panel ID for metadata
    parts = panel_id.split("-")
    domain = parts[0]
    subdomain = parts[1]
    topic = parts[2]
    order = parts[3]

    domain_map = {"OVR": "OVERVIEW", "ACT": "ACTIVITY", "INC": "INCIDENTS", "POL": "POLICIES", "LOG": "LOGS"}

    intent = {
        "panel_id": panel_id,
        "version": "1.0.0",
        "panel_class": "evidence",
        "metadata": {
            "domain": domain_map.get(domain, domain),
            "subdomain": subdomain,
            "topic": topic,
            "topic_id": f"{domain_map.get(domain, domain)}.{subdomain}.{topic}",
            "order": order,
            "action_layer": "L2_1",
            "source": "HISAR_PIPELINE",
            "review_status": "PENDING"
        },
        "display": {
            "name": panel_name,
            "visible_by_default": True,
            "nav_required": False,
            "expansion_mode": "INLINE"
        },
        "data": {
            "read": True,
            "download": False,
            "write": False,
            "replay": True
        },
        "controls": {
            "filtering": True,
            "activate": False,
            "confirmation_required": False
        },
        "capability": {
            "id": capability_id,
            "status": "DECLARED",
            "endpoint": endpoint,
            "method": "GET",
            "data_mapping": {
                "items": "items",
                "total": "total"
            }
        },
        "sdsr": {
            "scenario": f"SDSR-{panel_id}-001",
            "verified": False,
            "verification_date": None,
            "checks": {
                "endpoint_exists": "PENDING",
                "schema_matches": "PENDING",
                "auth_works": "PENDING",
                "data_is_real": "PENDING"
            }
        },
        "notes": f"Auto-generated intent for {panel_name}. Endpoint: {endpoint}"
    }

    # Create intent file
    intent_file.parent.mkdir(parents=True, exist_ok=True)
    with open(intent_file, "w") as f:
        yaml.dump(intent, f, default_flow_style=False, sort_keys=False)

    return True


def run_hisar_for_panel(panel_id: str) -> Dict:
    """Run full HISAR pipeline for a single panel"""
    result = {
        "panel_id": panel_id,
        "phases": {},
        "status": "UNKNOWN",
        "gap": None,
        "invariants": None
    }

    # Phase 1: Intent
    if not create_intent_yaml(panel_id):
        result["status"] = "SKIPPED"
        result["gap"] = "NO_ENDPOINT_MAPPING"
        return result

    result["phases"]["intent"] = "CREATED"

    # Phase 2: Registry sync
    code, out, err = run_command(
        ["python3", "aurora_intent_registry_sync.py", "--panel", panel_id]
    )
    if code != 0:
        result["phases"]["registry_sync"] = "FAILED"
        result["status"] = "FAILED"
        result["gap"] = "REGISTRY_SYNC_FAILED"
        return result
    result["phases"]["registry_sync"] = "PASS"

    # Approve
    code, out, err = run_command(
        ["python3", "aurora_intent_registry_sync.py", "--approve", panel_id]
    )
    result["phases"]["approve"] = "PASS" if code == 0 else "FAILED"

    # Phase 3: Capability scaffold
    # Check if capability already exists
    if panel_id in ENDPOINT_MAP:
        _, cap_id = ENDPOINT_MAP[panel_id]
        cap_file = ROOT_DIR / "backend" / "AURORA_L2_CAPABILITY_REGISTRY" / f"AURORA_L2_CAPABILITY_{cap_id}.yaml"
        if cap_file.exists():
            result["phases"]["capability"] = "EXISTS"
        else:
            code, out, err = run_command(
                ["python3", "aurora_capability_scaffold.py", "--panel", panel_id]
            )
            if code != 0:
                result["phases"]["capability"] = "FAILED"
                result["status"] = "FAILED"
                result["gap"] = "CAPABILITY_SCAFFOLD_FAILED"
                return result
            result["phases"]["capability"] = "PASS"
    else:
        result["phases"]["capability"] = "SKIP"

    # Phase 3.5: Coherency check
    code, out, err = run_command(
        ["python3", "aurora_coherency_check.py", "--panel", panel_id]
    )
    if code != 0:
        # Check if route doesn't exist
        if "Backend route" in err or "not found" in err.lower():
            result["phases"]["coherency"] = "FAILED"
            result["status"] = "BLOCKED"
            result["gap"] = "ENDPOINT_MISSING"
            return result
        result["phases"]["coherency"] = "FAILED"
        result["status"] = "BLOCKED"
        result["gap"] = "COHERENCY_FAILED"
        return result
    result["phases"]["coherency"] = "PASS"

    # Phase 4: SDSR synth
    # Check if scenario already exists
    scenario_file = ROOT_DIR / "backend" / "scripts" / "sdsr" / "scenarios" / f"SDSR-{panel_id}-001.yaml"
    if scenario_file.exists():
        result["phases"]["sdsr_synth"] = "EXISTS"
    else:
        code, out, err = run_command(
            ["python3", "aurora_sdsr_synth.py", "--panel", panel_id]
        )
        if code != 0:
            result["phases"]["sdsr_synth"] = "FAILED"
            result["status"] = "BLOCKED"
            result["gap"] = "SDSR_SYNTH_FAILED"
            return result
        result["phases"]["sdsr_synth"] = "PASS"

    # Phase 4b: SDSR run
    code, out, err = run_command(
        ["python3", "aurora_sdsr_runner.py", "--panel", panel_id]
    )

    # Parse SDSR result
    if "SDSR PASSED" in out:
        result["phases"]["sdsr_run"] = "PASS"
        # Parse invariants
        if "Invariants:" in out:
            for line in out.split("\n"):
                if "Invariants:" in line:
                    result["invariants"] = line.split("Invariants:")[1].strip().split()[0]
                    break

        # Apply observation
        code2, out2, err2 = run_command(
            ["python3", "aurora_apply_observation.py", "--observation",
             f"SDSR_OBSERVATION_{ENDPOINT_MAP.get(panel_id, ('', panel_id))[1]}.json"]
        )
        if code2 == 0:
            result["phases"]["apply_obs"] = "PASS"
            # Bind UI plan
            code3, out3, err3 = run_command(
                ["python3", "aurora_ui_plan_bind.py", "--panel", panel_id]
            )
            result["phases"]["bind"] = "PASS" if code3 == 0 else "FAILED"
            result["status"] = "BOUND"
        else:
            result["phases"]["apply_obs"] = "FAILED"
            result["status"] = "BLOCKED"
            result["gap"] = "OBSERVATION_APPLY_FAILED"
    else:
        result["phases"]["sdsr_run"] = "FAILED"
        result["status"] = "BLOCKED"

        # Determine gap type
        if "401" in out or "AUTH_FAILURE" in out:
            result["gap"] = "AUTH_FAILURE"
        elif "404" in out or "not found" in out.lower():
            result["gap"] = "ENDPOINT_MISSING"
        elif "PROVENANCE" in out.upper():
            result["gap"] = "PROVENANCE_MISSING"
        elif "schema" in out.lower() or "SCHEMA" in out:
            result["gap"] = "SCHEMA_MISMATCH"
        else:
            result["gap"] = "SDSR_FAILED"

        # Parse invariants
        if "Invariants:" in out:
            for line in out.split("\n"):
                if "Invariants:" in line:
                    result["invariants"] = line.split("Invariants:")[1].strip().split()[0]
                    break

    return result


def run_full_sweep():
    """Run HISAR for all panels"""
    print("=" * 70)
    print("AURORA L2 FULL HISAR SWEEP")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)

    # Load UI plan
    ui_plan = load_ui_plan()
    all_panels = get_all_panels(ui_plan)

    # Skip already bound panels from HIGHLIGHTS (known to be bound)
    bound_panels = {"OVR-SUM-HL-O1", "OVR-SUM-HL-O2", "OVR-SUM-HL-O3", "OVR-SUM-HL-O4"}

    results = {
        "sweep_date": datetime.now().isoformat(),
        "total_panels": len(all_panels),
        "panels": {},
        "summary": {
            "BOUND": [],
            "BLOCKED": [],
            "SKIPPED": [],
            "FAILED": []
        },
        "gaps": {}
    }

    # Group by domain for organized output
    domains = {}
    for panel in all_panels:
        domain = panel.split("-")[0]
        if domain not in domains:
            domains[domain] = []
        domains[domain].append(panel)

    for domain, panels in domains.items():
        print(f"\n{'=' * 50}")
        print(f"DOMAIN: {domain}")
        print(f"{'=' * 50}")

        for panel_id in panels:
            # Check current state
            current_state = get_panel_state(ui_plan, panel_id)

            if current_state == "BOUND":
                print(f"  ✓ {panel_id}: Already BOUND")
                results["panels"][panel_id] = {"status": "BOUND", "gap": None}
                results["summary"]["BOUND"].append(panel_id)
                continue

            if panel_id in bound_panels:
                print(f"  ✓ {panel_id}: Pre-bound (HIGHLIGHTS)")
                results["panels"][panel_id] = {"status": "BOUND", "gap": None}
                results["summary"]["BOUND"].append(panel_id)
                continue

            print(f"\n  ▶ {panel_id}...")

            result = run_hisar_for_panel(panel_id)
            results["panels"][panel_id] = result

            if result["status"] == "BOUND":
                print(f"    ✅ BOUND ({result.get('invariants', 'N/A')} invariants)")
                results["summary"]["BOUND"].append(panel_id)
            elif result["status"] == "BLOCKED":
                print(f"    ❌ BLOCKED: {result.get('gap', 'UNKNOWN')}")
                results["summary"]["BLOCKED"].append(panel_id)
                gap = result.get("gap", "UNKNOWN")
                if gap not in results["gaps"]:
                    results["gaps"][gap] = []
                results["gaps"][gap].append(panel_id)
            elif result["status"] == "SKIPPED":
                print(f"    ⏭️  SKIPPED: {result.get('gap', 'UNKNOWN')}")
                results["summary"]["SKIPPED"].append(panel_id)
            else:
                print(f"    ⚠️  FAILED: {result.get('gap', 'UNKNOWN')}")
                results["summary"]["FAILED"].append(panel_id)

    # Write results
    results_file = SCRIPT_DIR / "sweep_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("\n" + "=" * 70)
    print("SWEEP SUMMARY")
    print("=" * 70)
    print(f"Total Panels: {results['total_panels']}")
    print(f"  BOUND:   {len(results['summary']['BOUND'])}")
    print(f"  BLOCKED: {len(results['summary']['BLOCKED'])}")
    print(f"  SKIPPED: {len(results['summary']['SKIPPED'])}")
    print(f"  FAILED:  {len(results['summary']['FAILED'])}")

    print("\nGaps by Type:")
    for gap_type, panels in results["gaps"].items():
        print(f"  {gap_type}: {len(panels)} panels")

    print(f"\nResults written to: {results_file}")

    return results


if __name__ == "__main__":
    run_full_sweep()
