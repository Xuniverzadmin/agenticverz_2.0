# PIN-081: MN-OS Naming Evolution - Milestone to Subsystem Mapping

**Status:** COMPLETE
**Created:** 2025-12-15
**Category:** Architecture / Documentation / CI
**Related:** PIN-005, PIN-033, PIN-080

---

## Summary

Established a formal naming evolution from legacy milestone identifiers (M0-M19) to Machine-Native Operating System (MN-OS) subsystem names. This enables dual-name recognition across documentation, CI, and codebase while maintaining backward compatibility.

---

## Problem Statement

As Agenticverz matured from a milestone-based development model to a coherent operating system architecture, the milestone names (M0-M19) became limiting:

1. **Milestone names don't convey architectural role** - "M4" says nothing about its function
2. **No hierarchy visible** - The layered architecture wasn't reflected in naming
3. **Hard to communicate** - Explaining "M17 depends on M4" requires context
4. **Documentation fragmented** - No unified architectural view

---

## Solution: MN-OS Naming System

### Complete Milestone → Subsystem Mapping

| Milestone | Legacy Name | MN-OS Name | Acronym | Layer |
|-----------|-------------|------------|---------|-------|
| M0 | Foundations & Contracts | Kernel Primitives | KP | 1 |
| M1 | Runtime Interfaces | Agent Runtime Kernel | ARK | 1 |
| M2 | Skill Registration | OS Capability Table | OCT | 2 |
| M3 | Core Skills | Native OS Skills | NOS | 2 |
| M4 | Workflow Engine | Agent Execution Engine | **AXE** | 3 |
| M5 | Policy API | Constitutional Guardrail Layer | CGL | 3 |
| M6 | CostSim V2 | Resource Economics Engine | REE | 2 |
| M7 | Memory Integration | System Memory Matrix | SMM | 1 |
| M8 | SDK & Auth | Identity Authority & Access Panel | **IAAP** | 0 |
| M9 | Failure Catalog | System Failure Intelligence Layer | **SFIL** | 3 |
| M10 | Recovery Engine | System Self-Repair Layer | SSRL | 3 |
| M11 | LLM Adapters | Cognitive Interface Kernel | **CIK** | 2 |
| M12 | Multi-Agent System | MAS Orchestrator Core | MOC | 4 |
| M13 | Console UI | OS Control Center | OCC | 4 |
| M14 | BudgetLLM Safety | Cognitive Compliance Engine | CCE | 6 |
| M15 | SBA Foundations | Strategic Agency Kernel | **SAK** | 5 |
| M16 | Agent Governance | Agent Oversight Authority | **AOA** | 5 |
| M17 | CARE Routing | Cognitive Routing Kernel | **CRK** | 5 |
| M18 | CARE-L Evolution | Adaptive Governance Kernel | AGK | 6 |
| M19 | Policy Constitutional | OS Constitution | OSC | 6 |

### Architecture Layers

```
Layer 6: Constitutional Governance (M19, M18, M14)
Layer 5: Strategic Routing (M17, M15, M16)
Layer 4: Multi-Agent Orchestration (M12, M13)
Layer 3: Execution & Recovery (M4, M10, M9)
Layer 2: Capability & Cognitive I/O (M2, M3, M11, M6)
Layer 1: Kernel & Memory (M0, M1, M7)
Layer 0: Identity & Access (M8)
```

---

## Implementation

### 1. Documentation Created

| File | Purpose |
|------|---------|
| `docs/mn-os/subsystem_mapping.md` | Canonical reference for all mappings |
| `docs/mn-os/transition_guide.md` | Contributor/operator guide |
| `docs/mn-os/architecture_overview.md` | 6-layer architecture diagram |

### 2. CI Consistency Checker v5.0

**Upgrade:** v4.1 → v5.0

New Features:
- `--subsystems` flag for MN-OS dashboard view
- Dual-name recognition in detection patterns
- MNOS_NAME and MNOS_ACRONYM associative arrays
- Architecture layer display

```bash
# View MN-OS subsystem dashboard
./scripts/ops/ci_consistency_check.sh --subsystems

# Standard milestone view (still works)
./scripts/ops/ci_consistency_check.sh --milestone
```

### 3. Detection Pattern Updates

CI now recognizes both naming conventions:

```bash
# M4 detection (any match = PASS)
grep -rqE "ExecutionPlan|WorkflowStep|Agent Execution Engine|AXE"

# M17 detection
grep -rqE "CARE|CARERouter|Cognitive Routing Kernel|CRK"
```

---

## Usage Guidelines

### For Contributors

```python
# GOOD: Include both names in docstrings
class WorkflowEngine:
    """
    M4: Workflow Engine (Legacy)
    MN-OS: Agent Execution Engine (AXE)

    Deterministic execution pipeline for agent workflows.
    """
    pass
```

### For Operators

Both naming conventions appear in logs and metrics:

```
# Legacy format
[M4] Workflow execution started: run_id=abc123

# MN-OS format
[AXE] Agent execution initiated: run_id=abc123
```

---

## Migration Path

### Phase 1: Dual-Name Support (Current - v5.0)
- CI recognizes both naming systems
- Documentation uses both conventions
- No breaking changes

### Phase 2: MN-OS Primary (M20+)
- New features use MN-OS names by default
- Legacy names remain supported
- Deprecation warnings introduced

### Phase 3: Legacy Sunset (v2.0+)
- Legacy names deprecated
- Migration tools provided

---

## Files Changed

| File | Type | Description |
|------|------|-------------|
| `scripts/ops/ci_consistency_check.sh` | Modified | v4.1 → v5.0 with MN-OS support |
| `docs/mn-os/subsystem_mapping.md` | **NEW** | Canonical mapping reference |
| `docs/mn-os/transition_guide.md` | **NEW** | Contributor guide |
| `docs/mn-os/architecture_overview.md` | **NEW** | Architecture layers |

---

## CI Validation

```
+====================================================================+
|       MN-OS SUBSYSTEM DASHBOARD (Machine-Native OS) v5.0          |
|       Legacy Names → MN-OS Names (Dual Recognition)               |
+====================================================================+

ID   Legacy Name                  MN-OS Name               Acro   Status
------------------------------------------------------------------------
M0   Foundations & Contracts      Kernel Primitives        KP     PASS
M1   Runtime Interfaces           Agent Runtime Kernel     ARK    PASS
M2   Skill Registration           OS Capability Table      OCT    PASS
M3   Core Skills                  Native OS Skills         NOS    PASS
M4   Workflow Engine              Agent Execution Engine   AXE    PASS
...
M19  Policy Constitutional        OS Constitution          OSC    PASS
------------------------------------------------------------------------

Summary: 20 PASS | 0 WARN | 0 FAIL
```

---

## Related Documents

- [docs/mn-os/subsystem_mapping.md](../mn-os/subsystem_mapping.md)
- [docs/mn-os/transition_guide.md](../mn-os/transition_guide.md)
- [docs/mn-os/architecture_overview.md](../mn-os/architecture_overview.md)
- [PIN-005: Machine-Native Architecture](PIN-005-machine-native-architecture.md)
- [PIN-033: M8-M14 Realignment](PIN-033-m8-m14-machine-native-realignment.md)
- [PIN-080: CI Consistency Checker v4.1](PIN-080-ci-consistency-checker-v41.md)

---

*Generated: 2025-12-15*
