# Layer: L6 — Driver
# AUDIENCE: CUSTOMER
# Role: LLM service adapter for business builder
# Product: product-builder
# Temporal:
#   Trigger: worker
#   Execution: async
# Callers: business_builder stages
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2, L5
# Reference: Business Builder

# Worker LLM Service

"""
LLM Service for Business Builder Worker v0.3

Provides:
- Real LLM calls via Claude adapter
- Stage-specific prompt templates
- Token tracking for cost reporting
- Deterministic execution support

Usage:
    service = WorkerLLMService()
    result = await service.research(task, brand)
    result = await service.generate_copy(brand, research_output)
    result = await service.generate_ux(brand, copy_output)
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger("nova.workers.business_builder.llm")

# Check for API key
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
USE_STUB = not ANTHROPIC_API_KEY


@dataclass
class LLMResult:
    """Result from LLM call."""

    content: str
    input_tokens: int
    output_tokens: int
    model: str
    latency_ms: int
    success: bool
    error: Optional[str] = None


class WorkerLLMService:
    """
    LLM Service for Business Builder Worker.

    Uses Claude adapter for real LLM calls, with fallback to stub for testing.
    """

    def __init__(self, use_stub: bool = USE_STUB):
        self.use_stub = use_stub
        self._adapter = None
        self._total_tokens = 0

    def _get_adapter(self):
        """Get LLM adapter (lazy load)."""
        if self._adapter is None:
            if self.use_stub:
                from app.skills.llm_invoke_v2 import StubAdapter

                self._adapter = StubAdapter()
            else:
                from app.skills.adapters.claude_adapter import ClaudeAdapter

                self._adapter = ClaudeAdapter()
        return self._adapter

    async def _invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResult:
        """
        Invoke LLM with prompts.

        Args:
            system_prompt: System context
            user_prompt: User request
            max_tokens: Maximum output tokens
            temperature: Creativity (0=deterministic, 1=creative)

        Returns:
            LLMResult with content and metadata
        """
        from app.skills.llm_invoke_v2 import LLMConfig, Message

        adapter = self._get_adapter()

        config = LLMConfig(
            model=adapter.default_model,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
        )

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]

        try:
            result = await adapter.invoke(messages, config)

            if isinstance(result, tuple):
                # Error tuple
                error_type, message, _ = result
                return LLMResult(
                    content="",
                    input_tokens=0,
                    output_tokens=0,
                    model="",
                    latency_ms=0,
                    success=False,
                    error=f"{error_type}: {message}",
                )

            self._total_tokens += result.input_tokens + result.output_tokens

            return LLMResult(
                content=result.content,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                model=result.model,
                latency_ms=result.latency_ms,
                success=True,
            )

        except Exception as e:
            logger.exception("LLM invocation failed")
            return LLMResult(
                content="",
                input_tokens=0,
                output_tokens=0,
                model="",
                latency_ms=0,
                success=False,
                error=str(e),
            )

    @property
    def total_tokens(self) -> int:
        """Total tokens used across all calls."""
        return self._total_tokens

    # =========================================================================
    # Stage-Specific Methods
    # =========================================================================

    async def research(
        self,
        task: str,
        brand_name: str,
        target_audience: List[str],
        competitors_hint: Optional[List[str]] = None,
    ) -> LLMResult:
        """
        Generate market research report.

        Args:
            task: Business/product description
            brand_name: Company name
            target_audience: Target audience segments
            competitors_hint: Known competitors

        Returns:
            LLMResult with JSON market research report
        """
        system_prompt = """You are a market research analyst. Generate a comprehensive but concise market research report in JSON format.

Your output MUST be valid JSON with this structure:
{
    "summary": "2-3 sentence market overview",
    "market_size": "Small/Medium/Large with context",
    "growth_rate": "percentage or qualitative (e.g., 'High growth - 25% YoY')",
    "key_trends": ["trend1", "trend2", "trend3"],
    "competitors": [
        {
            "name": "Competitor Name",
            "positioning": "Their market position",
            "strengths": ["strength1", "strength2"],
            "weaknesses": ["weakness1"]
        }
    ],
    "opportunities": ["opportunity1", "opportunity2"],
    "threats": ["threat1", "threat2"],
    "recommendations": ["recommendation1", "recommendation2"]
}

Be specific, data-driven, and actionable. Do not include markdown formatting - just pure JSON."""

        competitors_str = ""
        if competitors_hint:
            competitors_str = f"\nKnown competitors to analyze: {', '.join(competitors_hint)}"

        user_prompt = f"""Generate a market research report for:

Business/Product: {task}
Company Name: {brand_name}
Target Audience: {", ".join(target_audience)}
{competitors_str}

Provide realistic market analysis based on the business type described."""

        return await self._invoke(system_prompt, user_prompt, max_tokens=2048, temperature=0.5)

    async def generate_strategy(
        self,
        task: str,
        brand_name: str,
        mission: str,
        value_proposition: str,
        tone_primary: str,
        research_summary: str,
    ) -> LLMResult:
        """
        Generate positioning and messaging strategy.

        Returns:
            LLMResult with JSON strategy framework
        """
        system_prompt = f"""You are a brand strategist. Create a positioning and messaging framework in JSON format.

Brand tone: {tone_primary}

Your output MUST be valid JSON with this structure:
{{
    "positioning_statement": "For [target], [brand] is the [category] that [key benefit] because [reason to believe]",
    "key_differentiators": ["diff1", "diff2", "diff3"],
    "messaging_framework": {{
        "headline": "Primary headline (max 10 words)",
        "subhead": "Supporting statement (max 25 words)",
        "cta": "Call to action (2-4 words)",
        "value_props": [
            {{"title": "Prop Title", "description": "Brief description"}},
            {{"title": "Prop Title", "description": "Brief description"}},
            {{"title": "Prop Title", "description": "Brief description"}}
        ]
    }},
    "tone_guidelines": {{
        "voice": "Description of brand voice",
        "dos": ["do1", "do2", "do3"],
        "donts": ["dont1", "dont2", "dont3"]
    }},
    "tagline_options": ["option1", "option2", "option3"]
}}

Be specific to the brand. Match the tone exactly. Do not include markdown - just pure JSON."""

        user_prompt = f"""Create a brand strategy for:

Business: {task}
Company: {brand_name}
Mission: {mission}
Value Proposition: {value_proposition}

Market Research Summary:
{research_summary[:1500]}"""

        return await self._invoke(system_prompt, user_prompt, max_tokens=2048, temperature=0.7)

    async def generate_copy(
        self,
        brand_name: str,
        tagline: Optional[str],
        value_proposition: str,
        tone_primary: str,
        messaging_framework: Dict[str, Any],
    ) -> LLMResult:
        """
        Generate landing page copy.

        Returns:
            LLMResult with JSON copy package
        """
        system_prompt = f"""You are an expert copywriter. Write compelling landing page copy in JSON format.

Brand tone: {tone_primary}
Brand tagline: {tagline or "None provided"}

Your output MUST be valid JSON with this structure:
{{
    "hero": {{
        "headline": "Attention-grabbing headline",
        "subhead": "Supporting statement that expands on the headline",
        "cta_text": "Button text",
        "cta_subtext": "Optional supporting text under button"
    }},
    "features": [
        {{
            "icon": "suggested icon name (e.g., 'zap', 'shield', 'clock')",
            "title": "Feature title",
            "description": "2-3 sentence feature description"
        }}
    ],
    "social_proof": {{
        "headline": "Social proof section headline",
        "testimonials": [
            {{
                "quote": "Customer testimonial",
                "author": "Name, Title at Company"
            }}
        ],
        "stats": [
            {{"value": "10K+", "label": "Stat label"}}
        ]
    }},
    "final_cta": {{
        "headline": "Closing headline",
        "subhead": "Final persuasive statement",
        "cta_text": "Button text"
    }}
}}

Write copy that matches the brand tone exactly. Be specific and compelling. No markdown - just JSON."""

        user_prompt = f"""Write landing page copy for:

Company: {brand_name}
Value Proposition: {value_proposition}

Messaging Framework:
{str(messaging_framework)[:1000]}

Generate compelling copy that converts visitors to customers."""

        return await self._invoke(system_prompt, user_prompt, max_tokens=2500, temperature=0.8)

    async def generate_ux_html(
        self,
        brand_name: str,
        primary_color: str,
        secondary_color: str,
        font_heading: str,
        font_body: str,
        copy_content: Dict[str, Any],
    ) -> LLMResult:
        """
        Generate complete HTML landing page.

        Returns:
            LLMResult with complete HTML page
        """
        system_prompt = f"""You are a frontend developer. Generate a complete, modern HTML landing page.

Brand colors:
- Primary: {primary_color}
- Secondary: {secondary_color}

Fonts:
- Headings: {font_heading}
- Body: {font_body}

Requirements:
1. Use inline CSS (no external stylesheets)
2. Mobile-responsive design
3. Modern, clean aesthetic
4. Include all sections from the copy content
5. Use Google Fonts link for custom fonts
6. Add smooth hover transitions
7. Include a sticky header

Output ONLY the complete HTML document starting with <!DOCTYPE html>. No explanations, no markdown code blocks - just the raw HTML."""

        user_prompt = f"""Generate a landing page for {brand_name} with this content:

{str(copy_content)[:2000]}

Create a visually stunning, conversion-optimized landing page. Use the exact copy provided."""

        return await self._invoke(system_prompt, user_prompt, max_tokens=4096, temperature=0.6)

    async def generate_ux_css(
        self,
        brand_name: str,
        primary_color: str,
        secondary_color: str,
        font_heading: str,
        font_body: str,
    ) -> LLMResult:
        """
        Generate standalone CSS stylesheet.

        Returns:
            LLMResult with CSS content
        """
        system_prompt = """You are a CSS expert. Generate a modern, responsive CSS stylesheet.

Requirements:
1. CSS variables for colors and fonts
2. Mobile-first responsive design
3. Smooth transitions and hover effects
4. Clean, maintainable code
5. Support for common landing page sections (header, hero, features, testimonials, CTA, footer)

Output ONLY the CSS code. No explanations, no markdown code blocks - just raw CSS."""

        user_prompt = f"""Generate a CSS stylesheet for {brand_name}:

Primary Color: {primary_color}
Secondary Color: {secondary_color}
Heading Font: {font_heading}
Body Font: {font_body}

Create professional, modern styles that work well for a landing page."""

        return await self._invoke(system_prompt, user_prompt, max_tokens=2048, temperature=0.5)


# Singleton instance
_llm_service: Optional[WorkerLLMService] = None


def get_llm_service() -> WorkerLLMService:
    """Get singleton LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = WorkerLLMService()
    return _llm_service
