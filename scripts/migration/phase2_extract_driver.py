#!/usr/bin/env python3
"""
Phase 2: EXTRACT_DRIVER Execution

Extracts DB operations from L4 engines to L6 drivers.
This is a semi-automated tool that:
1. Identifies DB operations in engine files
2. Generates driver file templates
3. Updates engine files to import from drivers

Usage:
  python scripts/migration/phase2_extract_driver.py --analyze
  python scripts/migration/phase2_extract_driver.py --generate-templates
  python scripts/migration/phase2_extract_driver.py --batch-by-pattern "*_service.py"
"""
import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Optional


# DB operation patterns to extract
DB_PATTERNS = {
    "imports": [
        r"from sqlalchemy import (select|insert|update|delete)",
        r"from sqlmodel import Session",
        r"from app\.models\.",
    ],
    "operations": [
        r"session\.execute\(",
        r"session\.add\(",
        r"\.scalars\(\)",
        r"\.one\(\)",
        r"\.all\(\)",
        r"\.first\(\)",
        r"\.commit\(\)",
        r"\.flush\(\)",
        r"\.refresh\(",
        r"select\(",
        r"insert\(",
        r"update\(",
        r"delete\(",
    ],
}

LAYER_NAMES = {
    "L2": "API",
    "L3": "Adapter",
    "L4": "Engine",
    "L5": "Worker",
    "L6": "Driver",
}


def get_extract_driver_files(report_path: Path) -> list[dict]:
    """Get files that need EXTRACT_DRIVER."""
    with open(report_path) as f:
        report = json.load(f)

    return [
        f for f in report["files"]
        if f.get("refactor_action") == "EXTRACT_DRIVER"
    ]


def analyze_file_for_db_ops(file_path: Path) -> dict:
    """Analyze a file for DB operations that need extraction."""
    content = file_path.read_text()
    lines = content.split("\n")

    analysis = {
        "file": str(file_path),
        "db_imports": [],
        "db_operations": [],
        "business_logic": [],
        "line_count": len(lines),
        "db_line_count": 0,
    }

    for i, line in enumerate(lines, 1):
        # Check for DB imports
        for pattern in DB_PATTERNS["imports"]:
            if re.search(pattern, line):
                analysis["db_imports"].append({
                    "line": i,
                    "content": line.strip(),
                    "pattern": pattern,
                })
                analysis["db_line_count"] += 1

        # Check for DB operations
        for pattern in DB_PATTERNS["operations"]:
            if re.search(pattern, line):
                analysis["db_operations"].append({
                    "line": i,
                    "content": line.strip(),
                    "pattern": pattern,
                })
                analysis["db_line_count"] += 1

    # Calculate DB density
    analysis["db_density"] = (
        analysis["db_line_count"] / analysis["line_count"] * 100
        if analysis["line_count"] > 0 else 0
    )

    return analysis


def generate_driver_template(
    source_file: Path,
    analysis: dict,
    audience: str,
    domain: str,
) -> str:
    """Generate a driver file template based on analysis."""
    filename = source_file.stem
    class_name = "".join(word.capitalize() for word in filename.split("_"))

    # Determine if read or write service
    is_write = any(
        op["pattern"] in ["insert(", "update(", "delete(", r"\.add\(", r"\.commit\("]
        for op in analysis["db_operations"]
    )
    service_type = "WriteService" if is_write else "ReadService"

    template = f'''# Layer: L6 — Driver
# AUDIENCE: {audience.upper()}
# Role: Data access layer for {filename.replace("_", " ")}

from typing import List, Optional
from sqlalchemy import select
from sqlmodel import Session

# TODO: Import required models
# from app.models.{domain} import YourModel


class {class_name}{service_type}:
    """
    Pure data access - no business logic.

    Extracted from: {source_file.name}
    DB operations found: {len(analysis["db_operations"])}
    """

    def __init__(self, session: Session):
        self.session = session

    # TODO: Extract DB operations from original file
    # Example patterns to extract:
'''

    # Add sample operations from analysis
    seen_patterns = set()
    for op in analysis["db_operations"][:10]:
        if op["content"] not in seen_patterns:
            template += f"    # {op['content']}\n"
            seen_patterns.add(op["content"])

    template += '''
    # def get_by_id(self, id: str) -> Optional[YourModel]:
    #     stmt = select(YourModel).where(YourModel.id == id)
    #     return self.session.execute(stmt).scalar_one_or_none()

    # def get_by_tenant(self, tenant_id: str) -> List[YourModel]:
    #     stmt = select(YourModel).where(YourModel.tenant_id == tenant_id)
    #     return self.session.execute(stmt).scalars().all()
'''

    return template


def extract_path_info(rel_path: str) -> tuple[str, str, str]:
    """Extract audience, domain, and folder from path."""
    parts = rel_path.split("/")
    # app/hoc/{audience}/{domain}/...
    try:
        hoc_idx = parts.index("hoc")
        audience = parts[hoc_idx + 1] if hoc_idx + 1 < len(parts) else "unknown"
        domain = parts[hoc_idx + 2] if hoc_idx + 2 < len(parts) else "unknown"
        folder = parts[hoc_idx + 3] if hoc_idx + 3 < len(parts) else "unknown"
        return audience, domain, folder
    except (ValueError, IndexError):
        return "unknown", "unknown", "unknown"


def group_files_by_pattern(files: list[dict]) -> dict[str, list[dict]]:
    """Group files by naming pattern for batch processing."""
    patterns = {
        "*_service.py": [],
        "*_facade.py": [],
        "*_engine.py": [],
        "*_adapter.py": [],
        "*_other.py": [],
    }

    for f in files:
        filename = Path(f["relative_path"]).name
        if filename.endswith("_service.py"):
            patterns["*_service.py"].append(f)
        elif filename.endswith("_facade.py"):
            patterns["*_facade.py"].append(f)
        elif filename.endswith("_engine.py"):
            patterns["*_engine.py"].append(f)
        elif filename.endswith("_adapter.py"):
            patterns["*_adapter.py"].append(f)
        else:
            patterns["*_other.py"].append(f)

    return patterns


def main():
    parser = argparse.ArgumentParser(description="Phase 2: Driver extraction")
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze files for DB operations"
    )
    parser.add_argument(
        "--generate-templates",
        action="store_true",
        help="Generate driver file templates"
    )
    parser.add_argument(
        "--batch-by-pattern",
        type=str,
        help="Process files matching pattern (e.g., '*_service.py')"
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("docs/architecture/migration/layer_fit_report.json"),
        help="Path to layer fit report"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/architecture/migration/driver_templates"),
        help="Output directory for templates"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of files"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("PHASE 2: EXTRACT_DRIVER ANALYSIS")
    print("=" * 60)

    # Get files to process
    files = get_extract_driver_files(args.report)
    print(f"\nFiles needing EXTRACT_DRIVER: {len(files)}")

    if args.limit:
        files = files[:args.limit]
        print(f"Limited to: {len(files)}")

    if not files:
        print("No files need driver extraction!")
        return 0

    # Group by pattern
    patterns = group_files_by_pattern(files)
    print("\nFiles by pattern:")
    for pattern, pattern_files in sorted(patterns.items(), key=lambda x: -len(x[1])):
        if pattern_files:
            print(f"  {pattern}: {len(pattern_files)}")

    if args.batch_by_pattern:
        # Filter to specific pattern
        files = patterns.get(args.batch_by_pattern, [])
        print(f"\nFiltering to pattern: {args.batch_by_pattern} ({len(files)} files)")

    if args.analyze:
        print("\n" + "=" * 60)
        print("DB OPERATION ANALYSIS")
        print("=" * 60)

        # Group by domain
        by_domain = defaultdict(list)
        for f in files:
            audience, domain, folder = extract_path_info(f["relative_path"])
            by_domain[f"{audience}/{domain}"].append(f)

        total_db_ops = 0
        high_density = []

        for domain_key in sorted(by_domain.keys()):
            domain_files = by_domain[domain_key]
            print(f"\n### {domain_key} ({len(domain_files)} files)")

            for f in domain_files[:5]:  # Show first 5 per domain
                file_path = Path("backend") / f["relative_path"]
                if file_path.exists():
                    analysis = analyze_file_for_db_ops(file_path)
                    total_db_ops += len(analysis["db_operations"])

                    density_icon = "🔴" if analysis["db_density"] > 30 else "🟡" if analysis["db_density"] > 10 else "🟢"
                    print(f"  {density_icon} {file_path.name}: {len(analysis['db_operations'])} ops ({analysis['db_density']:.1f}% density)")

                    if analysis["db_density"] > 30:
                        high_density.append({
                            "file": str(file_path),
                            "ops": len(analysis["db_operations"]),
                            "density": analysis["db_density"],
                        })

            if len(domain_files) > 5:
                print(f"  ... and {len(domain_files) - 5} more")

        print(f"\n\nTotal DB operations to extract: {total_db_ops}")
        print(f"High-density files (>30%): {len(high_density)}")

        if high_density:
            print("\nPriority extraction candidates:")
            for hd in sorted(high_density, key=lambda x: -x["density"])[:10]:
                print(f"  - {Path(hd['file']).name}: {hd['ops']} ops ({hd['density']:.1f}%)")

    if args.generate_templates:
        print("\n" + "=" * 60)
        print("GENERATING DRIVER TEMPLATES")
        print("=" * 60)

        args.output_dir.mkdir(parents=True, exist_ok=True)

        generated = 0
        for f in files:
            file_path = Path("backend") / f["relative_path"]
            if not file_path.exists():
                continue

            audience, domain, folder = extract_path_info(f["relative_path"])
            analysis = analyze_file_for_db_ops(file_path)

            # Only generate for files with actual DB operations
            if not analysis["db_operations"]:
                continue

            # Generate template
            template = generate_driver_template(file_path, analysis, audience, domain)

            # Save template
            template_path = args.output_dir / f"{file_path.stem}_driver.py"
            template_path.write_text(template)
            generated += 1

            print(f"  ✅ {template_path.name}")

        print(f"\n✅ Generated {generated} driver templates in {args.output_dir}")

    return 0


if __name__ == "__main__":
    exit(main())
