# Layer: L2 — Product APIs
# Product: system-wide (NOT console-only - SDK users call this)
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Unified NOTIFICATIONS facade - L2 API for notification operations
# Callers: Console, SDK, external systems
# Allowed Imports: L3, L4, L6
# Forbidden Imports: L1, L5
# Reference: GAP-109 (Notification API)
# GOVERNANCE NOTE:
# This is the ONE facade for NOTIFICATIONS domain.
# All notification flows through this API.
# SDSR tests this same API - no separate SDSR endpoints.

"""
Notifications API (L2)

Provides notification operations:
- POST /notifications (send notification)
- GET /notifications (list notifications)
- GET /notifications/{id} (get notification)
- POST /notifications/{id}/read (mark as read)
- GET /notifications/channels (list channels)
- GET /notifications/preferences (get preferences)
- PUT /notifications/preferences (update preferences)

This is the ONLY facade for notification operations.
All notification APIs flow through this router.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    OperationContext,
    get_operation_registry,
)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# =============================================================================
# Request/Response Models
# =============================================================================


class SendNotificationRequest(BaseModel):
    """Request to send notification."""
    channel: str = Field(..., description="Channel: email, slack, webhook, in_app, sms")
    recipient: str = Field(..., description="Recipient identifier")
    message: str = Field(..., description="Notification message")
    subject: Optional[str] = Field(None, description="Subject (for email)")
    priority: str = Field("normal", description="Priority: low, normal, high, urgent")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class UpdatePreferencesRequest(BaseModel):
    """Request to update notification preferences."""
    channels: Optional[Dict[str, bool]] = Field(None, description="Channel enable/disable")
    priorities: Optional[Dict[str, List[str]]] = Field(None, description="Priority settings")


# =============================================================================
# Endpoints
# =============================================================================


@router.post("", response_model=Dict[str, Any])
async def send_notification(
    request: SendNotificationRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("notifications.send")),
):
    """
    Send a notification (GAP-109).

    **Tier: REACT ($9)** - Notification sending.

    Channels:
    - email: Email notifications
    - slack: Slack messages
    - webhook: Webhook callbacks
    - in_app: In-app notifications
    - sms: SMS messages (requires configuration)
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "account.notifications",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "send_notification",
                "channel": request.channel,
                "recipient": request.recipient,
                "message": request.message,
                "subject": request.subject,
                "priority": request.priority,
                "metadata": request.metadata,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    notification = op.data
    return wrap_dict(notification.to_dict())


@router.get("", response_model=Dict[str, Any])
async def list_notifications(
    channel: Optional[str] = Query(None, description="Filter by channel"),
    status: Optional[str] = Query(None, description="Filter by status"),
    recipient: Optional[str] = Query(None, description="Filter by recipient"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("notifications.read")),
):
    """
    List notifications for the tenant.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "account.notifications",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "list_notifications",
                "channel": channel,
                "status": status,
                "recipient": recipient,
                "limit": limit,
                "offset": offset,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    notifications = op.data
    return wrap_dict({
        "notifications": [n.to_dict() for n in notifications],
        "total": len(notifications),
        "limit": limit,
        "offset": offset,
    })


@router.get("/channels", response_model=Dict[str, Any])
async def list_channels(
    ctx: TenantContext = Depends(get_tenant_context),
):
    """
    List available notification channels.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "account.notifications",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={"method": "list_channels"},
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    channels = op.data
    return wrap_dict({
        "channels": [c.to_dict() for c in channels],
    })


@router.get("/preferences", response_model=Dict[str, Any])
async def get_preferences(
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("notifications.read")),
):
    """
    Get notification preferences for the current user.
    """
    user_id = ctx.user_id or "default"
    registry = get_operation_registry()
    op = await registry.execute(
        "account.notifications",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "get_preferences",
                "user_id": user_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    prefs = op.data
    return wrap_dict(prefs.to_dict())


@router.put("/preferences", response_model=Dict[str, Any])
async def update_preferences(
    request: UpdatePreferencesRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("notifications.write")),
):
    """
    Update notification preferences for the current user.
    """
    user_id = ctx.user_id or "default"
    registry = get_operation_registry()
    op = await registry.execute(
        "account.notifications",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "update_preferences",
                "user_id": user_id,
                "channels": request.channels,
                "priorities": request.priorities,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    prefs = op.data
    return wrap_dict(prefs.to_dict())


@router.get("/{notification_id}", response_model=Dict[str, Any])
async def get_notification(
    notification_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("notifications.read")),
):
    """
    Get a specific notification.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "account.notifications",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "get_notification",
                "notification_id": notification_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    notification = op.data
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return wrap_dict(notification.to_dict())


@router.post("/{notification_id}/read", response_model=Dict[str, Any])
async def mark_as_read(
    notification_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    _tier: None = Depends(requires_feature("notifications.write")),
):
    """
    Mark a notification as read.
    """
    registry = get_operation_registry()
    op = await registry.execute(
        "account.notifications",
        OperationContext(
            session=None,
            tenant_id=ctx.tenant_id,
            params={
                "method": "mark_as_read",
                "notification_id": notification_id,
            },
        ),
    )
    if not op.success:
        raise HTTPException(status_code=500, detail={"error": "operation_failed", "message": op.error})

    notification = op.data
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return wrap_dict(notification.to_dict())
