# Layer: L4 — Domain Services
# AUDIENCE: INTERNAL
# Role: Internal infrastructure domain services package
# Reference: DIRECTORY_REORGANIZATION_PLAN.md

"""
Internal Domain Services (houseofcards)

Infrastructure and background services:
- recovery: Failure handling and recovery logic
- agent: Agent planning and orchestration

Pattern: app/houseofcards/internal/{domain}/{role}/{file}.py
"""

__all__ = [
    "recovery",
    "agent",
]
