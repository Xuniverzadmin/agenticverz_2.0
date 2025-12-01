# PIN-002: Critical Review - AOS Architecture & Plan

**Serial:** PIN-002
**Created:** 2025-11-30
**Status:** Active
**Category:** Architecture Review

---

## Executive Summary

The current plan is **directionally correct** but has **significant gaps** that will cause problems if not addressed before Phase 2. This review identifies architectural issues, missing pieces, and recommended changes.

---

## 1. WHAT'S GOOD (Keep)

### Infrastructure Foundation
- ✅ Worker pool with graceful shutdown - solid
- ✅ Prometheus metrics with proper labels - well done
- ✅ Alertmanager routing with secrets injection - production-ready
- ✅ Rerun tooling - operationally useful
- ✅ Skill registry pattern - extensible

### Code Quality
- ✅ SQLModel for ORM - clean, type-safe
- ✅ Protocol-based interfaces (PlannerProtocol, SkillInterface) - good abstraction
- ✅ Async skill execution - scalable
- ✅ Event publisher abstraction - decoupled

---

## 2. CRITICAL ISSUES (Must Fix)

### Issue 1: No Agent Entity Beyond Name

**Problem:** The `Agent` model is just an ID + name. Agents have no:
- Capabilities definition
- Default planner configuration
- Skill whitelist/blacklist
- Rate limits
- Quota/budget tracking
- Owner/permissions

**Impact:** Cannot build multi-tenant or capability-restricted agents.

**Fix:** Extend Agent model:
```python
class Agent(SQLModel, table=True):
    id: str
    name: str
    description: Optional[str]
    capabilities: Optional[str]  # JSON: allowed skills, limits
    planner_config: Optional[str]  # JSON: planner type, model, temperature
    owner_id: Optional[str]
    rate_limit_rpm: int = 60
    budget_cents: Optional[int]
    status: str  # active, paused, disabled
```

---

### Issue 2: Planner Has No Memory/Context

**Problem:** The planner receives `context_summary` and `memory_snippets` but:
- These are always `None` in the runner
- No actual memory retrieval happens
- No context window management
- No conversation history

**Impact:** Every run is stateless. Agent cannot learn or reference past actions.

**Fix:** Before planning:
1. Query recent memories for this agent
2. Build context summary from past runs
3. Implement context window truncation
4. Pass actual data to planner

---

### Issue 3: Skill Instantiation is Hardcoded

**Problem:** In `runner.py`:
```python
if skill_name == "calendar_write":
    instance = skill_cls(provider=os.getenv("CALENDAR_PROVIDER", "mock"))
else:
    instance = skill_cls(allow_external=True)
```

**Impact:** Adding a new skill requires modifying runner code. Not pluggable.

**Fix:** Skills should have a standard config interface:
```python
class SkillInterface:
    @classmethod
    def from_config(cls, config: dict) -> "SkillInterface":
        ...
```
And skill configs stored in registry or agent settings.

---

### Issue 4: No Input/Output Schema Validation

**Problem:** Skills accept `params: Dict[str, Any]` and return `Dict[str, Any]`. No validation.

**Impact:**
- Runtime errors from bad inputs
- Planner can generate invalid skill calls
- No IDE autocomplete or type safety
- Can't generate OpenAPI docs for skills

**Fix:** Use Pydantic models:
```python
class HttpCallInput(BaseModel):
    url: str
    method: str = "GET"
    headers: Optional[dict] = None
    body: Optional[str] = None

class HttpCallOutput(BaseModel):
    status_code: int
    body: str
    headers: dict
```

---

### Issue 5: No Step-Level Error Handling

**Problem:** If a skill fails mid-plan, the entire run fails. No:
- Continue-on-error option
- Fallback skills
- Partial success tracking
- Step-level retry (only run-level)

**Impact:** Brittle execution. One HTTP timeout kills the whole run.

**Fix:** Add step-level policies:
```python
{
  "step_id": "s1",
  "skill": "http_call",
  "params": {...},
  "on_error": "continue" | "abort" | "retry",
  "retry_count": 2,
  "fallback_skill": "cache_lookup"
}
```

---

### Issue 6: No Artifact/Output Storage

**Problem:** Run outputs are stored as JSON strings in `tool_calls_json`. No:
- Structured output storage
- Binary artifact handling (files, images)
- Output type classification
- Searchable results

**Impact:** Can't build useful queries like "show me all successful HTTP responses" or "find runs that produced PDF files".

**Fix:** Add Output/Artifact table:
```python
class RunArtifact(SQLModel, table=True):
    id: str
    run_id: str
    step_id: str
    artifact_type: str  # json, text, file, image
    content_json: Optional[str]
    file_path: Optional[str]
    mime_type: Optional[str]
    size_bytes: Optional[int]
    created_at: datetime
```

---

### Issue 7: Planner Contract is Undefined

**Problem:** The plan format is implicit:
```python
{"steps": [{"skill": "x", "params": {...}}]}
```
But there's no schema defining:
- Required vs optional fields
- Valid skill references
- Parameter format
- Conditional logic
- Parallel execution

**Impact:** Different planners may produce incompatible outputs.

**Fix:** Define explicit PlanSchema:
```python
class PlanStep(BaseModel):
    step_id: str
    skill: str
    params: dict
    depends_on: Optional[List[str]] = None
    condition: Optional[str] = None
    on_error: str = "abort"

class Plan(BaseModel):
    planner: str
    planner_version: str
    goal: str
    steps: List[PlanStep]
    metadata: Optional[dict] = None
```

---

## 3. GAPS IN THE ROADMAP

### Missing: Authentication & Multi-tenancy

The roadmap mentions "external developer agents" and "customer workflows" but there's no:
- User/tenant model
- API key scoping (currently one global key)
- Per-tenant quotas
- Audit logging per tenant

**When to add:** Before Phase 4 (Higher-level Agents)

---

### Missing: Async/Webhook Results

Currently runs are fire-and-forget with polling. No:
- Webhook callback on completion
- WebSocket streaming
- Event subscription

**When to add:** Phase 2 or 3

---

### Missing: Human-in-the-Loop

The vision mentions "human-in-loop pathways" but there's no design for:
- Approval gates
- Manual step execution
- User input mid-run
- Escalation triggers

**When to add:** Phase 3, design now

---

### Missing: Cost/Token Tracking

For LLM-based planners:
- No token counting
- No cost attribution
- No budget enforcement

**When to add:** Phase 2, with LLM skill

---

### Missing: Idempotency

No idempotency keys for:
- Goal submission
- Skill execution
- Reruns

**Impact:** Duplicate runs on network retry.

**When to add:** Phase 2

---

## 4. PHASE ORDER CRITIQUE

### Current Order (from PIN-001):
1. Runtime Foundation ✅
2. Core Agent Framework
3. System Skills
4. Higher-level Agents
5. Developer Experience
6. Production Infrastructure

### Issues:

**Problem 1:** Phase 2 and 3 are too interleaved.
You can't design skill interfaces without building a few skills first. You can't know what the planner needs without testing it.

**Recommendation:** Merge 2+3 into iterative cycles:
- Build 1 real skill → refine interface → build planner → test → iterate

**Problem 2:** Phase 6 (Production) is too late.
Security, auth, and multi-tenancy should be designed in Phase 2, not bolted on at the end.

**Recommendation:** Move auth/tenant model to Phase 2.

**Problem 3:** No testing phase.
Where's integration testing? Load testing? Chaos testing?

**Recommendation:** Add testing milestones after Phase 3.

---

## 5. RECOMMENDED REVISED PHASES

### Phase 2A: Core Contracts (1-2 days)
- Define PlanSchema with Pydantic
- Define SkillInput/SkillOutput base classes
- Define AgentCapabilities schema
- Add idempotency key to Run model

### Phase 2B: First Working Vertical (3-5 days)
- Build `http_call` skill with proper I/O schema
- Build `llm_invoke` skill (Claude API)
- Build basic LLM planner (not stub)
- Test: Goal → Plan → Execute → Output
- Fix issues discovered

### Phase 2C: Memory & Context (2-3 days)
- Implement memory retrieval before planning
- Add context window management
- Test multi-turn agent behavior

### Phase 2D: Error Handling & Resilience (2-3 days)
- Step-level error policies
- Partial success tracking
- Dead-letter queue for poison runs

### Phase 3: Expand Skills (1 week)
- File read/write
- Postgres query
- JSON transform
- Browser/scrape (optional)

### Phase 4: Auth & Multi-tenancy (3-5 days)
- User/tenant model
- Scoped API keys
- Per-tenant quotas
- Audit logging

### Phase 5: Higher Agents + Testing
- Build 2-3 useful agents
- Integration test suite
- Load testing

### Phase 6: Production Hardening
- Separate VPS
- Proper secrets management
- Backup/DR
- Monitoring tuning

---

## 6. SPECIFIC THINGS TO DO NOW

### Immediate (Before Writing More Code)

1. **Add Pydantic schemas for Plan and Skill I/O**
   - `app/schemas/plan.py`
   - `app/schemas/skill.py`

2. **Extend Agent model with capabilities**
   - Add fields, migration

3. **Add idempotency_key to Run model**
   - Prevent duplicate submissions

4. **Create a real LLM planner**
   - Even a simple one that calls Claude
   - Stub planner hides real problems

5. **Build http_call with proper schema**
   - Input: HttpCallInput
   - Output: HttpCallOutput
   - Validate in execute()

### Do NOT Do Yet

- ❌ Browser automation skill (complex, defer)
- ❌ Developer PAKs (premature)
- ❌ Multi-agent swarms (Phase 5+)
- ❌ Production deployment

---

## 7. QUESTIONS TO ANSWER

Before proceeding, decide:

1. **Single-tenant or multi-tenant first?**
   - If multi-tenant: design auth now
   - If single-tenant: defer, but don't create tech debt

2. **LLM provider?**
   - Claude (Anthropic) - recommended, you're already using it
   - OpenAI
   - Local (Ollama)
   - Multiple?

3. **Sync or async-first?**
   - Current: async skills, sync worker threads
   - Consider: full async with `asyncio` worker

4. **Artifact storage?**
   - Database (JSON blobs)
   - Object storage (S3/MinIO)
   - Local filesystem

5. **How will humans interact?**
   - API only?
   - Web UI?
   - CLI?
   - Slack bot?

---

## 8. SUMMARY

### Good
- Infrastructure is solid
- Abstractions are reasonable
- Monitoring is excellent

### Fix Before Phase 2
- Agent model too thin
- No memory/context retrieval
- Skill instantiation hardcoded
- No I/O validation
- No step-level error handling
- Plan schema undefined

### Revise Plan
- Merge Phase 2+3 into iterative cycles
- Add auth/tenancy earlier
- Add testing milestones
- Build real LLM planner early

### Priority Order
1. Define schemas (Plan, Skill I/O)
2. Extend Agent model
3. Build real LLM planner
4. Build http_call with validation
5. Add memory retrieval
6. Test end-to-end
7. Iterate

---

## 9. IMPLEMENTATION PROGRESS

### Completed (Phase 2A)

| Item | Status | Location |
|------|--------|----------|
| Plan Schema (Pydantic) | ✅ Done | `app/schemas/plan.py` |
| Skill I/O Schemas | ✅ Done | `app/schemas/skill.py` |
| Agent Schema | ✅ Done | `app/schemas/agent.py` |
| Artifact Schema | ✅ Done | `app/schemas/artifact.py` |
| Retry Policy Schema | ✅ Done | `app/schemas/retry.py` |
| Skill Registry (decorator) | ✅ Done | `app/skills/registry.py` |
| Factory Pattern | ✅ Done | `create_skill_instance()` |
| Validation Wrapper | ✅ Done | `app/skills/executor.py` |
| Agent Model Extended | ✅ Done | `app/db.py` - capabilities, budget, rate limits |
| Run Model Extended | ✅ Done | `app/db.py` - idempotency_key, parent_run_id |
| http_call with Schema | ✅ Done | Uses `@skill` decorator with HttpCallInput |

### Remaining (Phase 2B+)

| Item | Status | Priority |
|------|--------|----------|
| Real LLM Planner | ⏳ Pending | HIGH |
| Memory Retrieval | ⏳ Pending | HIGH |
| Step-level Error Handling | ⏳ Pending | HIGH |
| Artifact Storage | ⏳ Pending | MEDIUM |

---

## Changelog

| Date | Change |
|------|--------|
| 2025-11-30 | Initial critical review |
| 2025-11-30 | Completed Phase 2A: schemas, registry, validation, model extensions |
