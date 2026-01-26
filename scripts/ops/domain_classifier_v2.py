#!/usr/bin/env python3
"""
Domain Classifier V2 - Code Block Analysis

Reads shadow_domain_map_v1.csv and performs deeper code analysis
on files with confidence < HIGH to improve classification accuracy.

Analyzes:
- Function/method names
- Class names
- Import statements
- Return type hints
- Docstrings
- Variable names in key positions

Usage:
    python scripts/ops/domain_classifier_v2.py
    python scripts/ops/domain_classifier_v2.py --input v1.csv --output v2.csv
    python scripts/ops/domain_classifier_v2.py --verbose

Output:
    backend/app/hoc/cus/_domain_map/shadow_domain_map_v2.csv

Reference:
    docs/architecture/console_domains/DOMAIN_LANGUAGE_GUIDE.md
    docs/architecture/console_domains/DOMAIN_CRITERIA.yaml
"""

import argparse
import ast
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

# Paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent.parent
HOC_CUS_PATH = REPO_ROOT / "backend" / "app" / "hoc" / "cus"
CRITERIA_PATH = REPO_ROOT / "docs" / "architecture" / "console_domains" / "DOMAIN_CRITERIA.yaml"
DEFAULT_INPUT = HOC_CUS_PATH / "_domain_map" / "shadow_domain_map_v1.csv"
DEFAULT_OUTPUT = HOC_CUS_PATH / "_domain_map" / "shadow_domain_map_v2.csv"


@dataclass
class CodeAnalysis:
    """Results of code block analysis."""
    class_names: list[str]
    function_names: list[str]
    imports: list[str]
    return_types: list[str]
    docstrings: list[str]
    key_variables: list[str]
    decorators: list[str]


@dataclass
class V2Result:
    """V2 classification result."""
    file_path: str
    current_domain: str
    layer: str
    header_quality: str
    role_text: str
    v1_inferred_domain: str
    v1_confidence: str
    v2_inferred_domain: str
    v2_confidence: str
    v2_override: bool
    needs_split: bool
    evidence: str
    notes: str


def load_criteria(path: Path) -> dict:
    """Load DOMAIN_CRITERIA.yaml."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def load_v1_results(path: Path) -> list[dict]:
    """Load V1 classification results."""
    results = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results


def analyze_code(file_path: Path) -> Optional[CodeAnalysis]:
    """Perform AST-based code analysis."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
    except Exception:
        return None

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    analysis = CodeAnalysis(
        class_names=[],
        function_names=[],
        imports=[],
        return_types=[],
        docstrings=[],
        key_variables=[],
        decorators=[]
    )

    for node in ast.walk(tree):
        # Class names
        if isinstance(node, ast.ClassDef):
            analysis.class_names.append(node.name.lower())
            # Get class docstring
            if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant)):
                doc = str(node.body[0].value.value)[:200]
                analysis.docstrings.append(doc.lower())

        # Function names
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            analysis.function_names.append(node.name.lower())

            # Get function docstring
            if (node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant)):
                doc = str(node.body[0].value.value)[:200]
                analysis.docstrings.append(doc.lower())

            # Get return type annotation
            if node.returns:
                try:
                    ret_type = ast.unparse(node.returns).lower()
                    analysis.return_types.append(ret_type)
                except Exception:
                    pass

            # Get decorators
            for decorator in node.decorator_list:
                try:
                    dec_name = ast.unparse(decorator).lower()
                    analysis.decorators.append(dec_name)
                except Exception:
                    pass

        # Imports
        elif isinstance(node, ast.Import):
            for alias in node.names:
                analysis.imports.append(alias.name.lower())
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                analysis.imports.append(node.module.lower())
            for alias in node.names:
                analysis.imports.append(alias.name.lower())

        # Key variable assignments (class-level or module-level)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    analysis.key_variables.append(target.id.lower())

    return analysis


def build_code_text(analysis: CodeAnalysis) -> str:
    """Build combined text from code analysis for matching."""
    parts = []

    # Class names are strong signals
    parts.extend(analysis.class_names)

    # Function names
    parts.extend(analysis.function_names)

    # Imports (extract last part for matching)
    for imp in analysis.imports:
        parts.append(imp.split('.')[-1])

    # Return types
    parts.extend(analysis.return_types)

    # Docstrings
    parts.extend(analysis.docstrings)

    # Key variables
    parts.extend(analysis.key_variables)

    return ' '.join(parts)


def classify_from_code(
    code_text: str,
    role_text: str,
    criteria: dict,
    verbose: bool = False
) -> tuple[str, str, str, bool]:
    """
    Classify based on code analysis combined with role text.

    Returns: (inferred_domain, confidence, evidence, needs_split)
    """
    # Combine role text and code text for matching
    combined = f"{role_text} {code_text}".lower()

    ambiguous_keywords = criteria.get('ambiguous_keywords', [])
    scoring_rules = criteria.get('scoring', {})
    phrase_weight = scoring_rules.get('qualifier_phrase_weight', 3)
    weak_weight = scoring_rules.get('weak_keyword_weight', 1)
    weak_max = scoring_rules.get('weak_keyword_max', 2)
    margin_threshold = scoring_rules.get('ambiguous_margin_threshold', 3)

    domains = criteria.get('domains', {})
    results = []

    # Code-specific patterns (stronger signals from actual code)
    code_patterns = {
        'general': [
            'orchestrator', 'coordinator', 'runtime', 'gateway',
            'governance_orchestrator', 'job_executor', 'contract_'
        ],
        'policies': [
            'policy_', 'rule_', 'proposal_', 'policyengine',
            'policydriver', 'ruleengine', 'governance_rule'
        ],
        'controls': [
            'killswitch', 'circuit_breaker', 'throttle', 'quota',
            'limit_', 'threshold_config', 'feature_flag', 'controlconfig'
        ],
        'incidents': [
            'incident_', 'severity_', 'failure_', 'violation_',
            'guard_', 'recurrence', 'incidentengine', 'incidentdriver'
        ],
        'activity': [
            'run_', 'trace_', 'activity_', 'execution_',
            'rundriver', 'activityengine', 'traceengine'
        ],
        'analytics': [
            'metric_', 'cost_', 'divergence', 'statistic',
            'aggregate', 'analyticsengine', 'costengine'
        ],
        'overview': [
            'dashboard', 'summary_', 'overview_', 'snapshot',
            'health_summary', 'status_overview'
        ],
        'logs': [
            'audit_', 'evidence_', 'ledger', 'log_',
            'auditengine', 'evidenceengine', 'completeness'
        ],
        'integrations': [
            'integration_', 'adapter_', 'webhook_', 'connector',
            'external_', 'sdk_', 'graduation'
        ],
        'apis': [
            'apikey', 'api_key', 'scope_', 'permission_',
            'keydriver', 'keysengine', 'accesscontrol'
        ],
        'account': [
            'tenant_', 'member_', 'subscription', 'billing',
            'tenantengine', 'tenantdriver', 'accountengine'
        ]
    }

    for domain_name, domain_criteria in domains.items():
        score = 0
        evidence = []
        vetoed = False

        # 1. Check qualifier phrases from criteria (weight: 3)
        for phrase in domain_criteria.get('qualifier_phrases', []):
            if phrase.lower() in combined:
                score += phrase_weight
                evidence.append(f"phrase:{phrase}")

        # 2. Check code-specific patterns (weight: 2 - code is more reliable)
        code_weight = 2
        for pattern in code_patterns.get(domain_name, []):
            if pattern in code_text:
                score += code_weight
                evidence.append(f"code:{pattern}")

        # 3. Check veto phrases (HARD BLOCK)
        for veto in domain_criteria.get('veto_phrases', []):
            if veto.lower() in combined:
                vetoed = True
                if verbose:
                    print(f"  VETO: {domain_name} blocked by '{veto}'")
                break

        if vetoed:
            continue

        # 4. Weak keywords (LOW weight, capped)
        weak_score = 0
        for kw in domain_criteria.get('weak_keywords', []):
            if kw.lower() in combined:
                weak_score += weak_weight
        score += min(weak_score, weak_max)

        if score > 0:
            results.append((domain_name, score, evidence))

    if not results:
        return ("AMBIGUOUS", "LOW", "No pattern match in code", False)

    # Sort by score descending
    results.sort(key=lambda x: -x[1])

    best = results[0]

    # Check margin for ambiguity
    needs_split = False
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

    # Determine confidence (higher thresholds for V2 since we have more data)
    if best[1] >= 8:
        confidence = "HIGH"
    elif best[1] >= 4:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    evidence_str = "; ".join(best[2][:5])

    return (best[0], confidence, evidence_str, needs_split)


def process_v2(
    v1_results: list[dict],
    hoc_cus_path: Path,
    criteria: dict,
    verbose: bool = False
) -> list[V2Result]:
    """Process V2 classification."""
    results = []

    # Count files to process
    to_process = [r for r in v1_results if r['confidence'] != 'HIGH']
    high_confidence = [r for r in v1_results if r['confidence'] == 'HIGH']

    print(f"V1 Results: {len(v1_results)} total")
    print(f"  HIGH confidence (skip): {len(high_confidence)}")
    print(f"  LOW/MEDIUM (analyze): {len(to_process)}")
    print()

    for row in v1_results:
        file_path = row['file_path']
        full_path = hoc_cus_path / file_path

        # Keep HIGH confidence as-is
        if row['confidence'] == 'HIGH':
            result = V2Result(
                file_path=file_path,
                current_domain=row['current_domain'],
                layer=row['layer'],
                header_quality=row['header_quality'],
                role_text=row['role_text'],
                v1_inferred_domain=row['inferred_domain'],
                v1_confidence=row['confidence'],
                v2_inferred_domain=row['inferred_domain'],
                v2_confidence=row['confidence'],
                v2_override=False,
                needs_split=row['needs_split'] == 'YES',
                evidence=row['evidence'],
                notes=row['notes']
            )
            results.append(result)
            continue

        if verbose:
            print(f"Analyzing: {file_path}")

        # Perform code analysis
        analysis = analyze_code(full_path)

        if analysis is None:
            # Can't parse, keep V1 result
            result = V2Result(
                file_path=file_path,
                current_domain=row['current_domain'],
                layer=row['layer'],
                header_quality=row['header_quality'],
                role_text=row['role_text'],
                v1_inferred_domain=row['inferred_domain'],
                v1_confidence=row['confidence'],
                v2_inferred_domain=row['inferred_domain'],
                v2_confidence=row['confidence'],
                v2_override=False,
                needs_split=row['needs_split'] == 'YES',
                evidence=row['evidence'],
                notes=f"{row['notes']}; V2: parse error"
            )
            results.append(result)
            continue

        # Build code text for matching
        code_text = build_code_text(analysis)

        # Classify from code
        v2_domain, v2_confidence, v2_evidence, needs_split = classify_from_code(
            code_text,
            row['role_text'],
            criteria,
            verbose
        )

        # Check if V2 overrides V1
        v2_override = (v2_domain != row['inferred_domain'] and
                       v2_domain != 'AMBIGUOUS' and
                       v2_confidence in ('HIGH', 'MEDIUM'))

        # Build notes
        notes = row['notes']
        if v2_override:
            notes = f"V2 OVERRIDE: {row['inferred_domain']} -> {v2_domain}"
            if row['current_domain'] != v2_domain:
                notes += f"; MISPLACED in {row['current_domain']}"
        elif v2_domain == row['inferred_domain'] and v2_confidence != row['confidence']:
            notes = f"V2 confidence: {row['confidence']} -> {v2_confidence}"

        result = V2Result(
            file_path=file_path,
            current_domain=row['current_domain'],
            layer=row['layer'],
            header_quality=row['header_quality'],
            role_text=row['role_text'],
            v1_inferred_domain=row['inferred_domain'],
            v1_confidence=row['confidence'],
            v2_inferred_domain=v2_domain,
            v2_confidence=v2_confidence,
            v2_override=v2_override,
            needs_split=needs_split,
            evidence=v2_evidence,
            notes=notes
        )
        results.append(result)

        if verbose and v2_override:
            print(f"  OVERRIDE: {row['inferred_domain']} -> {v2_domain}")

    return results


def write_csv(results: list[V2Result], output_path: Path):
    """Write V2 results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        'file_path',
        'current_domain',
        'layer',
        'header_quality',
        'role_text',
        'v1_inferred_domain',
        'v1_confidence',
        'v2_inferred_domain',
        'v2_confidence',
        'v2_override',
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
                'v1_inferred_domain': result.v1_inferred_domain,
                'v1_confidence': result.v1_confidence,
                'v2_inferred_domain': result.v2_inferred_domain,
                'v2_confidence': result.v2_confidence,
                'v2_override': 'YES' if result.v2_override else 'NO',
                'needs_split': 'YES' if result.needs_split else 'NO',
                'evidence': result.evidence,
                'notes': result.notes
            })

    print(f"\nWrote {len(results)} rows to: {output_path}")


def print_summary(results: list[V2Result]):
    """Print V2 classification summary."""
    print("\n" + "=" * 60)
    print("V2 CLASSIFICATION SUMMARY")
    print("=" * 60)

    # Count by V2 inferred domain
    domain_counts = {}
    for r in results:
        domain_counts[r.v2_inferred_domain] = domain_counts.get(r.v2_inferred_domain, 0) + 1

    print("\nBy V2 Inferred Domain:")
    for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
        print(f"  {domain:20} {count:4}")

    # Count by V2 confidence
    conf_counts = {}
    for r in results:
        conf_counts[r.v2_confidence] = conf_counts.get(r.v2_confidence, 0) + 1

    print("\nBy V2 Confidence:")
    for conf, count in sorted(conf_counts.items()):
        print(f"  {conf:20} {count:4}")

    # Count overrides
    overrides = [r for r in results if r.v2_override]
    print(f"\nV2 Overrides: {len(overrides)}")

    # Count still ambiguous
    ambiguous = [r for r in results if r.v2_inferred_domain == "AMBIGUOUS"]
    print(f"Still Ambiguous: {len(ambiguous)}")

    # Count needs_split
    needs_split = [r for r in results if r.needs_split]
    print(f"Needs Split: {len(needs_split)}")

    # Confidence improvement
    v1_high = sum(1 for r in results if r.v1_confidence == 'HIGH')
    v2_high = sum(1 for r in results if r.v2_confidence == 'HIGH')
    print(f"\nConfidence Improvement:")
    print(f"  V1 HIGH: {v1_high}")
    print(f"  V2 HIGH: {v2_high}")
    print(f"  Gain: +{v2_high - v1_high}")

    # Misplacements
    misplaced = [r for r in results
                 if r.current_domain != r.v2_inferred_domain
                 and r.v2_inferred_domain not in ('AMBIGUOUS', 'UNKNOWN')]
    print(f"\nMisplaced Files: {len(misplaced)}")

    print("=" * 60)

    # Show sample overrides
    if overrides:
        print("\nSample V2 Overrides (first 10):")
        for r in overrides[:10]:
            print(f"  {r.file_path}")
            print(f"    V1: {r.v1_inferred_domain} ({r.v1_confidence})")
            print(f"    V2: {r.v2_inferred_domain} ({r.v2_confidence})")


def main():
    parser = argparse.ArgumentParser(
        description="Domain Classifier V2 - Code Block Analysis"
    )
    parser.add_argument(
        '--input', '-i',
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input V1 CSV path (default: {DEFAULT_INPUT})"
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output V2 CSV path (default: {DEFAULT_OUTPUT})"
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
    if not args.input.exists():
        print(f"ERROR: Input file does not exist: {args.input}")
        sys.exit(1)

    if not args.criteria.exists():
        print(f"ERROR: Criteria file does not exist: {args.criteria}")
        sys.exit(1)

    # Load data
    print(f"Loading V1 results from: {args.input}")
    v1_results = load_v1_results(args.input)

    print(f"Loading criteria from: {args.criteria}")
    criteria = load_criteria(args.criteria)

    # Process V2
    print("\nRunning V2 code analysis...")
    results = process_v2(
        v1_results=v1_results,
        hoc_cus_path=HOC_CUS_PATH,
        criteria=criteria,
        verbose=args.verbose
    )

    # Write output
    write_csv(results, args.output)

    # Print summary
    print_summary(results)

    print(f"\nDone. Review output at: {args.output}")


if __name__ == "__main__":
    main()
