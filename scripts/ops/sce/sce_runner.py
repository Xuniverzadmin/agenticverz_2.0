#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Signal Circuit Enumerator CLI entrypoint
# Callers: human operator (Phase 1 only)
# Allowed Imports: L6 (stdlib only), L8
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: SCE_CONTRACT.yaml

"""
Signal Circuit Enumerator (SCE) Runner

This is the CLI entrypoint for the SCE worker.

CONSTRAINTS (from SCE_CONTRACT.yaml):
  - Phase 1 ONLY
  - READ-ONLY (no code modification)
  - Evidence-only output (no enforcement)
  - No CI blocking
  - Blast radius = ZERO

USAGE:
  python scripts/ops/sce/sce_runner.py \\
    --repo-root . \\
    --playbook docs/playbooks/SESSION_PLAYBOOK.yaml \\
    --out docs/ci/scd/evidence \\
    --run-id phase1-initial

OUTPUT:
  - docs/ci/scd/evidence/SCE_RUN_<run-id>.json (raw evidence)
  - docs/ci/scd/SCE-L{X}-L{Y}-EVIDENCE.md (boundary summaries)
  - docs/ci/scd/SCE_REGISTRY_HINTS.md (non-authoritative hints)
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from passes import run_pass_1, run_pass_2, run_pass_3, run_pass_4


# Files/directories to exclude from scanning
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    "dist",
    "build",
    "*.egg-info",
    ".eggs",
]


def should_exclude(path: str) -> bool:
    """Check if a path should be excluded from scanning."""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path:
            return True
    return False


def collect_files(repo_root: str) -> Dict[str, str]:
    """
    Collect all Python files from the repository.

    Returns: Dict mapping relative file paths to file contents
    """
    files = {}
    repo_path = Path(repo_root).resolve()

    for py_file in repo_path.rglob("*.py"):
        rel_path = str(py_file.relative_to(repo_path))

        if should_exclude(rel_path):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            files[rel_path] = content
        except Exception as e:
            print(f"Warning: Could not read {rel_path}: {e}", file=sys.stderr)

    return files


def validate_preconditions(repo_root: str, playbook_path: str) -> bool:
    """
    Validate preconditions before running.

    From SCE_CONTRACT.yaml:
      - contract_read_and_understood
      - blast_radius_constraint_satisfied
      - no_forbidden_actions_possible_in_design
      - output_is_evidence_only_by_construction
      - ci_blocking_architecturally_impossible
      - human_ratification_required_for_any_action
    """
    # Check repo root exists
    if not os.path.isdir(repo_root):
        print(f"Error: Repository root '{repo_root}' does not exist", file=sys.stderr)
        return False

    # Check playbook exists (optional - used for layer constraints)
    if playbook_path and not os.path.isfile(os.path.join(repo_root, playbook_path)):
        print(
            f"Warning: Playbook '{playbook_path}' not found - using defaults",
            file=sys.stderr,
        )

    # Check contract exists
    contract_path = Path(__file__).parent / "SCE_CONTRACT.yaml"
    if not contract_path.exists():
        print(f"Error: SCE_CONTRACT.yaml not found at {contract_path}", file=sys.stderr)
        return False

    return True


def generate_boundary_summary(
    boundary: str,
    layer_assignments: List[Dict],
    boundary_crossings: List[Dict],
    declared_signals: List[Dict],
    observed_patterns: List[Dict],
    semantic_drifts: List[Dict],
    broken_circuits: List[Dict],
) -> str:
    """
    Generate a markdown summary for a specific layer boundary.

    Example: SCE-L4-L5-EVIDENCE.md
    """
    from_layer, to_layer = boundary.split("-")

    lines = [
        f"# SCE Evidence: {from_layer} to {to_layer} Boundary",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "**Status:** EVIDENCE ONLY - No conclusions, no fixes",
        "**Reference:** SCE_CONTRACT.yaml",
        "",
        "---",
        "",
        "## Boundary Crossings",
        "",
    ]

    # Filter crossings for this boundary
    relevant_crossings = [
        c
        for c in boundary_crossings
        if c.get("from_layer") == from_layer and c.get("to_layer") == to_layer
    ]

    if relevant_crossings:
        lines.append("| From File | To File | Type | Line |")
        lines.append("|-----------|---------|------|------|")
        for crossing in relevant_crossings[:50]:  # Limit to 50
            lines.append(
                f"| {crossing.get('from_file', '')} "
                f"| {crossing.get('to_file', '')} "
                f"| {crossing.get('crossing_type', '')} "
                f"| {crossing.get('line_number', '')} |"
            )
    else:
        lines.append("*No boundary crossings observed.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Declared Signals (from metadata)",
            "",
        ]
    )

    # Filter declared signals for files in these layers
    layer_files = {
        a["file_path"]
        for a in layer_assignments
        if a.get("layer") in (from_layer, to_layer)
    }
    relevant_declared = [
        s for s in declared_signals if s.get("file_path") in layer_files
    ]

    if relevant_declared:
        lines.append("| File | Type | Signal Name | Source |")
        lines.append("|------|------|-------------|--------|")
        for sig in relevant_declared[:50]:
            lines.append(
                f"| {sig.get('file_path', '')} "
                f"| {sig.get('signal_type', '')} "
                f"| {sig.get('signal_name', '')} "
                f"| {sig.get('raw_metadata', '')[:30]} |"
            )
    else:
        lines.append("*No declared signals found.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Observed Patterns (from code)",
            "",
        ]
    )

    # Filter observed patterns for files in these layers
    relevant_observed = [
        p for p in observed_patterns if p.get("file_path") in layer_files
    ]

    if relevant_observed:
        lines.append("| File | Pattern Type | Evidence | Confidence |")
        lines.append("|------|--------------|----------|------------|")
        for pattern in relevant_observed[:50]:
            evidence = pattern.get("evidence", "")[:40]
            lines.append(
                f"| {pattern.get('file_path', '')} "
                f"| {pattern.get('pattern_type', '')} "
                f"| {evidence} "
                f"| {pattern.get('confidence', '')} |"
            )
    else:
        lines.append("*No signal-like patterns observed.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Drifts Detected",
            "",
        ]
    )

    # Filter drifts for files in these layers
    relevant_drifts = [
        d
        for d in semantic_drifts
        if d.get("file_path") in layer_files or d.get("file_path") is None
    ]

    if relevant_drifts:
        lines.append("| Type | Description | Severity |")
        lines.append("|------|-------------|----------|")
        for drift in relevant_drifts[:50]:
            desc = drift.get("description", "")[:60]
            lines.append(
                f"| {drift.get('drift_type', '')} "
                f"| {desc} "
                f"| {drift.get('severity', '')} |"
            )
    else:
        lines.append("*No semantic drifts detected.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Broken Circuits",
            "",
        ]
    )

    relevant_circuits = [
        c
        for c in broken_circuits
        if c.get("file_path") in layer_files or c.get("file_path") is None
    ]

    if relevant_circuits:
        lines.append("| Type | Description | Severity |")
        lines.append("|------|-------------|----------|")
        for circuit in relevant_circuits[:50]:
            desc = circuit.get("description", "")[:60]
            lines.append(
                f"| {circuit.get('drift_type', '')} "
                f"| {desc} "
                f"| {circuit.get('severity', '')} |"
            )
    else:
        lines.append("*No broken circuits detected.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Classification",
            "",
            "This document is **EVIDENCE ONLY**.",
            "",
            "- No conclusions have been drawn",
            "- No fixes have been suggested",
            "- Human SCD ratification is required for any action",
            "",
        ]
    )

    return "\n".join(lines)


def generate_registry_hints(
    declared_signals: List[Dict],
    observed_patterns: List[Dict],
    semantic_drifts: List[Dict],
) -> str:
    """
    Generate non-authoritative registry hints.

    These are suggestions only - NOT applied automatically.
    """
    lines = [
        "# SCE Registry Hints",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "**Status:** NON-AUTHORITATIVE - Do NOT apply automatically",
        "**Reference:** SCE_CONTRACT.yaml",
        "",
        "---",
        "",
        "## Candidate Signals",
        "",
        "These patterns LOOK like signals but may not be. Confidence = LOW until human-ratified.",
        "",
    ]

    # High-confidence observed patterns that aren't declared
    undeclared = [
        d for d in semantic_drifts if d.get("drift_type") == "observed_not_declared"
    ]

    if undeclared:
        lines.append("| Pattern | File | Severity |")
        lines.append("|---------|------|----------|")
        for d in undeclared[:30]:
            lines.append(
                f"| {d.get('observed_pattern', '')[:40]} "
                f"| {d.get('file_path', '')} "
                f"| {d.get('severity', '')} |"
            )
    else:
        lines.append("*No candidate signals found.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Candidate Gaps",
            "",
            "These signals are DECLARED but no mechanical evidence was found.",
            "",
        ]
    )

    declared_not_observed = [
        d for d in semantic_drifts if d.get("drift_type") == "declared_not_observed"
    ]

    if declared_not_observed:
        lines.append("| Signal | File | Severity |")
        lines.append("|--------|------|----------|")
        for d in declared_not_observed[:30]:
            lines.append(
                f"| {d.get('declared_signal', '')} "
                f"| {d.get('file_path', '')} "
                f"| {d.get('severity', '')} |"
            )
    else:
        lines.append("*No candidate gaps found.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Candidate Drift",
            "",
            "These signals show direction or boundary mismatches.",
            "",
        ]
    )

    other_drifts = [
        d
        for d in semantic_drifts
        if d.get("drift_type") in ("direction_mismatch", "boundary_bypass")
    ]

    if other_drifts:
        lines.append("| Type | Description | Severity |")
        lines.append("|------|-------------|----------|")
        for d in other_drifts[:30]:
            desc = d.get("description", "")[:50]
            lines.append(
                f"| {d.get('drift_type', '')} | {desc} | {d.get('severity', '')} |"
            )
    else:
        lines.append("*No drift candidates found.*")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Important",
            "",
            "This file is **NOT applied automatically**.",
            "",
            "Human review is required before:",
            "- Adding signals to CI_SIGNAL_REGISTRY.md",
            "- Closing any gaps",
            "- Modifying any code",
            "",
        ]
    )

    return "\n".join(lines)


def run_sce(
    repo_root: str,
    playbook_path: str,
    output_dir: str,
    run_id: str,
) -> int:
    """
    Execute the Signal Circuit Enumerator.

    Returns: Exit code (0 = success, always 0 per contract - no CI blocking)
    """
    print("SCE Runner starting...")
    print(f"  Repo root: {repo_root}")
    print(f"  Output dir: {output_dir}")
    print(f"  Run ID: {run_id}")
    print()

    # Validate preconditions
    if not validate_preconditions(repo_root, playbook_path):
        print("Precondition validation failed", file=sys.stderr)
        # Still return 0 - SCE cannot block anything
        return 0

    # Collect files
    print("Collecting files...")
    files = collect_files(repo_root)
    print(f"  Found {len(files)} Python files")
    print()

    # Execute passes
    print("Executing Pass 1: Layer & Boundary Indexing...")
    pass_1_output = run_pass_1(repo_root, files)
    print(f"  Layer assignments: {len(pass_1_output['layer_assignments'])}")
    print(f"  Boundary crossings: {len(pass_1_output['boundary_crossings'])}")
    print()

    print("Executing Pass 2: Semantic Claim Extraction...")
    pass_2_output = run_pass_2(files)
    print(f"  Declared signals: {len(pass_2_output['declared_signals'])}")
    print(f"  Files with metadata: {len(pass_2_output['metadata_files'])}")
    print()

    print("Executing Pass 3: Mechanical Observation...")
    pass_3_output = run_pass_3(files)
    print(f"  Observed patterns: {len(pass_3_output['observed_patterns'])}")
    print(f"  Implicit signals: {len(pass_3_output['implicit_signals'])}")
    print()

    print("Executing Pass 4: Diff & Drift Detection...")
    pass_4_output = run_pass_4(pass_1_output, pass_2_output, pass_3_output)
    print(f"  Semantic drifts: {len(pass_4_output['semantic_drifts'])}")
    print(f"  Broken circuits: {len(pass_4_output['broken_circuits'])}")
    print()

    # Prepare output
    timestamp = datetime.now(timezone.utc).isoformat()
    evidence = {
        "run_id": run_id,
        "timestamp": timestamp,
        "phase": "1",
        "repo_root": os.path.abspath(repo_root),
        "passes": {
            "pass_1": pass_1_output,
            "pass_2": pass_2_output,
            "pass_3": pass_3_output,
            "pass_4": pass_4_output,
        },
        "summary": {
            "files_scanned": len(files),
            "layers_found": len(
                set(
                    a["layer"]
                    for a in pass_1_output["layer_assignments"]
                    if a["layer"] != "UNKNOWN"
                )
            ),
            "boundary_crossings": len(pass_1_output["boundary_crossings"]),
            "declared_signals": len(pass_2_output["declared_signals"]),
            "observed_patterns": len(pass_3_output["observed_patterns"]),
            "drifts_detected": len(pass_4_output["semantic_drifts"])
            + len(pass_4_output["broken_circuits"]),
        },
    }

    # Write output
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Raw evidence JSON
    evidence_file = output_path / f"SCE_RUN_{run_id}.json"
    print(f"Writing raw evidence to {evidence_file}...")
    with open(evidence_file, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, default=str)

    # Boundary summaries
    print("Generating boundary summaries...")
    boundaries_found: Set[str] = set()
    for crossing in pass_1_output["boundary_crossings"]:
        from_layer = crossing.get("from_layer", "")
        to_layer = crossing.get("to_layer", "")
        if from_layer and to_layer:
            boundaries_found.add(f"{from_layer}-{to_layer}")

    scd_dir = Path(repo_root) / "docs" / "ci" / "scd"
    scd_dir.mkdir(parents=True, exist_ok=True)

    for boundary in sorted(boundaries_found):
        summary = generate_boundary_summary(
            boundary,
            pass_1_output["layer_assignments"],
            pass_1_output["boundary_crossings"],
            pass_2_output["declared_signals"],
            pass_3_output["observed_patterns"],
            pass_4_output["semantic_drifts"],
            pass_4_output["broken_circuits"],
        )
        summary_file = scd_dir / f"SCE-{boundary}-EVIDENCE.md"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"  Wrote {summary_file}")

    # Registry hints
    hints = generate_registry_hints(
        pass_2_output["declared_signals"],
        pass_3_output["observed_patterns"],
        pass_4_output["semantic_drifts"],
    )
    hints_file = scd_dir / "SCE_REGISTRY_HINTS.md"
    with open(hints_file, "w", encoding="utf-8") as f:
        f.write(hints)
    print(f"  Wrote {hints_file}")

    print()
    print("=" * 60)
    print("SCE Run Complete")
    print("=" * 60)
    print()
    print("Summary:")
    print(f"  Files scanned: {evidence['summary']['files_scanned']}")
    print(f"  Layers found: {evidence['summary']['layers_found']}")
    print(f"  Boundary crossings: {evidence['summary']['boundary_crossings']}")
    print(f"  Declared signals: {evidence['summary']['declared_signals']}")
    print(f"  Observed patterns: {evidence['summary']['observed_patterns']}")
    print(f"  Drifts detected: {evidence['summary']['drifts_detected']}")
    print()
    print("IMPORTANT: This output is EVIDENCE ONLY.")
    print("No conclusions. No fixes. Human ratification required.")
    print()

    # Always return 0 - SCE cannot block anything
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Signal Circuit Enumerator (SCE) - Phase 1 Evidence Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CONSTRAINTS (from SCE_CONTRACT.yaml):
  - Phase 1 ONLY
  - READ-ONLY (no code modification)
  - Evidence-only output (no enforcement)
  - No CI blocking (always exits 0)
  - Blast radius = ZERO

Example:
  python scripts/ops/sce/sce_runner.py \\
    --repo-root . \\
    --playbook docs/playbooks/SESSION_PLAYBOOK.yaml \\
    --out docs/ci/scd/evidence \\
    --run-id phase1-initial
        """,
    )

    parser.add_argument(
        "--repo-root",
        required=True,
        help="Repository root directory to scan",
    )
    parser.add_argument(
        "--playbook",
        default="docs/playbooks/SESSION_PLAYBOOK.yaml",
        help="Path to SESSION_PLAYBOOK.yaml (relative to repo root)",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for evidence files",
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Human-chosen immutable run identifier (e.g., phase1-initial)",
    )

    args = parser.parse_args()

    sys.exit(
        run_sce(
            repo_root=args.repo_root,
            playbook_path=args.playbook,
            output_dir=args.out,
            run_id=args.run_id,
        )
    )


if __name__ == "__main__":
    main()
