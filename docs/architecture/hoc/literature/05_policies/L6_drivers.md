# Policies — L6 Drivers (14 files)

**Domain:** policies  
**Layer:** L6_drivers  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

---

## arbitrator.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/arbitrator.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 339

**Docstring:** Policy Arbitrator Engine

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyLimit` |  | Represents a policy limit. |
| `PolicyAction` |  | Represents a policy breach action. |
| `ArbitrationInput` |  | Input for policy arbitration. |
| `PolicyArbitrator` | __init__, arbitrate, _load_precedence_map, _get_precedence_map, _resolve_limit_conflict, _resolve_action_conflict | Resolves conflicts between multiple applicable policies. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_arbitrator` | `() -> PolicyArbitrator` | no | Get or create PolicyArbitrator singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `typing` | Optional | no |
| `sqlmodel` | Session, select | no |
| `app.db` | engine | no |
| `app.models.policy_precedence` | ArbitrationResult, ConflictStrategy, PolicyPrecedence | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`ACTION_SEVERITY`

---

## optimizer_conflict_resolver.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/optimizer_conflict_resolver.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 390

**Docstring:** Conflict resolution for PLang v2.0.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ConflictType` |  | Types of policy conflicts. |
| `PolicyConflict` | __str__ | A detected conflict between policies. |
| `ConflictResolver` | __init__, resolve, _detect_action_conflicts, _detect_priority_conflicts, _detect_category_conflicts, _detect_circular_dependencies, _get_condition_signature, _might_override (+6 more) | Resolves conflicts between policies. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum, auto | no |
| `typing` | Dict, List, Optional, Set, Tuple | no |
| `app.policy.compiler.grammar` | PLANG_GRAMMAR, ActionType, PolicyCategory | no |
| `app.policy.ir.ir_nodes` | IRAction, IRBlock, IRFunction, IRModule | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## policy_engine_driver.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/policy_engine_driver.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 1911

**Docstring:** Policy Engine Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyEngineDriver` | __init__, _get_engine, get_engine, fetch_ethical_constraints, fetch_risk_ceilings, fetch_safety_rules, fetch_business_rules, insert_evaluation (+86 more) | L6 driver for PolicyEngine data access. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_engine_driver` | `(db_url: str) -> PolicyEngineDriver` | no | Factory function for PolicyEngineDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `contextlib` | contextmanager | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional, Tuple | no |
| `sqlalchemy` | create_engine, text | no |
| `sqlalchemy.engine` | Connection, Engine | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`PolicyEngineDriver`, `get_policy_engine_driver`

---

## policy_graph_driver.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/policy_graph_driver.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 226

**Docstring:** Policy Graph Driver (L6 Data Access)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyGraphDriver` | __init__, fetch_active_policies, fetch_all_policies, fetch_active_limits, fetch_all_limits, fetch_resolved_conflicts | L6 Driver for policy graph data operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_graph_driver` | `(session: AsyncSession) -> PolicyGraphDriver` | no | Get a PolicyGraphDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## policy_proposal_read_driver.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/policy_proposal_read_driver.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 201

**Docstring:** Policy Proposal Read Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyProposalReadDriver` | __init__, fetch_unacknowledged_feedback, fetch_proposal_by_id, fetch_proposal_status, count_versions_for_proposal, fetch_proposals, check_rule_exists, fetch_rule_by_id | Read operations for policy proposals. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_proposal_read_driver` | `(session: AsyncSession) -> PolicyProposalReadDriver` | no | Factory function for PolicyProposalReadDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Optional | no |
| `uuid` | UUID | no |
| `sqlalchemy` | func, select, text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.feedback` | PatternFeedback | no |
| `app.models.policy` | PolicyProposal, PolicyVersion | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`PolicyProposalReadDriver`, `get_policy_proposal_read_driver`

---

## policy_proposal_write_driver.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/policy_proposal_write_driver.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 228

**Docstring:** Policy Proposal Write Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyProposalWriteDriver` | __init__, create_proposal, update_proposal_status, create_version, create_policy_rule, delete_policy_rule | Write operations for policy proposals. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_proposal_write_driver` | `(session: AsyncSession) -> PolicyProposalWriteDriver` | no | Factory function for PolicyProposalWriteDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `json` | json | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |
| `sqlalchemy` | text | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.policy` | PolicyProposal, PolicyVersion | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`PolicyProposalWriteDriver`, `get_policy_proposal_write_driver`

---

## policy_read_driver.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/policy_read_driver.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 243

**Docstring:** Policy Read Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TenantBudgetDataDTO` |  | Raw tenant budget settings from database. |
| `UsageSumDTO` |  | Raw usage sum from database. |
| `GuardrailDTO` |  | Raw guardrail data from database. |
| `PolicyReadDriver` | __init__, get_tenant_budget_settings, get_usage_sum_since, get_guardrail_by_id, list_all_guardrails, _to_guardrail_dto | L6 driver for customer policy read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_read_driver` | `(session: Session) -> PolicyReadDriver` | no | Get PolicyReadDriver instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime | no |
| `typing` | List, Optional | no |
| `pydantic` | BaseModel | no |
| `sqlalchemy` | and_, func, select | no |
| `sqlmodel` | Session | no |
| `app.models.killswitch` | DefaultGuardrail, ProxyCall | no |
| `app.models.tenant` | Tenant | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`PolicyReadDriver`, `get_policy_read_driver`, `TenantBudgetDataDTO`, `UsageSumDTO`, `GuardrailDTO`

---

## policy_rules_driver.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/policy_rules_driver.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 149

**Docstring:** Policy Rules Driver

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyRulesDriver` | __init__, fetch_rule_by_id, add_rule, add_integrity, create_rule, create_integrity, flush | Data access driver for policy rules. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_rules_driver` | `(session: AsyncSession) -> PolicyRulesDriver` | no | Factory function for PolicyRulesDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | TYPE_CHECKING, Optional | no |
| `sqlalchemy` | select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## policy_rules_read_driver.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/policy_rules_read_driver.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 255

**Docstring:** Policy Rules Read Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyRulesReadDriver` | __init__, fetch_policy_rules, fetch_policy_rule_by_id, count_policy_rules | Read operations for policy rules. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_rules_read_driver` | `(session: AsyncSession) -> PolicyRulesReadDriver` | no | Factory function for PolicyRulesReadDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timedelta, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Any, Optional | no |
| `sqlalchemy` | and_, func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.policy_control_plane` | PolicyEnforcement, PolicyRule, PolicyRuleIntegrity | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`PolicyRulesReadDriver`, `get_policy_rules_read_driver`

---

## proposals_read_driver.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/proposals_read_driver.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 413

**Docstring:** Proposals Read Driver (L6)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ProposalsReadDriver` | __init__, fetch_proposals, fetch_proposal_by_id, count_draft_proposals, list_proposals_paginated, get_proposal_stats, get_proposal_detail, list_proposal_versions | Read operations for policy proposals (list view). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_proposals_read_driver` | `(session: AsyncSession) -> ProposalsReadDriver` | no | Factory function for ProposalsReadDriver. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | Any, Optional | no |
| `sqlalchemy` | and_, func, select | no |
| `sqlalchemy.ext.asyncio` | AsyncSession | no |
| `app.models.policy` | PolicyProposal | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### __all__ Exports
`ProposalsReadDriver`, `get_proposals_read_driver`

---

## recovery_matcher.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/recovery_matcher.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 1011

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `MatchResult` |  | Result from matching a failure to a recovery suggestion. |
| `RecoveryMatcher` | __init__, _normalize_error, _calculate_time_weight, _compute_confidence, _generate_suggestion, _find_similar_failures, _count_occurrences, _get_cached_recovery (+10 more) | Matches failures to recovery suggestions using pattern matching |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.infra` | FeatureIntent, RetryPolicy | no |
| `hashlib` | hashlib | no |
| `logging` | logging | no |
| `math` | math | no |
| `os` | os | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | TYPE_CHECKING, Any, Dict, List, Optional (+1) | no |
| `app.security.sanitize` | sanitize_error_message | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`FEATURE_INTENT`, `RETRY_POLICY`, `HALF_LIFE_DAYS`, `EMBEDDING_SIMILARITY_THRESHOLD`, `LLM_ESCALATION_THRESHOLD`, `CACHE_TTL_SECONDS`, `LAMBDA`, `ALPHA`, `MIN_CONFIDENCE_THRESHOLD`, `NO_HISTORY_CONFIDENCE`, `EXACT_MATCH_CONFIDENCE`

---

## recovery_write_driver.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/recovery_write_driver.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 265

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RecoveryWriteService` | __init__, upsert_recovery_candidate, get_candidate_by_idempotency_key, enqueue_evaluation_db_fallback, update_recovery_candidate, insert_suggestion_provenance | Sync DB write operations for Recovery APIs. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `app.infra` | FeatureIntent, RetryPolicy | no |
| `typing` | Any, Dict, Optional, Tuple | no |
| `sqlalchemy` | text | no |
| `sqlmodel` | Session | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

### Constants
`FEATURE_INTENT`, `RETRY_POLICY`

---

## scope_resolver.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/scope_resolver.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 259

**Docstring:** Scope Resolver Engine

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `RunContext` |  | Context for scope resolution. |
| `ScopeResolutionResult` | to_snapshot | Result of scope resolution. |
| `ScopeResolver` | __init__, resolve_applicable_policies, _load_scopes, matches_scope, get_scope_for_policy, _get_scope | Resolves which policies apply to a given run context. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_scope_resolver` | `() -> ScopeResolver` | no | Get or create ScopeResolver singleton. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `typing` | Optional | no |
| `sqlmodel` | Session, select | no |
| `app.db` | engine | no |
| `app.models.policy_scope` | PolicyScope, ScopeType | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---

## symbol_table.py
**Path:** `backend/app/hoc/cus/policies/L6_drivers/symbol_table.py`  
**Layer:** L6_drivers | **Domain:** policies | **Lines:** 309

**Docstring:** Symbol table for PLang v2.0 compilation.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SymbolType` |  | Types of symbols in PLang. |
| `Symbol` | __repr__ | A symbol in the symbol table. |
| `Scope` | define, lookup, lookup_by_category, get_all_symbols | A scope in the symbol table. |
| `SymbolTable` | __init__, _define_builtins, enter_scope, exit_scope, define, lookup, lookup_policy, lookup_rule (+6 more) | Symbol table for PLang compilation. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `enum` | Enum, auto | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.policy.compiler.grammar` | PolicyCategory | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** DB operations — query building, data transformation, returns domain objects NOT ORM

**SHOULD call:** L7_models
**MUST NOT call:** L2_api, L3_adapters, L4_runtime, L5_engines
**Called by:** L5_engines, L4_runtime

---
