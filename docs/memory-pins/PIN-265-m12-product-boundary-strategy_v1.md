# PIN-265: M12 Product Boundary Strategy

**Status:** ACTIVE
**Created:** 2026-01-01
**Category:** Architecture / Product Boundary
**Related PINs:** PIN-062 (agents schema), PIN-063 (M12.1 stabilization)

---

## Executive Summary

M12 (Agent Orchestration) is declared as an **Internal Capability Product**, not part of AI Console. This PIN establishes governance to prevent product boundary contamination while preserving future optionality.

---

## 1. What M12 Is Today (Post Slice-3 Truth)

From CI Rediscovery Slice-3, we learned:

> **M12 is infrastructure-dependent, environment-assumed code.**

Key facts:
- `agents` schema exists in **Neon (prod-like)** but not **local**
- Tests implicitly assume **remote infra**
- Failures were *misleading*, not functional
- Skipping was the correct action, not fixing logic

**Conclusion:** M12 = a semi-productized subsystem that assumes a managed environment.

---

## 2. The Three Distinct Things (Never Confuse)

| Thing | What It Is | Who It's For |
|-------|------------|--------------|
| **AI Console** | Customer-facing governed system | External users |
| **Infra Core** | Shared primitives, policies, CI truth | All products |
| **M12 Agents** | Capability product (agent orchestration) | Internal-first |

**M12 must be treated as an Internal Capability Product**, not part of AI Console.

---

## 3. Product Boundary Rules (MANDATORY)

### Rule 1: M12 Is Not AI Console

M12 has:
- Separate schema (`agents.*`)
- Separate infra assumptions
- Separate CI lane (capability-gated)
- No guarantees beyond infra presence

### Rule 2: No Direct Imports

> **AI Console must not import M12 modules directly.**
> Interaction must be via adapters or async events only.

Allowed patterns:
- Webhook
- Task queue
- API boundary
- Event record

Forbidden:
```python
# FORBIDDEN in AI Console paths
from app.agents.services.job_service import JobService
```

### Rule 3: Explicit Capability Declaration

Any code requiring M12 infra must declare it:
- `@requires_agents_schema` marker for tests
- `@requires_capability("agents")` for production code
- CI reports skipped-by-capability, not silent skip

---

## 4. Internal Usage Pattern

Internal tools (CRM agent, email reader, Slack bot) are:
- **Clients of M12**
- Not co-located inside AI Console logic
- Run in separate service/schema/CI lane

> "We dogfood M12 like an external user would."

---

## 5. Future Productization Path

When ready to productize (n8n / Replit / Lovable-style):

1. Promote **Internal Capability → Experimental Product**
2. Freeze:
   - Agent schema
   - Skill interface (llm_invoke, email, webhook, slack)
3. Add:
   - Provisioning
   - Auth
   - Usage limits
4. Add **new CI rediscovery cycle** for M12 alone

Because isolated early, this is **additive**, not invasive.

---

## 6. CI Signal Categories (Updated)

Slice-3 revealed infrastructure-dependent subsystems need explicit capability requirements:

| CI Signal Category | Example | Response |
|--------------------|---------|----------|
| Logic failures | Assertion wrong | Fix test or code |
| Schema drift | Constructor vs factory | Fix to use factories |
| Infra absence | agents schema missing | Explicit skip with marker |

---

## 7. What NOT To Do

Do **not**:
- Force local schema creation just to satisfy tests
- "Fix" skips by mocking infra deeply
- Merge M12 assumptions into infra core
- Treat M12 as "just another module"

---

## 8. Enforcement

Add to SESSION_PLAYBOOK:

```yaml
m12_boundary:
  status: ENFORCED
  rule: "AI Console must not import app.agents.* directly"
  interaction_patterns:
    - webhook
    - task_queue
    - api_boundary
    - event_record
  ci_markers:
    - "@requires_agents_schema"
    - "@requires_capability('agents')"
```

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-01-01 | Declare M12 as Internal Capability Product | Prevent AI Console contamination |
| 2026-01-01 | Establish no-direct-import rule | Keep M12 swappable |
| 2026-01-01 | Add explicit capability markers | CI signal quality |

---

## References

- `docs/ci/CI_REDISCOVERY_MASTER_ROADMAP.md` — Slice-3 findings
- `tests/test_m12_*.py` — Capability-gated tests
- PIN-062 — Agents schema definition
