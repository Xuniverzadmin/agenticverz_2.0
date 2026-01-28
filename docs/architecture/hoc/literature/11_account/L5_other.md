# Account — L5 Other (2 files)

**Domain:** account  
**Layer:** L5_other  
**Reference:** HOC_LAYER_TOPOLOGY_V1.md (RATIFIED, V1.4.0)

---

## crm_validator_engine.py
**Path:** `backend/app/hoc/cus/account/L5_support/CRM/engines/crm_validator_engine.py`  
**Layer:** L5_other | **Domain:** account | **Lines:** 739

**Docstring:** Part-2 Validator Service (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IssueType` |  | Issue type classification. |
| `Severity` |  | Issue severity classification. |
| `RecommendedAction` |  | Recommended action from validator. |
| `IssueSource` |  | Issue source for confidence weighting. |
| `ValidatorInput` |  | Input to the validator. |
| `ValidatorVerdict` |  | Output from the validator. |
| `ValidatorErrorType` |  | Error types for validator failures. |
| `ValidatorError` |  | Error from validator with fallback verdict. |
| `ValidatorService` | __init__, validate, _do_validate, _extract_text, _classify_issue_type, _classify_severity, _find_severity_indicators, _extract_capabilities (+6 more) | Part-2 Validator Service (L4) |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `re` | re | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |

### Constants
`VALIDATOR_VERSION`, `CAPABILITY_REQUEST_KEYWORDS`, `BUG_REPORT_KEYWORDS`, `CONFIGURATION_KEYWORDS`, `ESCALATION_KEYWORDS`, `CRITICAL_INDICATORS`, `HIGH_INDICATORS`, `LOW_INDICATORS`

---

## validator_engine.py
**Path:** `backend/app/hoc/cus/account/L5_support/CRM/engines/validator_engine.py`  
**Layer:** L5_other | **Domain:** account | **Lines:** 735

**Docstring:** Part-2 Validator Service (L4)

### Classes
| Name | Methods | Docstring |
|------|---------|-----------|
| `IssueType` |  | Issue type classification. |
| `Severity` |  | Issue severity classification. |
| `RecommendedAction` |  | Recommended action from validator. |
| `IssueSource` |  | Issue source for confidence weighting. |
| `ValidatorInput` |  | Input to the validator. |
| `ValidatorVerdict` |  | Output from the validator. |
| `ValidatorErrorType` |  | Error types for validator failures. |
| `ValidatorError` |  | Error from validator with fallback verdict. |
| `ValidatorService` | __init__, validate, _do_validate, _extract_text, _classify_issue_type, _classify_severity, _find_severity_indicators, _extract_capabilities (+6 more) | Part-2 Validator Service (L4) |

### Imports
| Module | Names | Relative |
|--------|-------|----------|
| `re` | re | no |
| `dataclasses` | dataclass | no |
| `datetime` | datetime, timezone | no |
| `decimal` | Decimal | no |
| `enum` | Enum | no |
| `typing` | Any, Optional | no |
| `uuid` | UUID | no |

### Constants
`VALIDATOR_VERSION`, `CAPABILITY_REQUEST_KEYWORDS`, `BUG_REPORT_KEYWORDS`, `CONFIGURATION_KEYWORDS`, `ESCALATION_KEYWORDS`, `CRITICAL_INDICATORS`, `HIGH_INDICATORS`, `LOW_INDICATORS`

---
