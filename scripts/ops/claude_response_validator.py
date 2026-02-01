#!/usr/bin/env python3
# Layer: L8 — Operational Script
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: manual
#   Execution: sync
# Role: AgenticVerz — Claude Response Validator v2
# artifact_class: CODE
"""
AgenticVerz — Claude Response Validator v2

Validates Claude responses against:
1. Pre-Code Discipline contract (SELF-AUDIT, memory pins, etc.)
2. Behavior Library rules (BL-ENV-001, BL-TIME-001, etc.)
3. Evidence field requirements

Features:
- Loads rules from YAML/JSON library
- Trigger-based rule evaluation
- Evidence field checking
- Severity-based enforcement (BLOCKER/ERROR/WARN)

Usage:
    python claude_response_validator.py <response_file>
    echo "response text" | python claude_response_validator.py --stdin
    python claude_response_validator.py --stdin --library docs/behavior/behavior_library.json

Exit codes:
    0 = Valid response
    1 = Invalid response (missing required sections)
    2 = Usage error

Reference: docs/behavior/behavior_library.yaml
"""

import sys
import re
import argparse
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class ValidationResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


class Severity(Enum):
    BLOCKER = "BLOCKER"
    ERROR = "ERROR"
    WARN = "WARN"


@dataclass
class CheckResult:
    name: str
    result: ValidationResult
    message: str
    required: bool = True


@dataclass
class RuleFinding:
    """Result of evaluating a single behavior rule."""

    rule_id: str
    triggered: bool
    section_present: bool
    evidence_fields_present: List[str] = field(default_factory=list)
    evidence_fields_missing: List[str] = field(default_factory=list)
    severity: Severity = Severity.ERROR
    message: str = ""


# =============================================================================
# BEHAVIOR LIBRARY LOADING
# =============================================================================


def load_behavior_library(library_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load behavior library from JSON file.

    Searches in order:
    1. Provided path
    2. docs/behavior/behavior_library.json
    3. Falls back to embedded rules
    """
    search_paths = []
    if library_path:
        search_paths.append(Path(library_path))

    # Add default locations
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    search_paths.extend(
        [
            repo_root / "docs" / "behavior" / "behavior_library.json",
            Path("/root/agenticverz2.0/docs/behavior/behavior_library.json"),
        ]
    )

    for path in search_paths:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)

    # Fall back to embedded rules
    return {"version": 0, "library": []}


def evaluate_behavior_rules(
    response_text: str, rules: List[Dict[str, Any]]
) -> List[RuleFinding]:
    """
    Evaluate all behavior rules against response text.

    For each rule:
    1. Check if any trigger matches
    2. If triggered, check for required section
    3. Check for evidence fields

    Returns list of RuleFinding objects.
    """
    findings = []

    for rule in rules:
        rule_id = rule.get("id", "UNKNOWN")
        severity = Severity[rule.get("severity", "ERROR")]
        triggers = rule.get("triggers", {}).get("any_of", [])
        requires = rule.get("requires", {})
        evidence = rule.get("evidence", {})

        # Check if triggered
        triggered = False
        for trigger in triggers:
            if "keyword" in trigger:
                keyword = trigger["keyword"]
                if keyword.lower() in response_text.lower():
                    triggered = True
                    break

        if not triggered:
            findings.append(
                RuleFinding(
                    rule_id=rule_id,
                    triggered=False,
                    section_present=False,
                    severity=severity,
                    message=f"{rule_id}: Not triggered",
                )
            )
            continue

        # Rule is triggered - check for required sections
        sections = requires.get("sections", [])
        section_present = True
        for sec in sections:
            # Map section name to expected patterns
            section_patterns = {
                "RUNTIME_SYNC": r"RUNTIME SYNC(HRONIZATION)? CHECK",
                "AUTH_CONTRACT": r"AUTH(ENTICATION)? CONTRACT CHECK",
                "TIME_SEMANTICS": r"TIMESTAMP SEMANTICS CHECK",
                "SERVICE_ENUM": r"DOCKER NAME CHECK|SERVICE ENUM",
                "MIGRATION_HEAD": r"MIGRATION HEAD CHECK",
                "TEST_PREREQ": r"TEST PREREQUISITES? CHECK",
            }
            pattern = section_patterns.get(sec, sec)
            if not re.search(pattern, response_text, re.IGNORECASE):
                section_present = False
                break

        # Check evidence fields
        required_fields = evidence.get("required_fields", [])
        fields_present = []
        fields_missing = []

        for fld in required_fields:
            # Convert snake_case to various patterns
            patterns = [
                fld,
                fld.replace("_", " "),
                fld.replace("_", "-"),
            ]
            found = False
            for p in patterns:
                if re.search(rf"{p}.*:", response_text, re.IGNORECASE):
                    found = True
                    break
            if found:
                fields_present.append(fld)
            else:
                fields_missing.append(fld)

        # Determine message
        if section_present and not fields_missing:
            message = f"{rule_id}: Section and evidence present"
        elif section_present and fields_missing:
            message = f"{rule_id}: Section present but missing fields: {', '.join(fields_missing)}"
        else:
            message = rule.get(
                "message_on_fail", f"{rule_id}: Missing required section"
            )

        findings.append(
            RuleFinding(
                rule_id=rule_id,
                triggered=True,
                section_present=section_present,
                evidence_fields_present=fields_present,
                evidence_fields_missing=fields_missing,
                severity=severity,
                message=message,
            )
        )

    return findings


# =============================================================================
# INCIDENT CLASSIFIER
# =============================================================================


def classify_incident(log_text: str) -> set:
    """
    Classify incident from log/error text.

    Returns set of incident tags.
    """
    tags = set()

    # Environment drift
    if any(
        kw in log_text.lower()
        for kw in [
            "docker compose",
            "health",
            "container",
            "stale",
            "not running",
            "connection refused",
            "build",
            "rebuild",
        ]
    ):
        tags.add("ENV_DRIFT")

    # Auth mismatch
    if any(
        kw in log_text.lower()
        for kw in [
            "forbidden",
            "rbac",
            "x-aos-key",
            "x-machine-token",
            "401",
            "403",
            "unauthorized",
            "permission denied",
        ]
    ):
        tags.add("AUTH_MISMATCH")

    # Time/timezone semantics
    if any(
        kw in log_text.lower()
        for kw in ["timezone", "timestamp", "naive", "aware", "utc", "offset"]
    ):
        tags.add("TIME_SEMANTICS")

    # Migration issues
    if any(
        kw in log_text.lower()
        for kw in ["alembic", "migration", "head", "revision", "multiple heads"]
    ):
        tags.add("MIGRATION_FORK")

    return tags


def scaffold_rule(tag: str) -> Optional[str]:
    """
    Return the rule ID template for a given incident tag.
    """
    templates = {
        "ENV_DRIFT": "BL-ENV-001",
        "AUTH_MISMATCH": "BL-AUTH-001",
        "TIME_SEMANTICS": "BL-TIME-001",
        "MIGRATION_FORK": "BL-MIG-001",
    }
    return templates.get(tag)


class ClaudeResponseValidator:
    """Validates Claude responses for AgenticVerz compliance."""

    # Patterns that indicate code changes
    CODE_PATTERNS = [
        r"```python",
        r"```sql",
        r"```typescript",
        r"```javascript",
        r"```bash.*\n.*\s*(def |class |CREATE |ALTER |DROP |INSERT |UPDATE |DELETE )",
        r"def\s+\w+\s*\(",
        r"class\s+\w+\s*[:\(]",
        r"async\s+def\s+\w+",
        r"op\.add_column",
        r"op\.create_table",
        r"op\.execute",
        r"@app\.(get|post|put|delete|patch)",
    ]

    # Required sections when code is present
    REQUIRED_SECTIONS = {
        "self_audit": {
            "pattern": r"SELF-AUDIT",
            "message": "SELF-AUDIT section required for code changes",
        },
        "verify_db": {
            "pattern": r"Did I verify.*DB|Did I verify current DB|alembic current",
            "message": "Database verification check required",
        },
        "memory_pins": {
            "pattern": r"Did I read.*memory pins|memory pins.*YES",
            "message": "Memory pins check required",
        },
        "historical_mutation": {
            "pattern": r"Did I risk historical mutation|historical mutation.*YES|historical mutation.*NO",
            "message": "Historical mutation risk assessment required",
        },
    }

    # Boot sequence acknowledgement
    BOOT_ACK_PATTERN = r"(AgenticVerz boot sequence acknowledged|I accept the AgenticVerz Pre-Code Discipline)"

    # Blocked status pattern
    BLOCKED_PATTERN = r"STATUS:\s*BLOCKED"

    # =========================================================================
    # BEHAVIOR LIBRARY RULES (BL-*)
    # Reference: CLAUDE_BEHAVIOR_LIBRARY.md
    # =========================================================================

    BEHAVIOR_RULES = {
        "BL-ENV-001": {
            "name": "Runtime Sync Before Test",
            "triggers": [
                r"curl\s+.*localhost",
                r"curl\s+.*127\.0\.0\.1",
                r"curl\s+.*:8000",
                r"test\s+endpoint",
                r"testing\s+.*endpoint",
                r"docker compose up.*--build",
                r"rebuild.*container",
            ],
            "required_section": r"RUNTIME SYNC CHECK",
            "severity": "BLOCKING",
            "message": "BL-ENV-001: Runtime sync check required before testing endpoints",
        },
        "BL-DB-001": {
            "name": "Timestamp Semantics Alignment",
            "triggers": [
                r"datetime\.",
                r"utc_now\(\)",
                r"datetime\.now\(",
                r"datetime\.utcnow\(",
                r"timezone\.utc",
                r"TIMESTAMP\s+(WITH|WITHOUT)\s+TIME\s+ZONE",
                r"default_factory.*datetime",
            ],
            "required_section": r"TIMESTAMP SEMANTICS CHECK",
            "severity": "BLOCKING",
            "message": "BL-DB-001: Timestamp semantics check required for datetime operations",
        },
        "BL-AUTH-001": {
            "name": "Auth Contract Enumeration",
            "triggers": [
                r"401\s+",
                r"403\s+",
                r"422\s+.*auth",
                r"X-AOS-Key",
                r"X-Machine-Token",
                r"Authorization:\s+Bearer",
                r"Depends\(verify_",
                r"RBAC.*block",
            ],
            "required_section": r"AUTH CONTRACT CHECK",
            "severity": "BLOCKING",
            "message": "BL-AUTH-001: Auth contract enumeration required before endpoint testing",
        },
        "BL-MIG-001": {
            "name": "Migration Head Verification",
            "triggers": [
                r"alembic\s+revision",
                r"alembic\s+upgrade",
                r"op\.add_column",
                r"op\.create_table",
                r"op\.drop_",
                r"migration",
            ],
            "required_section": r"MIGRATION HEAD CHECK",
            "severity": "BLOCKING",
            "message": "BL-MIG-001: Migration head verification required before creating migrations",
        },
        "BL-DOCKER-001": {
            "name": "Docker Service Name Resolution",
            "triggers": [
                r"docker\s+compose",
                r"docker\s+exec",
                r"docker\s+logs",
                r"container.*restart",
            ],
            "required_section": r"DOCKER NAME CHECK",
            "severity": "WARNING",
            "message": "BL-DOCKER-001: Docker service/container name resolution recommended",
        },
        "BL-TEST-001": {
            "name": "Test Execution Prerequisites",
            "triggers": [
                r"pytest",
                r"python.*-m\s+pytest",
                r"run.*test",
                r"test.*suite",
            ],
            "required_section": r"TEST PREREQUISITES CHECK",
            "severity": "BLOCKING",
            "message": "BL-TEST-001: Test prerequisites check required before running tests",
        },
    }

    def __init__(
        self, response: str, strict: bool = True, library_path: Optional[str] = None
    ):
        self.response = response
        self.strict = strict
        self.checks: List[CheckResult] = []
        self.library_path = library_path
        self._library = None

    @property
    def library(self) -> Dict[str, Any]:
        """Lazy-load behavior library."""
        if self._library is None:
            self._library = load_behavior_library(self.library_path)
        return self._library

    def contains_code(self) -> bool:
        """Check if response contains code changes."""
        for pattern in self.CODE_PATTERNS:
            if re.search(pattern, self.response, re.IGNORECASE | re.MULTILINE):
                return True
        return False

    def is_blocked(self) -> bool:
        """Check if response indicates BLOCKED status."""
        return bool(re.search(self.BLOCKED_PATTERN, self.response, re.IGNORECASE))

    def has_boot_acknowledgement(self) -> bool:
        """Check for boot sequence acknowledgement."""
        return bool(re.search(self.BOOT_ACK_PATTERN, self.response, re.IGNORECASE))

    def check_required_section(self, name: str, config: dict) -> CheckResult:
        """Check if a required section is present."""
        pattern = config["pattern"]
        message = config["message"]

        if re.search(pattern, self.response, re.IGNORECASE | re.MULTILINE):
            return CheckResult(
                name=name,
                result=ValidationResult.PASS,
                message=f"{name}: Present",
                required=True,
            )
        else:
            return CheckResult(
                name=name, result=ValidationResult.FAIL, message=message, required=True
            )

    def check_behavior_rules(self) -> List[CheckResult]:
        """
        Check behavior library rules (BL-*).

        For each rule:
        1. Check if any trigger pattern matches
        2. If triggered, require the corresponding output section
        """
        results = []

        for rule_id, config in self.BEHAVIOR_RULES.items():
            # Check if any trigger matches
            triggered = False
            for trigger in config["triggers"]:
                if re.search(trigger, self.response, re.IGNORECASE | re.MULTILINE):
                    triggered = True
                    break

            if triggered:
                # Rule triggered - check for required section
                has_section = bool(
                    re.search(
                        config["required_section"],
                        self.response,
                        re.IGNORECASE | re.MULTILINE,
                    )
                )

                if has_section:
                    results.append(
                        CheckResult(
                            name=rule_id,
                            result=ValidationResult.PASS,
                            message=f"{rule_id} ({config['name']}): Section present",
                            required=config["severity"] == "BLOCKING",
                        )
                    )
                else:
                    # Missing required section
                    result_type = (
                        ValidationResult.FAIL
                        if config["severity"] == "BLOCKING"
                        else ValidationResult.WARN
                    )
                    results.append(
                        CheckResult(
                            name=rule_id,
                            result=result_type,
                            message=config["message"],
                            required=config["severity"] == "BLOCKING",
                        )
                    )
            else:
                # Rule not triggered - skip
                results.append(
                    CheckResult(
                        name=rule_id,
                        result=ValidationResult.SKIP,
                        message=f"{rule_id}: Not triggered",
                        required=False,
                    )
                )

        return results

    def validate(self) -> Tuple[bool, List[CheckResult]]:
        """
        Run all validation checks.

        Returns:
            Tuple of (is_valid, list_of_check_results)
        """
        self.checks = []

        # Check 1: Boot acknowledgement (warning only in non-strict mode)
        if self.has_boot_acknowledgement():
            self.checks.append(
                CheckResult(
                    name="boot_ack",
                    result=ValidationResult.PASS,
                    message="Boot sequence acknowledged",
                    required=False,
                )
            )
        else:
            self.checks.append(
                CheckResult(
                    name="boot_ack",
                    result=ValidationResult.WARN
                    if not self.strict
                    else ValidationResult.FAIL,
                    message="Boot sequence not acknowledged",
                    required=self.strict,
                )
            )

        # Check 2: If BLOCKED, validation passes (Claude correctly stopped)
        if self.is_blocked():
            self.checks.append(
                CheckResult(
                    name="blocked_status",
                    result=ValidationResult.PASS,
                    message="Response correctly indicates BLOCKED status",
                    required=False,
                )
            )
            # BLOCKED responses are always valid
            return True, self.checks

        # Check 3: If code present, require all sections
        has_code = self.contains_code()

        if has_code:
            self.checks.append(
                CheckResult(
                    name="code_detected",
                    result=ValidationResult.WARN,
                    message="Code changes detected - validating required sections",
                    required=False,
                )
            )

            # Check all required sections
            for name, config in self.REQUIRED_SECTIONS.items():
                result = self.check_required_section(name, config)
                self.checks.append(result)
        else:
            self.checks.append(
                CheckResult(
                    name="code_detected",
                    result=ValidationResult.SKIP,
                    message="No code changes detected - sections check skipped",
                    required=False,
                )
            )

        # Check 4: Behavior Library Rules (BL-*)
        # These apply regardless of code presence
        behavior_checks = self.check_behavior_rules()
        self.checks.extend(behavior_checks)

        # Check 5: Library-based rule evaluation (if library loaded)
        library_rules = self.library.get("library", [])
        if library_rules:
            lib_findings = evaluate_behavior_rules(self.response, library_rules)
            for finding in lib_findings:
                if finding.triggered:
                    # Convert to CheckResult
                    if finding.section_present and not finding.evidence_fields_missing:
                        result = ValidationResult.PASS
                    elif finding.severity == Severity.BLOCKER:
                        result = ValidationResult.FAIL
                    elif finding.severity == Severity.ERROR:
                        result = ValidationResult.FAIL
                    else:
                        result = ValidationResult.WARN

                    self.checks.append(
                        CheckResult(
                            name=f"lib:{finding.rule_id}",
                            result=result,
                            message=finding.message,
                            required=finding.severity
                            in [Severity.BLOCKER, Severity.ERROR],
                        )
                    )

        # Determine overall validity
        failures = [
            c for c in self.checks if c.result == ValidationResult.FAIL and c.required
        ]
        is_valid = len(failures) == 0

        return is_valid, self.checks

    def format_report(self, is_valid: bool, checks: List[CheckResult]) -> str:
        """Format validation report."""
        lines = []
        lines.append("=" * 60)
        lines.append("CLAUDE RESPONSE VALIDATION REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Summary
        status = "VALID" if is_valid else "INVALID"
        status_icon = "✅" if is_valid else "❌"
        lines.append(f"Status: {status_icon} {status}")
        lines.append("")

        # Check results
        lines.append("Checks:")
        lines.append("-" * 40)

        for check in checks:
            icon = {
                ValidationResult.PASS: "✅",
                ValidationResult.FAIL: "❌",
                ValidationResult.WARN: "⚠️",
                ValidationResult.SKIP: "⏭️",
            }[check.result]

            req = "[REQ]" if check.required else "[OPT]"
            lines.append(f"  {icon} {req} {check.name}: {check.message}")

        lines.append("")

        # Failures summary
        failures = [c for c in checks if c.result == ValidationResult.FAIL]
        if failures:
            lines.append("FAILURES:")
            lines.append("-" * 40)
            for f in failures:
                lines.append(f"  ❌ {f.message}")
            lines.append("")
            lines.append("ACTION REQUIRED:")
            lines.append("  Response must be rejected and re-requested.")

        lines.append("=" * 60)

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Validate Claude responses for AgenticVerz compliance"
    )
    parser.add_argument("file", nargs="?", help="Response file to validate")
    parser.add_argument("--stdin", action="store_true", help="Read response from stdin")
    parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Strict mode (default: true)",
    )
    parser.add_argument(
        "--lenient", action="store_true", help="Lenient mode (boot ack not required)"
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Only output VALID/INVALID"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--library", help="Path to behavior library JSON file")
    parser.add_argument(
        "--classify", action="store_true", help="Classify incident from input text"
    )

    args = parser.parse_args()

    # Incident classification mode
    if args.classify:
        if args.stdin:
            text = sys.stdin.read()
        elif args.file:
            with open(args.file, "r") as f:
                text = f.read()
        else:
            print("Provide text via --stdin or file argument")
            sys.exit(2)

        tags = classify_incident(text)
        if args.json:
            print(
                json.dumps(
                    {
                        "tags": list(tags),
                        "suggested_rules": [
                            scaffold_rule(t) for t in tags if scaffold_rule(t)
                        ],
                    },
                    indent=2,
                )
            )
        else:
            print("Incident Classification:")
            for tag in tags:
                rule = scaffold_rule(tag)
                print(f"  - {tag} → {rule}")
        sys.exit(0)

    # Read response
    if args.stdin:
        response = sys.stdin.read()
    elif args.file:
        with open(args.file, "r") as f:
            response = f.read()
    else:
        parser.print_help()
        sys.exit(2)

    # Validate
    strict = not args.lenient
    validator = ClaudeResponseValidator(
        response, strict=strict, library_path=args.library
    )
    is_valid, checks = validator.validate()

    # Output
    if args.json:
        output = {
            "valid": is_valid,
            "checks": [
                {
                    "name": c.name,
                    "result": c.result.value,
                    "message": c.message,
                    "required": c.required,
                }
                for c in checks
            ],
        }
        print(json.dumps(output, indent=2))
    elif args.quiet:
        print("VALID" if is_valid else "INVALID")
    else:
        report = validator.format_report(is_valid, checks)
        print(report)

    sys.exit(0 if is_valid else 1)


if __name__ == "__main__":
    main()
