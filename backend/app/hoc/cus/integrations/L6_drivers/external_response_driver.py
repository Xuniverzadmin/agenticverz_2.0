# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api|worker|scheduler
#   Execution: sync
# Role: External response persistence and interpretation driver
# Callers: L3 adapters (record_raw), L4/L5 engines (interpret), L2 (read_interpreted)
# Allowed Imports: L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-256 Phase E FIX-04
# NOTE: Renamed external_response_service.py → external_response_driver.py (2026-01-24)
#       per BANNED_NAMING rule (*_service.py → *_driver.py for L6 files)

"""
External Response Driver (Phase E FIX-04)

L6 service for persisting raw external responses and their interpretations.

Write Path (L3 → L6):
- Adapters call record_raw_response() with raw data
- Raw data is persisted with interpretation_owner declared
- L3 returns only receipt confirmation (not interpretation)

Interpretation Path (L4 → L6):
- L4 engines call interpret() with domain-meaningful result
- interpreted_value is persisted with interpreted_by

Read Path (L5/L2 ← L6):
- Consumers call get_interpreted() to read L4's interpretation
- Raw data is never exposed to consumers

Contract:
- Every external response has an explicit interpretation owner
- L3 adapters never interpret - only record raw data
- L4 engines are the only authority for interpretation
- L5/L2 never see raw_response - only interpreted_value
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app.models.external_response import (
    ExternalResponse,
    InterpretedResponse,
)


class ExternalResponseService:
    """
    Service for external response operations.

    Phase E FIX-04: Makes interpretation authority explicit and queryable.
    """

    def __init__(self, session: Session):
        self.session = session

    def record_raw_response(
        self,
        source: str,
        raw_response: dict,
        interpretation_owner: str,
        interpretation_contract: Optional[str] = None,
        request_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> ExternalResponse:
        """
        Record a raw external response (L3 → L6 write).

        Called by L3 adapters after receiving external API response.
        The adapter does NOT interpret - it records who should interpret.

        Args:
            source: ANTHROPIC, OPENAI, VOYAGEAI, WEBHOOK, OTHER
            raw_response: Untouched external data
            interpretation_owner: L4 engine responsible for interpretation
            interpretation_contract: Optional contract name
            request_id: Optional correlation ID
            run_id: Optional run context

        Returns:
            The newly created external response record
        """
        now = datetime.now(timezone.utc)

        response = ExternalResponse(
            source=source,
            raw_response=raw_response,
            interpretation_owner=interpretation_owner,
            interpretation_contract=interpretation_contract,
            request_id=request_id,
            run_id=run_id,
            received_at=now,
        )

        self.session.add(response)
        self.session.flush()

        return response

    def interpret(
        self,
        response_id: UUID,
        interpreted_value: dict,
        interpreted_by: str,
    ) -> ExternalResponse:
        """
        Record L4 engine interpretation (L4 → L6 write).

        Called by L4 engines after interpreting raw response.
        The interpreted_value becomes the domain-meaningful result.

        Args:
            response_id: ID of external response to interpret
            interpreted_value: Domain-meaningful result
            interpreted_by: L4 engine instance name

        Returns:
            The updated external response record
        """
        now = datetime.now(timezone.utc)

        stmt = (
            update(ExternalResponse)
            .where(ExternalResponse.id == response_id)
            .values(
                interpreted_value=interpreted_value,
                interpreted_at=now,
                interpreted_by=interpreted_by,
            )
            .returning(ExternalResponse)
        )
        result = self.session.execute(stmt)
        self.session.flush()

        return result.scalar_one()

    def get_raw_for_interpretation(
        self,
        response_id: UUID,
        expected_owner: str,
    ) -> Optional[ExternalResponse]:
        """
        Get raw response for L4 interpretation.

        Only returns if caller matches interpretation_owner.
        Prevents unauthorized interpretation.

        Args:
            response_id: ID of external response
            expected_owner: L4 engine claiming interpretation authority

        Returns:
            External response if owner matches, None otherwise
        """
        stmt = select(ExternalResponse).where(
            and_(
                ExternalResponse.id == response_id,
                ExternalResponse.interpretation_owner == expected_owner,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_interpreted(
        self,
        response_id: UUID,
    ) -> Optional[InterpretedResponse]:
        """
        Get interpreted response for consumers (L5/L2 ← L6 read).

        Returns only the interpreted value, not raw response.
        Consumer never sees untouched external data.

        Args:
            response_id: ID of external response

        Returns:
            InterpretedResponse with only domain-meaningful data
        """
        stmt = select(ExternalResponse).where(
            and_(
                ExternalResponse.id == response_id,
                ExternalResponse.interpreted_at.is_not(None),
            )
        )
        response = self.session.execute(stmt).scalar_one_or_none()

        if not response:
            return None

        return InterpretedResponse(
            id=response.id,
            source=response.source,
            interpretation_owner=response.interpretation_owner,
            interpreted_value=response.interpreted_value,
            interpreted_at=response.interpreted_at,
            interpreted_by=response.interpreted_by,
        )

    def get_pending_interpretations(
        self,
        interpretation_owner: str,
        limit: int = 100,
    ) -> list[ExternalResponse]:
        """
        Get responses pending interpretation by owner.

        Used by L4 engines to find work needing interpretation.

        Args:
            interpretation_owner: L4 engine responsible
            limit: Max results

        Returns:
            List of uninterpreted responses owned by this engine
        """
        stmt = (
            select(ExternalResponse)
            .where(
                and_(
                    ExternalResponse.interpretation_owner == interpretation_owner,
                    ExternalResponse.interpreted_at.is_(None),
                )
            )
            .order_by(ExternalResponse.received_at)
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars().all())


# Convenience functions for use without instantiating service


def record_external_response(
    session: Session,
    source: str,
    raw_response: dict,
    interpretation_owner: str,
    interpretation_contract: Optional[str] = None,
    request_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> ExternalResponse:
    """Record a raw external response (L3 → L6)."""
    service = ExternalResponseService(session)
    return service.record_raw_response(
        source=source,
        raw_response=raw_response,
        interpretation_owner=interpretation_owner,
        interpretation_contract=interpretation_contract,
        request_id=request_id,
        run_id=run_id,
    )


def interpret_response(
    session: Session,
    response_id: UUID,
    interpreted_value: dict,
    interpreted_by: str,
) -> ExternalResponse:
    """Record L4 engine interpretation (L4 → L6)."""
    service = ExternalResponseService(session)
    return service.interpret(
        response_id=response_id,
        interpreted_value=interpreted_value,
        interpreted_by=interpreted_by,
    )


def get_interpreted_response(
    session: Session,
    response_id: UUID,
) -> Optional[InterpretedResponse]:
    """Get interpreted response for consumers (L5/L2 ← L6)."""
    service = ExternalResponseService(session)
    return service.get_interpreted(response_id)
