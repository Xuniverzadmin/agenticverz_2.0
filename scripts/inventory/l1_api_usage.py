#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Find API calls referenced in frontend code (L1)
# Authority: READ-ONLY (audit script)
# Reference: L1_L2_L8 Binding Audit

"""
L1 → L2 Usage Mapping
Finds API calls referenced in frontend code.
Exposes: missing bindings, hardcoded assumptions, dead UI paths.
"""

import pathlib
import re

# Frontend roots to scan
FRONTEND_ROOTS = [
    "website",
    "frontend",
    "aos-console",
]

# Patterns to match API calls
API_PATTERNS = [
    re.compile(r'["\'](/api/v\d+/[a-zA-Z0-9_/\-\{\}]+)["\']'),
    re.compile(r'["\'](/api/[a-zA-Z0-9_/\-\{\}]+)["\']'),
    re.compile(r'fetch\(["\']([^"\']+)["\']'),
    re.compile(r'axios\.[a-z]+\(["\']([^"\']+)["\']'),
    re.compile(r'apiClient\.[a-z]+\(["\']([^"\']+)["\']'),
]

# Also look for hardcoded assumptions
ASSUMPTION_PATTERNS = [
    (re.compile(r"localhost:\d+"), "hardcoded_localhost"),
    (re.compile(r"127\.0\.0\.1:\d+"), "hardcoded_ip"),
    (re.compile(r'http://[^"\'\s]+'), "hardcoded_http"),
    (re.compile(r"assumes?\s+sync", re.I), "assumes_sync"),
    (re.compile(r"assumes?\s+real[\-\s]?time", re.I), "assumes_realtime"),
]


def scan_file(path: pathlib.Path):
    """Scan a frontend file for API references."""
    try:
        text = path.read_text(errors="ignore")
    except Exception:
        return [], []

    apis = []
    assumptions = []

    for pattern in API_PATTERNS:
        for match in pattern.finditer(text):
            api_path = match.group(1) if match.lastindex else match.group(0)
            # Normalize
            if api_path.startswith("/"):
                line_num = text[: match.start()].count("\n") + 1
                apis.append(
                    {
                        "api": api_path,
                        "file": str(path),
                        "line": line_num,
                    }
                )

    for pattern, assumption_type in ASSUMPTION_PATTERNS:
        for match in pattern.finditer(text):
            line_num = text[: match.start()].count("\n") + 1
            assumptions.append(
                {
                    "type": assumption_type,
                    "match": match.group(0)[:50],  # Truncate
                    "file": str(path),
                    "line": line_num,
                }
            )

    return apis, assumptions


def main():
    repo_root = pathlib.Path(__file__).parent.parent.parent

    all_apis = {}  # api -> set of files
    all_assumptions = []
    files_scanned = 0

    for root_name in FRONTEND_ROOTS:
        root_path = repo_root / root_name
        if not root_path.exists():
            continue

        # Scan JS/TS files
        for ext in ["*.js", "*.jsx", "*.ts", "*.tsx", "*.vue", "*.svelte"]:
            for path in root_path.rglob(ext):
                # Skip node_modules
                if "node_modules" in str(path):
                    continue

                files_scanned += 1
                apis, assumptions = scan_file(path)

                for api in apis:
                    rel_path = str(path.relative_to(repo_root))
                    api["file"] = rel_path
                    key = api["api"]
                    if key not in all_apis:
                        all_apis[key] = []
                    all_apis[key].append(api)

                for assumption in assumptions:
                    assumption["file"] = str(path.relative_to(repo_root))
                    all_assumptions.append(assumption)

    # Output markdown
    print("# L1 → L2 API Usage Mapping")
    print()
    print(f"**Files Scanned:** {files_scanned}")
    print(f"**Unique API Paths Found:** {len(all_apis)}")
    print()

    print("## API References Found")
    print()
    print("| API Path | Used In | Count |")
    print("|----------|---------|-------|")

    for api in sorted(all_apis.keys()):
        refs = all_apis[api]
        files = sorted(set(r["file"] for r in refs))
        files_str = ", ".join(f"`{f}`" for f in files[:3])
        if len(files) > 3:
            files_str += f" (+{len(files) - 3} more)"
        print(f"| `{api}` | {files_str} | {len(refs)} |")

    print()

    # Group by domain
    print("## By Domain")
    print()

    domains = {}
    for api in all_apis.keys():
        parts = api.strip("/").split("/")
        # Get domain (usually the third part after api/v1/)
        domain = parts[2] if len(parts) > 2 else "root"
        domains.setdefault(domain, []).append(api)

    print("| Domain | API Count |")
    print("|--------|-----------|")
    for domain in sorted(domains.keys()):
        print(f"| {domain} | {len(domains[domain])} |")

    print()

    # Assumptions found
    if all_assumptions:
        print("## Hardcoded Assumptions Found")
        print()
        print("These may indicate UI assumptions that don't match platform truth.")
        print()
        print("| Type | Match | File | Line |")
        print("|------|-------|------|------|")

        for a in sorted(all_assumptions, key=lambda x: (x["type"], x["file"])):
            print(f"| {a['type']} | `{a['match']}` | `{a['file']}` | {a['line']} |")
    else:
        print("## Hardcoded Assumptions")
        print()
        print("No hardcoded assumptions detected.")

    print()
    print("---")
    print()
    print("## Notes")
    print()
    print("- APIs with `{param}` are dynamic paths")
    print("- Count > 1 indicates the API is used in multiple places")
    print("- Cross-reference with L2 inventory to find missing bindings")


if __name__ == "__main__":
    main()
