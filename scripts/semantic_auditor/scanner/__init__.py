# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Scanner Package Root
# Authority: None (observational only)
# Callers: semantic_auditor.runner
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Scanner Module

Responsible for walking the repository, filtering executable files,
classifying files by structural role, and loading AST for analysis.
"""

from .repo_walker import RepoWalker
from .file_classifier import FileClassifier
from .ast_loader import ASTLoader

__all__ = ["RepoWalker", "FileClassifier", "ASTLoader"]
