#!/usr/bin/env python3
"""
HOC Phase 0 — Migration Manifest Generator

Parses V3_MANUAL_AUDIT_WORKBOOK.md for all ⚠️ (MISPLACED) entries,
resolves filesystem paths, computes SHA-256 hashes, detects collisions,
and produces:
  - MIGRATION_MANIFEST.csv  (one row per misplaced file)
  - MIGRATION_SUMMARY.md    (stats + domain breakdown)

Reference: PIN-470, Phase 0
Artifact Class: CODE
Layer: OPS
Audience: INTERNAL

Usage:
    python3 scripts/ops/hoc_phase0_manifest_generator.py
"""

import csv
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_HOC_CUS = REPO_ROOT / "backend" / "app" / "hoc" / "cus"
DOMAIN_MAP_DIR = BACKEND_HOC_CUS / "_domain_map"
WORKBOOK_PATH = DOMAIN_MAP_DIR / "V3_MANUAL_AUDIT_WORKBOOK.md"
MANIFEST_PATH = DOMAIN_MAP_DIR / "MIGRATION_MANIFEST.csv"
SUMMARY_PATH = DOMAIN_MAP_DIR / "MIGRATION_SUMMARY.md"

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@dataclass
class MigrationEntry:
    migration_id: str
    filename: str           # relative path from workbook header, e.g. "activity/L6_drivers/threshold_driver.py"
    current_domain: str
    current_layer: str
    target_domain: str
    target_layer: str       # same as current_layer unless overridden
    reason: str
    current_path: str = ""  # resolved absolute path
    target_path: str = ""   # computed absolute target path
    status: str = "PENDING"
    hash_source: str = ""
    hash_target: str = ""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_workbook(path: Path) -> List[MigrationEntry]:
    """Parse the workbook and return all MISPLACED entries."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    entries: List[MigrationEntry] = []
    seq = 0

    # We walk lines looking for ### headers, then collect attributes + decision
    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect entry header: ### [x] `some/path.py` or ### [~] `some/path.py`
        header_match = re.match(r'^### \[[x~]\] `(.+?)`', line)
        if not header_match:
            i += 1
            continue

        filename = header_match.group(1)

        # Scan forward for attributes and decision within this entry (until next --- or ### or EOF)
        current_domain = ""
        layer = ""
        reason = ""
        target_domain = ""
        is_misplaced = False
        j = i + 1

        while j < len(lines):
            ln = lines[j]

            # Stop at next entry or section separator
            if ln.startswith("### [") or (ln.strip() == "---" and j > i + 2):
                break

            # ---- Format A: Markdown table ----
            # | **Current Domain** | activity |
            td_match = re.match(r'^\| \*\*Current Domain\*\* \| (.+?) \|', ln)
            if td_match:
                current_domain = td_match.group(1).strip()

            layer_match = re.match(r'^\| \*\*Layer\*\* \| (.+?) \|', ln)
            if layer_match:
                layer = layer_match.group(1).strip()

            # **DECISION:** `target` ⚠️ (MISPLACED)
            dec_match = re.match(r'^\*\*DECISION:\*\* `(.+?)`.*⚠️ \(MISPLACED\)', ln)
            if dec_match:
                target_domain = dec_match.group(1).strip()
                is_misplaced = True

            # **Reason:** ...
            reason_match = re.match(r'^\*\*Reason:\*\* (.+)', ln)
            if reason_match:
                reason = reason_match.group(1).strip()

            # ---- Format B: Code-block style ----
            # Attribute: Current Domain  /  Value: policies
            if ln.strip().startswith("Attribute: Current Domain"):
                if j + 1 < len(lines):
                    val_match = re.match(r'^Value: (.+)', lines[j + 1].strip())
                    if val_match:
                        current_domain = val_match.group(1).strip()

            if ln.strip().startswith("Attribute: Layer"):
                if j + 1 < len(lines):
                    val_match = re.match(r'^Value: (.+)', lines[j + 1].strip())
                    if val_match:
                        layer = val_match.group(1).strip()

            # ASSIGN TO: controls ⚠️ (MISPLACED)
            assign_match = re.match(r'^ASSIGN TO: (.+?) ⚠️ \(MISPLACED\)', ln)
            if assign_match:
                target_domain = assign_match.group(1).strip()
                is_misplaced = True

            # Reason: ... (format B, no bold)
            if ln.strip().startswith("Reason:") and not ln.strip().startswith("**Reason"):
                reason = ln.strip()[len("Reason:"):].strip()

            j += 1

        if is_misplaced:
            seq += 1
            entry = MigrationEntry(
                migration_id=f"M{seq:03d}",
                filename=filename,
                current_domain=current_domain,
                current_layer=layer,
                target_domain=target_domain,
                target_layer=layer,  # default: same layer
                reason=reason,
            )
            entries.append(entry)

        i = j if j > i + 1 else i + 1

    return entries


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def normalize_layer_dir(layer_str: str) -> Optional[str]:
    """Extract layer directory name from layer string like 'L5 — Domain Engine' or 'L6 — Domain Driver'."""
    m = re.match(r'(L\d+)', layer_str)
    if not m:
        return None
    return m.group(1)


def resolve_source_path(entry: MigrationEntry) -> Optional[Path]:
    """Resolve the filename from the workbook to an actual filesystem path."""
    # The filename in the workbook is relative to backend/app/hoc/cus/
    candidate = BACKEND_HOC_CUS / entry.filename
    if candidate.exists():
        return candidate

    # Try glob search as fallback
    name = Path(entry.filename).name
    matches = list(BACKEND_HOC_CUS.rglob(name))
    if len(matches) == 1:
        return matches[0]

    # Try matching domain + filename within domain
    parts = Path(entry.filename).parts
    if len(parts) >= 2:
        domain = parts[0]
        fname = parts[-1]
        domain_matches = list((BACKEND_HOC_CUS / domain).rglob(fname))
        if len(domain_matches) == 1:
            return domain_matches[0]

    return None


def compute_target_path(entry: MigrationEntry, source_path: Path) -> Path:
    """Compute the target path by changing domain but preserving layer structure."""
    # Get relative path from HOC_CUS root
    rel = source_path.relative_to(BACKEND_HOC_CUS)
    parts = list(rel.parts)

    # parts[0] is current domain, rest is subdirectory + filename
    # Replace domain with target domain
    target_domain = entry.target_domain

    # Handle special target_domain with path override, e.g. "general/L5_engines/lifecycle/"
    if "/" in target_domain:
        # Full target path specified
        target_rel = Path(target_domain) / parts[-1]
        return BACKEND_HOC_CUS / target_rel

    # Standard case: swap domain, keep everything else
    parts[0] = target_domain
    return BACKEND_HOC_CUS / Path(*parts)


# ---------------------------------------------------------------------------
# Collision detection
# ---------------------------------------------------------------------------

def detect_collision(source_path: Path, target_path: Path) -> tuple:
    """Returns (status, hash_source, hash_target)."""
    hash_source = sha256_file(source_path)

    if not target_path.exists():
        return ("PENDING", hash_source, "")

    hash_target = sha256_file(target_path)
    if hash_source == hash_target:
        return ("REPLACE_IDENTICAL", hash_source, hash_target)
    else:
        return ("CONFLICT", hash_source, hash_target)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

CSV_FIELDS = [
    "migration_id", "current_path", "current_domain", "current_layer",
    "target_domain", "target_layer", "target_path", "reason",
    "status", "hash_source", "hash_target",
]


def write_manifest(entries: List[MigrationEntry]):
    DOMAIN_MAP_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for e in entries:
            writer.writerow({
                "migration_id": e.migration_id,
                "current_path": e.current_path,
                "current_domain": e.current_domain,
                "current_layer": e.current_layer,
                "target_domain": e.target_domain,
                "target_layer": e.target_layer,
                "target_path": e.target_path,
                "reason": e.reason,
                "status": e.status,
                "hash_source": e.hash_source,
                "hash_target": e.hash_target,
            })
    print(f"  Manifest: {MANIFEST_PATH}")


def write_summary(entries: List[MigrationEntry]):
    total = len(entries)
    pending = sum(1 for e in entries if e.status == "PENDING")
    identical = sum(1 for e in entries if e.status == "REPLACE_IDENTICAL")
    conflict = sum(1 for e in entries if e.status == "CONFLICT")
    unresolved = sum(1 for e in entries if e.status == "UNRESOLVED")

    # Domain breakdown: source → target
    from_domains: dict = {}
    to_domains: dict = {}
    for e in entries:
        from_domains[e.current_domain] = from_domains.get(e.current_domain, 0) + 1
        td = e.target_domain.split("/")[0]  # normalize path-style targets
        to_domains[td] = to_domains.get(td, 0) + 1

    lines = [
        "# Migration Manifest Summary",
        "",
        f"**Generated by:** `hoc_phase0_manifest_generator.py`",
        f"**Source:** `V3_MANUAL_AUDIT_WORKBOOK.md`",
        f"**Total entries:** {total}",
        "",
        "## Collision Report",
        "",
        f"| Status | Count |",
        f"|--------|-------|",
        f"| PENDING (clean move) | {pending} |",
        f"| REPLACE_IDENTICAL | {identical} |",
        f"| CONFLICT | {conflict} |",
        f"| UNRESOLVED (source not found) | {unresolved} |",
        "",
        "## Source Domain Breakdown (moving FROM)",
        "",
        "| Domain | Files |",
        "|--------|-------|",
    ]
    for d in sorted(from_domains.keys()):
        lines.append(f"| {d} | {from_domains[d]} |")

    lines += [
        "",
        "## Target Domain Breakdown (moving TO)",
        "",
        "| Domain | Files |",
        "|--------|-------|",
    ]
    for d in sorted(to_domains.keys()):
        lines.append(f"| {d} | {to_domains[d]} |")

    if conflict > 0:
        lines += [
            "",
            "## CONFLICT Entries (require manual decision)",
            "",
            "| ID | Source | Target |",
            "|----|--------|--------|",
        ]
        for e in entries:
            if e.status == "CONFLICT":
                lines.append(f"| {e.migration_id} | `{e.current_path}` | `{e.target_path}` |")

    if unresolved > 0:
        lines += [
            "",
            "## UNRESOLVED Entries (source file not found)",
            "",
            "| ID | Filename | Current Domain |",
            "|----|----------|----------------|",
        ]
        for e in entries:
            if e.status == "UNRESOLVED":
                lines.append(f"| {e.migration_id} | `{e.filename}` | {e.current_domain} |")

    lines.append("")
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"  Summary:  {SUMMARY_PATH}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("HOC Phase 0 — Migration Manifest Generator")
    print("=" * 60)

    if not WORKBOOK_PATH.exists():
        print(f"ERROR: Workbook not found: {WORKBOOK_PATH}")
        sys.exit(1)

    # 1. Parse
    print(f"\n[1/5] Parsing workbook...")
    entries = parse_workbook(WORKBOOK_PATH)
    print(f"  Found {len(entries)} MISPLACED entries")

    # 2. Validate unique IDs
    print(f"\n[2/5] Validating migration IDs...")
    ids = [e.migration_id for e in entries]
    if len(ids) != len(set(ids)):
        print("ERROR: Duplicate migration IDs detected!")
        sys.exit(1)
    print(f"  All {len(ids)} IDs unique ✓")

    # 3. Resolve paths + hash + collision
    print(f"\n[3/5] Resolving paths and computing hashes...")
    missing = 0
    for e in entries:
        source = resolve_source_path(e)
        if source is None:
            print(f"  WARNING: Cannot resolve source for {e.filename} (domain: {e.current_domain})")
            e.status = "UNRESOLVED"
            e.current_path = f"UNRESOLVED:{e.filename}"
            e.target_path = ""
            missing += 1
            continue

        e.current_path = str(source.relative_to(REPO_ROOT))
        target = compute_target_path(e, source)
        e.target_path = str(target.relative_to(REPO_ROOT))

        status, h_src, h_tgt = detect_collision(source, target)
        e.status = status
        e.hash_source = h_src
        e.hash_target = h_tgt

    resolved = len(entries) - missing
    print(f"  Resolved: {resolved}/{len(entries)}")
    if missing:
        print(f"  Missing:  {missing}")

    # 4. Summary stats
    print(f"\n[4/5] Collision summary:")
    for st in ["PENDING", "REPLACE_IDENTICAL", "CONFLICT", "UNRESOLVED"]:
        count = sum(1 for e in entries if e.status == st)
        if count:
            print(f"  {st}: {count}")

    # 5. Write outputs
    print(f"\n[5/5] Writing outputs...")
    write_manifest(entries)
    write_summary(entries)

    print(f"\nDone. {len(entries)} entries processed.")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
