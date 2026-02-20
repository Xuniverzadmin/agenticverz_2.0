# capability_id: CAP-018
# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L5 sql_gateway.py)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: external DB via asyncpg
#   Writes: none (read-only templates)
# Role: Owns asyncpg import and connection lifecycle for SQL gateway
# Callers: sql_gateway.py (L5)
# Allowed Imports: L6, asyncpg (external DB connector)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-520 No-Exemptions Phase 1
# artifact_class: CODE

"""
SQL Gateway Driver (L6)

Owns the asyncpg import and external database connection lifecycle.
Executes parameterized SQL templates provided by the L5 engine.

L6 Contract:
    - Accepts SqlQueryRequest from L5 (connection_string, sql, params)
    - Opens/closes asyncpg connection per query
    - Enforces max_rows and max_result_bytes caps
    - Returns SqlQueryResult DTO to L5
    - Does NOT commit (read-only by design; external DB)
"""

import asyncio
import logging
from typing import Any, Dict, List

import asyncpg

from app.hoc.cus.integrations.L5_schemas.sql_gateway_protocol import (
    SqlQueryRequest,
    SqlQueryResult,
)

logger = logging.getLogger("nova.services.connectors.sql_gateway_driver")


class SqlGatewayDriver:
    """L6 driver: executes parameterized SQL against external databases."""

    async def execute_query(self, request: SqlQueryRequest) -> SqlQueryResult:
        """Execute a parameterized query and return capped results."""
        conn = await asyncpg.connect(
            request.connection_string,
            timeout=request.timeout_seconds,
        )

        try:
            rows = await asyncio.wait_for(
                conn.fetch(request.sql, *request.param_values),
                timeout=request.timeout_seconds,
            )

            # Enforce max rows
            truncated = len(rows) > request.max_rows
            if truncated:
                logger.warning(
                    "sql_gateway_driver.rows_truncated",
                    extra={
                        "original_count": len(rows),
                        "limit": request.max_rows,
                    },
                )
                rows = rows[: request.max_rows]

            # Convert to dicts
            result_data: List[Dict[str, Any]] = [dict(row) for row in rows]

            # Check result size
            result_bytes = len(str(result_data).encode())
            if result_bytes > request.max_result_bytes:
                logger.warning(
                    "sql_gateway_driver.result_truncated",
                    extra={
                        "original_bytes": result_bytes,
                        "limit": request.max_result_bytes,
                    },
                )
                while result_bytes > request.max_result_bytes and result_data:
                    result_data.pop()
                    result_bytes = len(str(result_data).encode())
                truncated = True

            return SqlQueryResult(
                data=result_data,
                row_count=len(result_data),
                truncated=truncated,
                result_bytes=result_bytes,
            )

        finally:
            await conn.close()


def get_sql_gateway_driver() -> SqlGatewayDriver:
    """Factory for L4/L5 callers."""
    return SqlGatewayDriver()
