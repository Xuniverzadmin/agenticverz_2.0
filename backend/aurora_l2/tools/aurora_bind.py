#!/usr/bin/env python3
"""
AURORA L2 Bind Orchestrator

Single command that orchestrates the entire AURORA L2 pipeline
from intent to BOUND panel.

Usage:
    aurora_bind.py OVR-SUM-HL-O2
    aurora_bind.py OVR-SUM-HL-O2 --capability overview.metric_snapshot
    aurora_bind.py OVR-SUM-HL-O2 --continue  # Resume after human approval
    aurora_bind.py OVR-SUM-HL-O2 --status    # Check current status

Pipeline Phases:
    Phase 2: Intent Specification
        - Scaffold intent YAML (if missing)
        - Sync to registry (status=DRAFT)
        - WAIT for human approval (DRAFT → APPROVED)

    Phase 3: Capability Declaration
        - Scaffold capability YAML (status=DECLARED)

    Phase 3.5: Coherency Gate
        - Run coherency checks (COH-001 to COH-010)
        - BLOCK if coherency fails

    Phase 4: SDSR Verification
        - Generate SDSR scenario
        - Execute scenario
        - Emit observation

    Phase 5: Observation Application
        - Apply observation (DECLARED → OBSERVED)
        - Update intent YAML

    Phase 6: Compilation
        - Run AURORA L2 compiler
        - Generate projection

    Phase 7: PDG (if needed)
        - Auto-allowlist safe transitions

Author: AURORA L2 Automation
"""

import yaml
import json
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple
from enum import Enum

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent.parent
TOOLS_DIR = Path(__file__).parent
UI_PLAN = REPO_ROOT / "design/l2_1/ui_plan.yaml"
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
INTENT_REGISTRY = REPO_ROOT / "design/l2_1/AURORA_L2_INTENT_REGISTRY.yaml"
CAPABILITY_REGISTRY = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
SDSR_SCENARIOS_DIR = REPO_ROOT / "backend/scripts/sdsr/scenarios"


class BindPhase(Enum):
    INTENT_SCAFFOLD = "intent_scaffold"
    INTENT_APPROVAL = "intent_approval"
    CAPABILITY_SCAFFOLD = "capability_scaffold"
    COHERENCY_CHECK = "coherency_check"
    SDSR_SYNTHESIS = "sdsr_synthesis"
    SDSR_EXECUTION = "sdsr_execution"
    OBSERVATION_APPLY = "observation_apply"
    COMPILATION = "compilation"
    COMPLETE = "complete"


def run_script(script_name: str, *args) -> Tuple[int, str, str]:
    """Run a tool script and return (returncode, stdout, stderr)."""
    script_path = TOOLS_DIR / script_name
    cmd = [sys.executable, str(script_path)] + list(args)

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))
    return result.returncode, result.stdout, result.stderr


def get_panel_status(panel_id: str) -> Dict:
    """Get current status of a panel across all artifacts."""
    status = {
        'panel_id': panel_id,
        'in_ui_plan': False,
        'intent_exists': False,
        'intent_registry_status': None,
        'capability_exists': False,
        'capability_status': None,
        'capability_id': None,
        'sdsr_scenario_exists': False,
        'observation_exists': False,
        'current_phase': None,
        'next_action': None,
    }

    # Check ui_plan
    if UI_PLAN.exists():
        with open(UI_PLAN) as f:
            ui_plan = yaml.safe_load(f)
        for domain in ui_plan.get('domains', []):
            for subdomain in domain.get('subdomains', []):
                for topic in subdomain.get('topics', []):
                    for panel in topic.get('panels', []):
                        if panel.get('panel_id') == panel_id:
                            status['in_ui_plan'] = True
                            break

    # Check intent YAML (new naming convention with fallback to legacy)
    intent_path = INTENTS_DIR / f"AURORA_L2_INTENT_{panel_id}.yaml"
    if not intent_path.exists():
        intent_path = INTENTS_DIR / f"{panel_id}.yaml"  # Legacy fallback
    if intent_path.exists():
        status['intent_exists'] = True
        with open(intent_path) as f:
            intent = yaml.safe_load(f)
        capability_id = intent.get('capability', {}).get('id')
        if capability_id and not capability_id.startswith('[TODO'):
            status['capability_id'] = capability_id

    # Check intent registry
    if INTENT_REGISTRY.exists():
        with open(INTENT_REGISTRY) as f:
            registry = yaml.safe_load(f) or {}
        if panel_id in registry:
            status['intent_registry_status'] = registry[panel_id].get('status')

    # Check capability YAML
    if status['capability_id']:
        cap_path = CAPABILITY_REGISTRY / f"AURORA_L2_CAPABILITY_{status['capability_id']}.yaml"
        if cap_path.exists():
            status['capability_exists'] = True
            with open(cap_path) as f:
                cap = yaml.safe_load(f)
            status['capability_status'] = cap.get('status')

    # Check SDSR scenario
    scenario_path = SDSR_SCENARIOS_DIR / f"SDSR-{panel_id}-001.yaml"
    status['sdsr_scenario_exists'] = scenario_path.exists()

    # Check observation
    if status['capability_id']:
        obs_path = REPO_ROOT / "backend/scripts/sdsr/observations" / f"SDSR_OBSERVATION_{status['capability_id']}.json"
        status['observation_exists'] = obs_path.exists()

    # Determine current phase and next action
    if not status['in_ui_plan']:
        status['current_phase'] = 'NOT_IN_UI_PLAN'
        status['next_action'] = 'Add panel to ui_plan.yaml first'
    elif not status['intent_exists']:
        status['current_phase'] = BindPhase.INTENT_SCAFFOLD.value
        status['next_action'] = 'Run aurora_bind.py to scaffold intent'
    elif status['intent_registry_status'] != 'APPROVED':
        status['current_phase'] = BindPhase.INTENT_APPROVAL.value
        status['next_action'] = f"Approve intent: aurora_intent_registry_sync.py --approve {panel_id}"
    elif not status['capability_exists']:
        status['current_phase'] = BindPhase.CAPABILITY_SCAFFOLD.value
        status['next_action'] = 'Run aurora_bind.py --continue to scaffold capability'
    elif status['capability_status'] == 'DECLARED':
        if not status['sdsr_scenario_exists']:
            status['current_phase'] = BindPhase.SDSR_SYNTHESIS.value
            status['next_action'] = 'Run aurora_bind.py --continue to generate SDSR scenario'
        else:
            status['current_phase'] = BindPhase.SDSR_EXECUTION.value
            status['next_action'] = 'Run aurora_bind.py --continue to execute SDSR'
    elif status['capability_status'] in ['OBSERVED', 'TRUSTED']:
        status['current_phase'] = BindPhase.COMPLETE.value
        status['next_action'] = 'Panel is BOUND. Run compiler to update projection.'
    else:
        status['current_phase'] = 'UNKNOWN'
        status['next_action'] = 'Check artifacts manually'

    return status


def print_status(status: Dict):
    """Print panel status."""
    print(f"\nPanel Status: {status['panel_id']}")
    print("=" * 60)
    print(f"  In UI Plan:           {'✅' if status['in_ui_plan'] else '❌'}")
    print(f"  Intent YAML:          {'✅' if status['intent_exists'] else '❌'}")
    print(f"  Intent Registry:      {status['intent_registry_status'] or '❌'}")
    print(f"  Capability ID:        {status['capability_id'] or '❌'}")
    print(f"  Capability YAML:      {'✅' if status['capability_exists'] else '❌'}")
    print(f"  Capability Status:    {status['capability_status'] or '❌'}")
    print(f"  SDSR Scenario:        {'✅' if status['sdsr_scenario_exists'] else '❌'}")
    print(f"  Observation:          {'✅' if status['observation_exists'] else '❌'}")
    print()
    print(f"  Current Phase:        {status['current_phase']}")
    print(f"  Next Action:          {status['next_action']}")


def bind_panel(
    panel_id: str,
    capability_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    continue_from: bool = False,
    skip_approval_wait: bool = False,
    dry_run: bool = False,
) -> int:
    """
    Orchestrate binding a panel through all phases.
    Returns exit code.
    """
    print(f"\n{'='*60}")
    print(f"AURORA BIND: {panel_id}")
    print(f"{'='*60}")

    status = get_panel_status(panel_id)

    if not status['in_ui_plan']:
        print(f"\n❌ Panel {panel_id} not found in ui_plan.yaml")
        print("Add the panel to ui_plan.yaml first.")
        return 1

    # Phase 2: Intent Scaffold
    if not status['intent_exists']:
        print(f"\n[Phase 2] Intent Specification")
        print("-" * 40)

        args = ["--panel", panel_id]
        if capability_id:
            args.extend(["--capability", capability_id])
        if endpoint:
            args.extend(["--endpoint", endpoint])
        if dry_run:
            args.append("--dry-run")

        code, stdout, stderr = run_script("aurora_intent_scaffold.py", *args)
        print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

        if code != 0:
            return code

        # Sync to registry
        code, stdout, stderr = run_script("aurora_intent_registry_sync.py", "--panel", panel_id)
        print(stdout)

        status = get_panel_status(panel_id)

    # Check approval
    if status['intent_registry_status'] != 'APPROVED':
        print(f"\n[Phase 2] Intent Approval Required")
        print("-" * 40)
        print(f"Intent created with status: {status['intent_registry_status']}")
        print()
        print("Human action required:")
        print(f"  1. Review: {INTENTS_DIR / f'AURORA_L2_INTENT_{panel_id}.yaml'}")
        print(f"  2. Fill in TODO fields (display.name, capability.id, endpoint, notes)")
        print(f"  3. Approve: python aurora_intent_registry_sync.py --approve {panel_id}")
        print(f"  4. Continue: python aurora_bind.py {panel_id} --continue")

        if not skip_approval_wait:
            return 2  # Waiting for approval

    # Phase 3: Capability Scaffold
    if not status['capability_exists'] and status['capability_id']:
        print(f"\n[Phase 3] Capability Declaration")
        print("-" * 40)

        args = ["--panel", panel_id]
        if dry_run:
            args.append("--dry-run")

        code, stdout, stderr = run_script("aurora_capability_scaffold.py", *args)
        print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

        if code != 0:
            return code

        status = get_panel_status(panel_id)

    # Phase 3.5: Coherency Check
    print(f"\n[Phase 3.5] Coherency Gate")
    print("-" * 40)

    code, stdout, stderr = run_script("aurora_coherency_check.py", "--panel", panel_id)
    print(stdout)

    if code != 0:
        print("\n❌ Coherency gate failed. Fix issues before continuing.")
        return code

    # Phase 4: SDSR Synthesis
    if not status['sdsr_scenario_exists']:
        print(f"\n[Phase 4] SDSR Scenario Synthesis")
        print("-" * 40)

        args = ["--panel", panel_id]
        if dry_run:
            args.append("--dry-run")

        code, stdout, stderr = run_script("aurora_sdsr_synth.py", *args)
        print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

        if code != 0:
            return code

    # Phase 4: SDSR Execution
    if status['capability_status'] in ['DECLARED', 'ASSUMED', None]:
        print(f"\n[Phase 4] SDSR Execution")
        print("-" * 40)

        args = ["--panel", panel_id]
        if dry_run:
            args.append("--dry-run")

        code, stdout, stderr = run_script("aurora_sdsr_runner.py", *args)
        print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

        if code != 0:
            print("\n❌ SDSR verification failed.")
            return code

        status = get_panel_status(panel_id)

    # Phase 5: Apply Observation
    if status['observation_exists'] and status['capability_status'] in ['DECLARED', 'ASSUMED']:
        print(f"\n[Phase 5] Observation Application")
        print("-" * 40)

        args = ["--capability", status['capability_id']]
        if dry_run:
            args.append("--dry-run")

        code, stdout, stderr = run_script("aurora_apply_observation.py", *args)
        print(stdout)
        if stderr:
            print(stderr, file=sys.stderr)

        if code != 0:
            return code

    # Phase 6: Compilation
    print(f"\n[Phase 6] Compilation")
    print("-" * 40)

    if dry_run:
        print("DRY RUN: Would run compiler")
    else:
        # Run compiler
        import os
        env = os.environ.copy()
        env['DB_AUTHORITY'] = 'neon'

        result = subprocess.run(
            [sys.executable, "-m", "backend.aurora_l2.SDSR_UI_AURORA_compiler"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )

        # Show relevant output
        for line in result.stdout.split('\n'):
            if panel_id in line or 'BOUND' in line or 'Compiled' in line or 'OUTPUT' in line:
                print(line)

        if result.returncode != 0:
            print(f"\n⚠️  Compiler returned code {result.returncode}")
            if result.stderr:
                print(result.stderr)

    # Final status
    print(f"\n{'='*60}")
    print("AURORA BIND COMPLETE")
    print(f"{'='*60}")

    final_status = get_panel_status(panel_id)
    print_status(final_status)

    if final_status['capability_status'] in ['OBSERVED', 'TRUSTED']:
        print(f"\n✅ Panel {panel_id} is now BOUND")
        return 0
    else:
        print(f"\n⚠️  Panel not yet BOUND. Check status above.")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="AURORA L2 Bind Orchestrator - Single command to bind a panel"
    )
    parser.add_argument("panel_id", nargs="?", help="Panel ID to bind")
    parser.add_argument("--capability", help="Capability ID (optional)")
    parser.add_argument("--endpoint", help="API endpoint (optional)")
    parser.add_argument("--continue", dest="continue_from", action="store_true",
                        help="Continue after human approval")
    parser.add_argument("--status", action="store_true", help="Show panel status only")
    parser.add_argument("--skip-approval", action="store_true",
                        help="Skip waiting for approval (for already approved)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    args = parser.parse_args()

    if not args.panel_id:
        parser.print_help()
        return 1

    if args.status:
        status = get_panel_status(args.panel_id)
        print_status(status)
        return 0

    return bind_panel(
        panel_id=args.panel_id,
        capability_id=args.capability,
        endpoint=args.endpoint,
        continue_from=args.continue_from,
        skip_approval_wait=args.skip_approval or args.continue_from,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
