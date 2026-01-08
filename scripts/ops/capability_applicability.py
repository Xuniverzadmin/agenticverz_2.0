#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Type: Governance Script
# Reference: PIN-361 (STEP 1 Domain Applicability Matrix)
#
# STEP 1 – Domain Applicability Matrix
#
# Purpose: Determine which domains are allowed to attempt a capability,
#          based on questions, not UI, not architecture.
#
# Inputs:
# - capability_directional_metadata.xlsx (from STEP 0B)
# - domain_intent_spec.yaml (domain questions)
#
# Outputs:
# - capability_applicability_matrix.xlsx (authoritative)
# - capability_applicability_matrix.csv (derived)
# - capability_applicability_matrix.yaml (derived)
#
# Core Rule: A capability is applicable to a domain only if it
#            unambiguously answers at least one domain question.

from pathlib import Path
import yaml
import re
import sys
from typing import Dict, List, Any, Tuple

# ----------------------------
# CONFIG
# ----------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
DIR_META_XLSX = (
    REPO_ROOT / "docs/capabilities/directional/capability_directional_metadata.xlsx"
)
DIR_META_CSV = (
    REPO_ROOT / "docs/capabilities/directional/capability_directional_metadata.csv"
)
DOMAIN_SPEC = REPO_ROOT / "docs/domains/domain_intent_spec.yaml"
REGISTRY_PATH = REPO_ROOT / "docs/capabilities/CAPABILITY_REGISTRY_UNIFIED.yaml"

OUTPUT_DIR = REPO_ROOT / "docs/capabilities/applicability"
OUTPUT_XLSX = OUTPUT_DIR / "capability_applicability_matrix.xlsx"
OUTPUT_CSV = OUTPUT_DIR / "capability_applicability_matrix.csv"
OUTPUT_YAML = OUTPUT_DIR / "capability_applicability_matrix.yaml"

# ----------------------------
# KEYWORD MAPS (Domain → Capability matching)
# ----------------------------

# Keywords that indicate a capability answers a domain question
DOMAIN_KEYWORDS = {
    "ACTIVITY": {
        "primary": [
            "run",
            "execution",
            "running",
            "execute",
            "workflow",
            "job",
            "trace",
            "activity",
        ],
        "secondary": ["status", "poll", "dispatch", "worker", "skill", "runtime"],
        "exclude": ["incident", "policy", "recovery"],
    },
    "INCIDENTS": {
        "primary": ["incident", "failure", "error", "exception", "violation", "alert"],
        "secondary": ["recovery", "resolve", "acknowledge", "impact", "severity"],
        "exclude": [],
    },
    "POLICIES": {
        "primary": [
            "policy",
            "rule",
            "constraint",
            "limit",
            "enforcement",
            "governance",
        ],
        "secondary": [
            "evaluation",
            "conflict",
            "version",
            "proposal",
            "constitutional",
        ],
        "exclude": [],
    },
    "LOGS": {
        "primary": [
            "log",
            "trace",
            "audit",
            "replay",
            "evidence",
            "record",
            "deterministic",
        ],
        "secondary": ["export", "hash", "immutable", "proof", "timeline"],
        "exclude": [],
    },
}

# Question type → capability role affinity
ROLE_AFFINITY = {
    "state": ["control", "engine", "advisory"],
    "performance": ["advisory", "control"],
    "explanation": ["advisory", "engine"],
    "action": ["control", "engine"],
}

# Domain → expected console scopes
DOMAIN_SCOPE_AFFINITY = {
    "ACTIVITY": ["CUSTOMER", "SDK", "FOUNDER"],
    "INCIDENTS": ["CUSTOMER", "FOUNDER"],
    "POLICIES": ["CUSTOMER", "FOUNDER"],
    "LOGS": ["CUSTOMER", "FOUNDER"],
}


# ----------------------------
# LOADERS
# ----------------------------


def load_directional_metadata() -> List[Dict[str, Any]]:
    """Load capability directional metadata from STEP 0B."""
    try:
        import pandas as pd

        if DIR_META_XLSX.exists():
            df = pd.read_excel(DIR_META_XLSX)
        else:
            df = pd.read_csv(DIR_META_CSV)
        return df.to_dict(orient="records")
    except ImportError:
        # Fallback: read CSV manually
        import csv

        with open(DIR_META_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)


def load_domain_spec() -> Dict[str, Any]:
    """Load domain intent specification."""
    with open(DOMAIN_SPEC, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_registry() -> Dict[str, Any]:
    """Load capability registry for additional context."""
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


# ----------------------------
# MATCHING LOGIC
# ----------------------------


def get_capability_text(cap: Dict[str, Any], registry: Dict[str, Any]) -> str:
    """Get searchable text for a capability."""
    parts = [
        cap.get("canonical_name", ""),
        cap.get("capability_id", ""),
        cap.get("claimed_role", ""),
        cap.get("normalization_notes", ""),
        cap.get("governance_notes", ""),
    ]

    # Try to get description from registry
    cap_id = cap.get("capability_id", "")
    first_class = registry.get("first_class_capabilities", {})
    substrate = registry.get("substrate_capabilities", {})

    if cap_id in first_class:
        parts.append(first_class[cap_id].get("description", ""))
        routes = first_class[cap_id].get("routes", [])
        parts.extend(routes[:10])  # First 10 routes
    elif cap_id in substrate:
        parts.append(substrate[cap_id].get("description", ""))

    return " ".join(str(p).lower() for p in parts if p)


def match_keywords(text: str, keywords: Dict[str, List[str]]) -> Tuple[int, int, bool]:
    """
    Match keywords against text.
    Returns: (primary_matches, secondary_matches, has_exclusion)
    """
    primary = sum(1 for kw in keywords.get("primary", []) if kw in text)
    secondary = sum(1 for kw in keywords.get("secondary", []) if kw in text)
    excluded = any(kw in text for kw in keywords.get("exclude", []))
    return primary, secondary, excluded


def match_questions(cap_text: str, questions: List[Dict[str, Any]]) -> List[str]:
    """
    Match capability text against domain questions.
    Returns list of question IDs that the capability may answer.
    """
    matched = []

    for q in questions:
        q_text = q.get("text", "").lower()
        q_id = q.get("id", "")
        q_type = q.get("type", "")

        # Extract keywords from question
        q_words = set(re.findall(r"\b\w+\b", q_text))
        q_words -= {
            "what",
            "which",
            "how",
            "can",
            "did",
            "are",
            "is",
            "the",
            "a",
            "an",
            "i",
            "to",
            "on",
        }

        # Check for keyword overlap
        matches = sum(1 for word in q_words if word in cap_text and len(word) > 3)

        if matches >= 2:
            matched.append(q_id)
        elif matches >= 1 and q_type in ["state", "action"]:
            # More lenient for state/action questions
            matched.append(q_id)

    return matched


def compute_confidence(
    cap: Dict[str, Any],
    domain: str,
    questions_answered: List[str],
    domain_spec: Dict[str, Any],
) -> float:
    """
    Compute confidence score per PIN-361 rules.

    base = 0.4
    +0.3 if >=2 questions answered
    +0.2 if claimed_role matches domain intent
    +0.1 if trust_weight == HIGH
    -0.2 if exposure is advisory-only
    -0.2 if console scope mismatched
    """
    confidence = 0.4

    # Question coverage bonus
    if len(questions_answered) >= 2:
        confidence += 0.3
    elif len(questions_answered) == 1:
        confidence += 0.15

    # Role fit bonus
    domain_questions = domain_spec.get(domain, {}).get("questions", [])
    domain_types = set(q.get("type") for q in domain_questions)
    cap_role = cap.get("claimed_role", "unknown")

    role_match = False
    for qtype in domain_types:
        if cap_role in ROLE_AFFINITY.get(qtype, []):
            role_match = True
            break

    if role_match:
        confidence += 0.2

    # Trust weight bonus
    if cap.get("trust_weight") == "HIGH":
        confidence += 0.1

    # Advisory-only penalty
    if cap.get("claimed_role") == "advisory" and cap.get("mutability_claim") == "read":
        confidence -= 0.1

    # Console scope mismatch penalty
    cap_scope = cap.get("claimed_console_scope", "NONE")
    expected_scopes = DOMAIN_SCOPE_AFFINITY.get(domain, [])
    if cap_scope not in expected_scopes and cap_scope != "NONE":
        confidence -= 0.2

    # Substrate penalty (internal-only)
    if cap.get("status") == "SUBSTRATE":
        confidence -= 0.3

    return max(0.0, min(1.0, confidence))


def evaluate_capability_for_domain(
    cap: Dict[str, Any],
    domain: str,
    domain_spec: Dict[str, Any],
    registry: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Evaluate a single capability against a domain.
    Returns applicability result.
    """
    cap_text = get_capability_text(cap, registry)
    keywords = DOMAIN_KEYWORDS.get(domain, {})
    questions = domain_spec.get(domain, {}).get("questions", [])

    # Keyword matching
    primary, secondary, excluded = match_keywords(cap_text, keywords)

    # Question matching
    questions_answered = match_questions(cap_text, questions)

    # Early rejection: no keywords and no questions
    if primary == 0 and secondary == 0 and not questions_answered:
        return {
            "applicable": False,
            "questions_answered": [],
            "decision": "REJECT",
            "confidence": 0.0,
            "notes": "No keyword or question match",
        }

    # Early rejection: exclusion keywords
    if excluded and primary == 0:
        return {
            "applicable": False,
            "questions_answered": [],
            "decision": "REJECT",
            "confidence": 0.0,
            "notes": "Excluded by domain keywords",
        }

    # Compute confidence
    confidence = compute_confidence(cap, domain, questions_answered, domain_spec)

    # Boost confidence for strong keyword matches
    if primary >= 2:
        confidence = min(1.0, confidence + 0.1)

    # Decision logic
    if not questions_answered and primary == 0:
        decision = "REJECT"
        applicable = False
        notes = "Secondary keywords only, no questions answered"
    elif confidence >= 0.6:
        decision = "CONSUME"
        applicable = True
        notes = f"Primary:{primary} Secondary:{secondary} Questions:{len(questions_answered)}"
    elif confidence >= 0.4:
        decision = "DEFER"
        applicable = True
        notes = f"Low confidence. Primary:{primary} Secondary:{secondary}"
    else:
        decision = "REJECT"
        applicable = False
        notes = f"Below threshold. Confidence:{confidence:.2f}"

    # Check for multi-domain overlap (would be REVIEW)
    # This is detected later when aggregating results

    return {
        "applicable": applicable,
        "questions_answered": questions_answered,
        "decision": decision,
        "confidence": round(confidence, 2),
        "notes": notes,
    }


# ----------------------------
# MATRIX BUILDING
# ----------------------------


def build_applicability_matrix(
    capabilities: List[Dict[str, Any]],
    domain_spec: Dict[str, Any],
    registry: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Build the full applicability matrix."""
    rows = []
    domains = [d for d in domain_spec.keys() if d in DOMAIN_KEYWORDS]

    for cap in capabilities:
        cap_id = cap.get("capability_id", "UNKNOWN")

        for domain in domains:
            result = evaluate_capability_for_domain(cap, domain, domain_spec, registry)

            rows.append(
                {
                    "domain": domain,
                    "capability_id": cap_id,
                    "capability_name": cap.get("canonical_name", ""),
                    "applicable": result["applicable"],
                    "questions_answered": ", ".join(result["questions_answered"]),
                    "question_count": len(result["questions_answered"]),
                    "decision": result["decision"],
                    "confidence": result["confidence"],
                    "trust_weight": cap.get("trust_weight", "LOW"),
                    "console_scope": cap.get("claimed_console_scope", "NONE"),
                    "status": cap.get("status", "UNKNOWN"),
                    "notes": result["notes"],
                }
            )

    # Sort by domain, then by decision priority, then by confidence
    decision_order = {"CONSUME": 0, "DEFER": 1, "REVIEW": 2, "REJECT": 3}
    rows.sort(
        key=lambda x: (
            x["domain"],
            decision_order.get(x["decision"], 4),
            -x["confidence"],
        )
    )

    return rows


# ----------------------------
# OUTPUT
# ----------------------------


def write_outputs(rows: List[Dict[str, Any]]) -> None:
    """Write outputs in xlsx, csv, and yaml formats."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import pandas as pd

        df = pd.DataFrame(rows)

        # Column order
        column_order = [
            "domain",
            "capability_id",
            "capability_name",
            "applicable",
            "decision",
            "confidence",
            "questions_answered",
            "question_count",
            "trust_weight",
            "console_scope",
            "status",
            "notes",
        ]
        df = df[[c for c in column_order if c in df.columns]]

        # Write xlsx
        try:
            df.to_excel(OUTPUT_XLSX, index=False, engine="openpyxl")
            print(f"  [xlsx] {OUTPUT_XLSX}")
        except ImportError:
            print("  [xlsx] SKIPPED - openpyxl not installed")

        # Write csv
        df.to_csv(OUTPUT_CSV, index=False)
        print(f"  [csv]  {OUTPUT_CSV}")

    except ImportError:
        import csv

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        print(f"  [csv]  {OUTPUT_CSV}")

    # Write yaml
    with open(OUTPUT_YAML, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            rows, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
    print(f"  [yaml] {OUTPUT_YAML}")


def print_summary(rows: List[Dict[str, Any]], domain_spec: Dict[str, Any]) -> None:
    """Print detailed summary statistics."""
    print("\n" + "=" * 70)
    print("STEP 1 DOMAIN APPLICABILITY MATRIX SUMMARY")
    print("=" * 70)

    domains = list(domain_spec.keys())
    total = len(rows)

    # Overall decision distribution
    decisions = {}
    for r in rows:
        d = r["decision"]
        decisions[d] = decisions.get(d, 0) + 1

    print(
        f"\nTotal Evaluations: {total} ({len(rows) // len(domains)} capabilities x {len(domains)} domains)"
    )
    print("\nDecision Distribution (all domains):")
    for decision in ["CONSUME", "DEFER", "REVIEW", "REJECT"]:
        count = decisions.get(decision, 0)
        pct = 100 * count / total if total > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"  {decision:8} {count:3} ({pct:5.1f}%) {bar}")

    # Per-domain breakdown
    print("\n" + "-" * 70)
    print("PER-DOMAIN BREAKDOWN")
    print("-" * 70)

    for domain in domains:
        domain_rows = [r for r in rows if r["domain"] == domain]
        consume = sum(1 for r in domain_rows if r["decision"] == "CONSUME")
        defer = sum(1 for r in domain_rows if r["decision"] == "DEFER")
        reject = sum(1 for r in domain_rows if r["decision"] == "REJECT")

        print(f"\n{domain}:")
        print(f"  CONSUME: {consume:2}  DEFER: {defer:2}  REJECT: {reject:2}")

        # Show CONSUME capabilities
        if consume > 0:
            print("  --- CONSUME ---")
            for r in domain_rows:
                if r["decision"] == "CONSUME":
                    print(
                        f"    {r['capability_id']:8} ({r['confidence']:.2f}) {r['capability_name'][:40]}"
                    )

        # Show DEFER capabilities
        if defer > 0:
            print("  --- DEFER ---")
            for r in domain_rows:
                if r["decision"] == "DEFER":
                    print(
                        f"    {r['capability_id']:8} ({r['confidence']:.2f}) {r['capability_name'][:40]}"
                    )

    # High-confidence capabilities
    print("\n" + "-" * 70)
    print("HIGH CONFIDENCE CAPABILITIES (>=0.7)")
    print("-" * 70)

    high_conf = [r for r in rows if r["confidence"] >= 0.7]
    if high_conf:
        for r in sorted(high_conf, key=lambda x: -x["confidence"]):
            print(
                f"  {r['domain']:10} {r['capability_id']:8} ({r['confidence']:.2f}) {r['questions_answered'][:30]}"
            )
    else:
        print("  None")

    # Cross-domain capabilities (applicable to multiple domains)
    print("\n" + "-" * 70)
    print("CROSS-DOMAIN CAPABILITIES (applicable to 2+ domains)")
    print("-" * 70)

    cap_domains = {}
    for r in rows:
        if r["applicable"]:
            cap_id = r["capability_id"]
            if cap_id not in cap_domains:
                cap_domains[cap_id] = []
            cap_domains[cap_id].append(r["domain"])

    cross_domain = {k: v for k, v in cap_domains.items() if len(v) >= 2}
    if cross_domain:
        for cap_id, doms in sorted(cross_domain.items(), key=lambda x: -len(x[1])):
            print(f"  {cap_id:8} -> {', '.join(doms)}")
    else:
        print("  None")

    print("\n" + "=" * 70)


# ----------------------------
# ENTRYPOINT
# ----------------------------


def main():
    print("=" * 70)
    print("STEP 1: Domain Applicability Matrix")
    print("Reference: PIN-361")
    print("=" * 70)

    print("\n[1/4] Loading inputs...")

    if not DIR_META_XLSX.exists() and not DIR_META_CSV.exists():
        print("ERROR: Directional metadata not found")
        print(f"  Expected: {DIR_META_XLSX}")
        print(f"  Or: {DIR_META_CSV}")
        print("  Run STEP 0B first.")
        sys.exit(1)

    if not DOMAIN_SPEC.exists():
        print(f"ERROR: Domain spec not found at {DOMAIN_SPEC}")
        sys.exit(1)

    capabilities = load_directional_metadata()
    domain_spec = load_domain_spec()
    registry = load_registry()

    print(f"  Capabilities: {len(capabilities)}")
    print(f"  Domains: {len([d for d in domain_spec.keys() if d in DOMAIN_KEYWORDS])}")
    print(f"  Registry loaded: {bool(registry)}")

    print("\n[2/4] Evaluating applicability...")
    rows = build_applicability_matrix(capabilities, domain_spec, registry)
    print(f"  Generated {len(rows)} evaluations")

    print("\n[3/4] Writing outputs...")
    write_outputs(rows)

    print("\n[4/4] Summary...")
    print_summary(rows, domain_spec)

    print("\nSTEP 1 COMPLETE")
    print(f"Authoritative output: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
