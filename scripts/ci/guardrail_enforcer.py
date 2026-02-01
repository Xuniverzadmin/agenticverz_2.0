#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: CI
#   Execution: sync
# Role: GUARDRAIL ENFORCER - Governance enforcement with bypass accountability.
# artifact_class: CODE
"""
GUARDRAIL ENFORCER - Governance enforcement with bypass accountability.

This creates multiple layers of enforcement:
1. Pre-commit: Block commits with violations
2. Pre-push: Block pushes if guardrails were bypassed
3. Bypass ledger: Audit trail of all bypasses
4. Bypass requires explicit authorization code

Usage:
    python guardrail_enforcer.py --install    # Install all hooks
    python guardrail_enforcer.py --status     # Show enforcement status
    python guardrail_enforcer.py --bypasses   # Show bypass ledger
    python guardrail_enforcer.py --authorize  # Generate bypass code (admin only)
"""

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List

# Paths
REPO_ROOT = Path(__file__).parent.parent.parent
BYPASS_LEDGER = REPO_ROOT / ".governance" / "bypass_ledger.json"
BYPASS_CODES = REPO_ROOT / ".governance" / "bypass_codes.json"
ENFORCEMENT_STATUS = REPO_ROOT / ".governance" / "enforcement_status.json"

# Bypass code validity
BYPASS_CODE_VALIDITY_HOURS = 4


def ensure_governance_dir():
    """Ensure .governance directory exists."""
    gov_dir = REPO_ROOT / ".governance"
    gov_dir.mkdir(exist_ok=True)

    # Add to .gitignore if not already
    gitignore = REPO_ROOT / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if ".governance/" not in content:
            with open(gitignore, "a") as f:
                f.write("\n# Governance enforcement (local only)\n.governance/\n")


def load_json(path: Path) -> dict:
    """Load JSON file or return empty dict."""
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_json(path: Path, data: dict):
    """Save JSON file."""
    ensure_governance_dir()
    path.write_text(json.dumps(data, indent=2, default=str))


def generate_bypass_code(reason: str, author: str) -> str:
    """Generate a time-limited bypass authorization code."""
    timestamp = datetime.now().isoformat()
    expires = (datetime.now() + timedelta(hours=BYPASS_CODE_VALIDITY_HOURS)).isoformat()

    # Create hash-based code
    raw = f"{timestamp}:{author}:{reason}:{os.urandom(8).hex()}"
    code = hashlib.sha256(raw.encode()).hexdigest()[:12].upper()

    # Store the code
    codes = load_json(BYPASS_CODES)
    codes[code] = {
        "created": timestamp,
        "expires": expires,
        "author": author,
        "reason": reason,
        "used": False
    }
    save_json(BYPASS_CODES, codes)

    return code


def validate_bypass_code(code: str) -> tuple:
    """Validate a bypass code. Returns (valid, reason)."""
    codes = load_json(BYPASS_CODES)

    if code not in codes:
        return False, "Invalid bypass code"

    code_info = codes[code]

    # Check expiry
    expires = datetime.fromisoformat(code_info["expires"])
    if datetime.now() > expires:
        return False, f"Bypass code expired at {expires}"

    # Check if already used
    if code_info.get("used"):
        return False, "Bypass code already used"

    return True, code_info["reason"]


def mark_code_used(code: str, commit_hash: str):
    """Mark a bypass code as used."""
    codes = load_json(BYPASS_CODES)
    if code in codes:
        codes[code]["used"] = True
        codes[code]["used_at"] = datetime.now().isoformat()
        codes[code]["commit"] = commit_hash
        save_json(BYPASS_CODES, codes)


def record_bypass(commit_hash: str, author: str, reason: str, code: Optional[str] = None):
    """Record a bypass in the ledger."""
    ledger = load_json(BYPASS_LEDGER)

    if "bypasses" not in ledger:
        ledger["bypasses"] = []

    ledger["bypasses"].append({
        "timestamp": datetime.now().isoformat(),
        "commit": commit_hash,
        "author": author,
        "reason": reason,
        "authorized_code": code,
        "authorized": code is not None
    })

    save_json(BYPASS_LEDGER, ledger)


def get_last_commit_info() -> tuple:
    """Get info about the last commit."""
    try:
        hash_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True
        )
        author_result = subprocess.run(
            ["git", "log", "-1", "--format=%an <%ae>"],
            capture_output=True, text=True
        )
        return hash_result.stdout.strip(), author_result.stdout.strip()
    except:
        return "unknown", "unknown"


def check_unpushed_bypasses() -> List[Dict]:
    """Check for unpushed commits that bypassed guardrails."""
    ledger = load_json(BYPASS_LEDGER)
    bypasses = ledger.get("bypasses", [])

    # Get list of unpushed commits
    try:
        result = subprocess.run(
            ["git", "log", "--format=%H", "@{u}..HEAD"],
            capture_output=True, text=True
        )
        unpushed = set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
    except:
        unpushed = set()

    # Find bypasses in unpushed commits
    unauthorized = []
    for bypass in bypasses:
        if bypass["commit"] in unpushed and not bypass.get("authorized"):
            unauthorized.append(bypass)

    return unauthorized


# ============================================================
# HOOK SCRIPTS
# ============================================================

PRE_COMMIT_HOOK = '''#!/bin/bash
# Guardrail Enforcer - Pre-commit Hook
# DO NOT EDIT - Managed by guardrail_enforcer.py

SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)/scripts/ci"

# Run guardrail checks
python3 "$SCRIPT_DIR/guardrail_precommit.py"
RESULT=$?

if [ $RESULT -ne 0 ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  ⛔ COMMIT BLOCKED BY GOVERNANCE                         ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  Fix violations before committing.                       ║"
    echo "║                                                          ║"
    echo "║  To request bypass authorization:                        ║"
    echo "║    python scripts/ci/guardrail_enforcer.py --authorize   ║"
    echo "║                                                          ║"
    echo "║  Then commit with:                                       ║"
    echo "║    BYPASS_CODE=XXXX git commit -m \"message\"              ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    exit 1
fi

exit 0
'''

PRE_COMMIT_HOOK_WITH_BYPASS = '''#!/bin/bash
# Guardrail Enforcer - Pre-commit Hook with Bypass Support
# DO NOT EDIT - Managed by guardrail_enforcer.py

SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)/scripts/ci"

# Check for bypass code
if [ -n "$BYPASS_CODE" ]; then
    # Validate bypass code
    python3 "$SCRIPT_DIR/guardrail_enforcer.py" --validate-bypass "$BYPASS_CODE"
    if [ $? -eq 0 ]; then
        echo "✅ Bypass authorized with code: $BYPASS_CODE"
        # Record will be created in post-commit
        export GUARDRAIL_BYPASS_AUTHORIZED="$BYPASS_CODE"
        exit 0
    else
        echo "❌ Invalid or expired bypass code"
        exit 1
    fi
fi

# Run guardrail checks
python3 "$SCRIPT_DIR/guardrail_precommit.py"
RESULT=$?

if [ $RESULT -ne 0 ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  ⛔ COMMIT BLOCKED BY GOVERNANCE                         ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  Fix violations before committing.                       ║"
    echo "║                                                          ║"
    echo "║  Emergency bypass (requires authorization):              ║"
    echo "║    1. python scripts/ci/guardrail_enforcer.py --authorize║"
    echo "║    2. BYPASS_CODE=XXXX git commit -m \"message\"           ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    exit 1
fi

exit 0
'''

POST_COMMIT_HOOK = '''#!/bin/bash
# Guardrail Enforcer - Post-commit Hook
# Records bypass usage after successful commit

SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)/scripts/ci"

if [ -n "$GUARDRAIL_BYPASS_AUTHORIZED" ]; then
    COMMIT_HASH=$(git rev-parse HEAD)
    python3 "$SCRIPT_DIR/guardrail_enforcer.py" --record-bypass "$GUARDRAIL_BYPASS_AUTHORIZED" "$COMMIT_HASH"
fi
'''

PRE_PUSH_HOOK = '''#!/bin/bash
# Guardrail Enforcer - Pre-push Hook
# Blocks push if unauthorized bypasses exist

SCRIPT_DIR="$(cd "$(dirname "$0")/../.." && pwd)/scripts/ci"

python3 "$SCRIPT_DIR/guardrail_enforcer.py" --check-push
RESULT=$?

if [ $RESULT -ne 0 ]; then
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║  ⛔ PUSH BLOCKED - UNAUTHORIZED BYPASS DETECTED          ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    echo "║  You have commits that bypassed guardrails without       ║"
    echo "║  authorization. This is not allowed.                     ║"
    echo "║                                                          ║"
    echo "║  Options:                                                ║"
    echo "║    1. Amend/rebase to fix violations                     ║"
    echo "║    2. Get retroactive authorization (if justified)       ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    exit 1
fi

exit 0
'''


def install_hooks():
    """Install all governance hooks."""
    hooks_dir = REPO_ROOT / ".git" / "hooks"

    if not hooks_dir.exists():
        print("Error: Not a git repository")
        sys.exit(1)

    # Install pre-commit hook
    pre_commit = hooks_dir / "pre-commit"
    pre_commit.write_text(PRE_COMMIT_HOOK_WITH_BYPASS)
    pre_commit.chmod(0o755)
    print(f"✅ Installed: {pre_commit}")

    # Install post-commit hook
    post_commit = hooks_dir / "post-commit"
    post_commit.write_text(POST_COMMIT_HOOK)
    post_commit.chmod(0o755)
    print(f"✅ Installed: {post_commit}")

    # Install pre-push hook
    pre_push = hooks_dir / "pre-push"
    pre_push.write_text(PRE_PUSH_HOOK)
    pre_push.chmod(0o755)
    print(f"✅ Installed: {pre_push}")

    # Create governance directory
    ensure_governance_dir()

    # Save enforcement status
    status = {
        "installed": datetime.now().isoformat(),
        "hooks": ["pre-commit", "post-commit", "pre-push"],
        "bypass_requires_code": True
    }
    save_json(ENFORCEMENT_STATUS, status)

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  ✅ GOVERNANCE ENFORCEMENT INSTALLED                     ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  Hooks installed:                                        ║")
    print("║    • pre-commit  - Blocks commits with violations        ║")
    print("║    • post-commit - Records bypass usage                  ║")
    print("║    • pre-push    - Blocks push of unauthorized bypasses  ║")
    print("║                                                          ║")
    print("║  Bypass requires authorization code.                     ║")
    print("║  All bypasses are logged in .governance/bypass_ledger    ║")
    print("╚══════════════════════════════════════════════════════════╝")


def show_status():
    """Show enforcement status."""
    status = load_json(ENFORCEMENT_STATUS)
    ledger = load_json(BYPASS_LEDGER)

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  GOVERNANCE ENFORCEMENT STATUS                           ║")
    print("╚══════════════════════════════════════════════════════════╝")

    if status:
        print(f"  Installed: {status.get('installed', 'Unknown')}")
        print(f"  Hooks: {', '.join(status.get('hooks', []))}")
        print(f"  Bypass requires code: {status.get('bypass_requires_code', False)}")
    else:
        print("  ⚠️  Enforcement not installed")
        print("  Run: python guardrail_enforcer.py --install")

    bypasses = ledger.get("bypasses", [])
    if bypasses:
        print()
        print(f"  Total bypasses recorded: {len(bypasses)}")
        authorized = sum(1 for b in bypasses if b.get("authorized"))
        unauthorized = len(bypasses) - authorized
        print(f"    Authorized: {authorized}")
        print(f"    Unauthorized: {unauthorized}")

    print()


def show_bypasses():
    """Show bypass ledger."""
    ledger = load_json(BYPASS_LEDGER)
    bypasses = ledger.get("bypasses", [])

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  BYPASS LEDGER                                           ║")
    print("╚══════════════════════════════════════════════════════════╝")

    if not bypasses:
        print("  No bypasses recorded.")
        return

    for i, bypass in enumerate(bypasses[-10:], 1):  # Last 10
        status = "✅ Authorized" if bypass.get("authorized") else "⚠️ Unauthorized"
        print(f"  [{i}] {bypass['timestamp'][:16]}")
        print(f"      Commit: {bypass['commit'][:8]}")
        print(f"      Author: {bypass['author']}")
        print(f"      Status: {status}")
        print(f"      Reason: {bypass.get('reason', 'Not provided')}")
        print()


def authorize_bypass():
    """Interactive bypass authorization."""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  BYPASS AUTHORIZATION REQUEST                            ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  ⚠️  Bypassing guardrails should be exceptional.         ║")
    print("║  All bypasses are logged and auditable.                  ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # Get author
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True, text=True
        )
        author = result.stdout.strip() or "Unknown"
    except:
        author = "Unknown"

    print(f"  Author: {author}")
    print()

    # Get reason
    print("  Why do you need to bypass guardrails?")
    print("  (This will be recorded in the audit log)")
    print()
    reason = input("  Reason: ").strip()

    if not reason:
        print("  ❌ Reason is required")
        sys.exit(1)

    if len(reason) < 10:
        print("  ❌ Please provide a more detailed reason")
        sys.exit(1)

    # Generate code
    code = generate_bypass_code(reason, author)

    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  ✅ BYPASS AUTHORIZED                                    ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print(f"║  Code: {code}                                       ║")
    print(f"║  Valid for: {BYPASS_CODE_VALIDITY_HOURS} hours                                       ║")
    print("║                                                          ║")
    print("║  To commit with bypass:                                  ║")
    print(f"║    BYPASS_CODE={code} git commit -m \"message\"        ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: guardrail_enforcer.py [--install|--status|--bypasses|--authorize]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "--install":
        install_hooks()

    elif cmd == "--status":
        show_status()

    elif cmd == "--bypasses":
        show_bypasses()

    elif cmd == "--authorize":
        authorize_bypass()

    elif cmd == "--validate-bypass":
        if len(sys.argv) < 3:
            sys.exit(1)
        code = sys.argv[2]
        valid, reason = validate_bypass_code(code)
        if valid:
            print(f"Valid bypass code. Reason: {reason}")
            sys.exit(0)
        else:
            print(f"Invalid: {reason}")
            sys.exit(1)

    elif cmd == "--record-bypass":
        if len(sys.argv) < 4:
            sys.exit(1)
        code = sys.argv[2]
        commit_hash = sys.argv[3]
        codes = load_json(BYPASS_CODES)
        if code in codes:
            record_bypass(
                commit_hash,
                codes[code]["author"],
                codes[code]["reason"],
                code
            )
            mark_code_used(code, commit_hash)

    elif cmd == "--check-push":
        unauthorized = check_unpushed_bypasses()
        if unauthorized:
            print(f"Found {len(unauthorized)} unauthorized bypass(es):")
            for b in unauthorized:
                print(f"  - {b['commit'][:8]} by {b['author']}")
            sys.exit(1)
        sys.exit(0)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
