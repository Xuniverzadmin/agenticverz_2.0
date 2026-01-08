#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: developer (one-time bootstrap)
#   Execution: sync
# Role: Seed admin1@agenticverz.com user for console.agenticverz.com deployment
# Callers: Deployment scripts, developer CLI
# Allowed Imports: L6 (models, db)
# Forbidden Imports: L2, L3, L4, L5
# Reference: Console Deployment Plan

"""
Admin User Seed Script

Creates the initial admin user for console.agenticverz.com deployment.

What this script creates:
1. Tenant: agenticverz-internal (enterprise plan)
2. User: admin1@agenticverz.com
3. TenantMembership: owner role
4. APIKey: For programmatic access
5. AuditLog: Bootstrap action record

Usage:
    # Dry run (shows what would be created)
    python3 backend/scripts/seed_admin.py --dry-run

    # Create admin user
    python3 backend/scripts/seed_admin.py

    # Create with specific Clerk user ID (after Clerk setup)
    python3 backend/scripts/seed_admin.py --clerk-user-id user_abc123

Environment:
    DATABASE_URL: Required
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select

from app.db import get_engine
from app.models.tenant import (
    APIKey,
    AuditLog,
    Tenant,
    TenantMembership,
    User,
)


def utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


# =============================================================================
# CONFIGURATION
# =============================================================================

ADMIN_CONFIG = {
    "email": "admin1@agenticverz.com",
    "name": "Admin (Founder)",
    "tenant_name": "AgenticVerz Internal",
    "tenant_slug": "agenticverz-internal",
    "plan": "enterprise",
    "role": "owner",
    "api_key_name": "admin-console-key",
}


# =============================================================================
# SEED FUNCTIONS
# =============================================================================


def check_existing(session: Session) -> dict:
    """Check if admin user/tenant already exists."""
    results = {
        "tenant_exists": False,
        "user_exists": False,
        "membership_exists": False,
        "api_key_exists": False,
        "tenant_id": None,
        "user_id": None,
    }

    # Check tenant
    tenant = session.exec(select(Tenant).where(Tenant.slug == ADMIN_CONFIG["tenant_slug"])).first()
    if tenant:
        results["tenant_exists"] = True
        results["tenant_id"] = tenant.id

    # Check user
    user = session.exec(select(User).where(User.email == ADMIN_CONFIG["email"])).first()
    if user:
        results["user_exists"] = True
        results["user_id"] = user.id

    # Check membership
    if tenant and user:
        membership = session.exec(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant.id,
                TenantMembership.user_id == user.id,
            )
        ).first()
        if membership:
            results["membership_exists"] = True

    # Check API key
    if tenant:
        api_key = session.exec(
            select(APIKey).where(
                APIKey.tenant_id == tenant.id,
                APIKey.name == ADMIN_CONFIG["api_key_name"],
            )
        ).first()
        if api_key:
            results["api_key_exists"] = True

    return results


def create_tenant(session: Session) -> Tenant:
    """Create the admin tenant."""
    tenant = Tenant(
        name=ADMIN_CONFIG["tenant_name"],
        slug=ADMIN_CONFIG["tenant_slug"],
        plan=ADMIN_CONFIG["plan"],
        billing_email=ADMIN_CONFIG["email"],
        # Enterprise quotas
        max_workers=100,
        max_runs_per_day=100000,
        max_concurrent_runs=100,
        max_tokens_per_month=1_000_000_000,
        max_api_keys=100,
        status="active",
    )
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant


def create_user(session: Session, tenant_id: str, clerk_user_id: str) -> User:
    """Create the admin user."""
    user = User(
        email=ADMIN_CONFIG["email"],
        name=ADMIN_CONFIG["name"],
        clerk_user_id=clerk_user_id,
        email_verified=True,
        email_verified_at=utc_now(),
        default_tenant_id=tenant_id,
        status="active",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def create_membership(session: Session, tenant_id: str, user_id: str) -> TenantMembership:
    """Create the tenant membership with owner role."""
    membership = TenantMembership(
        tenant_id=tenant_id,
        user_id=user_id,
        role=ADMIN_CONFIG["role"],
        invited_by="system:bootstrap",
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


def create_api_key(session: Session, tenant_id: str, user_id: str) -> tuple[APIKey, str]:
    """Create an API key for the admin. Returns (APIKey, full_key)."""
    full_key, prefix, key_hash = APIKey.generate_key()
    # Fix: DB column is varchar(10), prefix from generate_key is 12 chars
    prefix = prefix[:10]

    api_key = APIKey(
        tenant_id=tenant_id,
        user_id=user_id,
        name=ADMIN_CONFIG["api_key_name"],
        key_prefix=prefix,
        key_hash=key_hash,
        permissions_json=json.dumps(["*"]),  # Full access
        status="active",
    )
    session.add(api_key)
    session.commit()
    session.refresh(api_key)
    return api_key, full_key


def log_audit(
    session: Session,
    action: str,
    resource_type: str,
    resource_id: str,
    tenant_id: str | None = None,
    user_id: str | None = None,
    details: dict | None = None,
) -> AuditLog:
    """Log an audit entry."""
    audit = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        new_value_json=json.dumps(details) if details else None,
    )
    session.add(audit)
    session.commit()
    session.refresh(audit)
    return audit


# =============================================================================
# MAIN
# =============================================================================


def main():
    parser = argparse.ArgumentParser(description="Seed admin1@agenticverz.com for console deployment")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without making changes",
    )
    parser.add_argument(
        "--clerk-user-id",
        default="pending_clerk_sync",
        help="Clerk user ID (default: pending_clerk_sync)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force creation even if partial records exist",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("ADMIN USER SEED SCRIPT")
    print("=" * 60)
    print(f"\n  Email:       {ADMIN_CONFIG['email']}")
    print(f"  Tenant:      {ADMIN_CONFIG['tenant_name']}")
    print(f"  Role:        {ADMIN_CONFIG['role']}")
    print(f"  Clerk ID:    {args.clerk_user_id}")

    if args.dry_run:
        print("\n  MODE: DRY RUN (no changes will be made)")

    print("\n" + "-" * 60)

    # Get database connection
    try:
        engine = get_engine()
    except RuntimeError as e:
        print(f"\n❌ Database connection failed: {e}")
        print("   Ensure DATABASE_URL is set")
        return 1

    with Session(engine) as session:
        # Check existing records
        existing = check_existing(session)

        print("\nExisting Records Check:")
        print(f"  Tenant:     {'✅ EXISTS' if existing['tenant_exists'] else '⬜ Missing'}")
        print(f"  User:       {'✅ EXISTS' if existing['user_exists'] else '⬜ Missing'}")
        print(f"  Membership: {'✅ EXISTS' if existing['membership_exists'] else '⬜ Missing'}")
        print(f"  API Key:    {'✅ EXISTS' if existing['api_key_exists'] else '⬜ Missing'}")

        # If everything exists, nothing to do
        all_exist = all(
            [
                existing["tenant_exists"],
                existing["user_exists"],
                existing["membership_exists"],
                existing["api_key_exists"],
            ]
        )

        if all_exist and not args.force:
            print("\n✅ Admin user already fully configured. Nothing to do.")
            return 0

        if args.dry_run:
            print("\n" + "-" * 60)
            print("DRY RUN - Would create:")
            if not existing["tenant_exists"]:
                print(f"  ➜ Tenant: {ADMIN_CONFIG['tenant_name']} ({ADMIN_CONFIG['plan']})")
            if not existing["user_exists"]:
                print(f"  ➜ User: {ADMIN_CONFIG['email']}")
            if not existing["membership_exists"]:
                print(f"  ➜ Membership: {ADMIN_CONFIG['role']} role")
            if not existing["api_key_exists"]:
                print("  ➜ API Key: Full access (*)")
            print("\nRun without --dry-run to apply changes.")
            return 0

        # Create missing records
        print("\n" + "-" * 60)
        print("Creating Records:\n")

        tenant_id = existing["tenant_id"]
        user_id = existing["user_id"]
        full_api_key = None

        # Create tenant if needed
        if not existing["tenant_exists"]:
            tenant = create_tenant(session)
            tenant_id = tenant.id
            print(f"  ✅ Created Tenant: {tenant.name} (ID: {tenant.id})")
            log_audit(
                session,
                action="bootstrap_create_tenant",
                resource_type="tenant",
                resource_id=tenant.id,
                details={"name": tenant.name, "plan": tenant.plan},
            )

        # Create user if needed
        if not existing["user_exists"]:
            user = create_user(session, tenant_id, args.clerk_user_id)
            user_id = user.id
            print(f"  ✅ Created User: {user.email} (ID: {user.id})")
            log_audit(
                session,
                action="bootstrap_create_user",
                resource_type="user",
                resource_id=user.id,
                tenant_id=tenant_id,
                details={"email": user.email, "clerk_user_id": args.clerk_user_id},
            )

        # Create membership if needed
        if not existing["membership_exists"] and tenant_id and user_id:
            membership = create_membership(session, tenant_id, user_id)
            print(f"  ✅ Created Membership: {membership.role} (ID: {membership.id})")
            log_audit(
                session,
                action="bootstrap_create_membership",
                resource_type="tenant_membership",
                resource_id=membership.id,
                tenant_id=tenant_id,
                user_id=user_id,
                details={"role": membership.role},
            )

        # Create API key if needed
        if not existing["api_key_exists"] and tenant_id:
            api_key, full_api_key = create_api_key(session, tenant_id, user_id)
            print(f"  ✅ Created API Key: {api_key.name} (Prefix: {api_key.key_prefix})")
            log_audit(
                session,
                action="bootstrap_create_api_key",
                resource_type="api_key",
                resource_id=api_key.id,
                tenant_id=tenant_id,
                user_id=user_id,
                details={"name": api_key.name, "prefix": api_key.key_prefix},
            )

    # Summary
    print("\n" + "=" * 60)
    print("✅ ADMIN USER BOOTSTRAP COMPLETE")
    print("=" * 60)

    if full_api_key:
        print("\n⚠️  IMPORTANT: Save this API key (shown only once):")
        print(f"\n    {full_api_key}\n")

    print("\nNext Steps:")
    print("  1. Create user in Clerk dashboard: admin1@agenticverz.com")
    print("  2. Add metadata in Clerk: is_operator: true")
    print("  3. Update clerk_user_id if needed:")
    print("     python3 backend/scripts/seed_admin.py --clerk-user-id <actual_id>")
    print("  4. Set environment variables:")
    print("     CONSOLE_MODE=DRAFT")
    print("     DATA_MODE=SYNTHETIC")
    print("     ACTION_MODE=NOOP")
    print("  5. Deploy console.agenticverz.com")

    return 0


if __name__ == "__main__":
    sys.exit(main())
