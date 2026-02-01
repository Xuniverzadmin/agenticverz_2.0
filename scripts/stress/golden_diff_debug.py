#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Golden File Diff Debugger for M4 Workflow Engine
# artifact_class: CODE
"""
Golden File Diff Debugger for M4 Workflow Engine

Analyzes golden file mismatches to identify:
- Seed mismatches
- Leaked volatile fields
- Unseeded RNG usage
- External call variations

Usage:
    python golden_diff_debug.py --golden-a <file_a.json> --golden-b <file_b.json> --verbose
    python golden_diff_debug.py --summary-dir /tmp/m4-shadow-... --output summary.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Known volatile fields that should NOT affect determinism
VOLATILE_FIELDS = {
    "timestamp",
    "created_at",
    "updated_at",
    "duration_ms",
    "duration",
    "elapsed",
    "elapsed_ms",
    "latency",
    "latency_ms",
    "execution_time",
    "wall_time",
    "real_time",
    "started_at",
    "finished_at",
    "completed_at",
}

# Fields that must be deterministic
DETERMINISTIC_FIELDS = {
    "seed",
    "step_seed",
    "base_seed",
    "workflow_hash",
    "step_hash",
    "output_hash",
    "content_hash",
    "signature",
    "hmac",
}


def load_golden(filepath: str) -> Optional[Dict]:
    """Load a golden file (JSON or JSONL)."""
    try:
        with open(filepath, "r") as f:
            content = f.read().strip()
            if not content:
                return None
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                records = []
                for line in content.split("\n"):
                    if line.strip():
                        records.append(json.loads(line))
                return {"records": records, "_type": "jsonl"}
    except Exception as e:
        print(f"Error loading {filepath}: {e}", file=sys.stderr)
        return None


def flatten_dict(d: Dict, parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                if isinstance(item, dict):
                    items.extend(flatten_dict(item, f"{new_key}[{i}]", sep).items())
                else:
                    items.append((f"{new_key}[{i}]", item))
        else:
            items.append((new_key, v))
    return dict(items)


def identify_diff_type(key: str, val_a: Any, val_b: Any) -> str:
    """Identify the type of difference."""
    key_lower = key.lower().split(".")[-1].split("[")[0]

    if key_lower in VOLATILE_FIELDS:
        return "VOLATILE_LEAK"
    if key_lower in DETERMINISTIC_FIELDS:
        return "DETERMINISM_VIOLATION"
    if "seed" in key_lower:
        return "SEED_MISMATCH"
    if "hash" in key_lower:
        return "HASH_MISMATCH"
    if "random" in key_lower or "rand" in key_lower:
        return "UNSEEDED_RNG"
    if "external" in key_lower or "api" in key_lower or "http" in key_lower:
        return "EXTERNAL_CALL_VARIATION"
    return "UNKNOWN"


def diff_golden_files(golden_a: Dict, golden_b: Dict, verbose: bool = False) -> Dict:
    """Compare two golden files and identify differences."""
    flat_a = flatten_dict(golden_a)
    flat_b = flatten_dict(golden_b)
    all_keys = set(flat_a.keys()) | set(flat_b.keys())

    differences = []
    volatile_leaks = []
    determinism_violations = []

    for key in sorted(all_keys):
        val_a = flat_a.get(key, "<MISSING>")
        val_b = flat_b.get(key, "<MISSING>")

        if val_a != val_b:
            diff_type = identify_diff_type(key, val_a, val_b)
            diff_entry = {
                "key": key,
                "value_a": str(val_a)[:200],
                "value_b": str(val_b)[:200],
                "diff_type": diff_type,
            }
            differences.append(diff_entry)

            if diff_type == "VOLATILE_LEAK":
                volatile_leaks.append(key)
            elif diff_type in (
                "DETERMINISM_VIOLATION",
                "SEED_MISMATCH",
                "HASH_MISMATCH",
            ):
                determinism_violations.append(key)

    return {
        "total_keys": len(all_keys),
        "differences_count": len(differences),
        "volatile_leaks": volatile_leaks,
        "determinism_violations": determinism_violations,
        "differences": differences if verbose else differences[:10],
        "is_match": len(differences) == 0,
        "severity": "CRITICAL"
        if determinism_violations
        else ("WARNING" if volatile_leaks else "OK"),
    }


def analyze_shadow_directory(shadow_dir: str) -> Dict:
    """Analyze a shadow simulation output directory."""
    shadow_path = Path(shadow_dir)

    if not shadow_path.exists():
        return {"error": f"Directory not found: {shadow_dir}"}

    reports_dir = shadow_path / "reports"
    golden_dir = shadow_path / "golden"

    summary = {
        "directory": str(shadow_path),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "cycles": 0,
        "total_workflows": 0,
        "total_replays": 0,
        "total_mismatches": 0,
        "mismatch_details": [],
        "cycle_summaries": [],
    }

    if reports_dir.exists():
        cycle_files = sorted(reports_dir.glob("cycle_*.json"))
        summary["cycles"] = len(cycle_files)

        for cycle_file in cycle_files:
            try:
                with open(cycle_file) as f:
                    cycle_data = json.load(f)

                workflows = cycle_data.get("primary", {}).get("total", 0)
                replays = cycle_data.get("shadow", {}).get("total_replays", 0)
                mismatches = cycle_data.get("shadow", {}).get("mismatches", 0)

                summary["total_workflows"] += workflows
                summary["total_replays"] += replays
                summary["total_mismatches"] += mismatches

                if mismatches > 0:
                    summary["mismatch_details"].extend(
                        cycle_data.get("mismatch_details", [])[:5]
                    )

                summary["cycle_summaries"].append(
                    {
                        "cycle": cycle_file.stem,
                        "workflows": workflows,
                        "replays": replays,
                        "mismatches": mismatches,
                        "passed": cycle_data.get("passed", mismatches == 0),
                    }
                )
            except Exception as e:
                summary["cycle_summaries"].append(
                    {"cycle": cycle_file.stem, "error": str(e)}
                )

    if golden_dir.exists():
        summary["golden_file_count"] = len(list(golden_dir.glob("*.json")))
        summary["golden_dir_size_bytes"] = sum(
            f.stat().st_size for f in golden_dir.glob("*.json")
        )

    summary["mismatch_rate"] = summary["total_mismatches"] / max(
        summary["total_replays"], 1
    )
    summary["passed"] = summary["total_mismatches"] == 0
    summary["verdict"] = "PASS" if summary["passed"] else "FAIL"

    return summary


def main():
    parser = argparse.ArgumentParser(description="Golden File Diff Debugger")
    parser.add_argument("--golden-a", help="First golden file path")
    parser.add_argument("--golden-b", help="Second golden file path")
    parser.add_argument(
        "--summary-dir", help="Shadow simulation directory to summarize"
    )
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()
    result = {}

    if args.summary_dir:
        result = analyze_shadow_directory(args.summary_dir)
    elif args.golden_a and args.golden_b:
        golden_a = load_golden(args.golden_a)
        golden_b = load_golden(args.golden_b)

        if golden_a is None:
            result = {"error": f"Could not load {args.golden_a}"}
        elif golden_b is None:
            result = {"error": f"Could not load {args.golden_b}"}
        else:
            result = diff_golden_files(golden_a, golden_b, args.verbose)
    else:
        parser.print_help()
        sys.exit(1)

    output = json.dumps(result, indent=2, default=str)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Output written to {args.output}")
    else:
        print(output)

    if result.get("verdict") == "FAIL" or result.get("severity") == "CRITICAL":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
