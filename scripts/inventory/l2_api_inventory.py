#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Extract all L2 API routes from FastAPI codebase
# Authority: READ-ONLY (audit script)
# Reference: L1_L2_L8 Binding Audit

"""
L2 API Contract Inventory
Extracts FastAPI routes and maps them to files, HTTP verbs, and authority.
Produces authoritative list of L2 surface area.
"""

import pathlib
import re
import sys

API_ROOT = pathlib.Path("backend/app/api")

# Keywords that indicate mutation
MUTATION_KEYWORDS = [
    "create",
    "update",
    "delete",
    "add",
    "remove",
    "set",
    "write",
    "post",
    "put",
]
SYSTEM_KEYWORDS = ["system", "internal", "admin", "ops", "founder"]


def extract_semantic_header(file_path: pathlib.Path):
    """Extract semantic header info from file."""
    try:
        text = file_path.read_text(errors="ignore")
    except Exception:
        return {}

    header = {}
    lines = text.split("\n")[:20]  # Check first 20 lines

    for line in lines:
        if line.startswith("# Layer:"):
            header["layer"] = line.replace("# Layer:", "").strip()
        elif line.startswith("# Authority:"):
            header["authority"] = line.replace("# Authority:", "").strip()
        elif line.startswith("# Product:"):
            header["product"] = line.replace("# Product:", "").strip()
        elif line.startswith("# Role:"):
            header["role"] = line.replace("# Role:", "").strip()

    return header


def extract_routes(file_path: pathlib.Path):
    """Extract FastAPI route definitions using regex (more reliable than AST)."""
    try:
        text = file_path.read_text(errors="ignore")
    except Exception:
        return [], None

    routes = []
    router_prefix = ""

    # Extract router prefix
    prefix_match = re.search(r'prefix\s*=\s*["\']([^"\']+)["\']', text)
    if prefix_match:
        router_prefix = prefix_match.group(1)

    # Pattern: @router.method("path") or @router.method("/path", ...)
    route_pattern = re.compile(
        r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']*)["\']',
        re.IGNORECASE,
    )

    # Find function definitions after decorators
    lines = text.split("\n")
    for i, line in enumerate(lines):
        match = route_pattern.search(line)
        if match:
            method = match.group(1).upper()
            path = match.group(2)

            # Find the function name (next def or async def)
            func_name = "unknown"
            for j in range(i + 1, min(i + 10, len(lines))):
                func_match = re.search(r"(?:async\s+)?def\s+(\w+)", lines[j])
                if func_match:
                    func_name = func_match.group(1)
                    break

            # Determine if it mutates
            mutates = method in ("POST", "PUT", "DELETE", "PATCH")
            func_lower = func_name.lower()
            if any(kw in func_lower for kw in MUTATION_KEYWORDS):
                mutates = True

            # Determine authority level
            authority = "user"
            if any(kw in func_lower for kw in SYSTEM_KEYWORDS):
                authority = "system"
            if "founder" in func_lower:
                authority = "founder"

            full_path = (
                router_prefix + path if not path.startswith(router_prefix) else path
            )

            routes.append(
                {
                    "method": method,
                    "path": full_path,
                    "function": func_name,
                    "mutates": mutates,
                    "authority": authority,
                    "line": i + 1,
                }
            )

    return routes, router_prefix


def main():
    repo_root = pathlib.Path(__file__).parent.parent.parent
    api_root = repo_root / "backend" / "app" / "api"

    if not api_root.exists():
        print(f"Error: API root not found at {api_root}", file=sys.stderr)
        sys.exit(1)

    all_routes = []

    for f in sorted(api_root.glob("*.py")):
        if f.name.startswith("__"):
            continue

        header = extract_semantic_header(f)
        routes, prefix = extract_routes(f)

        for route in routes:
            route["file"] = f.name
            route["semantic_layer"] = header.get("layer", "MISSING")
            route["semantic_authority"] = header.get("authority", "MISSING")
            route["product"] = header.get("product", "UNKNOWN")
            all_routes.append(route)

    # Output markdown
    print("# L2 API Contract Inventory")
    print()
    print(f"**Total Routes:** {len(all_routes)}")
    print(f"**Files Scanned:** {len(list(api_root.glob('*.py')))}")
    print()

    # Group by domain (based on prefix)
    domains = {}
    for route in all_routes:
        # Extract domain from path
        parts = route["path"].strip("/").split("/")
        domain = parts[2] if len(parts) > 2 else parts[0] if parts else "root"
        domains.setdefault(domain, []).append(route)

    print("## Routes by Domain")
    print()

    for domain in sorted(domains.keys()):
        routes = domains[domain]
        print(f"### {domain.title()}")
        print()
        print("| Method | Route | Function | Mutates | Authority | File |")
        print("|--------|-------|----------|---------|-----------|------|")

        for r in sorted(routes, key=lambda x: (x["path"], x["method"])):
            mutates = "YES" if r["mutates"] else "NO"
            print(
                f"| {r['method']} | `{r['path']}` | `{r['function']}` | {mutates} | {r['authority']} | `{r['file']}` |"
            )

        print()

    # Summary statistics
    print("## Summary")
    print()
    print("### By HTTP Method")
    print()
    print("| Method | Count |")
    print("|--------|-------|")
    by_method = {}
    for r in all_routes:
        by_method[r["method"]] = by_method.get(r["method"], 0) + 1
    for m, c in sorted(by_method.items()):
        print(f"| {m} | {c} |")

    print()
    print("### Mutation Analysis")
    print()
    mutating = sum(1 for r in all_routes if r["mutates"])
    readonly = len(all_routes) - mutating
    print(f"- **Mutating Routes:** {mutating}")
    print(f"- **Read-Only Routes:** {readonly}")

    print()
    print("### Product-Safe Analysis")
    print()
    print("| Authority | Count | Product-Safe? |")
    print("|-----------|-------|---------------|")
    by_auth = {}
    for r in all_routes:
        by_auth[r["authority"]] = by_auth.get(r["authority"], 0) + 1
    for auth, count in sorted(by_auth.items()):
        safe = "YES" if auth == "user" else "MAYBE" if auth == "founder" else "NO"
        print(f"| {auth} | {count} | {safe} |")

    print()
    print("### Files with Missing Semantic Headers")
    print()
    missing = set()
    for r in all_routes:
        if r["semantic_layer"] == "MISSING":
            missing.add(r["file"])

    if missing:
        print("| File |")
        print("|------|")
        for f in sorted(missing):
            print(f"| `{f}` |")
    else:
        print("All files have semantic headers.")


if __name__ == "__main__":
    main()
