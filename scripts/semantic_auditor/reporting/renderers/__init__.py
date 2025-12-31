# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Renderers Package Root
# Authority: None (observational only)
# Callers: semantic_auditor.reporting.report_builder
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Renderers Module

Output format renderers for semantic audit reports:
- Markdown for human-readable output
- JSON for machine-readable output
"""

from .markdown import MarkdownRenderer
from .json import JSONRenderer

__all__ = ["MarkdownRenderer", "JSONRenderer"]
