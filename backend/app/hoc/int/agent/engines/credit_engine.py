# Layer: L5 — Domain Engine
# Product: system-wide
# Role: Agent credit orchestration compatibility surface
# Callers: HOC internal agent runtime
# capability_id: CAP-008

"""Compatibility wrapper.

This module preserves the historical HOC import surface while delegating
implementation to the canonical service module.
"""

from app.agents.services.credit_service import *  # noqa: F401,F403
