# Layer: L4 — Domain Engines
# Product: system-wide
# Role: MCP (Model Context Protocol) services package
# Reference: GAP-141, GAP-142, GAP-143

"""
MCP services for external server integration.

Provides:
- Server registration and discovery (GAP-141)
- Tool→Policy mapping (GAP-142)
- Audit evidence emission (GAP-143)
"""

from app.services.mcp.server_registry import (
    MCPServerRegistry,
    MCPServer,
    MCPServerStatus,
    MCPTool,
    get_mcp_registry,
    configure_mcp_registry,
)

from app.services.mcp.policy_mapper import (
    MCPPolicyMapper,
    MCPPolicyDecision,
    get_mcp_policy_mapper,
)

from app.services.mcp.audit_evidence import (
    MCPAuditEmitter,
    MCPAuditEvent,
    MCPAuditEventType,
    get_mcp_audit_emitter,
)

__all__ = [
    # GAP-141: Server Registry
    "MCPServerRegistry",
    "MCPServer",
    "MCPServerStatus",
    "MCPTool",
    "get_mcp_registry",
    "configure_mcp_registry",
    # GAP-142: Policy Mapper
    "MCPPolicyMapper",
    "MCPPolicyDecision",
    "get_mcp_policy_mapper",
    # GAP-143: Audit Evidence
    "MCPAuditEmitter",
    "MCPAuditEvent",
    "MCPAuditEventType",
    "get_mcp_audit_emitter",
]
