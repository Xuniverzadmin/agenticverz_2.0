# Input Sanitizer
# Phase 5: Prompt-Injection Safe Input Gate
# Sanitizes user input before it reaches the planner

import logging
import os
import re
from dataclasses import dataclass
from typing import List, Optional, Set
from urllib.parse import urlparse

logger = logging.getLogger("nova.utils.input_sanitizer")

# ==================== CONFIGURATION ====================
# Maximum goal length
MAX_GOAL_LENGTH = int(os.getenv("MAX_GOAL_LENGTH", "10000"))

# Enable/disable specific checks
ENABLE_INJECTION_DETECTION = os.getenv("ENABLE_INJECTION_DETECTION", "true").lower() == "true"
ENABLE_URL_SANITIZATION = os.getenv("ENABLE_URL_SANITIZATION", "true").lower() == "true"

# Forbidden URL patterns (same as plan_inspector for consistency)
FORBIDDEN_HOSTS: Set[str] = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "169.254.169.254",  # AWS metadata
    "metadata.google.internal",  # GCP metadata
    "internal",
    "local",
}

# ==================== INJECTION PATTERNS ====================
# These patterns indicate potential prompt injection attempts

INJECTION_PATTERNS = [
    # Direct instruction override
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|rules?)", "instruction_override"),
    (r"disregard\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)", "instruction_override"),
    (r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?)", "instruction_override"),
    # System prompt manipulation
    (r"you\s+are\s+now\s+(a|an)\s+", "role_hijack"),
    (r"pretend\s+(you\s+are|to\s+be)\s+", "role_hijack"),
    (r"act\s+as\s+(if\s+)?(you\s+are|a|an)\s+", "role_hijack"),
    (r"your\s+new\s+(role|persona|identity)\s+is", "role_hijack"),
    # Dangerous skill invocation
    (r"(call|execute|run|invoke)\s+(postgres_query|sql|database).*(drop|truncate|delete|alter)", "dangerous_sql"),
    (r"drop\s+table", "dangerous_sql"),
    (r"truncate\s+table", "dangerous_sql"),
    (r"delete\s+from\s+\w+\s+where\s+1\s*=\s*1", "dangerous_sql"),
    # Bypass attempts
    (r"bypass\s+(validation|security|safety|checks?)", "bypass_attempt"),
    (r"skip\s+(validation|security|safety|checks?)", "bypass_attempt"),
    (r"disable\s+(validation|security|safety|checks?)", "bypass_attempt"),
    # Recursive/loop attacks
    (r"create\s+(a\s+)?plan\s+that\s+(creates?|generates?)\s+(more\s+)?plans?", "recursive_plan"),
    (r"loop\s+(forever|infinitely|until)", "infinite_loop"),
    (r"repeat\s+this\s+(task|action)\s+\d{3,}\s+times", "excessive_repeat"),
    # Code execution attempts
    (r"exec\s*\(", "code_execution"),
    (r"eval\s*\(", "code_execution"),
    (r"import\s+os\s*;?\s*os\.(system|popen)", "code_execution"),
    (r"subprocess\.(call|run|Popen)", "code_execution"),
    # Credential extraction
    (
        r"(show|print|display|output|return)\s+(me\s+)?(the\s+)?(api[_\s]?key|password|secret|credential|token)",
        "credential_leak",
    ),
    (r"what\s+(is|are)\s+(your|the)\s+(api[_\s]?key|password|secret|credential)", "credential_leak"),
]

# Compiled patterns for efficiency
_compiled_patterns = [(re.compile(pattern, re.IGNORECASE), name) for pattern, name in INJECTION_PATTERNS]


@dataclass
class SanitizationResult:
    """Result of input sanitization."""

    sanitized: str
    is_safe: bool
    warnings: List[str]
    blocked_reason: Optional[str] = None
    detected_patterns: List[str] = None

    def __post_init__(self):
        if self.detected_patterns is None:
            self.detected_patterns = []


def detect_injection_patterns(text: str) -> List[tuple]:
    """Detect prompt injection patterns in text.

    Returns:
        List of (pattern_name, matched_text) tuples
    """
    detected = []
    for pattern, name in _compiled_patterns:
        match = pattern.search(text)
        if match:
            detected.append((name, match.group(0)))
    return detected


def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text."""
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, text, re.IGNORECASE)


def is_url_safe(url: str) -> tuple[bool, Optional[str]]:
    """Check if a URL is safe (not targeting internal resources).

    Returns:
        Tuple of (is_safe, reason_if_unsafe)
    """
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        # Check forbidden hosts
        if host in FORBIDDEN_HOSTS:
            return False, f"Forbidden host: {host}"

        # Check private IP ranges
        if host.startswith("10.") or host.startswith("192.168."):
            return False, f"Private IP range: {host}"

        # Check 172.16-31.x.x
        if host.startswith("172."):
            try:
                second_octet = int(host.split(".")[1])
                if 16 <= second_octet <= 31:
                    return False, f"Private IP range: {host}"
            except (ValueError, IndexError):
                pass

        # Check for internal domain patterns
        for forbidden in FORBIDDEN_HOSTS:
            if host.endswith(f".{forbidden}"):
                return False, f"Internal domain: {host}"

        return True, None

    except Exception as e:
        return False, f"Invalid URL: {str(e)[:50]}"


def sanitize_goal(goal: str) -> SanitizationResult:
    """Sanitize a goal string before processing.

    This is the main entry point for the input sanitizer.

    Args:
        goal: The user-provided goal text

    Returns:
        SanitizationResult with sanitized text and safety info
    """
    warnings = []
    detected_patterns = []

    # Check length
    if len(goal) > MAX_GOAL_LENGTH:
        return SanitizationResult(
            sanitized=goal[:MAX_GOAL_LENGTH],
            is_safe=False,
            warnings=[f"Goal truncated from {len(goal)} to {MAX_GOAL_LENGTH} chars"],
            blocked_reason=f"Goal exceeds maximum length ({MAX_GOAL_LENGTH})",
        )

    # Normalize whitespace
    sanitized = " ".join(goal.split())

    # Detect injection patterns
    if ENABLE_INJECTION_DETECTION:
        detected = detect_injection_patterns(sanitized)
        if detected:
            detected_patterns = [name for name, _ in detected]

            # Log all detections
            for name, matched in detected:
                logger.warning(
                    "injection_pattern_detected",
                    extra={
                        "pattern": name,
                        "matched": matched[:100],
                        "goal_preview": sanitized[:200],
                    },
                )

            # Block on severe patterns
            severe_patterns = {"dangerous_sql", "code_execution", "credential_leak"}
            severe_detected = [p for p in detected_patterns if p in severe_patterns]

            if severe_detected:
                return SanitizationResult(
                    sanitized=sanitized,
                    is_safe=False,
                    warnings=[f"Detected: {', '.join(detected_patterns)}"],
                    blocked_reason=f"Dangerous pattern detected: {severe_detected[0]}",
                    detected_patterns=detected_patterns,
                )

            # Warn but allow on less severe patterns
            warnings.append(f"Suspicious patterns detected: {', '.join(detected_patterns)}")

    # Sanitize URLs
    if ENABLE_URL_SANITIZATION:
        urls = extract_urls(sanitized)
        unsafe_urls = []

        for url in urls:
            is_safe, reason = is_url_safe(url)
            if not is_safe:
                unsafe_urls.append((url, reason))

        if unsafe_urls:
            # Remove or redact unsafe URLs
            for url, reason in unsafe_urls:
                sanitized = sanitized.replace(url, "[BLOCKED_URL]")
                warnings.append(f"Blocked URL: {reason}")

                logger.warning("unsafe_url_blocked", extra={"url": url, "reason": reason})

    return SanitizationResult(
        sanitized=sanitized,
        is_safe=True,
        warnings=warnings,
        detected_patterns=detected_patterns,
    )


def validate_goal(goal: str) -> tuple[bool, Optional[str], List[str]]:
    """Convenience function to validate a goal.

    Returns:
        Tuple of (is_valid, error_message, warnings)
    """
    result = sanitize_goal(goal)
    return result.is_safe, result.blocked_reason, result.warnings
