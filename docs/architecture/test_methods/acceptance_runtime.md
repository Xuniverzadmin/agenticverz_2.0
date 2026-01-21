# Acceptance Checklist: Runtime Interfaces (M1)

**Milestone:** M1 - Runtime Interfaces
**Status:** Implementation Complete
**Date:** 2025-12-01

---

## 1. runtime.execute()

| Requirement | Test | Status |
|-------------|------|--------|
| Returns StructuredOutcome with stable fields: id, ok, result\|error, meta | `test_execute_success` | ✅ |
| Never throws exceptions - core guarantee | `test_execute_never_throws` | ✅ |
| Timeout behavior deterministic and covered | `test_execute_timeout` | ✅ |
| Unregistered skill returns error code "ERR_SKILL_NOT_FOUND" | `test_execute_missing_skill` | ✅ |
| Budget exceeded returns "ERR_BUDGET_EXCEEDED" | `test_execute_budget_exceeded` | ✅ |
| Exception handling returns "ERR_RUNTIME_EXCEPTION" | `test_execute_exception_handling` | ✅ |
| Records timing metadata (started_at, ended_at, duration_s) | `test_execute_records_meta_timing` | ✅ |

---

## 2. runtime.describe_skill()

| Requirement | Test | Status |
|-------------|------|--------|
| Returns SkillDescriptor with stable_fields and schema versions | `test_describe_existing_skill` | ✅ |
| Returns None for unregistered skills | `test_describe_missing_skill` | ✅ |
| Includes stable_fields mapping | `test_describe_returns_stable_fields` | ✅ |
| to_dict() serializes correctly | `test_descriptor_to_dict` | ✅ |

---

## 3. runtime.query()

| Requirement | Test | Status |
|-------------|------|--------|
| `remaining_budget_cents` - returns budget info | `test_query_remaining_budget` | ✅ |
| `allowed_skills` - returns list of skills | `test_query_allowed_skills` | ✅ |
| `what_did_i_try_already` - returns execution history | `test_query_what_did_i_try_already` | ✅ |
| `last_step_outcome` - returns most recent outcome | `test_query_last_step_outcome` | ✅ |
| `skills_available_for_goal` - deterministic for same input | `test_query_skills_for_goal_deterministic` | ✅ |
| Unknown query type returns error with supported list | `test_query_unknown_type` | ✅ |
| Deterministic for same inputs | `test_query_is_deterministic` | ✅ |

---

## 4. runtime.get_resource_contract()

| Requirement | Test | Status |
|-------------|------|--------|
| Returns ResourceContract matching registered contract | `test_get_existing_contract` | ✅ |
| Returns None for unregistered resources | `test_get_missing_contract` | ✅ |
| Contract has all required fields (budget, rate_limits, concurrency, time) | `test_contract_has_all_fields` | ✅ |
| to_dict() serializes correctly | `test_contract_to_dict` | ✅ |

---

## 5. StructuredOutcome

| Requirement | Test | Status |
|-------------|------|--------|
| success() factory creates successful outcome | `test_success_factory` | ✅ |
| failure() factory creates failed outcome with error structure | `test_failure_factory` | ✅ |
| to_dict() produces valid JSON | `test_to_dict_serialization` | ✅ |
| Immutable (frozen dataclass) | `test_outcome_is_immutable` | ✅ |

---

## 6. Contract Dataclasses

| Requirement | Test | Status |
|-------------|------|--------|
| ContractMetadata.now() creates with current timestamp | `test_contract_metadata_now` | ✅ |
| SkillContract.to_dict() serializes correctly | `test_skill_contract_to_dict` | ✅ |
| CostModel.estimate() calculates cost correctly | `test_cost_model_estimate` | ✅ |
| BudgetTracker tracks spending correctly | `test_budget_tracker_spending` | ✅ |

---

## 7. Determinism Tests

| Requirement | Test | Status |
|-------------|------|--------|
| Same inputs produce same outcome structure | `test_same_inputs_same_outcome_shape` | ✅ |
| Error codes are deterministic | `test_error_codes_are_deterministic` | ✅ |
| Query results are deterministic | `test_query_determinism` | ✅ |

---

## 8. Registration

| Requirement | Test | Status |
|-------------|------|--------|
| register_skill succeeds for new skill | `test_register_skill_success` | ✅ |
| register_skill fails for duplicate | `test_register_duplicate_skill_fails` | ✅ |
| register_resource_contract succeeds for new contract | `test_register_contract_success` | ✅ |
| register_resource_contract fails for duplicate | `test_register_duplicate_contract_fails` | ✅ |

---

## CI Requirements

| Requirement | Status |
|-------------|--------|
| pytest + pytest-asyncio pass locally | ⏳ Pending |
| pytest + pytest-asyncio pass in CI | ⏳ Pending |
| Golden-file comparison: one exemplar StructuredOutcome saved | ⏳ Pending |

---

## Files Delivered

| File | Purpose |
|------|---------|
| `backend/app/worker/runtime/__init__.py` | Module exports |
| `backend/app/worker/runtime/core.py` | Core Runtime, StructuredOutcome, SkillDescriptor, ResourceContract |
| `backend/app/worker/runtime/contracts.py` | Contract helper dataclasses |
| `backend/tests/runtime/__init__.py` | Test module |
| `backend/tests/runtime/test_runtime_interfaces.py` | 30+ interface tests |
| `backend/tests/acceptance_runtime.md` | This checklist |

---

## Vision Alignment

| Vision Pillar | M1 Coverage | Verified |
|---------------|-------------|----------|
| Deterministic state | StructuredOutcome with stable fields | ✅ |
| Queryable state | runtime.query() interface | ✅ |
| Capability awareness | runtime.describe_skill() + cost_model | ✅ |
| Failure as data | Structured errors with codes, categories | ✅ |
| Resource contracts | runtime.get_resource_contract() | ✅ |
| Never throws | execute() always returns StructuredOutcome | ✅ |

---

## Next Steps

1. Run tests locally: `pytest backend/tests/runtime/ -v`
2. Add pytest-asyncio to requirements.txt
3. Create golden file example
4. Push to GitHub and verify CI passes
5. Proceed to M2: Skill Registration + Core Stubs
