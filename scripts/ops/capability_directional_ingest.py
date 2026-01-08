#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Type: Governance Script
# Reference: PIN-360 (STEP 0B Directional Capability Normalization)
#
# STEP 0B – Directional Capability Normalization
#
# Inputs:
# - CAPABILITY_REGISTRY_UNIFIED.yaml (HIGH authority)
# - PIN-329-capability-promotion-merge-report.md (MEDIUM authority)
#
# Outputs:
# - capability_directional_metadata.xlsx (authoritative)
# - capability_directional_metadata.csv (derived)
# - capability_directional_metadata.yaml (derived)
#
# Design Principles:
# - No LLM calls - deterministic only
# - Same inputs → same outputs. Always.
# - May add inferred columns, may NOT remove/rename capabilities

from pathlib import Path
import yaml
import re
import sys
from typing import Dict, List, Any

# ----------------------------
# CONFIG
# ----------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "docs/capabilities/CAPABILITY_REGISTRY_UNIFIED.yaml"
PIN329_PATH = (
    REPO_ROOT / "docs/memory-pins/PIN-329-capability-promotion-merge-report.md"
)

OUTPUT_DIR = REPO_ROOT / "docs/capabilities/directional"
OUTPUT_XLSX = OUTPUT_DIR / "capability_directional_metadata.xlsx"
OUTPUT_CSV = OUTPUT_DIR / "capability_directional_metadata.csv"
OUTPUT_YAML = OUTPUT_DIR / "capability_directional_metadata.yaml"


# ----------------------------
# LOADERS
# ----------------------------


def load_registry() -> Dict[str, Any]:
    """Load the unified capability registry."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_pin329_text() -> str:
    """Load PIN-329 report as raw text for governance extraction."""
    return PIN329_PATH.read_text(encoding="utf-8")


# ----------------------------
# GOVERNANCE PARSING
# ----------------------------


def extract_pin329_metadata(pin_text: str, capability_id: str) -> Dict[str, Any]:
    """
    Extract governance hints from PIN-329 report.
    This is heuristic but deterministic.
    """
    data = {
        "promotion_origin": "pre-PIN-329",
        "governance_notes": "",
        "pin329_mentioned": False,
        "merged_from_count": 0,
        "has_justification": False,
    }

    if capability_id in pin_text:
        data["pin329_mentioned"] = True

        # Check for promotion origin
        if f"{capability_id}" in pin_text and "promoted" in pin_text.lower():
            # Check if this capability was promoted
            promoted_section = re.search(
                rf"(promoted|Promoted|PROMOTED).*{capability_id}", pin_text
            )
            new_cap_section = re.search(
                rf"{capability_id}.*\(NEW.*PROMOTED\)", pin_text
            )
            if promoted_section or new_cap_section:
                data["promotion_origin"] = "promoted_from_PIN-329"

        # Check for internalization
        if "internalized" in pin_text.lower() and capability_id.startswith("SUB-"):
            internalized_section = re.search(
                rf"{capability_id}.*internalized|internalized.*{capability_id}",
                pin_text,
                re.IGNORECASE,
            )
            if internalized_section:
                data["promotion_origin"] = "internalized_from_PIN-329"

        # Check for merge information
        merged_matches = re.findall(
            rf"{capability_id}.*Merged.*LCAP|Merged.*{capability_id}",
            pin_text,
            re.IGNORECASE,
        )
        if merged_matches:
            data["merged_from_count"] = len(merged_matches)

        # Extract surrounding context as governance notes
        match = re.search(rf"(.{{0,200}}{capability_id}.{{0,200}})", pin_text)
        if match:
            data["governance_notes"] = match.group(1).replace("\n", " ").strip()

        # Check for justification
        if "justification" in data["governance_notes"].lower():
            data["has_justification"] = True

    return data


# ----------------------------
# ATTRIBUTE INFERENCE
# ----------------------------


def infer_exposure_type(cap: Dict[str, Any]) -> str:
    """Infer exposure type from capability definition."""
    console_scope = cap.get("console_scope", "NONE")
    routes = cap.get("routes", [])
    commands = cap.get("commands", [])
    sdk_methods = cap.get("sdk_methods", [])
    execution_vectors = cap.get("execution_vectors", [])

    if "sdk" in execution_vectors or sdk_methods:
        return "SDK"
    if "cli" in execution_vectors or commands:
        return "CLI"
    if routes and console_scope in ["CUSTOMER", "FOUNDER"]:
        return "UI"
    if routes:
        return "API"
    return "INTERNAL"


def infer_role(cap: Dict[str, Any]) -> str:
    """Infer capability role from description and name."""
    name = cap.get("name", "").lower()
    description = cap.get("description", "").lower()

    # Engine patterns
    if any(
        word in name for word in ["engine", "workflow", "pipeline", "orchestration"]
    ):
        return "engine"

    # Middleware patterns
    if any(word in name for word in ["authentication", "authorization", "routing"]):
        return "middleware"

    # Advisory patterns
    if any(
        word in description
        for word in ["read-only", "advisory", "prediction", "observation"]
    ):
        return "advisory"

    # Control patterns
    if any(
        word in description
        for word in ["control", "management", "execution", "enforce"]
    ):
        return "control"

    # Substrate patterns
    if cap.get("status") == "SUBSTRATE":
        return "substrate"

    return "unknown"


def infer_determinism(cap: Dict[str, Any]) -> str:
    """Infer determinism claim from capability."""
    name = cap.get("name", "").lower()
    description = cap.get("description", "").lower()

    if any(
        word in name + description
        for word in ["prediction", "learning", "ml", "probabilistic"]
    ):
        return "probabilistic"
    if any(
        word in name + description for word in ["deterministic", "replay", "immutable"]
    ):
        return "deterministic"
    return "mixed"


def infer_mutability(cap: Dict[str, Any]) -> str:
    """Infer mutability from routes and description."""
    routes = cap.get("routes", [])
    founder_only = cap.get("founder_only_routes", [])
    description = cap.get("description", "").lower()

    # Check for write/control operations
    has_write = any(
        r.startswith(("POST", "PUT", "DELETE", "PATCH")) for r in routes + founder_only
    )

    if has_write and any(
        word in description for word in ["control", "management", "execute"]
    ):
        return "control"
    if has_write:
        return "write"
    if "read-only" in description:
        return "read"
    return "read"


def infer_replay_claim(cap: Dict[str, Any]) -> str:
    """Infer if capability supports replay."""
    name = cap.get("name", "").lower()
    description = cap.get("description", "").lower()
    routes = cap.get("routes", [])

    if "replay" in name or "replay" in description:
        return "yes"
    if any("replay" in r.lower() for r in routes):
        return "yes"
    if any(word in description for word in ["immutable", "trace", "deterministic"]):
        return "yes"
    return "unknown"


def infer_export_claim(cap: Dict[str, Any]) -> str:
    """Infer if capability supports data export."""
    routes = cap.get("routes", [])
    description = cap.get("description", "").lower()

    if any("export" in r.lower() for r in routes):
        return "yes"
    if "export" in description:
        return "yes"
    return "unknown"


# ----------------------------
# TRUST WEIGHT LOGIC
# ----------------------------


def compute_trust_weight(row: Dict[str, Any]) -> str:
    """
    Formal trust-weight rules per PIN-360.

    Elevation Rules:
    - T1: Registry + Code Alignment → MEDIUM
    - T2: Registry + Governance Rationale → MEDIUM
    - T3: Execution + Governance + Code → HIGH

    Degradation Rules:
    - D1: Planned → Always LOW
    - D2: Claude-only presence → Always LOW
    - D3: Middleware/Internal-only → max MEDIUM
    """
    # D1: Planned always LOW
    if row.get("lifecycle_state") == "planned":
        return "LOW"

    # Check conditions
    has_execution_semantics = row.get("claimed_role") in ["engine", "control"]
    has_code_artifacts = row.get("has_routes", False) or row.get(
        "has_sdk_methods", False
    )
    pin329_mentioned = row.get("pin329_mentioned", False)
    is_internal_only = row.get("claimed_exposure_type") == "INTERNAL"
    is_substrate = row.get("status") == "SUBSTRATE"

    # T3: Execution + Governance + Code → HIGH
    if has_execution_semantics and pin329_mentioned and has_code_artifacts:
        # D3: But internal-only caps MEDIUM
        if is_internal_only or is_substrate:
            return "MEDIUM"
        return "HIGH"

    # T2: Registry + Governance Rationale → MEDIUM
    if pin329_mentioned:
        return "MEDIUM"

    # T1: Registry + Code Alignment → MEDIUM
    if has_code_artifacts:
        return "MEDIUM"

    # Default: LOW
    return "LOW"


# ----------------------------
# NORMALIZATION
# ----------------------------


def normalize_capability(cap: Dict[str, Any], pin_text: str) -> Dict[str, Any]:
    """Normalize a single capability into directional profile."""
    cap_id = cap.get("capability_id", "UNKNOWN")

    # Extract PIN-329 metadata
    pin_meta = extract_pin329_metadata(pin_text, cap_id)

    # Determine origin
    origin = cap.get("origin", "pre-PIN-326")
    if "promoted" in str(origin).lower():
        pin_meta["promotion_origin"] = "promoted_from_PIN-329"
    elif "internalized" in str(origin).lower():
        pin_meta["promotion_origin"] = "internalized_from_PIN-329"
    elif pin_meta["promotion_origin"] == "pre-PIN-329":
        pin_meta["promotion_origin"] = origin if origin else "pre-PIN-329"

    # Build row
    routes = cap.get("routes", [])
    commands = cap.get("commands", [])
    sdk_methods = cap.get("sdk_methods", [])

    row = {
        "capability_id": cap_id,
        "canonical_name": cap.get("name", ""),
        "status": cap.get("status", "UNKNOWN"),
        "lifecycle_state": "active"
        if cap.get("status") in ["FIRST_CLASS", "SUBSTRATE"]
        else "planned",
        "promotion_origin": pin_meta["promotion_origin"],
        "claimed_console_scope": cap.get("console_scope", "NONE"),
        "claimed_exposure_type": infer_exposure_type(cap),
        "claimed_role": cap.get("role") or infer_role(cap),
        "determinism_claim": infer_determinism(cap),
        "mutability_claim": cap.get("mutability") or infer_mutability(cap),
        "replay_claim": infer_replay_claim(cap),
        "export_claim": infer_export_claim(cap),
        "owner": cap.get("owner", "platform"),
        "layer": cap.get("layer", ""),
        "has_routes": len(routes) > 0,
        "route_count": len(routes),
        "has_sdk_methods": len(sdk_methods) > 0,
        "sdk_method_count": len(sdk_methods),
        "has_commands": len(commands) > 0,
        "command_count": len(commands),
        "pin329_mentioned": pin_meta["pin329_mentioned"],
        "merged_from_count": pin_meta.get("merged_from_count", 0),
        "has_justification": pin_meta.get("has_justification", False),
        "governance_notes": pin_meta["governance_notes"][:200]
        if pin_meta["governance_notes"]
        else "",
        "normalization_notes": "",
    }

    # Compute trust weight
    row["trust_weight"] = compute_trust_weight(row)

    # Add normalization notes
    notes = []
    if row["lifecycle_state"] == "planned":
        notes.append("PLANNED - not implemented")
    if row["claimed_exposure_type"] == "INTERNAL":
        notes.append("Internal-only, no user exposure")
    if row["status"] == "SUBSTRATE":
        notes.append("Substrate - never user-invokable")
    if row["merged_from_count"] > 0:
        notes.append(f"Merged from {row['merged_from_count']} LCAPs")
    row["normalization_notes"] = "; ".join(notes)

    return row


def normalize_all_capabilities() -> List[Dict[str, Any]]:
    """Normalize all capabilities from registry."""
    registry = load_registry()
    pin_text = load_pin329_text()

    rows = []

    # Process FIRST_CLASS capabilities
    first_class = registry.get("first_class_capabilities", {})
    for cap_id, cap in first_class.items():
        cap["capability_id"] = cap_id
        row = normalize_capability(cap, pin_text)
        rows.append(row)

    # Process SUBSTRATE capabilities
    substrate = registry.get("substrate_capabilities", {})
    for cap_id, cap in substrate.items():
        cap["capability_id"] = cap_id
        row = normalize_capability(cap, pin_text)
        rows.append(row)

    # Sort by capability_id for deterministic output
    def sort_key(x: Dict[str, Any]) -> tuple:
        cap_id = x["capability_id"]
        prefix = 0 if cap_id.startswith("CAP-") else 1
        match = re.search(r"\d+", cap_id)
        num = int(match.group()) if match else 999
        return (prefix, num)

    rows.sort(key=sort_key)

    return rows


# ----------------------------
# OUTPUT
# ----------------------------


def write_outputs(rows: List[Dict[str, Any]]) -> None:
    """Write outputs in xlsx, csv, and yaml formats."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Try pandas for xlsx/csv
    try:
        import pandas as pd

        df = pd.DataFrame(rows)

        # Reorder columns for readability
        column_order = [
            "capability_id",
            "canonical_name",
            "status",
            "lifecycle_state",
            "promotion_origin",
            "trust_weight",
            "claimed_console_scope",
            "claimed_exposure_type",
            "claimed_role",
            "determinism_claim",
            "mutability_claim",
            "replay_claim",
            "export_claim",
            "owner",
            "layer",
            "has_routes",
            "route_count",
            "has_sdk_methods",
            "sdk_method_count",
            "has_commands",
            "command_count",
            "pin329_mentioned",
            "merged_from_count",
            "has_justification",
            "governance_notes",
            "normalization_notes",
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
        print("  [WARNING] pandas not available, writing csv manually")
        # Fallback: write csv manually
        import csv

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        print(f"  [csv]  {OUTPUT_CSV}")

    # Write yaml (always works)
    with open(OUTPUT_YAML, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            rows, f, default_flow_style=False, allow_unicode=True, sort_keys=False
        )
    print(f"  [yaml] {OUTPUT_YAML}")


def print_summary(rows: List[Dict[str, Any]]) -> None:
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("STEP 0B DIRECTIONAL NORMALIZATION SUMMARY")
    print("=" * 60)

    total = len(rows)
    first_class = sum(1 for r in rows if r["status"] == "FIRST_CLASS")
    substrate = sum(1 for r in rows if r["status"] == "SUBSTRATE")

    print(f"\nCapabilities Processed: {total}")
    print(f"  - FIRST_CLASS: {first_class}")
    print(f"  - SUBSTRATE:   {substrate}")

    # Trust weight distribution
    high = sum(1 for r in rows if r["trust_weight"] == "HIGH")
    medium = sum(1 for r in rows if r["trust_weight"] == "MEDIUM")
    low = sum(1 for r in rows if r["trust_weight"] == "LOW")

    print("\nTrust Weight Distribution:")
    print(f"  - HIGH:   {high}")
    print(f"  - MEDIUM: {medium}")
    print(f"  - LOW:    {low}")

    # Console scope distribution
    print("\nConsole Scope Distribution:")
    scopes = {}
    for r in rows:
        scope = r["claimed_console_scope"]
        scopes[scope] = scopes.get(scope, 0) + 1
    for scope, count in sorted(scopes.items()):
        print(f"  - {scope}: {count}")

    # Exposure type distribution
    print("\nExposure Type Distribution:")
    exposures = {}
    for r in rows:
        exp = r["claimed_exposure_type"]
        exposures[exp] = exposures.get(exp, 0) + 1
    for exp, count in sorted(exposures.items()):
        print(f"  - {exp}: {count}")

    # PIN-329 coverage
    mentioned = sum(1 for r in rows if r["pin329_mentioned"])
    print(f"\nPIN-329 Coverage: {mentioned}/{total} ({100 * mentioned // total}%)")

    print("\n" + "=" * 60)


# ----------------------------
# ENTRYPOINT
# ----------------------------


def main():
    print("=" * 60)
    print("STEP 0B: Directional Capability Normalization")
    print("Reference: PIN-360")
    print("=" * 60)

    print("\n[1/3] Loading inputs...")
    print(f"  Registry: {REGISTRY_PATH}")
    print(f"  PIN-329:  {PIN329_PATH}")

    if not REGISTRY_PATH.exists():
        print(f"ERROR: Registry not found at {REGISTRY_PATH}")
        sys.exit(1)
    if not PIN329_PATH.exists():
        print(f"ERROR: PIN-329 not found at {PIN329_PATH}")
        sys.exit(1)

    print("\n[2/3] Normalizing capabilities...")
    rows = normalize_all_capabilities()
    print(f"  Processed {len(rows)} capabilities")

    print("\n[3/3] Writing outputs...")
    write_outputs(rows)

    print_summary(rows)

    print("\nSTEP 0B COMPLETE")
    print(f"Authoritative output: {OUTPUT_XLSX}")


if __name__ == "__main__":
    main()
