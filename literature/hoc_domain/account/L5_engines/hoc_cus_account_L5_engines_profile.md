# hoc_cus_account_L5_engines_profile

| Field | Value |
|-------|-------|
| Path | `backend/app/hoc/cus/account/L5_engines/profile.py` |
| Layer | L5 — Domain Engine |
| Domain | account |
| Audience | CUSTOMER |
| Artifact Class | CODE |

## Description

Governance Profile configuration and validation

## Intent

**Role:** Governance Profile configuration and validation
**Reference:** PIN-470, PIN-454 (Cross-Domain Orchestration Audit), Section 2.1
**Callers:** main.py (L2), workers (L5)

## Purpose

Governance Profile Configuration

---

## Functions

### `_get_bool_env(name: str, default: bool) -> bool`
- **Async:** No
- **Docstring:** Get boolean from environment variable.
- **Calls:** getenv, lower

### `get_governance_profile() -> GovernanceProfile`
- **Async:** No
- **Docstring:** Get the current governance profile from environment.  Returns:
- **Calls:** GovernanceProfile, getenv, upper, warning

### `load_governance_config() -> GovernanceConfig`
- **Async:** No
- **Docstring:** Load complete governance configuration.  Loads profile defaults, then applies any environment variable overrides.
- **Calls:** GovernanceConfig, _get_bool_env, get_governance_profile, info, to_dict

### `validate_governance_config(config: Optional[GovernanceConfig]) -> List[str]`
- **Async:** No
- **Docstring:** Validate governance configuration for invalid combinations.  Args:
- **Calls:** GovernanceConfigError, all, append, error, get, info, len, load_governance_config, warning

### `get_governance_config() -> GovernanceConfig`
- **Async:** No
- **Docstring:** Get the validated governance configuration singleton.  Loads and validates on first call, caches thereafter.
- **Calls:** load_governance_config, validate_governance_config

### `reset_governance_config() -> None`
- **Async:** No
- **Docstring:** Reset the singleton (for testing).

### `validate_governance_at_startup() -> None`
- **Async:** No
- **Docstring:** Validate governance configuration at application startup.  Call this from main.py during FastAPI lifespan startup.
- **Calls:** get_governance_config, info

## Classes

### `GovernanceProfile(str, Enum)`
- **Docstring:** Pre-defined governance profiles.

### `GovernanceConfig`
- **Docstring:** Complete governance configuration derived from profile + overrides.
- **Methods:** to_dict
- **Class Variables:** profile: GovernanceProfile, rok_enabled: bool, rac_enabled: bool, transaction_coordinator_enabled: bool, event_reactor_enabled: bool, mid_execution_policy_check_enabled: bool, rac_durability_enforce: bool, phase_status_invariant_enforce: bool, rac_rollback_audit_enabled: bool, alert_fatigue_enabled: bool

### `GovernanceConfigError(Exception)`
- **Docstring:** Raised when governance configuration is invalid.
- **Methods:** __init__

## Attributes

- `logger` (line 65)
- `PROFILE_DEFAULTS: Dict[GovernanceProfile, Dict[str, bool]]` (line 157)
- `INVALID_COMBINATIONS: List[Tuple[FrozenSet[str], str]]` (line 199)
- `REQUIRED_COMBINATIONS: List[Tuple[str, str, str]]` (line 223)
- `_governance_config: Optional[GovernanceConfig]` (line 408)

---

## Import Analysis

| Category | Imports |
|----------|---------|
| _None_ | Pure stdlib |

## Callers

main.py (L2), workers (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: get_governance_profile
      signature: "get_governance_profile() -> GovernanceProfile"
    - name: load_governance_config
      signature: "load_governance_config() -> GovernanceConfig"
    - name: validate_governance_config
      signature: "validate_governance_config(config: Optional[GovernanceConfig]) -> List[str]"
    - name: get_governance_config
      signature: "get_governance_config() -> GovernanceConfig"
    - name: reset_governance_config
      signature: "reset_governance_config() -> None"
    - name: validate_governance_at_startup
      signature: "validate_governance_at_startup() -> None"
  classes:
    - name: GovernanceProfile
      methods: []
    - name: GovernanceConfig
      methods: [to_dict]
    - name: GovernanceConfigError
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
