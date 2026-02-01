#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Domain Classifier V1 - Header-Based Classification
# artifact_class: CODE
"""
Domain Classifier V1 - Header-Based Classification

Scans all .py files under hoc/cus/ and classifies them by domain
based on file headers and DOMAIN_CRITERIA.yaml rules.

Usage:
    python scripts/ops/domain_classifier_v1.py
    python scripts/ops/domain_classifier_v1.py --output /path/to/output.csv
    python scripts/ops/domain_classifier_v1.py --verbose

Output:
    backend/app/hoc/cus/_domain_map/shadow_domain_map_v1.csv

Reference:
    docs/architecture/console_domains/DOMAIN_LANGUAGE_GUIDE.md
    docs/architecture/console_domains/DOMAIN_CRITERIA.yaml
"""

import argparse
import csv
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

# Paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent
HOC_CUS_PATH = REPO_ROOT / "backend" / "app" / "hoc" / "cus"
CRITERIA_PATH = REPO_ROOT / "docs" / "architecture" / "console_domains" / "DOMAIN_CRITERIA.yaml"
DEFAULT_OUTPUT_DIR = HOC_CUS_PATH / "_domain_map"
DEFAULT_OUTPUT_FILE = DEFAULT_OUTPUT_DIR / "shadow_domain_map_v1.csv"


@dataclass
class FileHeader:
    """Extracted header information from a Python file."""
    layer: str = ""
    audience: str = ""
    role: str = ""
    data_access_reads: str = ""
    data_access_writes: str = ""
    product: str = ""
    raw_header: str = ""


@dataclass
class ClassificationResult:
    """Result of domain classification."""
    file_path: str
    current_domain: str
    layer: str
    header_quality: str  # FULL, PARTIAL, MISSING
    role_text: str
    inferred_domain: str
    confidence: str  # HIGH, MEDIUM, LOW
    needs_split: bool
    evidence: str
    notes: str = ""


def load_criteria(path: Path) -> dict:
    """Load DOMAIN_CRITERIA.yaml."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def extract_header(file_path: Path, max_lines: int = 50) -> FileHeader:
    """Extract structured header information from first N lines."""
    header = FileHeader()
    lines = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
    except Exception as e:
        header.raw_header = f"ERROR: {e}"
        return header

    raw = ''.join(lines)
    header.raw_header = raw[:500]  # Truncate for storage

    # Extract Layer
    match = re.search(r'#\s*Layer:\s*([^\n]+)', raw, re.IGNORECASE)
    if match:
        header.layer = match.group(1).strip()

    # Extract AUDIENCE
    match = re.search(r'#\s*AUDIENCE:\s*([^\n]+)', raw, re.IGNORECASE)
    if match:
        header.audience = match.group(1).strip()

    # Extract Role
    match = re.search(r'#\s*Role:\s*([^\n]+)', raw, re.IGNORECASE)
    if match:
        header.role = match.group(1).strip()

    # Extract Data Access
    match = re.search(r'#\s*Data Access:[^\n]*\n#\s*Reads:\s*([^\n]+)', raw, re.IGNORECASE)
    if match:
        header.data_access_reads = match.group(1).strip()

    match = re.search(r'#\s*Writes:\s*([^\n]+)', raw, re.IGNORECASE)
    if match:
        header.data_access_writes = match.group(1).strip()

    # Extract Product
    match = re.search(r'#\s*Product:\s*([^\n]+)', raw, re.IGNORECASE)
    if match:
        header.product = match.group(1).strip()

    # Also check docstring for role info
    docstring_match = re.search(r'"""([^"]{10,500})"""', raw, re.DOTALL)
    if docstring_match and not header.role:
        # Use first line of docstring as role
        first_line = docstring_match.group(1).strip().split('\n')[0]
        header.role = first_line[:200]

    return header


def get_header_quality(header: FileHeader) -> str:
    """Determine header quality: FULL, PARTIAL, MISSING."""
    has_layer = bool(header.layer)
    has_role = bool(header.role)
    has_audience = bool(header.audience)

    if has_layer and has_role and has_audience:
        return "FULL"
    elif has_role or has_layer:
        return "PARTIAL"
    else:
        return "MISSING"


def extract_current_domain(file_path: Path, hoc_cus_root: Path) -> str:
    """Extract current domain from file path."""
    try:
        rel_path = file_path.relative_to(hoc_cus_root)
        parts = rel_path.parts
        if len(parts) >= 1:
            return parts[0]  # First directory is the domain
    except ValueError:
        pass
    return "unknown"


def check_unqualified_keywords(text: str, ambiguous_keywords: list) -> list:
    """Check for unqualified ambiguous keywords."""
    text_lower = text.lower()
    unqualified = []

    for kw in ambiguous_keywords:
        if kw.lower() in text_lower:
            unqualified.append(kw)

    return unqualified


def classify_file(
    header: FileHeader,
    criteria: dict,
    verbose: bool = False
) -> tuple[str, str, str, bool]:
    """
    Classify file based on header and criteria.

    Returns: (inferred_domain, confidence, evidence, needs_split)
    """
    role_text = header.role.lower()
    combined_text = f"{header.role} {header.data_access_reads} {header.data_access_writes}".lower()

    if not role_text and not combined_text.strip():
        return ("UNKNOWN", "LOW", "No role text found", False)

    ambiguous_keywords = criteria.get('ambiguous_keywords', [])
    scoring_rules = criteria.get('scoring', {})
    phrase_weight = scoring_rules.get('qualifier_phrase_weight', 3)
    weak_weight = scoring_rules.get('weak_keyword_weight', 1)
    weak_max = scoring_rules.get('weak_keyword_max', 2)
    margin_threshold = scoring_rules.get('ambiguous_margin_threshold', 3)

    domains = criteria.get('domains', {})
    results = []

    for domain_name, domain_criteria in domains.items():
        score = 0
        evidence = []
        vetoed = False

        # Check qualifier phrases (HIGH weight)
        for phrase in domain_criteria.get('qualifier_phrases', []):
            if phrase.lower() in combined_text:
                score += phrase_weight
                evidence.append(f"phrase:{phrase}")

        # Check veto phrases (HARD BLOCK)
        for veto in domain_criteria.get('veto_phrases', []):
            if veto.lower() in combined_text:
                vetoed = True
                if verbose:
                    print(f"  VETO: {domain_name} blocked by '{veto}'")
                break

        if vetoed:
            continue

        # Weak keywords (LOW weight, capped)
        weak_score = 0
        for kw in domain_criteria.get('weak_keywords', []):
            if kw.lower() in combined_text:
                weak_score += weak_weight
        score += min(weak_score, weak_max)

        if score > 0:
            results.append((domain_name, score, evidence))

    if not results:
        # Check if it's due to unqualified keywords
        unqualified = check_unqualified_keywords(combined_text, ambiguous_keywords)
        if unqualified:
            return ("AMBIGUOUS", "LOW", f"Unqualified keywords: {unqualified}", False)
        return ("AMBIGUOUS", "LOW", "No phrase match", False)

    # Sort by score descending
    results.sort(key=lambda x: -x[1])

    best = results[0]

    # Check margin for ambiguity
    if len(results) >= 2:
        margin = best[1] - results[1][1]
        if margin < margin_threshold:
            needs_split = True
            return (
                "AMBIGUOUS",
                "LOW",
                f"Close: {best[0]}={best[1]} vs {results[1][0]}={results[1][1]}",
                needs_split
            )

    # Determine confidence
    if best[1] >= 6:
        confidence = "HIGH"
    elif best[1] >= 3:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    evidence_str = "; ".join(best[2][:5])  # Limit evidence items

    return (best[0], confidence, evidence_str, False)


def scan_files(hoc_cus_path: Path) -> list[Path]:
    """Scan for all Python files under hoc/cus/."""
    files = []
    for root, dirs, filenames in os.walk(hoc_cus_path):
        # Skip __pycache__ and _domain_map
        dirs[:] = [d for d in dirs if d not in ('__pycache__', '_domain_map', '.git')]

        for filename in filenames:
            if filename.endswith('.py') and filename != '__init__.py':
                files.append(Path(root) / filename)

    return sorted(files)


def run_classification(
    hoc_cus_path: Path,
    criteria_path: Path,
    output_path: Path,
    verbose: bool = False
) -> list[ClassificationResult]:
    """Run classification on all files."""

    # Load criteria
    print(f"Loading criteria from: {criteria_path}")
    criteria = load_criteria(criteria_path)

    # Scan files
    print(f"Scanning files under: {hoc_cus_path}")
    files = scan_files(hoc_cus_path)
    print(f"Found {len(files)} Python files (excluding __init__.py)")

    results = []

    for file_path in files:
        if verbose:
            print(f"\nProcessing: {file_path.name}")

        # Extract header
        header = extract_header(file_path)

        # Get current domain from path
        current_domain = extract_current_domain(file_path, hoc_cus_path)

        # Get header quality
        header_quality = get_header_quality(header)

        # Classify
        inferred_domain, confidence, evidence, needs_split = classify_file(
            header, criteria, verbose
        )

        # Determine notes
        notes = ""
        if current_domain != inferred_domain and inferred_domain not in ("AMBIGUOUS", "UNKNOWN"):
            notes = f"MISPLACED: currently in {current_domain}"
        elif inferred_domain == "AMBIGUOUS":
            notes = "Needs manual review"
        elif inferred_domain == "UNKNOWN":
            notes = "Missing header information"

        # Build relative path for output
        try:
            rel_path = str(file_path.relative_to(hoc_cus_path))
        except ValueError:
            rel_path = str(file_path)

        result = ClassificationResult(
            file_path=rel_path,
            current_domain=current_domain,
            layer=header.layer or "unknown",
            header_quality=header_quality,
            role_text=header.role[:200] if header.role else "",
            inferred_domain=inferred_domain,
            confidence=confidence,
            needs_split=needs_split,
            evidence=evidence,
            notes=notes
        )

        results.append(result)

        if verbose:
            print(f"  Current: {current_domain} -> Inferred: {inferred_domain} ({confidence})")

    return results


def write_csv(results: list[ClassificationResult], output_path: Path):
    """Write results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'file_path',
        'current_domain',
        'layer',
        'header_quality',
        'role_text',
        'inferred_domain',
        'confidence',
        'needs_split',
        'evidence',
        'notes'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for result in results:
            writer.writerow({
                'file_path': result.file_path,
                'current_domain': result.current_domain,
                'layer': result.layer,
                'header_quality': result.header_quality,
                'role_text': result.role_text,
                'inferred_domain': result.inferred_domain,
                'confidence': result.confidence,
                'needs_split': 'YES' if result.needs_split else 'NO',
                'evidence': result.evidence,
                'notes': result.notes
            })

    print(f"\nWrote {len(results)} rows to: {output_path}")


def print_summary(results: list[ClassificationResult]):
    """Print classification summary."""
    print("\n" + "=" * 60)
    print("CLASSIFICATION SUMMARY")
    print("=" * 60)

    # Count by inferred domain
    domain_counts = {}
    for r in results:
        domain_counts[r.inferred_domain] = domain_counts.get(r.inferred_domain, 0) + 1

    print("\nBy Inferred Domain:")
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        print(f"  {domain:20} {count:4}")

    # Count by confidence
    conf_counts = {}
    for r in results:
        conf_counts[r.confidence] = conf_counts.get(r.confidence, 0) + 1

    print("\nBy Confidence:")
    for conf, count in sorted(conf_counts.items()):
        print(f"  {conf:20} {count:4}")

    # Count misplacements
    misplaced = [r for r in results if "MISPLACED" in r.notes]
    print(f"\nMisplaced Files: {len(misplaced)}")

    # Count ambiguous
    ambiguous = [r for r in results if r.inferred_domain == "AMBIGUOUS"]
    print(f"Ambiguous Files: {len(ambiguous)}")

    # Count needs_split
    needs_split = [r for r in results if r.needs_split]
    print(f"Needs Split: {len(needs_split)}")

    # Header quality
    quality_counts = {}
    for r in results:
        quality_counts[r.header_quality] = quality_counts.get(r.header_quality, 0) + 1

    print("\nHeader Quality:")
    for quality, count in sorted(quality_counts.items()):
        print(f"  {quality:20} {count:4}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Domain Classifier V1 - Header-Based Classification"
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output CSV path (default: {DEFAULT_OUTPUT_FILE})"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Verbose output"
    )
    parser.add_argument(
        '--criteria', '-c',
        type=Path,
        default=CRITERIA_PATH,
        help=f"Path to DOMAIN_CRITERIA.yaml (default: {CRITERIA_PATH})"
    )

    args = parser.parse_args()

    # Validate paths
    if not HOC_CUS_PATH.exists():
        print(f"ERROR: HOC_CUS_PATH does not exist: {HOC_CUS_PATH}")
        sys.exit(1)

    if not args.criteria.exists():
        print(f"ERROR: Criteria file does not exist: {args.criteria}")
        sys.exit(1)

    # Run classification
    results = run_classification(
        hoc_cus_path=HOC_CUS_PATH,
        criteria_path=args.criteria,
        output_path=args.output,
        verbose=args.verbose
    )

    # Write output
    write_csv(results, args.output)

    # Print summary
    print_summary(results)

    print(f"\nDone. Review output at: {args.output}")


if __name__ == "__main__":
    main()
