# Layer: L8 — Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: SCE passes package initialization
# Callers: sce_runner.py
# Allowed Imports: None
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: SCE_CONTRACT.yaml

"""
SCE Passes Package

This package contains the four deterministic passes of the Signal Circuit Enumerator.
All passes are READ-ONLY and produce EVIDENCE-ONLY output.
"""

from .pass_1_layers import run_pass_1
from .pass_2_metadata import run_pass_2
from .pass_3_mechanics import run_pass_3
from .pass_4_diff import run_pass_4

__all__ = ["run_pass_1", "run_pass_2", "run_pass_3", "run_pass_4"]
