# M4: Internal Workflow Validation

**Status:** NOT STARTED
**Duration:** ~2 weeks
**Prerequisites:** M0-M3.5 Complete
**Last Updated:** 2025-12-01

---

## Mission Alignment

M4 validates that the machine-native runtime delivers on its core promises:
- **Deterministic execution** - Same inputs → Same outputs
- **Replay certification** - Workflows can be replayed from logs
- **Cost accountability** - Budget enforcement works correctly
- **Zero silent failures** - All errors are captured and categorized

---

## Objectives

1. **Internal Workflow Testing** - Run real multi-skill workflows through the runtime
2. **Determinism Certification** - Prove replay fidelity across workflow types
3. **Budget Enforcement Validation** - Verify hard ceiling enforcement
4. **Failure Catalog Coverage** - Ensure all error paths are mapped

---

## Deliverables

### D1: Workflow Test Suite (`tests/workflow/`)

| Test | Description | Coverage |
|------|-------------|----------|
| `test_simple_http_workflow.py` | Single http_call skill execution | Basic path |
| `test_llm_chain_workflow.py` | LLM invoke with chained transforms | Multi-skill |
| `test_budget_exceeded_workflow.py` | Workflow that hits budget ceiling | Cost control |
| `test_error_recovery_workflow.py` | Transient failure → retry → success | Resilience |
| `test_permanent_failure_workflow.py` | Non-retryable error handling | Error catalog |
| `test_mixed_skill_workflow.py` | http + llm + transform combined | Integration |

**Acceptance Criteria:**
- [ ] All workflows produce StructuredOutcome (never throw)
- [ ] All workflows record side_effects correctly
- [ ] All workflows are replayable from captured events
- [ ] Budget exceeded workflows halt with proper error code

### D2: Replay Certification Extension

Extend `tests/workflow/test_replay_certification.py`:

| Test | Description |
|------|-------------|
| `test_workflow_replay_http_call` | Replay http_call workflow |
| `test_workflow_replay_llm_invoke` | Replay llm_invoke workflow |
| `test_workflow_replay_mixed` | Replay mixed skill workflow |
| `test_replay_with_injected_failure` | Replay with simulated failure point |
| `test_replay_budget_behavior` | Verify budget checks during replay |

**Acceptance Criteria:**
- [ ] Replayed workflows produce byte-identical outputs (given same inputs)
- [ ] Replay mode respects captured timestamps
- [ ] Replay mode skips actual external calls (uses captured responses)

### D3: Budget Enforcement Validation

Create `tests/workflow/test_budget_enforcement.py`:

| Test | Description |
|------|-------------|
| `test_single_skill_budget_check` | Budget checked before skill execution |
| `test_workflow_budget_accumulation` | Budget tracks across multiple skills |
| `test_budget_exceeded_mid_workflow` | Workflow halts when budget exceeded |
| `test_budget_exceeded_error_code` | Correct error code returned |
| `test_budget_refund_on_failure` | Budget not charged for failed skills |

**Acceptance Criteria:**
- [ ] Budget is checked before each skill execution
- [ ] Workflow stops immediately when budget exceeded
- [ ] Error code is `BUDGET_EXCEEDED` (from error taxonomy)
- [ ] Budget tracking survives workflow retries

### D4: Failure Catalog Validation

Create `tests/workflow/test_failure_catalog.py`:

| Test | Description |
|------|-------------|
| `test_timeout_produces_timeout_error` | HTTP timeout → TIMEOUT code |
| `test_rate_limit_produces_resource_error` | 429 → RATE_LIMITED code |
| `test_4xx_produces_permanent_error` | 4xx → PERMANENT category |
| `test_5xx_produces_transient_error` | 5xx → TRANSIENT category |
| `test_validation_error_mapped` | Schema error → VALIDATION category |
| `test_all_error_codes_documented` | Every code has catalog entry |

**Acceptance Criteria:**
- [ ] All error codes in taxonomy are tested
- [ ] All error categories are tested
- [ ] Failure catalog is queryable at runtime
- [ ] Errors include retry hints

### D5: Observability Validation

Create `tests/workflow/test_observability.py`:

| Test | Description |
|------|-------------|
| `test_workflow_emits_metrics` | Prometheus metrics recorded |
| `test_skill_duration_histogram` | Skill latency tracked |
| `test_budget_metrics_accurate` | Budget counters match actual |
| `test_error_counters_increment` | Error metrics reflect failures |
| `test_replay_metrics_distinct` | Replay vs live distinguished |

**Acceptance Criteria:**
- [ ] All key metrics are emitted
- [ ] Metrics match actual behavior
- [ ] No metric gaps during workflows

---

## Non-Goals (Deferred to Later Milestones)

- External integration testing (M6)
- Memory persistence validation (M7)
- Multi-tenant isolation (Phase 2)
- Production load testing (Phase 2)

---

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| StructuredOutcome schema | ✅ Done | M0 |
| SkillMetadata schema | ✅ Done | M0 |
| ResourceContract schema | ✅ Done | M0 |
| Error taxonomy | ✅ Done | M0 |
| Runtime interfaces | ✅ Done | M1 |
| Skill registry | ✅ Done | M2 |
| http_call skill | ✅ Done | M3 |
| llm_invoke skill | ✅ Done | M3 |
| json_transform skill | ✅ Done | M3 |
| CLI demo | ✅ Done | M3.5 |
| Replay certification | ✅ Done | M3.5 |

---

## Test Infrastructure Required

### Fixtures

```python
# conftest.py additions
@pytest.fixture
def workflow_runtime():
    """Pre-configured runtime for workflow tests."""
    rt = Runtime(allow_external=False)  # Use stubs
    rt.register_skill("http_call", HttpCallSkill(allow_external=False))
    rt.register_skill("llm_invoke", LLMInvokeSkill(stub_mode=True))
    rt.register_skill("json_transform", JsonTransformSkill())
    return rt

@pytest.fixture
def budget_tracker():
    """Budget tracker with configurable ceiling."""
    return BudgetTracker(ceiling_cents=1000)

@pytest.fixture
def replay_recorder():
    """Records events for replay testing."""
    return ReplayRecorder()
```

### Mocks

```python
# Stubbed LLM responses for determinism
LLM_STUB_RESPONSES = {
    "summarize": {"text": "This is a summary.", "tokens": 50},
    "translate": {"text": "Translated text.", "tokens": 30},
    "analyze": {"text": "Analysis result.", "tokens": 100},
}

# Stubbed HTTP responses
HTTP_STUB_RESPONSES = {
    "https://api.github.com/zen": {"status": 200, "body": "Keep it logically awesome."},
    "https://httpstat.us/500": {"status": 500, "body": "Server error"},
}
```

---

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Workflow test coverage | 100% of deliverables | pytest --cov |
| Replay fidelity | 100% identical outputs | Byte comparison |
| Budget enforcement | 100% accurate | Test assertions |
| Error mapping | 100% codes tested | Catalog coverage |
| Zero exceptions | 0 uncaught exceptions | Test failures |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Flaky async tests | Medium | Medium | Use deterministic event loops |
| Stub response drift | Low | High | Golden file testing |
| Budget race conditions | Low | High | Atomic budget checks |
| Replay timestamp issues | Medium | Medium | Freeze time in tests |

---

## Timeline

| Week | Focus |
|------|-------|
| Week 1 | D1 (Workflow tests) + D2 (Replay extension) |
| Week 2 | D3 (Budget) + D4 (Failure catalog) + D5 (Observability) |

---

## Exit Criteria

M4 is complete when:

- [ ] All D1-D5 tests pass
- [ ] No xfailed tests
- [ ] No uncaught exceptions in any workflow
- [ ] Replay produces identical outputs
- [ ] Budget enforcement is atomic
- [ ] All error codes are tested
- [ ] CI pipeline includes M4 tests
- [ ] Documentation updated

---

## Post-M4 Readiness Checklist

Before starting M5 (Failure Catalog v1):

- [ ] M4 tests integrated into CI
- [ ] All M4 deliverables documented
- [ ] No regressions in M0-M3.5
- [ ] Performance baseline recorded
- [ ] Team retrospective completed

---

*Prepared: 2025-12-01*
*Author: AOS Development Team*
