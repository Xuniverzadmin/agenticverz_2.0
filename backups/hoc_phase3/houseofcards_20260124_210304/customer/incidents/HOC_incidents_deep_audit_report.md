# HOC Incidents Domain Deep Audit Report

**Status:** AUDIT COMPLETE
**Date:** 2026-01-23
**Scope:** `houseofcards/customer/incidents/` ONLY
**Auditor:** Claude Opus 4.5

---

## Executive Summary

The incidents domain contains **10 identified duplications** and **1 pattern inconsistency**. The primary issue is systematic DTO duplication where facades redefine engine dataclasses with identical fields, then manually map between them.

**Total Issues:** 10
- DTO Duplications: 7
- Type Alias Duplications: 1
- Semantic Overlap: 1
- Pattern Inconsistency: 1

---

## Files Audited

### Facades (1 file)
| File | LOC | Classes | Dataclasses | Functions |
|------|-----|---------|-------------|-----------|
| `facades/incidents_facade.py` | 1104 | 1 | 20 | 1 |

### Engines (10 files)
| File | LOC | Classes | Dataclasses | Functions |
|------|-----|---------|-------------|-----------|
| `engines/incident_engine.py` | 1012 | 1 | 0 | 2 |
| `engines/incident_read_service.py` | 200 | 1 | 0 | 1 |
| `engines/incident_write_service.py` | 284 | 1 | 0 | 1 |
| `engines/incident_aggregator.py` | 613 | 1 | 2 | 1 |
| `engines/recovery_rule_engine.py` | 790 | 7 | 3 | 6 |
| `engines/postmortem_service.py` | 486 | 1 | 4 | 0 |
| `engines/llm_failure_service.py` | 374 | 1 | 2 | 0 |
| `engines/recurrence_analysis_service.py` | 218 | 1 | 2 | 0 |
| `engines/recovery_evaluation_engine.py` | 404 | 1 | 2 | 2 |
| `engines/incident_pattern_service.py` | 278 | 1 | 2 | 0 |

**Total:** 11 files, ~5,763 LOC

---

## Duplication Issues

### INC-DUP-001: RecurrenceGroup Duplication

**Severity:** HIGH
**Type:** DTO Field Duplication (100%)

| Engine | Facade |
|--------|--------|
| `RecurrenceGroup` | `RecurrenceGroupResult` |
| `engines/recurrence_analysis_service.py:34` | `facades/incidents_facade.py:165` |

**Identical Fields:**
```python
category: str
resolution_method: Optional[str]
total_occurrences: int
distinct_days: int
occurrences_per_day: float
first_occurrence: datetime
last_occurrence: datetime
recent_incident_ids: list[str]
```

**Violation:** Facade redefines engine state DTO (violates Engine Ownership Rule).

**Fix:** Delete `RecurrenceGroupResult` from facade, import `RecurrenceGroup` from engine.

---

### INC-DUP-002: RecurrenceResult Duplication

**Severity:** HIGH
**Type:** DTO Field Duplication (100%)

| Engine | Facade |
|--------|--------|
| `RecurrenceResult` | `RecurrenceAnalysisResult` |
| `engines/recurrence_analysis_service.py:47` | `facades/incidents_facade.py:179` |

**Identical Fields:**
```python
groups: list[RecurrenceGroup]  # or RecurrenceGroupResult
baseline_days: int
total_recurring: int
generated_at: datetime
```

**Violation:** Facade redefines engine state DTO.

**Fix:** Delete `RecurrenceAnalysisResult` from facade, import `RecurrenceResult` from engine.

---

### INC-DUP-003: PatternMatch Duplication

**Severity:** HIGH
**Type:** DTO Field Duplication (100%)

| Engine | Facade |
|--------|--------|
| `PatternMatch` | `PatternMatchResult` |
| `engines/incident_pattern_service.py` | `facades/incidents_facade.py:138` |

**Identical Fields:**
```python
pattern_type: str
dimension: str
count: int
incident_ids: list[str]
confidence: float
```

**Violation:** Facade redefines engine state DTO.

**Fix:** Delete `PatternMatchResult` from facade, import `PatternMatch` from engine.

---

### INC-DUP-004: PatternResult Duplication

**Severity:** MEDIUM
**Type:** DTO Field Duplication (90%)

| Engine | Facade |
|--------|--------|
| `PatternResult` | `PatternDetectionResult` |
| `engines/incident_pattern_service.py` | `facades/incidents_facade.py:149` |

**Engine Fields:**
```python
patterns: list[PatternMatch]
incidents_analyzed: int
window_start: datetime
window_end: datetime
```

**Facade Fields (adds one):**
```python
patterns: list[PatternMatchResult]
window_hours: int              # ADDED
window_start: datetime
window_end: datetime
incidents_analyzed: int
```

**Recommendation:** Facade may extend engine DTO to add `window_hours`, or engine should include it.

---

### INC-DUP-005: ResolutionSummary Duplication

**Severity:** HIGH
**Type:** DTO Field Duplication (100%)

| Engine | Facade |
|--------|--------|
| `ResolutionSummary` | `ResolutionSummaryResult` |
| `engines/postmortem_service.py` | `facades/incidents_facade.py:328` |

**Identical Fields:**
```python
incident_id: str
title: str
category: Optional[str]
severity: str
resolution_method: Optional[str]
time_to_resolution_ms: Optional[int]
evidence_count: int
recovery_attempted: bool
```

**Violation:** Facade redefines engine state DTO.

**Fix:** Delete `ResolutionSummaryResult` from facade, import `ResolutionSummary` from engine.

---

### INC-DUP-006: LearningInsight Duplication

**Severity:** HIGH
**Type:** DTO Field Duplication (100%)

| Engine | Facade |
|--------|--------|
| `LearningInsight` | `LearningInsightResult` |
| `engines/postmortem_service.py` | `facades/incidents_facade.py:318` |

**Identical Fields:**
```python
insight_type: str
description: str
confidence: float
supporting_incident_ids: list[str]
```

**Violation:** Facade redefines engine state DTO.

**Fix:** Delete `LearningInsightResult` from facade, import `LearningInsight` from engine.

---

### INC-DUP-007: PostMortemResult / LearningsResult Duplication

**Severity:** HIGH
**Type:** DTO Field Duplication (100%)

| Engine | Facade |
|--------|--------|
| `PostMortemResult` | `LearningsResult` |
| `engines/postmortem_service.py` | `facades/incidents_facade.py:342` |

**Identical Fields:**
```python
incident_id: str
resolution_summary: ResolutionSummary  # or ResolutionSummaryResult
similar_incidents: list[ResolutionSummary]
insights: list[LearningInsight]
generated_at: datetime
```

**Violation:** Facade redefines engine state DTO with different name.

**Fix:** Delete `LearningsResult` from facade, import `PostMortemResult` from engine.

---

### INC-DUP-008: Type Alias Duplication

**Severity:** LOW
**Type:** Type Alias Duplication (100%)

| File 1 | File 2 |
|--------|--------|
| `engines/incident_aggregator.py:25-26` | `engines/llm_failure_service.py:32-33` |

**Duplicated Aliases:**
```python
UuidFn = Callable[[], str]
ClockFn = Callable[[], datetime]
```

**Recommendation:** Extract to shared `engines/incidents_types.py` or canonical location.

---

### INC-DUP-009: RuleContext / FailureContext Semantic Overlap

**Severity:** MEDIUM
**Type:** Semantic Overlap (Partial)

| File 1 | File 2 |
|--------|--------|
| `engines/recovery_rule_engine.py` | `engines/recovery_evaluation_engine.py` |
| `RuleContext` | `FailureContext` |

**RuleContext Fields:**
```python
error_code: str
error_message: Optional[str]
skill_id: Optional[str]
occurrence_count: int
historical_success_rate: Optional[float]
time_since_last_failure: Optional[int]
metadata: dict[str, Any]
```

**FailureContext Fields:**
```python
run_id: str
tenant_id: str
error_code: str
error_message: Optional[str]
# ... (need to verify full structure)
```

**Analysis:** Both represent failure context but for different purposes:
- `RuleContext` is for rule evaluation
- `FailureContext` is for recovery decision making

**Recommendation:** Review if these can share a base class or if separation is intentional.

---

## Pattern Inconsistencies

### INC-PATTERN-001: Factory Naming Inconsistency

**Severity:** LOW
**Type:** Naming Convention

| Factory | Pattern | File |
|---------|---------|------|
| `get_incidents_facade()` | `get_*` singleton | `facades/incidents_facade.py:1062` |
| `get_incident_engine()` | `get_*` singleton | `engines/incident_engine.py:1006` |
| `get_incident_read_service(session)` | `get_*` factory with DI | `engines/incident_read_service.py` |
| `get_incident_write_service(session)` | `get_*` factory with DI | `engines/incident_write_service.py` |
| `create_incident_aggregator()` | `create_*` factory | `engines/incident_aggregator.py` |

**Issue:** Mixed use of `get_*` and `create_*` prefixes.

**Recommendation:** Standardize on:
- `get_*` for singletons (no parameters)
- `create_*` for factories (take parameters)

---

## Artifact Catalog

### Dataclasses by File

**facades/incidents_facade.py (20 dataclasses):**
- `IncidentSummaryResult`
- `PaginationResult`
- `IncidentListResult`
- `IncidentDetailResult`
- `IncidentsByRunResult`
- `PatternMatchResult` ⚠️ DUP
- `PatternDetectionResult` ⚠️ DUP
- `RecurrenceGroupResult` ⚠️ DUP
- `RecurrenceAnalysisResult` ⚠️ DUP
- `CostImpactSummaryResult`
- `CostImpactResult`
- `IncidentMetricsResult`
- `HistoricalTrendDataPointResult`
- `HistoricalTrendResult`
- `HistoricalDistributionEntryResult`
- `HistoricalDistributionResult`
- `CostTrendDataPointResult`
- `CostTrendResult`
- `LearningInsightResult` ⚠️ DUP
- `ResolutionSummaryResult` ⚠️ DUP
- `LearningsResult` ⚠️ DUP

**engines/incident_aggregator.py (2 dataclasses):**
- `IncidentAggregatorConfig`
- `IncidentKey`

**engines/recovery_rule_engine.py (3 dataclasses):**
- `RuleContext`
- `RuleResult`
- `EvaluationResult`

**engines/postmortem_service.py (4 dataclasses):**
- `ResolutionSummary` → duplicated in facade
- `LearningInsight` → duplicated in facade
- `PostMortemResult` → duplicated in facade
- `CategoryLearnings`

**engines/llm_failure_service.py (2 dataclasses):**
- `LLMFailureFact`
- `LLMFailureResult`

**engines/recurrence_analysis_service.py (2 dataclasses):**
- `RecurrenceGroup` → duplicated in facade
- `RecurrenceResult` → duplicated in facade

**engines/recovery_evaluation_engine.py (2 dataclasses):**
- `FailureContext`
- `RecoveryDecision`

**engines/incident_pattern_service.py (2 dataclasses):**
- `PatternMatch` → duplicated in facade
- `PatternResult` → duplicated in facade

---

### Classes by File

| File | Class |
|------|-------|
| `facades/incidents_facade.py` | `IncidentsFacade` |
| `engines/incident_engine.py` | `IncidentEngine` |
| `engines/incident_read_service.py` | `IncidentReadService` |
| `engines/incident_write_service.py` | `IncidentWriteService` |
| `engines/incident_aggregator.py` | `IncidentAggregator` |
| `engines/recovery_rule_engine.py` | `Rule`, `ErrorCodeRule`, `HistoricalPatternRule`, `SkillSpecificRule`, `OccurrenceThresholdRule`, `CompositeRule`, `RecoveryRuleEngine` |
| `engines/postmortem_service.py` | `PostMortemService` |
| `engines/llm_failure_service.py` | `LLMFailureService` |
| `engines/recurrence_analysis_service.py` | `RecurrenceAnalysisService` |
| `engines/recovery_evaluation_engine.py` | `RecoveryEvaluationEngine` |
| `engines/incident_pattern_service.py` | `IncidentPatternService` |

---

### Factory Functions

| Function | Type | File |
|----------|------|------|
| `get_incidents_facade()` | Singleton | `facades/incidents_facade.py:1062` |
| `get_incident_engine()` | Singleton | `engines/incident_engine.py:1006` |
| `get_incident_read_service(session)` | Factory | `engines/incident_read_service.py` |
| `get_incident_write_service(session)` | Factory | `engines/incident_write_service.py` |
| `create_incident_aggregator()` | Factory | `engines/incident_aggregator.py` |

---

### Type Aliases

| Alias | Definition | Files |
|-------|------------|-------|
| `UuidFn` | `Callable[[], str]` | `incident_aggregator.py`, `llm_failure_service.py` |
| `ClockFn` | `Callable[[], datetime]` | `incident_aggregator.py`, `llm_failure_service.py` |

---

## Recommended Fixes (Priority Order)

### Priority 1: High-Severity DTO Duplications

1. **INC-DUP-001 to INC-DUP-003, INC-DUP-005 to INC-DUP-007**
   - Delete facade dataclasses with 100% field overlap
   - Import engine dataclasses directly
   - Estimated impact: 7 dataclasses removed from facade

### Priority 2: Medium-Severity Issues

2. **INC-DUP-004: PatternDetectionResult**
   - Option A: Add `window_hours` to engine's `PatternResult`
   - Option B: Keep facade extension but use inheritance

3. **INC-DUP-009: RuleContext/FailureContext**
   - Analyze if shared base class is appropriate
   - May be intentional separation

### Priority 3: Low-Severity Issues

4. **INC-DUP-008: Type Alias Duplication**
   - Create `engines/incidents_types.py` for shared types

5. **INC-PATTERN-001: Factory Naming**
   - Standardize naming convention across domain

---

## Rules to Enforce

Based on this audit, the following rules should be documented:

### 1. Engine Ownership Rule

> **Engines own canonical state DTOs. Facades only compose or extend. No facade may redefine engine state.**

### 2. No Manual DTO Mapping

> **If a facade method maps an engine DTO to a facade DTO with identical fields, delete the facade DTO and use the engine DTO directly.**

### 3. Type Alias Locality

> **Type aliases used by multiple engines should be defined in a shared types file, not duplicated.**

---

## Appendix: Duplication Summary Table

| Issue ID | Severity | Engine Type | Facade Type | Overlap |
|----------|----------|-------------|-------------|---------|
| INC-DUP-001 | HIGH | `RecurrenceGroup` | `RecurrenceGroupResult` | 100% |
| INC-DUP-002 | HIGH | `RecurrenceResult` | `RecurrenceAnalysisResult` | 100% |
| INC-DUP-003 | HIGH | `PatternMatch` | `PatternMatchResult` | 100% |
| INC-DUP-004 | MEDIUM | `PatternResult` | `PatternDetectionResult` | 90% |
| INC-DUP-005 | HIGH | `ResolutionSummary` | `ResolutionSummaryResult` | 100% |
| INC-DUP-006 | HIGH | `LearningInsight` | `LearningInsightResult` | 100% |
| INC-DUP-007 | HIGH | `PostMortemResult` | `LearningsResult` | 100% |
| INC-DUP-008 | LOW | `UuidFn`/`ClockFn` | `UuidFn`/`ClockFn` | 100% |
| INC-DUP-009 | MEDIUM | `RuleContext` | `FailureContext` | Partial |

---

## Quarantine Status (2026-01-23)

**Strategy:** Quarantine duplicates without deletion to preserve audit history.

### Infrastructure Created

| Path | Purpose |
|------|---------|
| `houseofcards/duplicate/README.md` | Governance document |
| `houseofcards/duplicate/__init__.py` | Import ban marker |
| `houseofcards/duplicate/incidents/__init__.py` | Domain quarantine root |
| `houseofcards/duplicate/activity/__init__.py` | Domain quarantine root |

### Quarantined Files (INC-DUP-001 to INC-DUP-007)

| Issue ID | Quarantine File | Canonical Source |
|----------|-----------------|------------------|
| INC-DUP-001 | `duplicate/incidents/recurrence_group_result.py` | `engines/recurrence_analysis_service.py:RecurrenceGroup` |
| INC-DUP-002 | `duplicate/incidents/recurrence_analysis_result.py` | `engines/recurrence_analysis_service.py:RecurrenceResult` |
| INC-DUP-003 | `duplicate/incidents/pattern_match_result.py` | `engines/incident_pattern_service.py:PatternMatch` |
| INC-DUP-004 | `duplicate/incidents/pattern_detection_result.py` | `engines/incident_pattern_service.py:PatternResult` |
| INC-DUP-005 | `duplicate/incidents/resolution_summary_result.py` | `engines/postmortem_service.py:ResolutionSummary` |
| INC-DUP-006 | `duplicate/incidents/learning_insight_result.py` | `engines/postmortem_service.py:LearningInsight` |
| INC-DUP-007 | `duplicate/incidents/learnings_result.py` | `engines/postmortem_service.py:PostMortemResult` |

### Type Alias Consolidation (INC-DUP-008)

**Created:** `engines/incidents_types.py`

Contains canonical definitions for:
- `UuidFn = Callable[[], str]`
- `ClockFn = Callable[[], datetime]`

### Remaining Items (Documented Only)

| Issue ID | Status | Reason |
|----------|--------|--------|
| INC-DUP-009 | DOCUMENTED | Semantic overlap — pending design decision |
| INC-PATTERN-001 | DOCUMENTED | Style issue — no code change required |

### Next Steps

1. **Import Migration:** Update facade to import from quarantine canonical sources
2. **CI Enforcement:** Add grep-based import ban check
3. **Removal Gate:** Delete quarantine files after import cleanup verified

---

## Execution Report (2026-01-23)

### Phase 1: Infrastructure

| File Created | Purpose |
|--------------|---------|
| `houseofcards/duplicate/README.md` | Governance: import ban, header contract, removal policy |
| `houseofcards/duplicate/__init__.py` | Root quarantine marker |
| `houseofcards/duplicate/incidents/__init__.py` | Incidents domain quarantine |
| `houseofcards/duplicate/activity/__init__.py` | Activity domain quarantine (prepared) |

---

### Phase 2: Quarantined DTOs

| Issue | File | Canonical |
|-------|------|-----------|
| INC-DUP-001 | `recurrence_group_result.py` | `RecurrenceGroup` |
| INC-DUP-002 | `recurrence_analysis_result.py` | `RecurrenceResult` |
| INC-DUP-003 | `pattern_match_result.py` | `PatternMatch` |
| INC-DUP-004 | `pattern_detection_result.py` | `PatternResult` |
| INC-DUP-005 | `resolution_summary_result.py` | `ResolutionSummary` |
| INC-DUP-006 | `learning_insight_result.py` | `LearningInsight` |
| INC-DUP-007 | `learnings_result.py` | `PostMortemResult` |

Each file has full header contract with:
- Canonical source reference
- Issue ID
- FROZEN status
- Removal policy

---

### Phase 3: Type Alias Consolidation

**Created:** `engines/incidents_types.py`

```python
UuidFn = Callable[[], str]
ClockFn = Callable[[], datetime]
```

---

### Phase 4: Documented Only (No Code Change)

| Issue | Status | Reason |
|-------|--------|--------|
| INC-DUP-009 | DOCUMENTED | `RuleContext` vs `FailureContext` — design decision pending |
| INC-PATTERN-001 | DOCUMENTED | Factory naming — style only |

---

### Files Created (12 total)

```
houseofcards/duplicate/
├── README.md
├── __init__.py
├── activity/
│   └── __init__.py
└── incidents/
    ├── __init__.py
    ├── recurrence_group_result.py
    ├── recurrence_analysis_result.py
    ├── pattern_match_result.py
    ├── pattern_detection_result.py
    ├── resolution_summary_result.py
    ├── learning_insight_result.py
    └── learnings_result.py

houseofcards/customer/incidents/engines/
└── incidents_types.py
```

---

### Pending Manual Steps

1. **Import Migration:** Replace facade DTOs with imports from canonical engines
2. **CI Check:** Add `grep -rn "houseofcards.duplicate" app/` to CI
3. **Removal Gate:** After verified, delete quarantine files

---

*This audit applies the same discipline as the Activity domain audit (ACTIVITY_DTO_RULES.md).
The same patterns of facade DTO duplication were found and should be resolved using the same approach.*
