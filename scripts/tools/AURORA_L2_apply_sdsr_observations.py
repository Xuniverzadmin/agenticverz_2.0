#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual | post-SDSR
#   Execution: sync
# Role: Apply SDSR observation artifacts to AURORA_L2 capability state
# Reference: CAPABILITY_STATUS_MODEL.yaml v2.0
"""
AURORA_L2 SDSR Observation Applier

Purpose:
---------
Apply SDSR observation artifacts to AURORA_L2 governance state.

This script is the ONLY allowed writer that may advance:
    DECLARED → OBSERVED

Core Invariant:
    Capabilities are not real because backend says so.
    They are real only when the system demonstrates them.

It updates:
- Capability registry YAML (authoritative state transition)
- Intent YAML (observation trace only - append-only provenance)

It does NOT:
- Infer behavior
- Modify projection rules
- Modify compiler logic
- Promote to TRUSTED (that requires governance approval)
- Mutate intent semantics (controls, expansion, ordering)

Usage:
    python3 scripts/tools/AURORA_L2_apply_sdsr_observations.py --observation sdsr/observations/SDSR_OBSERVATION_*.json
    python3 scripts/tools/AURORA_L2_apply_sdsr_observations.py --observation sdsr/observations/SDSR_OBSERVATION_*.json --dry-run
"""

import argparse
import json
import sys
from pathlib import Path

import yaml


# =============================================================================
# CONFIGURATION (EXPLICIT PATHS - NO INFERENCE)
# =============================================================================

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SDSR_OBSERVATION_DIR = REPO_ROOT / "sdsr/observations"
CAPABILITY_REGISTRY_DIR = REPO_ROOT / "backend/AURORA_L2_CAPABILITY_REGISTRY"
INTENTS_DIR = REPO_ROOT / "design/l2_1/intents"
OBSERVATION_SCHEMA_PATH = REPO_ROOT / "sdsr/SDSR_OBSERVATION_SCHEMA.json"

# Only PASSED observations may advance state
REQUIRED_SCENARIO_STATUS = "PASSED"

# Only these transitions are allowed
ALLOWED_TRANSITIONS = {
    "DECLARED": "OBSERVED",  # The only transition this script may perform
}

# =============================================================================
# HELPERS
# =============================================================================

def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def write_yaml(path: Path, data: dict):
    """Write YAML file preserving structure."""
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)


def fatal(msg: str):
    """Print fatal error and exit."""
    print(f"[FATAL] {msg}", file=sys.stderr)
    sys.exit(1)


def warn(msg: str):
    """Print warning."""
    print(f"[WARN] {msg}", file=sys.stderr)


def info(msg: str):
    """Print info message."""
    print(f"[INFO] {msg}")


def success(msg: str):
    """Print success message."""
    print(f"[OK] {msg}")


# =============================================================================
# INTENT TRACE (APPEND-ONLY)
# =============================================================================

def find_intents_using_capability(capability_id: str) -> list[Path]:
    """
    Find all intent YAML files that use a given capability.

    This is a mechanical lookup - no inference.
    Returns paths to intent YAMLs that reference this capability.
    """
    if not INTENTS_DIR.exists():
        return []

    matching_intents = []

    for intent_path in INTENTS_DIR.glob("*.yaml"):
        try:
            intent_yaml = load_yaml(intent_path)

            # Check if this capability is referenced in controls
            controls = intent_yaml.get("controls", {})
            activate_actions = controls.get("activate_actions", [])

            # Check data section for write_action
            data = intent_yaml.get("data", {})
            write_action = data.get("write_action")

            # Collect all actions used by this intent
            actions = list(activate_actions)
            if write_action:
                actions.append(write_action)

            if capability_id in actions:
                matching_intents.append(intent_path)

        except Exception:
            # Skip malformed intent files
            continue

    return matching_intents


def append_intent_observation_trace(
    *,
    intent_yaml_path: Path,
    scenario_id: str,
    observed_on: str,
    capability_id: str,
    observed_effects: list[dict],
    dry_run: bool = False,
) -> bool:
    """
    Append SDSR observation trace to an intent YAML file.

    This function:
      - NEVER mutates intent semantics
      - ONLY appends provenance
      - Is idempotent per (scenario_id, capability_id)

    Returns True if trace was added, False if already exists or error.
    """
    try:
        intent_yaml = load_yaml(intent_yaml_path)
    except Exception as e:
        warn(f"Failed to load intent {intent_yaml_path.name}: {e}")
        return False

    # Get or create observation_trace list
    trace = intent_yaml.setdefault("observation_trace", [])

    # Idempotency guard (same scenario + capability)
    for entry in trace:
        if (
            entry.get("scenario_id") == scenario_id
            and entry.get("capability_id") == capability_id
        ):
            info(f"Intent {intent_yaml_path.name}: trace already exists for {scenario_id}/{capability_id}")
            return False  # already recorded

    # Build trace entry
    trace_entry = {
        "scenario_id": scenario_id,
        "observed_on": observed_on,
        "capability_id": capability_id,
        "observed_effects": observed_effects,
    }

    trace.append(trace_entry)

    if not dry_run:
        write_yaml(intent_yaml_path, intent_yaml)
        info(f"Intent {intent_yaml_path.name}: added observation trace")
    else:
        info(f"[DRY RUN] Would add trace to {intent_yaml_path.name}")

    return True


# =============================================================================
# VALIDATION
# =============================================================================

def validate_observation(obs: dict) -> list[str]:
    """
    Validate observation structure.
    Returns list of error messages (empty if valid).
    """
    errors = []

    if not obs.get("scenario_id"):
        errors.append("Missing scenario_id")

    if obs.get("status") != REQUIRED_SCENARIO_STATUS:
        errors.append(f"Scenario status is '{obs.get('status')}', must be '{REQUIRED_SCENARIO_STATUS}'")

    if not obs.get("observed_at"):
        errors.append("Missing observed_at timestamp")

    capabilities = obs.get("capabilities_observed", [])
    if not capabilities:
        errors.append("No capabilities_observed in observation")

    for i, cap in enumerate(capabilities):
        if not cap.get("capability_id"):
            errors.append(f"capabilities_observed[{i}]: Missing capability_id")
        if not cap.get("observed_effects"):
            errors.append(f"capabilities_observed[{i}]: Missing observed_effects")

    return errors


# =============================================================================
# CORE LOGIC
# =============================================================================

def load_observation(observation_path: Path) -> dict | None:
    """Load and validate observation file. Returns None on error."""
    try:
        obs = json.loads(observation_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        warn(f"Invalid JSON in observation file: {e}")
        return None

    errors = validate_observation(obs)
    if errors:
        for err in errors:
            warn(err)
        return None

    return obs


def apply_observation(observation_path: Path, dry_run: bool) -> bool:
    """
    Apply a single SDSR observation file.

    Returns True if successful, False if errors occurred.
    """
    print("=" * 60)
    info(f"Processing observation: {observation_path.name}")
    print("=" * 60)

    # Load and validate observation
    obs = load_observation(observation_path)
    if obs is None:
        fatal("Observation loading/validation failed")
        return False

    scenario_id = obs["scenario_id"]
    observed_at = obs["observed_at"]
    capabilities = obs["capabilities_observed"]

    info(f"Scenario: {scenario_id}")
    info(f"Observed at: {observed_at}")
    info(f"Capabilities to process: {len(capabilities)}")
    print()

    # Track results
    promoted = []
    skipped = []
    failed = []

    for cap_obs in capabilities:
        result = apply_capability_observation(
            scenario_id=scenario_id,
            observed_at=observed_at,
            cap_obs=cap_obs,
            dry_run=dry_run,
        )

        if result == "promoted":
            promoted.append(cap_obs["capability_id"])
        elif result == "skipped":
            skipped.append(cap_obs["capability_id"])
        else:
            failed.append(cap_obs["capability_id"])

    # Summary
    print()
    print("=" * 60)
    print("OBSERVATION APPLICATION SUMMARY")
    print("=" * 60)
    print(f"Dry run: {dry_run}")
    print(f"Promoted (DECLARED → OBSERVED): {len(promoted)}")
    if promoted:
        for cap in promoted:
            print(f"  - {cap}")

    print(f"Skipped (already OBSERVED or TRUSTED): {len(skipped)}")
    if skipped:
        for cap in skipped:
            print(f"  - {cap}")

    print(f"Failed (invalid state): {len(failed)}")
    if failed:
        for cap in failed:
            print(f"  - {cap}")

    return len(failed) == 0


def apply_capability_observation(
    scenario_id: str,
    observed_at: str,
    cap_obs: dict,
    dry_run: bool,
) -> str:
    """
    Apply observation to a single capability.

    Returns: "promoted", "skipped", or "failed"
    """
    capability_id = cap_obs["capability_id"]

    # Find capability file
    cap_file = CAPABILITY_REGISTRY_DIR / f"AURORA_L2_CAPABILITY_{capability_id}.yaml"

    if not cap_file.exists():
        warn(f"Capability file not found: {cap_file}")
        return "failed"

    # Load current state
    cap_yaml = load_yaml(cap_file)
    current_status = cap_yaml.get("status", "UNKNOWN")

    # Check if transition is allowed
    if current_status in ("OBSERVED", "TRUSTED"):
        info(f"Capability {capability_id}: Already {current_status}, skipping")
        return "skipped"

    if current_status not in ALLOWED_TRANSITIONS:
        warn(f"Capability {capability_id}: Cannot transition from {current_status}")
        warn(f"  Only DECLARED → OBSERVED is allowed")
        warn(f"  Current status: {current_status}")
        return "failed"

    target_status = ALLOWED_TRANSITIONS[current_status]

    info(f"Capability {capability_id}: {current_status} → {target_status}")

    # Build updated YAML
    cap_yaml["status"] = target_status

    # Update metadata with observation details
    metadata = cap_yaml.setdefault("metadata", {})

    # Add observation metadata (system-only fields)
    metadata["observed_by"] = scenario_id
    metadata["observed_on"] = observed_at

    # Add observed effects
    observed_effects = []
    for effect in cap_obs.get("observed_effects", []):
        effect_str = f"{effect['entity']}.{effect['field']}: {effect['from']} → {effect['to']}"
        observed_effects.append(effect_str)
    metadata["observed_effects"] = observed_effects

    # Add UI context if provided
    if cap_obs.get("ui_panel"):
        metadata["observed_ui_panel"] = cap_obs["ui_panel"]
    if cap_obs.get("endpoint"):
        metadata["observed_endpoint"] = cap_obs["endpoint"]

    # Write (unless dry run)
    if not dry_run:
        write_yaml(cap_file, cap_yaml)
        success(f"Capability {capability_id} promoted to {target_status}")
    else:
        info(f"[DRY RUN] Would promote {capability_id} to {target_status}")

    # Update intent YAMLs with observation trace (append-only provenance)
    intent_paths = find_intents_using_capability(capability_id)
    if intent_paths:
        info(f"Found {len(intent_paths)} intent(s) using {capability_id}")
        for intent_path in intent_paths:
            append_intent_observation_trace(
                intent_yaml_path=intent_path,
                scenario_id=scenario_id,
                observed_on=observed_at,
                capability_id=capability_id,
                observed_effects=cap_obs.get("observed_effects", []),
                dry_run=dry_run,
            )

    return "promoted"


def apply_all_observations(dry_run: bool):
    """Apply all observation files in the observations directory."""
    if not SDSR_OBSERVATION_DIR.exists():
        fatal(f"Observations directory not found: {SDSR_OBSERVATION_DIR}")

    observation_files = sorted(SDSR_OBSERVATION_DIR.glob("SDSR_OBSERVATION_*.json"))

    if not observation_files:
        info("No observation files found")
        return

    info(f"Found {len(observation_files)} observation file(s)")
    print()

    all_success = True
    for obs_path in observation_files:
        if not apply_observation(obs_path, dry_run):
            all_success = False
        print()

    if not all_success:
        fatal("Some observations failed to apply")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Apply SDSR observations to AURORA_L2 capability state",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Apply a specific observation
  python3 scripts/tools/AURORA_L2_apply_sdsr_observations.py \\
      --observation sdsr/observations/SDSR_OBSERVATION_E2E_004.json

  # Dry run (validate without writing)
  python3 scripts/tools/AURORA_L2_apply_sdsr_observations.py \\
      --observation sdsr/observations/SDSR_OBSERVATION_E2E_004.json --dry-run

  # Apply all observations
  python3 scripts/tools/AURORA_L2_apply_sdsr_observations.py --all

Core Invariant:
  Capabilities are not real because backend says so.
  They are real only when the system demonstrates them.

  This script is the ONLY allowed writer that may advance:
      DECLARED → OBSERVED
        """
    )

    parser.add_argument(
        "--observation",
        type=Path,
        help="Path to specific SDSR_OBSERVATION_*.json file",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Apply all observation files in sdsr/observations/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only, do not write files",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("AURORA_L2 SDSR Observation Applier")
    print("=" * 60)
    print()
    print("Core Invariant:")
    print("  Capabilities are not real because backend says so.")
    print("  They are real only when the system demonstrates them.")
    print()

    if args.observation:
        if not args.observation.exists():
            fatal(f"Observation file not found: {args.observation}")
        apply_observation(args.observation, dry_run=args.dry_run)
    elif args.all:
        apply_all_observations(dry_run=args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)

    print()
    if args.dry_run:
        info("Dry run complete. No files modified.")
    else:
        success("Observation application complete.")
        info("Next: Run ./scripts/tools/run_aurora_l2_pipeline.sh to recompute bindings")


if __name__ == "__main__":
    main()
