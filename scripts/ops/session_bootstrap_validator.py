#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Session Bootstrap Validator (SPB)
# artifact_class: CODE
"""
Session Bootstrap Validator (SPB)

Enforces BL-BOOT-001: Session Playbook Bootstrap

Purpose:
  - Validate that Claude's first response contains SESSION_BOOTSTRAP_CONFIRMATION
  - Verify all mandatory documents from SESSION_PLAYBOOK.yaml are listed
  - Block any work before bootstrap is complete

Rule: Memory decays. Contracts don't.
      Sessions must boot like systems, not humans.

Usage:
    python scripts/ops/session_bootstrap_validator.py --response <file>
    python scripts/ops/session_bootstrap_validator.py --check-playbook
    python scripts/ops/session_bootstrap_validator.py --generate-template

Reference: BL-BOOT-001 behavior rule
Created: 2025-12-27
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

# Paths
PLAYBOOK_FILE = (
    Path(__file__).parent.parent.parent / "docs/playbooks/SESSION_PLAYBOOK.yaml"
)


def load_playbook():
    """Load the session playbook."""
    if not PLAYBOOK_FILE.exists():
        print(f"ERROR: Playbook not found: {PLAYBOOK_FILE}")
        sys.exit(1)

    with open(PLAYBOOK_FILE) as f:
        return yaml.safe_load(f)


def get_required_documents(playbook: dict) -> list[str]:
    """Extract required document names from playbook."""
    mandatory = playbook.get("mandatory_load", [])
    documents = []

    for item in mandatory:
        if isinstance(item, dict):
            path = item.get("path", "")
            # Extract just the filename
            filename = Path(path).name
            documents.append(filename)
        else:
            # Plain string path
            documents.append(Path(item).name)

    return documents


def extract_bootstrap_section(response_text: str) -> dict | None:
    """
    Extract SESSION_BOOTSTRAP_CONFIRMATION section from response.

    Returns parsed dict or None if not found.
    """
    # Look for the section
    pattern = r"SESSION_BOOTSTRAP_CONFIRMATION\s*\n([\s\S]*?)(?:\n\n|\Z)"
    match = re.search(pattern, response_text)

    if not match:
        return None

    section_text = match.group(1)
    result = {
        "playbook_version": None,
        "loaded_documents": [],
        "restrictions_acknowledged": False,
        "current_phase": None,
    }

    # Parse playbook_version
    version_match = re.search(r"playbook_version:\s*([0-9.]+)", section_text)
    if version_match:
        result["playbook_version"] = version_match.group(1)

    # Parse loaded_documents (indented list)
    docs_pattern = r"loaded_documents:\s*\n((?:\s+-\s+.+\n)+)"
    docs_match = re.search(docs_pattern, section_text)
    if docs_match:
        docs_text = docs_match.group(1)
        result["loaded_documents"] = [
            line.strip().lstrip("- ").strip()
            for line in docs_text.strip().split("\n")
            if line.strip().startswith("-")
        ]

    # Parse restrictions_acknowledged
    restrictions_match = re.search(
        r"restrictions_acknowledged:\s*(YES|NO)", section_text, re.IGNORECASE
    )
    if restrictions_match:
        result["restrictions_acknowledged"] = (
            restrictions_match.group(1).upper() == "YES"
        )

    # Parse current_phase
    phase_match = re.search(
        r"current_phase:\s*([A-Z0-9.]+)", section_text, re.IGNORECASE
    )
    if phase_match:
        result["current_phase"] = phase_match.group(1).upper()

    return result


def validate_bootstrap(response_text: str, playbook: dict) -> dict:
    """
    Validate bootstrap confirmation against playbook.

    Returns:
        {
            "valid": bool,
            "issues": list of issues,
            "bootstrap": parsed bootstrap section or None
        }
    """
    result = {
        "valid": True,
        "issues": [],
        "bootstrap": None,
    }

    # Extract bootstrap section
    bootstrap = extract_bootstrap_section(response_text)

    if bootstrap is None:
        result["valid"] = False
        result["issues"].append("SESSION_BOOTSTRAP_CONFIRMATION section not found")
        return result

    result["bootstrap"] = bootstrap

    # Get required documents from playbook
    required_docs = get_required_documents(playbook)
    playbook_version = playbook.get("session_playbook_version", "1.0")

    # Check playbook version
    if bootstrap["playbook_version"] != playbook_version:
        result["valid"] = False
        result["issues"].append(
            f"Version mismatch: expected {playbook_version}, got {bootstrap['playbook_version']}"
        )

    # Check all required documents are listed
    loaded_docs = set(bootstrap["loaded_documents"])
    required_set = set(required_docs)

    missing = required_set - loaded_docs
    if missing:
        result["valid"] = False
        result["issues"].append(f"Missing documents: {sorted(missing)}")

    # Check restrictions acknowledged
    if not bootstrap["restrictions_acknowledged"]:
        result["valid"] = False
        result["issues"].append("restrictions_acknowledged must be YES")

    # Check phase is declared
    if not bootstrap["current_phase"]:
        result["valid"] = False
        result["issues"].append("current_phase not declared")

    return result


def print_validation_result(result: dict, verbose: bool = False):
    """Print validation results."""
    print("=" * 60)
    print("SESSION BOOTSTRAP VALIDATION")
    print("=" * 60)
    print()

    if result["valid"]:
        print("✓ BOOTSTRAP VALID")
        print()
        if result["bootstrap"]:
            print(f"  Version: {result['bootstrap']['playbook_version']}")
            print(f"  Documents: {len(result['bootstrap']['loaded_documents'])} loaded")
            print(f"  Phase: {result['bootstrap']['current_phase']}")
    else:
        print("✗ BOOTSTRAP INVALID")
        print()
        print("Issues:")
        for issue in result["issues"]:
            print(f"  - {issue}")
        print()
        print("-" * 60)
        print("BL-BOOT-001 VIOLATION: Session bootstrap required.")
        print()
        print("Your first response must be SESSION_BOOTSTRAP_CONFIRMATION.")
        print("No work is allowed until bootstrap is complete.")
        print()
        print("Memory decays. Contracts don't.")
        print("Sessions must boot like systems, not humans.")

    if verbose and result["bootstrap"]:
        print()
        print("-" * 60)
        print("Loaded Documents:")
        for doc in result["bootstrap"]["loaded_documents"]:
            print(f"  - {doc}")

    return 0 if result["valid"] else 1


def generate_template(playbook: dict):
    """Generate the bootstrap confirmation template."""
    required_docs = get_required_documents(playbook)
    version = playbook.get("session_playbook_version", "1.0")

    template = f"""SESSION_BOOTSTRAP_CONFIRMATION
- playbook_version: {version}
- loaded_documents:
"""
    for doc in required_docs:
        template += f"  - {doc}\n"

    template += """- restrictions_acknowledged: YES
- current_phase: B
"""

    print("=" * 60)
    print("SESSION BOOTSTRAP TEMPLATE")
    print("=" * 60)
    print()
    print("Copy this as your first response:")
    print()
    print(template)
    return 0


def check_playbook(playbook: dict):
    """Check playbook structure and list required documents."""
    print("=" * 60)
    print("SESSION PLAYBOOK CHECK")
    print("=" * 60)
    print()

    version = playbook.get("session_playbook_version", "MISSING")
    print(f"Version: {version}")
    print()

    required_docs = get_required_documents(playbook)
    print(f"Mandatory Documents ({len(required_docs)}):")
    for doc in required_docs:
        print(f"  - {doc}")

    print()
    forbidden = playbook.get("forbidden_if_not_loaded", [])
    print(f"Forbidden Actions ({len(forbidden)}):")
    for item in forbidden:
        if isinstance(item, dict):
            print(f"  - {item.get('action', 'unknown')}: {item.get('reason', '')}")
        else:
            print(f"  - {item}")

    print()
    print("✓ Playbook structure valid")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Validate session bootstrap confirmation"
    )
    parser.add_argument(
        "--response",
        type=str,
        help="Path to file containing Claude's response to validate",
    )
    parser.add_argument(
        "--text",
        type=str,
        help="Direct text to validate (alternative to --response)",
    )
    parser.add_argument(
        "--check-playbook",
        action="store_true",
        help="Check playbook structure and list requirements",
    )
    parser.add_argument(
        "--generate-template",
        action="store_true",
        help="Generate bootstrap confirmation template",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    playbook = load_playbook()

    if args.check_playbook:
        return check_playbook(playbook)

    if args.generate_template:
        return generate_template(playbook)

    if args.response:
        with open(args.response) as f:
            response_text = f.read()
    elif args.text:
        response_text = args.text
    else:
        # Read from stdin
        print("Enter response text (Ctrl+D to end):")
        response_text = sys.stdin.read()

    result = validate_bootstrap(response_text, playbook)
    return print_validation_result(result, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
