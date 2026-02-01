# profile_policy_mode.py

**Path:** `backend/app/hoc/cus/hoc_spine/authority/profile_policy_mode.py`  
**Layer:** L4 — HOC Spine (Authority)  
**Component:** Authority

---

## Placement Card

```
File:            profile_policy_mode.py
Lives in:        authority/
Role:            Authority
Inbound:         main.py (L2), workers (L5)
Outbound:        none
Transaction:     Forbidden
Cross-domain:    none
Purpose:         Governance Profile Configuration
Violations:      none
```

## Purpose

Governance Profile Configuration

Reduces cognitive load and configuration drift by providing three
well-defined governance profiles:

- STRICT: Full enforcement, all features enabled, production-ready
- STANDARD: Core features enabled, some optional features disabled
- OBSERVE_ONLY: Audit and observe without enforcement (safe rollout)

Usage:
    from app.hoc.cus.hoc_spine.authority.profile_policy_mode import (
        get_governance_profile,
        validate_governance_config,
        GovernanceProfile,
    )

    # At startup
    profile = get_governance_profile()
    validate_governance_config()  # Raises if invalid combination

    # Check profile
    if profile == GovernanceProfile.STRICT:
        # Full enforcement mode
        ...

Environment Variables:
    GOVERNANCE_PROFILE: STRICT | STANDARD | OBSERVE_ONLY (default: STANDARD)

    Individual flags (override profile defaults):
    - ROK_ENABLED
    - RAC_ENABLED
    - TRANSACTION_COORDINATOR_ENABLED
    - EVENT_REACTOR_ENABLED
    - MID_EXECUTION_POLICY_CHECK_ENABLED
    - RAC_DURABILITY_ENFORCE (STRICT only)
    - PHASE_STATUS_INVARIANT_ENFORCE (STRICT only)

## Import Analysis

Pure stdlib — no application imports.

## Transaction Boundary

- **Commits:** no
- **Flushes:** no
- **Rollbacks:** no

## Functions

### `_get_bool_env(name: str, default: bool) -> bool`

Get boolean from environment variable.

### `get_governance_profile() -> GovernanceProfile`

Get the current governance profile from environment.

Returns:
    GovernanceProfile enum value

### `load_governance_config() -> GovernanceConfig`

Load complete governance configuration.

Loads profile defaults, then applies any environment variable overrides.

Returns:
    GovernanceConfig with all settings

### `validate_governance_config(config: Optional[GovernanceConfig]) -> List[str]`

Validate governance configuration for invalid combinations.

Args:
    config: Configuration to validate (loads from env if not provided)

Returns:
    List of warning messages (empty if valid)

Raises:
    GovernanceConfigError: If configuration has blocking violations

### `get_governance_config() -> GovernanceConfig`

Get the validated governance configuration singleton.

Loads and validates on first call, caches thereafter.

Returns:
    Validated GovernanceConfig

### `reset_governance_config() -> None`

Reset the singleton (for testing).

### `validate_governance_at_startup() -> None`

Validate governance configuration at application startup.

Call this from main.py during FastAPI lifespan startup.

Raises:
    GovernanceConfigError: If configuration is invalid

## Classes

### `GovernanceProfile(str, Enum)`

Pre-defined governance profiles.

Each profile represents a coherent set of feature flag settings
designed for specific deployment scenarios.

### `GovernanceConfig`

Complete governance configuration derived from profile + overrides.

#### Methods

- `to_dict() -> Dict[str, object]` — Serialize for logging.

### `GovernanceConfigError(Exception)`

Raised when governance configuration is invalid.

#### Methods

- `__init__(message: str, violations: List[str])` — _No docstring._

## Domain Usage

**Callers:** main.py (L2), workers (L5)

## Export Contract

```yaml
exports:
  functions:
    - name: _get_bool_env
      signature: "_get_bool_env(name: str, default: bool) -> bool"
      consumers: ["orchestrator"]
    - name: get_governance_profile
      signature: "get_governance_profile() -> GovernanceProfile"
      consumers: ["orchestrator"]
    - name: load_governance_config
      signature: "load_governance_config() -> GovernanceConfig"
      consumers: ["orchestrator"]
    - name: validate_governance_config
      signature: "validate_governance_config(config: Optional[GovernanceConfig]) -> List[str]"
      consumers: ["orchestrator"]
    - name: get_governance_config
      signature: "get_governance_config() -> GovernanceConfig"
      consumers: ["orchestrator"]
    - name: reset_governance_config
      signature: "reset_governance_config() -> None"
      consumers: ["orchestrator"]
    - name: validate_governance_at_startup
      signature: "validate_governance_at_startup() -> None"
      consumers: ["orchestrator"]
  classes:
    - name: GovernanceProfile
      methods: []
      consumers: ["orchestrator"]
    - name: GovernanceConfig
      methods:
        - to_dict
      consumers: ["orchestrator"]
    - name: GovernanceConfigError
      methods:
      consumers: ["orchestrator"]
  protocols: []
```

## Import Boundary

```yaml
boundary:
  allowed_inbound:
    - "hoc_spine.orchestrator.*"
  forbidden_inbound:
    - "hoc.cus.*"
    - "hoc.api.*"
  actual_imports:
    spine_internal: []
    l7_model: []
    external: []
  violations: []
```

## L5 Pairing Declaration

```yaml
pairing:
  serves_domains: []
  expected_l5_consumers: []
  orchestrator_operations: []
```

