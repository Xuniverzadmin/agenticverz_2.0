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
    AssertionCheck,
    ContentAccuracyResult,
    ContentAccuracyValidator,
    ValidationResult,
    validate_content_accuracy,
)

# M24 Prevention Engine (recommended)
from app.policy.validators.prevention_engine import (
    BaseValidator,
    BudgetValidator,
    ContentAccuracyValidatorV2,
    HallucinationValidator,
    PIIValidator,
    PolicyType,
    PolicyViolation,
    PreventionAction,
    PreventionContext,
    PreventionEngine,
    PreventionResult,
    SafetyValidator,
    Severity,
    create_incident_from_violation,
    evaluate_prevention,
    get_prevention_engine,
)
from app.policy.validators.prevention_hook import (
    PreventionAction as LegacyPreventionAction,
)
from app.policy.validators.prevention_hook import (
    PreventionContext as LegacyPreventionContext,
)
from app.policy.validators.prevention_hook import (
    PreventionHook,
    create_prevention_hook,
    evaluate_response,
    get_prevention_hook,
)
from app.policy.validators.prevention_hook import (
    PreventionResult as LegacyPreventionResult,
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
