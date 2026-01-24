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
- POST /api/v1/notifications (send notification)
- GET /api/v1/notifications (list notifications)
- GET /api/v1/notifications/{id} (get notification)
- POST /api/v1/notifications/{id}/read (mark as read)
- GET /api/v1/notifications/channels (list channels)
- GET /api/v1/notifications/preferences (get preferences)
- PUT /api/v1/notifications/preferences (update preferences)

This is the ONLY facade for notification operations.
All notification APIs flow through this router.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.auth.tenant_auth import TenantContext, get_tenant_context
from app.auth.tier_gating import requires_feature
from app.schemas.response import wrap_dict
from app.services.notifications.facade import (
    NotificationsFacade,
    get_notifications_facade,
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
# Dependencies
# =============================================================================


def get_facade() -> NotificationsFacade:
    """Get the notifications facade."""
    return get_notifications_facade()


# =============================================================================
# Endpoints
# =============================================================================


@router.post("", response_model=Dict[str, Any])
async def send_notification(
    request: SendNotificationRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: NotificationsFacade = Depends(get_facade),
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
    notification = await facade.send_notification(
        tenant_id=ctx.tenant_id,
        channel=request.channel,
        recipient=request.recipient,
        message=request.message,
        subject=request.subject,
        priority=request.priority,
        metadata=request.metadata,
    )

    return wrap_dict(notification.to_dict())


@router.get("", response_model=Dict[str, Any])
async def list_notifications(
    channel: Optional[str] = Query(None, description="Filter by channel"),
    status: Optional[str] = Query(None, description="Filter by status"),
    recipient: Optional[str] = Query(None, description="Filter by recipient"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    ctx: TenantContext = Depends(get_tenant_context),
    facade: NotificationsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("notifications.read")),
):
    """
    List notifications for the tenant.
    """
    notifications = await facade.list_notifications(
        tenant_id=ctx.tenant_id,
        channel=channel,
        status=status,
        recipient=recipient,
        limit=limit,
        offset=offset,
    )

    return wrap_dict({
        "notifications": [n.to_dict() for n in notifications],
        "total": len(notifications),
        "limit": limit,
        "offset": offset,
    })


@router.get("/channels", response_model=Dict[str, Any])
async def list_channels(
    ctx: TenantContext = Depends(get_tenant_context),
    facade: NotificationsFacade = Depends(get_facade),
):
    """
    List available notification channels.
    """
    channels = await facade.list_channels()

    return wrap_dict({
        "channels": [c.to_dict() for c in channels],
    })


@router.get("/preferences", response_model=Dict[str, Any])
async def get_preferences(
    ctx: TenantContext = Depends(get_tenant_context),
    facade: NotificationsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("notifications.read")),
):
    """
    Get notification preferences for the current user.
    """
    user_id = ctx.user_id or "default"
    prefs = await facade.get_preferences(
        tenant_id=ctx.tenant_id,
        user_id=user_id,
    )

    return wrap_dict(prefs.to_dict())


@router.put("/preferences", response_model=Dict[str, Any])
async def update_preferences(
    request: UpdatePreferencesRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: NotificationsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("notifications.write")),
):
    """
    Update notification preferences for the current user.
    """
    user_id = ctx.user_id or "default"
    prefs = await facade.update_preferences(
        tenant_id=ctx.tenant_id,
        user_id=user_id,
        channels=request.channels,
        priorities=request.priorities,
    )

    return wrap_dict(prefs.to_dict())


@router.get("/{notification_id}", response_model=Dict[str, Any])
async def get_notification(
    notification_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: NotificationsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("notifications.read")),
):
    """
    Get a specific notification.
    """
    notification = await facade.get_notification(
        notification_id=notification_id,
        tenant_id=ctx.tenant_id,
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return wrap_dict(notification.to_dict())


@router.post("/{notification_id}/read", response_model=Dict[str, Any])
async def mark_as_read(
    notification_id: str,
    ctx: TenantContext = Depends(get_tenant_context),
    facade: NotificationsFacade = Depends(get_facade),
    _tier: None = Depends(requires_feature("notifications.write")),
):
    """
    Mark a notification as read.
    """
    notification = await facade.mark_as_read(
        notification_id=notification_id,
        tenant_id=ctx.tenant_id,
    )

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return wrap_dict(notification.to_dict())
