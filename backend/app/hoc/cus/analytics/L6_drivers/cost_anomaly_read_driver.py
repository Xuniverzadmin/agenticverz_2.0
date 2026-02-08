# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api (via L5 engine)
#   Execution: sync
# Data Access:
#   Reads: CostBudget, CostAnomaly
#   Writes: CostAnomaly (upsert during persist)
# Database:
#   Scope: domain (analytics)
#   Models: CostBudget, CostAnomaly
# Role: Budget and anomaly persistence reads for cost_anomaly_detector_engine
# Callers: cost_anomaly_detector_engine.py (L5 engine, via Protocol)
# Allowed Imports: L6, L7 (models)
# Forbidden Imports: L1, L2, L3, L4, L5
# Forbidden: session.commit(), session.rollback() — L6 DOES NOT COMMIT
# Reference: PIN-511 Phase 1.2
# artifact_class: CODE

"""
Cost Anomaly Read Driver (PIN-511 Phase 1.2)

Extracts transitional ORM reads from cost_anomaly_detector_engine.py:
- Budget loading (was line ~521)
- Anomaly deduplication (was line ~878)
- Anomaly persistence (upsert + flush)

These were previously inline in the L5 engine with TRANSITIONAL_READ_OK markers.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlmodel import Session, select

from app.db import CostAnomaly, CostBudget
from app.hoc.cus.analytics.L5_schemas.cost_anomaly_dtos import PersistedAnomaly

logger = logging.getLogger("nova.analytics.cost_anomaly_read_driver")


class CostAnomalyReadDriver:
    """L6 driver for budget reads and anomaly deduplication/persistence.

    Implements CostAnomalyReadProtocol (L5_schemas).
    """

    def __init__(self, session: Session):
        self._session = session

    def fetch_active_budgets(self, tenant_id: str) -> list:
        """Fetch all active budgets for a tenant.

        Args:
            tenant_id: Tenant to fetch budgets for

        Returns:
            List of active CostBudget records
        """
        return self._session.exec(
            select(CostBudget).where(
                CostBudget.tenant_id == tenant_id,
                CostBudget.is_active == True,  # noqa: E712
            )
        ).all()

    def find_existing_anomaly(
        self,
        tenant_id: str,
        anomaly_type: str,
        entity_type: str,
        entity_id: Optional[str],
        since: datetime,
    ) -> Optional[CostAnomaly]:
        """Find an existing unresolved anomaly for deduplication.

        Args:
            tenant_id: Tenant scope
            anomaly_type: Anomaly type value
            entity_type: Entity type (user, feature, tenant)
            entity_id: Entity identifier
            since: Only consider anomalies detected after this time

        Returns:
            Existing CostAnomaly if found, None otherwise
        """
        return self._session.exec(
            select(CostAnomaly).where(
                CostAnomaly.tenant_id == tenant_id,
                CostAnomaly.anomaly_type == anomaly_type,
                CostAnomaly.entity_type == entity_type,
                CostAnomaly.entity_id == entity_id,
                CostAnomaly.detected_at >= since,
                CostAnomaly.resolved == False,  # noqa: E712
            )
        ).first()

    def persist_anomaly(self, anomaly: CostAnomaly) -> None:
        """Add or update an anomaly record (no commit — L4 owns transaction)."""
        self._session.add(anomaly)

    def flush_and_refresh(self, anomalies: List[CostAnomaly]) -> None:
        """Flush to get generated IDs and refresh objects."""
        self._session.flush()
        for ca in anomalies:
            self._session.refresh(ca)

    def upsert_anomaly(
        self,
        tenant_id: str,
        anomaly_type: str,
        severity: str,
        entity_type: str,
        entity_id: Optional[str],
        current_value_cents: float,
        expected_value_cents: float,
        deviation_pct: float,
        threshold_pct: float,
        message: str,
        breach_count: int,
        derived_cause: str,
        metadata_json: Dict[str, Any],
        today_start: datetime,
    ) -> PersistedAnomaly:
        """Create or update a CostAnomaly ORM row and return a DTO.

        PIN-520 No-Exemptions Phase 2: ORM construction lives in L6,
        L5 receives a pure PersistedAnomaly DTO.
        """
        existing = self.find_existing_anomaly(
            tenant_id=tenant_id,
            anomaly_type=anomaly_type,
            entity_type=entity_type,
            entity_id=entity_id,
            since=today_start,
        )

        if existing:
            existing.current_value_cents = current_value_cents
            existing.deviation_pct = deviation_pct
            existing.severity = severity
            existing.message = message
            existing.breach_count = breach_count
            existing.derived_cause = derived_cause
            existing.metadata_json = metadata_json
            self._session.add(existing)
            self._session.flush()
            self._session.refresh(existing)
            orm = existing
        else:
            orm = CostAnomaly(
                tenant_id=tenant_id,
                anomaly_type=anomaly_type,
                severity=severity,
                entity_type=entity_type,
                entity_id=entity_id,
                current_value_cents=current_value_cents,
                expected_value_cents=expected_value_cents,
                deviation_pct=deviation_pct,
                threshold_pct=threshold_pct,
                message=message,
                breach_count=breach_count,
                derived_cause=derived_cause,
                metadata_json=metadata_json,
            )
            self._session.add(orm)
            self._session.flush()
            self._session.refresh(orm)

        return PersistedAnomaly(
            id=str(orm.id),
            tenant_id=str(orm.tenant_id),
            anomaly_type=orm.anomaly_type,
            severity=orm.severity,
            entity_type=orm.entity_type,
            entity_id=orm.entity_id,
            current_value_cents=float(orm.current_value_cents) if orm.current_value_cents else 0.0,
            expected_value_cents=float(orm.expected_value_cents) if orm.expected_value_cents else 0.0,
            deviation_pct=float(orm.deviation_pct) if orm.deviation_pct else 0.0,
            message=orm.message or "",
            breach_count=orm.breach_count or 0,
            derived_cause=orm.derived_cause or "",
            metadata_json=orm.metadata_json or {},
        )


def get_cost_anomaly_read_driver(session: Session) -> CostAnomalyReadDriver:
    """Factory for CostAnomalyReadDriver."""
    return CostAnomalyReadDriver(session)
