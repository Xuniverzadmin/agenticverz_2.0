#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Type: Governance Script
# Reference: PIN-362 (STEP 1B L2.1 Compatibility Scan)
#
# STEP 1B – L2.1 Capability Compatibility Scan
#
# Purpose: Given capability truth + domain admissibility + L2.1 surfaces,
#          determine where a capability can mechanically live — and generate
#          new surfaces only when structurally required.
#
# Inputs:
# - capability_directional_metadata.xlsx (from STEP 0B)
# - capability_applicability_matrix.xlsx (from STEP 1)
# - l2_supertable_v3_cap_expanded.xlsx (L2.1 baseline)
#
# Outputs:
# - L21_supertable_v3_cap_bounded_v1.xlsx (extended + bounded)
# - l21_bind_failures.xlsx (why binding failed)
# - l21_generated_rows.xlsx (audit trail)

from pathlib import Path
import sys
from typing import Dict, List, Any, Tuple

# ----------------------------
# CONFIG
# ----------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
CAP_META = (
    REPO_ROOT / "docs/capabilities/directional/capability_directional_metadata.xlsx"
)
CAP_META_CSV = (
    REPO_ROOT / "docs/capabilities/directional/capability_directional_metadata.csv"
)
APPLICABILITY = (
    REPO_ROOT / "docs/capabilities/applicability/capability_applicability_matrix.xlsx"
)
APPLICABILITY_CSV = (
    REPO_ROOT / "docs/capabilities/applicability/capability_applicability_matrix.csv"
)
L21_BASE = REPO_ROOT / "design/l2_1/supertable/l2_supertable_v3_cap_expanded.xlsx"
ENUMS_PATH = REPO_ROOT / "docs/capabilities/l21_enums.yaml"

OUTPUT_DIR = REPO_ROOT / "docs/capabilities/l21_bounded"
OUT_BOUND = OUTPUT_DIR / "L21_supertable_v3_cap_bounded_v1.xlsx"
OUT_FAIL = OUTPUT_DIR / "l21_bind_failures.xlsx"
OUT_GEN = OUTPUT_DIR / "l21_generated_rows.xlsx"
OUT_BASELINE = OUTPUT_DIR / "l21_baseline_rows.xlsx"

# ----------------------------
# ENUM DEFINITIONS (LOCKED)
# ----------------------------

AUTHORITY_LEVELS = {"OBSERVE": 0, "EXPLAIN": 1, "ACT": 2, "CONTROL": 3, "ADMIN": 4}

DETERMINISM_LEVELS = {"ADVISORY": 0, "BOUNDED": 1, "STRICT": 2}

MUTABILITY_LEVELS = {"READ": 0, "WRITE": 1, "EXECUTE": 2, "GOVERN": 3}

# ----------------------------
# LOADERS
# ----------------------------


def load_inputs():
    """Load all input files."""
    try:
        import pandas as pd

        # Load capability metadata
        if CAP_META.exists():
            caps = pd.read_excel(CAP_META)
        else:
            caps = pd.read_csv(CAP_META_CSV)

        # Load applicability matrix
        if APPLICABILITY.exists():
            appl = pd.read_excel(APPLICABILITY)
        else:
            appl = pd.read_csv(APPLICABILITY_CSV)

        # Load L2.1 supertable
        l21 = pd.read_excel(L21_BASE, sheet_name="SUPERTABLE")

        return (
            caps.to_dict(orient="records"),
            appl.to_dict(orient="records"),
            l21.to_dict(orient="records"),
        )

    except ImportError:
        print("ERROR: pandas required")
        sys.exit(1)


# ----------------------------
# L2.1 ROW INFERENCE
# ----------------------------


def infer_authority_from_row(row: Dict[str, Any]) -> str:
    """Infer authority class from L2.1 row columns."""
    # Check action columns
    has_write = (
        row.get("Write") == "YES" or str(row.get("Write Action", "")).strip() != ""
    )
    has_activate = (
        row.get("Activate") == "YES"
        or str(row.get("Activate Action", "")).strip() != ""
    )
    confirmation = str(row.get("Confirmation Required", "")).upper()

    if confirmation == "YES" or "delete" in str(row.get("Activate Action", "")).lower():
        return "ADMIN"
    if has_activate or "freeze" in str(row.get("Write Action", "")).lower():
        return "CONTROL"
    if has_write:
        return "ACT"
    if row.get("Read") == "YES":
        return "OBSERVE"
    return "OBSERVE"


def infer_determinism_from_row(row: Dict[str, Any]) -> str:
    """Infer determinism from L2.1 row."""
    replay = str(row.get("Replay", "")).upper()
    panel_name = str(row.get("Panel Name", "")).lower()
    domain = str(row.get("Domain", ""))

    if replay == "YES" or "replay" in panel_name or "trace" in panel_name:
        return "STRICT"
    if "prediction" in panel_name or "forecast" in panel_name:
        return "ADVISORY"
    if domain == "Logs":
        return "STRICT"
    return "BOUNDED"


def infer_mutability_from_row(row: Dict[str, Any]) -> str:
    """Infer mutability from L2.1 row."""
    has_write = row.get("Write") == "YES"
    has_activate = row.get("Activate") == "YES"
    action_layer = str(row.get("Action Layer", "")).upper()

    if (
        "GOVERN" in action_layer
        or "policy" in str(row.get("Activate Action", "")).lower()
    ):
        return "GOVERN"
    if has_activate:
        return "EXECUTE"
    if has_write:
        return "WRITE"
    return "READ"


def infer_surface_type(row: Dict[str, Any]) -> str:
    """Infer surface type from L2.1 row."""
    order = str(row.get("Order", "O1"))
    panel_name = str(row.get("Panel Name", "")).lower()

    if "replay" in panel_name or "evidence" in panel_name or "proof" in panel_name:
        return "EVIDENCE"
    if "timeline" in panel_name or "history" in panel_name:
        return "TIMELINE"
    if "action" in panel_name or order in ["O4", "O5"]:
        return "ACTION"
    if order in ["O3"] or "detail" in panel_name:
        return "DETAIL"
    return "TIMELINE"


def extract_baseline_rows(l21_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract L2.1 baseline rows with inferred attributes."""
    baseline = []

    for i, row in enumerate(l21_rows):
        domain = row.get("Domain", "")

        # Skip Overview for now (it's derived)
        if domain == "Overview":
            continue

        baseline_row = {
            "row_id": row.get("row_uid", f"L21-{domain[:3].upper()}-{i:03d}"),
            "original_panel_id": row.get("Panel ID", ""),
            "panel_name": row.get("Panel Name", ""),
            "domain": domain,
            "subdomain": row.get("Subdomain", ""),
            "topic": row.get("Topic", ""),
            "order": row.get("Order", "O1"),
            "surface_type": infer_surface_type(row),
            "authority_required": infer_authority_from_row(row),
            "determinism_required": infer_determinism_from_row(row),
            "mutability_required": infer_mutability_from_row(row),
            "ui_visibility": "VISIBLE"
            if row.get("Visible by Default") == "YES"
            else "COLLAPSIBLE",
            "origin": "BASELINE",
            # Original columns for reference
            "read": row.get("Read", ""),
            "write": row.get("Write", ""),
            "activate": row.get("Activate", ""),
            "replay": row.get("Replay", ""),
        }
        baseline.append(baseline_row)

    return baseline


# ----------------------------
# CAPABILITY ATTRIBUTE MAPPING
# ----------------------------


def map_capability_authority(cap: Dict[str, Any]) -> str:
    """Map capability claimed_role to authority level."""
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


def map_capability_determinism(cap: Dict[str, Any]) -> str:
    """Map capability determinism_claim to level."""
    det = str(cap.get("determinism_claim", "mixed")).lower()

    if det == "deterministic":
        return "STRICT"
    if det == "probabilistic":
        return "ADVISORY"
    return "BOUNDED"


def map_capability_mutability(cap: Dict[str, Any]) -> str:
    """Map capability mutability_claim to level."""
    mut = str(cap.get("mutability_claim", "read")).lower()

    if mut == "control":
        return "GOVERN"
    if mut == "write":
        return "WRITE"
    return "READ"


# ----------------------------
# COMPATIBILITY CHECK
# ----------------------------


def check_compatibility(
    cap_attrs: Dict[str, int], row_attrs: Dict[str, int]
) -> Tuple[bool, str]:
    """
    Check if capability can bind to row.
    Returns (compatible, reason).
    """
    # Authority check: capability must meet or exceed row requirement
    if cap_attrs["authority"] < row_attrs["authority"]:
        return False, "AUTHORITY_MISMATCH"

    # Determinism check: capability must meet or exceed row requirement
    if cap_attrs["determinism"] < row_attrs["determinism"]:
        return False, "DETERMINISM_MISMATCH"

    # Mutability check: capability must meet or exceed row requirement
    if cap_attrs["mutability"] < row_attrs["mutability"]:
        return False, "MUTABILITY_MISMATCH"

    return True, "OK"


# ----------------------------
# ROW GENERATION
# ----------------------------


def generate_row_for_capability(
    cap: Dict[str, Any], domain: str, cap_attrs: Dict[str, int]
) -> Dict[str, Any]:
    """
    Generate a new L2.1 row for a capability that doesn't fit existing rows.
    Only called when structurally required.
    """
    cap_id = cap.get("capability_id", "UNKNOWN")

    # Determine surface type based on authority
    authority_name = [
        k for k, v in AUTHORITY_LEVELS.items() if v == cap_attrs["authority"]
    ][0]
    if authority_name == "OBSERVE":
        surface = "EVIDENCE"
    elif authority_name in ["ACT", "CONTROL"]:
        surface = "ACTION"
    else:
        surface = "SUBSTRATE"

    # Get level names
    det_name = [
        k for k, v in DETERMINISM_LEVELS.items() if v == cap_attrs["determinism"]
    ][0]
    mut_name = [
        k for k, v in MUTABILITY_LEVELS.items() if v == cap_attrs["mutability"]
    ][0]

    return {
        "row_id": f"{domain[:3].upper()}-GEN-{cap_id}",
        "original_panel_id": f"GEN-{cap_id}",
        "panel_name": f"[Generated] {cap.get('canonical_name', cap_id)}",
        "domain": domain,
        "subdomain": "Generated",
        "topic": f"CAP-{cap_id}",
        "order": "O3",
        "surface_type": surface,
        "authority_required": authority_name,
        "determinism_required": det_name,
        "mutability_required": mut_name,
        "ui_visibility": "COLLAPSIBLE",
        "origin": "GENERATED",
        "generated_for": cap_id,
        "read": "YES",
        "write": "NO",
        "activate": "NO",
        "replay": "NO",
    }


# ----------------------------
# MAIN SCAN
# ----------------------------


def run_scan():
    """Run the L2.1 capability compatibility scan."""
    caps, appl, l21_raw = load_inputs()

    print("\n[2/5] Extracting L2.1 baseline rows...")
    baseline_rows = extract_baseline_rows(l21_raw)
    print(f"  Extracted {len(baseline_rows)} rows (excluding Overview)")

    # Group baseline by domain
    rows_by_domain = {}
    for row in baseline_rows:
        domain = row["domain"]
        if domain not in rows_by_domain:
            rows_by_domain[domain] = []
        rows_by_domain[domain].append(row)

    print(f"  Domains: {list(rows_by_domain.keys())}")
    for d, rows in rows_by_domain.items():
        print(f"    {d}: {len(rows)} rows")

    print("\n[3/5] Running compatibility scan...")

    # Build capability lookup
    cap_lookup = {c.get("capability_id"): c for c in caps}

    bounded_rows = []
    failures = []
    generated = []

    # Filter to CONSUME/DEFER only
    applicable = [a for a in appl if a.get("decision") in ("CONSUME", "DEFER")]
    print(f"  Scanning {len(applicable)} applicable capability-domain pairs")

    for app in applicable:
        cap_id = app.get("capability_id")
        domain = str(app.get("domain", ""))

        if not domain or cap_id not in cap_lookup:
            failures.append(
                {
                    "capability_id": cap_id,
                    "domain": domain,
                    "reason": "CAPABILITY_NOT_FOUND",
                }
            )
            continue

        cap = cap_lookup[cap_id]

        # Map capability attributes to levels
        cap_attrs = {
            "authority": AUTHORITY_LEVELS[map_capability_authority(cap)],
            "determinism": DETERMINISM_LEVELS[map_capability_determinism(cap)],
            "mutability": MUTABILITY_LEVELS[map_capability_mutability(cap)],
        }

        # Get domain rows
        domain_rows = rows_by_domain.get(domain, [])
        bound = False
        bind_reasons = []

        for row in domain_rows:
            row_attrs = {
                "authority": AUTHORITY_LEVELS[row["authority_required"]],
                "determinism": DETERMINISM_LEVELS[row["determinism_required"]],
                "mutability": MUTABILITY_LEVELS[row["mutability_required"]],
            }

            ok, reason = check_compatibility(cap_attrs, row_attrs)

            if ok:
                bounded_rows.append(
                    {
                        **row,
                        "capability_id": cap_id,
                        "capability_name": cap.get("canonical_name", ""),
                        "binding_status": "PASS",
                        "binding_reason": "COMPATIBLE",
                    }
                )
                bound = True
            else:
                bind_reasons.append(f"{row['row_id']}:{reason}")

        if not bound:
            # Attempt controlled row expansion
            new_row = generate_row_for_capability(cap, domain, cap_attrs)

            # Verify new row doesn't exceed capability
            new_row_attrs = {
                "authority": AUTHORITY_LEVELS[new_row["authority_required"]],
                "determinism": DETERMINISM_LEVELS[new_row["determinism_required"]],
                "mutability": MUTABILITY_LEVELS[new_row["mutability_required"]],
            }

            if (
                new_row_attrs["authority"] <= cap_attrs["authority"]
                and new_row_attrs["determinism"] <= cap_attrs["determinism"]
                and new_row_attrs["mutability"] <= cap_attrs["mutability"]
            ):
                generated.append(new_row)
                bounded_rows.append(
                    {
                        **new_row,
                        "capability_id": cap_id,
                        "capability_name": cap.get("canonical_name", ""),
                        "binding_status": "PASS-GENERATED",
                        "binding_reason": "ROW_GENERATED",
                    }
                )
            else:
                failures.append(
                    {
                        "capability_id": cap_id,
                        "domain": domain,
                        "reason": "NO_COMPATIBLE_ROW",
                        "tried": "; ".join(bind_reasons[:5]),
                    }
                )

    return baseline_rows, bounded_rows, failures, generated


# ----------------------------
# OUTPUT
# ----------------------------


def write_outputs(baseline: List, bounded: List, failures: List, generated: List):
    """Write all output files."""
    import pandas as pd

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Baseline rows
    pd.DataFrame(baseline).to_excel(OUT_BASELINE, index=False)
    print(f"  [baseline] {OUT_BASELINE}")

    # Bounded supertable
    pd.DataFrame(bounded).to_excel(OUT_BOUND, index=False)
    print(f"  [bounded]  {OUT_BOUND}")

    # Failures
    pd.DataFrame(failures).to_excel(OUT_FAIL, index=False)
    print(f"  [failures] {OUT_FAIL}")

    # Generated rows
    pd.DataFrame(generated).to_excel(OUT_GEN, index=False)
    print(f"  [generated] {OUT_GEN}")


def print_summary(baseline: List, bounded: List, failures: List, generated: List):
    """Print scan summary."""
    print("\n" + "=" * 70)
    print("STEP 1B L2.1 COMPATIBILITY SCAN SUMMARY")
    print("=" * 70)

    print(f"\nBaseline Rows: {len(baseline)}")
    print(f"Bounded Bindings: {len(bounded)}")
    print(f"  - PASS: {sum(1 for b in bounded if b.get('binding_status') == 'PASS')}")
    print(
        f"  - PASS-GENERATED: {sum(1 for b in bounded if b.get('binding_status') == 'PASS-GENERATED')}"
    )
    print(f"Failures: {len(failures)}")
    print(f"Generated Rows: {len(generated)}")

    # Per-domain breakdown
    print("\n" + "-" * 70)
    print("PER-DOMAIN BREAKDOWN")
    print("-" * 70)

    domains = set(b.get("domain") for b in bounded)
    for domain in sorted(domains):
        domain_bound = [b for b in bounded if b.get("domain") == domain]
        domain_gen = [g for g in generated if g.get("domain") == domain]
        print(f"\n{domain}:")
        print(f"  Bindings: {len(domain_bound)}")
        print(f"  Generated: {len(domain_gen)}")

        # Show unique capabilities bound
        caps_bound = set(b.get("capability_id") for b in domain_bound)
        print(f"  Capabilities: {len(caps_bound)}")
        for cap in sorted(caps_bound):
            status = [
                b.get("binding_status")
                for b in domain_bound
                if b.get("capability_id") == cap
            ][0]
            print(f"    {cap}: {status}")

    # Failures breakdown
    if failures:
        print("\n" + "-" * 70)
        print("FAILURES")
        print("-" * 70)
        for f in failures:
            print(f"  {f.get('capability_id')} @ {f.get('domain')}: {f.get('reason')}")

    print("\n" + "=" * 70)


# ----------------------------
# ENTRYPOINT
# ----------------------------


def main():
    print("=" * 70)
    print("STEP 1B: L2.1 Capability Compatibility Scan")
    print("Reference: PIN-362")
    print("=" * 70)

    print("\n[1/5] Loading inputs...")

    if not CAP_META.exists() and not CAP_META_CSV.exists():
        print("ERROR: Capability metadata not found. Run STEP 0B first.")
        sys.exit(1)

    if not APPLICABILITY.exists() and not APPLICABILITY_CSV.exists():
        print("ERROR: Applicability matrix not found. Run STEP 1 first.")
        sys.exit(1)

    if not L21_BASE.exists():
        print(f"ERROR: L2.1 supertable not found at {L21_BASE}")
        sys.exit(1)

    baseline, bounded, failures, generated = run_scan()

    print("\n[4/5] Writing outputs...")
    write_outputs(baseline, bounded, failures, generated)

    print("\n[5/5] Summary...")
    print_summary(baseline, bounded, failures, generated)

    print("\nSTEP 1B COMPLETE")
    print(f"Authoritative output: {OUT_BOUND}")


if __name__ == "__main__":
    main()
