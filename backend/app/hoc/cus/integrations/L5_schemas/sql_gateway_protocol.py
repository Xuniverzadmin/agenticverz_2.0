# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import
#   Execution: sync
# Role: Protocol and DTOs for SQL gateway driver interface
# Callers: sql_gateway.py (L5), sql_gateway_driver.py (L6)
# Allowed Imports: stdlib
# Forbidden Imports: asyncpg, sqlalchemy, sqlmodel, app.models, app.db
# Reference: PIN-520 No-Exemptions Phase 1
# artifact_class: CODE

"""
SQL Gateway Protocol & DTOs

Defines the interface contract between L5 (sql_gateway.py) and L6
(sql_gateway_driver.py). L5 builds a SqlQueryRequest; L6 executes it
against an external database via asyncpg and returns SqlQueryResult.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol, runtime_checkable


@dataclass(frozen=True)
class SqlQueryRequest:
    """Immutable request DTO passed from L5 to L6."""

    connection_string: str
    sql: str
    param_values: List[Any]
    timeout_seconds: int
    max_rows: int
    max_result_bytes: int


@dataclass
class SqlQueryResult:
    """Result DTO returned from L6 to L5."""

    data: List[Dict[str, Any]]
    row_count: int
    truncated: bool
    result_bytes: int


@runtime_checkable
class SqlGatewayDriverProtocol(Protocol):
    """Protocol that L6 sql_gateway_driver must implement."""

    async def execute_query(self, request: SqlQueryRequest) -> SqlQueryResult: ...
