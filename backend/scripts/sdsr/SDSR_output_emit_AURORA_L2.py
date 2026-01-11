"""
SDSR_output_emit_AURORA_L2.py

Witness statement emitter.

Purpose:
    Serialize SDSR-observed truth (ScenarioSDSROutput)
    into an AURORA_L2-compatible observation artifact.

This module:
    - DOES write JSON files
    - DOES NOT modify AURORA_L2 state
    - DOES NOT infer effects
    - DOES NOT promote capabilities
    - DOES NOT call compilers or pipelines

Truth is testified here, not decided.

Reference: CAPABILITY_STATUS_MODEL.yaml v2.0
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, TYPE_CHECKING

# Add script directory to path for imports
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Import from same directory
if TYPE_CHECKING:
    from Scenario_SDSR_output import (
        ScenarioSDSROutput,
        ObservedCapability,
        ObservedEffect,
    )
else:
    from Scenario_SDSR_output import (
        ScenarioSDSROutput,
        ObservedCapability,
        ObservedEffect,
    )


# =============================================================================
# Configuration (explicit, no magic)
# =============================================================================

# Resolve paths relative to repo root (SCRIPT_DIR already defined above)
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
OBSERVATIONS_DIR = REPO_ROOT / "sdsr" / "observations"


# =============================================================================
# Serialization helpers
# =============================================================================

def _serialize_effect(effect: ObservedEffect) -> Dict[str, Any]:
    """Serialize ObservedEffect to dict.

    Note: Schema uses 'from'/'to', not 'before'/'after'.
    """
    return {
        "entity": effect.entity,
        "field": effect.field,
        "from": effect.before,  # Schema field name
        "to": effect.after,     # Schema field name
    }


def _serialize_capability(cap: ObservedCapability) -> Dict[str, Any]:
    """Serialize ObservedCapability to dict.

    Note: Schema uses 'observed_effects', not 'effects'.
    """
    return {
        "capability_id": cap.capability_id,
        "endpoint": cap.endpoint,
        "method": cap.method,
        "observed_effects": [_serialize_effect(e) for e in cap.effects],  # Schema field name
    }


def _serialize_output(scenario_output: ScenarioSDSROutput) -> Dict[str, Any]:
    """Serialize ScenarioSDSROutput to observation dict.

    Output conforms to SDSR_OBSERVATION_SCHEMA.json.

    CRITICAL: observation_class is the mechanical discriminator that
    tells Aurora whether to expect capabilities or not.
    """
    return {
        "scenario_id": scenario_output.scenario_id,
        "status": scenario_output.status,  # Required: PASSED | FAILED | HALTED
        "observation_class": scenario_output.observation_class,  # INFRASTRUCTURE | EFFECT
        "observed_at": scenario_output.observed_at.isoformat(),
        "observed_effects": [
            _serialize_effect(e)
            for e in scenario_output.observed_effects
        ],
        "capabilities_observed": [
            _serialize_capability(cap)
            for cap in scenario_output.realized_capabilities
        ],
        "metadata": {
            "run_id": scenario_output.run_id,
            "runner_version": "inject_synthetic.py v1.0",
            "notes": scenario_output.notes,
        },
    }


# =============================================================================
# Public API
# =============================================================================

def emit_aurora_l2_observation(
    scenario_output: ScenarioSDSROutput,
    *,
    observations_dir: Path = OBSERVATIONS_DIR,
) -> str:
    """
    Emit an SDSR observation artifact for AURORA_L2.

    This function is a witness. It serializes truth.
    It does not decide, infer, promote, or compile.

    Parameters:
        scenario_output:
            ScenarioSDSROutput produced by Scenario_SDSR_output.py

        observations_dir:
            Directory to write observation file (default: sdsr/observations/)

    Returns:
        Absolute path to the written observation file.

    Raises:
        ValueError: If scenario_output.status is not "PASSED".
            Only PASSED scenarios may produce observation artifacts.
    """
    if scenario_output.status != "PASSED":
        raise ValueError(
            f"SDSR observation emission is only allowed for PASSED scenarios. "
            f"Got status: '{scenario_output.status}'"
        )

    # Ensure output directory exists
    observations_dir.mkdir(parents=True, exist_ok=True)

    # Serialize to observation dict
    observation = _serialize_output(scenario_output)

    # Write to file
    filename = f"SDSR_OBSERVATION_{scenario_output.scenario_id}.json"
    filepath = observations_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(observation, f, indent=2, sort_keys=True)

    return str(filepath.resolve())


def validate_observation_file(filepath: str) -> Dict[str, Any]:
    """
    Load and validate an observation file.

    Parameters:
        filepath: Path to observation JSON file

    Returns:
        Parsed observation dict

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        ValueError: If observation is missing required fields
    """
    with open(filepath, "r", encoding="utf-8") as f:
        observation = json.load(f)

    # Validate required fields (per SDSR_OBSERVATION_SCHEMA.json)
    required_fields = [
        "scenario_id",
        "status",
        "observation_class",  # CRITICAL: mechanical discriminator
        "observed_at",
        "observed_effects",
        "capabilities_observed",
    ]
    missing = [f for f in required_fields if f not in observation]
    if missing:
        raise ValueError(f"Observation missing required fields: {missing}")

    # Validate observation_class is valid
    if observation.get("observation_class") not in ("INFRASTRUCTURE", "EFFECT"):
        raise ValueError(
            f"Invalid observation_class: {observation.get('observation_class')}. "
            "Must be INFRASTRUCTURE or EFFECT."
        )

    return observation


# =============================================================================
# CLI for manual testing (not for production use)
# =============================================================================

if __name__ == "__main__":
    import sys

    print("SDSR_output_emit_AURORA_L2.py")
    print("=" * 60)
    print()
    print("This module is meant to be imported, not run directly.")
    print()
    print("Usage:")
    print("  from SDSR_output_emit_AURORA_L2 import emit_aurora_l2_observation")
    print("  ")
    print("  if scenario_output.status == 'PASSED':")
    print("      filepath = emit_aurora_l2_observation(scenario_output)")
    print()
    print(f"Observations directory: {OBSERVATIONS_DIR}")
    print()

    # List existing observations
    if OBSERVATIONS_DIR.exists():
        obs_files = list(OBSERVATIONS_DIR.glob("SDSR_OBSERVATION_*.json"))
        if obs_files:
            print(f"Existing observations: {len(obs_files)}")
            for f in obs_files:
                print(f"  - {f.name}")
        else:
            print("No observations found.")
    else:
        print("Observations directory does not exist yet.")

    sys.exit(0)
