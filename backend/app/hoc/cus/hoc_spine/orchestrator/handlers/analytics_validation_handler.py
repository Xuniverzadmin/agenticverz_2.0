# Layer: L4 — HOC Spine (Handler)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Role: L4 handler — dataset validation + divergence reporting
# Callers: Admin API, ops tooling
# Allowed Imports: hoc_spine, hoc.cus.analytics.L5_engines (lazy)
# Forbidden Imports: L1, L2
# Reference: PIN-513 Batch 3A3 Wiring
# artifact_class: CODE

"""
Analytics Validation Handler (PIN-513 Batch 3A3 Wiring)

L4 handler for dataset validation and divergence reporting.

Wires from analytics/L5_engines/datasets_engine.py:
- get_dataset_validator()
- validate_dataset(dataset_id)
- validate_all_datasets()

Wires from analytics/L5_engines/divergence_engine.py:
- generate_divergence_report(start_date, end_date, tenant_id)
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger("nova.hoc_spine.handlers.analytics_validation")


class AnalyticsValidationHandler:
    """L4 handler: dataset validation and divergence reporting."""

    # ── Dataset validation ──

    def get_validator(self) -> Any:
        """Get dataset validator instance."""
        from app.hoc.cus.analytics.L5_engines.datasets_engine import (
            get_dataset_validator,
        )

        return get_dataset_validator()

    async def validate_dataset(self, dataset_id: str) -> Any:
        """Validate a single dataset."""
        from app.hoc.cus.analytics.L5_engines.datasets_engine import validate_dataset

        result = await validate_dataset(dataset_id=dataset_id)
        logger.info(
            "dataset_validated",
            extra={"dataset_id": dataset_id},
        )
        return result

    async def validate_all(self) -> Dict[str, Any]:
        """Validate all datasets."""
        from app.hoc.cus.analytics.L5_engines.datasets_engine import (
            validate_all_datasets,
        )

        results = await validate_all_datasets()
        logger.info(
            "all_datasets_validated",
            extra={"count": len(results)},
        )
        return results

    # ── Divergence reporting ──

    async def generate_divergence_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
    ) -> Any:
        """Generate a V1/V2 divergence report."""
        from app.hoc.cus.analytics.L5_engines.divergence_engine import (
            generate_divergence_report,
        )

        report = await generate_divergence_report(
            start_date=start_date,
            end_date=end_date,
            tenant_id=tenant_id,
        )
        logger.info(
            "divergence_report_generated",
            extra={"tenant_id": tenant_id},
        )
        return report
