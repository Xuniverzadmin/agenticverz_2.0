# AOS v1 Feature Freeze

**Status:** LOCKED
**Effective Date:** 2025-12-04
**Milestone:** M6a

---

## Purpose

This document defines the **locked feature set** for AOS v1. No new skills or major runtime features will be added after this milestone. Only bug fixes and security patches are permitted.

---

## v1 Locked Skills

### Core Skills (M3)

| Skill | Version | Purpose | Side Effects |
|-------|---------|---------|--------------|
| `http_call` | v0.2.0 | HTTP requests with retry/timeout | Network I/O |
| `llm_invoke` | v0.1.0 | LLM calls with cost tracking | API calls, token usage |
| `json_transform` | v0.1.0 | Deterministic JSON transforms | None (pure) |

### Database Skills

| Skill | Version | Purpose | Side Effects |
|-------|---------|---------|--------------|
| `postgres_query` | v0.1.0 | SQL queries with parameterization | Database I/O |

### Calendar Skills

| Skill | Version | Purpose | Side Effects |
|-------|---------|---------|--------------|
| `calendar_write` | v0.1.0 | Calendar event management | Calendar API |

### Notification Skills (Planned for M9, not v1)

These skills are **NOT included in v1** but are planned:
- `webhook_send` - M9
- `slack_send` - M9
- `email_send` - M9

---

## v1 Machine-Native APIs

### Runtime APIs (M5.5 - Complete)

| API | Endpoint | Purpose |
|-----|----------|---------|
| `runtime.simulate()` | `POST /api/v1/runtime/simulate` | Plan evaluation before execution |
| `runtime.query()` | `POST /api/v1/runtime/query` | Runtime state queries |
| `runtime.capabilities()` | `GET /api/v1/runtime/capabilities` | Available skills, budget, rate limits |
| `runtime.skills()` | `GET /api/v1/runtime/skills` | List available skills |
| `runtime.describe_skill()` | `GET /api/v1/runtime/skills/{id}` | Skill metadata with failure modes |

### Policy APIs (M5 - Complete)

| API | Endpoint | Purpose |
|-----|----------|---------|
| Policy evaluation | `POST /api/v1/policy/eval` | Evaluate skill execution policy |
| Approval requests | `POST /api/v1/policy/requests` | Create approval requests |
| Approval workflow | `POST /api/v1/policy/requests/{id}/approve` | Approve/reject requests |

---

## Runtime Infrastructure (Not Skills)

The following are **runtime infrastructure components**, not skills. They are subject to change in minor versions:

### Memory Integration (M7)

- `runtime.query("relevant_memories", goal, max_tokens)` - Memory retrieval
- Context window manager - Truncation and relevance scoring
- AgentProfile memory backend selection

**Clarification:** Memory is runtime infrastructure that enhances planning and context management. It is NOT a skill that agents invoke directly.

### Observability (M6)

- Prometheus metrics (`/metrics` endpoint)
- Trace storage and retrieval
- Run correlation IDs

### Workflow Engine (M4)

- Checkpoint/restore
- Golden replay validation
- Policy enforcement

---

## What's NOT in v1

The following features are explicitly **deferred to Phase 2 or later**:

| Feature | Deferred To | Reason |
|---------|-------------|--------|
| `code_execute` sandbox | Post-M10 | Security complexity |
| Adaptive runtime | M13 (Phase 2) | Needs run history data |
| Web console | M11 (Phase 2) | Frontend development |
| Human-in-the-loop UI | M11 (Phase 2) | Requires console |
| ML failure matching | M13 (Phase 2) | Needs training data |
| Multi-tenant isolation | Phase 2 | Enterprise feature |

---

## Change Control Process

### Allowed Changes After Freeze

1. **Bug fixes** - Fix incorrect behavior
2. **Security patches** - Address vulnerabilities
3. **Performance improvements** - No behavior change
4. **Documentation updates** - Clarifications only

### Prohibited Changes After Freeze

1. **New skills** - Add in Phase 2
2. **New runtime APIs** - Add in Phase 2
3. **Schema changes** - Breaks compatibility
4. **Behavior changes** - Violates determinism

### Exception Process

To request an exception:
1. Create a PIN documenting the change
2. Justify why it can't wait for Phase 2
3. Assess impact on determinism/replay
4. Get sign-off from PO

---

## Version Numbering

### v1.0.0 Release Criteria

- [ ] All M0-M7 milestones complete
- [ ] All exit criteria from PIN-024 (M6) met
- [ ] 60-second demo works end-to-end
- [ ] Python SDK passes all tests
- [ ] Documentation complete

### v1.x.y Patch Releases

- `x` - Major (v1 locked)
- `y` - Minor bug fixes and patches

---

## Sign-off

This feature freeze is effective immediately.

**Freeze Date:** 2025-12-04
**Signed By:** System (auto-generated)

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-04 | Initial feature freeze document |
