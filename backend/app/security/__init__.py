# Layer: L6 — Platform Substrate
# Product: system-wide
# Reference: PIN-052

"""
Security utilities for AOS.

Modules:
- sanitize: Text sanitization for embeddings to prevent secret leakage
"""

from .sanitize import (
    is_safe_for_embedding,
    sanitize,
    sanitize_error_message,
    sanitize_for_embedding,
)

__all__ = [
    "sanitize_for_embedding",
    "sanitize_error_message",
    "is_safe_for_embedding",
    "sanitize",
]
