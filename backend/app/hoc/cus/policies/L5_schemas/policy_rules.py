# capability_id: CAP-009
# Layer: L5 — Domain Schema
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Role: Policy rules request/response schemas
# Callers: api/policies.py, services/limits/policy_rules_service.py
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-LIM-02

"""
Policy Rules Schemas (PIN-LIM-02)

Request and response models for policy rule CRUD operations.
Rules define governance constraints that govern LLM Run behavior.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class EnforcementModeEnum(str):
    """Policy rule enforcement modes."""
    BLOCK = "BLOCK"
    WARN = "WARN"
    AUDIT = "AUDIT"
    DISABLED = "DISABLED"


class PolicyScopeEnum(str):
    """Policy rule scope levels."""
    GLOBAL = "GLOBAL"
    TENANT = "TENANT"
    PROJECT = "PROJECT"
    AGENT = "AGENT"


class PolicySourceEnum(str):
    """Policy rule creation source."""
    MANUAL = "MANUAL"
    SYSTEM = "SYSTEM"
    LEARNED = "LEARNED"


class CreatePolicyRuleRequest(BaseModel):
    """Request model for creating a policy rule."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=256,
        description="Human-readable rule name",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1024,
        description="Optional rule description",
    )
    enforcement_mode: str = Field(
        default="WARN",
        pattern="^(BLOCK|WARN|AUDIT|DISABLED)$",
        description="Enforcement mode: BLOCK, WARN, AUDIT, DISABLED",
    )
    scope: str = Field(
        default="TENANT",
        pattern="^(GLOBAL|TENANT|PROJECT|AGENT)$",
        description="Scope level: GLOBAL, TENANT, PROJECT, AGENT",
    )
    scope_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Specific entity ID for non-GLOBAL scope",
    )
    conditions: Optional[dict[str, Any]] = Field(
        default=None,
        description="Rule conditions as JSON (optional)",
    )
    source: str = Field(
        default="MANUAL",
        pattern="^(MANUAL|SYSTEM|LEARNED)$",
        description="Rule source: MANUAL, SYSTEM, LEARNED",
    )
    source_proposal_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="ID of source proposal if LEARNED",
    )
    parent_rule_id: Optional[str] = Field(
        default=None,
        description="Parent rule ID for rule hierarchy",
    )


class UpdatePolicyRuleRequest(BaseModel):
    """Request model for updating a policy rule."""

    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=256,
        description="Updated rule name",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1024,
        description="Updated description",
    )
    enforcement_mode: Optional[str] = Field(
        default=None,
        pattern="^(BLOCK|WARN|AUDIT|DISABLED)$",
        description="Updated enforcement mode",
    )
    conditions: Optional[dict[str, Any]] = Field(
        default=None,
        description="Updated rule conditions",
    )
    status: Optional[str] = Field(
        default=None,
        pattern="^(ACTIVE|RETIRED)$",
        description="Updated status: ACTIVE or RETIRED",
    )
    retirement_reason: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Reason for retirement (if retiring)",
    )
    superseded_by: Optional[str] = Field(
        default=None,
        description="ID of rule that supersedes this one",
    )


class PolicyRuleResponse(BaseModel):
    """Response model for policy rule operations."""

    rule_id: str = Field(description="Unique rule identifier")
    tenant_id: str = Field(description="Owning tenant ID")
    name: str = Field(description="Rule name")
    description: Optional[str] = Field(default=None, description="Rule description")
    enforcement_mode: str = Field(description="Enforcement mode")
    scope: str = Field(description="Scope level")
    scope_id: Optional[str] = Field(default=None, description="Scope entity ID")
    conditions: Optional[dict[str, Any]] = Field(default=None, description="Rule conditions")
    status: str = Field(description="Rule status")
    source: str = Field(description="Rule source")
    source_proposal_id: Optional[str] = Field(default=None, description="Source proposal ID")
    parent_rule_id: Optional[str] = Field(default=None, description="Parent rule ID")
    created_at: datetime = Field(description="Creation timestamp")
    created_by: Optional[str] = Field(default=None, description="Creator user ID")
    updated_at: datetime = Field(description="Last update timestamp")
    retired_at: Optional[datetime] = Field(default=None, description="Retirement timestamp")
    retired_by: Optional[str] = Field(default=None, description="User who retired the rule")
    retirement_reason: Optional[str] = Field(default=None, description="Reason for retirement")
    superseded_by: Optional[str] = Field(default=None, description="Superseding rule ID")

    class Config:
        from_attributes = True
