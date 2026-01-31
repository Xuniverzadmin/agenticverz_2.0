# HOC Topology — Index

**Directory:** `docs/architecture/topology/`
**Purpose:** Topology proposals, reviews, and ratified specifications for HOC layer architecture.

---

## Current Status

**V2.0.0 RATIFIED** — 6-layer execution-centric topology (L3 removed, single orchestrator)

| Change from V1.4.0 | Impact |
|-------------------|--------|
| L3 layer removed | 6 layers instead of 7 |
| `general` abolished | Replaced by `hoc_spine` |
| Single orchestrator | L4 owns ALL cross-domain |
| Linear trace | L2 → L4 → L5 → L6 |

---

## Documents

| Document | Version | Status | Description |
|----------|---------|--------|-------------|
| [HOC_LAYER_TOPOLOGY_V2.0.0.md](HOC_LAYER_TOPOLOGY_V2.0.0.md) | **V2.0.0** | **RATIFIED** | 6-layer topology. L3 removed. Single orchestrator (L4). BINDING. |
| [HOC_SPINE_TOPOLOGY_PROPOSAL.md](HOC_SPINE_TOPOLOGY_PROPOSAL.md) | V1.5.0 | SUPERSEDED | Two constitutions model. Superseded by V2.0.0. |
| [HOC_SPINE_TOPOLOGY_REVIEW.md](HOC_SPINE_TOPOLOGY_REVIEW.md) | — | REFERENCE | Binding decisions: Option C approved, no L5 in spine. |

---

## Related Documents

| Document | Location | Description |
|----------|----------|-------------|
| HOC_LAYER_TOPOLOGY_V1.md | `docs/architecture/architecture_core/` | V1.4.0 — SUPERSEDED by V2.0.0 |
| HOC_LITERATURE_PLAN.md | `docs/architecture/hoc/literature/` | Literature generation plan (V1.1.0) |
| LITERATURE_INDEX.md | `docs/architecture/hoc/literature/` | Per-domain literature outputs index |

---

## Ratification Record (V2.0.0)

Ratified: 2026-01-28

- [x] L3 removal acceptable
- [x] L4/hoc_spine as single orchestrator acceptable
- [x] `general` domain abolishment acceptable
- [x] Migration plan for existing L3 files acceptable
- [x] 6-layer topology acceptable

---

## Workflow

```
PROPOSED → REVIEWED → DRAFT → RATIFIED → LOCKED
           (V1.5.0)   (V2.0.0)  ← CURRENT
```

V2.0.0 is **RATIFIED** and **BINDING**.
