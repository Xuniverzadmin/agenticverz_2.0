# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: AI Console
# Temporal:
#   Trigger: api
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: via ExportBundleProtocol (L6 driver)
#   Writes: none
# Role: Export business logic — validates requests and delegates to L6 driver
# Callers: incidents_bridge (L4), future L2 API
# Allowed Imports: L5_schemas (own domain), hoc_spine shared schemas
# Forbidden Imports: L1, L2, L3, L6 (direct), sqlalchemy, sibling domains
# Reference: PIN-511 Phase 2.1, PIN-513 Wiring Plan #6 (integrity_driver injection)
# artifact_class: CODE

"""
Export Engine (PIN-511 Phase 2.1)

L5 engine that owns export business logic for the incidents domain.
Validates export requests, selects bundle type, delegates to L6 driver via Protocol.

Responsibilities:
- Validate export request (permissions, compliance period)
- Select bundle type (evidence, SOC2, executive)
- Call driver via Protocol
- Return structured result

Rules:
- No session — receives driver via constructor
- No cross-domain imports
- No decision logic beyond selection + validation
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("nova.incidents.export_engine")


class ExportEngine:
    """L5 engine for incident export operations.

    Receives ExportBundleProtocol driver via constructor.
    No direct DB access — all data operations via Protocol.
    """

    def __init__(self, driver):
        """Initialize with L6 driver (satisfies ExportBundleProtocol).

        Args:
            driver: L6 export_bundle_driver implementing ExportBundleProtocol
        """
        self._driver = driver

    async def export_evidence(
        self,
        incident_id: str,
        exported_by: str = "system",
        export_reason: Optional[str] = None,
        include_raw_steps: bool = True,
    ) -> Dict[str, Any]:
        """Generate evidence export bundle.

        Validates the request and delegates to the L6 driver.

        Args:
            incident_id: Incident to export
            exported_by: User or system identifier
            export_reason: Reason for export (audit trail)
            include_raw_steps: Whether to include full trace steps

        Returns:
            Dict with bundle data and metadata
        """
        if not incident_id:
            raise ValueError("incident_id is required for evidence export")

        logger.info(
            "export_engine.export_evidence",
            extra={"incident_id": incident_id, "exported_by": exported_by},
        )

        bundle = await self._driver.create_evidence_bundle(
            incident_id=incident_id,
            exported_by=exported_by,
            export_reason=export_reason,
            include_raw_steps=include_raw_steps,
        )

        return {
            "bundle_type": "evidence",
            "incident_id": incident_id,
            "bundle": bundle,
        }

    async def export_soc2(
        self,
        incident_id: str,
        exported_by: str = "system",
        custom_controls: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """Generate SOC2 compliance export bundle.

        Validates the request and delegates to the L6 driver.

        Args:
            incident_id: Incident to export
            exported_by: User or system identifier
            custom_controls: Optional custom SOC2 control mappings

        Returns:
            Dict with SOC2 bundle data and metadata
        """
        if not incident_id:
            raise ValueError("incident_id is required for SOC2 export")

        logger.info(
            "export_engine.export_soc2",
            extra={"incident_id": incident_id, "exported_by": exported_by},
        )

        bundle = await self._driver.create_soc2_bundle(
            incident_id=incident_id,
            exported_by=exported_by,
            custom_controls=custom_controls,
        )

        return {
            "bundle_type": "soc2",
            "incident_id": incident_id,
            "bundle": bundle,
        }

    async def export_executive_debrief(
        self,
        incident_id: str,
        exported_by: str = "system",
    ) -> Dict[str, Any]:
        """Generate executive debrief export bundle.

        Validates the request and delegates to the L6 driver.

        Args:
            incident_id: Incident to export
            exported_by: User or system identifier

        Returns:
            Dict with executive debrief data and metadata
        """
        if not incident_id:
            raise ValueError("incident_id is required for executive debrief")

        logger.info(
            "export_engine.export_executive_debrief",
            extra={"incident_id": incident_id, "exported_by": exported_by},
        )

        bundle = await self._driver.create_executive_debrief(
            incident_id=incident_id,
            exported_by=exported_by,
        )

        return {
            "bundle_type": "executive_debrief",
            "incident_id": incident_id,
            "bundle": bundle,
        }

    async def export_with_integrity(
        self,
        incident_id: str,
        run_id: str,
        bundle_type: str = "evidence",
        exported_by: str = "system",
        export_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export bundle with integrity evaluation attached.

        Delegates to the appropriate export method and attaches integrity
        data from the integrity_driver (L6, logs domain).

        Args:
            incident_id: Incident to export
            run_id: Run ID for integrity computation
            bundle_type: evidence, soc2, or executive_debrief
            exported_by: User or system identifier
            export_reason: Reason for export

        Returns:
            Export result dict with integrity evaluation attached
        """
        # Generate the export bundle
        dispatch = {
            "evidence": lambda: self.export_evidence(
                incident_id=incident_id,
                exported_by=exported_by,
                export_reason=export_reason,
            ),
            "soc2": lambda: self.export_soc2(
                incident_id=incident_id,
                exported_by=exported_by,
            ),
            "executive_debrief": lambda: self.export_executive_debrief(
                incident_id=incident_id,
                exported_by=exported_by,
            ),
        }

        export_fn = dispatch.get(bundle_type)
        if not export_fn:
            raise ValueError(f"Unknown bundle_type: {bundle_type}")

        result = await export_fn()

        # Attach integrity evaluation via L6 driver (lazy import)
        from app.hoc.cus.logs.L6_drivers.integrity_driver import (
            compute_integrity_v2,
        )

        result["integrity"] = compute_integrity_v2(run_id)
        return result
