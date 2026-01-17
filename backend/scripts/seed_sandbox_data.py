#!/usr/bin/env python3
# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual (CLI)
#   Execution: sync
# Role: Seed sandbox tenant data for local development
# Reference: PIN-439

"""Sandbox Data Seeder

Seeds local database with demo tenant and integration data for customer sandbox mode.

USAGE:
    # From backend directory
    python scripts/seed_sandbox_data.py

REQUIREMENTS:
    - Local PostgreSQL database (not Neon)
    - DATABASE_URL environment variable set

WHAT IT CREATES:
    - demo-tenant tenant record
    - Demo OpenAI integration (with fake key)
    - Demo Anthropic integration (with fake key)
    - Sample daily usage records
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Seed data configuration
SANDBOX_TENANTS = [
    {
        "id": "demo-tenant",
        "name": "Demo Tenant",
        "status": "active",
    },
    {
        "id": "tenant-2",
        "name": "Tenant Two",
        "status": "active",
    },
    {
        "id": "ci-tenant",
        "name": "CI Test Tenant",
        "status": "active",
    },
]

SANDBOX_INTEGRATIONS = [
    {
        "tenant_id": "demo-tenant",
        "name": "Demo OpenAI",
        "provider_type": "openai",
        "status": "enabled",
        "credentials_encrypted": "sandbox_openai_key_encrypted",
        "config": '{"model": "gpt-4", "max_tokens": 4096}',
        "budget_limit_cents": 10000,  # $100
        "rate_limit_rpm": 100,
        "rate_limit_tpm": 100000,
    },
    {
        "tenant_id": "demo-tenant",
        "name": "Demo Anthropic",
        "provider_type": "anthropic",
        "status": "enabled",
        "credentials_encrypted": "sandbox_anthropic_key_encrypted",
        "config": '{"model": "claude-sonnet-4-20250514", "max_tokens": 8192}',
        "budget_limit_cents": 20000,  # $200
        "rate_limit_rpm": 50,
        "rate_limit_tpm": 200000,
    },
    {
        "tenant_id": "tenant-2",
        "name": "Tenant 2 OpenAI",
        "provider_type": "openai",
        "status": "enabled",
        "credentials_encrypted": "sandbox_t2_openai_key",
        "config": '{"model": "gpt-3.5-turbo"}',
        "budget_limit_cents": 5000,
        "rate_limit_rpm": 50,
        "rate_limit_tpm": 50000,
    },
]


def seed_tenants(session: Session) -> None:
    """Seed sandbox tenants."""
    print("Seeding tenants...")

    for tenant in SANDBOX_TENANTS:
        # Check if tenant exists
        result = session.execute(
            text("SELECT id FROM tenants WHERE id = :id"),
            {"id": tenant["id"]}
        ).fetchone()

        if result:
            print(f"  Tenant {tenant['id']} already exists, skipping")
            continue

        # Insert tenant
        session.execute(
            text("""
                INSERT INTO tenants (id, name, status, created_at, updated_at)
                VALUES (:id, :name, :status, NOW(), NOW())
            """),
            tenant
        )
        print(f"  Created tenant: {tenant['id']}")

    session.commit()


def seed_integrations(session: Session) -> None:
    """Seed sandbox customer integrations."""
    print("Seeding customer integrations...")

    for integration in SANDBOX_INTEGRATIONS:
        # Check if integration exists
        result = session.execute(
            text("""
                SELECT id FROM cus_integrations
                WHERE tenant_id = :tenant_id AND name = :name
            """),
            {"tenant_id": integration["tenant_id"], "name": integration["name"]}
        ).fetchone()

        if result:
            print(f"  Integration {integration['name']} already exists, skipping")
            continue

        # Insert integration
        integration_id = str(uuid4())
        session.execute(
            text("""
                INSERT INTO cus_integrations (
                    id, tenant_id, name, provider_type, status,
                    credentials_encrypted, config,
                    budget_limit_cents, budget_period,
                    rate_limit_rpm, rate_limit_tpm,
                    health_status, created_at, updated_at
                ) VALUES (
                    :id, :tenant_id, :name, :provider_type, :status,
                    :credentials_encrypted, :config::jsonb,
                    :budget_limit_cents, 'monthly',
                    :rate_limit_rpm, :rate_limit_tpm,
                    'healthy', NOW(), NOW()
                )
            """),
            {
                "id": integration_id,
                **integration,
            }
        )
        print(f"  Created integration: {integration['name']} ({integration_id[:8]}...)")

    session.commit()


def seed_sample_usage(session: Session) -> None:
    """Seed sample usage data for the past 7 days."""
    print("Seeding sample usage data...")

    # Get demo-tenant integrations
    result = session.execute(
        text("""
            SELECT id, name FROM cus_integrations
            WHERE tenant_id = 'demo-tenant'
        """)
    ).fetchall()

    if not result:
        print("  No integrations found for demo-tenant, skipping usage seeding")
        return

    now = datetime.now(timezone.utc)

    for integration_id, integration_name in result:
        for days_ago in range(7):
            usage_date = (now - timedelta(days=days_ago)).date()

            # Check if daily record exists
            existing = session.execute(
                text("""
                    SELECT id FROM cus_usage_daily
                    WHERE integration_id = :integration_id AND usage_date = :usage_date
                """),
                {"integration_id": integration_id, "usage_date": usage_date}
            ).fetchone()

            if existing:
                continue

            # Insert sample daily usage (decreasing as we go back in time)
            multiplier = 1.0 - (days_ago * 0.1)
            session.execute(
                text("""
                    INSERT INTO cus_usage_daily (
                        id, integration_id, tenant_id, usage_date,
                        total_calls, total_input_tokens, total_output_tokens,
                        total_cost_cents, error_count, avg_latency_ms,
                        created_at
                    ) VALUES (
                        :id, :integration_id, 'demo-tenant', :usage_date,
                        :total_calls, :total_input_tokens, :total_output_tokens,
                        :total_cost_cents, :error_count, :avg_latency_ms,
                        NOW()
                    )
                """),
                {
                    "id": str(uuid4()),
                    "integration_id": integration_id,
                    "usage_date": usage_date,
                    "total_calls": int(100 * multiplier),
                    "total_input_tokens": int(50000 * multiplier),
                    "total_output_tokens": int(25000 * multiplier),
                    "total_cost_cents": int(150 * multiplier),
                    "error_count": int(5 * multiplier) if days_ago % 3 == 0 else 0,
                    "avg_latency_ms": int(500 + (days_ago * 50)),
                }
            )

        print(f"  Seeded 7 days of usage for: {integration_name}")

    session.commit()


def main():
    """Main entry point."""
    print("=" * 60)
    print("Customer Sandbox Data Seeder")
    print("=" * 60)

    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    # Safety check: don't seed Neon
    if "neon" in database_url.lower():
        print("ERROR: Refusing to seed data on Neon (production) database")
        print("       This script is for local/CI databases only")
        sys.exit(1)

    print(f"Database: {database_url[:50]}...")
    print()

    # Create engine and session
    engine = create_engine(database_url)

    with Session(engine) as session:
        try:
            # Check if tenants table exists
            session.execute(text("SELECT 1 FROM tenants LIMIT 1"))
        except Exception as e:
            print(f"ERROR: tenants table not found. Run migrations first.")
            print(f"       {e}")
            sys.exit(1)

        try:
            # Check if cus_integrations table exists
            session.execute(text("SELECT 1 FROM cus_integrations LIMIT 1"))
        except Exception as e:
            print(f"ERROR: cus_integrations table not found. Run migration 103 first.")
            print(f"       {e}")
            sys.exit(1)

        # Seed data
        seed_tenants(session)
        seed_integrations(session)
        seed_sample_usage(session)

    print()
    print("=" * 60)
    print("Sandbox data seeding complete!")
    print()
    print("To test, use:")
    print('  curl -H "X-AOS-Customer-Key: cus_sandbox_demo" \\')
    print('       http://localhost:8000/api/v1/cus/integrations')
    print("=" * 60)


if __name__ == "__main__":
    main()
