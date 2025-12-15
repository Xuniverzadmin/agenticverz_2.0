# Brand Schema for Business Builder Worker
# Defines brand constraints that SBA agents must adhere to
"""
Brand schema that triggers:
- M15: Strategy binding (agents must follow brand rules)
- M18: Drift detection (outputs compared against brand embeddings)
- M19: Policy governance (forbidden claims enforcement)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class ToneLevel(str, Enum):
    """Brand tone levels."""
    CASUAL = "casual"
    NEUTRAL = "neutral"
    PROFESSIONAL = "professional"
    FORMAL = "formal"
    LUXURY = "luxury"


class AudienceSegment(str, Enum):
    """Target audience segments."""
    B2C_CONSUMER = "b2c_consumer"
    B2C_PROSUMER = "b2c_prosumer"
    B2B_SMB = "b2b_smb"
    B2B_ENTERPRISE = "b2b_enterprise"
    B2B_DEVELOPER = "b2b_developer"


class ToneRule(BaseModel):
    """Rule defining acceptable tone in copy."""
    primary: ToneLevel = Field(
        default=ToneLevel.PROFESSIONAL,
        description="Primary tone for all copy"
    )
    avoid: List[ToneLevel] = Field(
        default_factory=list,
        description="Tones to avoid"
    )
    examples_good: List[str] = Field(
        default_factory=list,
        description="Example phrases that match the tone"
    )
    examples_bad: List[str] = Field(
        default_factory=list,
        description="Example phrases to avoid"
    )


class ForbiddenClaim(BaseModel):
    """Claims that must not appear in any output."""
    pattern: str = Field(
        ...,
        description="Regex pattern or substring to detect"
    )
    reason: str = Field(
        default="Policy violation",
        description="Why this claim is forbidden"
    )
    severity: str = Field(
        default="error",
        description="error = block, warning = flag"
    )


class VisualIdentity(BaseModel):
    """Visual brand constraints."""
    primary_color: Optional[str] = Field(
        default=None,
        description="Primary brand color (hex)"
    )
    secondary_color: Optional[str] = Field(
        default=None,
        description="Secondary brand color (hex)"
    )
    font_heading: Optional[str] = Field(
        default="Inter",
        description="Heading font family"
    )
    font_body: Optional[str] = Field(
        default="Inter",
        description="Body font family"
    )
    logo_placement: Optional[str] = Field(
        default="top-left",
        description="Preferred logo placement"
    )


class CompetitorContext(BaseModel):
    """Competitor information for positioning."""
    name: str = Field(..., description="Competitor name")
    positioning: Optional[str] = Field(
        default=None,
        description="Their positioning statement"
    )
    differentiate_from: Optional[str] = Field(
        default=None,
        description="How we differ from them"
    )


class BrandSchema(BaseModel):
    """
    Complete brand schema for Business Builder Worker.

    This triggers multiple moats:
    - M15 SBA: Agents bound to brand rules
    - M18: Drift detection against brand embeddings
    - M19: Policy enforcement for forbidden claims
    - M9: Failure patterns for brand violations
    """

    # Core identity
    company_name: str = Field(
        ...,
        min_length=1,
        description="Company or product name"
    )
    tagline: Optional[str] = Field(
        default=None,
        description="Brand tagline"
    )
    mission: str = Field(
        ...,
        min_length=10,
        description="Mission statement"
    )
    vision: Optional[str] = Field(
        default=None,
        description="Vision statement"
    )
    value_proposition: str = Field(
        ...,
        min_length=20,
        description="Core value proposition"
    )

    # Audience
    target_audience: List[AudienceSegment] = Field(
        default_factory=lambda: [AudienceSegment.B2B_SMB],
        description="Target audience segments"
    )
    audience_pain_points: List[str] = Field(
        default_factory=list,
        description="Pain points to address"
    )

    # Tone & Voice
    tone: ToneRule = Field(
        default_factory=ToneRule,
        description="Tone rules for copy"
    )
    voice_attributes: List[str] = Field(
        default_factory=lambda: ["clear", "helpful", "confident"],
        description="Voice attributes (e.g., friendly, authoritative)"
    )

    # Constraints (M19 Policy triggers)
    forbidden_claims: List[ForbiddenClaim] = Field(
        default_factory=list,
        description="Claims that must never appear"
    )
    required_disclosures: List[str] = Field(
        default_factory=list,
        description="Required legal/compliance disclosures"
    )

    # Visual
    visual: VisualIdentity = Field(
        default_factory=VisualIdentity,
        description="Visual identity constraints"
    )

    # Competitors (for positioning)
    competitors: List[CompetitorContext] = Field(
        default_factory=list,
        description="Competitor context for differentiation"
    )

    # Budget constraint (M19 Policy trigger)
    budget_tokens: Optional[int] = Field(
        default=None,
        ge=1000,
        le=1000000,
        description="Maximum token budget for execution"
    )

    @field_validator('mission')
    @classmethod
    def validate_mission_not_empty(cls, v: str) -> str:
        """Ensure mission is substantive."""
        if len(v.split()) < 3:
            raise ValueError("Mission must be at least 3 words")
        return v

    @field_validator('value_proposition')
    @classmethod
    def validate_value_prop(cls, v: str) -> str:
        """Ensure value prop is substantive."""
        if len(v.split()) < 5:
            raise ValueError("Value proposition must be at least 5 words")
        return v

    def to_strategy_context(self) -> Dict[str, Any]:
        """
        Convert to SBA strategy context.

        This is used by M15 to bind agents to brand rules.
        """
        return {
            "brand_name": self.company_name,
            "mission": self.mission,
            "value_prop": self.value_proposition,
            "tone_primary": self.tone.primary.value,
            "tone_avoid": [t.value for t in self.tone.avoid],
            "voice": self.voice_attributes,
            "forbidden_patterns": [fc.pattern for fc in self.forbidden_claims],
            "audience": [a.value for a in self.target_audience],
            "budget_tokens": self.budget_tokens,
        }

    def to_policy_rules(self) -> List[Dict[str, Any]]:
        """
        Convert to M19 policy rules.

        Returns PLang-compatible policy definitions.
        """
        rules = []

        # Forbidden claims as DENY rules
        for fc in self.forbidden_claims:
            rules.append({
                "category": "SAFETY",
                "condition": f'contains(output, "{fc.pattern}")',
                "action": "deny" if fc.severity == "error" else "escalate",
                "reason": fc.reason,
            })

        # Budget enforcement
        if self.budget_tokens:
            rules.append({
                "category": "OPERATIONAL",
                "condition": f"cost.tokens > {self.budget_tokens}",
                "action": "deny",
                "reason": "Budget exceeded",
            })

        return rules

    def get_drift_anchors(self) -> List[str]:
        """
        Get text anchors for M18 drift detection.

        These are embedded and compared against outputs.
        """
        anchors = [
            self.mission,
            self.value_proposition,
        ]
        if self.tagline:
            anchors.append(self.tagline)
        anchors.extend(self.tone.examples_good)
        return anchors

    @classmethod
    def from_file(cls, path: str) -> "BrandSchema":
        """Load brand schema from JSON file."""
        import json
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.model_validate(data)

    def to_file(self, path: str) -> None:
        """Save brand schema to JSON file."""
        import json
        with open(path, 'w') as f:
            json.dump(self.model_dump(mode='json'), f, indent=2)


# Default forbidden claims for all brands
DEFAULT_FORBIDDEN_CLAIMS = [
    ForbiddenClaim(
        pattern="world's best",
        reason="Unverifiable superlative claim",
        severity="error"
    ),
    ForbiddenClaim(
        pattern="guaranteed results",
        reason="Cannot guarantee outcomes",
        severity="error"
    ),
    ForbiddenClaim(
        pattern="100% accurate",
        reason="Unverifiable accuracy claim",
        severity="error"
    ),
    ForbiddenClaim(
        pattern="risk-free",
        reason="All investments carry risk",
        severity="warning"
    ),
]


def create_minimal_brand(
    company_name: str,
    mission: str,
    value_proposition: str,
    tone: ToneLevel = ToneLevel.PROFESSIONAL,
) -> BrandSchema:
    """Create a minimal valid brand schema."""
    return BrandSchema(
        company_name=company_name,
        mission=mission,
        value_proposition=value_proposition,
        tone=ToneRule(primary=tone),
        forbidden_claims=DEFAULT_FORBIDDEN_CLAIMS,
    )
