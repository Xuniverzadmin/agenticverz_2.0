"""
Data Contracts Module - M29 Data Contract Freeze

This module defines the FROZEN API contracts for AOS.
These contracts are IMMUTABLE once deployed.

Contract Invariants:
1. Field names NEVER change (use deprecation instead)
2. Required fields NEVER become optional
3. Types NEVER widen (int -> float is FORBIDDEN)
4. New optional fields MAY be added (backward compatible)
5. Removal requires 2-version deprecation cycle

Domains:
- guard: Customer Console contracts (tenant-scoped)
- ops: Founder Ops Console contracts (global view)

IMPORTANT: These domains MUST NOT share response models.
Cross-pollution violates Category 2 auth boundaries.
"""

from app.contracts.common import *  # noqa: F401, F403
from app.contracts.guard import *  # noqa: F401, F403
from app.contracts.ops import *  # noqa: F401, F403

__all__ = [
    # Guard contracts
    "GuardStatusDTO",
    "TodaySnapshotDTO",
    "IncidentSummaryDTO",
    "IncidentDetailDTO",
    "ApiKeyDTO",
    "TenantSettingsDTO",
    "ReplayResultDTO",
    # Ops contracts
    "SystemPulseDTO",
    "CustomerSegmentDTO",
    "CustomerAtRiskDTO",
    "IncidentPatternDTO",
    "StickinessByFeatureDTO",
    "RevenueRiskDTO",
    "InfraLimitsDTO",
    "PlaybookDTO",
    # Common (non-domain, version/health only)
    "HealthDTO",
    "ErrorDTO",
]

# Contract version - bump on any change
CONTRACT_VERSION = "1.0.0"
CONTRACT_FROZEN_AT = "2025-12-23"
