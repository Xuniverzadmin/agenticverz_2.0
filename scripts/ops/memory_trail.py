#!/usr/bin/env python3
"""
Memory Trail Automation System

Auto-creates/updates memory PINs, updates INDEX.md, creates test reports.

IMPORTANT: Update existing PINs instead of creating new ones!
- Use `find` to search for related PINs first
- Use `update` to append to existing PINs
- Only use `pin` for genuinely NEW topics

Usage:
    # Find existing PINs (ALWAYS DO THIS FIRST)
    python scripts/ops/memory_trail.py find "ops console"
    python scripts/ops/memory_trail.py find 111

    # Update existing PIN (PREFERRED)
    python scripts/ops/memory_trail.py update 111 \
        --section "Updates" \
        --content "Added customers panel..."

    # Create new PIN (only for NEW topics)
    python scripts/ops/memory_trail.py pin \
        --title "New Feature" \
        --category "Category" \
        --summary "Description"

    # Create a test report
    python scripts/ops/memory_trail.py report \
        --title "Test Name" \
        --type "Integration" \
        --status "PASS"

    # List next available IDs
    python scripts/ops/memory_trail.py next

Author: Agenticverz
Date: 2025-12-20
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Paths
ROOT_DIR = Path(__file__).parent.parent.parent
PINS_DIR = ROOT_DIR / "docs" / "memory-pins"
INDEX_PATH = PINS_DIR / "INDEX.md"
REPORTS_DIR = ROOT_DIR / "docs" / "test_reports"
REGISTER_PATH = REPORTS_DIR / "REGISTER.md"


def get_next_pin_number() -> int:
    """Find the next available PIN number."""
    max_pin = 0
    for f in PINS_DIR.glob("PIN-*.md"):
        match = re.match(r"PIN-(\d+)", f.name)
        if match:
            num = int(match.group(1))
            max_pin = max(max_pin, num)
    return max_pin + 1


def get_next_report_number() -> int:
    """Find the next available test report number."""
    max_tr = 0
    for f in REPORTS_DIR.glob("TR-*.md"):
        match = re.match(r"TR-(\d+)", f.name)
        if match:
            num = int(match.group(1))
            max_tr = max(max_tr, num)
    return max_tr + 1


def find_pin(query: str) -> list[tuple[int, str, Path]]:
    """Find PINs matching a query (number or keyword)."""
    results = []

    # Check if query is a number
    if query.isdigit():
        pin_num = int(query)
        for f in PINS_DIR.glob(f"PIN-{pin_num:03d}-*.md"):
            with open(f, "r") as file:
                first_line = file.readline().strip()
                title = first_line.replace("# ", "").replace(f"PIN-{pin_num:03d}: ", "")
            results.append((pin_num, title, f))
        return results

    # Search by keyword in filename and content
    query_lower = query.lower()
    for f in PINS_DIR.glob("PIN-*.md"):
        match = re.match(r"PIN-(\d+)", f.name)
        if not match:
            continue
        pin_num = int(match.group(1))

        # Check filename
        if query_lower in f.name.lower():
            with open(f, "r") as file:
                first_line = file.readline().strip()
                title = first_line.replace("# ", "").replace(f"PIN-{pin_num:03d}: ", "")
            results.append((pin_num, title, f))
            continue

        # Check content
        with open(f, "r") as file:
            content = file.read()
            first_line = content.split("\n")[0].strip()
            title = first_line.replace("# ", "").replace(f"PIN-{pin_num:03d}: ", "")
            if query_lower in content.lower():
                results.append((pin_num, title, f))

    return sorted(results, key=lambda x: x[0], reverse=True)[:10]


def update_pin(
    pin_num: int,
    section: str,
    content: str,
    update_status: Optional[str] = None,
) -> Path:
    """Update an existing PIN by appending content."""

    # Find the PIN file
    pin_files = list(PINS_DIR.glob(f"PIN-{pin_num:03d}-*.md"))
    if not pin_files:
        print(f"❌ PIN-{pin_num:03d} not found")
        sys.exit(1)

    filepath = pin_files[0]
    today = datetime.now().strftime("%Y-%m-%d")

    with open(filepath, "r") as f:
        pin_content = f.read()

    # Extract title for changelog
    title_match = re.search(r"^# PIN-\d+: (.+)$", pin_content, re.MULTILINE)
    title = title_match.group(1) if title_match else "Unknown"

    # Update status if requested
    if update_status:
        status_emoji = "✅" if update_status.upper() == "COMPLETE" else "🏗️"
        pin_content = re.sub(
            r"\*\*Status:\*\* [^\n]+",
            f"**Status:** {status_emoji} {update_status.upper()}",
            pin_content,
        )

    # Check if section exists
    section_pattern = rf"^## {re.escape(section)}$"
    if re.search(section_pattern, pin_content, re.MULTILINE):
        # Append to existing section
        pattern = rf"(## {re.escape(section)}\n)(.*?)(\n## |\Z)"

        def append_to_section(match):
            existing = match.group(2).rstrip()
            next_section = match.group(3) if match.group(3) != "\Z" else ""
            return f"{match.group(1)}{existing}\n\n### Update ({today})\n\n{content}\n\n{next_section}"

        pin_content = re.sub(pattern, append_to_section, pin_content, flags=re.DOTALL)
    else:
        # Add new section at the end (before Related PINs if exists)
        new_section = f"\n---\n\n## {section}\n\n### Update ({today})\n\n{content}\n"

        if "## Related PINs" in pin_content:
            pin_content = pin_content.replace(
                "## Related PINs", f"{new_section}\n## Related PINs"
            )
        else:
            pin_content = pin_content.rstrip() + new_section

    # Write updated content
    with open(filepath, "w") as f:
        f.write(pin_content)

    # Update INDEX.md changelog only
    update_index_changelog(pin_num, title, section, today)

    print(f"✅ Updated PIN-{pin_num:03d}: {title}")
    print(f"   Added section: {section}")
    print(f"   File: {filepath}")

    return filepath


def update_index_changelog(pin_num: int, title: str, section: str, date: str):
    """Add changelog entry for PIN update."""

    with open(INDEX_PATH, "r") as f:
        content = f.read()

    # Update "Last Updated" line
    content = re.sub(
        r"\*\*Last Updated:\*\* [^\n]+",
        f"**Last Updated:** {date} (PIN-{pin_num:03d} {title} - {section})",
        content,
    )

    # Add changelog entry
    changelog_entry = f"| {date} | **PIN-{pin_num:03d} {title}** - Updated: {section} |"
    pattern = r"(\| Date \| Change \|\n\|------\|--------\|)\n"
    replacement = f"\\1\n{changelog_entry}\n"
    content = re.sub(pattern, replacement, content)

    with open(INDEX_PATH, "w") as f:
        f.write(content)

    print("   Updated INDEX.md changelog")


def create_pin(
    title: str,
    category: str,
    status: str = "COMPLETE",
    milestone: Optional[str] = None,
    summary: Optional[str] = None,
    content: Optional[str] = None,
    from_file: Optional[str] = None,
    related_pins: Optional[list] = None,
    commits: Optional[list] = None,
) -> tuple[int, Path]:
    """Create a new memory PIN and update INDEX.md."""

    pin_num = get_next_pin_number()
    today = datetime.now().strftime("%Y-%m-%d")

    # Sanitize title for filename
    safe_title = re.sub(r"[^a-zA-Z0-9\s-]", "", title.lower())
    safe_title = re.sub(r"\s+", "-", safe_title.strip())
    filename = f"PIN-{pin_num:03d}-{safe_title}.md"
    filepath = PINS_DIR / filename

    # Build PIN content
    if from_file:
        with open(from_file, "r") as f:
            pin_content = f.read()
        title_match = re.match(r"#\s+(.+)", pin_content)
        if title_match:
            title = title_match.group(1)
    else:
        status_emoji = (
            "✅"
            if status.upper() == "COMPLETE"
            else "🏗️"
            if "PROGRESS" in status.upper()
            else "📋"
        )

        pin_content = f"""# PIN-{pin_num:03d}: {title}

**Status:** {status_emoji} {status.upper()}
**Created:** {today}
**Category:** {category}
"""
        if milestone:
            pin_content += f"**Milestone:** {milestone}\n"

        pin_content += """
---

## Summary

"""
        pin_content += f"{summary}\n" if summary else "[Add summary here]\n"

        pin_content += """
---

## Details

"""
        pin_content += f"{content}\n" if content else "[Add details here]\n"

        if commits:
            pin_content += "\n---\n\n## Commits\n\n"
            for commit in commits:
                pin_content += f"- `{commit}`\n"

        if related_pins:
            pin_content += "\n---\n\n## Related PINs\n\n"
            for pin in related_pins:
                pin_content += f"- [PIN-{pin:03d}](PIN-{pin:03d}-.md)\n"

    with open(filepath, "w") as f:
        f.write(pin_content)

    update_index_new_pin(pin_num, filename, title, category, status, today)

    print(f"✅ Created PIN-{pin_num:03d}: {title}")
    print(f"   File: {filepath}")

    return pin_num, filepath


def update_index_new_pin(
    pin_num: int, filename: str, title: str, category: str, status: str, date: str
):
    """Update INDEX.md with a new PIN entry."""

    with open(INDEX_PATH, "r") as f:
        content = f.read()

    content = re.sub(
        r"\*\*Last Updated:\*\* [^\n]+",
        f"**Last Updated:** {date} (PIN-{pin_num:03d} {title})",
        content,
    )

    pattern = r"(\| \[PIN-\d+\]\([^)]+\) \|[^\n]+\|)\n(\n---\n\n## Vision Achievement Summary)"
    status_display = (
        f"**✅ {status.upper()}**"
        if status.upper() == "COMPLETE"
        else f"**🏗️ {status.upper()}**"
    )
    new_row = f"| [PIN-{pin_num:03d}]({filename}) | **{title}** | {category} | {status_display} | {date} |"
    replacement = f"\\1\n{new_row}\n\\2"
    content = re.sub(pattern, replacement, content)

    changelog_entry = (
        f"| {date} | **PIN-{pin_num:03d} {title}** - Created via memory_trail. |"
    )
    pattern = r"(\| Date \| Change \|\n\|------\|--------\|)\n"
    replacement = f"\\1\n{changelog_entry}\n"
    content = re.sub(pattern, replacement, content)

    with open(INDEX_PATH, "w") as f:
        f.write(content)

    print("   Updated INDEX.md")


def create_test_report(
    title: str,
    report_type: str,
    status: str,
    run_id: Optional[str] = None,
    tokens: Optional[int] = None,
    findings: Optional[str] = None,
    content: Optional[str] = None,
    gaps: Optional[list] = None,
) -> tuple[int, Path]:
    """Create a new test report and update REGISTER.md."""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    tr_num = get_next_report_number()
    today = datetime.now().strftime("%Y-%m-%d")

    safe_title = re.sub(r"[^a-zA-Z0-9\s-]", "", title.upper())
    safe_title = re.sub(r"\s+", "_", safe_title.strip())
    filename = f"TR-{tr_num:03d}_{safe_title}_{today}.md"
    filepath = REPORTS_DIR / filename

    status_display = {
        "PASS": "✅ **PASS**",
        "FAIL": "❌ **FAIL**",
        "FAILED": "❌ **FAIL**",
        "GAPS": "⚠️ **GAPS**",
    }.get(status.upper(), f"🔄 **{status.upper()}**")

    report_content = f"""# TR-{tr_num:03d}: {title}

**Date:** {today}
**Type:** {report_type}
**Status:** {status_display}
"""
    if run_id:
        report_content += f"**Run ID:** `{run_id}`\n"
    if tokens:
        report_content += f"**Tokens:** {tokens:,}\n"

    report_content += "\n---\n\n## Summary\n\n"
    report_content += f"{findings}\n" if findings else "[Add summary here]\n"

    if content:
        report_content += f"\n---\n\n## Details\n\n{content}\n"

    if gaps:
        report_content += "\n---\n\n## Gaps Identified\n\n| Gap ID | Description | Priority | Status |\n|--------|-------------|----------|--------|\n"
        for i, gap in enumerate(gaps, 1):
            report_content += f"| GAP-{i:03d} | {gap} | MEDIUM | OPEN |\n"

    report_content += f"\n---\n\n*Generated by memory_trail.py on {today}*\n"

    with open(filepath, "w") as f:
        f.write(report_content)

    update_register(
        tr_num, filename, title, report_type, status, run_id, tokens, findings, today
    )

    print(f"✅ Created TR-{tr_num:03d}: {title}")
    print(f"   File: {filepath}")

    return tr_num, filepath


def update_register(
    tr_num, filename, title, report_type, status, run_id, tokens, findings, date
):
    """Update REGISTER.md with the new test report entry."""
    if not REGISTER_PATH.exists():
        print("   Warning: REGISTER.md not found")
        return

    with open(REGISTER_PATH, "r") as f:
        content = f.read()

    content = re.sub(
        r"\*\*Last Updated:\*\* [^\n]+", f"**Last Updated:** {date}", content
    )
    content = re.sub(r"\*Last test run: [^\*]+\*", f"*Last test run: {date}*", content)

    status_display = {
        "PASS": "✅ **PASS**",
        "FAIL": "❌ **FAIL**",
        "GAPS": "⚠️ **GAPS**",
    }.get(status.upper(), f"🔄 **{status.upper()}**")
    run_id_display = f"`{run_id}`" if run_id else "N/A"
    tokens_display = f"{tokens:,}" if tokens else "N/A"
    findings_short = (
        (findings[:50] + "...")
        if findings and len(findings) > 50
        else (findings or "N/A")
    )

    new_row = f"| [TR-{tr_num:03d}]({filename}) | {date} | {title} | {report_type} | {status_display} | {run_id_display} | {tokens_display} | {findings_short} |"
    pattern = r"(\| \[TR-\d+\]\([^)]+\) \|[^\n]+\|)\n(\n---\n\n## Test Categories)"
    replacement = f"\\1\n{new_row}\n\\2"
    content = re.sub(pattern, replacement, content)

    changelog_entry = f"| {date} | Created TR-{tr_num:03d}: {title} | Claude |"
    pattern = r"(\| Date \| Action \| By \|\n\|------\|--------\|-----\|)\n"
    replacement = f"\\1\n{changelog_entry}\n"
    content = re.sub(pattern, replacement, content)

    with open(REGISTER_PATH, "w") as f:
        f.write(content)

    print("   Updated REGISTER.md")


def show_next():
    """Show next available PIN and TR numbers."""
    print(f"📌 Next PIN number: PIN-{get_next_pin_number():03d}")
    print(f"📋 Next Test Report: TR-{get_next_report_number():03d}")


def main():
    parser = argparse.ArgumentParser(
        description="Memory Trail - Create/Update PINs and Test Reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
WORKFLOW (Always follow this order):
  1. FIND first:  %(prog)s find "keyword"
  2. UPDATE if exists:  %(prog)s update PIN_NUM --section "Updates" --content "..."
  3. CREATE only if new topic:  %(prog)s pin --title "..." --category "..."

Examples:
  # Find existing PINs
  %(prog)s find "ops console"
  %(prog)s find 111

  # Update existing PIN (PREFERRED)
  %(prog)s update 111 --section "Changelog" --content "Added customers panel"

  # Create new PIN (only for NEW topics)
  %(prog)s pin -t "New Feature" -c "Category" --summary "Description"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Find subcommand
    find_parser = subparsers.add_parser(
        "find", help="Find existing PINs by number or keyword"
    )
    find_parser.add_argument("query", help="PIN number or search keyword")

    # Update subcommand
    update_parser = subparsers.add_parser(
        "update", help="Update existing PIN (PREFERRED)"
    )
    update_parser.add_argument("pin_num", type=int, help="PIN number to update")
    update_parser.add_argument(
        "--section",
        "-S",
        required=True,
        help="Section name (e.g., 'Changelog', 'Updates')",
    )
    update_parser.add_argument(
        "--content", "-C", required=True, help="Content to append"
    )
    update_parser.add_argument("--status", help="Update status (e.g., COMPLETE)")

    # PIN subcommand
    pin_parser = subparsers.add_parser(
        "pin", help="Create NEW PIN (use update for existing)"
    )
    pin_parser.add_argument("--title", "-t", required=True, help="PIN title")
    pin_parser.add_argument("--category", "-c", required=True, help="Category")
    pin_parser.add_argument("--status", "-s", default="COMPLETE", help="Status")
    pin_parser.add_argument("--milestone", "-m", help="Milestone")
    pin_parser.add_argument("--summary", help="Summary")
    pin_parser.add_argument("--content", help="Content")
    pin_parser.add_argument("--from-file", "-f", help="Read from file")
    pin_parser.add_argument("--related", nargs="+", type=int, help="Related PINs")
    pin_parser.add_argument("--commits", nargs="+", help="Commits")

    # Report subcommand
    report_parser = subparsers.add_parser("report", help="Create test report")
    report_parser.add_argument("--title", "-t", required=True, help="Title")
    report_parser.add_argument("--type", "-T", required=True, help="Type")
    report_parser.add_argument("--status", "-s", required=True, help="Status")
    report_parser.add_argument("--run-id", "-r", help="Run ID")
    report_parser.add_argument("--tokens", type=int, help="Tokens")
    report_parser.add_argument("--findings", "-F", help="Findings")
    report_parser.add_argument("--content", help="Content")
    report_parser.add_argument("--gaps", nargs="+", help="Gaps")

    # Next subcommand
    subparsers.add_parser("next", help="Show next available IDs")

    args = parser.parse_args()

    if args.command == "find":
        results = find_pin(args.query)
        if not results:
            print(f"❌ No PINs found matching '{args.query}'")
        else:
            print(f"📌 Found {len(results)} PIN(s):\n")
            for pin_num, title, filepath in results:
                print(f"   PIN-{pin_num:03d}: {title}")
                print(f"            {filepath.name}\n")
    elif args.command == "update":
        update_pin(args.pin_num, args.section, args.content, args.status)
    elif args.command == "pin":
        create_pin(
            args.title,
            args.category,
            args.status,
            args.milestone,
            args.summary,
            args.content,
            args.from_file,
            args.related,
            args.commits,
        )
    elif args.command == "report":
        create_test_report(
            args.title,
            args.type,
            args.status,
            args.run_id,
            args.tokens,
            args.findings,
            args.content,
            args.gaps,
        )
    elif args.command == "next":
        show_next()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
