# Governance Baseline Report

**Generated:** 2026-01-05
**Timestamp:** 20260105_155515
**Registry Version:** 1.0.0

---

## Capability States

| State | Count | Capabilities |
|-------|-------|--------------|
| CLOSED | 11 | authentication, authorization, multi_agent, policy_engine, care_routing, governance_orchestration, workflow_engine, learning_pipeline, memory_system, optimization_engine, skill_system |
| FROZEN | 0 | - |
| READ_ONLY | 2 | policy_proposals, prediction_plane |
| PARTIAL | 3 | replay, cost_simulation, founder_console |
| PLANNED | 1 | cross_project |
| QUARANTINED | 0 | - |

**Total Capabilities:** 17

---

## Authority Surfaces

The following capabilities have authority enforcement:

- **authentication** (CAP-006)
  - `/backend/app/auth/invariants.py`
  - `/backend/app/auth/route_planes.py`
- **authorization** (CAP-007)
- **care_routing** (CAP-010)
- **cost_simulation** (CAP-002)
- **founder_console** (CAP-005)
- **governance_orchestration** (CAP-011)
- **learning_pipeline** (CAP-013)
- **memory_system** (CAP-014)
- **multi_agent** (CAP-008)
- **optimization_engine** (CAP-015)
- **policy_engine** (CAP-009)
- **policy_proposals** (CAP-003)
- **prediction_plane** (CAP-004)
  - `/backend/app/auth/authority.py:require_predictions_read`
  - `/docs/governance/PERMISSION_TAXONOMY_V1.md:predictions`
- **replay** (CAP-001)
  - `/backend/app/auth/authority.py:require_replay_execute`
  - `/docs/governance/PERMISSION_TAXONOMY_V1.md:replay`
- **skill_system** (CAP-016)
- **workflow_engine** (CAP-012)

---

## CI Invariants

The following CI checks are enforced:

### Capability Registry (capability-registry.yml)
| Check | Description | Status |
|-------|-------------|--------|
| T1: Capability Linkage | Code changes must link to registered capability | ACTIVE |
| T2: UI Expansion Guard | UI changes require ui_expansion_allowed flag | ACTIVE |
| T3: Registry Validation | Registry structure must be valid | ACTIVE |
| T4: Gap Heatmap | Auto-updates on main merge | ACTIVE |

### Governance Freeze (Phase G)
| Check | Description | Status |
|-------|-------------|--------|
| G1: Registry Mutation | State changes require PIN reference | ACTIVE |
| G2: Plane Purity | Route/authority plane matching | ACTIVE |
| G3: Taxonomy Lock | Permission changes require version bump | ACTIVE |
| G4: Worker Auth | Workers use API keys only | ACTIVE |
| G5: Authority Guard | Replay/prediction routes have RBAC | ACTIVE |

---

## Known Intentional Gaps

These gaps are by design and should not be "fixed":

- **cross_project**: Cross-project aggregation NOT PRESENT by design in customer console

---

## Blocking Gaps

Gaps that block promotion:

- **cost_simulation** (PLANE_ASYMMETRY): Client exists but no UI page
- **policy_proposals** (LIFECYCLE_INCOMPLETE): Read-only API, no creation flow
- **founder_console** (LIFECYCLE_INCOMPLETE): Routing wiring unverified
- **replay** (PLANE_ASYMMETRY): UI exists but no dedicated client API wrapper

---

## Frozen Artifacts

The following artifacts are frozen and require founder approval to modify:

| Artifact | Path | Frozen Since |
|----------|------|--------------|
| Permission Taxonomy | docs/governance/PERMISSION_TAXONOMY_V1.md | 2026-01-05 |
| Capability Registry | docs/capabilities/CAPABILITY_REGISTRY.yaml | 2026-01-05 |

---

## Verification Commands

```bash
# Verify authority guard
python3 scripts/ops/capability_registry_enforcer.py authority-guard --scan-all

# Verify plane purity
python3 scripts/ops/capability_registry_enforcer.py plane-purity --scan-all

# Verify worker auth
python3 scripts/ops/capability_registry_enforcer.py worker-auth --scan-all

# Validate registry
python3 scripts/ops/capability_registry_enforcer.py validate-registry
```

---

## Baseline Hash

This baseline can be verified against the registry:

```
Registry Hash: e220d518
Capabilities: 17
CLOSED: 11
Authority Surfaces: 16
```

---

*This report is the baseline of truth. Any drift from this state requires explicit governance approval.*
