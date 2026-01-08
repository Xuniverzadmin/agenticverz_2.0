#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Type: Governance Script
# Reference: PIN-364 (STEP X — Capability Opportunity Mapping)
#
# STEP X – Capability Opportunity Mapping (Read-Only)
#
# Purpose: Identify latent product surfaces and customer questions implied
#          by existing capabilities WITHOUT affecting STEP 1 / 1B / STEP 3.
#
# This is roadmap intelligence, not architecture.
#
# Inputs (frozen, read-only):
# - capability_directional_metadata.xlsx (from STEP 0B)
# - capability_applicability_matrix.xlsx (from STEP 1)
# - l2_supertable_v3_rebased_surfaces.xlsx (from STEP 1B-R)
# - domain_intent_spec.yaml (from STEP 1)
#
# Outputs (new only):
# - capability_opportunity_map.xlsx (surface gaps per capability)
# - unasked_questions.xlsx (candidate customer questions)
#
# Hard Stop Rules:
# - No writes to STEP 1-3 artifacts
# - No L2.1 mutation
# - No UI logic
# - Deterministic
# - Record-only outputs

from pathlib import Path
import sys
from typing import Dict, List, Any, Set, Optional
import yaml

# ----------------------------
# CONFIG
# ----------------------------

REPO_ROOT = Path(__file__).parent.parent.parent

# FROZEN INPUTS
CAP_META_XLSX = (
    REPO_ROOT / "docs/capabilities/directional/capability_directional_metadata.xlsx"
)
CAP_META_CSV = (
    REPO_ROOT / "docs/capabilities/directional/capability_directional_metadata.csv"
)
APPLICABILITY_XLSX = (
    REPO_ROOT / "docs/capabilities/applicability/capability_applicability_matrix.xlsx"
)
APPLICABILITY_CSV = (
    REPO_ROOT / "docs/capabilities/applicability/capability_applicability_matrix.csv"
)
REBASED_SURFACES = (
    REPO_ROOT / "docs/capabilities/l21_bounded/l2_supertable_v3_rebased_surfaces.xlsx"
)
RERUN_RESULTS = REPO_ROOT / "docs/capabilities/l21_bounded/l21_rerun_results.xlsx"
DOMAIN_INTENT = REPO_ROOT / "docs/domains/domain_intent_spec.yaml"

# OUTPUT (NEW ONLY)
OUTPUT_DIR = REPO_ROOT / "docs/capabilities/step_x"
OUT_OPPORTUNITY_MAP = OUTPUT_DIR / "capability_opportunity_map.xlsx"
OUT_UNASKED_QUESTIONS = OUTPUT_DIR / "unasked_questions.xlsx"

# ----------------------------
# ENUM DEFINITIONS (LOCKED)
# ----------------------------

AUTHORITY_LEVELS = {"OBSERVE": 0, "EXPLAIN": 1, "ACT": 2, "CONTROL": 3, "ADMIN": 4}
DETERMINISM_LEVELS = {"ADVISORY": 0, "BOUNDED": 1, "STRICT": 2}
MUTABILITY_LEVELS = {"READ": 0, "WRITE": 1, "EXECUTE": 2, "GOVERN": 3}

# Gap types (per PIN-364)
GAP_TYPES = {
    "Product": "New customer-facing surface",
    "UX": "Better visibility of existing value",
    "Productization": "Platform feature → product",
    "Ignore": "Internal-only, no surface value",
}

# Customer value classification
CUSTOMER_VALUES = ["HIGH", "MEDIUM", "LOW"]
AUDIENCES = ["DEV", "OPS", "FOUNDER", "ENTERPRISE"]
TIME_HORIZONS = ["NOW", "NEXT", "LATER"]


# ----------------------------
# LOADERS
# ----------------------------


def load_inputs():
    """Load all FROZEN input files."""
    try:
        import pandas as pd

        # Load capability metadata
        if CAP_META_XLSX.exists():
            caps = pd.read_excel(CAP_META_XLSX)
        elif CAP_META_CSV.exists():
            caps = pd.read_csv(CAP_META_CSV)
        else:
            print("ERROR: Capability metadata not found")
            sys.exit(1)

        # Load applicability matrix
        if APPLICABILITY_XLSX.exists():
            appl = pd.read_excel(APPLICABILITY_XLSX)
        elif APPLICABILITY_CSV.exists():
            appl = pd.read_csv(APPLICABILITY_CSV)
        else:
            print("ERROR: Applicability matrix not found")
            sys.exit(1)

        # Load rebased surfaces
        if not REBASED_SURFACES.exists():
            print(f"ERROR: Rebased surfaces not found at {REBASED_SURFACES}")
            sys.exit(1)
        surfaces = pd.read_excel(REBASED_SURFACES)

        # Load re-run results (current bindings)
        if not RERUN_RESULTS.exists():
            print(f"ERROR: Re-run results not found at {RERUN_RESULTS}")
            sys.exit(1)
        bindings = pd.read_excel(RERUN_RESULTS)

        # Load domain intent spec
        if not DOMAIN_INTENT.exists():
            print(f"ERROR: Domain intent spec not found at {DOMAIN_INTENT}")
            sys.exit(1)
        with open(DOMAIN_INTENT) as f:
            intent = yaml.safe_load(f)

        return (
            caps.to_dict(orient="records"),
            appl.to_dict(orient="records"),
            surfaces.to_dict(orient="records"),
            bindings.to_dict(orient="records"),
            intent,
        )

    except ImportError:
        print("ERROR: pandas and pyyaml required")
        sys.exit(1)


# ----------------------------
# STEP X.A — Surface Opportunity Scan
# ----------------------------


def get_surface_compatibility(
    cap_authority: int,
    cap_determinism: int,
    cap_mutability: int,
    surface: Dict[str, Any],
) -> bool:
    """Check if a capability can bind to a surface based on dimensions."""
    surf_authority = AUTHORITY_LEVELS.get(
        str(surface.get("authority_required", "OBSERVE")).upper(), 0
    )
    surf_determinism = DETERMINISM_LEVELS.get(
        str(surface.get("determinism_required", "BOUNDED")).upper(), 1
    )
    surf_mutability = MUTABILITY_LEVELS.get(
        str(surface.get("mutability_required", "READ")).upper(), 0
    )

    # Capability must meet or exceed surface requirements
    return (
        cap_authority >= surf_authority
        and cap_determinism >= surf_determinism
        and cap_mutability >= surf_mutability
    )


def classify_gap_type(
    cap: Dict[str, Any], surface: Dict[str, Any], current_surfaces: Set[str]
) -> str:
    """Classify the gap type for a potential surface binding."""
    cap_status = str(cap.get("status", "")).upper()
    cap_scope = str(cap.get("claimed_console_scope", "")).upper()
    # surface_type available via surface.get("surface_type") if needed

    # SUBSTRATE capabilities don't create user value
    if cap_status == "SUBSTRATE":
        return "Ignore"

    # Internal-only capabilities
    if cap_scope in ["NONE", "INTERNAL"]:
        return "Ignore"

    # If capability has routes/UI but surface is new
    has_routes = cap.get("has_routes", False)
    if has_routes and len(current_surfaces) > 0:
        return "UX"  # Better visibility of existing value

    # Founder-only capabilities could be productized
    if cap_scope == "FOUNDER":
        return "Productization"

    # Customer-facing new surface
    if cap_scope == "CUSTOMER":
        return "Product"

    # SDK/API capabilities could become products
    if cap_scope == "SDK":
        return "Productization"

    return "UX"


def run_surface_opportunity_scan(
    caps: List[Dict[str, Any]],
    appl: List[Dict[str, Any]],
    surfaces: List[Dict[str, Any]],
    bindings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    STEP X.A: For each capability, identify surface gaps.

    Compare allowed surfaces (by authority, determinism, mutability)
    vs currently bound surfaces.
    """
    print("\n[2/4] Running STEP X.A — Surface Opportunity Scan...")

    opportunity_map = []

    # Build capability lookup
    cap_lookup = {c.get("capability_id"): c for c in caps}

    # Build current bindings lookup: capability_id -> set of bound surfaces
    current_bindings: Dict[str, Set[str]] = {}
    for b in bindings:
        cap_id = b.get("capability_id")
        surface_id = b.get("bound_surface")
        if cap_id not in current_bindings:
            current_bindings[cap_id] = set()
        current_bindings[cap_id].add(surface_id)

    # Get applicable capabilities (CONSUME or DEFER)
    applicable_caps = set()
    for a in appl:
        if a.get("decision") in ("CONSUME", "DEFER"):
            applicable_caps.add(a.get("capability_id"))

    print(f"  Processing {len(applicable_caps)} applicable capabilities...")
    print(f"  Against {len(surfaces)} rebased surfaces...")

    for cap_id in sorted(applicable_caps):
        if cap_id not in cap_lookup:
            continue

        cap = cap_lookup[cap_id]

        # Get capability dimensions
        cap_authority = AUTHORITY_LEVELS.get(
            str(cap.get("claimed_role", "observe")).upper()
            if str(cap.get("claimed_role", "")).upper()
            in ["OBSERVE", "EXPLAIN", "ACT", "CONTROL", "ADMIN"]
            else map_role_to_authority(cap),
            0,
        )
        cap_determinism = DETERMINISM_LEVELS.get(
            str(cap.get("determinism_claim", "bounded")).upper()
            if str(cap.get("determinism_claim", "")).upper()
            in ["ADVISORY", "BOUNDED", "STRICT"]
            else map_determinism(cap),
            1,
        )
        cap_mutability = MUTABILITY_LEVELS.get(
            str(cap.get("mutability_claim", "read")).upper()
            if str(cap.get("mutability_claim", "")).upper()
            in ["READ", "WRITE", "EXECUTE", "GOVERN"]
            else map_mutability(cap),
            0,
        )

        # Get currently bound surfaces
        current_surfaces = current_bindings.get(cap_id, set())

        # Find all compatible surfaces
        potential_surfaces = []
        for surface in surfaces:
            if get_surface_compatibility(
                cap_authority, cap_determinism, cap_mutability, surface
            ):
                potential_surfaces.append(surface.get("surface_id"))

        # Compute gaps
        gap_surfaces = set(potential_surfaces) - current_surfaces

        # Classify each gap
        for surface in surfaces:
            surf_id = surface.get("surface_id")
            if surf_id in gap_surfaces:
                gap_type = classify_gap_type(cap, surface, current_surfaces)
                customer_value = classify_customer_value(cap, surface)

                opportunity_map.append(
                    {
                        "capability_id": cap_id,
                        "capability_name": cap.get("canonical_name", ""),
                        "status": cap.get("status", ""),
                        "authority": list(AUTHORITY_LEVELS.keys())[cap_authority],
                        "determinism": list(DETERMINISM_LEVELS.keys())[cap_determinism],
                        "mutability": list(MUTABILITY_LEVELS.keys())[cap_mutability],
                        "current_surfaces": ", ".join(sorted(current_surfaces)),
                        "potential_surface": surf_id,
                        "surface_type": surface.get("surface_type", ""),
                        "gap_type": gap_type,
                        "customer_value": customer_value["value"],
                        "audience": customer_value["audience"],
                        "time_horizon": customer_value["horizon"],
                    }
                )

    print(f"  Found {len(opportunity_map)} surface gap opportunities")
    return opportunity_map


def map_role_to_authority(cap: Dict[str, Any]) -> str:
    """Map claimed_role to authority level name."""
    role = str(cap.get("claimed_role", "unknown")).lower()
    mutability = str(cap.get("mutability_claim", "read")).lower()

    if role in ["engine", "control"]:
        if mutability == "control":
            return "CONTROL"
        return "ACT"
    if role == "advisory":
        return "EXPLAIN"
    if role == "substrate":
        return "OBSERVE"
    if mutability == "write":
        return "ACT"
    return "OBSERVE"


def map_determinism(cap: Dict[str, Any]) -> str:
    """Map determinism_claim to level name."""
    det = str(cap.get("determinism_claim", "mixed")).lower()
    if det == "deterministic":
        return "STRICT"
    if det == "probabilistic":
        return "ADVISORY"
    return "BOUNDED"


def map_mutability(cap: Dict[str, Any]) -> str:
    """Map mutability_claim to level name."""
    mut = str(cap.get("mutability_claim", "read")).lower()
    if mut == "control":
        return "GOVERN"
    if mut == "write":
        return "WRITE"
    return "READ"


def classify_customer_value(
    cap: Dict[str, Any], surface: Dict[str, Any]
) -> Dict[str, str]:
    """Classify customer value, audience, and time horizon."""
    cap_scope = str(cap.get("claimed_console_scope", "")).upper()
    cap_status = str(cap.get("status", "")).upper()
    trust_weight = str(cap.get("trust_weight", "")).upper()
    has_routes = cap.get("has_routes", False)

    # Determine value
    value = "LOW"
    if trust_weight == "HIGH" and has_routes:
        value = "HIGH"
    elif trust_weight in ["HIGH", "MEDIUM"] or has_routes:
        value = "MEDIUM"

    # Determine audience
    audience = "DEV"
    if cap_scope == "FOUNDER":
        audience = "FOUNDER"
    elif cap_scope == "CUSTOMER":
        audience = "OPS"
    elif cap_scope == "SDK":
        audience = "DEV"

    # Determine time horizon
    horizon = "LATER"
    if cap_status == "FIRST_CLASS" and has_routes:
        horizon = "NOW"
    elif cap_status == "FIRST_CLASS":
        horizon = "NEXT"

    return {"value": value, "audience": audience, "horizon": horizon}


# ----------------------------
# STEP X.B — Unasked Question Derivation
# ----------------------------


def extract_existing_questions(intent: Dict[str, Any]) -> Set[str]:
    """Extract all existing question texts from domain_intent_spec."""
    existing = set()
    for domain_data in intent.values():
        if isinstance(domain_data, dict) and "questions" in domain_data:
            for q in domain_data["questions"]:
                text = str(q.get("text", "")).lower().strip()
                if text:
                    existing.add(text)
    return existing


def generate_candidate_question(
    cap: Dict[str, Any], gap_type: str, surface_type: str
) -> Optional[Dict[str, str]]:
    """Generate a candidate question based on capability and gap."""
    cap_name = cap.get("canonical_name", "")
    cap_role = str(cap.get("claimed_role", "")).lower()

    # Question templates based on role and gap type
    templates = {
        ("observe", "Product"): f"What is the current state of {cap_name}?",
        ("observe", "UX"): f"How can I see {cap_name} data more clearly?",
        ("advisory", "Product"): f"What does {cap_name} recommend?",
        ("advisory", "UX"): f"What predictions are available from {cap_name}?",
        ("control", "Product"): f"How can I configure {cap_name}?",
        ("control", "Productization"): f"Can {cap_name} be exposed to customers?",
        ("engine", "Product"): f"What actions can I take with {cap_name}?",
        ("engine", "Productization"): f"Can I trigger {cap_name} from the UI?",
    }

    key = (cap_role, gap_type)
    if key in templates:
        return {
            "question": templates[key],
            "type": "state" if cap_role == "observe" else "action",
        }

    # Generic fallback
    if gap_type == "Product":
        return {
            "question": f"What can I learn from {cap_name}?",
            "type": "explanation",
        }
    if gap_type == "UX":
        return {
            "question": f"How do I access {cap_name} features?",
            "type": "action",
        }

    return None


def run_unasked_question_derivation(
    caps: List[Dict[str, Any]],
    opportunity_map: List[Dict[str, Any]],
    intent: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    STEP X.B: Generate candidate customer questions for capabilities with gaps.

    Verify question does not exist in domain_intent_spec.yaml.
    """
    print("\n[3/4] Running STEP X.B — Unasked Question Derivation...")

    # Extract existing questions
    existing_questions = extract_existing_questions(intent)
    print(f"  Found {len(existing_questions)} existing questions")

    # Build capability lookup
    cap_lookup = {c.get("capability_id"): c for c in caps}

    # Group opportunities by capability
    caps_with_gaps: Dict[str, List[Dict[str, Any]]] = {}
    for opp in opportunity_map:
        cap_id = opp.get("capability_id")
        if opp.get("gap_type") not in ["Ignore"]:  # Only non-ignored gaps
            if cap_id not in caps_with_gaps:
                caps_with_gaps[cap_id] = []
            caps_with_gaps[cap_id].append(opp)

    unasked = []
    for cap_id, gaps in caps_with_gaps.items():
        if cap_id not in cap_lookup:
            continue

        cap = cap_lookup[cap_id]

        # Generate one candidate question per unique gap type
        seen_gap_types = set()
        for gap in gaps:
            gap_type = gap.get("gap_type")
            surface_type = gap.get("surface_type")

            if gap_type in seen_gap_types:
                continue
            seen_gap_types.add(gap_type)

            candidate = generate_candidate_question(cap, gap_type, surface_type)
            if not candidate:
                continue

            # Check if question already exists
            question_text = candidate["question"].lower().strip()
            if question_text in existing_questions:
                continue

            # Find potential domain
            domain_candidate = infer_domain_for_capability(cap, intent)

            unasked.append(
                {
                    "capability_id": cap_id,
                    "capability_name": cap.get("canonical_name", ""),
                    "proposed_question": candidate["question"],
                    "question_type": candidate["type"],
                    "domain_candidate": domain_candidate,
                    "gap_type": gap_type,
                    "rationale": generate_rationale(cap, gap_type),
                }
            )

    print(f"  Generated {len(unasked)} candidate unasked questions")
    return unasked


def infer_domain_for_capability(cap: Dict[str, Any], intent: Dict[str, Any]) -> str:
    """Infer which domain a capability's question might belong to."""
    cap_name = str(cap.get("canonical_name", "")).lower()
    cap_role = str(cap.get("claimed_role", "")).lower()

    # Keyword matching
    if any(kw in cap_name for kw in ["replay", "activity", "execution", "run"]):
        return "ACTIVITY"
    if any(kw in cap_name for kw in ["incident", "failure", "error", "violation"]):
        return "INCIDENTS"
    if any(kw in cap_name for kw in ["policy", "rule", "constraint", "governance"]):
        return "POLICIES"
    if any(kw in cap_name for kw in ["log", "trace", "audit", "evidence"]):
        return "LOGS"

    # Role-based inference
    if cap_role == "observe":
        return "LOGS"
    if cap_role in ["control", "engine"]:
        return "POLICIES"

    return "ACTIVITY"  # Default


def generate_rationale(cap: Dict[str, Any], gap_type: str) -> str:
    """Generate a rationale for why this question might matter."""
    cap_scope = str(cap.get("claimed_console_scope", "")).upper()
    has_routes = cap.get("has_routes", False)
    trust_weight = str(cap.get("trust_weight", "")).upper()

    parts = []

    if gap_type == "Product":
        parts.append("New customer-facing value opportunity")
    elif gap_type == "UX":
        parts.append("Existing capability with hidden visibility")
    elif gap_type == "Productization":
        parts.append("Platform feature ready for product exposure")

    if has_routes:
        parts.append(f"Already has {cap.get('route_count', 0)} routes")
    if trust_weight == "HIGH":
        parts.append("High trust weight")

    if cap_scope == "FOUNDER":
        parts.append("Currently founder-only")
    elif cap_scope == "SDK":
        parts.append("Currently SDK-only")

    return "; ".join(parts) if parts else "Capability has surface potential"


# ----------------------------
# OUTPUT
# ----------------------------


def write_outputs(opportunity_map: List[Dict[str, Any]], unasked: List[Dict[str, Any]]):
    """Write all output files (NEW ONLY — no STEP 1-3 mutation)."""
    import pandas as pd

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write opportunity map
    df_opp = pd.DataFrame(opportunity_map)
    df_opp.to_excel(OUT_OPPORTUNITY_MAP, index=False)
    print(f"  [opportunity_map] {OUT_OPPORTUNITY_MAP}")

    # Write unasked questions
    df_unasked = pd.DataFrame(unasked)
    df_unasked.to_excel(OUT_UNASKED_QUESTIONS, index=False)
    print(f"  [unasked_questions] {OUT_UNASKED_QUESTIONS}")


def print_summary(opportunity_map: List[Dict[str, Any]], unasked: List[Dict[str, Any]]):
    """Print STEP X summary."""
    print("\n" + "=" * 70)
    print("STEP X CAPABILITY OPPORTUNITY MAPPING — SUMMARY")
    print("Reference: PIN-364")
    print("=" * 70)

    # Opportunity map summary
    print("\n--- STEP X.A: Surface Opportunity Scan ---")
    print(f"Total surface gaps identified: {len(opportunity_map)}")

    # Group by gap type
    gap_counts: Dict[str, int] = {}
    for opp in opportunity_map:
        gt = opp.get("gap_type", "Unknown")
        gap_counts[gt] = gap_counts.get(gt, 0) + 1

    print("\nBy Gap Type:")
    for gt, count in sorted(gap_counts.items()):
        print(f"  {gt}: {count}")

    # Group by customer value
    value_counts: Dict[str, int] = {}
    for opp in opportunity_map:
        if opp.get("gap_type") != "Ignore":
            val = opp.get("customer_value", "Unknown")
            value_counts[val] = value_counts.get(val, 0) + 1

    print("\nBy Customer Value (excluding Ignore):")
    for val, count in sorted(value_counts.items(), reverse=True):
        print(f"  {val}: {count}")

    # Top capabilities by gap count
    cap_gap_counts: Dict[str, int] = {}
    for opp in opportunity_map:
        if opp.get("gap_type") != "Ignore":
            cap_id = opp.get("capability_id")
            cap_gap_counts[cap_id] = cap_gap_counts.get(cap_id, 0) + 1

    print("\nTop 5 Capabilities by Gap Count:")
    for cap_id, count in sorted(
        cap_gap_counts.items(), key=lambda x: x[1], reverse=True
    )[:5]:
        cap_name = next(
            (
                o.get("capability_name")
                for o in opportunity_map
                if o.get("capability_id") == cap_id
            ),
            cap_id,
        )
        print(f"  {cap_id} ({cap_name}): {count} gaps")

    # Unasked questions summary
    print("\n--- STEP X.B: Unasked Question Derivation ---")
    print(f"Total candidate questions: {len(unasked)}")

    # Group by domain
    domain_counts: Dict[str, int] = {}
    for q in unasked:
        dom = q.get("domain_candidate", "Unknown")
        domain_counts[dom] = domain_counts.get(dom, 0) + 1

    print("\nBy Domain Candidate:")
    for dom, count in sorted(domain_counts.items()):
        print(f"  {dom}: {count}")

    # Sample questions
    if unasked:
        print("\nSample Unasked Questions:")
        for q in unasked[:5]:
            print(f"  - [{q.get('domain_candidate')}] {q.get('proposed_question')}")
            print(f"    Rationale: {q.get('rationale')}")

    print("\n" + "=" * 70)
    print("STEP X COMPLETE — READ-ONLY ANALYSIS")
    print("These outputs are for roadmap intelligence only.")
    print("They must NOT feed back into STEP 1-3 or L2.1.")
    print("=" * 70)


# ----------------------------
# ENTRYPOINT
# ----------------------------


def main():
    print("=" * 70)
    print("STEP X: Capability Opportunity Mapping (Read-Only)")
    print("Reference: PIN-364")
    print("=" * 70)

    print("\n[1/4] Loading frozen inputs...")
    caps, appl, surfaces, bindings, intent = load_inputs()

    print(f"  Capabilities: {len(caps)}")
    print(f"  Applicability: {len(appl)}")
    print(f"  Rebased surfaces: {len(surfaces)}")
    print(f"  Current bindings: {len(bindings)}")
    print(f"  Domains with intent: {len(intent)}")

    # STEP X.A
    opportunity_map = run_surface_opportunity_scan(caps, appl, surfaces, bindings)

    # STEP X.B
    unasked = run_unasked_question_derivation(caps, opportunity_map, intent)

    # Write outputs
    print("\n[4/4] Writing outputs (NEW ONLY)...")
    write_outputs(opportunity_map, unasked)

    # Summary
    print_summary(opportunity_map, unasked)


if __name__ == "__main__":
    main()
