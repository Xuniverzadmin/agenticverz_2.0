#!/usr/bin/env python3
"""
Demo Event Seeder - M24 Ops Console
====================================

Populates ops_events with synthetic data to demonstrate the Customer Console.
Creates realistic customer archetypes with various risk signals.

Usage:
  python3 scripts/ops/seed_demo_events.py
  python3 scripts/ops/seed_demo_events.py --tenants 20 --days 14
  python3 scripts/ops/seed_demo_events.py --clean  # Remove seeded data first
  python3 scripts/ops/seed_demo_events.py --dry-run

Customer Archetypes Generated:
  1. Healthy Active    - Regular API calls, investigations, replays
  2. Silent Churn      - API active but no investigation in 7+ days
  3. Policy Friction   - Repeated POLICY_BLOCK_REPEAT events
  4. Abandonment       - REPLAY_ABORTED / EXPORT_ABORTED patterns
  5. Engagement Decay  - Declining activity over time
  6. Legal Only        - Only CERT_VERIFIED, no investigation
"""

import argparse
import os
import random
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

# Database
import psycopg2
from psycopg2.extras import execute_values

# Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_cVfk6XMYdt4G@ep-long-surf-a1n0hv91-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require",
)

# Seed marker (to identify demo data for cleanup)
SEED_MARKER = "demo_seed_v1"

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


# ----------------------------
# Event Types
# ----------------------------

EVENT_TYPES = {
    # Core activity
    "API_CALL_RECEIVED": {"weight": 100, "has_latency": True},
    "INCIDENT_CREATED": {"weight": 20, "entity_type": "incident"},
    "INCIDENT_VIEWED": {"weight": 15, "entity_type": "incident"},
    # Friction events (Phase-2)
    "INCIDENT_VIEWED_NO_ACTION": {
        "weight": 5,
        "entity_type": "incident",
        "friction": True,
    },
    "REPLAY_STARTED": {"weight": 10, "entity_type": "replay"},
    "REPLAY_EXECUTED": {"weight": 8, "entity_type": "replay"},
    "REPLAY_ABORTED": {"weight": 3, "entity_type": "replay", "friction": True},
    "REPLAY_FAILED": {"weight": 2, "entity_type": "replay", "friction": True},
    "EXPORT_STARTED": {"weight": 8, "entity_type": "export"},
    "EXPORT_GENERATED": {"weight": 6, "entity_type": "export"},
    "EXPORT_ABORTED": {"weight": 2, "entity_type": "export", "friction": True},
    "EXPORT_FAILED": {"weight": 1, "entity_type": "export", "friction": True},
    # Policy
    "POLICY_EVALUATED": {"weight": 30},
    "POLICY_BLOCKED": {"weight": 5},
    "POLICY_BLOCK_REPEAT": {"weight": 2, "friction": True},
    # Certificate
    "CERT_VERIFIED": {"weight": 10, "entity_type": "certificate"},
    # LLM
    "LLM_CALL_MADE": {"weight": 40, "has_latency": True, "has_cost": True},
    "LLM_CALL_FAILED": {"weight": 3},
    # Session
    "SESSION_STARTED": {"weight": 15},
    "SESSION_ENDED": {"weight": 12},
    "SESSION_IDLE_TIMEOUT": {"weight": 3, "friction": True},
}


# ----------------------------
# Customer Archetypes
# ----------------------------


@dataclass
class CustomerArchetype:
    name: str
    description: str
    event_mix: Dict[str, float]  # Event type -> probability multiplier
    activity_pattern: str  # "steady", "declining", "sporadic", "inactive"
    events_per_day_range: Tuple[int, int]


ARCHETYPES = {
    "healthy_active": CustomerArchetype(
        name="Healthy Active",
        description="Regular API calls, investigations, replays, exports",
        event_mix={
            "API_CALL_RECEIVED": 2.0,
            "INCIDENT_CREATED": 1.5,
            "INCIDENT_VIEWED": 2.0,
            "REPLAY_STARTED": 1.5,
            "REPLAY_EXECUTED": 1.5,
            "EXPORT_STARTED": 1.0,
            "EXPORT_GENERATED": 1.0,
            "LLM_CALL_MADE": 1.5,
            "POLICY_EVALUATED": 1.0,
            "SESSION_STARTED": 1.5,
            "SESSION_ENDED": 1.5,
        },
        activity_pattern="steady",
        events_per_day_range=(20, 50),
    ),
    "silent_churn": CustomerArchetype(
        name="Silent Churn",
        description="API active but no investigation in 7+ days",
        event_mix={
            "API_CALL_RECEIVED": 2.0,
            "LLM_CALL_MADE": 1.0,
            "POLICY_EVALUATED": 1.0,
            # No incident views or replays
        },
        activity_pattern="steady",
        events_per_day_range=(10, 25),
    ),
    "policy_friction": CustomerArchetype(
        name="Policy Friction",
        description="Repeated POLICY_BLOCK_REPEAT events",
        event_mix={
            "API_CALL_RECEIVED": 1.5,
            "POLICY_EVALUATED": 3.0,
            "POLICY_BLOCKED": 2.0,
            "POLICY_BLOCK_REPEAT": 5.0,  # High friction
            "INCIDENT_CREATED": 0.5,
            "SESSION_STARTED": 1.0,
        },
        activity_pattern="sporadic",
        events_per_day_range=(15, 35),
    ),
    "abandonment": CustomerArchetype(
        name="Abandonment Pattern",
        description="Started but aborted replays/exports",
        event_mix={
            "API_CALL_RECEIVED": 1.5,
            "INCIDENT_CREATED": 1.0,
            "INCIDENT_VIEWED": 1.5,
            "INCIDENT_VIEWED_NO_ACTION": 3.0,  # Hesitation
            "REPLAY_STARTED": 3.0,
            "REPLAY_ABORTED": 4.0,  # High abort rate
            "REPLAY_EXECUTED": 0.5,
            "EXPORT_STARTED": 2.0,
            "EXPORT_ABORTED": 3.0,  # High abort rate
            "EXPORT_GENERATED": 0.3,
            "SESSION_IDLE_TIMEOUT": 2.0,
        },
        activity_pattern="declining",
        events_per_day_range=(10, 30),
    ),
    "engagement_decay": CustomerArchetype(
        name="Engagement Decay",
        description="Activity declining week over week",
        event_mix={
            "API_CALL_RECEIVED": 1.0,
            "INCIDENT_CREATED": 0.8,
            "INCIDENT_VIEWED": 0.5,
            "REPLAY_EXECUTED": 0.3,
            "SESSION_STARTED": 0.5,
            "SESSION_IDLE_TIMEOUT": 1.5,
        },
        activity_pattern="declining",
        events_per_day_range=(5, 20),
    ),
    "legal_only": CustomerArchetype(
        name="Legal Only",
        description="Only certs verified, no investigation",
        event_mix={
            "API_CALL_RECEIVED": 1.0,
            "CERT_VERIFIED": 5.0,  # Only certs
            "POLICY_EVALUATED": 0.5,
        },
        activity_pattern="sporadic",
        events_per_day_range=(5, 15),
    ),
}


# ----------------------------
# Demo Tenant Names
# ----------------------------

COMPANY_PREFIXES = [
    "Acme",
    "Nova",
    "Quantum",
    "Stellar",
    "Apex",
    "Nexus",
    "Zenith",
    "Pulse",
    "Vertex",
    "Cipher",
    "Lunar",
    "Solar",
    "Cosmic",
    "Vortex",
    "Phoenix",
    "Atlas",
    "Titan",
    "Nebula",
    "Echo",
    "Flux",
]

COMPANY_SUFFIXES = [
    "AI",
    "Labs",
    "Tech",
    "Systems",
    "Corp",
    "Inc",
    "Solutions",
    "Dynamics",
    "Robotics",
    "Intelligence",
    "Analytics",
    "Ventures",
]


def generate_company_name() -> str:
    return f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_SUFFIXES)}"


# ----------------------------
# Event Generation
# ----------------------------


def generate_events_for_tenant(
    tenant_id: uuid.UUID,
    tenant_name: str,
    archetype: CustomerArchetype,
    days: int,
    now: datetime,
) -> List[Dict[str, Any]]:
    """Generate events for a single tenant based on archetype."""
    events = []

    for day_offset in range(days, 0, -1):
        day_start = now - timedelta(days=day_offset)

        # Calculate activity level based on pattern
        if archetype.activity_pattern == "steady":
            activity_mult = 1.0
        elif archetype.activity_pattern == "declining":
            # More activity in the past, less recently
            activity_mult = 0.3 + (day_offset / days) * 0.7
        elif archetype.activity_pattern == "sporadic":
            activity_mult = random.uniform(0.3, 1.5)
        elif archetype.activity_pattern == "inactive":
            activity_mult = 0.1 if day_offset > 7 else 0.0
        else:
            activity_mult = 1.0

        # Determine number of events for this day
        min_events, max_events = archetype.events_per_day_range
        base_events = random.randint(min_events, max_events)
        num_events = int(base_events * activity_mult)

        # Generate session for the day
        session_id = uuid.uuid4() if random.random() > 0.3 else None

        for _ in range(num_events):
            # Pick event type based on archetype mix
            event_type = pick_event_type(archetype.event_mix)
            if not event_type:
                continue

            event_config = EVENT_TYPES.get(event_type, {})

            # Generate timestamp within the day
            seconds_offset = random.randint(0, 86400)
            timestamp = day_start + timedelta(seconds=seconds_offset)

            # Build event
            event = {
                "event_id": uuid.uuid4(),
                "timestamp": timestamp,
                "tenant_id": tenant_id,
                "event_type": event_type,
                "session_id": session_id,
                "entity_type": event_config.get("entity_type"),
                "entity_id": uuid.uuid4() if event_config.get("entity_type") else None,
                "severity": random.randint(1, 3)
                if event_config.get("friction")
                else None,
                "latency_ms": random.randint(50, 2000)
                if event_config.get("has_latency")
                else None,
                "cost_usd": Decimal(str(round(random.uniform(0.001, 0.05), 6)))
                if event_config.get("has_cost")
                else None,
                "metadata": {
                    "seed_marker": SEED_MARKER,
                    "tenant_name": tenant_name,
                    "archetype": archetype.name,
                },
            }

            # Add friction signal for friction events
            if event_config.get("friction"):
                event["metadata"]["friction_signal"] = event_type.lower()

            events.append(event)

    return events


def pick_event_type(event_mix: Dict[str, float]) -> Optional[str]:
    """Pick an event type based on weighted probabilities."""
    # Build weighted list
    weighted = []
    for event_type, multiplier in event_mix.items():
        if event_type in EVENT_TYPES:
            base_weight = EVENT_TYPES[event_type]["weight"]
            weighted.append((event_type, base_weight * multiplier))

    if not weighted:
        return None

    total = sum(w for _, w in weighted)
    r = random.uniform(0, total)

    cumulative = 0
    for event_type, weight in weighted:
        cumulative += weight
        if r <= cumulative:
            return event_type

    return weighted[-1][0]


# ----------------------------
# Database Operations
# ----------------------------


def get_connection():
    """Get database connection."""
    return psycopg2.connect(DATABASE_URL)


def clean_seeded_data(conn) -> int:
    """Remove previously seeded demo data."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM ops_events WHERE metadata->>'seed_marker' = %s", (SEED_MARKER,)
        )
        deleted = cur.rowcount
        conn.commit()
    return deleted


def insert_events(conn, events: List[Dict[str, Any]]) -> int:
    """Bulk insert events."""
    if not events:
        return 0

    # Prepare data for insertion
    columns = [
        "event_id",
        "timestamp",
        "tenant_id",
        "user_id",
        "session_id",
        "event_type",
        "entity_type",
        "entity_id",
        "severity",
        "latency_ms",
        "cost_usd",
        "metadata",
    ]

    values = []
    for e in events:
        values.append(
            (
                str(e["event_id"]),
                e["timestamp"],
                str(e["tenant_id"]),
                None,  # user_id
                str(e["session_id"]) if e["session_id"] else None,
                e["event_type"],
                e["entity_type"],
                str(e["entity_id"]) if e["entity_id"] else None,
                e["severity"],
                e["latency_ms"],
                float(e["cost_usd"]) if e["cost_usd"] else None,
                psycopg2.extras.Json(e["metadata"]),
            )
        )

    with conn.cursor() as cur:
        execute_values(
            cur,
            f"""
            INSERT INTO ops_events ({', '.join(columns)})
            VALUES %s
            """,
            values,
            template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        )
        conn.commit()

    return len(values)


# ----------------------------
# Main
# ----------------------------


def main():
    parser = argparse.ArgumentParser(description="Seed demo events for Ops Console")
    parser.add_argument(
        "--tenants", type=int, default=12, help="Number of tenants to create"
    )
    parser.add_argument(
        "--days", type=int, default=14, help="Days of history to generate"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Remove existing seeded data first"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be created"
    )
    args = parser.parse_args()

    print(f"\n{CYAN}{'='*60}{RESET}")
    print(f"{CYAN}{BOLD}  Ops Console Demo Seeder{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")

    now = datetime.now(timezone.utc)

    # Determine archetype distribution
    # Aim for: 40% healthy, 60% various risk patterns
    archetype_distribution = [
        ("healthy_active", 0.35),
        ("silent_churn", 0.15),
        ("policy_friction", 0.12),
        ("abandonment", 0.15),
        ("engagement_decay", 0.13),
        ("legal_only", 0.10),
    ]

    # Generate tenants with archetypes
    tenants = []
    for i in range(args.tenants):
        tenant_id = uuid.uuid4()
        tenant_name = generate_company_name()

        # Pick archetype based on distribution
        r = random.random()
        cumulative = 0
        archetype_key = "healthy_active"
        for key, prob in archetype_distribution:
            cumulative += prob
            if r <= cumulative:
                archetype_key = key
                break

        tenants.append(
            {
                "id": tenant_id,
                "name": tenant_name,
                "archetype": ARCHETYPES[archetype_key],
                "archetype_key": archetype_key,
            }
        )

    # Show plan
    print(f"  {BOLD}Configuration:{RESET}")
    print(f"    Tenants: {args.tenants}")
    print(f"    Days of history: {args.days}")
    print(f"    Database: {DATABASE_URL[:50]}...")
    print()

    print(f"  {BOLD}Tenant Distribution:{RESET}")
    archetype_counts = {}
    for t in tenants:
        key = t["archetype_key"]
        archetype_counts[key] = archetype_counts.get(key, 0) + 1

    for key, count in sorted(archetype_counts.items()):
        arch = ARCHETYPES[key]
        color = (
            GREEN
            if key == "healthy_active"
            else YELLOW
            if key in ["silent_churn", "abandonment", "engagement_decay"]
            else RESET
        )
        print(f"    {color}{arch.name:20s}{RESET} {count:3d} tenants")
    print()

    # Generate events
    print(f"  {BOLD}Generating events...{RESET}")
    all_events = []
    for t in tenants:
        events = generate_events_for_tenant(
            tenant_id=t["id"],
            tenant_name=t["name"],
            archetype=t["archetype"],
            days=args.days,
            now=now,
        )
        all_events.extend(events)
        print(f"    {t['name']:30s} {len(events):5d} events ({t['archetype'].name})")

    print(f"\n  {BOLD}Total events: {len(all_events):,}{RESET}")

    if args.dry_run:
        print(f"\n  {YELLOW}Dry run - no data inserted{RESET}")
        print(f"{CYAN}{'='*60}{RESET}\n")
        return

    # Connect and insert
    print(f"\n  {BOLD}Inserting into database...{RESET}")

    try:
        conn = get_connection()

        # Clean existing data if requested
        if args.clean:
            deleted = clean_seeded_data(conn)
            print(f"    {YELLOW}Cleaned {deleted:,} existing seeded events{RESET}")

        # Insert new events
        inserted = insert_events(conn, all_events)
        print(f"    {GREEN}Inserted {inserted:,} events{RESET}")

        conn.close()

    except Exception as e:
        print(f"    {RED}Error: {e}{RESET}")
        sys.exit(1)

    # Summary
    print(f"\n{CYAN}{'─'*60}{RESET}")
    print(f"  {GREEN}✓ Demo data seeded successfully{RESET}")
    print(f"\n  {DIM}Run the console test to verify:{RESET}")
    print(f"  {DIM}  python3 scripts/ops/test_customer_console.py --verbose{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")


if __name__ == "__main__":
    main()
