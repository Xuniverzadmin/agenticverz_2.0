# Layer: L6 — Platform Substrate
# Product: system-wide
# Temporal:
#   Trigger: api|worker
#   Execution: sync
# Role: Trace data redaction for security
# Callers: trace store
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L5
# Reference: Trace System

"""
PII Redaction Utility for Trace Storage
M8 Deliverable: Secure trace storage with PII masking

Redacts sensitive data from traces before storage:
- Passwords, API keys, tokens
- Credit card numbers
- Email addresses
- Custom patterns via configuration
"""

import copy
import re
from typing import Any

# PII patterns with compiled regexes
PII_PATTERNS = [
    # Passwords and secrets in JSON
    (re.compile(r'(?i)("password"\s*:\s*)"[^"]*"'), r'\1"<REDACTED>"'),
    (re.compile(r'(?i)("secret"\s*:\s*)"[^"]*"'), r'\1"<REDACTED>"'),
    (re.compile(r'(?i)("api_key"\s*:\s*)"[^"]*"'), r'\1"<REDACTED>"'),
    (re.compile(r'(?i)("apikey"\s*:\s*)"[^"]*"'), r'\1"<REDACTED>"'),
    (re.compile(r'(?i)("token"\s*:\s*)"[^"]*"'), r'\1"<REDACTED>"'),
    (re.compile(r'(?i)("access_token"\s*:\s*)"[^"]*"'), r'\1"<REDACTED>"'),
    (re.compile(r'(?i)("refresh_token"\s*:\s*)"[^"]*"'), r'\1"<REDACTED>"'),
    (re.compile(r'(?i)("bearer"\s*:\s*)"[^"]*"'), r'\1"<REDACTED>"'),
    (re.compile(r'(?i)("private_key"\s*:\s*)"[^"]*"'), r'\1"<REDACTED>"'),
    # Authorization headers
    (re.compile(r'(?i)("authorization"\s*:\s*)"[^"]*"'), r'\1"<REDACTED>"'),
    (re.compile(r'(?i)("x-api-key"\s*:\s*)"[^"]*"'), r'\1"<REDACTED>"'),
    # Bearer tokens in values
    (re.compile(r"(?i)Bearer\s+[A-Za-z0-9\-_\.]+"), r"Bearer <REDACTED>"),
    # Credit card numbers (13-19 digits)
    (re.compile(r"\b\d{13,19}\b"), "<REDACTED_CARD>"),
    # SSN (XXX-XX-XXXX)
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "<REDACTED_SSN>"),
    # Email addresses
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "<REDACTED_EMAIL>"),
    # AWS Access Keys
    (re.compile(r"AKIA[0-9A-Z]{16}"), "<REDACTED_AWS_KEY>"),
    # GitHub tokens
    (re.compile(r"ghp_[A-Za-z0-9]{36}"), "<REDACTED_GITHUB_TOKEN>"),
    (re.compile(r"gho_[A-Za-z0-9]{36}"), "<REDACTED_GITHUB_TOKEN>"),
    # Slack tokens
    (re.compile(r"xox[baprs]-[A-Za-z0-9\-]+"), "<REDACTED_SLACK_TOKEN>"),
    # Generic long hex strings (likely secrets/hashes - be careful)
    # Only redact if they look like API keys (32+ chars, hex)
    (re.compile(r'(?i)("key"\s*:\s*)"[a-f0-9]{32,}"'), r'\1"<REDACTED_KEY>"'),
]

# Fields to always redact (case-insensitive)
SENSITIVE_FIELD_NAMES = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "api_key",
    "apikey",
    "api-key",
    "token",
    "access_token",
    "refresh_token",
    "auth_token",
    "authorization",
    "bearer",
    "private_key",
    "privatekey",
    "ssh_key",
    "credentials",
    "cred",
    "ssn",
    "social_security",
    "credit_card",
    "creditcard",
    "card_number",
    "cvv",
    "cvc",
}


def redact_json_string(json_str: str) -> str:
    """
    Apply PII redaction patterns to a JSON string.

    Args:
        json_str: JSON string to redact

    Returns:
        Redacted JSON string
    """
    result = json_str
    for pattern, replacement in PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def redact_dict(data: dict[str, Any], depth: int = 0, max_depth: int = 20) -> dict[str, Any]:
    """
    Recursively redact sensitive fields in a dictionary.

    Args:
        data: Dictionary to redact
        depth: Current recursion depth
        max_depth: Maximum recursion depth

    Returns:
        Redacted dictionary (new copy)
    """
    if depth > max_depth:
        return data

    result = {}
    for key, value in data.items():
        # Check if field name is sensitive
        key_lower = key.lower()
        if key_lower in SENSITIVE_FIELD_NAMES:
            result[key] = "<REDACTED>"
        elif isinstance(value, dict):
            result[key] = redact_dict(value, depth + 1, max_depth)
        elif isinstance(value, list):
            result[key] = redact_list(value, depth + 1, max_depth)
        elif isinstance(value, str):
            result[key] = redact_string_value(value)
        else:
            result[key] = value

    return result


def redact_list(data: list[Any], depth: int = 0, max_depth: int = 20) -> list[Any]:
    """Recursively redact sensitive fields in a list."""
    if depth > max_depth:
        return data

    result = []
    for item in data:
        if isinstance(item, dict):
            result.append(redact_dict(item, depth + 1, max_depth))
        elif isinstance(item, list):
            result.append(redact_list(item, depth + 1, max_depth))
        elif isinstance(item, str):
            result.append(redact_string_value(item))
        else:
            result.append(item)

    return result


def redact_string_value(value: str) -> str:
    """Redact sensitive patterns in a string value."""
    result = value

    # Check for email
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", result):
        result = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<REDACTED_EMAIL>", result)

    # Check for bearer tokens
    if "bearer" in result.lower():
        result = re.sub(r"(?i)Bearer\s+[A-Za-z0-9\-_\.]+", "Bearer <REDACTED>", result)

    # Check for AWS keys
    result = re.sub(r"AKIA[0-9A-Z]{16}", "<REDACTED_AWS_KEY>", result)

    # Check for GitHub tokens
    result = re.sub(r"gh[poa]_[A-Za-z0-9]{36}", "<REDACTED_GITHUB_TOKEN>", result)

    # Check for Slack tokens
    result = re.sub(r"xox[baprs]-[A-Za-z0-9\-]+", "<REDACTED_SLACK_TOKEN>", result)

    return result


def redact_trace_data(trace: dict[str, Any]) -> dict[str, Any]:
    """
    Redact PII from a complete trace object.

    This is the main entry point for trace redaction.
    Creates a deep copy to avoid modifying the original.

    Args:
        trace: Trace object to redact

    Returns:
        Redacted trace (new copy)
    """
    # Make a deep copy
    redacted = copy.deepcopy(trace)

    # Redact plan parameters
    if "plan" in redacted and isinstance(redacted["plan"], list):
        redacted["plan"] = redact_list(redacted["plan"])

    # Redact step data
    if "steps" in redacted and isinstance(redacted["steps"], list):
        for step in redacted["steps"]:
            if isinstance(step, dict):
                # Redact params
                if "params" in step:
                    step["params"] = redact_dict(step["params"]) if isinstance(step["params"], dict) else step["params"]

                # Redact outcome_data
                if "outcome_data" in step and step["outcome_data"]:
                    step["outcome_data"] = (
                        redact_dict(step["outcome_data"])
                        if isinstance(step["outcome_data"], dict)
                        else step["outcome_data"]
                    )

                # Redact input/output if present
                if "input_data" in step:
                    step["input_data"] = (
                        redact_dict(step["input_data"]) if isinstance(step["input_data"], dict) else step["input_data"]
                    )
                if "output_data" in step:
                    step["output_data"] = (
                        redact_dict(step["output_data"])
                        if isinstance(step["output_data"], dict)
                        else step["output_data"]
                    )

    # Redact metadata
    if "metadata" in redacted and isinstance(redacted["metadata"], dict):
        redacted["metadata"] = redact_dict(redacted["metadata"])

    return redacted


def is_sensitive_field(field_name: str) -> bool:
    """Check if a field name indicates sensitive data."""
    return field_name.lower() in SENSITIVE_FIELD_NAMES


def add_sensitive_field(field_name: str) -> None:
    """Add a custom field name to the sensitive fields set."""
    SENSITIVE_FIELD_NAMES.add(field_name.lower())


def add_redaction_pattern(pattern: str, replacement: str) -> None:
    """Add a custom redaction pattern."""
    PII_PATTERNS.append((re.compile(pattern), replacement))
