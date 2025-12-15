# MN-OS Transition Guide

**Version:** 1.0
**Created:** 2025-12-15
**Audience:** Contributors, Operators, Architects

---

## Purpose

This guide helps contributors and operators understand how **legacy milestone names (M0-M19)** map to **MN-OS subsystem names**, ensuring smooth transition as Agenticverz evolves into a Machine-Native Operating System.

---

## Quick Reference Card

| Legacy | MN-OS Subsystem | Acronym |
|--------|-----------------|---------|
| M0 | Kernel Primitives | KP |
| M1 | Agent Runtime Kernel | ARK |
| M2 | OS Capability Table | OCT |
| M3 | Native OS Skills | NOS |
| M4 | Agent Execution Engine | **AXE** |
| M5 | Constitutional Guardrail Layer | CGL |
| M6 | Resource Economics Engine | REE |
| M7 | System Memory Matrix | SMM |
| M8 | Identity Authority & Access Panel | **IAAP** |
| M9 | System Failure Intelligence Layer | **SFIL** |
| M10 | System Self-Repair Layer | SSRL |
| M11 | Cognitive Interface Kernel | **CIK** |
| M12 | MAS Orchestrator Core | MOC |
| M13 | OS Control Center | OCC |
| M14 | Cognitive Compliance Engine | CCE |
| M15 | Strategic Agency Kernel | **SAK** |
| M16 | Agent Oversight Authority | **AOA** |
| M17 | Cognitive Routing Kernel | **CRK** |
| M18 | Adaptive Governance Kernel | AGK |
| M19 | OS Constitution | OSC |

---

## For Contributors

### When Writing Code

```python
# GOOD: Include both names in docstrings
class WorkflowEngine:
    """
    M4: Workflow Engine (Legacy)
    MN-OS: Agent Execution Engine (AXE)

    Deterministic execution pipeline for agent workflows.
    """
    pass

# GOOD: Add MN-OS identifiers to module headers
# backend/app/workflow/engine.py
# ============================================================================
# M4 - Agent Execution Engine (AXE)
# Legacy: Workflow Engine [PIN-013/020]
# ============================================================================
```

### When Writing Tests

```python
# Tests can use either naming convention
class TestAXE:  # MN-OS name
    """Tests for Agent Execution Engine (M4 Workflow)"""

    def test_execution_plan_determinism(self):
        # Legacy class names still work
        from app.workflow.engine import ExecutionPlan
        ...
```

### When Writing Documentation

```markdown
## M4: Agent Execution Engine (AXE)

> **Legacy Name:** Workflow Engine
> **PIN Reference:** PIN-013/020

The Agent Execution Engine provides deterministic workflow execution...
```

---

## For Operators

### Log Patterns

Both naming conventions appear in logs:

```
# Legacy format
[M4] Workflow execution started: run_id=abc123

# MN-OS format
[AXE] Agent execution initiated: run_id=abc123
```

### Metrics

Prometheus metrics use both naming schemes:

```
# Legacy
nova_m4_workflow_executions_total

# MN-OS (future)
mnos_axe_executions_total
```

### Alerts

Alert rules reference both names:

```yaml
# alertmanager rule
- alert: WorkflowEngineHighLatency  # Legacy
  expr: nova_m4_workflow_latency_seconds > 5
  annotations:
    summary: "AXE (M4) execution latency high"  # MN-OS reference
```

---

## CI Consistency Checker Compatibility

The CI Consistency Checker v5.0 recognizes **both** naming conventions:

```bash
# Run standard check (recognizes both names)
./scripts/ops/ci_consistency_check.sh

# Run with subsystem view
./scripts/ops/ci_consistency_check.sh --subsystems

# Check specific subsystem by MN-OS name
./scripts/ops/ci_consistency_check.sh --subsystem AXE
```

### Detection Logic

```
IF legacy_patterns_found AND mnos_patterns_found → PASS (migrating)
IF legacy_patterns_found AND NOT mnos_patterns_found → PASS (legacy)
IF NOT legacy_patterns_found AND mnos_patterns_found → PASS (modern)
IF NOT legacy_patterns_found AND NOT mnos_patterns_found → FAIL
```

---

## Phased Migration

### Phase 1: Dual-Name Support (Current - v4.1+)

- CI recognizes both naming systems
- Code can use either naming convention
- Documentation introduces MN-OS names alongside legacy
- No breaking changes

### Phase 2: MN-OS Primary (M20+)

- New features use MN-OS names by default
- Legacy names remain supported
- Deprecation warnings for legacy-only usage
- Documentation prioritizes MN-OS names

### Phase 3: Legacy Sunset (v2.0+)

- Legacy names marked as deprecated
- Migration tools provided
- Final transition to pure MN-OS naming

---

## Common Mappings by Domain

### Execution Domain
```
M4 Workflow     → AXE (Agent Execution Engine)
M1 Runtime      → ARK (Agent Runtime Kernel)
M0 Foundations  → KP  (Kernel Primitives)
```

### Routing Domain
```
M17 CARE        → CRK (Cognitive Routing Kernel)
M18 CARE-L      → AGK (Adaptive Governance Kernel)
M15 SBA         → SAK (Strategic Agency Kernel)
```

### Safety Domain
```
M19 Policy      → OSC (OS Constitution)
M14 BudgetLLM   → CCE (Cognitive Compliance Engine)
M5 Policy API   → CGL (Constitutional Guardrail Layer)
```

### Recovery Domain
```
M9 Failure      → SFIL (System Failure Intelligence Layer)
M10 Recovery    → SSRL (System Self-Repair Layer)
```

---

## FAQ

### Q: Do I need to rename my existing code?

**A:** No. Legacy names continue to work. Add MN-OS names in comments/docstrings when modifying existing code.

### Q: Which names should I use in new code?

**A:** During Phase 1, either is acceptable. Prefer MN-OS names in docstrings and comments for forward compatibility.

### Q: Will CI break if I only use legacy names?

**A:** No. CI v5.0 accepts either naming convention.

### Q: Where can I find the official mapping?

**A:** See [subsystem_mapping.md](subsystem_mapping.md)

---

## Related Documents

- [Subsystem Mapping](subsystem_mapping.md)
- [Architecture Overview](architecture_overview.md)
- [PIN-081: MN-OS Naming Evolution](../memory-pins/PIN-081-mn-os-naming-evolution.md)

---

*Generated: 2025-12-15*
