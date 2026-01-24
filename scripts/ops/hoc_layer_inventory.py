#!/usr/bin/env python3
"""
HOC Layer Inventory Generator

Generates a CSV mapping all files across HOC layer topology for customer domains.
Reference: HOC Layer Topology V1.4.0, PIN-470

Usage:
    python scripts/ops/hoc_layer_inventory.py
    python scripts/ops/hoc_layer_inventory.py --output inventory.csv
"""

import csv
import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field

# Configuration
BACKEND_ROOT = Path(__file__).parent.parent.parent / "backend"
FRONTEND_ROOT = Path(__file__).parent.parent.parent / "website" / "app-shell"
HOC_ROOT = BACKEND_ROOT / "app" / "hoc"
MODELS_ROOT = BACKEND_ROOT / "app" / "models"

# Customer domains
CUSTOMER_DOMAINS = [
    "general",
    "overview",
    "activity",
    "incidents",
    "policies",
    "logs",
    "analytics",
    "integrations",
    "api_keys",
    "account",
]

@dataclass
class LayerFiles:
    """Files found in a specific layer."""
    files: List[str] = field(default_factory=list)
    missing: bool = False
    notes: str = ""


@dataclass
class DomainInventory:
    """Inventory for a single domain across all layers."""
    domain: str
    l1_frontend: LayerFiles = field(default_factory=LayerFiles)
    l2_1_facades: LayerFiles = field(default_factory=LayerFiles)
    l2_apis: LayerFiles = field(default_factory=LayerFiles)
    l3_adapters: LayerFiles = field(default_factory=LayerFiles)
    l4_runtime: LayerFiles = field(default_factory=LayerFiles)
    l5_engines: LayerFiles = field(default_factory=LayerFiles)
    l5_schemas: LayerFiles = field(default_factory=LayerFiles)
    l5_other: LayerFiles = field(default_factory=LayerFiles)  # notifications, support, vault, etc.
    l6_drivers: LayerFiles = field(default_factory=LayerFiles)
    l7_models: LayerFiles = field(default_factory=LayerFiles)


def scan_directory(path: Path, extensions: tuple = (".py",)) -> List[str]:
    """Scan directory for files with given extensions, excluding __init__.py and __pycache__."""
    if not path.exists():
        return []

    files = []
    for item in path.rglob("*"):
        if item.is_file() and item.suffix in extensions:
            if item.name == "__init__.py":
                continue
            if "__pycache__" in str(item):
                continue
            # Get relative path from the scanned directory
            rel_path = item.relative_to(path)
            files.append(str(rel_path))

    return sorted(files)


def scan_l1_frontend(domain: str) -> LayerFiles:
    """Scan L1 Frontend layer for domain-specific pages/components."""
    result = LayerFiles()

    # Check pages directory
    pages_dir = FRONTEND_ROOT / "src" / "pages"
    if pages_dir.exists():
        # Look for domain-related files
        domain_patterns = {
            "activity": ["Run", "Activity"],
            "analytics": ["Cost", "Usage", "Analytics"],
            "account": ["Credits", "Account", "Profile"],
            "policies": ["Policy", "Policies"],
            "incidents": ["Incident"],
            "logs": ["Log", "Trace", "Audit"],
            "overview": ["Overview", "Dashboard"],
            "integrations": ["Integration", "Connector"],
            "api_keys": ["ApiKey", "Key"],
            "general": ["General"],
        }

        patterns = domain_patterns.get(domain, [domain.capitalize()])

        for f in pages_dir.rglob("*.tsx"):
            if "__pycache__" in str(f):
                continue
            for pattern in patterns:
                if pattern in f.name:
                    result.files.append(f.name)
                    break

    if not result.files:
        result.missing = True
        result.notes = "To be built with UI projection"

    return result


def scan_l2_1_facades(domain: str) -> LayerFiles:
    """Scan L2.1 HTTP Facades layer."""
    result = LayerFiles()

    facades_dir = HOC_ROOT / "api" / "facades" / "cus"
    if facades_dir.exists():
        # Look for domain-specific facade
        domain_file = facades_dir / f"{domain}_facade.py"
        if domain_file.exists():
            result.files.append(f"{domain}_facade.py")

        # Also check for files containing domain name
        for f in facades_dir.glob("*.py"):
            if f.name == "__init__.py":
                continue
            if domain in f.name.lower() and f.name not in result.files:
                result.files.append(f.name)

    if not result.files:
        result.missing = True
        result.notes = "No dedicated facade"

    return result


def scan_l2_apis(domain: str) -> LayerFiles:
    """Scan L2 API routes layer."""
    result = LayerFiles()

    api_dir = HOC_ROOT / "api" / "cus" / domain
    if api_dir.exists():
        result.files = scan_directory(api_dir, (".py",))

    if not result.files:
        result.missing = True
        result.notes = "No API routes"

    return result


def scan_l3_adapters(domain: str) -> LayerFiles:
    """Scan L3 Adapters layer."""
    result = LayerFiles()

    adapters_dir = HOC_ROOT / "cus" / domain / "L3_adapters"
    if adapters_dir.exists():
        result.files = scan_directory(adapters_dir, (".py",))

    # Also check old adapters/ location
    old_adapters_dir = HOC_ROOT / "cus" / domain / "adapters"
    if old_adapters_dir.exists():
        old_files = scan_directory(old_adapters_dir, (".py",))
        for f in old_files:
            if f not in result.files:
                result.files.append(f"(old) {f}")

    if not result.files:
        result.missing = True
        result.notes = "No adapters needed"

    return result


def scan_l4_runtime(domain: str) -> LayerFiles:
    """Scan L4 Runtime layer (only in general domain)."""
    result = LayerFiles()

    if domain == "general":
        runtime_dir = HOC_ROOT / "cus" / "general" / "L4_runtime"
        if runtime_dir.exists():
            result.files = scan_directory(runtime_dir, (".py",))
    else:
        result.notes = "L4 only in general/"

    if domain == "general" and not result.files:
        result.missing = True
        result.notes = "Runtime not implemented"

    return result


def scan_l5_engines(domain: str) -> LayerFiles:
    """Scan L5 Engines layer."""
    result = LayerFiles()

    engines_dir = HOC_ROOT / "cus" / domain / "L5_engines"
    if engines_dir.exists():
        result.files = scan_directory(engines_dir, (".py",))

    # Also check old engines/ location
    old_engines_dir = HOC_ROOT / "cus" / domain / "engines"
    if old_engines_dir.exists():
        old_files = scan_directory(old_engines_dir, (".py",))
        for f in old_files:
            if f not in result.files:
                result.files.append(f"(old) {f}")

    if not result.files:
        result.missing = True
        result.notes = "No engines"

    return result


def scan_l5_schemas(domain: str) -> LayerFiles:
    """Scan L5 Schemas layer."""
    result = LayerFiles()

    schemas_dir = HOC_ROOT / "cus" / domain / "L5_schemas"
    if schemas_dir.exists():
        result.files = scan_directory(schemas_dir, (".py",))

    # Also check old schemas/ location
    old_schemas_dir = HOC_ROOT / "cus" / domain / "schemas"
    if old_schemas_dir.exists():
        old_files = scan_directory(old_schemas_dir, (".py",))
        for f in old_files:
            if f not in result.files:
                result.files.append(f"(old) {f}")

    if not result.files:
        result.missing = True
        result.notes = "No schemas"

    return result


def scan_l5_other(domain: str) -> LayerFiles:
    """Scan other L5 subdirectories (notifications, support, vault, lifecycle, controls, etc.)."""
    result = LayerFiles()

    domain_dir = HOC_ROOT / "cus" / domain
    if not domain_dir.exists():
        return result

    # Look for other L5_ prefixed directories
    l5_dirs = [
        "L5_notifications",
        "L5_support",
        "L5_vault",
        "L5_lifecycle",
        "L5_controls",
        "L5_ui",
        "L5_utils",
        "L5_workflow",
    ]

    for l5_dir in l5_dirs:
        subdir = domain_dir / l5_dir
        if subdir.exists():
            files = scan_directory(subdir, (".py",))
            for f in files:
                result.files.append(f"{l5_dir}/{f}")

    # Also check old named directories
    old_dirs = ["lifecycle", "controls", "notifications", "support"]
    for old_dir in old_dirs:
        subdir = domain_dir / old_dir
        if subdir.exists():
            files = scan_directory(subdir, (".py",))
            for f in files:
                result.files.append(f"(old) {old_dir}/{f}")

    return result


def scan_l6_drivers(domain: str) -> LayerFiles:
    """Scan L6 Drivers layer."""
    result = LayerFiles()

    drivers_dir = HOC_ROOT / "cus" / domain / "L6_drivers"
    if drivers_dir.exists():
        result.files = scan_directory(drivers_dir, (".py",))

    # Also check old drivers/ location
    old_drivers_dir = HOC_ROOT / "cus" / domain / "drivers"
    if old_drivers_dir.exists():
        old_files = scan_directory(old_drivers_dir, (".py",))
        for f in old_files:
            if f not in result.files:
                result.files.append(f"(old) {f}")

    if not result.files:
        result.missing = True
        result.notes = "No drivers"

    return result


def scan_l7_models(domain: str) -> LayerFiles:
    """Scan L7 Models layer."""
    result = LayerFiles()

    # Models are shared, but we can identify domain-related models
    if not MODELS_ROOT.exists():
        result.missing = True
        result.notes = "Models directory not found"
        return result

    # Domain to model name patterns
    domain_patterns = {
        "general": ["tenant", "knowledge", "contract", "run_lifecycle", "governance"],
        "overview": ["overview"],
        "activity": ["execution", "run", "threshold"],
        "incidents": ["killswitch", "incident", "lessons"],
        "policies": ["policy", "override", "precedence", "scope", "snapshot"],
        "logs": ["audit", "log", "trace", "export"],
        "analytics": ["cost", "prediction", "feedback", "alert", "monitor"],
        "integrations": ["external", "retrieval", "connector"],
        "api_keys": ["api_key"],
        "account": ["tenant", "cus_models"],
    }

    patterns = domain_patterns.get(domain, [domain])

    for f in MODELS_ROOT.glob("*.py"):
        if f.name == "__init__.py":
            continue
        for pattern in patterns:
            if pattern in f.name.lower():
                result.files.append(f.name)
                break

    if not result.files:
        result.notes = "Uses shared models"

    return result


def scan_domain(domain: str) -> DomainInventory:
    """Scan all layers for a single domain."""
    return DomainInventory(
        domain=domain,
        l1_frontend=scan_l1_frontend(domain),
        l2_1_facades=scan_l2_1_facades(domain),
        l2_apis=scan_l2_apis(domain),
        l3_adapters=scan_l3_adapters(domain),
        l4_runtime=scan_l4_runtime(domain),
        l5_engines=scan_l5_engines(domain),
        l5_schemas=scan_l5_schemas(domain),
        l5_other=scan_l5_other(domain),
        l6_drivers=scan_l6_drivers(domain),
        l7_models=scan_l7_models(domain),
    )


def format_layer_cell(layer: LayerFiles) -> str:
    """Format layer files for CSV cell."""
    if layer.missing:
        return f"MISSING: {layer.notes}" if layer.notes else "MISSING"

    if not layer.files:
        return layer.notes if layer.notes else "-"

    # Join files with newlines for multi-line cells
    file_list = "\n".join(layer.files)
    if layer.notes:
        return f"{file_list}\n[{layer.notes}]"
    return file_list


def format_layer_count(layer: LayerFiles) -> str:
    """Format layer file count."""
    if layer.missing:
        return "0 (MISSING)"
    return str(len(layer.files))


def generate_csv(output_path: Optional[str] = None):
    """Generate the HOC layer inventory CSV."""

    print("Scanning HOC Layer Topology for Customer Domains...")
    print(f"HOC Root: {HOC_ROOT}")
    print(f"Frontend Root: {FRONTEND_ROOT}")
    print()

    # Scan all domains
    inventories: List[DomainInventory] = []
    for domain in CUSTOMER_DOMAINS:
        print(f"  Scanning {domain}...")
        inv = scan_domain(domain)
        inventories.append(inv)

    print()

    # Define CSV headers
    headers = [
        "S.No",
        "Domain",
        "L1 Frontend\n(UI Pages/Components)",
        "L1 Count",
        "L2.1 Facades\n(HTTP grouping)",
        "L2.1 Count",
        "L2 APIs\n(hoc/api/cus/{domain}/)",
        "L2 Count",
        "L3 Adapters\n(hoc/cus/{domain}/L3_adapters/)",
        "L3 Count",
        "L4 Runtime\n(hoc/cus/general/L4_runtime/)",
        "L4 Count",
        "L5 Engines\n(hoc/cus/{domain}/L5_engines/)",
        "L5 Eng Count",
        "L5 Schemas\n(hoc/cus/{domain}/L5_schemas/)",
        "L5 Sch Count",
        "L5 Other\n(notifications, support, vault, etc.)",
        "L5 Other Count",
        "L6 Drivers\n(hoc/cus/{domain}/L6_drivers/)",
        "L6 Count",
        "L7 Models\n(app/models/)",
        "L7 Count",
        "Total Files",
        "Status",
    ]

    # Build rows
    rows = []
    for i, inv in enumerate(inventories, 1):
        total = (
            len(inv.l1_frontend.files) +
            len(inv.l2_1_facades.files) +
            len(inv.l2_apis.files) +
            len(inv.l3_adapters.files) +
            len(inv.l4_runtime.files) +
            len(inv.l5_engines.files) +
            len(inv.l5_schemas.files) +
            len(inv.l5_other.files) +
            len(inv.l6_drivers.files) +
            len(inv.l7_models.files)
        )

        # Determine status
        missing_layers = []
        if inv.l1_frontend.missing:
            missing_layers.append("L1")
        if inv.l2_apis.missing:
            missing_layers.append("L2")
        if inv.l5_engines.missing:
            missing_layers.append("L5-eng")
        if inv.l6_drivers.missing:
            missing_layers.append("L6")

        if missing_layers:
            status = f"Missing: {', '.join(missing_layers)}"
        else:
            status = "Complete"

        row = [
            i,
            inv.domain,
            format_layer_cell(inv.l1_frontend),
            format_layer_count(inv.l1_frontend),
            format_layer_cell(inv.l2_1_facades),
            format_layer_count(inv.l2_1_facades),
            format_layer_cell(inv.l2_apis),
            format_layer_count(inv.l2_apis),
            format_layer_cell(inv.l3_adapters),
            format_layer_count(inv.l3_adapters),
            format_layer_cell(inv.l4_runtime),
            format_layer_count(inv.l4_runtime),
            format_layer_cell(inv.l5_engines),
            format_layer_count(inv.l5_engines),
            format_layer_cell(inv.l5_schemas),
            format_layer_count(inv.l5_schemas),
            format_layer_cell(inv.l5_other),
            format_layer_count(inv.l5_other),
            format_layer_cell(inv.l6_drivers),
            format_layer_count(inv.l6_drivers),
            format_layer_cell(inv.l7_models),
            format_layer_count(inv.l7_models),
            total,
            status,
        ]
        rows.append(row)

    # Calculate totals
    totals = ["", "TOTAL"]
    for col_idx in range(2, len(headers)):
        if "Count" in headers[col_idx] or headers[col_idx] == "Total Files":
            total = sum(
                int(row[col_idx].split()[0]) if isinstance(row[col_idx], str) and row[col_idx][0].isdigit()
                else (row[col_idx] if isinstance(row[col_idx], int) else 0)
                for row in rows
            )
            totals.append(total)
        elif headers[col_idx] == "Status":
            totals.append("")
        else:
            totals.append("")
    rows.append(totals)

    # Write CSV
    if output_path is None:
        output_path = str(Path(__file__).parent.parent.parent / "docs" / "architecture" / "hoc" / "HOC_LAYER_INVENTORY.csv")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"CSV generated: {output_path}")
    print()

    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"{'Domain':<15} {'L1':>5} {'L2.1':>5} {'L2':>5} {'L3':>5} {'L4':>5} {'L5-E':>6} {'L5-S':>6} {'L5-O':>6} {'L6':>5} {'L7':>5} {'Total':>6}")
    print("-" * 80)

    grand_total = 0
    for inv in inventories:
        l1 = len(inv.l1_frontend.files)
        l2_1 = len(inv.l2_1_facades.files)
        l2 = len(inv.l2_apis.files)
        l3 = len(inv.l3_adapters.files)
        l4 = len(inv.l4_runtime.files)
        l5_e = len(inv.l5_engines.files)
        l5_s = len(inv.l5_schemas.files)
        l5_o = len(inv.l5_other.files)
        l6 = len(inv.l6_drivers.files)
        l7 = len(inv.l7_models.files)
        total = l1 + l2_1 + l2 + l3 + l4 + l5_e + l5_s + l5_o + l6 + l7
        grand_total += total

        print(f"{inv.domain:<15} {l1:>5} {l2_1:>5} {l2:>5} {l3:>5} {l4:>5} {l5_e:>6} {l5_s:>6} {l5_o:>6} {l6:>5} {l7:>5} {total:>6}")

    print("-" * 80)
    print(f"{'TOTAL':<15} {' ':>5} {' ':>5} {' ':>5} {' ':>5} {' ':>5} {' ':>6} {' ':>6} {' ':>6} {' ':>5} {' ':>5} {grand_total:>6}")
    print()

    # Print missing layers by domain
    print("MISSING LAYERS:")
    print("-" * 40)
    for inv in inventories:
        missing = []
        if inv.l1_frontend.missing:
            missing.append("L1 Frontend")
        if inv.l2_1_facades.missing:
            missing.append("L2.1 Facades")
        if inv.l2_apis.missing:
            missing.append("L2 APIs")
        if inv.l3_adapters.missing:
            missing.append("L3 Adapters")
        if inv.l5_engines.missing:
            missing.append("L5 Engines")
        if inv.l6_drivers.missing:
            missing.append("L6 Drivers")

        if missing:
            print(f"  {inv.domain}: {', '.join(missing)}")

    print()
    return output_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate HOC Layer Inventory CSV")
    parser.add_argument("--output", "-o", help="Output CSV path")
    args = parser.parse_args()

    generate_csv(args.output)
