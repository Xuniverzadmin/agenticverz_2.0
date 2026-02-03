# Layer: L6 — Domain Driver
# AUDIENCE: INTERNAL
# Role: Usage record persistence driver - writes UsageRecord to DB
# Temporal:
#   Trigger: api
#   Execution: async
# Data Access:
#   Reads: none
#   Writes: usage_records
# Database:
#   Scope: domain (policies/metering)
#   Models: UsageRecord
# Callers: L5 usage_monitor
# Allowed Imports: L7 (models), sqlalchemy
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: GAP-053

"""
Usage Record Driver (L6)

Persists usage records to the usage_records table.
Called by UsageMonitor (L5) after step execution.

L6 contract:
- Receives AsyncSession from caller
- NEVER commits — caller owns transaction
- Fire-and-forget semantics (errors logged, not raised)
"""

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import UsageRecord
from app.hoc.cus.hoc_spine.services.time import utc_now

logger = logging.getLogger("nova.hoc.policies.usage_record_driver")


class UsageRecordDriver:
    """L6 driver for persisting usage records."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def insert_usage(
        self,
        tenant_id: str,
        meter_name: str,
        amount: int,
        unit: str = "count",
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        worker_id: Optional[str] = None,
        api_key_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Insert a usage record.

        Args:
            tenant_id: Tenant ID
            meter_name: Meter name (e.g., "tokens_used", "cost_cents", "step_latency_ms")
            amount: Usage amount
            unit: Unit of measurement
            period_start: Period start (defaults to now)
            period_end: Period end (defaults to now)
            worker_id: Optional worker/run ID
            api_key_id: Optional API key ID
            metadata: Optional metadata dict

        Returns:
            Created record ID
        """
        now = utc_now()
        record = UsageRecord(
            tenant_id=tenant_id,
            meter_name=meter_name,
            amount=amount,
            unit=unit,
            period_start=period_start or now,
            period_end=period_end or now,
            worker_id=worker_id,
            api_key_id=api_key_id,
            metadata_json=json.dumps(metadata) if metadata else None,
            recorded_at=now,
        )
        self._session.add(record)
        await self._session.flush()
        return record.id
