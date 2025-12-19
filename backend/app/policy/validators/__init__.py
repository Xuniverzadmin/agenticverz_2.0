# M23/M24 Policy Validators
# Content accuracy and assertion validation for LLM outputs
#
# Prevention mechanisms for policy gaps:
# - CONTENT_ACCURACY: Prevents assertions about missing data
# - PII: Detects and blocks PII exposure
# - SAFETY: Detects harmful content
# - HALLUCINATION: Detects unsupported claims
# - BUDGET_LIMIT: Token/cost enforcement
# - Prevention hooks: Pre-response validation
# - Prevention engine: Multi-policy evaluation with severity levels

from app.policy.validators.content_accuracy import (
    ContentAccuracyValidator,
    ContentAccuracyResult,
    AssertionCheck,
    ValidationResult,
    validate_content_accuracy,
)

from app.policy.validators.prevention_hook import (
    PreventionHook,
    PreventionContext as LegacyPreventionContext,
    PreventionResult as LegacyPreventionResult,
    PreventionAction as LegacyPreventionAction,
    create_prevention_hook,
    get_prevention_hook,
    evaluate_response,
)

# M24 Prevention Engine (recommended)
from app.policy.validators.prevention_engine import (
    PolicyType,
    Severity,
    PreventionAction,
    PolicyViolation,
    PreventionContext,
    PreventionResult,
    BaseValidator,
    ContentAccuracyValidatorV2,
    PIIValidator,
    SafetyValidator,
    HallucinationValidator,
    BudgetValidator,
    PreventionEngine,
    get_prevention_engine,
    evaluate_prevention,
    create_incident_from_violation,
)

__all__ = [
    # Content Accuracy Validator (M23)
    "ContentAccuracyValidator",
    "ContentAccuracyResult",
    "AssertionCheck",
    "ValidationResult",
    "validate_content_accuracy",
    # Legacy Prevention Hook (M23)
    "PreventionHook",
    "LegacyPreventionContext",
    "LegacyPreventionResult",
    "LegacyPreventionAction",
    "create_prevention_hook",
    "get_prevention_hook",
    "evaluate_response",
    # Prevention Engine (M24 - recommended)
    "PolicyType",
    "Severity",
    "PreventionAction",
    "PolicyViolation",
    "PreventionContext",
    "PreventionResult",
    "BaseValidator",
    "ContentAccuracyValidatorV2",
    "PIIValidator",
    "SafetyValidator",
    "HallucinationValidator",
    "BudgetValidator",
    "PreventionEngine",
    "get_prevention_engine",
    "evaluate_prevention",
    "create_incident_from_violation",
]
