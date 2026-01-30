# hoc_models_lessons_learned

| Field | Value |
|-------|-------|
| Path | `backend/app/models/lessons_learned.py` |
| Layer | L6 — Platform Substrate (Data Models) |
| Domain | shared |
| Audience | SHARED |
| Artifact Class | CODE |

## Description

Lessons learned data model for policy domain intelligence

## Intent

**Role:** Lessons learned data model for policy domain intelligence
**Reference:** PIN-411, POLICIES_DOMAIN_AUDIT.md Section 11
**Callers:** LessonsLearnedEngine (L4), API facades (L2)

## Purpose

Lessons Learned Model (L6)

---

## Classes

### `LessonType(str, Enum)`
- **Docstring:** Type of lesson learned.

### `LessonStatus(str, Enum)`
- **Docstring:** Status of a lesson.

### `LessonSeverity(str, Enum)`
- **Docstring:** Severity of the originating event.

### `LessonLearned(SQLModel)`
- **Docstring:** Lesson learned from system events.
- **Class Variables:** id: UUID, tenant_id: str, lesson_type: str, severity: Optional[str], source_event_id: UUID, source_event_type: str, source_run_id: Optional[UUID], title: str, description: str, proposed_action: Optional[str], detected_pattern: Optional[dict[str, Any]], status: str, draft_proposal_id: Optional[UUID], created_at: datetime, converted_at: Optional[datetime], deferred_until: Optional[datetime], dismissed_at: Optional[datetime], dismissed_by: Optional[str], dismissed_reason: Optional[str], is_synthetic: bool, synthetic_scenario_id: Optional[str]

### `LessonSummary(SQLModel)`
- **Docstring:** Summary view of a lesson (O2 result shape).
- **Class Variables:** id: UUID, tenant_id: str, lesson_type: str, severity: Optional[str], title: str, status: str, source_event_type: str, created_at: datetime, has_proposed_action: bool

### `LessonDetail(SQLModel)`
- **Docstring:** Detailed view of a lesson (O3 result shape).
- **Class Variables:** id: UUID, tenant_id: str, lesson_type: str, severity: Optional[str], source_event_id: UUID, source_event_type: str, source_run_id: Optional[UUID], title: str, description: str, proposed_action: Optional[str], detected_pattern: Optional[dict[str, Any]], status: str, draft_proposal_id: Optional[UUID], created_at: datetime, converted_at: Optional[datetime], deferred_until: Optional[datetime], dismissed_at: Optional[datetime], dismissed_by: Optional[str], dismissed_reason: Optional[str]

---

## Import Analysis

| Category | Imports |
|----------|---------|
| External | `sqlalchemy`, `sqlalchemy.dialects.postgresql`, `sqlmodel` |

## Callers

LessonsLearnedEngine (L4), API facades (L2)

## Export Contract

```yaml
exports:
  functions: []
  classes:
    - name: LessonType
      methods: []
    - name: LessonStatus
      methods: []
    - name: LessonSeverity
      methods: []
    - name: LessonLearned
      methods: []
    - name: LessonSummary
      methods: []
    - name: LessonDetail
      methods: []
```

## Evaluation Notes

- **Disposition:** KEEP / MODIFY / QUARANTINE / DEPRECATED
- **Rationale:** ---
