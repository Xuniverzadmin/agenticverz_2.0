# MN-OS Architecture Overview

**Version:** 1.0
**Created:** 2025-12-15
**Status:** Reference Architecture

---

## Vision

**MN-OS (Machine-Native Operating System)** is an operating system designed for autonomous agents, not humans. It provides:

- **Predictable** execution through deterministic workflows
- **Reliable** operation through self-repair mechanisms
- **Deterministic** outcomes through seed-based reproducibility
- **Safe** operation through constitutional governance

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MN-OS v1 ARCHITECTURE                       │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 6: CONSTITUTIONAL GOVERNANCE                                  │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐              │
│ │ OS            │ │ Adaptive      │ │ Cognitive     │              │
│ │ Constitution  │ │ Governance    │ │ Compliance    │              │
│ │ (M19)         │ │ Kernel (M18)  │ │ Engine (M14)  │              │
│ └───────────────┘ └───────────────┘ └───────────────┘              │
│ Policy interpretation, learning governance, safety compliance       │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Policy Decisions
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 5: STRATEGIC ROUTING                                          │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐              │
│ │ Cognitive     │ │ Strategic     │ │ Agent         │              │
│ │ Routing (M17) │ │ Agency (M15)  │ │ Oversight(M16)│              │
│ └───────────────┘ └───────────────┘ └───────────────┘              │
│ CARE routing, strategy-bound agents, oversight dashboard            │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Routing Decisions
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 4: MULTI-AGENT ORCHESTRATION                                  │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ MAS Orchestrator Core (M12)                                   │  │
│ │ Agent coordination, credit management, blackboard state       │  │
│ └───────────────────────────────────────────────────────────────┘  │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ OS Control Center (M13) - Governance Console UI               │  │
│ └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Agent Requests
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 3: EXECUTION & RECOVERY                                       │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐              │
│ │ Agent         │ │ Self-Repair   │ │ Failure       │              │
│ │ Execution(M4) │ │ Layer (M10)   │ │ Intel (M9)    │              │
│ └───────────────┘ └───────────────┘ └───────────────┘              │
│ Deterministic workflows, recovery suggestions, failure patterns     │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Execution Requests
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 2: CAPABILITY & COGNITIVE I/O                                 │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐              │
│ │ Capability    │ │ Native OS     │ │ Cognitive     │              │
│ │ Table (M2)    │ │ Skills (M3)   │ │ Interface(M11)│              │
│ └───────────────┘ └───────────────┘ └───────────────┘              │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ Resource Economics Engine (M6) - Cost simulation & budgets    │  │
│ └───────────────────────────────────────────────────────────────┘  │
│ Skill registration, LLM adapters, cost governance                   │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Skill Invocations
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 1: KERNEL & MEMORY                                            │
│ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐              │
│ │ Kernel        │ │ Agent Runtime │ │ Memory        │              │
│ │ Primitives(M0)│ │ Kernel (M1)   │ │ Matrix (M7)   │              │
│ └───────────────┘ └───────────────┘ └───────────────┘              │
│ Type contracts, execution runtime, context persistence              │
└─────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Auth/Identity
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 0: IDENTITY & ACCESS                                          │
│ ┌───────────────────────────────────────────────────────────────┐  │
│ │ Identity Authority & Access Panel (M8) - IAAP                 │  │
│ │ SDK packaging, authentication, RBAC                           │  │
│ └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Subsystem Responsibilities

### Layer 6: Constitutional Governance

| Subsystem | Responsibility |
|-----------|----------------|
| **OS Constitution (M19)** | Policy interpretation, 5-category rules (Safety, Privacy, Operational, Routing, Custom) |
| **Adaptive Governance Kernel (M18)** | Learning from feedback, oscillation detection, rollback mechanisms |
| **Cognitive Compliance Engine (M14)** | BudgetLLM safety, cost envelopes, risk scoring |

### Layer 5: Strategic Routing

| Subsystem | Responsibility |
|-----------|----------------|
| **Cognitive Routing Kernel (M17)** | 5-stage CARE pipeline, capability probes, risk-aware routing |
| **Strategic Agency Kernel (M15)** | Strategy-bound agents, cascade validation, semantic dependencies |
| **Agent Oversight Authority (M16)** | Governance dashboard, SBA inspector, fulfillment heatmaps |

### Layer 4: Multi-Agent Orchestration

| Subsystem | Responsibility |
|-----------|----------------|
| **MAS Orchestrator Core (M12)** | Agent coordination, planner, blackboard, credit management |
| **OS Control Center (M13)** | Console UI, monitoring dashboards, boundary checklists |

### Layer 3: Execution & Recovery

| Subsystem | Responsibility |
|-----------|----------------|
| **Agent Execution Engine (M4)** | Deterministic workflows, checkpoints, golden-run replay |
| **System Self-Repair Layer (M10)** | Recovery suggestions, leader election, outbox processing |
| **System Failure Intelligence Layer (M9)** | Failure pattern persistence, R2 storage, aggregation |

### Layer 2: Capability & Cognitive I/O

| Subsystem | Responsibility |
|-----------|----------------|
| **OS Capability Table (M2)** | Skill registration, versioning, capability contracts |
| **Native OS Skills (M3)** | Core skills: http_call, json_transform, llm_invoke, slack_send |
| **Cognitive Interface Kernel (M11)** | LLM adapters, tokenizer metering, embedding services |
| **Resource Economics Engine (M6)** | CostSim V2, drift detection, circuit breakers |

### Layer 1: Kernel & Memory

| Subsystem | Responsibility |
|-----------|----------------|
| **Kernel Primitives (M0)** | Database models, migrations, type contracts, async engine |
| **Agent Runtime Kernel (M1)** | Execution runtime, query interfaces, skill descriptors |
| **System Memory Matrix (M7)** | Memory PINs, RBAC, context persistence, TTL management |

### Layer 0: Identity & Access

| Subsystem | Responsibility |
|-----------|----------------|
| **Identity Authority & Access Panel (M8)** | SDK packaging, authentication, API key management |

---

## Data Flow

```
External Request
       │
       ▼
┌──────────────────┐
│  IAAP (M8)       │ ─── Auth & Identity
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  CRK (M17)       │ ─── Route to appropriate agent/skill
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  OSC (M19)       │ ─── Check policy compliance
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  SAK (M15)       │ ─── Validate strategy cascade
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  MOC (M12)       │ ─── Orchestrate multi-agent execution
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  AXE (M4)        │ ─── Execute deterministic workflow
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  NOS (M3)        │ ─── Invoke skills
└──────────────────┘
       │
       ▼
┌──────────────────┐
│  AGK (M18)       │ ─── Record feedback, adjust routing
└──────────────────┘
       │
       ▼
    Response
```

---

## Key Design Principles

### 1. Machine-Native, Not Human-Native

- Agents query execution context, not parse logs
- Structured outcomes, never exceptions
- Failure as navigable data
- Pre-execution simulation

### 2. Constitutional by Default

- All actions pass through policy layer
- Safety categories enforced at OS level
- Audit trail for all decisions

### 3. Self-Optimizing

- CARE-L learns from execution feedback
- Routing weights adjust automatically
- Oscillation detection prevents thrashing

### 4. Deterministic Replay

- Seed-based reproducibility
- Golden-run comparison
- Checkpoint serialization

---

## Future: M20+

**M20: Machine-Native OS v1.0** will unify all subsystems under a single coherent OS interface:

- Unified syscall-like API
- Cross-subsystem communication bus
- Plugin architecture for extensions
- Marketplace for agents and skills

---

## Related Documents

- [Subsystem Mapping](subsystem_mapping.md)
- [Transition Guide](transition_guide.md)
- [PIN-005: Machine-Native Architecture](../memory-pins/PIN-005-machine-native-architecture.md)
- [PIN-033: M8-M14 Realignment](../memory-pins/PIN-033-m8-m14-machine-native-realignment.md)

---

*Generated: 2025-12-15*
