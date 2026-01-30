# hoc_models_knowledge_lifecycle

| Field | Value |
|-------|-------|
| Path | `backend/app/models/knowledge_lifecycle.py` |
| Layer | L4 — Domain Engine |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

GAP-089 Knowledge Plane Lifecycle State Machine

## Intent

**Role:** GAP-089 Knowledge Plane Lifecycle State Machine
**Reference:** GAP-089, DOMAINS_E2E_SCAFFOLD_V3.md Section 7.15.2
**Callers:** KnowledgeLifecycleManager, SDK facade, policy gates

## Purpose

GAP-089: Knowledge Plane Lifecycle State Machine

---

## Functions

### `is_valid_transition(from_state: KnowledgePlaneLifecycleState, to_state: KnowledgePlaneLifecycleState) -> bool`
- **Async:** No
- **Docstring:** Check if a lifecycle transition is valid.  Enforces:
- **Calls:** get, set

### `get_valid_transitions(from_state: KnowledgePlaneLifecycleState) -> Set[KnowledgePlaneLifecycleState]`
- **Async:** No
- **Docstring:** Get all valid target states from a given state.
- **Calls:** copy, get, set

### `validate_transition(from_state: KnowledgePlaneLifecycleState, to_state: KnowledgePlaneLifecycleState) -> TransitionResult`
- **Async:** No
- **Docstring:** Validate a lifecycle transition and return detailed result.  Returns TransitionResult with:
- **Calls:** TransitionResult, get_valid_transitions, is_valid_transition, requires_async_job, requires_policy_gate

### `get_action_for_transition(from_state: KnowledgePlaneLifecycleState, to_state: KnowledgePlaneLifecycleState) -> Optional[str]`
- **Async:** No
- **Docstring:** Get the action name for a given transition, if valid.
- **Calls:** items

### `get_transition_for_action(action: str, current_state: KnowledgePlaneLifecycleState) -> Optional[KnowledgePlaneLifecycleState]`
- **Async:** No
- **Docstring:** Get the target state for an action from current state, if valid.
- **Calls:** get_next_onboarding_state

### `get_next_onboarding_state(current: KnowledgePlaneLifecycleState) -> Optional[KnowledgePlaneLifecycleState]`
- **Async:** No
- **Docstring:** Get the next state in the onboarding path, if applicable.
- **Calls:** index, len

### `get_next_offboarding_state(current: KnowledgePlaneLifecycleState) -> Optional[KnowledgePlaneLifecycleState]`
- **Async:** No
- **Docstring:** Get the next state in the offboarding path, if applicable.
- **Calls:** index, len

## Classes

### `KnowledgePlaneLifecycleState(IntEnum)`
- **Docstring:** Knowledge plane lifecycle states.
- **Methods:** is_onboarding, is_operational, is_offboarding, is_terminal, is_failed, allows_queries, allows_policy_binding, allows_new_runs, allows_modifications, requires_async_job, requires_policy_gate

### `LifecycleAction`
- **Docstring:** Named lifecycle actions that trigger state transitions.

### `TransitionResult`
- **Docstring:** Result of a lifecycle transition attempt.
- **Methods:** __bool__
- **Class Variables:** allowed: bool, from_state: KnowledgePlaneLifecycleState, to_state: KnowledgePlaneLifecycleState, reason: Optional[str], requires_gate: bool, requires_async: bool

## Attributes

- `VALID_TRANSITIONS: dict[KnowledgePlaneLifecycleState, Set[KnowledgePlaneLifecycleState]]` (line 146)
- `ACTION_TRANSITIONS: dict[str, Tuple[Set[KnowledgePlaneLifecycleState], KnowledgePlaneLifecycleState]]` (line 231)
- `JOB_COMPLETE_STATES: Set[KnowledgePlaneLifecycleState]` (line 286)
- `ILLEGAL_TRANSITIONS: list[Tuple[KnowledgePlaneLifecycleState, KnowledgePlaneLifecycleState, str]]` (line 456)
- `__all__` (line 482)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

KnowledgeLifecycleManager, SDK facade, policy gates

## Export Contract

```yaml
exports:
  functions:
    - name: is_valid_transition
      signature: "is_valid_transition(from_state: KnowledgePlaneLifecycleState, to_state: KnowledgePlaneLifecycleState) -> bool"
    - name: get_valid_transitions
      signature: "get_valid_transitions(from_state: KnowledgePlaneLifecycleState) -> Set[KnowledgePlaneLifecycleState]"
    - name: validate_transition
      signature: "validate_transition(from_state: KnowledgePlaneLifecycleState, to_state: KnowledgePlaneLifecycleState) -> TransitionResult"
    - name: get_action_for_transition
      signature: "get_action_for_transition(from_state: KnowledgePlaneLifecycleState, to_state: KnowledgePlaneLifecycleState) -> Optional[str]"
    - name: get_transition_for_action
      signature: "get_transition_for_action(action: str, current_state: KnowledgePlaneLifecycleState) -> Optional[KnowledgePlaneLifecycleState]"
    - name: get_next_onboarding_state
      signature: "get_next_onboarding_state(current: KnowledgePlaneLifecycleState) -> Optional[KnowledgePlaneLifecycleState]"
    - name: get_next_offboarding_state
      signature: "get_next_offboarding_state(current: KnowledgePlaneLifecycleState) -> Optional[KnowledgePlaneLifecycleState]"
  classes:
    - name: KnowledgePlaneLifecycleState
      methods: [is_onboarding, is_operational, is_offboarding, is_terminal, is_failed, allows_queries, allows_policy_binding, allows_new_runs, allows_modifications, requires_async_job, requires_policy_gate]
    - name: LifecycleAction
      methods: []
    - name: TransitionResult
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
