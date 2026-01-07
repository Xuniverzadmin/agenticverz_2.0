# UI Irreversible-Action Contract

**Version:** 1.0.0
**Status:** NORMATIVE
**Effective:** 2026-01-07
**Applies to:** Customer Console (GC_L + FACILITATION)
**Reference:** PIN-342

---

## 1. Scope

This contract governs any customer-initiated action that is irreversible or has irreversible downstream effects within the Customer Console.

---

## 2. Definitions

### 2.1 Irreversible Action

An action is **irreversible** if **any** of the following is true:

| Condition | Example |
|-----------|---------|
| Cannot be fully undone | Policy activation that blocks runs |
| Produces downstream effects that cannot be rewound | Pausing executions |
| Changes enforcement posture | MONITOR → ENFORCE |
| Alters cost/availability materially | Spend caps |
| Changes governance state | Killswitch engagement |

### 2.2 Human Sovereignty

Only a **human actor** may authorize irreversible impact. Systems may **prepare**, **simulate**, and **recommend** — they may not decide or execute.

---

## 3. Obligations (MUST)

### 3.1 Explicit Intent Declaration

The UI **MUST** present the exact action name and scope prior to authorization.

- No euphemisms
- No icon-only confirmation

### 3.2 Explicit Consequence Disclosure

The UI **MUST** list concrete consequences in plain language:

- What will stop
- What will continue
- Scope of impact

### 3.3 Simulation / Preview

If simulation exists for the action, the UI **MUST** display:

- Affected entities count
- Historical "would have happened" summary

If unavailable, the UI **MUST** state: "Simulation unavailable"

### 3.4 Human Attribution Capture

The UI **MUST** capture:

- Actor identity (implicit via auth)
- Explicit confirmation
- Reason/justification text (required for ENFORCE, KILLSWITCH)

### 3.5 Deliberate Confirmation

Irreversible actions **MUST** require ≥2 deliberate steps:

| Mode | Description |
|------|-------------|
| `TYPED` | User types confirmation phrase |
| `MODAL` | Two-step modal dialog |
| `DELAYED` | Countdown timer before confirm enabled |

### 3.6 Post-Action State Visibility

After execution, the UI **MUST** immediately display:

- New state
- Scope
- Reversibility (or lack thereof)

---

## 4. Prohibitions (MUST NOT)

| Prohibition | Reason |
|-------------|--------|
| Bundle multiple irreversible actions | Prevents hidden consequences |
| Auto-focus or default to "Confirm" | Prevents accidental confirmation |
| Auto-trigger based on FACILITATION | Preserves human sovereignty |
| Use language implying system decided | Maintains attribution clarity |
| Hide irreversible actions behind simple toggles | Prevents accidental activation |

---

## 5. Action Metadata Schema

Every irreversible UI action **MUST** declare metadata:

```json
{
  "action_id": "string",
  "irreversible": true,
  "requires_simulation": boolean,
  "requires_reason": boolean,
  "min_confirmation_steps": 2,
  "confirmation_mode": ["TYPED" | "MODAL" | "DELAYED"],
  "allowed_copy": ["string array"]
}
```

---

## 6. Endpoint Mapping

### 6.1 Policies

| Endpoint | Irreversible | Requirements |
|----------|--------------|--------------|
| `POST /api/customer/policies` | NO | Basic confirmation |
| `POST /api/customer/policies/{id}/simulate` | NO | None |
| `POST /api/customer/policies/{id}/activate` | **YES** | Intent, consequences, simulation, reason, ≥2 steps |
| `POST /api/customer/policies/{id}/mode` | **YES** | Consequences, simulation, typed confirm, reason |

### 6.2 Killswitch

| Endpoint | Irreversible | Requirements |
|----------|--------------|--------------|
| `POST /api/customer/killswitch` | **YES** | Intent, scope, reason, delayed confirm |
| `POST /api/customer/killswitch/resume` | NO | Single confirm + reason |

### 6.3 Spend Guardrails

| Endpoint | Irreversible | Requirements |
|----------|--------------|--------------|
| `POST /api/customer/spend/guardrails` | **YES** | Consequences, simulation, reason, ≥2 steps |

### 6.4 Integrations

| Endpoint | Irreversible | Requirements |
|----------|--------------|--------------|
| `POST /api/customer/integrations/{id}/disable` | **YES** | Consequences, reason, two-step confirm |

---

## 7. Request Payload Schema

```json
{
  "actor_id": "uuid",
  "intent": "ACTIVATE | PAUSE | DISABLE | CONFIGURE",
  "confirmation": true,
  "confirmation_steps_completed": 2,
  "reason": "string",
  "evidence_refs": ["simulation_id"]
}
```

---

## 8. Backend Rejection Rules

Backend **MUST** reject with `409 GOVERNANCE_VIOLATION` when:

| Condition |
|-----------|
| Action metadata marks irreversible and UI did not meet contract |
| `confirmation` is false |
| `reason` missing where required |
| Simulation required but not referenced |
| Actor is not human |

---

## 9. Frontend Validation Rules

### 9.1 Action Gating

Block submission unless:
- `confirmation === true`
- `confirmation_steps_completed >= min_confirmation_steps`
- `reason` present when required

### 9.2 Copy Guard

- Only render strings from `allowed_copy`
- Other copy → build-time lint failure

### 9.3 Simulation Gate

If `requires_simulation === true`:
- Fetch and display simulation
- Include `evidence_refs: [simulation_id]` in payload

### 9.4 FACILITATION Guard

FACILITATION **MAY** prefill forms.
FACILITATION **MUST NOT**:
- Trigger submits
- Auto-set confirmation
- Reduce confirmation steps

---

## 10. Governance

This contract is **NORMATIVE**. Changes require:

1. PIN update with rationale
2. Human ratification
3. Version increment

---

**Status:** NORMATIVE
**Reference:** PIN-342
