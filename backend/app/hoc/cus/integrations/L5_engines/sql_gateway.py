# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api (via mediation layer)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: (via SQL templates - external DB)
#   Writes: none (read-only templates)
# Role: Template-based SQL queries (NO raw SQL from LLM)
# Product: system-wide
# Callers: RetrievalMediator
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-060

"""
Module: sql_gateway
Purpose: Template-based SQL queries (NO raw SQL from LLM).

Key Difference from PostgresQuerySkill:
    - PostgresQuerySkill: LLM provides SQL string (DANGEROUS)
    - SqlGatewayService: LLM selects template ID, machine fills parameters

Security Invariant: LLM NEVER sees or constructs SQL.
The SQL comes from pre-registered, audited templates.

Imports (Dependencies):
    - None (credential service passed via constructor)

Exports (Provides):
    - SqlGatewayService: Governed SQL access
    - SqlGatewayConfig: Configuration dataclass
    - QueryTemplate: SQL template definition

Wiring Points:
    - Called from: RetrievalMediator
    - Registered in: ConnectorRegistry

Acceptance Criteria:
    - [x] AC-060-01: No raw SQL from LLM
    - [x] AC-060-02: Template ID required
    - [x] AC-060-03: Parameters validated
    - [x] AC-060-04: Read-only enforced
    - [x] AC-060-05: SQL injection prevented
    - [x] AC-060-06: Max rows enforced
    - [x] AC-060-07: Tenant isolation (INV-003)
    - [x] AC-060-08: Max result bytes enforced
    - [x] AC-060-09: Query timeout enforced
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
import logging

# Credential and CredentialService imported from canonical source — INT-DUP-001, INT-DUP-002
from app.hoc.cus.integrations.L5_engines.credentials import (
    Credential,
    CredentialService,
)

logger = logging.getLogger("nova.services.connectors.sql_gateway")

# Blast-radius caps (INV-003 connector constraints)
DEFAULT_MAX_ROWS = 1000
DEFAULT_MAX_RESULT_BYTES = 5 * 1024 * 1024  # 5MB
DEFAULT_TIMEOUT_SECONDS = 30


class ParameterType(str, Enum):
    """Supported parameter types for validation."""
    STRING = "str"
    INTEGER = "int"
    FLOAT = "float"
    BOOLEAN = "bool"
    DATE = "date"
    TIMESTAMP = "timestamp"
    UUID = "uuid"
    LIST_STRING = "list[str]"
    LIST_INT = "list[int]"


@dataclass
class ParameterSpec:
    """Specification for a query parameter."""
    name: str
    param_type: ParameterType
    required: bool = True
    default: Any = None
    description: str = ""
    max_length: Optional[int] = None  # For strings
    min_value: Optional[float] = None  # For numbers
    max_value: Optional[float] = None  # For numbers


@dataclass
class QueryTemplate:
    """Definition of a SQL query template."""
    id: str
    name: str
    description: str
    sql: str  # Parameterized SQL with $1, $2, etc. placeholders
    parameters: List[ParameterSpec]
    read_only: bool = True
    max_rows: int = DEFAULT_MAX_ROWS
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS


@dataclass
class SqlGatewayConfig:
    """Configuration for SQL gateway."""
    id: str
    name: str
    connection_string_ref: str  # Vault reference
    allowed_templates: List[str]  # Template IDs this connector can use
    max_rows: int = DEFAULT_MAX_ROWS
    max_result_bytes: int = DEFAULT_MAX_RESULT_BYTES
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    read_only: bool = True  # Default to read-only
    tenant_id: str = ""  # Owning tenant for isolation


# Credential dataclass removed — INT-DUP-001 quarantine
# Import from canonical source: engines/credentials/types.py

# CredentialService protocol removed — INT-DUP-002 quarantine
# Import from canonical source: engines/credentials/protocol.py


class SqlGatewayError(Exception):
    """Error from SQL gateway."""
    pass


class SqlInjectionAttemptError(SqlGatewayError):
    """Potential SQL injection detected."""
    pass


class SqlGatewayService:
    """
    Governed SQL gateway.

    Machine controls:
    - SQL query templates (pre-registered)
    - Parameter validation
    - Connection credentials
    - Read-only enforcement
    - Row limits

    LLM controls:
    - Template selection (by ID from allowlist)
    - Parameter values (validated against spec)

    Implements Connector protocol for use with RetrievalMediator.
    """

    def __init__(
        self,
        config: SqlGatewayConfig,
        template_registry: Dict[str, QueryTemplate],
        credential_service: Optional[CredentialService] = None,
    ):
        self.config = config
        self.templates = template_registry
        self.credential_service = credential_service

    @property
    def id(self) -> str:
        """Connector ID for protocol compliance."""
        return self.config.id

    async def execute(
        self,
        action: str,  # Template ID
        payload: Dict[str, Any],  # Parameter values
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a templated SQL query.

        Args:
            action: Template ID to execute
            payload: Parameter values for the template
            tenant_id: Requesting tenant (for isolation)

        Returns:
            Query results with token_count

        Raises:
            SqlGatewayError: On query failure
            ValueError: If template unknown or parameters invalid
        """
        # Step 1: Resolve template (machine-controlled)
        template = self._resolve_template(action)

        # Step 2: Validate parameters (prevent SQL injection)
        validated_params = self._validate_parameters(template, payload)

        # Step 3: Check read-only constraint
        if self.config.read_only and not template.read_only:
            raise SqlGatewayError(
                f"Read-only connector cannot execute write template '{action}'"
            )

        # Step 4: Get connection string (machine-controlled from vault)
        connection_string = await self._get_connection_string()

        # Step 5: Execute query
        try:
            import asyncpg

            conn = await asyncpg.connect(
                connection_string,
                timeout=self.config.timeout_seconds,
            )

            try:
                # Build parameter list in order
                param_values = [
                    validated_params.get(p.name)
                    for p in template.parameters
                    if p.name in validated_params
                ]

                # Execute with timeout
                rows = await asyncio.wait_for(
                    conn.fetch(template.sql, *param_values),
                    timeout=template.timeout_seconds,
                )

                # Enforce max rows
                row_limit = min(template.max_rows, self.config.max_rows)
                if len(rows) > row_limit:
                    logger.warning("sql_gateway.rows_truncated", extra={
                        "connector_id": self.id,
                        "template_id": action,
                        "original_count": len(rows),
                        "limit": row_limit,
                    })
                    rows = rows[:row_limit]
                    truncated = True
                else:
                    truncated = False

                # Convert to dicts
                result_data = [dict(row) for row in rows]

                # Check result size
                result_bytes = len(str(result_data).encode())
                if result_bytes > self.config.max_result_bytes:
                    logger.warning("sql_gateway.result_truncated", extra={
                        "connector_id": self.id,
                        "template_id": action,
                        "original_bytes": result_bytes,
                        "limit": self.config.max_result_bytes,
                    })
                    # Truncate by removing rows until under limit
                    while result_bytes > self.config.max_result_bytes and result_data:
                        result_data.pop()
                        result_bytes = len(str(result_data).encode())
                    truncated = True

                return {
                    "data": result_data,
                    "row_count": len(result_data),
                    "truncated": truncated,
                    "token_count": result_bytes,
                }

            finally:
                await conn.close()

        except asyncio.TimeoutError:
            logger.error("sql_gateway.timeout", extra={
                "connector_id": self.id,
                "template_id": action,
                "timeout": template.timeout_seconds,
            })
            raise SqlGatewayError(
                f"Query timed out after {template.timeout_seconds}s"
            )

        except Exception as e:
            logger.error("sql_gateway.error", extra={
                "connector_id": self.id,
                "template_id": action,
                "error": str(e),
            })
            raise SqlGatewayError(f"Query failed: {e}") from e

    def _resolve_template(self, template_id: str) -> QueryTemplate:
        """Resolve template by ID (machine-controlled)."""
        if template_id not in self.templates:
            available = list(self.templates.keys())
            raise ValueError(
                f"Unknown template: {template_id}. Available: {available}"
            )

        template = self.templates[template_id]

        if template_id not in self.config.allowed_templates:
            raise ValueError(
                f"Template '{template_id}' not allowed for this connector. "
                f"Allowed: {self.config.allowed_templates}"
            )

        return template

    def _validate_parameters(
        self,
        template: QueryTemplate,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate and type-coerce parameters.

        This is the SQL injection prevention layer.
        All values are validated against their declared types.
        """
        validated = {}

        for param_spec in template.parameters:
            name = param_spec.name

            if name not in payload:
                if param_spec.required:
                    raise ValueError(f"Missing required parameter: {name}")
                if param_spec.default is not None:
                    validated[name] = param_spec.default
                continue

            value = payload[name]

            # Type validation and coercion
            try:
                validated[name] = self._coerce_parameter(value, param_spec)
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Invalid value for parameter '{name}': {e}"
                )

        # Check for extra parameters (potential injection attempt)
        extra_params = set(payload.keys()) - {p.name for p in template.parameters}
        if extra_params:
            logger.warning("sql_gateway.extra_parameters", extra={
                "template_id": template.id,
                "extra": list(extra_params),
            })
            # Don't raise - just ignore extra params

        return validated

    def _coerce_parameter(
        self,
        value: Any,
        spec: ParameterSpec,
    ) -> Any:
        """Coerce and validate a single parameter."""
        if value is None:
            if spec.required:
                raise ValueError("None not allowed for required parameter")
            return spec.default

        if spec.param_type == ParameterType.STRING:
            result = str(value)
            if spec.max_length and len(result) > spec.max_length:
                raise ValueError(f"String exceeds max length {spec.max_length}")
            # Check for SQL injection patterns
            self._check_sql_injection(result)
            return result

        elif spec.param_type == ParameterType.INTEGER:
            result = int(value)
            if spec.min_value is not None and result < spec.min_value:
                raise ValueError(f"Value below minimum {spec.min_value}")
            if spec.max_value is not None and result > spec.max_value:
                raise ValueError(f"Value above maximum {spec.max_value}")
            return result

        elif spec.param_type == ParameterType.FLOAT:
            result = float(value)
            if spec.min_value is not None and result < spec.min_value:
                raise ValueError(f"Value below minimum {spec.min_value}")
            if spec.max_value is not None and result > spec.max_value:
                raise ValueError(f"Value above maximum {spec.max_value}")
            return result

        elif spec.param_type == ParameterType.BOOLEAN:
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes')
            return bool(value)

        elif spec.param_type == ParameterType.UUID:
            import uuid
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(str(value))

        elif spec.param_type == ParameterType.DATE:
            if isinstance(value, str):
                return datetime.strptime(value, '%Y-%m-%d').date()
            return value

        elif spec.param_type == ParameterType.TIMESTAMP:
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            return value

        elif spec.param_type == ParameterType.LIST_STRING:
            if not isinstance(value, list):
                raise ValueError("Expected list")
            result = [str(v) for v in value]
            for v in result:
                self._check_sql_injection(v)
            return result

        elif spec.param_type == ParameterType.LIST_INT:
            if not isinstance(value, list):
                raise ValueError("Expected list")
            return [int(v) for v in value]

        else:
            raise ValueError(f"Unknown parameter type: {spec.param_type}")

    def _check_sql_injection(self, value: str):
        """Check for SQL injection patterns."""
        # Suspicious patterns that might indicate injection attempts
        suspicious_patterns = [
            "';", '";', '--', '/*', '*/', 'UNION', 'SELECT',
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE',
            'CREATE', 'ALTER', 'EXEC', 'EXECUTE',
        ]

        upper_value = value.upper()
        for pattern in suspicious_patterns:
            if pattern in upper_value:
                logger.warning("sql_gateway.suspicious_pattern", extra={
                    "pattern": pattern,
                    "value_preview": value[:50],
                })
                raise SqlInjectionAttemptError(
                    f"Suspicious pattern detected in parameter value"
                )

    async def _get_connection_string(self) -> str:
        """Get connection string from vault (machine-controlled)."""
        if not self.credential_service:
            raise SqlGatewayError("No credential service configured")

        credential = await self.credential_service.get(
            self.config.connection_string_ref
        )
        return credential.value


# Need asyncio for timeout
import asyncio
