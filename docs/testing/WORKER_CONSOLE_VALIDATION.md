# Worker Execution Console - Validation Test Scenarios

**Created:** 2024-12-16
**Purpose:** Test scenarios for validating Risk Areas identified during debugging

---

## Risk 1: Drift & Recovery Events Testing

These scenarios force `drift_detected`, `failure_detected`, `recovery_applied`, and `policy_violation` events.

### Test 1.1: Policy Violation - Forbidden Claims

**Goal:** Trigger `policy_violation` event

**Brand Configuration:**
```json
{
  "company_name": "MegaCorp AI",
  "mission": "We are the world's best AI company making guaranteed results",
  "value_proposition": "100% accurate predictions that are completely risk-free for your business",
  "tagline": "Guaranteed Results or Your Money Back",
  "target_audience": ["b2b_enterprise"],
  "tone": {
    "primary": "professional",
    "avoid": []
  },
  "forbidden_claims": [
    {"pattern": "world's best", "reason": "Unverifiable superlative", "severity": "error"},
    {"pattern": "guaranteed results", "reason": "Cannot guarantee outcomes", "severity": "error"},
    {"pattern": "100% accurate", "reason": "Unverifiable accuracy", "severity": "error"},
    {"pattern": "risk-free", "reason": "All investments carry risk", "severity": "warning"}
  ]
}
```

**Task:** "Create a landing page that emphasizes our unbeatable track record"

**Expected Events:**
- `policy_violation` for "world's best" in mission
- `policy_violation` for "guaranteed results" in mission
- `policy_violation` for "100% accurate" in value_proposition
- `policy_violation` (warning) for "risk-free" in value_proposition

---

### Test 1.2: Drift Detection - Contradictory Brand

**Goal:** Trigger `drift_detected` event with high drift score

**Brand Configuration:**
```json
{
  "company_name": "LuxuryTech Elite",
  "mission": "Exclusive premium technology solutions for discerning enterprises",
  "value_proposition": "Bespoke, white-glove enterprise solutions with unparalleled sophistication",
  "tagline": "Excellence Redefined",
  "target_audience": ["b2b_enterprise"],
  "tone": {
    "primary": "luxury",
    "avoid": ["casual"],
    "examples_good": ["curated experience", "bespoke solutions", "distinguished clientele"],
    "examples_bad": ["cheap", "budget", "basic", "easy"]
  }
}
```

**Task:** "Write super casual copy with lots of slang and emojis for Gen Z audience"

**Expected Events:**
- `drift_detected` with high drift score (task contradicts luxury brand)
- Possible `stage_failed` or `recovery_started` if drift exceeds threshold

---

### Test 1.3: Budget Constraint Failure

**Goal:** Trigger budget-related failure and recovery

**Brand Configuration:**
```json
{
  "company_name": "BudgetTest Inc",
  "mission": "Testing budget constraints in the worker pipeline",
  "value_proposition": "Minimal budget allocation to force constraint violations",
  "target_audience": ["b2b_smb"],
  "tone": {
    "primary": "professional"
  },
  "budget_tokens": 1000
}
```

**Task:** "Create a comprehensive 10-page marketing strategy with full competitive analysis, 50 headline variations, and detailed UX specifications"

**Expected Events:**
- `failure_detected` with pattern "budget_exceeded"
- `recovery_started` with action "reduce_scope" or "truncate"
- `recovery_completed` or `run_failed` depending on severity

---

### Test 1.4: Invalid Task Trigger

**Goal:** Trigger `failure_detected` at preflight stage

**Task (empty or invalid):** ""

**Expected Events:**
- `stage_failed` at preflight
- `failure_detected` with pattern "validation_error"

---

## Risk 3: Brand Preset Defaults Testing

### Valid Enum Values Reference

**ToneLevel (tone.primary):**
- `casual`
- `neutral`
- `professional`
- `formal`
- `luxury`

**AudienceSegment (target_audience[]):**
- `b2c_consumer`
- `b2c_prosumer`
- `b2b_smb`
- `b2b_enterprise`
- `b2b_developer`

---

### Test 3.1: All Tone Levels

Run with each tone level to verify no validation errors:

| Test | tone.primary | Expected |
|------|--------------|----------|
| 3.1a | `casual` | Pass |
| 3.1b | `neutral` | Pass |
| 3.1c | `professional` | Pass |
| 3.1d | `formal` | Pass |
| 3.1e | `luxury` | Pass |

**Base Brand:**
```json
{
  "company_name": "ToneTest Co",
  "mission": "Testing all tone levels work correctly",
  "value_proposition": "Ensuring proper enum validation across all supported tones",
  "target_audience": ["b2b_smb"],
  "tone": {
    "primary": "<TONE_VALUE>",
    "avoid": []
  }
}
```

---

### Test 3.2: All Audience Segments

| Test | target_audience | Expected |
|------|-----------------|----------|
| 3.2a | `["b2c_consumer"]` | Pass |
| 3.2b | `["b2c_prosumer"]` | Pass |
| 3.2c | `["b2b_smb"]` | Pass |
| 3.2d | `["b2b_enterprise"]` | Pass |
| 3.2e | `["b2b_developer"]` | Pass |
| 3.2f | `["b2c_consumer", "b2c_prosumer"]` | Pass (multi) |

---

### Test 3.3: Mixed Audience + Tone Combinations

| Test | Tone | Audience | Scenario |
|------|------|----------|----------|
| 3.3a | `luxury` | `b2b_enterprise` | High-end B2B |
| 3.3b | `casual` | `b2c_consumer` | Consumer app |
| 3.3c | `formal` | `b2b_developer` | Developer docs |
| 3.3d | `neutral` | `b2b_smb` | SMB SaaS |

---

## Validation Checklist

### Pre-Test Setup
- [ ] Console accessible at agenticverz.com/console/workers
- [ ] API token set in localStorage (`aos_token`)
- [ ] Browser DevTools open for console logs
- [ ] Network tab monitoring SSE stream

### Event Verification
- [ ] `connected` event received
- [ ] `run_started` event received
- [ ] `stage_started` events for each stage
- [ ] `stage_completed` events with duration/tokens
- [ ] `log` events with stage_id and agent
- [ ] `routing_decision` events with agent selection
- [ ] `artifact_created` events WITH content
- [ ] `run_completed` event with totals

### Failure Path Events (Risk 1)
- [ ] `policy_violation` triggered with forbidden claims
- [ ] `drift_detected` triggered with contradictory task
- [ ] `failure_detected` triggered with budget/validation
- [ ] `recovery_started` triggered after failure
- [ ] `recovery_completed` or graceful degradation

### Brand Validation (Risk 3)
- [ ] All 5 ToneLevel values accepted
- [ ] All 5 AudienceSegment values accepted
- [ ] Multi-audience arrays accepted
- [ ] Invalid enum values rejected (422)

---

## Quick Test Commands

### Test via curl (Backend Direct)

```bash
# Set token
export AOS_TOKEN="your-token-here"

# Test 1.1: Policy violation brand
curl -X POST https://agenticverz.com/api/v1/workers/business-builder/run-streaming \
  -H "Content-Type: application/json" \
  -H "X-AOS-Key: $AOS_TOKEN" \
  -d '{
    "task": "Create marketing copy",
    "brand": {
      "company_name": "TestCorp",
      "mission": "We guarantee the worlds best results",
      "value_proposition": "100% accurate AI that is completely risk-free",
      "target_audience": ["b2b_smb"],
      "tone": {"primary": "professional"}
    }
  }'

# Test 3.1e: Luxury tone
curl -X POST https://agenticverz.com/api/v1/workers/business-builder/run-streaming \
  -H "Content-Type: application/json" \
  -H "X-AOS-Key: $AOS_TOKEN" \
  -d '{
    "task": "Create premium landing page",
    "brand": {
      "company_name": "LuxTech",
      "mission": "Premium solutions for discerning clients",
      "value_proposition": "Bespoke technology experiences for the elite enterprise",
      "target_audience": ["b2b_enterprise"],
      "tone": {"primary": "luxury"}
    }
  }'
```

---

## Log Color Reference

When viewing browser DevTools console:

| Color | Source | Prefix |
|-------|--------|--------|
| Purple | API Client | `[WORKER-API]` |
| Green | SSE Hook | `[SSE-HOOK]` |
| Orange | Console UI | `[CONSOLE-UI]` |

---

## Notes

- Artifact streaming happens AFTER run completion (acceptable for v0.2)
- SSE connection closes after `run_completed` - this is expected
- Debug logging can be disabled by setting `DEBUG = false` in each file
