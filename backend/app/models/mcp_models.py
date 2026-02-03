# Layer: L7 — Platform Substrate
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: MCP (Model Context Protocol) data models for external tool servers
# Callers: L6 drivers, L5 engines
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-516, GAP-170

"""
MCP Models (PIN-516 Phase 1)

SQLAlchemy models for MCP server integration:
- McpServer: Registered external MCP servers
- McpTool: Tools exposed by MCP servers
- McpToolInvocation: Immutable audit trail of tool invocations

Phase-1 Invariants (PIN-516):
- INV-1: Models include lifecycle + versioning fields
- INV-2: Credentials stored by reference only (credential_id)
- INV-3: Invocations are immutable (enforced by DB trigger)

Tables created by migration 119_w2_mcp_servers.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


# =============================================================================
# Enums (match DB check constraints)
# =============================================================================


class McpServerStatus(str, Enum):
    """MCP server status values (ck_mcp_servers_status)."""
    PENDING = "pending"
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    DISABLED = "disabled"
    ERROR = "error"


class McpTransport(str, Enum):
    """MCP transport types (ck_mcp_servers_transport)."""
    HTTP = "http"
    HTTPS = "https"
    STDIO = "stdio"
    SSE = "sse"
    WEBSOCKET = "websocket"


class McpAuthType(str, Enum):
    """MCP authentication types (ck_mcp_servers_auth_type)."""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH = "oauth"
    BEARER = "bearer"
    BASIC = "basic"


class McpRiskLevel(str, Enum):
    """MCP tool risk levels (ck_mcp_tools_risk_level)."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class McpPolicyDecision(str, Enum):
    """Policy decision values (ck_mcp_tool_invocations_policy_decision)."""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    FLAGGED = "flagged"
    PENDING = "pending"


class McpInvocationOutcome(str, Enum):
    """Invocation outcome values (ck_mcp_tool_invocations_outcome)."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"
    PENDING = "pending"


class McpActorType(str, Enum):
    """Actor type values (ck_mcp_tool_invocations_actor_type)."""
    HUMAN = "human"
    MACHINE = "machine"
    SYSTEM = "system"


# =============================================================================
# SQLAlchemy Models (L7)
# =============================================================================


class McpServer(Base):
    """
    Registered MCP server record.

    Represents an external MCP server registered by a customer.
    Credentials are stored by REFERENCE ONLY (credential_id → vault).

    PIN-516 INV-1: Includes lifecycle fields (status, last_health_check_at).
    PIN-516 INV-3: credential_id is opaque reference, never plaintext.
    """

    __tablename__ = "mcp_servers"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(String(64), nullable=False, unique=True, index=True)

    # Identity
    tenant_id = Column(String(64), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)

    # Connection
    url = Column(String(512), nullable=False)
    transport = Column(String(32), nullable=False, default="http")
    auth_type = Column(String(32), nullable=True)
    credential_id = Column(String(64), nullable=True)  # Vault reference ONLY

    # Status (lifecycle)
    status = Column(String(32), nullable=False, default="pending")
    last_health_check_at = Column(DateTime(timezone=True), nullable=True)
    health_check_failures = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)

    # Capabilities
    capabilities = Column(JSONB, nullable=False, default=list)
    protocol_version = Column(String(16), nullable=True)

    # Discovery
    tool_count = Column(Integer, nullable=False, default=0)
    resource_count = Column(Integer, nullable=False, default=0)
    last_discovery_at = Column(DateTime(timezone=True), nullable=True)

    # Policy
    requires_approval = Column(Boolean, nullable=False, default=True)
    default_policy_id = Column(String(64), nullable=True)

    # Rate limiting
    rate_limit_requests = Column(Integer, nullable=True)
    rate_limit_window_seconds = Column(Integer, nullable=True, default=60)

    # Metadata
    tags = Column(JSONB, nullable=True, default=list)
    extra_metadata = Column("metadata", JSONB, nullable=True)  # 'metadata' is reserved in SQLAlchemy

    # Timestamps
    registered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    tools = relationship("McpTool", back_populates="server", cascade="all, delete-orphan")


class McpTool(Base):
    """
    MCP tool discovered from a server.

    Tools are discovered via MCP protocol and stored for governance.
    Each tool has a risk level and can be enabled/disabled.

    PIN-516 INV-1: Includes discovered_at timestamp.
    """

    __tablename__ = "mcp_tools"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_id = Column(String(64), nullable=False, unique=True, index=True)

    # Identity
    server_id = Column(
        String(64),
        ForeignKey("mcp_servers.server_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id = Column(String(64), nullable=False, index=True)

    # Tool definition
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)

    # Schema
    input_schema = Column(JSONB, nullable=False)
    output_schema = Column(JSONB, nullable=True)

    # Policy
    requires_policy = Column(Boolean, nullable=False, default=True)
    policy_id = Column(String(64), nullable=True)
    risk_level = Column(String(16), nullable=False, default="medium")

    # Status
    enabled = Column(Boolean, nullable=False, default=True)

    # Usage tracking
    invocation_count = Column(BigInteger, nullable=False, default=0)
    last_invoked_at = Column(DateTime(timezone=True), nullable=True)
    failure_count = Column(BigInteger, nullable=False, default=0)

    # Metadata
    extra_metadata = Column("metadata", JSONB, nullable=True)  # 'metadata' is reserved in SQLAlchemy

    # Timestamps
    discovered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    server = relationship("McpServer", back_populates="tools")


class McpToolInvocation(Base):
    """
    Immutable audit trail of MCP tool invocations.

    Every tool invocation is recorded with policy decision and outcome.
    This table is APPEND-ONLY (enforced by DB trigger).

    PIN-516 INV-1: Includes input_hash and output_hash for integrity.
    """

    __tablename__ = "mcp_tool_invocations"

    # Primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    invocation_id = Column(String(64), nullable=False, unique=True, index=True)

    # References
    tool_id = Column(
        String(64),
        ForeignKey("mcp_tools.tool_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    server_id = Column(String(64), nullable=False, index=True)
    tenant_id = Column(String(64), nullable=False, index=True)

    # Context
    run_id = Column(String(100), nullable=True, index=True)
    step_index = Column(Integer, nullable=True)
    actor_id = Column(String(100), nullable=True)
    actor_type = Column(String(32), nullable=False, default="machine")

    # Invocation details
    tool_name = Column(String(128), nullable=False)
    input_hash = Column(String(64), nullable=False)  # SHA256 for integrity
    input_preview = Column(Text, nullable=True)  # Truncated for debugging

    # Policy
    policy_id = Column(String(64), nullable=True)
    policy_snapshot_id = Column(String(64), nullable=True)
    policy_decision = Column(String(32), nullable=False, default="allowed")
    policy_reason = Column(Text, nullable=True)

    # Result
    outcome = Column(String(32), nullable=False)
    output_hash = Column(String(64), nullable=True)  # SHA256 for integrity
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)

    # Timing
    duration_ms = Column(Integer, nullable=True)

    # Timestamps
    invoked_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


# =============================================================================
# Pydantic Models (API Request/Response)
# =============================================================================


class McpServerCreate(BaseModel):
    """Input model for registering an MCP server."""

    name: str = Field(..., max_length=128)
    url: str = Field(..., max_length=512)
    description: Optional[str] = None
    transport: str = Field(default="http")
    auth_type: Optional[str] = None
    credential_ref: Optional[str] = Field(
        default=None,
        description="Vault reference for credentials (never plaintext)"
    )
    requires_approval: bool = True
    rate_limit_requests: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    extra_metadata: Optional[Dict[str, Any]] = None


class McpServerResponse(BaseModel):
    """Output model for MCP server."""

    server_id: str
    tenant_id: str
    name: str
    url: str
    description: Optional[str]
    transport: str
    auth_type: Optional[str]
    status: str
    protocol_version: Optional[str]
    tool_count: int
    resource_count: int
    requires_approval: bool
    rate_limit_requests: Optional[int]
    last_health_check_at: Optional[datetime]
    health_check_failures: int
    last_discovery_at: Optional[datetime]
    registered_at: datetime
    updated_at: datetime
    tags: List[str]

    class Config:
        from_attributes = True


class McpServerUpdate(BaseModel):
    """Input model for updating an MCP server."""

    name: Optional[str] = Field(default=None, max_length=128)
    description: Optional[str] = None
    requires_approval: Optional[bool] = None
    rate_limit_requests: Optional[int] = None
    tags: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class McpToolResponse(BaseModel):
    """Output model for MCP tool."""

    tool_id: str
    server_id: str
    name: str
    description: Optional[str]
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]]
    risk_level: str
    enabled: bool
    requires_policy: bool
    invocation_count: int
    failure_count: int
    last_invoked_at: Optional[datetime]
    discovered_at: datetime

    class Config:
        from_attributes = True


class McpToolUpdate(BaseModel):
    """Input model for updating tool settings."""

    enabled: Optional[bool] = None
    risk_level: Optional[str] = None
    policy_id: Optional[str] = None


class McpToolInvocationCreate(BaseModel):
    """Input model for recording a tool invocation."""

    tool_id: str
    server_id: str
    tenant_id: str
    run_id: Optional[str] = None
    step_index: Optional[int] = None
    actor_id: Optional[str] = None
    actor_type: str = "machine"
    tool_name: str
    input_hash: str
    input_preview: Optional[str] = None
    policy_id: Optional[str] = None
    policy_snapshot_id: Optional[str] = None
    policy_decision: str = "allowed"
    policy_reason: Optional[str] = None
    outcome: str
    output_hash: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    invoked_at: datetime
    completed_at: Optional[datetime] = None


class McpToolInvocationResponse(BaseModel):
    """Output model for tool invocation audit record."""

    invocation_id: str
    tool_id: Optional[str]
    server_id: str
    tenant_id: str
    run_id: Optional[str]
    tool_name: str
    policy_decision: str
    outcome: str
    error_code: Optional[str]
    error_message: Optional[str]
    duration_ms: Optional[int]
    invoked_at: datetime
    completed_at: Optional[datetime]
    recorded_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Utility Types
# =============================================================================


class McpServerHealthStatus(BaseModel):
    """Health check result for an MCP server."""

    server_id: str
    status: str
    is_healthy: bool
    last_check_at: datetime
    failure_count: int
    error: Optional[str] = None


class McpToolDiscoveryResult(BaseModel):
    """Result of tool discovery for an MCP server."""

    server_id: str
    discovered_at: datetime
    tools_found: int
    tools_added: int
    tools_updated: int
    tools_removed: int
    errors: List[str] = Field(default_factory=list)
