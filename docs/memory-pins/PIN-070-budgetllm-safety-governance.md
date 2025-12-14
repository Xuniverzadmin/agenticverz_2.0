# PIN-070: BudgetLLM Safety Governance Layer

**Date:** 2025-12-14
**Status:** COMPLETE
**Version:** 0.2.0
**Category:** Feature / Safety

---

## Executive Summary

BudgetLLM now includes a **Safety Governance Layer** that transforms it from a cost-control tool into a full "LLM Governor" controlling:
- **Cost** (budget limits, caching)
- **Quality** (parameter clamping, determinism scoring)
- **Safety** (hallucination risk scoring, enforcement)

**Tagline:** "Your agent stops before you overspend — and before it goes off the rails."

**Differentiator:** No other SDK actively *prevents* hallucinations. Helicone/LangSmith observe. BudgetLLM governs.

---

## What Was Built

### New Modules

| Module | Purpose | Lines |
|--------|---------|-------|
| `core/safety.py` | SafetyController class, HighRiskOutputError | ~180 |
| `core/prompt_classifier.py` | Classify prompts into 7 types | ~175 |
| `core/output_analysis.py` | Analyze output for risk signals | ~160 |
| `core/risk_formula.py` | Weighted risk scoring formula | ~170 |
| `tests/test_safety_governance.py` | 32 comprehensive tests | ~510 |

### Updated Modules

| Module | Changes |
|--------|---------|
| `core/client.py` | Safety integration, new params, risk scoring in response |
| `__init__.py` | Export SafetyController, HighRiskOutputError, version 0.2.0 |

---

## Technical Architecture

### Flow Diagram

```
Request → Classify Prompt → Clamp Parameters → Check Cache
                                                    ↓
                                              [Cache Hit?]
                                              /         \
                                           Yes           No
                                            ↓             ↓
                                    Return Cached    Check Budget
                                                          ↓
                                                    Call OpenAI
                                                          ↓
                                                  Analyze Output
                                                          ↓
                                                  Calculate Risk
                                                          ↓
                                                  Enforce Safety
                                                    /         \
                                              [Risk OK?]  [Risk High?]
                                                  ↓             ↓
                                            Record Cost   Raise Error
                                                  ↓
                                            Cache Response
                                                  ↓
                                            Return with risk_score
```

### Prompt Classification

7 prompt types with risk weighting:

| Type | Weight | Description |
|------|--------|-------------|
| `factual` | 1.2 | Facts, definitions, explanations (highest accuracy needed) |
| `coding` | 1.1 | Code generation, debugging |
| `analytical` | 1.0 | Comparison, evaluation |
| `instruction` | 0.9 | How-to, step-by-step |
| `general` | 0.85 | Unclassified |
| `opinion` | 0.7 | Subjective queries |
| `creative` | 0.3 | Stories, poems (lowest accuracy constraint) |

**Pattern Matching:** Uses weighted regex patterns to classify prompts.

### Output Analysis

4 risk signals extracted from LLM output:

| Signal | Detection Method | Weight |
|--------|------------------|--------|
| `unsupported_claims` | "Studies show" without citations | 0.35 |
| `self_contradiction` | Conflicting terms (always/never) | 0.35 |
| `hedging` | Uncertainty language density | 0.15 |
| `numeric_inconsistency` | Conflicting numbers | 0.15 |

### Risk Scoring Formula

```python
# Input risk (40% weight)
input_risk = (
    0.45 * temperature +
    0.15 * (1 - top_p) * temperature +
    0.25 * (max_tokens / 4096) +
    0.15 * model_quality_penalty
)

# Output risk (60% weight)
output_risk = (
    0.35 * unsupported_claims +
    0.35 * self_contradiction +
    0.15 * hedging +
    0.15 * numeric_inconsistency
)

# Final score
risk_score = prompt_weight * (0.4 * input_risk + 0.6 * output_risk)
```

### Model Quality Penalties

| Model | Penalty | Rationale |
|-------|---------|-----------|
| gpt-4o | 0.0 | Highest quality |
| gpt-4-turbo | 0.05 | High quality |
| gpt-4o-mini | 0.15 | Good but smaller |
| gpt-3.5-turbo | 0.25 | Lower quality |

---

## API Changes

### New Client Parameters

```python
Client(
    # Existing
    openai_key="sk-...",
    budget_cents=1000,
    daily_limit_cents=500,
    monthly_limit_cents=5000,
    cache_enabled=True,
    cache_ttl=3600,
    redis_url=None,
    auto_pause=True,

    # NEW - Safety Governance
    max_temperature=1.0,        # Clamp temperature (default: no clamping)
    max_top_p=1.0,              # Clamp top_p (default: no clamping)
    max_completion_tokens=4096, # Clamp max_tokens (default: no clamping)
    enforce_safety=False,       # Enable safety enforcement (default: off)
    block_on_high_risk=True,    # Block or warn on high risk
    risk_threshold=0.6,         # Risk score threshold for blocking
)
```

### New Response Fields

```python
response = client.chat("What is Python?")

# Existing fields
response["choices"][0]["message"]["content"]
response["usage"]["total_tokens"]
response["cost_cents"]
response["cache_hit"]

# NEW fields
response["risk_score"]       # 0.0 - 1.0
response["risk_factors"]     # Detailed breakdown
response["params_clamped"]   # What was auto-corrected
```

### Risk Factors Structure

```python
{
    "prompt_type": "factual",
    "prompt_weight": 1.2,
    "prompt_confidence": 0.85,
    "input_risk": 0.234,
    "input_breakdown": {
        "temperature": 0.135,
        "top_p": 0.0,
        "max_tokens": 0.061,
        "model_quality": 0.023
    },
    "output_risk": 0.089,
    "output_breakdown": {
        "unsupported_claims": 0.0,
        "hedging": 0.045,
        "self_contradiction": 0.0,
        "numeric_inconsistency": 0.0
    },
    "determinism_score": 0.72,
    "model": "gpt-4o-mini",
    "model_penalty": 0.15
}
```

### New Exceptions

```python
from budgetllm import HighRiskOutputError

try:
    response = client.chat("Give me facts about X")
except HighRiskOutputError as e:
    print(e.risk_score)    # 0.72
    print(e.risk_factors)  # Full breakdown
```

---

## Usage Examples

### Basic Risk Scoring (No Enforcement)

```python
from budgetllm import Client

client = Client(
    openai_key="sk-...",
    budget_cents=1000,
)

response = client.chat("What is machine learning?")

print(f"Risk: {response['risk_score']}")  # e.g., 0.18
print(f"Type: {response['risk_factors']['prompt_type']}")  # "factual"
```

### Parameter Clamping

```python
client = Client(
    openai_key="sk-...",
    budget_cents=1000,
    max_temperature=0.5,  # Clamp high temps
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
    temperature=1.0,  # Will be clamped to 0.5
)

print(response["params_clamped"])
# {"temperature": {"original": 1.0, "clamped_to": 0.5}}
```

### Safety Enforcement

```python
from budgetllm import Client, HighRiskOutputError

client = Client(
    openai_key="sk-...",
    budget_cents=1000,
    enforce_safety=True,
    risk_threshold=0.5,
)

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Give me exact statistics"}],
        temperature=1.0,
    )
except HighRiskOutputError as e:
    print(f"Blocked! Risk: {e.risk_score}")
    print(f"Factors: {e.risk_factors}")
```

### Agent with Safety Guard

```python
from budgetllm import Client, BudgetExceededError, HighRiskOutputError

client = Client(
    budget_cents=500,
    max_temperature=0.7,
    enforce_safety=True,
    risk_threshold=0.6,
)

def safe_agent_step(task: str) -> str:
    try:
        response = client.chat(task)
        return response["choices"][0]["message"]["content"]
    except BudgetExceededError:
        return "Agent stopped: budget exceeded"
    except HighRiskOutputError as e:
        return f"Agent paused: output too risky ({e.risk_score:.2f})"
```

---

## Test Coverage

### Test Summary

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_budgetllm.py` | 24 | PASS |
| `test_openai_compat.py` | 15 | PASS |
| `test_safety_governance.py` | 32 | PASS |
| **Total** | **71** | **PASS** |

### Safety Governance Tests

| Category | Tests |
|----------|-------|
| Prompt Classifier | 6 |
| Output Analysis | 5 |
| Risk Formula | 5 |
| SafetyController | 7 |
| Client Integration | 6 |
| Edge Cases | 3 |

---

## Design Decisions

### 1. Safety Off by Default

**Decision:** `enforce_safety=False` by default

**Rationale:**
- Don't break existing users
- Safety is opt-in, not forced
- Risk scoring still works (observability without enforcement)

### 2. Heuristic-Based Scoring

**Decision:** Use heuristics, not ML models

**Rationale:**
- Zero latency overhead
- No additional API calls
- Works offline
- Transparent and debuggable

### 3. Output Risk Weighted Higher (60%)

**Decision:** Output analysis weighted 60% vs input 40%

**Rationale:**
- Actual content is more indicative than parameters
- High temperature doesn't always mean bad output
- Enables post-hoc risk assessment

### 4. No Auto-Correction (Yet)

**Decision:** Clamp inputs only, don't modify outputs

**Rationale:**
- Modifying LLM output is ethically complex
- Users should see original response
- Future feature with explicit opt-in

---

## Limitations

### Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Heuristics aren't perfect | False positives/negatives possible | Call it "estimated" risk |
| English-centric patterns | Non-English prompts less accurate | Add i18n patterns later |
| No semantic understanding | Can miss subtle hallucinations | Future: add verification API |
| Citation detection is simple | May miss complex citations | Improve regex patterns |

### What This Is NOT

- **Not ground truth:** Risk score is heuristic, not definitive
- **Not content moderation:** Doesn't detect harmful content
- **Not fact-checking:** Doesn't verify claims against sources
- **Not ML-based:** No model inference, just pattern matching

---

## Future Enhancements

### Phase 2 (If Validated)

| Feature | Description |
|---------|-------------|
| Auto-stabilization | Retry with lower temperature on high risk |
| Model routing | Route factual queries to GPT-4o |
| Fact verification | Call search API to verify claims |
| Custom patterns | User-defined risk patterns |

### Dashboard Integration

| Metric | Display |
|--------|---------|
| Avg risk score | Line chart over time |
| Risk distribution | Histogram |
| Clamping frequency | Counter |
| Blocks triggered | Alert log |

---

## File Structure

```
budgetllm/
├── __init__.py                    # v0.2.0, exports SafetyController
├── core/
│   ├── client.py                  # Safety integration (371→547 lines)
│   ├── budget.py                  # Unchanged
│   ├── cache.py                   # Unchanged
│   ├── safety.py                  # NEW: SafetyController
│   ├── prompt_classifier.py       # NEW: Prompt classification
│   ├── output_analysis.py         # NEW: Output risk signals
│   ├── risk_formula.py            # NEW: Risk scoring
│   └── backends/
│       ├── memory.py              # Unchanged
│       └── redis.py               # Unchanged
└── tests/
    ├── test_budgetllm.py          # 24 tests
    ├── test_openai_compat.py      # 15 tests
    └── test_safety_governance.py  # NEW: 32 tests
```

---

## Related PINs

- **PIN-069:** BudgetLLM Go-To-Market Plan (Phase 0 complete)
- **PIN-068:** M13 Prompt Caching Implementation
- **PIN-067:** M13 Iterations Cost Calculator Fix

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2025-12-14 | Claude | Initial implementation: SafetyController, prompt classifier, output analysis, risk formula |
| 2025-12-14 | Claude | 71 tests passing, version bump to 0.2.0 |

---

## Conclusion

BudgetLLM now offers a unique value proposition:

> **"The first LLM SDK that actively governs cost, quality, and safety."**

This positions BudgetLLM in its own category, beyond observability tools like Helicone/LangSmith.

**Next Steps:**
1. Publish to PyPI (v0.2.0)
2. Update README with safety governance docs
3. Get beta user feedback on risk scoring utility
4. Iterate based on real-world usage patterns
