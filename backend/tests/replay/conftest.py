# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: pytest
#   Execution: sync
# Role: Replay test fixtures
# Callers: pytest
# Allowed Imports: L6
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-276 Test Isolation

"""
Replay test fixtures.

Provides test isolation for m11_audit tables to prevent cross-test pollution.
"""

import os

import pytest
from sqlalchemy import create_engine, text


@pytest.fixture(autouse=True)
def clean_m11_audit_tables():
    """
    Clean m11_audit tables before each test to ensure isolation.

    PIN-276: Test isolation for replay E2E tests.
    """
    database_url = os.environ.get("DATABASE_URL", "postgresql://nova:novapass@localhost:5433/nova_aos")
    engine = create_engine(database_url)

    with engine.connect() as conn:
        # Clean before test
        conn.execute(text("DELETE FROM m11_audit.ops"))
        conn.execute(text("DELETE FROM m11_audit.replay_runs"))
        conn.commit()

    yield

    # Clean after test (belt and suspenders)
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM m11_audit.ops"))
        conn.execute(text("DELETE FROM m11_audit.replay_runs"))
        conn.commit()

    engine.dispose()
