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
        ACv2Evidence,
    )
else:
    from Scenario_SDSR_output import (
        ScenarioSDSROutput,
        ObservedCapability,
        ObservedEffect,
        ACv2Evidence,
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


def _serialize_ac_v2_evidence(evidence: "ACv2Evidence") -> Dict[str, Any]:
    """Serialize ACv2Evidence to dict for baseline certification."""
    result: Dict[str, Any] = {
        "evaluated_at": evidence.evaluated_at,
        "ac_v2_pass": evidence.ac_v2_pass,
        "ac_v2_failures": evidence.ac_v2_failures,
    }

    if evidence.run_record:
        result["run_record"] = {
            "fields_present": evidence.run_record.fields_present,
            "fields_missing": evidence.run_record.fields_missing,
            "run_id": evidence.run_record.run_id,
            "run_status": evidence.run_record.run_status,
            "timestamp_start": evidence.run_record.timestamp_start,
            "timestamp_end": evidence.run_record.timestamp_end,
        }

    if evidence.observability:
        result["observability"] = {
            "logs_exist": evidence.observability.logs_exist,
            "logs_correlated_to_run": evidence.observability.logs_correlated_to_run,
            "trace_exists": evidence.observability.trace_exists,
            "trace_id": evidence.observability.trace_id,
            "trace_steps_count": evidence.observability.trace_steps_count,
            "steps_linked_to_trace": evidence.observability.steps_linked_to_trace,
            "steps_linked_to_run": evidence.observability.steps_linked_to_run,
            "steps_linked_to_scenario": evidence.observability.steps_linked_to_scenario,
            "orphan_step_ids": evidence.observability.orphan_step_ids,
        }

    if evidence.policy_context:
        result["policy_context"] = {
            "policies_evaluated_exists": evidence.policy_context.policies_evaluated_exists,
            "policy_results_value": evidence.policy_context.policy_results_value,
            "thresholds_checked_exists": evidence.policy_context.thresholds_checked_exists,
        }

    # PIN-407: Use explicit_outcome (renamed from explicit_absence)
    # Check both new and deprecated field names for backward compatibility
    explicit_outcome = getattr(evidence, 'explicit_outcome', None) or getattr(evidence, 'explicit_absence', None)
    if explicit_outcome:
        result["explicit_outcome"] = {
            # PIN-407: New outcome-based fields
            "incident_created": explicit_outcome.incident_created,
            "incident_outcome": explicit_outcome.incident_outcome,
            "policy_evaluated": explicit_outcome.policy_evaluated,
            "policy_outcome": explicit_outcome.policy_outcome,
            "policy_proposal_created": explicit_outcome.policy_proposal_created,
            "policy_proposal_needed": explicit_outcome.policy_proposal_needed,
            # Reference counts (observational)
            "incidents_table_count": explicit_outcome.incidents_table_count,
            "proposals_table_count": explicit_outcome.proposals_table_count,
            # Capture validation
            "capture_complete": explicit_outcome.capture_complete,
            "capture_failures": explicit_outcome.capture_failures,
        }

    if evidence.integrity:
        result["integrity"] = {
            "expected_events": evidence.integrity.expected_events,
            "observed_events": evidence.integrity.observed_events,
            "missing_events": evidence.integrity.missing_events,
            "integrity_score": evidence.integrity.integrity_score,
        }

    return result


def _serialize_output(scenario_output: ScenarioSDSROutput) -> Dict[str, Any]:
    """Serialize ScenarioSDSROutput to observation dict.

    Output conforms to SDSR_OBSERVATION_SCHEMA.json.

    CRITICAL: observation_class is the mechanical discriminator that
    tells Aurora whether to expect capabilities or not.
    """
    result: Dict[str, Any] = {
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

    # AC v2 Evidence (BASELINE TRUST - SDSR-E2E-006)
    if scenario_output.ac_v2_evidence:
        result["ac_v2_evidence"] = _serialize_ac_v2_evidence(scenario_output.ac_v2_evidence)

    return result


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
