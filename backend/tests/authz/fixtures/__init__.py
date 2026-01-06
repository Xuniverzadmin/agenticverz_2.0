# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: test
#   Execution: sync
# Role: Authorization test fixtures package
# Reference: PIN-310 (Fast-Track M7 Closure)

from tests.authz.fixtures.principals import (
    ALL_PRINCIPALS,
    HUMAN_PRINCIPALS,
    MACHINE_PRINCIPALS,
    PRINCIPAL_STATS,
    PRINCIPALS_BY_TYPE,
    get_human_principal_ids,
    get_machine_principal_ids,
    get_principal,
    get_principals_by_type,
    list_principal_ids,
)

__all__ = [
    "ALL_PRINCIPALS",
    "HUMAN_PRINCIPALS",
    "MACHINE_PRINCIPALS",
    "PRINCIPALS_BY_TYPE",
    "PRINCIPAL_STATS",
    "get_principal",
    "get_principals_by_type",
    "list_principal_ids",
    "get_human_principal_ids",
    "get_machine_principal_ids",
]
