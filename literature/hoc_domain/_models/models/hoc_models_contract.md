# hoc_models_contract

| Field | Value |
|-------|-------|
| Path | `backend/app/models/contract.py` |
| Layer | L6 — Platform Substrate |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

System Contract database models

## Intent

**Role:** System Contract database models
**Reference:** PIN-291, SYSTEM_CONTRACT_OBJECT.md, part2-design-v1
**Callers:** governance/*, L4 domain services

## Purpose

System Contract Models (Part-2 CRM Workflow)

---

## Classes

### `ContractStatus(str, Enum)`
- **Docstring:** System Contract lifecycle states.

### `AuditVerdict(str, Enum)`
- **Docstring:** Audit verification verdict.

### `RiskLevel(str, Enum)`
- **Docstring:** Risk level classification.

### `ProposedChangeType(str, Enum)`
- **Docstring:** Types of proposed changes in a contract.

### `ContractSource(str, Enum)`
- **Docstring:** Issue source classification.

### `SystemContract(Base)`
- **Docstring:** System Contract database model.

### `ProposedChangeBase(BaseModel)`
- **Docstring:** Base schema for proposed changes.
- **Class Variables:** type: ProposedChangeType

### `CapabilityEnableChange(ProposedChangeBase)`
- **Docstring:** Enable a capability.
- **Class Variables:** type: ProposedChangeType, capability_name: str, target_lifecycle: str

### `CapabilityDisableChange(ProposedChangeBase)`
- **Docstring:** Disable a capability.
- **Class Variables:** type: ProposedChangeType, capability_name: str, reason: str

### `ConfigurationUpdateChange(ProposedChangeBase)`
- **Docstring:** Update configuration.
- **Class Variables:** type: ProposedChangeType, scope: str, key: str, old_value: Any, new_value: Any

### `ParameterChangeChange(ProposedChangeBase)`
- **Docstring:** Change parameters.
- **Class Variables:** type: ProposedChangeType, scope: str, parameters: dict[str, Any]

### `ValidatorVerdictData(BaseModel)`
- **Docstring:** Stored validator verdict data.
- **Class Variables:** issue_type: str, severity: str, affected_capabilities: list[str], recommended_action: str, confidence_score: Decimal, reason: str, analyzed_at: datetime, validator_version: str

### `EligibilityVerdictData(BaseModel)`
- **Docstring:** Stored eligibility verdict data.
- **Class Variables:** decision: str, reason: str, blocking_signals: list[str], missing_prerequisites: list[str], evaluated_at: datetime, rules_version: str

### `TransitionRecord(BaseModel)`
- **Docstring:** Record of a state transition.
- **Class Variables:** from_status: str, to_status: str, reason: str, transitioned_by: str, transitioned_at: datetime

### `ContractCreate(BaseModel)`
- **Docstring:** Input model for creating a contract from validated proposal.
- **Methods:** validate_confidence
- **Class Variables:** issue_id: UUID, source: ContractSource, title: str, description: Optional[str], proposed_changes: dict[str, Any], affected_capabilities: list[str], risk_level: RiskLevel, validator_verdict: ValidatorVerdictData, eligibility_verdict: EligibilityVerdictData, confidence_score: Decimal, created_by: str, expires_at: Optional[datetime]

### `ContractResponse(BaseModel)`
- **Docstring:** Output model for contract data.
- **Class Variables:** contract_id: UUID, version: int, issue_id: UUID, source: str, status: str, status_reason: Optional[str], title: str, description: Optional[str], proposed_changes: dict[str, Any], affected_capabilities: list[str], risk_level: str, validator_verdict: Optional[dict[str, Any]], eligibility_verdict: Optional[dict[str, Any]], confidence_score: Optional[Decimal], created_by: str, approved_by: Optional[str], approved_at: Optional[datetime], activation_window_start: Optional[datetime], activation_window_end: Optional[datetime], execution_constraints: Optional[dict[str, Any]], job_id: Optional[UUID], audit_verdict: str, audit_reason: Optional[str], audit_completed_at: Optional[datetime], created_at: datetime, updated_at: datetime, expires_at: Optional[datetime], transition_history: list[dict[str, Any]]

### `ContractApproval(BaseModel)`
- **Docstring:** Input model for founder approval.
- **Class Variables:** approved_by: str, activation_window_hours: int, execution_constraints: Optional[dict[str, Any]]

### `ContractRejection(BaseModel)`
- **Docstring:** Input model for rejection.
- **Class Variables:** rejected_by: str, reason: str

### `InvalidTransitionError(Exception)`
- **Docstring:** Raised when an invalid state transition is attempted.
- **Methods:** __init__

### `ContractImmutableError(Exception)`
- **Docstring:** Raised when attempting to modify an immutable contract.
- **Methods:** __init__

### `MayNotVerdictError(Exception)`
- **Docstring:** Raised when attempting to create a contract with MAY_NOT verdict.
- **Methods:** __init__

## Attributes

- `TERMINAL_STATES` (line 82)
- `VALID_TRANSITIONS: dict[ContractStatus, frozenset[ContractStatus]]` (line 154)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| L7 Model | `app.models.costsim_cb` |
| External | `pydantic`, `sqlalchemy`, `sqlalchemy.dialects.postgresql` |

## Callers

governance/*, L4 domain services

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: ContractStatus
      methods: []
    - name: AuditVerdict
      methods: []
    - name: RiskLevel
      methods: []
    - name: ProposedChangeType
      methods: []
    - name: ContractSource
      methods: []
    - name: SystemContract
      methods: []
    - name: ProposedChangeBase
      methods: []
    - name: CapabilityEnableChange
      methods: []
    - name: CapabilityDisableChange
      methods: []
    - name: ConfigurationUpdateChange
      methods: []
    - name: ParameterChangeChange
      methods: []
    - name: ValidatorVerdictData
      methods: []
    - name: EligibilityVerdictData
      methods: []
    - name: TransitionRecord
      methods: []
    - name: ContractCreate
      methods: [validate_confidence]
    - name: ContractResponse
      methods: []
    - name: ContractApproval
      methods: []
    - name: ContractRejection
      methods: []
    - name: InvalidTransitionError
      methods: []
    - name: ContractImmutableError
      methods: []
    - name: MayNotVerdictError
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
