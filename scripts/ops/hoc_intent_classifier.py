#!/usr/bin/env python3
# Layer: L4 — Scripts/Ops
# AUDIENCE: FOUNDER
# Product: system-wide
# Role: Classify intent per function from FUNCTION_INVENTORY.csv — adds intent, intent_confidence, intent_reason columns
# artifact_class: CODE

"""
HOC Intent Classifier

Reads FUNCTION_INVENTORY.csv and classifies each function's intent using
rule-based heuristics. Outputs an extended CSV with intent columns.

Usage:
    python3 scripts/ops/hoc_intent_classifier.py
    python3 scripts/ops/hoc_intent_classifier.py --domain incidents
    python3 scripts/ops/hoc_intent_classifier.py --json
    python3 scripts/ops/hoc_intent_classifier.py --input literature/hoc_domain/FUNCTION_INVENTORY.csv
"""

import argparse
import csv
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = PROJECT_ROOT / "literature" / "hoc_domain" / "FUNCTION_INVENTORY.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "literature" / "hoc_domain" / "FUNCTION_INVENTORY.csv"

# Intent categories
INTENT_PERSISTENCE = "Persistence/Driver"
INTENT_OPERATION = "Operation"
INTENT_POLICY = "Policy/Decision"
INTENT_COORDINATOR = "Coordinator/Aggregator"
INTENT_HELPER = "Internal Helper"
INTENT_UNCLASSIFIED = "Unclassified"

# Name patterns for rule-based classification
POLICY_PATTERNS = [
    "validate", "check", "allow", "deny", "evaluate", "enforce", "verify",
    "guard", "assert", "is_valid", "can_", "should_", "must_",
]

COORDINATOR_PATTERNS = [
    "aggregate", "coordinate", "merge", "combine", "collect", "batch",
    "orchestrate", "dispatch", "compose", "resolve", "reconcile",
]

HELPER_PATTERNS = [
    "parse", "format", "serialize", "transform", "convert", "encode",
    "decode", "normalize", "sanitize", "extract", "build_", "make_",
    "to_", "from_", "_to_", "_from_",
]


# ---------------------------------------------------------------------------
# Classification Rules
# ---------------------------------------------------------------------------


def classify_intent(row: dict[str, str]) -> tuple[str, str, str]:
    """
    Classify a function's intent. Returns (intent, confidence, reason).

    Rules in priority order:
    1. Layer L6 → Persistence/Driver
    2. called_by contains L4 → Operation
    3. Name matches policy patterns → Policy/Decision
    4. Name matches coordinator patterns → Coordinator/Aggregator
    5. Name matches helper patterns → Internal Helper
    6. called_by contains L2 → Operation (gap)
    7. side_effects == pure and called_by empty → Internal Helper
    8. Else → Unclassified
    """
    layer = row.get("layer", "")
    called_by = row.get("called_by", "")
    symbol = row.get("symbol", "").lower()
    side_effects = row.get("side_effects", "")

    # Extract just the function name (after class prefix if any)
    fn_name = symbol.split(".")[-1] if "." in symbol else symbol

    # Skip dunder methods
    if fn_name.startswith("__") and fn_name.endswith("__"):
        return INTENT_HELPER, "high", "dunder method"

    # Skip private methods (single underscore)
    if fn_name.startswith("_"):
        return INTENT_HELPER, "medium", "private function"

    matches = []

    # Rule 1: L6 → Persistence/Driver
    if layer == "L6":
        matches.append((INTENT_PERSISTENCE, "high", "L6 layer = persistence"))

    # Rule 2: called_by contains L4
    if "L4:" in called_by:
        matches.append((INTENT_OPERATION, "high", "called by L4 orchestrator"))

    # Rule 3: Policy patterns
    for pattern in POLICY_PATTERNS:
        if pattern in fn_name:
            matches.append((INTENT_POLICY, "medium", f"name matches '{pattern}'"))
            break

    # Rule 4: Coordinator patterns
    for pattern in COORDINATOR_PATTERNS:
        if pattern in fn_name:
            matches.append((INTENT_COORDINATOR, "medium", f"name matches '{pattern}'"))
            break

    # Rule 5: Helper patterns
    for pattern in HELPER_PATTERNS:
        if pattern in fn_name:
            matches.append((INTENT_HELPER, "medium", f"name matches '{pattern}'"))
            break

    # Rule 6: called_by contains L2 (gap — should go through L4)
    if "L2:" in called_by:
        matches.append((INTENT_OPERATION, "medium", "called by L2 (gap — should route via L4)"))

    # Rule 7: pure + no callers → helper
    if side_effects == "pure" and not called_by:
        matches.append((INTENT_HELPER, "low", "pure function with no callers"))

    if not matches:
        return INTENT_UNCLASSIFIED, "low", "no classification rules matched"

    # If multiple matches with different intents → ambiguous
    unique_intents = set(m[0] for m in matches)
    if len(unique_intents) > 1:
        reasons = "; ".join(f"{m[0]}({m[2]})" for m in matches)
        # Pick highest priority match
        priority = [
            INTENT_PERSISTENCE, INTENT_OPERATION, INTENT_POLICY,
            INTENT_COORDINATOR, INTENT_HELPER,
        ]
        for p in priority:
            if p in unique_intents:
                return p, "ambiguous", f"multi-match: {reasons}"

    return matches[0]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run_classification(
    input_path: Path,
    output_path: Path,
    domain_filter: str | None = None,
    as_json: bool = False,
) -> dict:
    """Read inventory CSV, classify, write extended CSV."""
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        print("Run hoc_function_inventory_generator.py first.", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if domain_filter:
        rows = [r for r in rows if r.get("domain") == domain_filter]

    print(f"Loaded {len(rows)} function records")

    # Classify
    for row in rows:
        intent, confidence, reason = classify_intent(row)
        row["intent"] = intent
        row["intent_confidence"] = confidence
        row["intent_reason"] = reason

    # Stats
    by_intent: dict[str, int] = {}
    by_confidence: dict[str, int] = {}
    for r in rows:
        by_intent[r["intent"]] = by_intent.get(r["intent"], 0) + 1
        by_confidence[r["intent_confidence"]] = by_confidence.get(r["intent_confidence"], 0) + 1

    if as_json:
        result = {
            "total": len(rows),
            "by_intent": by_intent,
            "by_confidence": by_confidence,
            "rows": rows,
        }
        json.dump(result, sys.stdout, indent=2)
        print()
        return result

    # Write extended CSV
    extended_columns = list(reader.fieldnames or []) if hasattr(reader, "fieldnames") else []
    if not extended_columns:
        # Reconstruct from first row
        extended_columns = [k for k in rows[0].keys() if k not in ("intent", "intent_confidence", "intent_reason")]
    for col in ("intent", "intent_confidence", "intent_reason"):
        if col not in extended_columns:
            extended_columns.append(col)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=extended_columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nCSV written: {output_path}")
    print(f"  Rows: {len(rows)}")
    print("\nBy intent:")
    for intent in sorted(by_intent):
        print(f"  {intent}: {by_intent[intent]}")
    print("\nBy confidence:")
    for conf in sorted(by_confidence):
        print(f"  {conf}: {by_confidence[conf]}")

    # Accuracy estimate
    high_or_medium = sum(v for k, v in by_confidence.items() if k in ("high", "medium"))
    pct = (high_or_medium / len(rows) * 100) if rows else 0
    print(f"\nClassification coverage (high+medium): {high_or_medium}/{len(rows)} ({pct:.1f}%)")

    return {"total": len(rows), "by_intent": by_intent}


def main():
    parser = argparse.ArgumentParser(
        description="HOC Intent Classifier — classify function intent from inventory"
    )
    parser.add_argument("--input", "-i", type=str,
                        help=f"Input CSV path (default: {DEFAULT_INPUT.relative_to(PROJECT_ROOT)})")
    parser.add_argument("--output", "-o", type=str,
                        help=f"Output CSV path (default: overwrites input)")
    parser.add_argument("--domain", type=str, help="Process only this domain")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else DEFAULT_INPUT
    output_path = Path(args.output) if args.output else input_path

    print("=" * 60)
    print("HOC Intent Classifier")
    print("=" * 60)
    print()

    run_classification(input_path, output_path, domain_filter=args.domain, as_json=args.json)

    print()
    print("=" * 60)
    print("Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()
