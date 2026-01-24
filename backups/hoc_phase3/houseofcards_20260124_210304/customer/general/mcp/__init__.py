# Layer: L5 — Domain Engines
# AUDIENCE: CUSTOMER
# Role: MCP (Model Context Protocol) cross-domain services
# Reference: HOC_LAYER_TOPOLOGY_V1.md, INTEGRATIONS_PHASE2.5_IMPLEMENTATION_PLAN.md

"""
customer / general / mcp

Cross-domain MCP services for the customer audience.
Contains shared MCP infrastructure used across customer domains.
"""

from .server_registry import (
    MCPCapability,
    MCPRegistrationResult,
    MCPServer,
    MCPServerRegistry,
    MCPServerStatus,
    MCPTool,
    configure_mcp_registry,
    get_mcp_registry,
    reset_mcp_registry,
)

__all__ = [
    "MCPCapability",
    "MCPRegistrationResult",
    "MCPServer",
    "MCPServerRegistry",
    "MCPServerStatus",
    "MCPTool",
    "configure_mcp_registry",
    "get_mcp_registry",
    "reset_mcp_registry",
]
