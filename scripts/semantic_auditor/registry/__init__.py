# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Registry Package Root
# Authority: None (observational only)
# Callers: semantic_auditor.runner
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Registry Module

Maintains indices of semantic contracts and coordinate maps:
- Semantic contract index (which contracts exist, frozen domains)
- Semantic coordinate map (file to layer/role/domain mapping)
"""

from .semantic_contract_index import SemanticContractIndex
from .semantic_coordinate_map import SemanticCoordinateMap

__all__ = ["SemanticContractIndex", "SemanticCoordinateMap"]
