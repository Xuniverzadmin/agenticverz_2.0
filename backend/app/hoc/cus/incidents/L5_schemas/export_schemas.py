# Layer: L5 — Domain Schema
# AUDIENCE: CUSTOMER
# Role: Protocol and DTOs for incident export operations
# Reference: PIN-511 Phase 2.1
# artifact_class: CODE

"""
Export Schemas (PIN-511 Phase 2.1)

Defines the ExportBundleProtocol that export_engine.py (L5) depends on.
L6 export_bundle_driver implements this Protocol.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class ExportBundleProtocol(Protocol):
    """Protocol for export bundle operations.

    Implemented by: ExportBundleDriver (L6)
    Consumed by: ExportEngine (L5 engine)
    """

    async def create_evidence_bundle(
        self,
        incident_id: str,
        exported_by: str = "system",
        export_reason: Optional[str] = None,
        include_raw_steps: bool = True,
    ) -> Any:
        """Create evidence bundle from incident."""
        ...

    async def create_soc2_bundle(
        self,
        incident_id: str,
        exported_by: str = "system",
        custom_controls: Optional[dict] = None,
    ) -> Any:
        """Create SOC2 compliance bundle from incident."""
        ...

    async def create_executive_debrief(
        self,
        incident_id: str,
        exported_by: str = "system",
    ) -> Any:
        """Create executive debrief bundle from incident."""
        ...
