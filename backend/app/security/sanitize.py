# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Sanitize text before embedding to prevent secret leakage
# Callers: vector_store.py, recovery_matcher.py, iaec.py
# Allowed Imports: None (pure functions)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: PIN-052

"""
Security Sanitization for Embedding Operations

Prevents secrets, PII, and sensitive data from being embedded and stored
in vector databases. This is critical for data security compliance.

Patterns removed:
- API keys (various formats)
- Passwords and secrets in error messages
- Bearer tokens
- Connection strings with credentials
- Email addresses
- IP addresses (optional)
- Credit card numbers
- SSN patterns

PIN-052: Data Ownership & Embedding Security
"""

import re
from typing import List, Tuple

# Compiled regex patterns for performance
PATTERNS: List[Tuple[re.Pattern, str, str]] = [
    # API Keys - various formats
    (
        re.compile(r"\b(sk-[a-zA-Z0-9]{20,})\b", re.IGNORECASE),
        "[REDACTED_API_KEY]",
        "openai_key",
    ),
    (
        re.compile(r"\b(sk_live_[a-zA-Z0-9]{20,})\b", re.IGNORECASE),
        "[REDACTED_API_KEY]",
        "stripe_live_key",
    ),
    (
        re.compile(r"\b(sk_test_[a-zA-Z0-9]{20,})\b", re.IGNORECASE),
        "[REDACTED_API_KEY]",
        "stripe_test_key",
    ),
    (
        re.compile(r"\b(pk_live_[a-zA-Z0-9]{20,})\b", re.IGNORECASE),
        "[REDACTED_API_KEY]",
        "stripe_pk_key",
    ),
    (
        re.compile(r"\b(xox[baprs]-[a-zA-Z0-9-]+)\b", re.IGNORECASE),
        "[REDACTED_API_KEY]",
        "slack_token",
    ),
    (
        re.compile(r"\b(ghp_[a-zA-Z0-9]{36})\b", re.IGNORECASE),
        "[REDACTED_API_KEY]",
        "github_pat",
    ),
    (
        re.compile(r"\b(gho_[a-zA-Z0-9]{36})\b", re.IGNORECASE),
        "[REDACTED_API_KEY]",
        "github_oauth",
    ),
    (
        re.compile(r"\b(ghu_[a-zA-Z0-9]{36})\b", re.IGNORECASE),
        "[REDACTED_API_KEY]",
        "github_user",
    ),
    (
        re.compile(r"\b(ghr_[a-zA-Z0-9]{36})\b", re.IGNORECASE),
        "[REDACTED_API_KEY]",
        "github_refresh",
    ),
    (
        re.compile(r"\b(AKIA[0-9A-Z]{16})\b"),
        "[REDACTED_AWS_KEY]",
        "aws_access_key",
    ),
    # Generic API key patterns
    (
        re.compile(r"\b(api[_-]?key[=:]\s*['\"]?[a-zA-Z0-9_-]{20,}['\"]?)", re.IGNORECASE),
        "[REDACTED_API_KEY]",
        "generic_api_key",
    ),
    (
        re.compile(r"\b(apikey[=:]\s*['\"]?[a-zA-Z0-9_-]{20,}['\"]?)", re.IGNORECASE),
        "[REDACTED_API_KEY]",
        "generic_apikey",
    ),
    # Bearer tokens
    (
        re.compile(r"(Bearer\s+[a-zA-Z0-9_\-\.]+)", re.IGNORECASE),
        "Bearer [REDACTED_TOKEN]",
        "bearer_token",
    ),
    # Authorization headers
    (
        re.compile(r"(Authorization[=:]\s*['\"]?[a-zA-Z0-9_\-\.]+['\"]?)", re.IGNORECASE),
        "Authorization: [REDACTED]",
        "auth_header",
    ),
    # Passwords in various contexts
    (
        re.compile(r"(password[=:]\s*['\"]?[^\s'\"]{4,}['\"]?)", re.IGNORECASE),
        "password=[REDACTED]",
        "password",
    ),
    (
        re.compile(r"(passwd[=:]\s*['\"]?[^\s'\"]{4,}['\"]?)", re.IGNORECASE),
        "passwd=[REDACTED]",
        "passwd",
    ),
    (
        re.compile(r"(secret[=:]\s*['\"]?[^\s'\"]{8,}['\"]?)", re.IGNORECASE),
        "secret=[REDACTED]",
        "secret",
    ),
    # Connection strings with credentials
    (
        re.compile(
            r"(postgresql://[^:]+:[^@]+@[^\s]+)",
            re.IGNORECASE,
        ),
        "postgresql://[REDACTED_CONNECTION]",
        "postgres_url",
    ),
    (
        re.compile(
            r"(postgres://[^:]+:[^@]+@[^\s]+)",
            re.IGNORECASE,
        ),
        "postgres://[REDACTED_CONNECTION]",
        "postgres_url_alt",
    ),
    (
        re.compile(
            r"(mysql://[^:]+:[^@]+@[^\s]+)",
            re.IGNORECASE,
        ),
        "mysql://[REDACTED_CONNECTION]",
        "mysql_url",
    ),
    (
        re.compile(
            r"(mongodb://[^:]+:[^@]+@[^\s]+)",
            re.IGNORECASE,
        ),
        "mongodb://[REDACTED_CONNECTION]",
        "mongodb_url",
    ),
    (
        re.compile(
            r"(redis://:[^@]+@[^\s]+)",
            re.IGNORECASE,
        ),
        "redis://[REDACTED_CONNECTION]",
        "redis_url",
    ),
    # Private keys
    (
        re.compile(r"(-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----)"),
        "[REDACTED_PRIVATE_KEY]",
        "private_key",
    ),
    # JWT tokens (but not just any base64)
    (
        re.compile(r"\b(eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*)\b"),
        "[REDACTED_JWT]",
        "jwt_token",
    ),
    # Credit card numbers (basic pattern)
    (
        re.compile(r"\b(\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4})\b"),
        "[REDACTED_CC]",
        "credit_card",
    ),
    # SSN patterns (US)
    (
        re.compile(r"\b(\d{3}[-\s]?\d{2}[-\s]?\d{4})\b"),
        "[REDACTED_SSN]",
        "ssn",
    ),
]

# Email pattern (optional - sometimes needed in error context)
EMAIL_PATTERN = re.compile(r"\b([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b")

# IP address pattern (optional)
IP_PATTERN = re.compile(r"\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b")

# Hex strings that look like secrets (32+ chars)
HEX_SECRET_PATTERN = re.compile(r"\b([a-fA-F0-9]{32,})\b")


def sanitize_for_embedding(
    text: str,
    redact_emails: bool = True,
    redact_ips: bool = False,
    redact_hex_secrets: bool = True,
    audit: bool = False,
) -> str:
    """
    Sanitize text before embedding to prevent secret leakage.

    This function removes sensitive data patterns from text before it
    is sent to embedding APIs or stored in vector databases.

    Args:
        text: Raw text to sanitize
        redact_emails: Whether to redact email addresses (default True)
        redact_ips: Whether to redact IP addresses (default False - often needed for debugging)
        redact_hex_secrets: Whether to redact long hex strings (default True)
        audit: If True, return (sanitized_text, list_of_redactions) for logging

    Returns:
        Sanitized text with secrets replaced by [REDACTED_*] placeholders.
        If audit=True, returns tuple of (sanitized_text, redactions_list)

    Example:
        >>> sanitize_for_embedding("API key: sk-1234567890abcdefghij")
        "API key: [REDACTED_API_KEY]"

        >>> sanitize_for_embedding("Connect to postgres://user:pass@host/db")  # pragma: allowlist secret
        "Connect to postgres://[REDACTED_CONNECTION]"
    """
    if not text:
        return "" if not audit else ("", [])

    redactions = [] if audit else None
    result = text

    # Apply all secret patterns
    for pattern, replacement, pattern_name in PATTERNS:
        if audit:
            matches = pattern.findall(result)
            if matches:
                redactions.extend([(pattern_name, m if isinstance(m, str) else m[0]) for m in matches])
        result = pattern.sub(replacement, result)

    # Optional: Redact emails
    if redact_emails:
        if audit:
            matches = EMAIL_PATTERN.findall(result)
            if matches:
                redactions.extend([("email", m) for m in matches])
        result = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", result)

    # Optional: Redact IPs
    if redact_ips:
        if audit:
            matches = IP_PATTERN.findall(result)
            if matches:
                redactions.extend([("ip_address", m) for m in matches])
        result = IP_PATTERN.sub("[REDACTED_IP]", result)

    # Optional: Redact long hex strings (likely secrets)
    if redact_hex_secrets:
        if audit:
            matches = HEX_SECRET_PATTERN.findall(result)
            if matches:
                redactions.extend([("hex_secret", m[:8] + "...") for m in matches])
        result = HEX_SECRET_PATTERN.sub("[REDACTED_HEX]", result)

    if audit:
        return result, redactions
    return result


def sanitize_error_message(error_msg: str) -> str:
    """
    Sanitize an error message specifically.

    Error messages often contain sensitive data like:
    - Stack traces with connection strings
    - Failed authentication details
    - API responses with tokens

    Args:
        error_msg: Raw error message

    Returns:
        Sanitized error message safe for embedding
    """
    # Apply standard sanitization with stricter settings
    return sanitize_for_embedding(
        error_msg,
        redact_emails=True,
        redact_ips=True,  # IPs in errors are often internal
        redact_hex_secrets=True,
    )


def is_safe_for_embedding(text: str) -> bool:
    """
    Check if text is safe to embed without sanitization.

    Useful for validation before embedding operations.

    Args:
        text: Text to check

    Returns:
        True if no sensitive patterns detected
    """
    # Check all secret patterns
    for pattern, _, _ in PATTERNS:
        if pattern.search(text):
            return False

    # Check email
    if EMAIL_PATTERN.search(text):
        return False

    # Check hex secrets
    if HEX_SECRET_PATTERN.search(text):
        return False

    return True


# Convenience alias
sanitize = sanitize_for_embedding
