#!/usr/bin/env python3
"""
Generate customer domain-wise classification report from layer_fit_report.json.
"""
import json
from collections import defaultdict
from pathlib import Path
from datetime import datetime


def extract_domain(file_path: str) -> tuple[str, str]:
    """Extract audience and domain from file path."""
    # Path pattern: app/hoc/{audience}/{domain}/...
    parts = file_path.split("/")
    if "hoc" in parts:
        idx = parts.index("hoc")
        if idx + 2 < len(parts):
            audience = parts[idx + 1]
            domain = parts[idx + 2]
            return audience, domain
    return "unknown", "unknown"


def get_folder_layer(file_path: str) -> str:
    """Determine folder layer from path."""
    if "/api/" in file_path:
        return "L2"
    elif "/facades/" in file_path:
        return "L3"
    elif "/engines/" in file_path:
        return "L4"
    elif "/workers/" in file_path:
        return "L5"
    elif "/drivers/" in file_path or "/schemas/" in file_path:
        return "L6"
    return "?"


def main():
    # Load the report
    report_path = Path(__file__).parent.parent.parent / "docs/architecture/migration/layer_fit_report.json"
    with open(report_path) as f:
        report = json.load(f)

    # Organize files by audience and domain
    domain_data = defaultdict(lambda: defaultdict(list))

    for file_info in report["files"]:
        rel_path = file_info["relative_path"]
        audience, domain = extract_domain(rel_path)
        domain_data[audience][domain].append(file_info)

    # Generate markdown report
    lines = []
    lines.append("# HOC Layer Fit Analysis - Customer Domain Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"**Total Files:** {report['meta']['files_classified']}")
    lines.append(f"**Total Work Items:** {report['meta']['total_work_items']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Focus on CUSTOMER audience
    if "customer" in domain_data:
        customer_domains = domain_data["customer"]

        # Summary table
        lines.append("## Executive Summary")
        lines.append("")
        lines.append("| Domain | Files | FIT | MISFIT | NO_ACTION | HEADER_FIX | RECLASSIFY | EXTRACT_DRIVER | EXTRACT_AUTH | SPLIT |")
        lines.append("|--------|-------|-----|--------|-----------|------------|------------|----------------|--------------|-------|")

        domain_summaries = []
        for domain in sorted(customer_domains.keys()):
            files = customer_domains[domain]
            fit_count = sum(1 for f in files if f["classification"]["layer_fit"])
            misfit_count = len(files) - fit_count

            action_counts = defaultdict(int)
            for f in files:
                action = f.get("refactor_action", "NO_ACTION")
                action_counts[action] += 1

            domain_summaries.append({
                "domain": domain,
                "files": len(files),
                "fit": fit_count,
                "misfit": misfit_count,
                "actions": action_counts
            })

            lines.append(f"| **{domain}** | {len(files)} | {fit_count} | {misfit_count} | "
                        f"{action_counts['NO_ACTION']} | {action_counts['HEADER_FIX_ONLY']} | "
                        f"{action_counts['RECLASSIFY_ONLY']} | {action_counts['EXTRACT_DRIVER']} | "
                        f"{action_counts['EXTRACT_AUTHORITY']} | {action_counts['SPLIT_FILE']} |")

        # Total row
        total_files = sum(d["files"] for d in domain_summaries)
        total_fit = sum(d["fit"] for d in domain_summaries)
        total_misfit = sum(d["misfit"] for d in domain_summaries)
        total_actions = defaultdict(int)
        for d in domain_summaries:
            for action, count in d["actions"].items():
                total_actions[action] += count

        lines.append(f"| **TOTAL** | {total_files} | {total_fit} | {total_misfit} | "
                    f"{total_actions['NO_ACTION']} | {total_actions['HEADER_FIX_ONLY']} | "
                    f"{total_actions['RECLASSIFY_ONLY']} | {total_actions['EXTRACT_DRIVER']} | "
                    f"{total_actions['EXTRACT_AUTHORITY']} | {total_actions['SPLIT_FILE']} |")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Work priority matrix
        lines.append("## Work Priority Matrix")
        lines.append("")
        lines.append("| Priority | Domain | Work Items | LOW | MEDIUM | HIGH | Recommendation |")
        lines.append("|----------|--------|------------|-----|--------|------|----------------|")

        # Sort by work items (excluding NO_ACTION)
        sorted_domains = sorted(domain_summaries,
                               key=lambda d: sum(v for k, v in d["actions"].items() if k != "NO_ACTION"),
                               reverse=True)

        for i, d in enumerate(sorted_domains, 1):
            work_items = sum(v for k, v in d["actions"].items() if k != "NO_ACTION")
            if work_items == 0:
                continue

            low = d["actions"]["HEADER_FIX_ONLY"] + d["actions"]["RECLASSIFY_ONLY"]
            medium = d["actions"]["EXTRACT_DRIVER"]
            high = d["actions"]["EXTRACT_AUTHORITY"] + d["actions"]["SPLIT_FILE"]

            # Recommendation based on composition
            if high > low:
                rec = "Architect review needed"
            elif medium > low:
                rec = "Batch extract drivers"
            else:
                rec = "Quick wins first"

            lines.append(f"| {i} | **{d['domain']}** | {work_items} | {low} | {medium} | {high} | {rec} |")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Detailed domain sections
        lines.append("## Detailed Domain Analysis")
        lines.append("")

        for domain in sorted(customer_domains.keys()):
            files = customer_domains[domain]
            if not files:
                continue

            lines.append(f"### {domain.upper()}")
            lines.append("")

            # Layer distribution
            folder_layers = defaultdict(int)
            declared_layers = defaultdict(int)
            dominant_layers = defaultdict(int)

            for f in files:
                fl = get_folder_layer(f["relative_path"])
                folder_layers[fl] += 1

                dl = f["classification"].get("declared_layer", "?")
                declared_layers[dl or "?"] += 1

                dom = f["classification"].get("dominant_layer", "?")
                dominant_layers[dom or "?"] += 1

            lines.append(f"**Files:** {len(files)}")
            lines.append("")
            lines.append("| Metric | L2 | L3 | L4 | L5 | L6 | ? |")
            lines.append("|--------|-----|-----|-----|-----|-----|---|")
            lines.append(f"| Folder | {folder_layers['L2']} | {folder_layers['L3']} | {folder_layers['L4']} | {folder_layers['L5']} | {folder_layers['L6']} | {folder_layers['?']} |")
            lines.append(f"| Declared | {declared_layers.get('L2', 0)} | {declared_layers.get('L3', 0)} | {declared_layers.get('L4', 0)} | {declared_layers.get('L5', 0)} | {declared_layers.get('L6', 0)} | {declared_layers.get('?', 0)} |")
            lines.append(f"| Dominant | {dominant_layers.get('L2', 0)} | {dominant_layers.get('L3', 0)} | {dominant_layers.get('L4', 0)} | {dominant_layers.get('L5', 0)} | {dominant_layers.get('L6', 0)} | {dominant_layers.get('?', 0) + dominant_layers.get('NONE', 0)} |")
            lines.append("")

            # Work backlog by action
            action_files = defaultdict(list)
            for f in files:
                action = f.get("refactor_action", "NO_ACTION")
                action_files[action].append(f)

            work_items = sum(len(v) for k, v in action_files.items() if k != "NO_ACTION")
            if work_items > 0:
                lines.append(f"**Work Backlog:** {work_items} items")
                lines.append("")

                # Show each action type with sample files
                action_order = ["HEADER_FIX_ONLY", "RECLASSIFY_ONLY", "EXTRACT_DRIVER", "EXTRACT_AUTHORITY", "SPLIT_FILE"]
                for action in action_order:
                    if action in action_files and action_files[action]:
                        action_list = action_files[action]
                        effort = "LOW" if action in ["HEADER_FIX_ONLY", "RECLASSIFY_ONLY"] else "MEDIUM" if action == "EXTRACT_DRIVER" else "HIGH"
                        lines.append(f"**{action}** ({len(action_list)} files, {effort} effort)")
                        lines.append("")
                        # Show up to 5 sample files
                        for f in action_list[:5]:
                            filename = f["relative_path"].split("/")[-1]
                            declared = f["classification"].get("declared_layer", "?")
                            detected = f["classification"].get("dominant_layer", "?")
                            lines.append(f"- `{filename}` (declared: {declared}, detected: {detected})")
                        if len(action_list) > 5:
                            lines.append(f"- ... and {len(action_list) - 5} more")
                        lines.append("")
            else:
                lines.append("**Work Backlog:** No work items (all files fit)")
                lines.append("")

            lines.append("---")
            lines.append("")

    # Also include summary for other audiences
    lines.append("## Other Audiences Summary")
    lines.append("")
    lines.append("| Audience | Domains | Files | Work Items |")
    lines.append("|----------|---------|-------|------------|")

    for audience in sorted(domain_data.keys()):
        if audience == "customer":
            continue
        domains = domain_data[audience]
        total_files = sum(len(files) for files in domains.values())
        work_items = 0
        for files in domains.values():
            for f in files:
                action = f.get("refactor_action", "NO_ACTION")
                if action != "NO_ACTION":
                    work_items += 1
        lines.append(f"| **{audience.upper()}** | {len(domains)} | {total_files} | {work_items} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Recommended Execution Plan")
    lines.append("")
    lines.append("1. **Phase 1: Quick Wins (LOW effort)**")
    lines.append("   - HEADER_FIX_ONLY: Update file headers to match behavior")
    lines.append("   - RECLASSIFY_ONLY: Move files to correct folders")
    lines.append("   - Start with domains: policies, logs, general (high volume, low complexity)")
    lines.append("")
    lines.append("2. **Phase 2: Driver Extraction (MEDIUM effort)**")
    lines.append("   - EXTRACT_DRIVER: Extract DB operations to L6 drivers")
    lines.append("   - Prioritize: policies (34), logs (23), integrations (20)")
    lines.append("   - Use driver extraction templates")
    lines.append("")
    lines.append("3. **Phase 3: Complex Work (HIGH effort)**")
    lines.append("   - EXTRACT_AUTHORITY: Architectural review required")
    lines.append("   - SPLIT_FILE: Careful refactoring needed")
    lines.append("   - Focus domains: integrations (7 HIGH), incidents (2 HIGH)")
    lines.append("")

    # Write the report
    output_path = Path(__file__).parent.parent.parent / "docs/architecture/migration/layer_fit_customer_domains.md"
    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    print(f"Report generated: {output_path}")
    print(f"Total CUSTOMER files: {total_files}")
    print(f"Total work items: {sum(total_actions.values()) - total_actions['NO_ACTION']}")


if __name__ == "__main__":
    main()
