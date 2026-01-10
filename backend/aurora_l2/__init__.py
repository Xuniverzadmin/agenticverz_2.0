# AURORA_L2 Intent Compiler Package
# Layer: L4 — Domain Engines
# Product: system-wide
# Temporal:
#   Trigger: scheduler | manual
#   Execution: sync
# Role: Compile intent YAMLs to SQL-ready format
# Reference: design/l2_1/AURORA_L2.md

"""
AURORA_L2 Intent Compiler

This package provides mechanical compilation of AURORA_L2 intent specs
from YAML format to SQL-ready format.

Key Constraints (from AURORA_L2.md):
- NO interpretation of semantics
- NO modification of UNREVIEWED intents
- Tags all rows with review_status
- Faithful reproduction of intent data
"""
