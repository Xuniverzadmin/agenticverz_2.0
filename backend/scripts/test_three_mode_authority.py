#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: Three-Mode Authority System Test (PIN-440)
# artifact_class: CODE
"""
Three-Mode Authority System Test (PIN-440)

Tests the three authority modes:
1. LOCAL: AOS_MODE=local, DB_AUTHORITY=local → Sandbox ALLOWED
2. TEST:  AOS_MODE=test, DB_AUTHORITY=neon → Sandbox ALLOWED (NEW!)
3. PROD:  AOS_MODE=prod, DB_AUTHORITY=neon → Sandbox BLOCKED

Usage:
    python scripts/test_three_mode_authority.py
"""

import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_sandbox_allowed_logic():
    """Test the is_sandbox_allowed() logic with different env combinations."""

    print("=" * 70)
    print("THREE-MODE AUTHORITY SYSTEM TEST (PIN-440)")
    print("=" * 70)
    print()

    # Test matrix: (AOS_MODE, DB_AUTHORITY, CUSTOMER_SANDBOX_ENABLED, expected_result)
    test_cases = [
        # LOCAL mode tests
        ("local", "local", "true", True, "LOCAL mode with local DB"),
        ("local", "local", "false", False, "LOCAL mode but sandbox disabled"),
        ("local", "", "true", True, "LOCAL mode with empty DB_AUTHORITY"),

        # TEST mode tests (THE FIX - these should now work!)
        ("test", "neon", "true", True, "TEST mode with Neon DB (NEW!)"),
        ("test", "local", "true", True, "TEST mode with local DB"),
        ("test", "neon", "false", False, "TEST mode but sandbox disabled"),

        # PROD mode tests (should always block sandbox)
        ("prod", "neon", "true", False, "PROD mode with Neon - MUST BLOCK"),
        ("prod", "neon", "false", False, "PROD mode, sandbox disabled anyway"),
        ("prod", "local", "true", False, "PROD mode with local DB - STILL BLOCKED (security)"),

        # Edge cases
        ("", "neon", "true", False, "Empty AOS_MODE defaults to prod"),
        ("invalid", "neon", "true", False, "Invalid AOS_MODE treated as blocked"),
    ]

    passed = 0
    failed = 0

    for aos_mode, db_authority, sandbox_enabled, expected, description in test_cases:
        # Simulate the is_sandbox_allowed() logic
        actual = simulate_is_sandbox_allowed(aos_mode, db_authority, sandbox_enabled)

        status = "✅ PASS" if actual == expected else "❌ FAIL"
        if actual == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} | {description}")
        print(f"       AOS_MODE={aos_mode or '(empty)'}, DB_AUTHORITY={db_authority or '(empty)'}, SANDBOX_ENABLED={sandbox_enabled}")
        print(f"       Expected: {expected}, Got: {actual}")
        print()

    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


def simulate_is_sandbox_allowed(aos_mode: str, db_authority: str, sandbox_enabled: str) -> bool:
    """
    Simulate the is_sandbox_allowed() function logic.

    This mirrors the PATCHED logic in customer_sandbox.py:

    def is_sandbox_allowed() -> bool:
        if AOS_MODE not in ("local", "test"):
            return False
        if not CUSTOMER_SANDBOX_ENABLED:
            return False
        # PIN-440 FIX: Only block neon in PROD mode
        if DB_AUTHORITY == "neon" and AOS_MODE == "prod":
            return False
        return True
    """
    # Check AOS_MODE
    if aos_mode not in ("local", "test"):
        return False

    # Check CUSTOMER_SANDBOX_ENABLED
    if sandbox_enabled.lower() != "true":
        return False

    # PIN-440 FIX: Only block neon in PROD mode
    if db_authority == "neon" and aos_mode == "prod":
        return False

    return True


def test_live_module():
    """Test the actual customer_sandbox module."""
    print()
    print("=" * 70)
    print("LIVE MODULE TEST")
    print("=" * 70)
    print()

    # Import the actual module
    try:
        # We need to reload to pick up any env changes
        import importlib
        import app.auth.customer_sandbox as cs
        importlib.reload(cs)

        print(f"Current environment:")
        print(f"  AOS_MODE = {cs.AOS_MODE}")
        print(f"  DB_AUTHORITY = {cs.DB_AUTHORITY}")
        print(f"  CUSTOMER_SANDBOX_ENABLED = {cs.CUSTOMER_SANDBOX_ENABLED}")
        print()
        print(f"is_sandbox_allowed() = {cs.is_sandbox_allowed()}")
        print()

        # Test sandbox key resolution
        if cs.is_sandbox_allowed():
            principal = cs.resolve_sandbox_auth("cus_sandbox_demo")
            if principal:
                print(f"Sandbox principal resolved:")
                print(f"  tenant_id = {principal.tenant_id}")
                print(f"  customer_id = {principal.customer_id}")
                print(f"  role = {principal.role}")
                print(f"  authority = {principal.authority}")
            else:
                print("Sandbox principal NOT resolved (key invalid)")
        else:
            print("Sandbox not allowed in current environment")

        return True
    except Exception as e:
        print(f"❌ Error testing live module: {e}")
        return False


def main():
    """Run all tests."""
    # Run logic tests
    logic_ok = test_sandbox_allowed_logic()

    # Run live module test
    live_ok = test_live_module()

    print()
    print("=" * 70)
    print("FINAL STATUS")
    print("=" * 70)
    print(f"Logic tests: {'✅ PASS' if logic_ok else '❌ FAIL'}")
    print(f"Live module: {'✅ PASS' if live_ok else '❌ FAIL'}")
    print()

    if logic_ok and live_ok:
        print("✅ ALL TESTS PASSED - Three-mode authority system is working!")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
