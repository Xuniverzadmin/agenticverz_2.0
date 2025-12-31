# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Pass 4 - Diff & Drift Detection
# Callers: sce_runner.py
# Allowed Imports: L6 (stdlib only), L8
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: SCE_CONTRACT.yaml

"""
Pass 4: Diff & Drift Detection

Operation: compare_declared_vs_observed

Detects:
  - declared_not_observed
  - observed_not_declared
  - direction_mismatch
  - boundary_bypass
  - half_circuits

Emits:
  - SEMANTIC_DRIFT
  - BROKEN_CANDIDATE_CIRCUIT

This pass compares Pass 2 (declared) with Pass 3 (observed).
It produces EVIDENCE of drift, not conclusions.
This pass is READ-ONLY. It does not modify any files.
"""

from typing import Dict, List, Set


def normalize_signal_name(name: str) -> str:
    """
    Normalize a signal name for comparison.

    Handles variations like:
    - "run.started" vs "run_started" vs "RunStarted"
    - Case differences
    - Underscore/dot/hyphen variations
    """
    # Convert to lowercase
    normalized = name.lower()
    # Replace separators with underscore
    normalized = normalized.replace(".", "_").replace("-", "_")
    # Remove extra underscores
    normalized = "_".join(filter(None, normalized.split("_")))
    return normalized


def find_declared_not_observed(
    declared_signals: List[Dict],
    observed_patterns: List[Dict],
) -> List[Dict]:
    """
    Find signals that are DECLARED but NOT OBSERVED mechanically.

    This could indicate:
    - Dead code (declaration exists but never used)
    - Documentation drift
    - Planned but unimplemented signals
    """
    drifts = []

    # Build set of observed signal indicators
    observed_indicators: Set[str] = set()
    for pattern in observed_patterns:
        # Extract signal-like names from evidence
        evidence = pattern.get("evidence", "")
        # Simple extraction - look for quoted strings or signal names
        if "'" in evidence:
            parts = evidence.split("'")
            for i in range(1, len(parts), 2):
                observed_indicators.add(normalize_signal_name(parts[i]))
        if pattern.get("pattern_type") in ("event_publish", "event_subscribe"):
            observed_indicators.add(normalize_signal_name(evidence))

    # Check each declared signal
    for declared in declared_signals:
        signal_name = declared.get("signal_name", "")
        normalized_name = normalize_signal_name(signal_name)

        # Check if any observed pattern seems to match
        found = False
        for indicator in observed_indicators:
            if normalized_name in indicator or indicator in normalized_name:
                found = True
                break

        if not found:
            drifts.append(
                {
                    "drift_type": "declared_not_observed",
                    "description": f"Signal '{signal_name}' is declared but no mechanical pattern was observed",
                    "file_path": declared.get("file_path"),
                    "declared_signal": signal_name,
                    "observed_pattern": None,
                    "severity": "MEDIUM",
                }
            )

    return drifts


def find_observed_not_declared(
    declared_signals: List[Dict],
    observed_patterns: List[Dict],
) -> List[Dict]:
    """
    Find signal-like patterns that are OBSERVED but NOT DECLARED.

    This could indicate:
    - Undocumented signals (code exists but no metadata)
    - Implicit coupling
    - Missing signal declarations
    """
    drifts = []

    # Build set of declared signal names
    declared_names: Set[str] = set()
    for declared in declared_signals:
        signal_name = declared.get("signal_name", "")
        declared_names.add(normalize_signal_name(signal_name))

    # Check high-confidence observed patterns
    for pattern in observed_patterns:
        if pattern.get("confidence") != "HIGH":
            continue

        evidence = pattern.get("evidence", "")
        pattern_type = pattern.get("pattern_type", "")

        # Only check event-like patterns
        if pattern_type not in ("event_publish", "event_subscribe", "dispatch_call"):
            continue

        # Check if this pattern matches any declaration
        found = False
        for name in declared_names:
            if name in normalize_signal_name(evidence):
                found = True
                break

        if not found:
            drifts.append(
                {
                    "drift_type": "observed_not_declared",
                    "description": f"Pattern '{evidence}' observed but no matching signal declared",
                    "file_path": pattern.get("file_path"),
                    "declared_signal": None,
                    "observed_pattern": evidence,
                    "severity": "HIGH" if pattern_type == "event_publish" else "MEDIUM",
                }
            )

    return drifts


def find_direction_mismatches(
    declared_signals: List[Dict],
    observed_patterns: List[Dict],
) -> List[Dict]:
    """
    Find signals where declared direction (emit/consume) doesn't match observed.
    """
    drifts = []

    # Group declared signals by file and normalized name
    declared_by_file: Dict[str, Dict[str, str]] = {}
    for declared in declared_signals:
        file_path = declared.get("file_path", "")
        signal_name = normalize_signal_name(declared.get("signal_name", ""))
        signal_type = declared.get("signal_type", "")

        if file_path not in declared_by_file:
            declared_by_file[file_path] = {}
        declared_by_file[file_path][signal_name] = signal_type

    # Check observed patterns for direction mismatches
    for pattern in observed_patterns:
        file_path = pattern.get("file_path", "")
        pattern_type = pattern.get("pattern_type", "")

        # Determine observed direction
        observed_direction = None
        if pattern_type in ("event_publish", "dispatch_call"):
            observed_direction = "emit"
        elif pattern_type in ("event_subscribe",):
            observed_direction = "consume"

        if observed_direction and file_path in declared_by_file:
            evidence = pattern.get("evidence", "")
            for declared_name, declared_type in declared_by_file[file_path].items():
                if declared_name in normalize_signal_name(evidence):
                    if declared_type != observed_direction:
                        drifts.append(
                            {
                                "drift_type": "direction_mismatch",
                                "description": f"Signal declared as '{declared_type}' but observed as '{observed_direction}'",
                                "file_path": file_path,
                                "declared_signal": declared_name,
                                "observed_pattern": evidence,
                                "severity": "HIGH",
                            }
                        )

    return drifts


def find_boundary_bypasses(
    boundary_crossings: List[Dict],
    layer_assignments: List[Dict],
) -> List[Dict]:
    """
    Find imports that bypass expected layer boundaries.

    Example: L2 importing directly from L5 (should go through L3/L4)
    """
    drifts = []

    # Define allowed import directions per layer model
    allowed_imports = {
        "L1": {"L2"},
        "L2": {"L3", "L4", "L6"},
        "L3": {"L4", "L6"},
        "L4": {"L5", "L6"},
        "L5": {"L6"},
        "L6": set(),  # L6 imports nothing from other layers
        "L7": {"L6"},
        "L8": set(),  # L8 (tests/CI) can import anything for testing
    }

    for crossing in boundary_crossings:
        from_layer = crossing.get("from_layer", "")
        to_layer = crossing.get("to_layer", "")

        # Skip L8 - tests can import anything
        if from_layer == "L8":
            continue

        # Check if this crossing is allowed
        allowed = allowed_imports.get(from_layer, set())
        if to_layer not in allowed:
            drifts.append(
                {
                    "drift_type": "boundary_bypass",
                    "description": f"{from_layer} imports from {to_layer} but allowed imports are {allowed}",
                    "file_path": crossing.get("from_file"),
                    "declared_signal": None,
                    "observed_pattern": f"import from {crossing.get('to_file')}",
                    "severity": "HIGH" if from_layer in ("L1", "L2") else "MEDIUM",
                }
            )

    return drifts


def find_half_circuits(
    declared_signals: List[Dict],
    observed_patterns: List[Dict],
) -> List[Dict]:
    """
    Find signals that have only emitters OR only consumers (not both).

    A complete circuit needs:
    - Emitter (publish/dispatch)
    - Consumer (subscribe/handle)
    """
    drifts = []

    # Collect all emit signals
    emit_signals: Set[str] = set()
    consume_signals: Set[str] = set()

    # From declarations
    for declared in declared_signals:
        signal_name = normalize_signal_name(declared.get("signal_name", ""))
        signal_type = declared.get("signal_type", "")
        if signal_type == "emit":
            emit_signals.add(signal_name)
        elif signal_type == "consume":
            consume_signals.add(signal_name)

    # From observations
    for pattern in observed_patterns:
        pattern_type = pattern.get("pattern_type", "")
        evidence = pattern.get("evidence", "")
        normalized_evidence = normalize_signal_name(evidence)

        if pattern_type in ("event_publish", "dispatch_call"):
            emit_signals.add(normalized_evidence)
        elif pattern_type in ("event_subscribe",):
            consume_signals.add(normalized_evidence)

    # Find emitters without consumers
    for signal in emit_signals:
        if signal and signal not in consume_signals:
            # Check if any consumer partially matches
            partial_match = False
            for consumer in consume_signals:
                if signal in consumer or consumer in signal:
                    partial_match = True
                    break

            if not partial_match:
                drifts.append(
                    {
                        "drift_type": "half_circuit",
                        "description": f"Signal '{signal}' has emitter but no consumer found",
                        "file_path": None,
                        "declared_signal": signal,
                        "observed_pattern": None,
                        "severity": "MEDIUM",
                    }
                )

    # Find consumers without emitters
    for signal in consume_signals:
        if signal and signal not in emit_signals:
            # Check if any emitter partially matches
            partial_match = False
            for emitter in emit_signals:
                if signal in emitter or emitter in signal:
                    partial_match = True
                    break

            if not partial_match:
                drifts.append(
                    {
                        "drift_type": "half_circuit",
                        "description": f"Signal '{signal}' has consumer but no emitter found",
                        "file_path": None,
                        "declared_signal": signal,
                        "observed_pattern": None,
                        "severity": "MEDIUM",
                    }
                )

    return drifts


def run_pass_4(
    pass_1_output: Dict,
    pass_2_output: Dict,
    pass_3_output: Dict,
) -> Dict:
    """
    Execute Pass 4: Diff & Drift Detection.

    Args:
        pass_1_output: Output from Pass 1 (layer assignments, boundary crossings)
        pass_2_output: Output from Pass 2 (declared signals)
        pass_3_output: Output from Pass 3 (observed patterns)

    Returns:
        Pass 4 output dict containing:
        - semantic_drifts (SEMANTIC_DRIFT findings)
        - broken_circuits (BROKEN_CANDIDATE_CIRCUIT findings)
    """
    declared_signals = pass_2_output.get("declared_signals", [])
    observed_patterns = pass_3_output.get("observed_patterns", [])
    layer_assignments = pass_1_output.get("layer_assignments", [])
    boundary_crossings = pass_1_output.get("boundary_crossings", [])

    # Collect all drift types
    semantic_drifts = []
    broken_circuits = []

    # 1. Declared but not observed
    drifts = find_declared_not_observed(declared_signals, observed_patterns)
    semantic_drifts.extend(drifts)

    # 2. Observed but not declared
    drifts = find_observed_not_declared(declared_signals, observed_patterns)
    semantic_drifts.extend(drifts)

    # 3. Direction mismatches
    drifts = find_direction_mismatches(declared_signals, observed_patterns)
    semantic_drifts.extend(drifts)

    # 4. Boundary bypasses
    drifts = find_boundary_bypasses(boundary_crossings, layer_assignments)
    broken_circuits.extend(drifts)

    # 5. Half circuits
    drifts = find_half_circuits(declared_signals, observed_patterns)
    broken_circuits.extend(drifts)

    return {
        "semantic_drifts": semantic_drifts,
        "broken_circuits": broken_circuits,
    }
