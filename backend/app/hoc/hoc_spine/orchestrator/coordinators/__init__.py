# Layer: L4 — HOC Spine (Orchestrator)
# AUDIENCE: INTERNAL
# Role: Coordinator package — cross-domain mediation (C4 Loop Model)
# Reference: PIN-504 (Cross-Domain Violation Resolution), PIN-487 (Loop Model)
# artifact_class: CODE

"""
Coordinators (C4 — Loop Model)

Cross-domain mediators that sit at L4 and break L5→L5/L6 violations.
Each coordinator provides a clean interface for one cross-domain concern,
using lazy imports to delegate to the appropriate domain engines/drivers.

Coordinators:
- AuditCoordinator: Audit event dispatch (incidents→logs, policies→logs)
- SignalCoordinator: Threshold signal emission (controls→activity)
"""
