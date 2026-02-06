# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Temporal:
#   Trigger: api/worker
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via L6 drivers
#   Writes: via L6 drivers
# Role: Detection Facade - Centralized access to anomaly detection operations
# Callers: L2 detection.py API, SDK, Worker
# Allowed Imports: L5, L6
# Forbidden Imports: L1, L2, L3, sqlalchemy (runtime)
# Reference: PIN-470, GAP-102 (Anomaly Detection API)
# Location: hoc/cus/analytics/L5_engines/detection_facade.py
# L4 is reserved for general/L4_runtime/ only per HOC Layer Topology.

"""
Detection Facade (L5 Domain Engine)

This facade provides the external interface for anomaly detection operations.
All detection APIs MUST use this facade instead of directly importing
internal detection modules.

Why This Facade Exists:
- Prevents L2→L4 layer violations
- Centralizes anomaly detection logic
- Provides unified access to cost, behavioral, and policy anomalies
- Single point for audit emission

Wrapped Services:
- CostAnomalyDetector: Cost anomaly detection (GAP-066)
- (Future) BehavioralDetector: Behavioral anomaly detection
- (Future) DriftDetector: Model drift detection

L2 API Routes (GAP-102):
- POST /api/v1/detection/run (run detection on demand)
- GET /api/v1/detection/anomalies (list anomalies)
- GET /api/v1/detection/anomalies/{id} (get anomaly)
- POST /api/v1/detection/anomalies/{id}/resolve (resolve anomaly)
- GET /api/v1/detection/status (detection engine status)

Usage:
    from app.hoc.cus.analytics.L5_engines.detection_facade import get_detection_facade

    facade = get_detection_facade()

    # Run detection
    result = await facade.run_detection(tenant_id="...", detection_type="cost")

    # List anomalies
    anomalies = await facade.list_anomalies(tenant_id="...")
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
import uuid

logger = logging.getLogger("nova.services.detection.facade")


# =============================================================================
# PIN-520: Protocol for anomaly coordinator injection (L5 purity)
# =============================================================================


class AnomalyCoordinatorPort(Protocol):
    """
    Protocol for anomaly detection + incident ingestion (PIN-520 L5 purity).

    L5 declares what it needs; L4 provides the implementation via bridge.
    This removes the L5 → L4 orchestrator import violation.
    """

    async def detect_and_ingest(
        self, session: Any, tenant_id: str
    ) -> Dict[str, Any]:
        """Run detection and ingest results into incidents."""
        ...


class DetectionType(str, Enum):
    """Types of anomaly detection."""
    COST = "cost"  # Cost anomalies (spikes, drift, budget)
    BEHAVIORAL = "behavioral"  # Behavioral anomalies (patterns)
    DRIFT = "drift"  # Model/data drift
    POLICY = "policy"  # Policy violations


# AnomalySeverity enum removed — ANA-DUP-001 quarantine
# Import from canonical source: cost_anomaly_detector.py
from app.hoc.cus.analytics.L5_engines.cost_anomaly_detector_engine import (
    AnomalySeverity,
)


class AnomalyStatus(str, Enum):
    """Anomaly resolution status."""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@dataclass
class DetectionResult:
    """Result of a detection run."""
    success: bool
    detection_type: str
    anomalies_detected: int
    anomalies_created: int
    incidents_created: int
    tenant_id: str
    run_at: str
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "detection_type": self.detection_type,
            "anomalies_detected": self.anomalies_detected,
            "anomalies_created": self.anomalies_created,
            "incidents_created": self.incidents_created,
            "tenant_id": self.tenant_id,
            "run_at": self.run_at,
            "error": self.error,
        }


@dataclass
class AnomalyInfo:
    """Anomaly information."""
    id: str
    tenant_id: str
    detection_type: str
    anomaly_type: str
    severity: str
    status: str
    entity_type: str
    entity_id: Optional[str]
    current_value: float
    expected_value: float
    deviation_pct: float
    message: str
    derived_cause: Optional[str]
    incident_id: Optional[str]
    detected_at: str
    resolved_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "detection_type": self.detection_type,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "status": self.status,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "current_value": self.current_value,
            "expected_value": self.expected_value,
            "deviation_pct": self.deviation_pct,
            "message": self.message,
            "derived_cause": self.derived_cause,
            "incident_id": self.incident_id,
            "detected_at": self.detected_at,
            "resolved_at": self.resolved_at,
            "metadata": self.metadata,
        }


@dataclass
class DetectionStatusInfo:
    """Detection engine status."""
    healthy: bool
    engines: Dict[str, Dict[str, Any]]
    last_run: Optional[str]
    next_scheduled_run: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "healthy": self.healthy,
            "engines": self.engines,
            "last_run": self.last_run,
            "next_scheduled_run": self.next_scheduled_run,
        }


class DetectionFacade:
    """
    Facade for anomaly detection operations.

    This is the ONLY entry point for L2 APIs and SDK to interact with
    detection services.

    Layer: L5 (Domain Engine)
    Callers: detection.py (L2), aos_sdk, Worker

    PIN-520: anomaly_coordinator is now injected via L4 bridge instead of
    being imported directly from L4 orchestrator.
    """

    def __init__(self, anomaly_coordinator: Optional[AnomalyCoordinatorPort] = None):
        """Initialize facade with lazy-loaded services.

        Args:
            anomaly_coordinator: Optional coordinator for anomaly detection + ingestion.
                                 If not provided, cost detection will be unavailable.
                                 L4 handlers should inject via AnalyticsEngineBridge.
        """
        self._cost_detector = None
        self._last_run: Optional[datetime] = None
        self._anomaly_coordinator = anomaly_coordinator

        # In-memory store for demo (would be database in production)
        self._anomalies: Dict[str, AnomalyInfo] = {}

    @property
    def cost_detector(self):
        """Lazy-load CostAnomalyDetector."""
        # Note: CostAnomalyDetector requires a session, so we return the class
        # and instantiate it with session when needed
        try:
            from app.hoc.cus.analytics.L5_engines.cost_anomaly_detector_engine import CostAnomalyDetector
            return CostAnomalyDetector
        except ImportError:
            logger.warning("CostAnomalyDetector not available")
            return None

    # =========================================================================
    # Detection Operations (GAP-102)
    # =========================================================================

    async def run_detection(
        self,
        tenant_id: str,
        detection_type: str = "cost",
        session=None,
    ) -> DetectionResult:
        """
        Run anomaly detection on demand.

        Args:
            tenant_id: Tenant ID
            detection_type: Type of detection (cost, behavioral, drift)
            session: Database session (required for cost detection)

        Returns:
            DetectionResult with detection outcome
        """
        logger.info(
            "facade.run_detection",
            extra={"tenant_id": tenant_id, "detection_type": detection_type}
        )

        now = datetime.now(timezone.utc)
        self._last_run = now

        try:
            if detection_type == "cost":
                return await self._run_cost_detection(tenant_id, session)
            else:
                # Other detection types not yet implemented
                return DetectionResult(
                    success=False,
                    detection_type=detection_type,
                    anomalies_detected=0,
                    anomalies_created=0,
                    incidents_created=0,
                    tenant_id=tenant_id,
                    run_at=now.isoformat(),
                    error=f"Detection type '{detection_type}' not yet implemented",
                )

        except Exception as e:
            logger.error(
                "facade.run_detection failed",
                extra={"error": str(e), "tenant_id": tenant_id}
            )
            return DetectionResult(
                success=False,
                detection_type=detection_type,
                anomalies_detected=0,
                anomalies_created=0,
                incidents_created=0,
                tenant_id=tenant_id,
                run_at=now.isoformat(),
                error=str(e),
            )

    async def _run_cost_detection(
        self,
        tenant_id: str,
        session,
    ) -> DetectionResult:
        """Run cost anomaly detection.

        PIN-520: Uses injected anomaly_coordinator instead of importing
        from L4 orchestrator. L5 must not import L4.
        """
        now = datetime.now(timezone.utc)

        if session is None:
            return DetectionResult(
                success=False,
                detection_type="cost",
                anomalies_detected=0,
                anomalies_created=0,
                incidents_created=0,
                tenant_id=tenant_id,
                run_at=now.isoformat(),
                error="Database session required for cost detection",
            )

        if self.cost_detector is None:
            return DetectionResult(
                success=False,
                detection_type="cost",
                anomalies_detected=0,
                anomalies_created=0,
                incidents_created=0,
                tenant_id=tenant_id,
                run_at=now.isoformat(),
                error="CostAnomalyDetector not available",
            )

        # PIN-520: Coordinator must be injected via L4 bridge
        if self._anomaly_coordinator is None:
            return DetectionResult(
                success=False,
                detection_type="cost",
                anomalies_detected=0,
                anomalies_created=0,
                incidents_created=0,
                tenant_id=tenant_id,
                run_at=now.isoformat(),
                error="Anomaly coordinator not available (inject via L4 bridge)",
            )

        try:
            # PIN-520: Use injected coordinator instead of L4 orchestrator import
            result = await self._anomaly_coordinator.detect_and_ingest(session, tenant_id)

            detected = result.get("detected", [])
            incidents = result.get("incidents_created", [])

            # Convert to AnomalyInfo and store
            for anomaly in detected:
                info = AnomalyInfo(
                    id=anomaly.id,
                    tenant_id=tenant_id,
                    detection_type="cost",
                    anomaly_type=anomaly.anomaly_type,
                    severity=anomaly.severity,
                    status="open",
                    entity_type=anomaly.entity_type,
                    entity_id=anomaly.entity_id,
                    current_value=anomaly.current_value_cents,
                    expected_value=anomaly.expected_value_cents,
                    deviation_pct=anomaly.deviation_pct,
                    message=anomaly.message,
                    derived_cause=anomaly.derived_cause,
                    incident_id=None,
                    detected_at=anomaly.detected_at.isoformat() if hasattr(anomaly, 'detected_at') else now.isoformat(),
                    metadata=anomaly.metadata_json if hasattr(anomaly, 'metadata_json') else {},
                )
                self._anomalies[info.id] = info

            return DetectionResult(
                success=True,
                detection_type="cost",
                anomalies_detected=len(detected),
                anomalies_created=len(detected),
                incidents_created=len(incidents),
                tenant_id=tenant_id,
                run_at=now.isoformat(),
            )

        except Exception as e:
            logger.error(
                "facade._run_cost_detection failed",
                extra={"error": str(e), "tenant_id": tenant_id}
            )
            return DetectionResult(
                success=False,
                detection_type="cost",
                anomalies_detected=0,
                anomalies_created=0,
                incidents_created=0,
                tenant_id=tenant_id,
                run_at=now.isoformat(),
                error=str(e),
            )

    # =========================================================================
    # Anomaly CRUD Operations (GAP-102)
    # =========================================================================

    async def list_anomalies(
        self,
        tenant_id: str,
        detection_type: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AnomalyInfo]:
        """
        List anomalies for a tenant.

        Args:
            tenant_id: Tenant ID
            detection_type: Optional filter by detection type
            severity: Optional filter by severity
            status: Optional filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of AnomalyInfo
        """
        logger.debug(
            "facade.list_anomalies",
            extra={"tenant_id": tenant_id, "detection_type": detection_type}
        )

        # Filter anomalies
        results = []
        for anomaly in self._anomalies.values():
            if anomaly.tenant_id != tenant_id:
                continue
            if detection_type and anomaly.detection_type != detection_type:
                continue
            if severity and anomaly.severity != severity:
                continue
            if status and anomaly.status != status:
                continue
            results.append(anomaly)

        # Sort by detected_at descending
        results.sort(key=lambda a: a.detected_at, reverse=True)

        # Apply pagination
        return results[offset:offset + limit]

    async def get_anomaly(
        self,
        anomaly_id: str,
        tenant_id: str,
    ) -> Optional[AnomalyInfo]:
        """
        Get a specific anomaly.

        Args:
            anomaly_id: Anomaly ID
            tenant_id: Tenant ID for authorization

        Returns:
            AnomalyInfo or None if not found
        """
        anomaly = self._anomalies.get(anomaly_id)
        if anomaly and anomaly.tenant_id == tenant_id:
            return anomaly
        return None

    async def resolve_anomaly(
        self,
        anomaly_id: str,
        tenant_id: str,
        resolution: str,
        notes: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> Optional[AnomalyInfo]:
        """
        Resolve an anomaly.

        Args:
            anomaly_id: Anomaly ID
            tenant_id: Tenant ID for authorization
            resolution: Resolution status (resolved, dismissed)
            notes: Optional resolution notes
            actor: Who resolved it

        Returns:
            Updated AnomalyInfo or None if not found
        """
        logger.info(
            "facade.resolve_anomaly",
            extra={
                "anomaly_id": anomaly_id,
                "resolution": resolution,
                "actor": actor,
            }
        )

        anomaly = self._anomalies.get(anomaly_id)
        if not anomaly or anomaly.tenant_id != tenant_id:
            return None

        now = datetime.now(timezone.utc)
        anomaly.status = resolution
        anomaly.resolved_at = now.isoformat()
        if notes:
            anomaly.metadata["resolution_notes"] = notes
        if actor:
            anomaly.metadata["resolved_by"] = actor

        return anomaly

    async def acknowledge_anomaly(
        self,
        anomaly_id: str,
        tenant_id: str,
        actor: Optional[str] = None,
    ) -> Optional[AnomalyInfo]:
        """
        Acknowledge an anomaly (mark as seen but not resolved).

        Args:
            anomaly_id: Anomaly ID
            tenant_id: Tenant ID for authorization
            actor: Who acknowledged it

        Returns:
            Updated AnomalyInfo or None if not found
        """
        anomaly = self._anomalies.get(anomaly_id)
        if not anomaly or anomaly.tenant_id != tenant_id:
            return None

        anomaly.status = "acknowledged"
        if actor:
            anomaly.metadata["acknowledged_by"] = actor
            anomaly.metadata["acknowledged_at"] = datetime.now(timezone.utc).isoformat()

        return anomaly

    # =========================================================================
    # Status Operations (GAP-102)
    # =========================================================================

    def get_detection_status(self) -> DetectionStatusInfo:
        """
        Get detection engine status.

        Returns:
            DetectionStatusInfo with engine health
        """
        engines = {
            "cost": {
                "status": "healthy" if self.cost_detector else "unavailable",
                "available": self.cost_detector is not None,
            },
            "behavioral": {
                "status": "not_implemented",
                "available": False,
            },
            "drift": {
                "status": "not_implemented",
                "available": False,
            },
        }

        healthy = engines["cost"]["available"]

        return DetectionStatusInfo(
            healthy=healthy,
            engines=engines,
            last_run=self._last_run.isoformat() if self._last_run else None,
            next_scheduled_run=None,  # Would come from scheduler
        )


# =============================================================================
# Module-level singleton accessor
# =============================================================================

_facade_instance: Optional[DetectionFacade] = None


def get_detection_facade(
    anomaly_coordinator: Optional[AnomalyCoordinatorPort] = None,
) -> DetectionFacade:
    """
    Get the detection facade instance.

    This is the recommended way to access detection operations
    from L2 APIs and the SDK.

    PIN-520: L4 callers must inject anomaly_coordinator.
    L5 must not import from hoc_spine.

    Args:
        anomaly_coordinator: Optional coordinator for cost anomaly detection.
                             Required for cost detection to work (injected by L4 caller).

    Returns:
        DetectionFacade instance
    """
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = DetectionFacade(anomaly_coordinator=anomaly_coordinator)
    elif anomaly_coordinator is not None and _facade_instance._anomaly_coordinator is None:
        # Allow late injection if coordinator wasn't provided initially
        _facade_instance._anomaly_coordinator = anomaly_coordinator
    return _facade_instance
