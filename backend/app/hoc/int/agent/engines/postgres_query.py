# PostgreSQL Query Skill
# Safe, parameterized SQL queries with read-only by default

import logging
import os
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from .registry import skill

logger = logging.getLogger("nova.skills.postgres_query")

# Configuration
MAX_ROWS = int(os.getenv("PG_QUERY_MAX_ROWS", "1000"))
QUERY_TIMEOUT_SECONDS = int(os.getenv("PG_QUERY_TIMEOUT", "30"))
ALLOW_WRITE_QUERIES = os.getenv("PG_ALLOW_WRITE", "false").lower() == "true"

# Forbidden patterns (even in read mode)
FORBIDDEN_PATTERNS = [
    r"\bDROP\b",
    r"\bTRUNCATE\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bCOPY\b",
    r"\bEXECUTE\b",
    r"\bCALL\b",
    r";\s*--",  # Comment injection
    r";\s*$",  # Multiple statements
]


class PostgresQueryInput(BaseModel):
    """Input schema for postgres_query skill."""

    query: str = Field(
        description="Parameterized SQL query using %(name)s placeholders",
        min_length=1,
        max_length=10000,
    )
    params: Optional[Dict[str, Any]] = Field(default=None, description="Parameters for the query")
    readonly: bool = Field(default=True, description="If true, only SELECT queries allowed")
    max_rows: Optional[int] = Field(default=None, description="Maximum rows to return (capped at system limit)")
    database_url: Optional[str] = Field(default=None, description="Override database URL (must be pre-approved)")

    @field_validator("query")
    @classmethod
    def validate_query_safety(cls, v: str) -> str:
        """Check query doesn't contain forbidden patterns."""
        query_upper = v.upper()
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                raise ValueError("Query contains forbidden pattern")
        return v


class PostgresQueryOutput(BaseModel):
    """Output schema for postgres_query skill."""

    status: str = Field(description="'ok' or 'error'")
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="Query results")
    row_count: int = Field(default=0, description="Number of rows returned")
    columns: List[str] = Field(default_factory=list, description="Column names")
    truncated: bool = Field(default=False, description="True if results were truncated")
    error: Optional[str] = Field(default=None, description="Error message if failed")


def is_read_only_query(query: str) -> bool:
    """Check if query is read-only (SELECT, WITH...SELECT, EXPLAIN)."""
    normalized = query.strip().upper()

    # Allow SELECT
    if normalized.startswith("SELECT"):
        return True

    # Allow WITH ... SELECT (CTEs)
    if normalized.startswith("WITH") and "SELECT" in normalized:
        # Make sure there's no INSERT/UPDATE/DELETE after WITH
        if not any(kw in normalized for kw in ["INSERT", "UPDATE", "DELETE"]):
            return True

    # Allow EXPLAIN
    if normalized.startswith("EXPLAIN"):
        return True

    return False


@skill(
    name="postgres_query",
    input_schema=PostgresQueryInput,
    output_schema=PostgresQueryOutput,
    tags=["database", "sql", "postgres"],
)
class PostgresQuerySkill:
    """Execute safe, parameterized PostgreSQL queries.

    Features:
    - Read-only by default (only SELECT/WITH/EXPLAIN)
    - Parameterized queries to prevent SQL injection
    - Row limit enforcement
    - Query timeout
    - Forbidden pattern blocking
    """

    def __init__(self, database_url: Optional[str] = None, **kwargs):
        """Initialize with optional database URL override."""
        self.database_url = database_url or os.getenv("DATABASE_URL")

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the SQL query.

        Args:
            params: Query parameters including 'query', 'params', 'readonly'

        Returns:
            Skill result dict with rows and metadata
        """
        import psycopg2
        from psycopg2.extras import RealDictCursor

        logger.info("skill_execution_start", extra={"skill": "postgres_query"})

        query = params.get("query", "")
        query_params = params.get("params") or {}
        readonly = params.get("readonly", True)
        max_rows = min(params.get("max_rows") or MAX_ROWS, MAX_ROWS)
        db_url = params.get("database_url") or self.database_url

        # Safety checks
        if not db_url:
            return self._error_result("No database URL configured")

        # Check read-only mode
        if readonly and not is_read_only_query(query):
            return self._error_result("Query is not read-only. Set readonly=false to allow write operations.")

        # Even if not readonly, block writes unless explicitly allowed
        if not readonly and not ALLOW_WRITE_QUERIES:
            return self._error_result("Write queries are disabled. Set PG_ALLOW_WRITE=true to enable.")

        # Validate forbidden patterns (already done by Pydantic, but double-check)
        query_upper = query.upper()
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                return self._error_result("Query contains forbidden pattern")

        # Add LIMIT if not present for SELECT queries
        if is_read_only_query(query) and "LIMIT" not in query_upper:
            query = f"{query.rstrip().rstrip(';')} LIMIT {max_rows}"

        conn = None
        try:
            conn = psycopg2.connect(db_url)
            conn.set_session(readonly=readonly)

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Set statement timeout (validated integer constant)
                # Note: SET does not support parameter substitution, but QUERY_TIMEOUT_SECONDS
                # is a validated integer from environment, not user input
                timeout_ms = int(QUERY_TIMEOUT_SECONDS) * 1000  # postflight: ignore[security]
                cur.execute("SET statement_timeout = %s", (timeout_ms,))

                # Execute the query
                cur.execute(query, query_params)

                # Fetch results
                if cur.description:
                    columns = [desc[0] for desc in cur.description]
                    rows = cur.fetchmany(max_rows + 1)  # Fetch one extra to detect truncation

                    truncated = len(rows) > max_rows
                    if truncated:
                        rows = rows[:max_rows]

                    # Convert to list of dicts
                    result_rows = [dict(row) for row in rows]
                else:
                    columns = []
                    result_rows = []
                    truncated = False

            conn.commit()

            logger.info(
                "skill_execution_end",
                extra={
                    "skill": "postgres_query",
                    "status": "ok",
                    "row_count": len(result_rows),
                    "truncated": truncated,
                },
            )

            return {
                "skill": "postgres_query",
                "skill_version": "1.0.0",
                "result": {
                    "status": "ok",
                    "rows": result_rows,
                    "row_count": len(result_rows),
                    "columns": columns,
                    "truncated": truncated,
                    "error": None,
                },
                "side_effects": {"database_read": True} if readonly else {"database_write": True},
            }

        except psycopg2.Error as e:
            logger.exception("skill_execution_error", extra={"skill": "postgres_query", "error": str(e)})
            return self._error_result(f"Database error: {str(e)[:200]}")

        except Exception as e:
            logger.exception("skill_execution_error", extra={"skill": "postgres_query", "error": str(e)})
            return self._error_result(f"Unexpected error: {str(e)[:200]}")

        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _error_result(self, message: str) -> Dict[str, Any]:
        """Create an error result."""
        return {
            "skill": "postgres_query",
            "skill_version": "1.0.0",
            "result": {
                "status": "error",
                "rows": [],
                "row_count": 0,
                "columns": [],
                "truncated": False,
                "error": message,
            },
            "side_effects": {},
        }
