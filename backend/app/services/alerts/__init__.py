# Layer: L4 — Domain Engines
# Product: system-wide
# Reference: GAP-049 (AlertFatigueController)
"""
Alert Services (GAP-049)

Provides alert fatigue management including rate limiting,
suppression, and aggregation of repetitive alerts.

This module provides:
    - AlertFatigueController: Main service for fatigue management
    - AlertFatigueConfig: Configuration for fatigue thresholds
    - AlertFatigueState: State tracking for alert sources
    - Helper functions for quick access
"""

from app.services.alerts.fatigue_controller import (
    AlertFatigueAction,
    AlertFatigueConfig,
    AlertFatigueController,
    AlertFatigueError,
    AlertFatigueMode,
    AlertFatigueState,
    AlertFatigueStats,
    check_alert_fatigue,
    get_fatigue_stats,
    suppress_alert,
)

__all__ = [
    "AlertFatigueAction",
    "AlertFatigueConfig",
    "AlertFatigueController",
    "AlertFatigueError",
    "AlertFatigueMode",
    "AlertFatigueState",
    "AlertFatigueStats",
    "check_alert_fatigue",
    "get_fatigue_stats",
    "suppress_alert",
]
