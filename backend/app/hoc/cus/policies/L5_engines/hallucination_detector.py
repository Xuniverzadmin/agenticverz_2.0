# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: worker
#   Execution: async
# Role: Detect potential hallucinations in LLM outputs (non-blocking)
# Callers: worker/runner.py, services/incident_engine.py
# Allowed Imports: L6, L7
# Forbidden Imports: L1, L2, L3, L4, sqlalchemy, sqlmodel
# Reference: GAP-023, INV-002 (HALLU-INV-001)
# NOTE: Reclassified L6→L5 (2026-01-24) - no Session imports, pure detection logic

"""
Module: hallucination_detector
Purpose: Detect potential hallucinations in LLM outputs.

CRITICAL INVARIANT (INV-002 / HALLU-INV-001):
    Hallucination detection is ALWAYS non-blocking by default.
    This is because:
    - Hallucination detection is PROBABILISTIC (60-90% confidence)
    - Policy violations (cost, rate, PII) are DETERMINISTIC (facts)
    - False positives on hallucination blocking destroy customer trust
    - Blocking requires explicit customer opt-in

Imports (Dependencies):
    - dataclasses: Detection result structures
    - hashlib: Content hashing for evidence

Exports (Provides):
    - HallucinationDetector: Main detection service
    - HallucinationResult: Detection result dataclass
    - HallucinationIndicator: Individual indicator dataclass
    - HallucinationType: Type of hallucination detected

Wiring Points:
    - Called from: worker/runner.py after step completion
    - Calls: incident_engine.create_incident() with blocking=False
"""

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class HallucinationType(str, Enum):
    """Types of hallucination indicators."""

    # Factual hallucinations
    FABRICATED_CITATION = "fabricated_citation"
    INVALID_URL = "invalid_url"
    NONEXISTENT_ENTITY = "nonexistent_entity"
    TEMPORAL_IMPOSSIBILITY = "temporal_impossibility"

    # Logical hallucinations
    SELF_CONTRADICTION = "self_contradiction"
    LOGICAL_INCONSISTENCY = "logical_inconsistency"

    # Instruction hallucinations
    INSTRUCTION_FABRICATION = "instruction_fabrication"
    CAPABILITY_OVERCLAIM = "capability_overclaim"

    # Generic
    CONFIDENCE_MISMATCH = "confidence_mismatch"
    UNKNOWN = "unknown"


class HallucinationSeverity(str, Enum):
    """Severity levels for hallucination detections."""

    LOW = "low"  # Minor inconsistency, likely noise
    MEDIUM = "medium"  # Moderate concern, worth flagging
    HIGH = "high"  # Significant hallucination detected
    CRITICAL = "critical"  # Clear fabrication, customer opt-in can block


@dataclass
class HallucinationIndicator:
    """
    Individual hallucination indicator.

    Represents a single piece of evidence suggesting hallucination.
    Multiple indicators combine to form overall confidence.
    """

    indicator_type: HallucinationType
    description: str
    confidence: float  # 0.0 to 1.0
    evidence: str  # The problematic text
    severity: HallucinationSeverity = HallucinationSeverity.MEDIUM
    context: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "indicator_type": self.indicator_type.value,
            "description": self.description,
            "confidence": self.confidence,
            "evidence": self.evidence[:500],  # Truncate for storage
            "severity": self.severity.value,
            "context": self.context,
        }


@dataclass
class HallucinationResult:
    """
    Result of hallucination detection.

    Contains overall assessment and individual indicators.
    """

    detected: bool
    overall_confidence: float  # 0.0 to 1.0
    indicators: list[HallucinationIndicator] = field(default_factory=list)
    blocking_recommended: bool = False  # NEVER True by default (INV-002)
    blocking_customer_opted_in: bool = False
    content_hash: str = ""
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_incident_data(self) -> dict[str, Any]:
        """
        Convert to incident creation data.

        CRITICAL: blocking is ALWAYS False unless customer opted in (INV-002).
        """
        return {
            "category": "HALLUCINATION",
            "severity": self._derive_severity().value,
            "blocking": self.blocking_customer_opted_in,  # NEVER True by default
            "confidence": self.overall_confidence,
            "indicators": [i.to_dict() for i in self.indicators],
            "content_hash": self.content_hash,
            "checked_at": self.checked_at.isoformat(),
        }

    def _derive_severity(self) -> HallucinationSeverity:
        """Derive overall severity from indicators."""
        if not self.indicators:
            return HallucinationSeverity.LOW

        severity_order = [
            HallucinationSeverity.CRITICAL,
            HallucinationSeverity.HIGH,
            HallucinationSeverity.MEDIUM,
            HallucinationSeverity.LOW,
        ]

        for severity in severity_order:
            if any(i.severity == severity for i in self.indicators):
                return severity

        return HallucinationSeverity.LOW


@dataclass
class HallucinationConfig:
    """
    Configuration for hallucination detection.

    INV-002 COMPLIANCE:
        - blocking_enabled defaults to False
        - blocking_enabled=True requires explicit customer opt-in
    """

    # Detection thresholds
    minimum_confidence: float = 0.6  # Only report if >= 60% confident
    high_confidence_threshold: float = 0.85  # Flag for review if >= 85%

    # Customer opt-in for blocking (MUST be explicit)
    blocking_enabled: bool = False  # INV-002: NEVER True by default
    blocking_threshold: float = 0.9  # Only block if >= 90% AND opted-in

    # Pattern detection toggles
    detect_url_validity: bool = True
    detect_citation_validity: bool = True
    detect_contradictions: bool = True
    detect_temporal_issues: bool = True

    # Rate limiting (to prevent performance impact)
    max_content_length: int = 50000  # Skip detection for very long content
    timeout_seconds: float = 5.0  # Timeout for detection


class HallucinationDetector:
    """
    Hallucination detection service.

    CRITICAL INVARIANT (INV-002 / HALLU-INV-001):
        This service MUST be non-blocking by default.
        Hallucination detection is PROBABILISTIC, not DETERMINISTIC.
        False positives on blocking destroy customer trust.

    Detection feeds OBSERVABILITY path, not SPINE.
    Customer must explicitly opt-in for blocking behavior.
    """

    def __init__(self, config: Optional[HallucinationConfig] = None):
        """
        Initialize detector with config.

        Args:
            config: Optional config. Defaults enforce INV-002 compliance.
        """
        self.config = config or HallucinationConfig()

        # URL pattern for detecting potentially fabricated URLs
        self._url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+',
            re.IGNORECASE
        )

        # Citation patterns for detecting academic-style citations
        # Pattern 1: (Author, YYYY) or (Author YYYY)
        self._citation_pattern = re.compile(
            r'\(([A-Z][a-z]+(?:\s+(?:et\s+al\.?|&\s+[A-Z][a-z]+))?),?\s*(\d{4})\)',
            re.IGNORECASE
        )
        # Pattern 2: "According to Author (YYYY)" - name outside parens
        self._inline_citation_pattern = re.compile(
            r'(?:according\s+to|per|as\s+per|citing)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*\((\d+)\)',
            re.IGNORECASE
        )

    def detect(
        self,
        content: str,
        context: Optional[dict[str, Any]] = None,
        customer_blocking_opted_in: bool = False,
    ) -> HallucinationResult:
        """
        Detect potential hallucinations in content.

        Args:
            content: The LLM output to check
            context: Optional context (e.g., original prompt, run_id)
            customer_blocking_opted_in: Whether customer opted into blocking

        Returns:
            HallucinationResult with detection outcome

        CRITICAL: This method NEVER blocks unless customer_blocking_opted_in=True.
        """
        # Skip detection for very long content (performance guard)
        if len(content) > self.config.max_content_length:
            return HallucinationResult(
                detected=False,
                overall_confidence=0.0,
                content_hash=self._hash_content(content),
            )

        indicators: list[HallucinationIndicator] = []

        # Run detection patterns
        if self.config.detect_url_validity:
            indicators.extend(self._detect_suspicious_urls(content))

        if self.config.detect_citation_validity:
            indicators.extend(self._detect_suspicious_citations(content))

        if self.config.detect_contradictions:
            indicators.extend(self._detect_contradictions(content))

        if self.config.detect_temporal_issues:
            indicators.extend(self._detect_temporal_issues(content, context))

        # Calculate overall confidence
        if not indicators:
            overall_confidence = 0.0
            detected = False
        else:
            # Weighted average by severity
            weights = {
                HallucinationSeverity.CRITICAL: 1.5,
                HallucinationSeverity.HIGH: 1.2,
                HallucinationSeverity.MEDIUM: 1.0,
                HallucinationSeverity.LOW: 0.5,
            }
            weighted_sum = sum(
                i.confidence * weights.get(i.severity, 1.0) for i in indicators
            )
            weight_total = sum(weights.get(i.severity, 1.0) for i in indicators)
            overall_confidence = min(weighted_sum / weight_total, 1.0)
            detected = overall_confidence >= self.config.minimum_confidence

        # Filter indicators below minimum confidence
        significant_indicators = [
            i for i in indicators if i.confidence >= self.config.minimum_confidence
        ]

        # INV-002: Blocking is NEVER recommended unless customer opted in
        blocking_recommended = (
            customer_blocking_opted_in
            and self.config.blocking_enabled
            and overall_confidence >= self.config.blocking_threshold
        )

        return HallucinationResult(
            detected=detected,
            overall_confidence=overall_confidence,
            indicators=significant_indicators,
            blocking_recommended=blocking_recommended,
            blocking_customer_opted_in=customer_blocking_opted_in,
            content_hash=self._hash_content(content),
        )

    def _detect_suspicious_urls(self, content: str) -> list[HallucinationIndicator]:
        """Detect potentially fabricated URLs."""
        indicators = []
        urls = self._url_pattern.findall(content)

        for url in urls:
            # Check for suspicious patterns in URLs
            suspicious_patterns = [
                # Made-up looking TLDs
                (r'\.(?:fake|test|example|demo)\b', 0.8, "Suspicious TLD"),
                # Very long random-looking paths
                (r'/[a-z0-9]{30,}/', 0.65, "Suspicious path length"),
                # Repeated patterns
                (r'(.)\1{4,}', 0.7, "Repeated characters"),
            ]

            for pattern, confidence, description in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    indicators.append(HallucinationIndicator(
                        indicator_type=HallucinationType.INVALID_URL,
                        description=description,
                        confidence=confidence,
                        evidence=url,
                        severity=HallucinationSeverity.MEDIUM,
                    ))

        return indicators

    def _detect_suspicious_citations(self, content: str) -> list[HallucinationIndicator]:
        """Detect potentially fabricated academic citations."""
        indicators = []

        # Check both citation patterns
        citations = self._citation_pattern.findall(content)
        inline_citations = self._inline_citation_pattern.findall(content)

        # Combine all citations found
        all_citations = list(citations) + list(inline_citations)

        for author, year in all_citations:
            try:
                year_int = int(year)
            except ValueError:
                continue

            current_year = datetime.now().year

            # Future citations are definitely wrong
            if year_int > current_year:
                indicators.append(HallucinationIndicator(
                    indicator_type=HallucinationType.FABRICATED_CITATION,
                    description=f"Citation year {year} is in the future",
                    confidence=0.95,
                    evidence=f"({author}, {year})",
                    severity=HallucinationSeverity.HIGH,
                ))
            # Very old citations might be fabricated
            elif year_int < 1800:
                indicators.append(HallucinationIndicator(
                    indicator_type=HallucinationType.FABRICATED_CITATION,
                    description=f"Citation year {year} is suspiciously old",
                    confidence=0.7,
                    evidence=f"({author}, {year})",
                    severity=HallucinationSeverity.MEDIUM,
                ))

        return indicators

    def _detect_contradictions(self, content: str) -> list[HallucinationIndicator]:
        """Detect self-contradictions in content."""
        indicators = []

        # Simple contradiction patterns
        contradiction_pairs = [
            (r'\bis\s+(?:always|never)\b', r'\bis\s+(?:sometimes|occasionally)\b'),
            (r'\bwill\s+definitely\b', r'\bmight\s+not\b'),
            (r'\b100%\s+(?:sure|certain)\b', r'\b(?:uncertain|unsure)\b'),
        ]

        content_lower = content.lower()
        for pattern_a, pattern_b in contradiction_pairs:
            match_a = re.search(pattern_a, content_lower)
            match_b = re.search(pattern_b, content_lower)
            if match_a and match_b:
                indicators.append(HallucinationIndicator(
                    indicator_type=HallucinationType.SELF_CONTRADICTION,
                    description="Self-contradicting statements detected",
                    confidence=0.75,
                    evidence=f"{match_a.group()} ... {match_b.group()}",
                    severity=HallucinationSeverity.MEDIUM,
                ))

        return indicators

    def _detect_temporal_issues(
        self,
        content: str,
        context: Optional[dict[str, Any]] = None,
    ) -> list[HallucinationIndicator]:
        """Detect temporal impossibilities."""
        indicators = []
        current_year = datetime.now().year

        # Check for future events stated as facts
        future_year_pattern = re.compile(
            rf'\b(in|during|by)\s+({current_year + 1}|{current_year + 2})\b',
            re.IGNORECASE
        )
        matches = future_year_pattern.findall(content)
        for prep, year in matches:
            # Only flag if it's stated as a fact, not a prediction
            if "will" not in content.lower() and "might" not in content.lower():
                indicators.append(HallucinationIndicator(
                    indicator_type=HallucinationType.TEMPORAL_IMPOSSIBILITY,
                    description=f"Future year {year} stated as fact",
                    confidence=0.7,
                    evidence=f"{prep} {year}",
                    severity=HallucinationSeverity.MEDIUM,
                ))

        return indicators

    def _hash_content(self, content: str) -> str:
        """Generate hash of content for evidence tracking."""
        return hashlib.sha256(content.encode()).hexdigest()


# Factory function for creating detector with customer config
def create_detector_for_tenant(
    tenant_config: Optional[dict[str, Any]] = None,
) -> HallucinationDetector:
    """
    Create a detector configured for a specific tenant.

    Args:
        tenant_config: Optional tenant-specific configuration

    Returns:
        Configured HallucinationDetector

    CRITICAL (INV-002): blocking_enabled requires explicit tenant opt-in.
    """
    config = HallucinationConfig()

    if tenant_config:
        # Only enable blocking if tenant explicitly opts in
        config.blocking_enabled = tenant_config.get("hallucination_blocking_enabled", False)
        config.blocking_threshold = tenant_config.get("hallucination_blocking_threshold", 0.9)
        config.minimum_confidence = tenant_config.get("hallucination_min_confidence", 0.6)

    return HallucinationDetector(config)
