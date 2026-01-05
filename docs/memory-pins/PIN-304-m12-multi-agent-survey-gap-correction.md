# PIN-304: M12 Multi-Agent Survey Gap Correction

**Status:** CORRECTION
**Created:** 2026-01-05
**Category:** Governance / Survey Integrity
**Corrects:** PIN-303

---

## Summary

PIN-303 (Frontend Constitution Alignment System Survey) under-represented M12 Multi-Agent Orchestration. This PIN documents the gap, provides the correction, and explains why it was missed.

---

## The Gap

### What PIN-303 Captured for M12

| Section | M12 Coverage | Status |
|---------|--------------|--------|
| A2. Services | Not listed | MISSING |
| B1. API | `/agents` endpoints only | PARTIAL |
| C1. Objects | `Agent` object only | INCOMPLETE |

### What M12 Actually Contains

**Location:** `/backend/app/agents/`

**7 Core Services:**
- JobService — Job queue management, SKIP LOCKED claiming
- WorkerService — Worker orchestration, parallel execution
- BlackboardService — Redis shared state for agent coordination
- MessageService — P2P messaging between agents
- RegistryService — Agent registry and discovery
- CreditService — Usage-based credit billing
- InvokeAuditService — Agent invocation audit trail

**4 Skills:**
- agent_invoke — Invoke another agent with correlation ID
- agent_spawn — Spawn child agent
- blackboard_ops — Read/write shared blackboard state
- llm_invoke_governed — LLM calls with governance

**SBA Subsystem (5 components):**
- sba/evolution — Strategy evolution
- sba/generator — Strategy generation
- sba/schema — SBA data schemas
- sba/service — SBA service layer
- sba/validator — Strategy validation

---

## Why It Was Missed

### Root Cause Analysis

| Factor | Explanation |
|--------|-------------|
| **1. Survey scope was breadth-focused** | Survey covered 8 sections (A-H) comprehensively, sacrificing depth on individual subsystems |
| **2. Frontend-biased framing** | Survey titled "Frontend Constitution Alignment" naturally prioritized customer-facing surfaces over internal infrastructure |
| **3. API-surface bias** | Explore agent prioritized API routers (38 of them) and customer endpoints over internal orchestration |
| **4. Path not in primary search patterns** | Survey targeted `/backend/app/api/`, `/backend/app/auth/`, `/backend/app/services/`, `/backend/app/models/` — but `/backend/app/agents/` is a separate module |
| **5. M12 is not customer-visible** | M12 powers execution but isn't directly exposed to customers — invisible to frontend-focused survey |
| **6. False confidence from CI validation** | Milestone check showed "M12 PASS (semantic: 2)" which masked the survey gap |
| **7. Service map was selective** | Section A2 listed "representative" services from governance work, not exhaustive enumeration |

### The Core Problem

> **The survey collected what customers see, not what the system does.**

M12 is infrastructure/execution layer. It's essential to how agents work, but it's not a customer console surface. The "Frontend Constitution Alignment" framing caused systematic under-representation of backend orchestration.

---

## Corrected Survey Data

### A2. Service Map (M12 Addition)

| Service Name | Layer | Owns Data (Y/N) | Mutates State (Y/N) | Exposed APIs |
|--------------|-------|-----------------|---------------------|--------------|
| JobService | L4 | N | Y | Internal (orchestrator) |
| WorkerService | L4/L5 | N | Y | Internal (workers) |
| BlackboardService | L4 | N | Y | Redis blackboard ops |
| MessageService | L4 | N | Y | P2P agent messaging |
| RegistryService | L4 | N | Y | Agent registry |
| CreditService | L4 | N | Y | Credit billing |
| InvokeAuditService | L4 | N | N | Audit trail |
| GovernanceService | L4 | N | Y | Agent governance |

### C1. Object Registry (M12 Addition)

| Object | Source of Truth | Mutable (Y/N) | Tenant-Scoped (Y/N) | Notes |
|--------|-----------------|---------------|---------------------|-------|
| AgentJob | L6 (PostgreSQL) | Y (state transitions) | Y | Job queue entries |
| BlackboardEntry | L6 (Redis) | Y | Y | Shared agent state |
| AgentMessage | L6 (PostgreSQL) | N (append-only) | Y | P2P messages |
| CreditLedger | L6 (PostgreSQL) | N (append-only) | Y | Usage credits |
| InvokeAudit | L6 (PostgreSQL) | N | Y | Invocation audit |

### Layer Classification

| Component | Layer | Role |
|-----------|-------|------|
| Agent Services | L4 | Domain engines (orchestration logic) |
| Agent Skills | L5 | Execution (agent_invoke, agent_spawn) |
| Blackboard (Redis) | L6 | Platform substrate (shared state) |
| Job Queue (PostgreSQL) | L6 | Platform substrate (persistence) |

---

## Lessons Learned

### For Future Surveys

1. **Enumerate all `/backend/app/` subdirectories** — Don't assume governance-mentioned services are exhaustive
2. **Separate "customer-visible" from "system-complete"** — Frontend survey ≠ system survey
3. **Check module `__init__.py` exports** — These declare the public interface
4. **Don't trust CI validation alone** — "M12 PASS" checks existence, not survey coverage
5. **Name the bias explicitly** — "Frontend Constitution" biased toward frontend; rename if system-wide needed

### Survey Integrity Rule

> **A survey must declare its scope explicitly. If it says "system survey" it must cover all layers. If it says "frontend survey" the gaps in backend must be acknowledged.**

PIN-303 was titled "Frontend Constitution Alignment" but was expected to be system-complete. This mismatch caused the gap.

---

## Files

- `/backend/app/agents/__init__.py` — M12 module root
- `/backend/app/agents/services/__init__.py` — M12 services
- `/backend/app/agents/skills/` — M12 skills
- `/backend/app/agents/sba/` — SBA subsystem

## References

- PIN-062 — M12 Multi-Agent System design
- PIN-063 — M12 implementation
- PIN-303 — Original survey (corrected by this PIN)

---

## Related PINs

- [PIN-303](PIN-303-frontend-constitution-alignment-system-survey.md) — Original survey
- [PIN-062](PIN-062-.md) — M12 design
- [PIN-063](PIN-063-.md) — M12 implementation
