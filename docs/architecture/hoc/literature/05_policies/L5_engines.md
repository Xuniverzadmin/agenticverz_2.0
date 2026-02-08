# Policies — L5 Engines (51 files)

**Domain:** policies  
**Layer:** L5_engines  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

**Layer Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

---

## ast.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/ast.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 381

**Docstring:** Policy DSL Abstract Syntax Tree (AST) Definitions

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `Scope` |  | Policy scope determines visibility boundaries. |
| `Mode` |  | Policy mode determines enforcement semantics. |
| `Comparator` |  | Comparison operators for predicates. |
| `LogicalOperator` |  | Logical operators for compound conditions. |
| `WarnAction` | to_dict | Emit a warning message. |
| `BlockAction` | to_dict | Block execution. |
| `RequireApprovalAction` | to_dict | Require human approval before proceeding. |
| `Predicate` | to_dict | A simple comparison predicate. |
| `ExistsPredicate` | to_dict | Check if a metric exists. |
| `LogicalCondition` | to_dict | A compound condition combining two conditions with AND/OR. |
| `Clause` | __post_init__, to_dict | A single when-then clause. |
| `PolicyMetadata` | __post_init__, to_dict | Policy metadata header. |
| `PolicyAST` | __post_init__, to_dict, to_json, compute_hash, name, version, scope, mode | Root AST node for a complete policy. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `is_predicate` | `(condition: Condition) -> bool` | no | Check if condition is a simple predicate. |
| `is_exists_predicate` | `(condition: Condition) -> bool` | no | Check if condition is an exists predicate. |
| `is_logical_condition` | `(condition: Condition) -> bool` | no | Check if condition is a compound logical condition. |
| `is_warn_action` | `(action: Action) -> bool` | no | Check if action is a WARN action. |
| `is_block_action` | `(action: Action) -> bool` | no | Check if action is a BLOCK action. |
| `is_require_approval_action` | `(action: Action) -> bool` | no | Check if action is a REQUIRE_APPROVAL action. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `dataclasses` | dataclass, field | no |
| `enum` | Enum | no |
| `typing` | Any, Literal, Union | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## authority_checker.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/authority_checker.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 284

**Docstring:** Module: authority_checker

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `OverrideStatus` |  | Status of an override check. |
| `OverrideCheckResult` | to_dict | Result of an override authority check. |
| `OverrideAuthorityChecker` | check, _is_override_active, check_from_dict | Checks override authority status for the prevention engine. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `should_skip_enforcement` | `(override_authority: Any) -> bool` | no | Quick helper to check if enforcement should be skipped. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## binding_moment_enforcer.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/binding_moment_enforcer.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 276

**Docstring:** Module: binding_moment_enforcer

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `BindingMoment` |  | When a policy should be evaluated. |
| `EvaluationPoint` |  | Current point in execution where evaluation is requested. |
| `BindingDecision` |  | Decision about whether to evaluate a policy. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `should_evaluate_policy` | `(policy: Any, context: Dict[str, Any], evaluation_point: EvaluationPoint) -> Bin` | no | Determine if a policy should be evaluated at this point. |
| `get_binding_moment` | `(policy: Any) -> BindingMoment` | no | Get the binding moment for a policy. |
| `clear_run_cache` | `(run_id: str) -> None` | no | Clear the evaluation cache for a run (call on run completion). |
| `_mark_evaluated` | `(run_id: str, policy_id: str) -> None` | no | Mark a policy as evaluated for a run. |
| `_was_evaluated` | `(run_id: str, policy_id: str) -> bool` | no | Check if a policy was already evaluated for a run. |
| `_check_fields_changed` | `(policy: Any, context: Dict[str, Any]) -> bool` | no | Check if monitored fields changed (for ON_CHANGE binding). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Optional, Any, Dict, Set | no |
| `datetime` | datetime, timezone | no |
| `logging` | logging | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## compiler_parser.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/compiler_parser.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 460

**Docstring:** Parser for PLang v2.0 with M19 category support.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ParseError` | __init__ | Error during parsing. |
| `Parser` | __init__, from_source, current, peek, advance, expect, match, parse (+18 more) | Parser for PLang v2.0. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | List, Optional | no |
| `app.policy.ast.nodes` | ActionBlockNode, ASTNode, AttrAccessNode, BinaryOpNode, ConditionBlockNode (+12) | no |
| `app.policy.compiler.grammar` | ActionType, PolicyCategory | no |
| `app.policy.compiler.tokenizer` | Token, Tokenizer, TokenType | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## content_accuracy.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/content_accuracy.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 386

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AssertionType` |  | Types of assertions detected in output. |
| `ValidationResult` |  | Result of content accuracy validation. |
| `AssertionCheck` |  | A single assertion check result. |
| `ContentAccuracyResult` | to_dict | Complete result of content accuracy validation. |
| `ContentAccuracyValidator` | __init__, validate, _detect_assertion_type, _get_nested_value, _extract_claim, _claims_affirmative | Validates that LLM output does not make assertions about missing data. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `validate_content_accuracy` | `(output: str, context: Dict[str, Any], user_query: Optional[str] = None, strict_` | no | Convenience function to validate content accuracy. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `re` | re | no |
| `dataclasses` | dataclass, field | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`DEFINITIVE_PATTERNS`, `UNCERTAINTY_PATTERNS`, `HEDGED_PATTERNS`, `CONTRACT_TERMS`

---

## customer_policy_read_engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/customer_policy_read_engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 343

**Docstring:** Customer Policy Read Service (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `BudgetConstraint` |  | Customer-visible budget constraint. |
| `RateLimit` |  | Customer-visible rate limit. |
| `GuardrailSummary` |  | Customer-visible guardrail summary. |
| `PolicyConstraints` |  | Customer-visible policy constraints summary. |
| `CustomerPolicyReadService` | __init__, get_policy_constraints, get_guardrail_detail, _get_budget_constraint, _calculate_period_bounds, _get_rate_limits, _get_guardrails | L4 service for policy constraint read operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_customer_policy_read_service` | `(session: 'Session') -> CustomerPolicyReadService` | no | Factory function for CustomerPolicyReadService. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | TYPE_CHECKING, List, Optional | no |
| `app.hoc.cus.policies.L6_drivers.policy_read_driver` | PolicyReadDriver, get_policy_read_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## decorator.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/decorator.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 192

**Docstring:** @governed Decorator - PIN-337 Optional Ergonomic Wrapper

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `governed` | `(capability: str, execution_vector: str = 'HTTP', extract_tenant: Optional[Calla` | no | Decorator that routes execution through the ExecutionKernel. |
| `_extract_tenant_id` | `(args: tuple, kwargs: dict, extractor: Optional[Callable[..., str]]) -> str` | no | Extract tenant_id from function arguments. |
| `_extract_subject` | `(args: tuple, kwargs: dict, extractor: Optional[Callable[..., str]]) -> str` | no | Extract subject from function arguments. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `functools` | functools | no |
| `inspect` | inspect | no |
| `logging` | logging | no |
| `typing` | Any, Callable, Optional, TypeVar | no |
| `app.governance.kernel` | ExecutionKernel, InvocationContext | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`F`

---

## degraded_mode.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/degraded_mode.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 217

**Docstring:** Degraded Mode - Graceful Governance Degradation

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `DegradedModeStatus` | get_inactive | Current status of degraded mode. |
| `DegradedModeTransition` |  | Result of degraded mode transition. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `enter_degraded_mode` | `(reason: str, entered_by: str, existing_runs_action: str = 'WARN') -> DegradedMo` | no | Enter degraded mode. |
| `exit_degraded_mode` | `(exited_by: str = 'system') -> DegradedModeTransition` | no | Exit degraded mode. |
| `is_degraded_mode_active` | `() -> bool` | no | Check if degraded mode is currently active. |
| `get_degraded_mode_status` | `() -> DegradedModeStatus` | no | Get current degraded mode status. |
| `should_allow_new_run` | `(run_id: str) -> bool` | no | Check if a new run should be allowed. |
| `get_existing_run_action` | `() -> str` | no | Get action for existing/in-flight runs in degraded mode. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `threading` | Lock | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## deterministic_engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/deterministic_engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 560

**Docstring:** Deterministic execution engine for PLang v2.0.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ExecutionStatus` |  | Status of policy execution. |
| `ExecutionContext` | __post_init__, _generate_id, get_variable, set_variable, push_call, pop_call, add_trace | Execution context for policy evaluation. |
| `ExecutionResult` | to_dict | Result of policy execution. |
| `DeterministicEngine` | __init__, _register_builtins, execute, _execute_function, _execute_instruction, _eval_binary_op, _eval_unary_op, _eval_compare (+2 more) | Deterministic policy execution engine. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `safe_regex_match` | `(input_str: str, pattern: str) -> bool` | no | Safe regex match with length limits and ReDoS guards. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `re` | re | no |
| `dataclasses` | dataclass, field | no |
| `enum` | Enum, auto | no |
| `typing` | Any, Callable, Dict, List, Optional | no |
| `app.hoc.cus.policies.L5_schemas.policy_check` | PolicyCheckValidator | no |
| `app.policy.compiler.grammar` | ActionType, PolicyCategory | no |
| `app.policy.ir.ir_nodes` | IRAction, IRBinaryOp, IRCall, IRCheckPolicy, IRCompare (+11) | no |
| `app.hoc.cus.policies.L5_engines.intent` | Intent, IntentEmitter, IntentPayload, IntentType | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`MAX_PATTERN_LEN`, `MAX_INPUT_LEN`, `_REDOS_PATTERN`

---

## dsl_parser.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/dsl_parser.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 523

**Docstring:** Policy DSL Parser

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ParseLocation` | __str__ | Source location for error reporting. |
| `ParseError` | __init__ | Raised when parsing fails. |
| `Token` |  | A lexical token with position info. |
| `Lexer` | __init__, tokenize, _advance, _convert_value | Tokenizer for Policy DSL. |
| `Parser` | __init__, current, error, expect, accept, parse, _parse_header, _parse_clauses (+9 more) | Recursive descent parser for Policy DSL. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `parse` | `(source: str) -> PolicyAST` | no | Parse Policy DSL text into AST. |
| `parse_condition` | `(source: str) -> Condition` | no | Parse a standalone condition expression. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `re` | re | no |
| `dataclasses` | dataclass | no |
| `typing` | Any | no |
| `app.dsl.ast` | Action, BlockAction, Clause, Comparator, Condition (+10) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 2779

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyEngine` | __init__, driver, evaluate, pre_check, _check_ethical_constraints, _evaluate_ethical_constraint, _extract_text_content, _check_safety_rules (+53 more) | M19 Policy Engine - Constitutional Governance Layer. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_engine` | `() -> PolicyEngine` | no | Get singleton policy engine with M18 Governor integration. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `os` | os | no |
| `re` | re | no |
| `time` | time | no |
| `datetime` | datetime, timedelta, timezone | no |
| `typing` | TYPE_CHECKING, Any, Dict, List, Optional (+1) | no |
| `uuid` | uuid4 | no |
| `app.hoc.cus.policies.L6_drivers.policy_engine_driver` | PolicyEngineDriver, get_policy_engine_driver | no |
| `app.policy.models` | ActionType, BusinessRule, BusinessRuleType, EthicalConstraint, EthicalConstraintType (+14) | no |
| `app.contracts.decisions` | emit_policy_decision | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`POLICY_SIGNING_SECRET`, `MAX_EVALUATION_TIME_MS`, `CACHE_TTL_SECONDS`, `DEFAULT_COST_CEILING_PER_HOUR`, `DEFAULT_RETRY_CEILING_PER_MINUTE`, `DEFAULT_CASCADE_DEPTH`, `DEFAULT_CONCURRENT_AGENTS`

---

## failure_mode_handler.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/failure_mode_handler.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 296

**Docstring:** Module: failure_mode_handler

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `FailureMode` |  | Failure mode for policy evaluation. |
| `FailureType` |  | Type of failure encountered. |
| `FailureDecision` |  | Decision made when failure occurs. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `set_governance_config_getter` | `(getter: Callable[[], Any]) -> None` | no | Set the governance config getter for L5 purity (PIN-520). |
| `get_failure_mode` | `() -> FailureMode` | no | Get configured failure mode. |
| `handle_policy_failure` | `(error: Optional[Exception], context: Dict[str, Any], failure_type: FailureType ` | no | Handle a policy evaluation failure. |
| `handle_missing_policy` | `(context: Dict[str, Any]) -> FailureDecision` | no | Handle case where no policy exists for the action. |
| `handle_evaluation_error` | `(error: Exception, context: Dict[str, Any]) -> FailureDecision` | no | Handle policy evaluation error. |
| `handle_timeout` | `(context: Dict[str, Any], timeout_seconds: float) -> FailureDecision` | no | Handle policy evaluation timeout. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Optional, Any, Dict, Callable | no |
| `datetime` | datetime, timezone | no |
| `logging` | logging | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`DEFAULT_FAILURE_MODE`

---

## folds.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/folds.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 403

**Docstring:** IR optimizations for PLang v2.0.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `FoldResult` |  | Result of a folding operation. |
| `ConstantFolder` | __init__, fold_module, fold_function, fold_block, try_fold, _fold_binary_op, _fold_unary_op, _fold_compare | Constant folding optimization. |
| `DeadCodeEliminator` | __init__, eliminate, _mark_governance_critical, _eliminate_function, _find_reachable_blocks, _find_used_instructions | Dead code elimination. |
| `PolicySimplifier` | __init__, simplify, _find_mergeable_policies, _merge_policies | Policy-specific simplifications. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional, Set | no |
| `app.policy.ir.ir_nodes` | IRAction, IRBinaryOp, IRBlock, IRCompare, IRFunction (+6) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## governance_facade.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/governance_facade.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 740

**Docstring:** Governance Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GovernanceMode` |  | Governance operation modes. |
| `GovernanceStateResult` | to_dict | Result of governance state query. |
| `KillSwitchResult` | to_dict | Result of kill switch operation. |
| `ConflictResolutionResult` | to_dict | Result of conflict resolution. |
| `BootStatusResult` | to_dict | Result of boot status check. |
| `GovernanceFacade` | __init__, enable_kill_switch, disable_kill_switch, set_mode, get_governance_state, resolve_conflict, list_conflicts, get_boot_status | Facade for governance control operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_governance_facade` | `(runtime_switch: Optional[ModuleType] = None) -> GovernanceFacade` | no | Get the governance facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `types` | ModuleType | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## grammar.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/grammar.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 216

**Docstring:** PLang v2.0 Grammar (EBNF):

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GrammarNodeType` |  | Grammar node types for PLang v2.0. |
| `PolicyCategory` |  | M19 Policy Categories. |
| `ActionType` |  | Policy action types. |
| `GrammarProduction` |  | A production rule in the grammar. |
| `PLangGrammar` | get_category_priority, get_action_precedence, is_keyword, is_operator, is_category, is_action | PLang v2.0 Grammar Definition. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `enum` | Enum, auto | no |
| `typing` | Dict, List, Set | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`PLANG_GRAMMAR`

---

## intent.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/intent.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 405

**Docstring:** Intent system for PLang v2.0 runtime.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IntentType` |  | Types of intents emitted by policy runtime. |
| `IntentPayload` | to_dict, from_dict | Payload data for an intent. |
| `Intent` | __post_init__, _generate_id, to_dict, from_dict | An intent emitted by the policy runtime. |
| `IntentEmitter` | __init__, create_intent, validate_intent, emit, emit_all, register_handler, get_pending, get_emitted (+1 more) | Emits intents from policy runtime to M18. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `hashlib` | hashlib | no |
| `json` | json | no |
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum, auto | no |
| `typing` | Any, Awaitable, Callable, Dict, List (+1) | no |
| `app.hoc.cus.policies.L5_schemas.intent_validation` | PolicyIntentValidationResult, PolicyIntentValidator | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`_ENFORCEMENT_INTENT_TYPES`

---

## interpreter.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/interpreter.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 562

**Docstring:** Policy DSL Interpreter

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `EvaluationError` | __init__ | Raised when evaluation fails. |
| `TypeMismatchError` |  | Raised when types are incompatible for comparison. |
| `MissingMetricError` |  | Raised when a required metric is not in facts. |
| `ActionResult` | to_dict | A single action from evaluation. |
| `ClauseResult` | to_dict | Evaluation result for a single clause. |
| `EvaluationResult` | to_dict, has_block, has_require_approval, warnings | Complete evaluation result for a policy. |
| `Interpreter` | __init__, evaluate, _evaluate_clause, _evaluate_condition, _execute_instruction, _compare, _types_compatible, _collect_actions | Pure interpreter for Policy IR. |
| `_LenientInterpreter` | _execute_instruction, _compare | Lenient interpreter that treats missing metrics as non-matching. |
| `_MissingSentinel` |  | Sentinel value for missing metrics. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `evaluate` | `(ir: PolicyIR, facts: dict[str, Any]) -> EvaluationResult` | no | Evaluate policy IR against facts. |
| `evaluate_policy` | `(ir: PolicyIR, facts: dict[str, Any], strict: bool = True) -> EvaluationResult` | no | Evaluate policy with optional strict mode. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `dataclasses` | dataclass, field | no |
| `typing` | Any | no |
| `app.dsl.ir_compiler` | CompiledClause, Instruction, OpCode, PolicyIR | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`_MISSING_SENTINEL`

---

## ir_builder.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/ir_builder.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 408

**Docstring:** IR Builder for PLang v2.0.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IRBuilder` | __init__, build, _next_id, _next_block_name, _emit, _new_block, visit_program, visit_policy_decl (+13 more) | Builds IR from PLang AST. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Optional | no |
| `app.policy.ast.nodes` | ActionBlockNode, AttrAccessNode, BinaryOpNode, ConditionBlockNode, FuncCallNode (+10) | no |
| `app.policy.ast.visitors` | BaseVisitor | no |
| `app.policy.compiler.grammar` | ActionType | no |
| `app.policy.ir.ir_nodes` | IRAction, IRBinaryOp, IRBlock, IRCall, IRCompare (+12) | no |
| `app.policy.ir.symbol_table` | Symbol, SymbolTable, SymbolType | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## ir_compiler.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/ir_compiler.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 460

**Docstring:** Policy DSL Intermediate Representation (IR) Compiler

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `OpCode` |  | Closed instruction set for Policy IR. |
| `Instruction` | to_dict | A single IR instruction. |
| `CompiledClause` | to_dict | Compiled form of a single when-then clause. |
| `PolicyIR` | to_dict, to_json, compute_hash, instruction_count | Complete IR for a policy. |
| `IRCompiler` | __init__, compile, _compile_clause, _compile_condition, _emit_condition, _emit_predicate, _emit_exists, _emit_logical (+1 more) | Compiles PolicyAST to PolicyIR. |
| `OptimizingIRCompiler` | __init__, compile | IR Compiler with safe optimizations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `compile_policy` | `(ast: PolicyAST, optimize: bool = False) -> PolicyIR` | no | Compile PolicyAST to PolicyIR. |
| `ir_hash` | `(ast: PolicyAST) -> str` | no | Convenience function to get IR hash from AST. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `dataclasses` | dataclass, field | no |
| `enum` | Enum | no |
| `typing` | Any | no |
| `app.dsl.ast` | Action, Clause, Condition, ExistsPredicate, LogicalCondition (+9) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## ir_nodes.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/ir_nodes.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 404

**Docstring:** IR nodes for PLang v2.0 compilation.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IRType` |  | IR value types. |
| `IRGovernance` | from_ast, to_dict | Governance metadata for IR nodes. |
| `IRNode` | __str__ | Base class for all IR nodes. |
| `IRInstruction` |  | Base class for IR instructions. |
| `IRLoadConst` | __str__ | Load constant value. |
| `IRLoadVar` | __str__ | Load variable value. |
| `IRStoreVar` | __str__ | Store value to variable. |
| `IRBinaryOp` | __str__ | Binary operation. |
| `IRUnaryOp` | __str__ | Unary operation. |
| `IRCompare` | __str__ | Comparison operation. |
| `IRJump` | __str__ | Unconditional jump. |
| `IRJumpIf` | __str__ | Conditional jump. |
| `IRCall` | __str__ | Function call. |
| `IRReturn` | __str__ | Return from function. |
| `IRAction` | __str__ | Policy action instruction. |
| `IRCheckPolicy` | __str__ | Check against M19 policy engine. |
| `IREmitIntent` | __str__ | Emit intent to M18 execution layer. |
| `IRBlock` | add_instruction, is_terminated, __str__ | Basic block in IR. |
| `IRFunction` | add_block, get_block, __str__ | Function in IR. |
| `IRModule` | add_function, get_function, get_functions_by_category, __str__ | Module in IR. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `abc` | ABC, abstractmethod | no |
| `dataclasses` | dataclass, field | no |
| `enum` | Enum, auto | no |
| `typing` | Any, Dict, List, Optional | no |
| `app.policy.compiler.grammar` | ActionType, PolicyCategory | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## kernel.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/kernel.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 623

**Docstring:** ExecutionKernel - PIN-337 Governance Enforcement Infrastructure

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `EnforcementMode` |  | Enforcement mode for capability execution. |
| `InvocationContext` |  | Context for an execution invocation. |
| `ExecutionResult` |  | Result of an execution through the kernel. |
| `ExecutionKernel` | invoke, invoke_async, _emit_envelope, _record_invocation_start, _record_invocation_complete, is_known_capability, get_known_capabilities | Mandatory execution kernel - single choke point for all EXECUTE power. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_enforcement_mode` | `(capability_id: str) -> EnforcementMode` | no | Get enforcement mode for a capability. |
| `set_enforcement_mode` | `(capability_id: str, mode: EnforcementMode) -> None` | no | Set enforcement mode for a capability. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `uuid` | uuid | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Callable, Optional, TypeVar | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`T`

---

## kill_switch.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/kill_switch.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 223

**Docstring:** Kill Switch - Runtime Governance Bypass

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `KillSwitchStatus` | get_current | Current status of the kill switch. |
| `KillSwitchActivation` |  | Result of kill switch activation. |
| `KillSwitchDeactivation` |  | Result of kill switch deactivation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `activate_kill_switch` | `(reason: str, activated_by: str, auto_expire_minutes: int = 60) -> KillSwitchAct` | no | Activate the runtime kill switch. |
| `deactivate_kill_switch` | `(deactivated_by: str = 'system') -> KillSwitchDeactivation` | no | Deactivate the runtime kill switch. |
| `is_kill_switch_active` | `() -> bool` | no | Check if kill switch is currently active. |
| `should_bypass_governance` | `() -> bool` | no | Check if governance should be bypassed. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `threading` | Lock | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## lessons_engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/lessons_engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 1082

**Docstring:** Lessons Learned Engine (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LessonsLearnedEngine` | __init__, _get_driver, detect_lesson_from_failure, detect_lesson_from_near_threshold, detect_lesson_from_critical_success, emit_near_threshold, emit_critical_success, list_lessons (+12 more) | L4 Domain Engine for lesson creation and management. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `is_valid_transition` | `(from_status: str, to_status: str) -> bool` | no | Check if a state transition is valid. |
| `get_threshold_band` | `(utilization: float) -> str` | no | Get the threshold band for a utilization percentage. |
| `get_lessons_learned_engine` | `(driver: Any = None) -> LessonsLearnedEngine` | no | Get a LessonsLearnedEngine instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `os` | os | no |
| `datetime` | datetime, timezone | no |
| `typing` | TYPE_CHECKING, Any, Dict, List, Optional | no |
| `uuid` | UUID, uuid4 | no |
| `prometheus_client` | Counter | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`LESSONS_CREATION_FAILED`, `LESSON_TYPE_FAILURE`, `LESSON_TYPE_NEAR_THRESHOLD`, `LESSON_TYPE_CRITICAL_SUCCESS`, `LESSON_STATUS_PENDING`, `LESSON_STATUS_CONVERTED`, `LESSON_STATUS_DEFERRED`, `LESSON_STATUS_DISMISSED`, `SEVERITY_CRITICAL`, `SEVERITY_HIGH`, `SEVERITY_MEDIUM`, `SEVERITY_LOW`, `SEVERITY_NONE`, `NEAR_THRESHOLD_PERCENT`, `DEBOUNCE_WINDOW_HOURS`, `THRESHOLD_BANDS`

---

## limits.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/limits.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 157

**Docstring:** Phase-6 Limits — Derived from Plan (Not Stored)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `Limits` | is_unlimited | Phase-6 Limits Model (Immutable, Derived). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `derive_limits` | `(limits_profile: str) -> Limits` | no | Derive limits from a limits profile key. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`DEFAULT_LIMITS`

### __all__ Exports
`Limits`, `derive_limits`, `LIMITS_PROFILES`, `DEFAULT_LIMITS`

---

## limits_facade.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/limits_facade.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 459

**Docstring:** Limits Facade (L4 Domain Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LimitType` |  | Types of limits. |
| `LimitPeriod` |  | Limit period. |
| `LimitConfig` | to_dict | Limit configuration. |
| `LimitCheckResult` | to_dict | Result of checking a limit. |
| `UsageSummary` | to_dict | Usage summary across all limits. |
| `LimitsFacade` | __init__, _get_or_create_limit, list_limits, get_limit, update_limit, check_limit, get_usage, reset_limit | Facade for limit operations. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_limits_facade` | `() -> LimitsFacade` | no | Get the limits facade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## nodes.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/nodes.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 379

**Docstring:** AST nodes for PLang v2.0.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `GovernanceMetadata` | merge_with | M19 Governance metadata attached to AST nodes. |
| `ASTNode` | accept, location | Base class for all AST nodes. |
| `ExprNode` |  | Base class for expression nodes. |
| `ProgramNode` | accept | Root node representing a complete PLang program. |
| `PolicyDeclNode` | __post_init__, accept | Policy declaration node. |
| `RuleDeclNode` | __post_init__, accept | Rule declaration node. |
| `ImportNode` | accept | Import statement node. |
| `RuleRefNode` | accept | Reference to a named rule. |
| `PriorityNode` | accept | Priority declaration node. |
| `ConditionBlockNode` | accept | When/then condition block. |
| `ActionBlockNode` | accept | Action block (deny, allow, escalate, route). |
| `RouteTargetNode` | accept | Route target specification. |
| `BinaryOpNode` | accept | Binary operation (and, or, ==, !=, etc.). |
| `UnaryOpNode` | accept | Unary operation (not). |
| `ValueNode` |  | Base class for value nodes. |
| `IdentNode` | accept | Identifier node. |
| `LiteralNode` | accept | Literal value node (number, string, boolean). |
| `FuncCallNode` | accept | Function call node. |
| `AttrAccessNode` | accept | Attribute access node (obj.attr). |
| `ASTVisitor` | visit_program, visit_policy_decl, visit_rule_decl, visit_import, visit_rule_ref, visit_priority, visit_condition_block, visit_action_block (+7 more) | Abstract base class for AST visitors. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `abc` | ABC, abstractmethod | no |
| `dataclasses` | dataclass, field | no |
| `typing` | Any, List, Optional | no |
| `app.policy.compiler.grammar` | ActionType, PolicyCategory | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## phase_status_invariants.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/phase_status_invariants.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 360

**Docstring:** Module: phase_status_invariants

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `InvariantCheckResult` |  | Result of an invariant check. |
| `PhaseStatusInvariantEnforcementError` | __init__, to_dict | Raised when phase-status invariant enforcement fails. |
| `InvariantCheckResponse` | to_dict | Response from an invariant check. |
| `PhaseStatusInvariantChecker` | __init__, from_governance_config, enforcement_enabled, get_allowed_statuses, is_valid_combination, check, ensure_valid, should_allow_transition | Checks and enforces phase-status invariants. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `check_phase_status_invariant` | `(phase: str, status: str, enforcement_enabled: bool = True) -> InvariantCheckRes` | no | Quick helper to check a phase-status invariant. |
| `ensure_phase_status_invariant` | `(phase: str, status: str, enforcement_enabled: bool = True) -> None` | no | Quick helper to ensure phase-status invariant or raise error. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Any, FrozenSet, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## plan.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/plan.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 145

**Docstring:** Phase-6 Plan Model — Named Contracts (Not Pricing Logic)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PlanTier` | from_string | Plan tier hierarchy. |
| `Plan` | __post_init__ | Phase-6 Plan Model (Immutable). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum | no |
| `typing` | Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`PLAN_FREE`, `PLAN_PRO`, `PLAN_ENTERPRISE`, `DEFAULT_PLAN`

### __all__ Exports
`PlanTier`, `Plan`, `PLAN_FREE`, `PLAN_PRO`, `PLAN_ENTERPRISE`, `DEFAULT_PLAN`

---

## policies_facade.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/policies_facade.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 1193

**Docstring:** PoliciesFacade (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyRuleSummaryResult` |  | Policy rule summary for list view (O2). |
| `PolicyRulesListResult` |  | Policy rules list response. |
| `PolicyRuleDetailResult` |  | Policy rule detail response (O3). |
| `LimitSummaryResult` |  | Limit summary for list view (O2). |
| `LimitsListResult` |  | Limits list response. |
| `LimitDetailResult` |  | Limit detail response (O3). |
| `PolicyStateResult` |  | Policy layer state summary (ACT-O4). |
| `PolicyMetricsResult` |  | Policy enforcement metrics (ACT-O5). |
| `PolicyConflictResult` |  | Policy conflict summary (DFT-O4). |
| `ConflictsListResult` |  | Policy conflicts list response. |
| `PolicyDependencyRelation` |  | A dependency relationship. |
| `PolicyNodeResult` |  | A node in the dependency graph (DFT-O5). |
| `PolicyDependencyEdge` |  | A dependency edge in the graph. |
| `DependencyGraphResult` |  | Policy dependency graph response. |
| `PolicyViolationResult` |  | Policy violation summary (VIO-O1). |
| `ViolationsListResult` |  | Policy violations list response. |
| `BudgetDefinitionResult` |  | Budget definition summary (THR-O2). |
| `BudgetsListResult` |  | Budget definitions list response. |
| `PolicyRequestResult` |  | Pending policy request summary (ACT-O3). |
| `PolicyRequestsListResult` |  | Policy requests list response. |
| `LessonSummaryResult` |  | Lesson summary for list view (O2). |
| `LessonsListResult` |  | Lessons list response. |
| `LessonDetailResult` |  | Lesson detail response (O3). |
| `LessonStatsResult` |  | Lesson statistics response. |
| `PoliciesFacade` | __init__, list_policy_rules, get_policy_rule_detail, list_limits, get_limit_detail, list_lessons, get_lesson_detail, get_lesson_stats (+7 more) | Unified facade for policy management. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policies_facade` | `(driver: Optional[PoliciesFacadeDriver] = None) -> PoliciesFacade` | no | Get the singleton PoliciesFacade instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timedelta, timezone | no |
| `decimal` | Decimal | no |
| `typing` | Any, Optional | no |
| `app.hoc.cus.policies.L6_drivers.policies_facade_driver` | PoliciesFacadeDriver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`PoliciesFacade`, `get_policies_facade`, `PolicyRuleSummaryResult`, `PolicyRulesListResult`, `PolicyRuleDetailResult`, `LimitSummaryResult`, `LimitsListResult`, `LimitDetailResult`, `PolicyStateResult`, `PolicyMetricsResult`, `PolicyConflictResult`, `ConflictsListResult`, `PolicyDependencyRelation`, `PolicyNodeResult`, `PolicyDependencyEdge`, `DependencyGraphResult`, `PolicyViolationResult`, `ViolationsListResult`, `BudgetDefinitionResult`, `BudgetsListResult`, `PolicyRequestResult`, `PolicyRequestsListResult`, `LessonSummaryResult`, `LessonsListResult`, `LessonDetailResult`, `LessonStatsResult`

---

## policies_limits_query_engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/policies_limits_query_engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 343

**Docstring:** Limits Query Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `LimitSummaryResult` |  | Limit summary for list view (O2). |
| `LimitsListResult` |  | Limits list response. |
| `LimitDetailResult` |  | Limit detail response (O3). |
| `BudgetDefinitionResult` |  | Budget definition summary (THR-O2). |
| `BudgetsListResult` |  | Budget definitions list response. |
| `LimitsQueryEngine` | __init__, list_limits, get_limit_detail, list_budgets | L5 Query Engine for limits. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_limits_query_engine` | `(session: 'AsyncSession' = None) -> LimitsQueryEngine` | no | Get a LimitsQueryEngine instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `decimal` | Decimal | no |
| `typing` | TYPE_CHECKING, Any, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`LimitsQueryEngine`, `get_limits_query_engine`, `LimitSummaryResult`, `LimitsListResult`, `LimitDetailResult`, `BudgetDefinitionResult`, `BudgetsListResult`

---

## policies_proposals_query_engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/policies_proposals_query_engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 294

**Docstring:** Proposals Query Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyRequestResult` |  | Pending policy request summary (ACT-O3). |
| `PolicyRequestsListResult` |  | Policy requests list response. |
| `PolicyRequestDetailResult` |  | Policy request detail response. |
| `ProposalsQueryEngine` | __init__, list_policy_requests, get_policy_request_detail, count_drafts, list_proposals_paginated, get_proposal_stats, get_proposal_detail, list_proposal_versions | L5 Query Engine for policy proposals. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_proposals_query_engine` | `(session: 'AsyncSession') -> ProposalsQueryEngine` | no | Get a ProposalsQueryEngine instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `typing` | TYPE_CHECKING, Any, Optional | no |
| `app.hoc.cus.policies.L6_drivers.proposals_read_driver` | ProposalsReadDriver, get_proposals_read_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`ProposalsQueryEngine`, `get_proposals_query_engine`, `PolicyRequestResult`, `PolicyRequestsListResult`, `PolicyRequestDetailResult`

---

## policies_rules_query_engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/policies_rules_query_engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 246

**Docstring:** Policy Rules Query Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyRuleSummaryResult` |  | Policy rule summary for list view (O2). |
| `PolicyRulesListResult` |  | Policy rules list response. |
| `PolicyRuleDetailResult` |  | Policy rule detail response (O3). |
| `PolicyRulesQueryEngine` | __init__, list_policy_rules, get_policy_rule_detail, count_rules | L5 Query Engine for policy rules. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_rules_query_engine` | `(session: 'AsyncSession') -> PolicyRulesQueryEngine` | no | Get a PolicyRulesQueryEngine instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime | no |
| `decimal` | Decimal | no |
| `typing` | TYPE_CHECKING, Any, Optional | no |
| `app.hoc.cus.policies.L6_drivers.policy_rules_read_driver` | PolicyRulesReadDriver, get_policy_rules_read_driver | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`PolicyRulesQueryEngine`, `get_policy_rules_query_engine`, `PolicyRuleSummaryResult`, `PolicyRulesListResult`, `PolicyRuleDetailResult`

---

## policy_command.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/policy_command.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 480

**Docstring:** Policy Command (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyViolation` |  | A policy violation detected during evaluation. |
| `PolicyEvaluationResult` |  | Result from policy evaluation command. |
| `ApprovalConfig` |  | Approval level configuration. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `simulate_cost` | `(skill_id: str, tenant_id: str, payload: Dict[str, Any]) -> Optional[int]` | yes | Simulate cost for a skill execution. |
| `check_policy_violations` | `(skill_id: str, tenant_id: str, agent_id: Optional[str], payload: Dict[str, Any]` | yes | Check for policy violations. |
| `evaluate_policy` | `(skill_id: str, tenant_id: str, agent_id: Optional[str], payload: Dict[str, Any]` | yes | Evaluate policy for a skill execution. |
| `_record_policy_decision` | `(decision: str, policy_type: str) -> None` | no | Record policy decision metric. |
| `_record_capability_violation` | `(violation_type: str, skill_id: str, tenant_id: Optional[str] = None) -> None` | no | Record capability violation metric. |
| `_record_budget_rejection` | `(resource_type: str, skill_id: str) -> None` | no | Record budget rejection metric. |
| `_record_approval_request_created` | `(policy_type: str) -> None` | no | Record approval request creation metric. |
| `_record_approval_action` | `(result: str) -> None` | no | Record approval action metric. |
| `_record_approval_escalation` | `() -> None` | no | Record approval escalation metric. |
| `_record_webhook_fallback` | `() -> None` | no | Record webhook fallback metric. |
| `record_approval_created` | `(policy_type: str) -> None` | no | Record that an approval request was created. |
| `record_approval_outcome` | `(result: str) -> None` | no | Record approval outcome (approved/rejected/expired). |
| `record_escalation` | `() -> None` | no | Record that an escalation occurred. |
| `record_webhook_used` | `() -> None` | no | Record that webhook fallback was used. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`PolicyViolation`, `PolicyEvaluationResult`, `ApprovalConfig`, `simulate_cost`, `check_policy_violations`, `evaluate_policy`, `record_approval_created`, `record_approval_outcome`, `record_escalation`, `record_webhook_used`

---

## policy_conflict_resolver.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/policy_conflict_resolver.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 267

**Docstring:** Module: conflict_resolver

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `ActionSeverity` |  | Action severity for conflict resolution. Higher = more restrictive. |
| `ConflictResolutionStrategy` |  | Resolution strategy for policy conflicts. |
| `PolicyAction` |  | A triggered policy action. |
| `ResolvedAction` |  | Result of conflict resolution. |
| `PolicyConflictLog` |  | Audit log entry for conflict resolution. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `resolve_policy_conflict` | `(actions: List[PolicyAction], strategy: ConflictResolutionStrategy = ConflictRes` | no | Resolve conflict when multiple policies trigger. |
| `create_conflict_log` | `(run_id: str, resolved: ResolvedAction, strategy: ConflictResolutionStrategy) ->` | no | Create audit log entry for conflict resolution. |
| `get_action_severity` | `(action: str) -> int` | no | Get the severity level for an action. |
| `is_more_restrictive` | `(action_a: str, action_b: str) -> bool` | no | Check if action_a is more restrictive than action_b. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `enum` | Enum, IntEnum | no |
| `dataclasses` | dataclass | no |
| `typing` | List, Optional | no |
| `datetime` | datetime, timezone | no |
| `logging` | logging | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`ACTION_SEVERITY`

---

## policy_driver.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/policy_driver.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 424

**Docstring:** Policy Domain Driver (INTERNAL)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyDriver` | __init__, _engine, policy_engine_driver, evaluate, pre_check, get_state, reload_policies, get_violations (+30 more) | Driver for Policy domain operations (INTERNAL). |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_policy_driver` | `(db_url: Optional[str] = None) -> PolicyDriver` | no | Get the PolicyDriver singleton. |
| `reset_policy_driver` | `() -> None` | no | Reset the driver singleton (for testing). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `datetime` | datetime | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## policy_limits_engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/policy_limits_engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 391

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyLimitsServiceError` |  | Base exception for policy limits service. |
| `LimitNotFoundError` |  | Raised when limit is not found. |
| `LimitValidationError` |  | Raised when limit validation fails. |
| `ImmutableFieldError` |  | Raised when attempting to modify immutable fields. |
| `PolicyLimitsService` | __init__, create, update, delete, get, _get_limit, _validate_category_fields, _to_response | Service for policy limit CRUD operations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `typing` | TYPE_CHECKING, Any, Optional | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |
| `app.hoc.cus.hoc_spine.drivers.cross_domain` | generate_uuid | no |
| `app.hoc.cus.hoc_spine.schemas.domain_enums` | ActorType | no |
| `app.hoc.cus.controls.L5_schemas.policy_limits` | CreatePolicyLimitRequest, UpdatePolicyLimitRequest, PolicyLimitResponse | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## policy_mapper.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/policy_mapper.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 643

**Docstring:** Module: policy_mapper

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `MCPPolicyDecisionType` |  | Types of policy decisions for MCP tools. |
| `MCPDenyReason` |  | Reasons for denying MCP tool invocation. |
| `MCPPolicyDecision` | to_dict, allow, deny | Policy decision for MCP tool invocation. |
| `MCPToolPolicy` |  | Policy configuration for an MCP tool. |
| `MCPPolicyMapper` | __init__, check_tool_invocation, register_tool_policy, _evaluate_policy, _check_explicit_allow, _check_rate_limit, _get_policy_engine | Maps MCP tool invocations to policy gates. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_mcp_policy_mapper` | `() -> MCPPolicyMapper` | no | Get or create the singleton MCPPolicyMapper. |
| `configure_mcp_policy_mapper` | `(policy_engine: Optional[Any] = None) -> MCPPolicyMapper` | no | Configure the singleton MCPPolicyMapper. |
| `reset_mcp_policy_mapper` | `() -> None` | no | Reset the singleton (for testing). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## policy_models.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/policy_models.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 739

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyCategory` |  | Categories of policies in the M19 Policy Layer. |
| `PolicyDecision` |  | Possible decisions from policy evaluation. |
| `ActionType` |  | Types of actions that require policy evaluation. |
| `ViolationType` |  | Types of policy violations. |
| `ViolationSeverity` |  | Enhanced violation severity classifications (GAP 5). |
| `RecoverabilityType` |  | Whether a violation is recoverable. |
| `SafetyRuleType` |  | Types of safety rules. |
| `EthicalConstraintType` |  | Types of ethical constraints. |
| `BusinessRuleType` |  | Types of business rules. |
| `PolicyEvaluationRequest` |  | Request for policy evaluation. |
| `PolicyModification` |  | Modification applied to an action by policy engine. |
| `PolicyEvaluationResult` |  | Result of policy evaluation. |
| `PolicyViolation` |  | A policy violation record. |
| `PolicyRule` |  | A single rule within a policy. |
| `Policy` |  | A policy definition. |
| `RiskCeiling` |  | A risk ceiling definition. |
| `SafetyRule` |  | A safety rule definition. |
| `EthicalConstraint` |  | An ethical constraint definition. |
| `BusinessRule` |  | A business rule definition. |
| `PolicyState` |  | Current state of the policy layer. |
| `PolicyLoadResult` |  | Result of loading policies from database. |
| `PolicyVersion` |  | A versioned snapshot of a policy set (GAP 1). |
| `PolicyProvenance` |  | Audit trail for policy changes (GAP 1). |
| `PolicyDependency` |  | Dependency relationship between policies (GAP 2). |
| `PolicyConflict` |  | A detected conflict between policies (GAP 2). |
| `DependencyGraph` |  | The complete policy dependency graph (GAP 2). |
| `TemporalPolicyType` |  | Types of temporal policies. |
| `TemporalPolicy` |  | A temporal/sliding window policy (GAP 3). |
| `TemporalMetricWindow` |  | A sliding window of metric values (GAP 3). |
| `PolicyContext` |  | Complete policy context passed through the decision cycle (GAP 4). |
| `EnhancedPolicyEvaluationRequest` |  | Enhanced evaluation request with full context (GAP 4). |
| `EnhancedPolicyViolation` |  | Enhanced violation with severity classification (GAP 5). |
| `EnhancedPolicyEvaluationResult` |  | Enhanced evaluation result with full context (GAPs 1-5). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, List, Optional | no |
| `uuid` | uuid4 | no |
| `pydantic` | BaseModel, Field | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## policy_proposal_engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/policy_proposal_engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 716

**Docstring:** Policy Proposal Engine (L5)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyActivationBlockedError` | __init__ | GOV-POL-001: Raised when policy activation is blocked due to BLOCKING conflicts. |
| `PolicyDeletionBlockedError` | __init__ | GOV-POL-002: Raised when policy deletion is blocked due to dependents. |
| `PolicyProposalEngine` | __init__, check_proposal_eligibility, create_proposal, review_proposal, _create_policy_rule_from_proposal, delete_policy_rule, get_proposal_summary | L5 Domain Engine for policy proposal lifecycle management. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `generate_default_rule` | `(policy_type: str, feedback_type: str) -> dict` | no | Generate a default rule template based on policy type. |
| `get_policy_proposal_engine` | `(session: 'AsyncSession') -> PolicyProposalEngine` | no | Get a PolicyProposalEngine instance with drivers. |
| `check_proposal_eligibility` | `(session: 'AsyncSession', tenant_id: Optional[UUID] = None, feedback_type: Optio` | yes | Backward-compatible wrapper for eligibility checking. |
| `create_policy_proposal` | `(session: 'AsyncSession', proposal: PolicyProposalCreate) -> str` | yes | Backward-compatible wrapper for proposal creation. |
| `review_policy_proposal` | `(session: 'AsyncSession', proposal_id: UUID, review: PolicyApprovalRequest, audi` | yes | Backward-compatible wrapper for proposal review. |
| `delete_policy_rule` | `(session: 'AsyncSession', rule_id: str, tenant_id: str, deleted_by: str) -> bool` | yes | Backward-compatible wrapper for rule deletion. |
| `get_proposal_summary` | `(session: 'AsyncSession', tenant_id: Optional[UUID] = None, status: Optional[str` | yes | Backward-compatible wrapper for proposal summary. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `logging` | logging | no |
| `typing` | TYPE_CHECKING, Any, Optional | no |
| `uuid` | UUID | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |
| `app.hoc.cus.policies.L6_drivers.policy_proposal_read_driver` | PolicyProposalReadDriver, get_policy_proposal_read_driver | no |
| `app.hoc.cus.policies.L6_drivers.policy_proposal_write_driver` | PolicyProposalWriteDriver, get_policy_proposal_write_driver | no |
| `app.hoc.cus.hoc_spine.schemas.domain_enums` | ActorType | no |
| `app.hoc.cus.policies.L5_engines.policy_graph` | ConflictSeverity, get_conflict_engine, get_dependency_engine | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`FEEDBACK_THRESHOLD_FOR_PROPOSAL`, `PROPOSAL_TYPES`

### __all__ Exports
`PolicyProposalEngine`, `get_policy_proposal_engine`, `PolicyActivationBlockedError`, `PolicyDeletionBlockedError`, `FEEDBACK_THRESHOLD_FOR_PROPOSAL`, `PROPOSAL_TYPES`, `generate_default_rule`, `check_proposal_eligibility`, `create_policy_proposal`, `review_policy_proposal`, `delete_policy_rule`, `get_proposal_summary`

---

## policy_rules_engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/policy_rules_engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 397

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PolicyRulesServiceError` |  | Base exception for policy rules service. |
| `RuleNotFoundError` |  | Raised when rule is not found. |
| `RuleValidationError` |  | Raised when rule validation fails. |
| `PolicyRulesService` | __init__, create, update, get, _get_rule, _validate_conditions, _compute_hash, _to_response | Service for policy rule CRUD operations. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `uuid` | uuid | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `typing` | TYPE_CHECKING, Any, Optional | no |
| `app.hoc.cus.hoc_spine.services.time` | utc_now | no |
| `app.hoc.cus.hoc_spine.drivers.cross_domain` | generate_uuid | no |
| `app.hoc.cus.policies.L6_drivers.policy_rules_driver` | PolicyRulesDriver, get_policy_rules_driver | no |
| `app.hoc.cus.hoc_spine.schemas.domain_enums` | ActorType | no |
| `app.hoc.cus.policies.L5_schemas.policy_rules` | CreatePolicyRuleRequest, UpdatePolicyRuleRequest, PolicyRuleResponse | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## prevention_hook.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/prevention_hook.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 302

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `PreventionAction` |  | Action to take when prevention hook triggers. |
| `PreventionContext` | __post_init__ | Context for prevention hook evaluation. |
| `PreventionResult` | __post_init__, to_dict | Result of prevention hook evaluation. |
| `PreventionHook` | __init__, evaluate, get_safe_response | Prevention hook for pre-response validation. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `create_prevention_hook` | `(strict_mode: bool = True, block_on_fail: bool = True) -> PreventionHook` | no | Factory function to create a prevention hook. |
| `get_prevention_hook` | `() -> PreventionHook` | no | Get the global prevention hook instance. |
| `evaluate_response` | `(tenant_id: str, call_id: str, user_query: str, context_data: Dict[str, Any], ll` | no | Convenience function to evaluate an LLM response. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, Dict, Optional | no |
| `uuid` | uuid4 | no |
| `app.hoc.cus.policies.L5_engines.content_accuracy` | ContentAccuracyValidator, ValidationResult | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## protection_provider.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/protection_provider.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 388

**Docstring:** Phase-7 Abuse Protection Provider — Interface and Mock Implementation

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `AbuseProtectionProvider` | check_rate_limit, check_burst, check_cost, detect_anomaly, check_all | Phase-7 Abuse Protection Provider Protocol. |
| `MockAbuseProtectionProvider` | __init__, check_rate_limit, check_burst, check_cost, detect_anomaly, check_all, add_cost, reset (+1 more) | Phase-7 Mock Abuse Protection Provider. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_protection_provider` | `() -> AbuseProtectionProvider` | no | Get the abuse protection provider instance. |
| `set_protection_provider` | `(provider: AbuseProtectionProvider) -> None` | no | Set the abuse protection provider instance. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Protocol, Optional | no |
| `logging` | logging | no |
| `time` | time | no |
| `app.protection.decisions` | Decision, ProtectionResult, AnomalySignal, allow, reject_rate_limit (+2) | no |
| `app.billing` | get_billing_provider, Limits | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`AbuseProtectionProvider`, `MockAbuseProtectionProvider`, `get_protection_provider`, `set_protection_provider`

---

## recovery_evaluation_engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/recovery_evaluation_engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 415

**Docstring:** Domain engine for recovery evaluation decisions.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `FailureContext` | __post_init__ | Context for recovery evaluation (mirrors L5 FailureEvent for L4 use). |
| `RecoveryDecision` | to_dict | Domain decision DTO returned by L4 engine to L5 executor. |
| `RecoveryEvaluationEngine` | __init__, evaluate, emit_decision_record | L4 Domain Engine for recovery evaluation decisions. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `evaluate_recovery` | `(failure_match_id: str, error_code: str, error_message: str, **kwargs) -> Recove` | no | Convenience function to evaluate a failure and get a decision. |
| `evaluate_and_execute` | `(failure_match_id: str, error_code: str, error_message: str, **kwargs) -> 'Evalu` | yes | Full entry point: evaluate failure and execute decision. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, Optional | no |
| `app.contracts.decisions` | emit_recovery_decision | no |
| `app.hoc.cus.policies.L6_drivers.recovery_matcher` | RecoveryMatcher | no |
| `app.hoc.cus.hoc_spine.utilities.recovery_decisions` | combine_confidences, should_auto_execute, should_select_action | no |
| `app.hoc.cus.hoc_spine.services.cross_domain_gateway` | evaluate_rules | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`FailureContext`, `RecoveryDecision`, `RecoveryEvaluationEngine`, `evaluate_recovery`, `evaluate_and_execute`

---

## runtime_command.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/runtime_command.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 561

**Docstring:** Runtime Domain Commands (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `QueryResult` |  | Result from a runtime query command. |
| `SkillInfo` |  | Domain information about a skill. |
| `ResourceContractInfo` |  | Domain information about a resource contract. |
| `CapabilitiesInfo` |  | Domain information about available capabilities. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_supported_query_types` | `() -> List[str]` | no | Get list of supported query types. |
| `query_remaining_budget` | `(spent_cents: int = 0, total_cents: int = DEFAULT_BUDGET_CENTS) -> QueryResult` | no | Query remaining budget. |
| `query_execution_history` | `(history: Optional[List[Dict[str, Any]]] = None) -> QueryResult` | no | Query execution history. |
| `query_allowed_skills` | `() -> QueryResult` | no | Query list of allowed skills. |
| `query_last_step_outcome` | `(outcome: Optional[Dict[str, Any]] = None) -> QueryResult` | no | Query last step outcome. |
| `query_skills_for_goal` | `(goal: str) -> QueryResult` | no | Query skills available for a goal. |
| `execute_query` | `(query_type: str, params: Optional[Dict[str, Any]] = None) -> QueryResult` | no | Execute a runtime query. |
| `get_skill_info` | `(skill_id: str) -> Optional[SkillInfo]` | no | Get domain information about a skill. |
| `list_skills` | `() -> List[str]` | no | List all available skill IDs. |
| `get_all_skill_descriptors` | `() -> Dict[str, Dict[str, Any]]` | no | Get descriptors for all skills. |
| `get_resource_contract` | `(resource_id: str) -> ResourceContractInfo` | no | Get resource contract information. |
| `get_capabilities` | `(agent_id: Optional[str] = None, tenant_id: Optional[str] = None) -> Capabilitie` | no | Get capabilities for an agent/tenant. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`DEFAULT_BUDGET_CENTS`, `DEFAULT_RATE_LIMIT_PER_MINUTE`, `DEFAULT_MAX_CONCURRENT`, `SUPPORTED_QUERY_TYPES`, `DEFAULT_SKILL_METADATA`, `QueryResult`, `SkillInfo`, `ResourceContractInfo`, `CapabilitiesInfo`, `get_supported_query_types`, `query_remaining_budget`, `query_execution_history`, `query_allowed_skills`, `query_last_step_outcome`, `query_skills_for_goal`, `execute_query`, `get_skill_info`, `list_skills`, `get_all_skill_descriptors`, `get_resource_contract`, `get_capabilities`

---

## sandbox_engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/sandbox_engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 562

**Docstring:** Sandbox Service (GAP-174)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SandboxPolicy` | to_resource_limits, to_dict | Policy for sandbox execution. |
| `ExecutionRequest` |  | Request to execute code in a sandbox. |
| `ExecutionRecord` | to_dict | Record of a sandbox execution for audit. |
| `SandboxService` | __init__, _setup_default_policies, _get_executor, execute, _get_policy, _check_quota, _track_execution, define_policy (+4 more) | High-level sandbox service. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_sandbox_service` | `() -> 'SandboxService'` | no | Return the process-wide SandboxService singleton (GAP-174). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `logging` | logging | no |
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `typing` | Any, Dict, List, Optional, Set | no |
| `sandbox_executor` | ExecutionResult, IsolationLevel, NetworkPolicy, ResourceLimits, SandboxExecutor (+2) | yes |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## snapshot_engine.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/snapshot_engine.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 594

**Docstring:** Policy Snapshot Immutability Engine (GAP-029).

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `SnapshotStatus` |  | Status of a policy snapshot. |
| `ImmutabilityViolation` |  | Types of immutability violations. |
| `PolicySnapshotData` | compute_hash, verify_integrity, verify_threshold_integrity, get_policies, get_thresholds, to_dict | Immutable policy snapshot data. |
| `PolicySnapshotError` | __init__, to_dict | Exception for policy snapshot errors. |
| `SnapshotRegistryStats` | to_dict | Statistics for snapshot registry. |
| `PolicySnapshotRegistry` | __init__, create, get, get_active, get_by_version, list, get_history, archive (+8 more) | Registry for managing immutable policy snapshots. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `get_snapshot_registry` | `() -> PolicySnapshotRegistry` | no | Get the singleton registry instance. |
| `_reset_snapshot_registry` | `() -> None` | no | Reset the singleton (for testing). |
| `create_policy_snapshot` | `(tenant_id: str, policies: list[dict[str, Any]], thresholds: dict[str, Any], pol` | no | Create a new immutable policy snapshot. |
| `get_policy_snapshot` | `(snapshot_id: str) -> Optional[PolicySnapshotData]` | no | Get a policy snapshot by ID. |
| `get_active_snapshot` | `(tenant_id: str) -> Optional[PolicySnapshotData]` | no | Get the active policy snapshot for a tenant. |
| `get_snapshot_history` | `(tenant_id: str, limit: int = 100) -> List[PolicySnapshotData]` | no | Get snapshot version history for a tenant. |
| `verify_snapshot` | `(snapshot_id: str) -> dict[str, Any]` | no | Verify snapshot integrity. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass, field | no |
| `datetime` | datetime, timezone | no |
| `enum` | Enum | no |
| `typing` | Any, List, Optional | no |
| `hashlib` | hashlib | no |
| `json` | json | no |
| `uuid` | uuid | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## state.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/state.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 108

**Docstring:** Phase-6 Billing State — Commercial State Model

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `BillingState` | from_string, default, allows_usage, is_in_good_standing | Phase-6 Billing States (Tenant-scoped). |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `enum` | Enum | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`BillingState`

---

## tokenizer.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/tokenizer.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 352

**Docstring:** Tokenizer for PLang v2.0 with M19 category support.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `TokenType` |  | Token types for PLang v2.0. |
| `Token` | __repr__, is_category, is_action | A token in PLang source code. |
| `TokenizerError` | __init__ | Error during tokenization. |
| `Tokenizer` | __init__, current_char, peek, advance, skip_whitespace, skip_comment, read_string, read_number (+4 more) | Tokenizer for PLang v2.0. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `enum` | Enum, auto | no |
| `typing` | Iterator, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`KEYWORD_TOKENS`

---

## validator.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/validator.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 386

**Docstring:** Policy DSL Semantic Validator

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `Severity` |  | Severity level for validation issues. |
| `ValidationIssue` | __str__ | A single validation issue found in the policy. |
| `ValidationResult` | __post_init__, errors, warnings, __bool__ | Result of policy validation. |
| `PolicyValidator` | __init__, validate, _validate_mode_enforcement, _validate_metrics, _extract_metrics, _validate_structure, _check_warnings | Validates PolicyAST against semantic rules. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `validate` | `(policy: PolicyAST, allowed_metrics: set[str] | None = None) -> ValidationResult` | no | Validate a policy AST. |
| `is_valid` | `(policy: PolicyAST, allowed_metrics: set[str] | None = None) -> bool` | no | Quick check if a policy is valid. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `__future__` | annotations | no |
| `dataclasses` | dataclass, field | no |
| `enum` | Enum | no |
| `typing` | Callable | no |
| `app.dsl.ast` | Condition, Mode, PolicyAST, is_block_action, is_exists_predicate (+3) | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### Constants
`V001`, `V002`, `V010`, `V020`, `V021`, `W001`, `W002`

---

## visitors.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/visitors.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 307

**Docstring:** AST visitors for PLang v2.0.

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `BaseVisitor` | visit_program, visit_policy_decl, visit_rule_decl, visit_import, visit_rule_ref, visit_priority, visit_condition_block, visit_action_block (+7 more) | Base visitor with default implementations. |
| `PrintVisitor` | __init__, _emit, get_output, visit_program, visit_policy_decl, visit_rule_decl, visit_import, visit_rule_ref (+10 more) | Visitor that prints AST in readable format. |
| `CategoryCollector` | __init__, get_categories, visit_policy_decl, visit_rule_decl | Visitor that collects all categories used in the AST. |
| `RuleExtractor` | __init__, get_rules, visit_policy_decl, visit_rule_decl, visit_condition_block | Visitor that extracts all rules with their governance metadata. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `typing` | Any, Dict, List | no |
| `app.policy.ast.nodes` | ActionBlockNode, ASTVisitor, AttrAccessNode, BinaryOpNode, ConditionBlockNode (+11) | no |
| `app.policy.compiler.grammar` | PolicyCategory | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

---

## worker_execution_command.py
**Path:** `backend/app/hoc/cus/policies/L5_engines/worker_execution_command.py`  
**Layer:** L5_engines | **Domain:** policies | **Lines:** 355

**Docstring:** Worker Execution Command (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `WorkerExecutionResult` |  | Result from worker execution command. |
| `ReplayResult` |  | Result from replay command. |

### Functions
| Name | Signature | Async | Docstring |
|------|-----------|-------|-----------|
| `calculate_cost_cents` | `(model: str, input_tokens: int, output_tokens: int) -> int` | no | Calculate LLM cost in cents. |
| `get_brand_schema_types` | `()` | no | Get brand schema types from L5. |
| `convert_brand_request` | `(brand_req) -> Any` | no | Convert API brand request to BrandSchema. |
| `execute_worker` | `(task: str, brand: Optional[Any] = None, budget: Optional[int] = None, strict_mo` | yes | Execute Business Builder Worker. |
| `replay_execution` | `(replay_token: str, run_id: str) -> ReplayResult` | yes | Replay a previous execution. |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `dataclasses` | dataclass | no |
| `typing` | Any, Dict, List, Optional | no |

### Prescriptive Wiring (per HOC_LAYER_TOPOLOGY_V1)

**Contract:** Business logic — pattern detection, decisions, calls L6 for DB ops

**SHOULD call:** L6_drivers, L5_schemas
**MUST NOT call:** L2_api, L3_adapters, L7_models
**Called by:** L3_adapters, L4_runtime

### __all__ Exports
`WorkerExecutionResult`, `ReplayResult`, `calculate_cost_cents`, `get_brand_schema_types`, `convert_brand_request`, `execute_worker`, `replay_execution`

---
