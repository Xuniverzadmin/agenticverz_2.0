# MN-OS Subsystem Mapping

**Version:** 1.0
**Created:** 2025-12-15
**Status:** Canonical Reference

---

## Overview

This document maps **Agenticverz Milestones (M0-M19)** to their **evolved MN-OS subsystem names**. This naming evolution reflects the architectural maturity of the system as it transitions from a milestone-based development model to a **Machine-Native Operating System (MN-OS)**.

---

## Naming Evolution Stages

| Stage | Description |
|-------|-------------|
| **Current** | Original milestone names (M0-M19) |
| **Evolved** | Architectural subsystem names |
| **MN-OS** | Final OS-level subsystem identifiers |

---

## Complete Milestone → Subsystem Mapping

### Kernel & Primitives Layer

| Milestone | PIN | Current Name | Evolved Name | MN-OS Name |
|-----------|-----|--------------|--------------|------------|
| **M0** | PIN-009 | Foundations & Contracts | System Primitives Layer | **Kernel Primitives** |
| **M1** | PIN-009 | Runtime Interfaces | Execution Runtime Layer | **Agent Runtime Kernel** |

### Capability & Skills Layer

| Milestone | PIN | Current Name | Evolved Name | MN-OS Name |
|-----------|-----|--------------|--------------|------------|
| **M2** | PIN-010 | Skill Registration | Capability Registry | **OS Capability Table** |
| **M3** | PIN-010 | Core Skill Implementations | System Capability Pack | **Native OS Skills** |

### Execution & Workflow Layer

| Milestone | PIN | Current Name | Evolved Name | MN-OS Name |
|-----------|-----|--------------|--------------|------------|
| **M4** | PIN-013/020 | Workflow Engine | Deterministic Execution Engine | **Agent Execution Engine (AXE)** |
| **M5** | PIN-021 | Policy API & Approval | Policy Enforcement Layer | **Constitutional Guardrail Layer** |

### Resource & Memory Layer

| Milestone | PIN | Current Name | Evolved Name | MN-OS Name |
|-----------|-----|--------------|--------------|------------|
| **M6** | PIN-026 | Feature Freeze & CostSim V2 | Predictive Cost Governor | **Resource Economics Engine** |
| **M7** | PIN-031/032 | Memory Integration | Memory & Context Plane | **System Memory Matrix** |

### Identity & Access Layer

| Milestone | PIN | Current Name | Evolved Name | MN-OS Name |
|-----------|-----|--------------|--------------|------------|
| **M8** | PIN-033 | SDK Packaging & Auth | Access & Identity Layer | **Identity Authority & Access Panel (IAAP)** |

### Failure & Recovery Layer

| Milestone | PIN | Current Name | Evolved Name | MN-OS Name |
|-----------|-----|--------------|--------------|------------|
| **M9** | PIN-048 | Failure Catalog Persistence | Failure Pattern Engine | **System Failure Intelligence Layer (SFIL)** |
| **M10** | PIN-050 | Recovery Suggestion Engine | Autonomous Recovery Engine | **System Self-Repair Layer** |

### Cognitive Interface Layer

| Milestone | PIN | Current Name | Evolved Name | MN-OS Name |
|-----------|-----|--------------|--------------|------------|
| **M11** | PIN-055/060 | Store Factories & LLM Adapters | Model Interface Layer | **Cognitive Interface Kernel** |

### Multi-Agent Orchestration Layer

| Milestone | PIN | Current Name | Evolved Name | MN-OS Name |
|-----------|-----|--------------|--------------|------------|
| **M12** | PIN-062/063 | Multi-Agent System | Multi-Agent Orchestration Graph | **MAS Orchestrator Core** |
| **M13** | PIN-064 | Console UI & Boundary Checklist | Governance Console | **OS Control Center** |

### Safety & Compliance Layer

| Milestone | PIN | Current Name | Evolved Name | MN-OS Name |
|-----------|-----|--------------|--------------|------------|
| **M14** | PIN-070 | BudgetLLM Safety Governance | Cognitive Safety & Cost Governance | **Cognitive Compliance Engine** |

### Strategic Agency Layer

| Milestone | PIN | Current Name | Evolved Name | MN-OS Name |
|-----------|-----|--------------|--------------|------------|
| **M15** | PIN-072 | SBA Foundations | Strategic Agent Foundations | **Strategic Agency Kernel** |
| **M16** | PIN-074 | Agent Governance Console | Agent Oversight Dashboard | **Agent Oversight Authority** |

### Routing & Learning Layer

| Milestone | PIN | Current Name | Evolved Name | MN-OS Name |
|-----------|-----|--------------|--------------|------------|
| **M17** | PIN-075 | CARE Routing Engine | Adaptive Routing & Execution Engine | **Cognitive Routing Kernel (CRK)** |
| **M18** | PIN-076 | CARE-L & SBA Evolution | Learning Governance Engine | **Adaptive Governance Kernel** |

### Constitutional Layer

| Milestone | PIN | Current Name | Evolved Name | MN-OS Name |
|-----------|-----|--------------|--------------|------------|
| **M19** | PIN-078 | Policy Layer Constitutional | Constitutional Reasoning Layer | **OS Constitution + Interpretive Engine** |

---

## MN-OS Architecture Stack

```
+===================================================================+
|                    MN-OS v1 (Machine-Native OS)                   |
+===================================================================+

  ┌─────────────────────────────────────────────────────────────────┐
  │              CONSTITUTION & GOVERNANCE LAYER                    │
  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
  │  │ M19: OS         │ │ M18: Adaptive   │ │ M14: Cognitive  │   │
  │  │ Constitution    │ │ Governance      │ │ Compliance      │   │
  │  │                 │ │ Kernel          │ │ Engine          │   │
  │  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │            ROUTING, STRATEGY & MULTI-AGENT LAYER                │
  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
  │  │ M17: CRK    │ │ M15: SAK    │ │ M12: MAS    │ │ M16: AOA  │ │
  │  │ (Routing)   │ │ (Strategy)  │ │ Orchestrator│ │ (Oversight│ │
  │  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │                EXECUTION & RECOVERY LAYER                       │
  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
  │  │ M4: AXE         │ │ M10: Self-Repair│ │ M9: SFIL        │   │
  │  │ (Execution)     │ │ Layer           │ │ (Failure Intel) │   │
  │  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │           CAPABILITY, SKILL & COGNITIVE IO LAYER                │
  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌─────────────────┐ │
  │  │ M3: Native│ │ M2: OS    │ │ M11: CIK  │ │ M6: Resource    │ │
  │  │ OS Skills │ │ Cap Table │ │ (Cog I/O) │ │ Economics       │ │
  │  └───────────┘ └───────────┘ └───────────┘ └─────────────────┘ │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │              KERNEL PRIMITIVES & MEMORY LAYER                   │
  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐   │
  │  │ M0: Kernel      │ │ M1: Agent       │ │ M7: System      │   │
  │  │ Primitives      │ │ Runtime Kernel  │ │ Memory Matrix   │   │
  │  └─────────────────┘ └─────────────────┘ └─────────────────┘   │
  └─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │              ACCESS, AUTH & PACKAGING LAYER                     │
  │  ┌─────────────────────────────────────────────────────────┐   │
  │  │ M8: Identity Authority & Access Panel (IAAP)            │   │
  │  └─────────────────────────────────────────────────────────┘   │
  │  ┌─────────────────────────────────────────────────────────┐   │
  │  │ M13: OS Control Center (Governance Console)             │   │
  │  └─────────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────┘
```

---

## Subsystem Acronyms

| Acronym | Full Name | Milestone |
|---------|-----------|-----------|
| **AXE** | Agent Execution Engine | M4 |
| **CRK** | Cognitive Routing Kernel | M17 |
| **SAK** | Strategic Agency Kernel | M15 |
| **SFIL** | System Failure Intelligence Layer | M9 |
| **CIK** | Cognitive Interface Kernel | M11 |
| **IAAP** | Identity Authority & Access Panel | M8 |
| **MAS** | Multi-Agent System | M12 |
| **AOA** | Agent Oversight Authority | M16 |

---

## CI Detection Patterns

The CI Consistency Checker v5.0 recognizes both legacy and MN-OS names:

```bash
# M4 detection patterns (any match = PASS)
grep -rqE "ExecutionPlan|WorkflowStep|CheckpointState|Deterministic Execution Engine|Agent Execution Engine|AXE"

# M17 detection patterns
grep -rqE "CARE|CARERouter|Cognitive Routing Kernel|CRK|5.*stage.*pipeline"

# M19 detection patterns
grep -rqE "Policy.*Constitutional|OS Constitution|Interpretive Engine|safety.*category"
```

---

## Migration Path

### Phase 1: Dual-Name Support (Current)
- CI recognizes both legacy and MN-OS names
- Documentation uses both naming systems
- Code comments introduce MN-OS identifiers

### Phase 2: Evolved Names (M20+)
- New code uses evolved/MN-OS names
- Legacy names remain for backward compatibility
- Documentation prioritizes MN-OS names

### Phase 3: Full MN-OS (Post v1.0)
- Legacy names deprecated (not removed)
- All new development uses MN-OS names
- Architecture diagrams use MN-OS exclusively

---

## Related Documents

- [Transition Guide](transition_guide.md)
- [Architecture Overview](architecture_overview.md)
- [PIN-033: M8-M14 Machine-Native Realignment](../memory-pins/PIN-033-m8-m14-machine-native-realignment.md)
- [PIN-081: MN-OS Naming Evolution](../memory-pins/PIN-081-mn-os-naming-evolution.md)

---

*Generated: 2025-12-15*
*Version: 1.0*
