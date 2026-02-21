# capability_id: CAP-005
# Layer: L2 — API Endpoint
# AUDIENCE: FOUNDER
# Role: Founder Actions API - M29 Category 6
"""Founder Actions API - M29 Category 6

PIN-151: M29 Categories 4-6 - Founder Action Paths

This router provides endpoints for founder actions on the Ops Console.
All actions are audited, rate-limited, and require MFA verification.

Endpoints:
- POST /ops/actions/freeze-tenant     - Immediately block all API calls for tenant
- POST /ops/actions/throttle-tenant   - Reduce tenant rate limit to 10% of normal
- POST /ops/actions/freeze-api-key    - Immediately revoke specific API key
- POST /ops/actions/override-incident - Mark incident as false positive

Reversal Endpoints:
- POST /ops/actions/unfreeze-tenant   - Restore tenant access
- POST /ops/actions/unthrottle-tenant - Restore tenant rate limit
- POST /ops/actions/unfreeze-api-key  - Restore API key

INVARIANTS:
1. Every action writes an immutable audit record (no audit → API fails)
2. Founders cannot freeze AND throttle the same tenant simultaneously
3. All actions are reversible EXCEPT override-incident
4. Customer tokens are rejected (must be FOPS token with MFA)
5. Rate limited: N actions per founder per hour
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.auth.console_auth import FounderToken, verify_fops_token
from app.contracts.ops import (
    FounderActionListDTO,
    FounderActionRequestDTO,
    FounderActionResponseDTO,
    FounderActionSummaryDTO,
    FounderAuditRecordDTO,
    FounderReversalRequestDTO,
)
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import (
    get_sync_session_dep,
    sql_text,
)
from app.hoc.fdr.ops.engines.founder_action_write_engine import FounderActionWriteService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ops/actions",
    tags=["founder-actions"],
)

# =============================================================================
# SAFETY RAILS CONFIGURATION
# =============================================================================

# Rate limit: max actions per founder per hour
MAX_ACTIONS_PER_HOUR = 10

# Action-to-reversal mapping
REVERSAL_MAP = {
    "FREEZE_TENANT": "UNFREEZE_TENANT",
    "THROTTLE_TENANT": "UNTHROTTLE_TENANT",
    "FREEZE_API_KEY": "UNFREEZE_API_KEY",  # pragma: allowlist secret
}

# Reversible actions (OVERRIDE_INCIDENT is NOT reversible)
REVERSIBLE_ACTIONS = {"FREEZE_TENANT", "THROTTLE_TENANT", "FREEZE_API_KEY"}

# Mutually exclusive actions (cannot have both active on same target)
# Rule: FREEZE wins over THROTTLE
# - Cannot THROTTLE a frozen tenant (blocked)
# - CAN FREEZE a throttled tenant (freeze wins, throttle auto-superseded)
MUTUALLY_EXCLUSIVE = {
    ("THROTTLE_TENANT", "FREEZE_TENANT"),  # Cannot throttle frozen tenant
    # NOTE: ("FREEZE_TENANT", "THROTTLE_TENANT") is NOT here because freeze wins
}


# =============================================================================
# SAFETY RAIL HELPERS
# =============================================================================


def check_rate_limit(
    session,
    founder_id: str,
) -> bool:
    """Check if founder has exceeded rate limit. Returns True if allowed."""
    query = sql_text(
        """
        SELECT COUNT(*) FROM founder_actions
        WHERE founder_id = :founder_id
        AND applied_at > NOW() - INTERVAL '1 hour'
    """
    )
    result = session.execute(query, {"founder_id": founder_id})
    count = result.scalar() or 0
    return count < MAX_ACTIONS_PER_HOUR


def check_duplicate_action(
    session,
    action_type: str,
    target_id: str,
) -> bool:
    """
    Check if same action is already active on target.
    Returns True if duplicate found (should reject).

    Examples:
    - Freeze frozen tenant → True (conflict)
    - Throttle throttled tenant → True (conflict)
    - Freeze same API key twice → True (conflict)
    """
    query = sql_text(
        """
        SELECT id FROM founder_actions
        WHERE action_type = :action_type
        AND target_id = :target_id
        AND is_active = true
        LIMIT 1
    """
    )
    result = session.execute(
        query,
        {
            "action_type": action_type,
            "target_id": target_id,
        },
    )
    return result.fetchone() is not None


def check_mutual_exclusion(
    session,
    action_type: str,
    target_id: str,
) -> Optional[str]:
    """
    Check for mutually exclusive active actions.
    Returns conflicting action_type if found, None otherwise.

    Rules:
    - FREEZE + THROTTLE are mutually exclusive
    - But FREEZE wins over THROTTLE (allowed to freeze throttled tenant)
    """
    for exclusive_pair in MUTUALLY_EXCLUSIVE:
        if action_type == exclusive_pair[0]:
            conflicting_type = exclusive_pair[1]
            query = sql_text(
                """
                SELECT id FROM founder_actions
                WHERE action_type = :action_type
                AND target_id = :target_id
                AND is_active = true
                LIMIT 1
            """
            )
            result = session.execute(
                query,
                {
                    "action_type": conflicting_type,
                    "target_id": target_id,
                },
            )
            if result.fetchone():
                return conflicting_type
    return None


def get_target_name(
    session,
    target_type: str,
    target_id: str,
) -> Optional[str]:
    """Get display name for target."""
    if target_type == "TENANT":
        query = sql_text("SELECT name FROM tenants WHERE id = :id")
    elif target_type == "API_KEY":
        query = sql_text("SELECT name FROM api_keys WHERE id = :id")
    else:
        return None

    result = session.execute(query, {"id": target_id})
    row = result.fetchone()
    return row[0] if row else None


def validate_target_exists(
    session,
    target_type: str,
    target_id: str,
) -> bool:
    """Validate that target exists."""
    if target_type == "TENANT":
        query = sql_text("SELECT 1 FROM tenants WHERE id = :id")
    elif target_type == "API_KEY":
        query = sql_text("SELECT 1 FROM api_keys WHERE id = :id")
    elif target_type == "INCIDENT":
        query = sql_text("SELECT 1 FROM incidents WHERE id = :id")
    else:
        return False

    result = session.execute(query, {"id": target_id})
    return result.fetchone() is not None


def apply_action_effect(
    session,
    action_type: str,
    target_type: str,
    target_id: str,
) -> bool:
    """
    Apply the actual effect of an action.
    Returns True if successful.
    """
    try:
        if action_type == "FREEZE_TENANT":
            session.execute(sql_text("UPDATE tenants SET status = 'frozen' WHERE id = :id"), {"id": target_id})
        elif action_type == "THROTTLE_TENANT":
            # Set throttle factor to 10% (0.1)
            session.execute(sql_text("UPDATE tenants SET throttle_factor = 0.1 WHERE id = :id"), {"id": target_id})
        elif action_type == "FREEZE_API_KEY":
            session.execute(sql_text("UPDATE api_keys SET status = 'revoked' WHERE id = :id"), {"id": target_id})
        elif action_type == "OVERRIDE_INCIDENT":
            session.execute(
                sql_text(
                    """
                    UPDATE incidents
                    SET status = 'resolved',
                        resolution = 'false_positive',
                        resolved_at = NOW()
                    WHERE id = :id
                """
                ),
                {"id": target_id},
            )
        elif action_type == "UNFREEZE_TENANT":
            session.execute(sql_text("UPDATE tenants SET status = 'active' WHERE id = :id"), {"id": target_id})
        elif action_type == "UNTHROTTLE_TENANT":
            session.execute(sql_text("UPDATE tenants SET throttle_factor = 1.0 WHERE id = :id"), {"id": target_id})
        elif action_type == "UNFREEZE_API_KEY":
            session.execute(sql_text("UPDATE api_keys SET status = 'active' WHERE id = :id"), {"id": target_id})
        return True
    except Exception as e:
        logger.error(f"Failed to apply action {action_type}: {e}")
        return False


# =============================================================================
# CORE ACTION ENDPOINT
# =============================================================================


async def execute_action(
    request: FounderActionRequestDTO,
    token: FounderToken,
    session,
) -> FounderActionResponseDTO:
    """
    Core action execution logic shared by all action endpoints.

    Flow:
    1. Validate MFA verified
    2. Check rate limit
    3. Check mutual exclusion
    4. Validate target exists
    5. Write audit record FIRST
    6. Apply action effect
    7. Return response
    """
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # Step 1: Validate MFA
    if not token.mfa:
        return FounderActionResponseDTO(
            status="REJECTED",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message="MFA verification required for founder actions",
        )

    # Step 2: Check rate limit
    if not check_rate_limit(session, token.sub):
        return FounderActionResponseDTO(
            status="RATE_LIMITED",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message=f"Rate limit exceeded: max {MAX_ACTIONS_PER_HOUR} actions per hour",
        )

    # Step 3: Check duplicate action (same action already active)
    if check_duplicate_action(session, request.action, request.target.id):
        return FounderActionResponseDTO(
            status="CONFLICT",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message=f"{request.action} is already active on this target",
        )

    # Step 4: Check mutual exclusion (freeze vs throttle)
    conflicting = check_mutual_exclusion(
        session,
        request.action,
        request.target.id,
    )
    if conflicting:
        return FounderActionResponseDTO(
            status="CONFLICT",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message=f"Cannot {request.action} while {conflicting} is active on this target",
        )

    # Step 4: Validate target exists
    if not validate_target_exists(session, request.target.type, request.target.id):
        return FounderActionResponseDTO(
            status="REJECTED",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message=f"Target {request.target.type} with id {request.target.id} not found",
        )

    # Get target name for audit
    target_name = get_target_name(session, request.target.type, request.target.id)

    # Determine reversibility
    is_reversible = request.action in REVERSIBLE_ACTIONS

    # Phase 2B: Use write service for DB operations
    write_service = FounderActionWriteService(session)

    # Step 5: Write audit record FIRST (immutable)
    action = write_service.create_founder_action(
        action_type=request.action,
        target_type=request.target.type,
        target_id=request.target.id,
        target_name=target_name,
        reason_code=request.reason.code,
        reason_note=request.reason.note,
        source_incident_id=request.source_incident_id,
        founder_id=token.sub,
        founder_email=token.email,
        mfa_verified=token.mfa,
        is_reversible=is_reversible,
    )

    # Step 6: Apply action effect
    success = apply_action_effect(
        session,
        request.action,
        request.target.type,
        request.target.id,
    )

    if not success:
        write_service.rollback()
        return FounderActionResponseDTO(
            status="REJECTED",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message="Failed to apply action effect",
        )

    write_service.commit()

    # Build undo hint
    undo_hint = None
    if is_reversible:
        reversal = REVERSAL_MAP.get(request.action)
        if reversal:
            undo_hint = f"Use POST /ops/actions/{reversal.lower().replace('_', '-')} with action_id={action.id}"

    logger.info(
        f"Founder action applied: {request.action} on {request.target.type}:{request.target.id} "
        f"by {token.email} (action_id={action.id})"
    )

    return FounderActionResponseDTO(
        status="APPLIED",
        action_id=action.id,
        applied_at=now_iso,
        reversible=is_reversible,
        undo_hint=undo_hint,
        message=None,
    )


# =============================================================================
# ACTION ENDPOINTS (4 total)
# =============================================================================


@router.post(
    "/freeze-tenant",
    response_model=FounderActionResponseDTO,
    summary="Freeze tenant - block all API calls",
    description="Immediately block all API calls for a tenant. Reversible via unfreeze-tenant.",
)
async def freeze_tenant(
    request: FounderActionRequestDTO,
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_sync_session_dep),
) -> FounderActionResponseDTO:
    """Freeze tenant - immediately block all API calls."""
    # Validate action type matches endpoint
    if request.action != "FREEZE_TENANT":
        raise HTTPException(
            status_code=400,
            detail=f"This endpoint only accepts FREEZE_TENANT action, got {request.action}",
        )
    if request.target.type != "TENANT":
        raise HTTPException(
            status_code=400,
            detail=f"FREEZE_TENANT requires TENANT target, got {request.target.type}",
        )
    return await execute_action(request, token, session)


@router.post(
    "/throttle-tenant",
    response_model=FounderActionResponseDTO,
    summary="Throttle tenant - reduce rate limit to 10%",
    description="Reduce tenant rate limit to 10% of normal. Reversible via unthrottle-tenant.",
)
async def throttle_tenant(
    request: FounderActionRequestDTO,
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_sync_session_dep),
) -> FounderActionResponseDTO:
    """Throttle tenant - reduce rate limit to 10%."""
    if request.action != "THROTTLE_TENANT":
        raise HTTPException(
            status_code=400,
            detail=f"This endpoint only accepts THROTTLE_TENANT action, got {request.action}",
        )
    if request.target.type != "TENANT":
        raise HTTPException(
            status_code=400,
            detail=f"THROTTLE_TENANT requires TENANT target, got {request.target.type}",
        )
    return await execute_action(request, token, session)


@router.post(
    "/freeze-api-key",
    response_model=FounderActionResponseDTO,
    summary="Freeze API key - immediately revoke",
    description="Immediately revoke a specific API key. Reversible via unfreeze-api-key.",
)
async def freeze_api_key(
    request: FounderActionRequestDTO,
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_sync_session_dep),
) -> FounderActionResponseDTO:
    """Freeze API key - immediately revoke."""
    if request.action != "FREEZE_API_KEY":
        raise HTTPException(
            status_code=400,
            detail=f"This endpoint only accepts FREEZE_API_KEY action, got {request.action}",
        )
    if request.target.type != "API_KEY":
        raise HTTPException(
            status_code=400,
            detail=f"FREEZE_API_KEY requires API_KEY target, got {request.target.type}",
        )
    return await execute_action(request, token, session)


@router.post(
    "/override-incident",
    response_model=FounderActionResponseDTO,
    summary="Override incident - mark as false positive",
    description="Mark incident as false positive and close it. NOT REVERSIBLE.",
)
async def override_incident(
    request: FounderActionRequestDTO,
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_sync_session_dep),
) -> FounderActionResponseDTO:
    """Override incident - mark as false positive. NOT REVERSIBLE."""
    if request.action != "OVERRIDE_INCIDENT":
        raise HTTPException(
            status_code=400,
            detail=f"This endpoint only accepts OVERRIDE_INCIDENT action, got {request.action}",
        )
    if request.target.type != "INCIDENT":
        raise HTTPException(
            status_code=400,
            detail=f"OVERRIDE_INCIDENT requires INCIDENT target, got {request.target.type}",
        )
    return await execute_action(request, token, session)


# =============================================================================
# REVERSAL ENDPOINTS (3 total)
# =============================================================================


async def execute_reversal(
    request: FounderReversalRequestDTO,
    reversal_type: str,
    token: FounderToken,
    session,
) -> FounderActionResponseDTO:
    """
    Core reversal execution logic.

    Flow:
    1. Validate MFA verified
    2. Check rate limit
    3. Find original action
    4. Validate action is reversible
    5. Write reversal audit record
    6. Apply reversal effect
    7. Mark original action as reversed
    """
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat()

    # Step 1: Validate MFA
    if not token.mfa:
        return FounderActionResponseDTO(
            status="REJECTED",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message="MFA verification required for founder actions",
        )

    # Step 2: Check rate limit
    if not check_rate_limit(session, token.sub):
        return FounderActionResponseDTO(
            status="RATE_LIMITED",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message=f"Rate limit exceeded: max {MAX_ACTIONS_PER_HOUR} actions per hour",
        )

    # Step 3: Find original action
    query = sql_text(
        """
        SELECT id, action_type, target_type, target_id, target_name,
               reason_code, is_active, is_reversible
        FROM founder_actions
        WHERE id = :action_id
    """
    )
    result = session.execute(query, {"action_id": request.action_id})
    original = result.fetchone()

    if not original:
        return FounderActionResponseDTO(
            status="REJECTED",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message=f"Original action {request.action_id} not found",
        )

    # Step 4: Validate action is reversible
    if not original.is_reversible:
        return FounderActionResponseDTO(
            status="REJECTED",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message=f"Action {request.action_id} is not reversible",
        )

    if not original.is_active:
        return FounderActionResponseDTO(
            status="REJECTED",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message=f"Action {request.action_id} is already reversed",
        )

    # Validate reversal type matches original action
    expected_reversal = REVERSAL_MAP.get(original.action_type)
    if expected_reversal != reversal_type:
        return FounderActionResponseDTO(
            status="REJECTED",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message=f"Cannot use {reversal_type} to reverse {original.action_type}",
        )

    # Phase 2B: Use write service for DB operations
    write_service = FounderActionWriteService(session)

    # Step 5: Write reversal audit record
    reversal_action = write_service.create_founder_action(
        action_type=reversal_type,
        target_type=original.target_type,
        target_id=original.target_id,
        target_name=original.target_name,
        reason_code="FALSE_POSITIVE" if not request.reason else "OTHER",
        reason_note=request.reason,
        source_incident_id=None,
        founder_id=token.sub,
        founder_email=token.email,
        mfa_verified=token.mfa,
        is_reversible=False,  # Reversals are not reversible
    )

    # Step 6: Apply reversal effect
    success = apply_action_effect(
        session,
        reversal_type,
        original.target_type,
        original.target_id,
    )

    if not success:
        write_service.rollback()
        return FounderActionResponseDTO(
            status="REJECTED",
            action_id="",
            applied_at=now_iso,
            reversible=False,
            undo_hint=None,
            message="Failed to apply reversal effect",
        )

    # Step 7: Mark original action as reversed
    write_service.mark_action_reversed(
        action_id=request.action_id,
        reversed_at=now,
        reversed_by_action_id=reversal_action.id,
    )

    write_service.commit()

    logger.info(
        f"Founder action reversed: {reversal_type} on {original.target_type}:{original.target_id} "
        f"by {token.email} (reversal_id={reversal_action.id}, original_id={request.action_id})"
    )

    return FounderActionResponseDTO(
        status="APPLIED",
        action_id=reversal_action.id,
        applied_at=now_iso,
        reversible=False,
        undo_hint=None,
        message=f"Successfully reversed action {request.action_id}",
    )


@router.post(
    "/unfreeze-tenant",
    response_model=FounderActionResponseDTO,
    summary="Unfreeze tenant - restore access",
    description="Restore tenant access after a freeze. Requires the action_id of the original freeze.",
)
async def unfreeze_tenant(
    request: FounderReversalRequestDTO,
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_sync_session_dep),
) -> FounderActionResponseDTO:
    """Unfreeze tenant - restore access."""
    return await execute_reversal(request, "UNFREEZE_TENANT", token, session)


@router.post(
    "/unthrottle-tenant",
    response_model=FounderActionResponseDTO,
    summary="Unthrottle tenant - restore rate limit",
    description="Restore tenant rate limit after a throttle. Requires the action_id of the original throttle.",
)
async def unthrottle_tenant(
    request: FounderReversalRequestDTO,
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_sync_session_dep),
) -> FounderActionResponseDTO:
    """Unthrottle tenant - restore rate limit."""
    return await execute_reversal(request, "UNTHROTTLE_TENANT", token, session)


@router.post(
    "/unfreeze-api-key",
    response_model=FounderActionResponseDTO,
    summary="Unfreeze API key - restore access",
    description="Restore API key access after a freeze. Requires the action_id of the original freeze.",
)
async def unfreeze_api_key(
    request: FounderReversalRequestDTO,
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_sync_session_dep),
) -> FounderActionResponseDTO:
    """Unfreeze API key - restore access."""
    return await execute_reversal(request, "UNFREEZE_API_KEY", token, session)


# =============================================================================
# AUDIT TRAIL ENDPOINTS
# =============================================================================


@router.get(
    "/audit",
    response_model=FounderActionListDTO,
    summary="Get founder action audit trail",
    description="Get list of recent founder actions for audit purposes.",
)
async def get_audit_trail(
    page: int = 1,
    page_size: int = 50,
    target_id: Optional[str] = None,
    action_type: Optional[str] = None,
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_sync_session_dep),
) -> FounderActionListDTO:
    """Get founder action audit trail."""
    offset = (page - 1) * page_size

    # Build query with optional filters
    where_clauses = []
    params = {"limit": page_size, "offset": offset}

    if target_id:
        where_clauses.append("target_id = :target_id")
        params["target_id"] = target_id
    if action_type:
        where_clauses.append("action_type = :action_type")
        params["action_type"] = action_type

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Get total count
    count_query = sql_text(f"SELECT COUNT(*) FROM founder_actions WHERE {where_sql}")
    total_count = session.execute(count_query, params).scalar() or 0

    # Get actions
    query = sql_text(
        f"""
        SELECT id, action_type, target_type, target_id, target_name,
               reason_code, founder_email, applied_at, is_active,
               reversed_at IS NOT NULL as is_reversed
        FROM founder_actions
        WHERE {where_sql}
        ORDER BY applied_at DESC
        LIMIT :limit OFFSET :offset
    """
    )
    result = session.execute(query, params)

    actions = []
    for row in result:
        actions.append(
            FounderActionSummaryDTO(
                action_id=row.id,
                action_type=row.action_type,
                target_type=row.target_type,
                target_id=row.target_id,
                target_name=row.target_name,
                reason_code=row.reason_code,
                founder_email=row.founder_email,
                applied_at=row.applied_at.isoformat() if row.applied_at else "",
                is_reversed=row.is_reversed,
                is_active=row.is_active,
            )
        )

    return FounderActionListDTO(
        actions=actions,
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/audit/{action_id}",
    response_model=FounderAuditRecordDTO,
    summary="Get single audit record",
    description="Get detailed audit record for a specific action.",
)
async def get_audit_record(
    action_id: str,
    token: FounderToken = Depends(verify_fops_token),
    session = Depends(get_sync_session_dep),
) -> FounderAuditRecordDTO:
    """Get single audit record."""
    query = sql_text(
        """
        SELECT id, action_type, target_type, target_id, reason_code,
               reason_note, source_incident_id, founder_id, founder_email,
               mfa_verified, applied_at, reversed_at, reversed_by_action_id
        FROM founder_actions
        WHERE id = :action_id
    """
    )
    result = session.execute(query, {"action_id": action_id})
    row = result.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail=f"Action {action_id} not found")

    return FounderAuditRecordDTO(
        audit_id=f"audit_{row.id}",
        action_id=row.id,
        action_type=row.action_type,
        target_type=row.target_type,
        target_id=row.target_id,
        reason_code=row.reason_code,
        reason_note=row.reason_note,
        source_incident_id=row.source_incident_id,
        founder_id=row.founder_id,
        founder_email=row.founder_email,
        mfa_verified=row.mfa_verified,
        applied_at=row.applied_at.isoformat() if row.applied_at else "",
        reversed_at=row.reversed_at.isoformat() if row.reversed_at else None,
        reversed_by_action_id=row.reversed_by_action_id,
    )
