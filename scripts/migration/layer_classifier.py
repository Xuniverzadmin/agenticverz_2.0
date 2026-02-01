#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Layer Classifier - Pass 2: Classification & Violation Detection
# artifact_class: CODE
"""
Layer Classifier - Pass 2: Classification & Violation Detection

Reads signals_raw.json from Pass 1 and:
- Applies layer classification rules
- Detects violations (DRIFT, DATA_LEAK, AUTHORITY_LEAK, etc.)
- Generates layer fit report

Output: layer_fit_report.json, summary.md

Usage:
    python scripts/migration/layer_classifier.py
    python scripts/migration/layer_classifier.py --input signals_raw.json
"""

import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Change to repo root
os.chdir(Path(__file__).parent.parent.parent)

INPUT_FILE = Path("docs/architecture/migration/signals_raw.json")
OUTPUT_JSON = Path("docs/architecture/migration/layer_fit_report.json")
OUTPUT_MD = Path("docs/architecture/migration/layer_fit_summary.md")


@dataclass
class Violation:
    """A detected violation in layer classification."""
    code: str  # DRIFT, DATA_LEAK, AUTHORITY_LEAK, etc.
    severity: str  # HIGH, MEDIUM, LOW
    detail: str
    pattern: Optional[str] = None


@dataclass
class Classification:
    """Classification result for a file."""
    declared_layer: Optional[str]
    folder_layer: Optional[str]
    detected_layers: Dict[str, int]  # Layer -> signal count
    dominant_layer: Optional[str]
    layer_fit: bool
    confidence: str  # HIGH, MEDIUM, LOW


@dataclass
class FileClassification:
    """Complete classification of a single file."""
    file: str
    relative_path: str
    classification: Classification
    violations: List[Violation]
    misfit_type: Optional[str] = None
    remediation: Optional[str] = None
    refactor_action: Optional[str] = None  # Axis C: What work is needed
    estimated_effort: Optional[str] = None  # LOW, MEDIUM, HIGH


# =============================================================================
# Refactor Actions (Axis C - Work Type)
# =============================================================================

# Canonical refactor actions
REFACTOR_ACTIONS = {
    "HEADER_FIX_ONLY": "Fix header/metadata only, no code changes",
    "RECLASSIFY_ONLY": "Move file to correct folder, update header",
    "EXTRACT_DRIVER": "Extract DB operations to new L6 Driver service",
    "EXTRACT_AUTHORITY": "Move HTTP/decisions to appropriate layer",
    "SPLIT_FILE": "Split file into multiple single-responsibility files",
    "QUARANTINE_DUPLICATE": "Move to duplicate/ folder",
    "NO_ACTION": "File is correctly placed and classified",
}

# Effort estimates by action
ACTION_EFFORT = {
    "HEADER_FIX_ONLY": "LOW",
    "RECLASSIFY_ONLY": "LOW",
    "QUARANTINE_DUPLICATE": "LOW",
    "EXTRACT_DRIVER": "MEDIUM",
    "EXTRACT_AUTHORITY": "HIGH",
    "SPLIT_FILE": "HIGH",
    "NO_ACTION": "NONE",
}


# =============================================================================
# Layer Signal Mapping
# =============================================================================

# Map signal codes to canonical layers
SIGNAL_TO_LAYER = {
    "L2_API": "L2",
    "L3_ADAPTER": "L3",
    "L4_ENGINE": "L4",
    "L4_ENGINE_GOOD": "L4",
    "L5_WORKER": "L5",
    "L6_DRIVER": "L6",
    "L6_SCHEMA": "L6",
}

# Layer names for display
LAYER_NAMES = {
    "L2": "APIs",
    "L3": "Adapters",
    "L4": "Engines",
    "L5": "Workers",
    "L6": "Drivers/Schemas",
}

# Forbidden signals per layer (violations)
# Layer -> set of forbidden signal types
FORBIDDEN_SIGNALS = {
    "L2": set(),  # L2 is the HTTP boundary - can use FastAPI
    "L3": {"L6_DRIVER", "L2_API"},  # Adapters shouldn't do DB or HTTP
    "L4": {"L6_DRIVER", "L2_API"},  # Engines shouldn't do DB or HTTP
    "L5": {"L2_API"},  # Workers shouldn't do HTTP
    "L6": {"L2_API"},  # Drivers/Schemas shouldn't do HTTP
}

# Violation codes and severities
VIOLATION_SEVERITY = {
    "DRIFT": "HIGH",  # Declared != Detected
    "DATA_LEAK": "HIGH",  # Non-L6 touching DB
    "AUTHORITY_LEAK_HTTP": "HIGH",  # L4 doing HTTP
    "AUTHORITY_LEAK_SCHEDULE": "MEDIUM",  # L4 doing scheduling
    "EXECUTION_LEAK": "MEDIUM",  # L3/L5 doing retries
    "TEMPORAL_LEAK": "MEDIUM",  # sleep in wrong layers
    "SCOPE_CREEP": "MEDIUM",  # Does too much
    "LAYER_JUMP": "HIGH",  # Completely wrong layer
    "UNCLASSIFIED": "LOW",  # No layer declared
    "SIGNAL_MISMATCH": "LOW",  # Signals don't match expectations
    "NO_SIGNALS": "LOW",  # No detectable patterns
}


def extract_layer_counts(signals: List[dict]) -> Dict[str, int]:
    """Count signals by canonical layer."""
    counts: Dict[str, int] = defaultdict(int)

    for signal in signals:
        signal_layer = signal.get("layer", "")
        canonical = SIGNAL_TO_LAYER.get(signal_layer)
        if canonical:
            counts[canonical] += 1

    return dict(counts)


def get_dominant_layer(layer_counts: Dict[str, int]) -> Optional[str]:
    """Determine the dominant layer from signal counts."""
    if not layer_counts:
        return None

    # Sort by count descending
    sorted_layers = sorted(layer_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_layers[0][0]


def detect_violations(
    file_data: dict,
    declared_layer: Optional[str],
    folder_layer: Optional[str],
    detected_layers: Dict[str, int],
    dominant_layer: Optional[str],
) -> List[Violation]:
    """Detect all violations for a file."""
    violations = []
    signals = file_data.get("signals", [])

    # 1. DRIFT: Declared layer != Detected dominant layer
    if declared_layer and dominant_layer and declared_layer != dominant_layer:
        # Check if it's a significant mismatch
        declared_count = detected_layers.get(declared_layer, 0)
        dominant_count = detected_layers.get(dominant_layer, 0)

        if dominant_count > declared_count:
            violations.append(Violation(
                code="DRIFT",
                severity="HIGH",
                detail=f"Declared {declared_layer} but dominant signals are {dominant_layer} "
                       f"({dominant_count} vs {declared_count} signals)",
            ))

    # 2. DATA_LEAK: Non-L6 file has L6_DRIVER signals
    effective_layer = declared_layer or folder_layer
    if effective_layer and effective_layer != "L6":
        l6_count = detected_layers.get("L6", 0)
        if l6_count > 0:
            # Check for actual DB access patterns
            db_signals = [s for s in signals if s.get("layer") == "L6_DRIVER"]
            if db_signals:
                violations.append(Violation(
                    code="DATA_LEAK",
                    severity="HIGH",
                    detail=f"{effective_layer} file has {len(db_signals)} L6_DRIVER signals (DB access)",
                    pattern=db_signals[0].get("pattern") if db_signals else None,
                ))

    # 3. AUTHORITY_LEAK: L4 doing HTTP things
    if effective_layer == "L4":
        l2_signals = [s for s in signals if s.get("layer") == "L2_API"]
        # Filter out false positives (e.g., "Request" in non-HTTP context)
        http_signals = [s for s in l2_signals if s.get("pattern") in [
            r"@router\.(get|post|put|delete|patch)",
            r"return JSONResponse",
            r"raise HTTPException",
        ]]
        if http_signals:
            violations.append(Violation(
                code="AUTHORITY_LEAK_HTTP",
                severity="HIGH",
                detail=f"L4 Engine has HTTP-related code",
                pattern=http_signals[0].get("pattern"),
            ))

    # 4. TEMPORAL_LEAK: sleep patterns in wrong layers
    temporal_signals = [s for s in signals if s.get("violation") == "TEMPORAL_LEAK"]
    if temporal_signals and effective_layer in ["L3", "L4"]:
        violations.append(Violation(
            code="TEMPORAL_LEAK",
            severity="MEDIUM",
            detail=f"Temporal pattern (sleep/retry) in {effective_layer}",
            pattern=temporal_signals[0].get("pattern"),
        ))

    # 5. LAYER_JUMP: Folder layer != Declared layer (major mismatch)
    if folder_layer and declared_layer and folder_layer != declared_layer:
        # Allow L4 declared in engines/ (expected)
        # But flag L6 declared in engines/ or L4 declared in drivers/
        layer_distance = abs(int(folder_layer[1]) - int(declared_layer[1]))
        if layer_distance >= 2:
            violations.append(Violation(
                code="LAYER_JUMP",
                severity="HIGH",
                detail=f"Folder suggests {folder_layer} but declares {declared_layer}",
            ))

    return violations


def determine_refactor_action(
    layer_fit: bool,
    violations: List[Violation],
    declared_layer: Optional[str],
    folder_layer: Optional[str],
    detected_layers: Dict[str, int],
    dominant_layer: Optional[str],
) -> tuple:
    """Determine the canonical refactor action needed for a file.

    Returns (refactor_action, estimated_effort)
    """
    if layer_fit and not violations:
        return "NO_ACTION", "NONE"

    violation_codes = {v.code for v in violations}

    # Check for duplicate path patterns
    # (would be detected by path analysis, not implemented here yet)

    # Priority 1: If only DRIFT with no other violations and behavior matches folder
    if violation_codes == {"DRIFT"} and folder_layer == dominant_layer:
        return "HEADER_FIX_ONLY", "LOW"

    # Priority 2: If LAYER_JUMP only (wrong folder, correct behavior)
    if violation_codes == {"LAYER_JUMP"} and declared_layer == dominant_layer:
        return "RECLASSIFY_ONLY", "LOW"

    # Priority 3: If only detected layer is L6 but file is in non-L6 location
    # and no L4 signals - pure reclassification
    if (list(detected_layers.keys()) == ["L6"] and
        declared_layer and declared_layer != "L6" and
        "DATA_LEAK" not in violation_codes):
        return "RECLASSIFY_ONLY", "LOW"

    # Priority 4: DATA_LEAK - need to extract DB operations
    if "DATA_LEAK" in violation_codes:
        # Check if file has mixed L4 + L6 signals (needs extraction)
        if "L4" in detected_layers and "L6" in detected_layers:
            return "EXTRACT_DRIVER", "MEDIUM"
        # If only L6 signals in a non-L6 file, might just need reclassification
        elif list(detected_layers.keys()) == ["L6"]:
            return "RECLASSIFY_ONLY", "LOW"
        else:
            return "EXTRACT_DRIVER", "MEDIUM"

    # Priority 5: AUTHORITY_LEAK - need to extract HTTP/decisions
    if "AUTHORITY_LEAK_HTTP" in violation_codes:
        return "EXTRACT_AUTHORITY", "HIGH"

    # Priority 6: Multiple layer signals without clear dominant - SPLIT
    if len(detected_layers) >= 3:
        return "SPLIT_FILE", "HIGH"

    # Priority 7: TEMPORAL_LEAK - move to runtime
    if "TEMPORAL_LEAK" in violation_codes:
        return "EXTRACT_AUTHORITY", "MEDIUM"

    # Priority 8: DRIFT only (header mismatch)
    if "DRIFT" in violation_codes:
        # If dominant doesn't match declared, decide based on behavior
        if dominant_layer and declared_layer:
            if dominant_layer == folder_layer:
                # File behaves like its folder, header is wrong
                return "HEADER_FIX_ONLY", "LOW"
            elif declared_layer == folder_layer:
                # Header matches folder, but behavior is different - needs refactor
                if "L6" in detected_layers and declared_layer != "L6":
                    return "EXTRACT_DRIVER", "MEDIUM"
                else:
                    return "RECLASSIFY_ONLY", "LOW"
        return "HEADER_FIX_ONLY", "LOW"

    # Default: If we get here with violations, something needs fixing
    if violations:
        return "RECLASSIFY_ONLY", "LOW"

    return "NO_ACTION", "NONE"


def classify_file(file_data: dict) -> FileClassification:
    """Classify a single file."""
    relative_path = file_data.get("relative_path", "")
    header = file_data.get("header", {})
    signals = file_data.get("signals", [])

    # Extract layers
    declared_layer = header.get("declared_layer")
    folder_layer = file_data.get("folder_layer")

    # Count signals by layer
    detected_layers = extract_layer_counts(signals)
    dominant_layer = get_dominant_layer(detected_layers)

    # Determine layer fit
    effective_layer = declared_layer or folder_layer

    # Layer fit logic:
    # - If declared matches dominant (or dominant is L4 good signals for L4 files) -> FIT
    # - If no signals but folder matches declared -> FIT (schema files often have no signals)
    # - Otherwise -> MISFIT

    layer_fit = False
    confidence = "LOW"

    if not detected_layers:
        # No signals detected - trust folder/declared
        layer_fit = True
        confidence = "LOW"
    elif effective_layer and dominant_layer:
        if effective_layer == dominant_layer:
            layer_fit = True
            confidence = "HIGH"
        elif effective_layer == "L4" and "L4" in detected_layers:
            # L4 files may have L6 schema signals for return types
            l4_count = detected_layers.get("L4", 0)
            l6_count = detected_layers.get("L6", 0)
            if l4_count >= l6_count // 2:  # Allow some schema signals
                layer_fit = True
                confidence = "MEDIUM"
        elif effective_layer == "L6" and dominant_layer in ["L4", "L6"]:
            # L6 schema files may trigger L4 patterns
            layer_fit = True
            confidence = "MEDIUM"

    # Detect violations
    violations = detect_violations(
        file_data, declared_layer, folder_layer, detected_layers, dominant_layer
    )

    # If violations, layer_fit is false
    if any(v.severity == "HIGH" for v in violations):
        layer_fit = False

    # Determine misfit type
    misfit_type = None
    remediation = None

    if not layer_fit:
        if violations:
            # Use the highest severity violation as the misfit type
            sorted_violations = sorted(
                violations,
                key=lambda v: ["HIGH", "MEDIUM", "LOW"].index(v.severity)
            )
            misfit_type = sorted_violations[0].code
        else:
            # No explicit violation but still misfit - classify reason
            if not declared_layer and not folder_layer:
                misfit_type = "UNCLASSIFIED"
            elif detected_layers and dominant_layer:
                misfit_type = "SIGNAL_MISMATCH"
            else:
                misfit_type = "NO_SIGNALS"

        # Suggest remediation
        if misfit_type == "DRIFT":
            remediation = f"Update header to declare {dominant_layer} OR refactor to match declared layer"
        elif misfit_type == "DATA_LEAK":
            remediation = "Extract DB operations to a L6 Driver service"
        elif misfit_type == "AUTHORITY_LEAK_HTTP":
            remediation = "Move HTTP handling to L2 API layer"
        elif misfit_type == "TEMPORAL_LEAK":
            remediation = "Move temporal logic (sleep, retry) to L5 Worker or runtime infrastructure"
        elif misfit_type == "LAYER_JUMP":
            remediation = "Move file to correct folder matching declared layer"
        elif misfit_type == "UNCLASSIFIED":
            remediation = "Add layer header declaration and move to appropriate folder"
        elif misfit_type == "SIGNAL_MISMATCH":
            remediation = f"Review signals - dominant is {dominant_layer}, verify layer assignment"
        elif misfit_type == "NO_SIGNALS":
            remediation = "Add layer header declaration - no patterns detected"

    classification = Classification(
        declared_layer=declared_layer,
        folder_layer=folder_layer,
        detected_layers=detected_layers,
        dominant_layer=dominant_layer,
        layer_fit=layer_fit,
        confidence=confidence,
    )

    # Determine refactor action (Axis C)
    refactor_action, estimated_effort = determine_refactor_action(
        layer_fit=layer_fit,
        violations=violations,
        declared_layer=declared_layer,
        folder_layer=folder_layer,
        detected_layers=detected_layers,
        dominant_layer=dominant_layer,
    )

    return FileClassification(
        file=file_data.get("file", ""),
        relative_path=relative_path,
        classification=classification,
        violations=violations,
        misfit_type=misfit_type,
        remediation=remediation,
        refactor_action=refactor_action,
        estimated_effort=estimated_effort,
    )


def generate_summary_markdown(
    classifications: List[FileClassification],
    signal_counts: Dict[str, int],
) -> str:
    """Generate markdown summary report."""
    lines = [
        "# HOC Layer Fit Analysis Report",
        "",
        f"**Generated:** {date.today()}",
        f"**Files Analyzed:** {len(classifications)}",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
    ]

    # Count fits and misfits
    fit_count = sum(1 for c in classifications if c.classification.layer_fit)
    misfit_count = len(classifications) - fit_count

    fit_pct = (fit_count / len(classifications) * 100) if classifications else 0
    misfit_pct = (misfit_count / len(classifications) * 100) if classifications else 0

    lines.extend([
        "| Status | Count | % |",
        "|--------|-------|---|",
        f"| **LAYER_FIT** | {fit_count} | {fit_pct:.1f}% |",
        f"| **MISFIT** | {misfit_count} | {misfit_pct:.1f}% |",
        "",
    ])

    # Violation breakdown
    violation_counts: Dict[str, int] = defaultdict(int)
    for c in classifications:
        for v in c.violations:
            violation_counts[v.code] += 1

    if violation_counts:
        lines.extend([
            "## 2. Violation Breakdown",
            "",
            "| Violation | Count | Severity |",
            "|-----------|-------|----------|",
        ])
        for code, count in sorted(violation_counts.items(), key=lambda x: -x[1]):
            severity = VIOLATION_SEVERITY.get(code, "UNKNOWN")
            lines.append(f"| {code} | {count} | {severity} |")
        lines.append("")

    # Layer distribution
    layer_counts: Dict[str, int] = defaultdict(int)
    for c in classifications:
        if c.classification.dominant_layer:
            layer_counts[c.classification.dominant_layer] += 1

    lines.extend([
        "## 3. Layer Distribution (by dominant signals)",
        "",
        "| Layer | Name | Files |",
        "|-------|------|-------|",
    ])
    for layer in ["L2", "L3", "L4", "L5", "L6"]:
        name = LAYER_NAMES.get(layer, "")
        count = layer_counts.get(layer, 0)
        lines.append(f"| {layer} | {name} | {count} |")
    lines.append("")

    # Signal distribution from input
    lines.extend([
        "## 4. Signal Distribution (from Pass 1)",
        "",
        "| Signal Type | Count |",
        "|-------------|-------|",
    ])
    for signal_type, count in sorted(signal_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| {signal_type} | {count} |")
    lines.append("")

    # Top misfits
    misfits = [c for c in classifications if not c.classification.layer_fit]
    if misfits:
        lines.extend([
            "## 5. Misfit Files (Requiring Remediation)",
            "",
        ])

        # Group by misfit type
        by_type: Dict[str, List[FileClassification]] = defaultdict(list)
        for m in misfits:
            by_type[m.misfit_type or "UNKNOWN"].append(m)

        for misfit_type, files in sorted(by_type.items()):
            lines.extend([
                f"### {misfit_type} ({len(files)} files)",
                "",
            ])

            # Show top 10
            for f in files[:10]:
                declared = f.classification.declared_layer or "?"
                dominant = f.classification.dominant_layer or "?"
                lines.append(f"- `{f.relative_path}`")
                lines.append(f"  - Declared: {declared}, Dominant: {dominant}")
                if f.violations:
                    lines.append(f"  - Issue: {f.violations[0].detail}")
                if f.remediation:
                    lines.append(f"  - Remediation: {f.remediation}")

            if len(files) > 10:
                lines.append(f"- ... and {len(files) - 10} more")
            lines.append("")

    # Fit files by confidence
    fits = [c for c in classifications if c.classification.layer_fit]
    confidence_counts = Counter(f.classification.confidence for f in fits)

    lines.extend([
        "## 6. Layer Fit Confidence",
        "",
        "| Confidence | Count |",
        "|------------|-------|",
    ])
    for conf in ["HIGH", "MEDIUM", "LOW"]:
        lines.append(f"| {conf} | {confidence_counts.get(conf, 0)} |")
    lines.append("")

    # Work Backlog by Refactor Action (KEY SECTION)
    action_counts: Dict[str, int] = defaultdict(int)
    effort_totals: Dict[str, int] = defaultdict(int)
    for c in classifications:
        if c.refactor_action:
            action_counts[c.refactor_action] += 1
            if c.estimated_effort == "LOW":
                effort_totals["LOW"] += 1
            elif c.estimated_effort == "MEDIUM":
                effort_totals["MEDIUM"] += 1
            elif c.estimated_effort == "HIGH":
                effort_totals["HIGH"] += 1

    lines.extend([
        "---",
        "",
        "## 7. WORK BACKLOG (By Refactor Action)",
        "",
        "> **This is the actionable migration plan.**",
        "> Execute in this order for minimal risk and maximum efficiency.",
        "",
        "| # | Action | Files | Effort | Description |",
        "|---|--------|-------|--------|-------------|",
    ])

    # Migration order (from GPT feedback)
    migration_order = [
        "HEADER_FIX_ONLY",
        "RECLASSIFY_ONLY",
        "QUARANTINE_DUPLICATE",
        "EXTRACT_DRIVER",
        "EXTRACT_AUTHORITY",
        "SPLIT_FILE",
        "NO_ACTION",
    ]

    order_num = 1
    for action in migration_order:
        count = action_counts.get(action, 0)
        if count > 0:
            effort = ACTION_EFFORT.get(action, "?")
            desc = REFACTOR_ACTIONS.get(action, "")
            lines.append(f"| {order_num} | **{action}** | {count} | {effort} | {desc} |")
            order_num += 1

    lines.append("")

    # Effort summary
    total_work = sum(action_counts.values()) - action_counts.get("NO_ACTION", 0)
    lines.extend([
        "### Effort Summary",
        "",
        "| Effort Level | Files |",
        "|--------------|-------|",
        f"| LOW (quick wins) | {effort_totals.get('LOW', 0)} |",
        f"| MEDIUM (standard) | {effort_totals.get('MEDIUM', 0)} |",
        f"| HIGH (complex) | {effort_totals.get('HIGH', 0)} |",
        f"| **Total Work Items** | **{total_work}** |",
        "",
    ])

    # Sample files for each action (for context)
    lines.extend([
        "### Sample Files by Action",
        "",
    ])

    for action in migration_order:
        if action == "NO_ACTION":
            continue
        action_files = [c for c in classifications if c.refactor_action == action]
        if action_files:
            lines.append(f"#### {action} ({len(action_files)} files)")
            lines.append("")
            for f in action_files[:5]:
                declared = f.classification.declared_layer or "?"
                dominant = f.classification.dominant_layer or "?"
                lines.append(f"- `{f.relative_path}` (declared: {declared}, detected: {dominant})")
            if len(action_files) > 5:
                lines.append(f"- ... and {len(action_files) - 5} more")
            lines.append("")

    lines.extend([
        "---",
        "",
        "## 8. Recommended Migration Order",
        "",
        "1. **HEADER_FIX_ONLY** - Fast wins, improves signal accuracy",
        "2. **RECLASSIFY_ONLY** - Folder hygiene, zero logic risk",
        "3. **QUARANTINE_DUPLICATE** - Reduces noise, prevents double work",
        "4. **EXTRACT_DRIVER** - Biggest category, needs conventions first",
        "5. **EXTRACT_AUTHORITY** - High risk, requires L4 runtime stability",
        "6. **SPLIT_FILE** - Last, architectural surgery",
        "",
    ])

    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="HOC Layer Classification (Pass 2)")
    parser.add_argument("--input", default=str(INPUT_FILE), help="Input signals JSON")
    parser.add_argument("--output-json", default=str(OUTPUT_JSON), help="Output JSON")
    parser.add_argument("--output-md", default=str(OUTPUT_MD), help="Output Markdown")
    args = parser.parse_args()

    print("=" * 60)
    print("HOC LAYER ANALYSIS - PASS 2: CLASSIFICATION")
    print("=" * 60)

    # Load signals
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        print("Run layer_analysis.py (Pass 1) first.")
        return 1

    with open(input_path) as f:
        data = json.load(f)

    files = data.get("files", [])
    signal_counts = data.get("meta", {}).get("signal_counts", {})

    print(f"\nInput file: {input_path}")
    print(f"Files to classify: {len(files)}")

    # Classify each file
    classifications = []
    for file_data in files:
        c = classify_file(file_data)
        classifications.append(c)

    # Count results
    fit_count = sum(1 for c in classifications if c.classification.layer_fit)
    misfit_count = len(classifications) - fit_count

    print(f"\nClassification Results:")
    print(f"  LAYER_FIT: {fit_count}")
    print(f"  MISFIT: {misfit_count}")

    # Count violations
    violation_counts: Dict[str, int] = defaultdict(int)
    for c in classifications:
        for v in c.violations:
            violation_counts[v.code] += 1

    if violation_counts:
        print(f"\nViolations Detected:")
        for code, count in sorted(violation_counts.items(), key=lambda x: -x[1]):
            print(f"  {code}: {count}")

    # Count refactor actions
    action_counts: Dict[str, int] = defaultdict(int)
    for c in classifications:
        if c.refactor_action:
            action_counts[c.refactor_action] += 1

    total_work = sum(action_counts.values()) - action_counts.get("NO_ACTION", 0)

    print(f"\n" + "=" * 60)
    print("WORK BACKLOG (By Refactor Action)")
    print("=" * 60)

    migration_order = [
        "HEADER_FIX_ONLY",
        "RECLASSIFY_ONLY",
        "QUARANTINE_DUPLICATE",
        "EXTRACT_DRIVER",
        "EXTRACT_AUTHORITY",
        "SPLIT_FILE",
        "NO_ACTION",
    ]

    for action in migration_order:
        count = action_counts.get(action, 0)
        if count > 0:
            effort = ACTION_EFFORT.get(action, "?")
            print(f"  {action}: {count} files ({effort} effort)")

    print(f"\n  TOTAL WORK ITEMS: {total_work}")

    # Write JSON output
    output_json_path = Path(args.output_json)
    output_json_path.parent.mkdir(parents=True, exist_ok=True)

    def to_dict(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return obj

    output_data = {
        "meta": {
            "generated": str(date.today()),
            "files_classified": len(classifications),
            "layer_fit_count": fit_count,
            "misfit_count": misfit_count,
            "violation_counts": dict(violation_counts),
            "action_counts": dict(action_counts),
            "total_work_items": total_work,
        },
        "files": [to_dict(c) for c in classifications],
    }

    with open(output_json_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\nJSON output written to: {output_json_path}")

    # Write markdown summary
    output_md_path = Path(args.output_md)
    summary = generate_summary_markdown(classifications, signal_counts)

    with open(output_md_path, "w") as f:
        f.write(summary)

    print(f"Markdown summary written to: {output_md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
