#!/usr/bin/env python3
"""
AgenticVerz — Incident Classifier

Converts incidents into behavior library rules.
Follows the Incident → Rule conversion template from CLAUDE_BEHAVIOR_LIBRARY.md.

Usage:
    # Interactive mode
    python incident_classifier.py

    # Create rule from incident description
    python incident_classifier.py classify "Description of what happened"

    # Generate rule YAML from incident details
    python incident_classifier.py generate --incident-file incident.json

Reference: CLAUDE_BEHAVIOR_LIBRARY.md
"""

import json
import argparse
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class IncidentClass(Enum):
    """Known incident classes."""

    ENVIRONMENT_DRIFT = "environment_drift"
    TIMEZONE_MISMATCH = "timezone_mismatch"
    AUTH_MISMATCH = "auth_mismatch"
    MIGRATION_FORK = "migration_fork"
    SERVICE_NAME_MISMATCH = "service_name_mismatch"
    TEST_PREREQUISITES = "test_prerequisites"
    SCHEMA_ASSUMPTION = "schema_assumption"
    RBAC_BLOCKING = "rbac_blocking"
    CONTAINER_STALE = "container_stale"
    UNKNOWN = "unknown"


class Severity(Enum):
    """Rule severity levels."""

    BLOCKING = "BLOCKING"
    WARNING = "WARNING"


@dataclass
class Incident:
    """Represents a classified incident."""

    date: str
    description: str
    root_cause: str
    time_wasted: str
    incident_class: IncidentClass

    # Prevention details
    trigger: str
    check: str
    output: str

    # Optional
    error_message: Optional[str] = None
    endpoint: Optional[str] = None
    table: Optional[str] = None


@dataclass
class BehaviorRule:
    """Generated behavior rule."""

    id: str
    name: str
    incident_class: str
    severity: Severity
    triggers: List[str]
    requires: List[dict]
    forbid: List[str]
    violation_type: str
    violation_message: str
    violation_action: str
    output_required: str


# Incident classification patterns
CLASSIFICATION_PATTERNS = {
    IncidentClass.ENVIRONMENT_DRIFT: [
        r"container.*not.*rebuild",
        r"old.*code.*running",
        r"changes.*not.*deployed",
        r"docker.*stale",
        r"runtime.*drift",
    ],
    IncidentClass.TIMEZONE_MISMATCH: [
        r"timezone",
        r"aware.*naive",
        r"offset.*datetime",
        r"utc.*mismatch",
        r"timestamp.*without.*time.*zone",
    ],
    IncidentClass.AUTH_MISMATCH: [
        r"401",
        r"403",
        r"unauthorized",
        r"forbidden",
        r"auth.*header",
        r"rbac.*block",
        r"permission.*denied",
    ],
    IncidentClass.MIGRATION_FORK: [
        r"multiple.*head",
        r"migration.*fork",
        r"alembic.*conflict",
        r"revision.*branch",
    ],
    IncidentClass.SERVICE_NAME_MISMATCH: [
        r"service.*name.*container",
        r"wrong.*service",
        r"compose.*name",
    ],
    IncidentClass.TEST_PREREQUISITES: [
        r"test.*fail.*prerequisite",
        r"database.*not.*ready",
        r"service.*not.*healthy",
    ],
}


def classify_incident(description: str) -> IncidentClass:
    """
    Classify an incident based on its description.

    Returns the most likely incident class.
    """
    import re

    description_lower = description.lower()

    scores = {}
    for inc_class, patterns in CLASSIFICATION_PATTERNS.items():
        score = 0
        for pattern in patterns:
            if re.search(pattern, description_lower):
                score += 1
        if score > 0:
            scores[inc_class] = score

    if not scores:
        return IncidentClass.UNKNOWN

    return max(scores.keys(), key=lambda k: scores[k])


def get_next_rule_id(incident_class: IncidentClass) -> str:
    """
    Generate the next rule ID for the given incident class.

    Format: BL-XXX-NNN where XXX is class prefix and NNN is number.
    """
    # Map incident class to prefix
    prefix_map = {
        IncidentClass.ENVIRONMENT_DRIFT: "ENV",
        IncidentClass.TIMEZONE_MISMATCH: "DB",
        IncidentClass.AUTH_MISMATCH: "AUTH",
        IncidentClass.MIGRATION_FORK: "MIG",
        IncidentClass.SERVICE_NAME_MISMATCH: "DOCKER",
        IncidentClass.TEST_PREREQUISITES: "TEST",
        IncidentClass.SCHEMA_ASSUMPTION: "SCHEMA",
        IncidentClass.RBAC_BLOCKING: "RBAC",
        IncidentClass.CONTAINER_STALE: "CONT",
        IncidentClass.UNKNOWN: "UNK",
    }

    prefix = prefix_map.get(incident_class, "UNK")

    # TODO: Read existing rules to determine next number
    # For now, return placeholder
    return f"BL-{prefix}-NNN"


def generate_rule_yaml(incident: Incident) -> str:
    """
    Generate YAML rule definition from an incident.
    """
    rule_id = get_next_rule_id(incident.incident_class)

    yaml = f"""# New Rule Template
id: {rule_id}
name: <Descriptive Name>
class: {incident.incident_class.value}
severity: BLOCKING

# What was the incident?
incident:
  date: {incident.date}
  description: {incident.description}
  root_cause: {incident.root_cause}
  time_wasted: {incident.time_wasted}

# What would have prevented it?
prevention:
  trigger: {incident.trigger}
  check: {incident.check}
  output: {incident.output}

# Structured rule
triggers:
  - <condition 1>
  - <condition 2>

requires:
  - step_1:
      action: "<action>"
      command: "<command>"
      reason: "<reason>"

forbid:
  - <forbidden action 1>
  - <forbidden action 2>

violation:
  type: BLOCKING
  message: "{rule_id} VIOLATION: <description>"
  action: "STOP. <what to do>"

output_required: |
  <SECTION NAME> CHECK
  - Field 1: <value>
  - Field 2: <value>
"""
    return yaml


def interactive_classify():
    """
    Interactive incident classification.
    """
    print("=" * 60)
    print("INCIDENT CLASSIFIER — Convert incidents to behavior rules")
    print("=" * 60)
    print()

    # Get incident details
    print("Describe the incident (what went wrong):")
    description = input("> ").strip()

    if not description:
        print("No description provided. Exiting.")
        return

    # Classify
    incident_class = classify_incident(description)
    print()
    print(f"Classified as: {incident_class.value}")
    print()

    # Get more details
    print("What was the root cause?")
    root_cause = input("> ").strip()

    print("How much time was wasted debugging?")
    time_wasted = input("> ").strip()

    print("What should trigger this rule in the future?")
    trigger = input("> ").strip()

    print("What check would have prevented this?")
    check = input("> ").strip()

    print("What output should Claude provide to prove compliance?")
    output = input("> ").strip()

    # Create incident
    incident = Incident(
        date=datetime.now().strftime("%Y-%m-%d"),
        description=description,
        root_cause=root_cause,
        time_wasted=time_wasted,
        incident_class=incident_class,
        trigger=trigger,
        check=check,
        output=output,
    )

    # Generate rule
    print()
    print("=" * 60)
    print("GENERATED RULE YAML")
    print("=" * 60)
    print()
    print(generate_rule_yaml(incident))
    print()
    print("=" * 60)
    print("Next steps:")
    print("1. Review and refine the generated YAML")
    print("2. Add specific trigger patterns and required steps")
    print("3. Add to CLAUDE_BEHAVIOR_LIBRARY.md")
    print("4. Update claude_response_validator.py if needed")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Classify incidents and generate behavior rules"
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["classify", "generate", "interactive"],
        default="interactive",
        help="Command to run",
    )
    parser.add_argument(
        "description", nargs="?", help="Incident description (for classify command)"
    )
    parser.add_argument(
        "--incident-file", help="JSON file with incident details (for generate command)"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command == "classify" and args.description:
        incident_class = classify_incident(args.description)
        if args.json:
            print(
                json.dumps(
                    {
                        "description": args.description,
                        "class": incident_class.value,
                    },
                    indent=2,
                )
            )
        else:
            print(f"Incident Class: {incident_class.value}")
            print(f"Suggested Rule ID: {get_next_rule_id(incident_class)}")

    elif args.command == "generate" and args.incident_file:
        with open(args.incident_file, "r") as f:
            data = json.load(f)
        incident = Incident(
            date=data.get("date", datetime.now().strftime("%Y-%m-%d")),
            description=data["description"],
            root_cause=data["root_cause"],
            time_wasted=data.get("time_wasted", "unknown"),
            incident_class=IncidentClass(data.get("class", "unknown")),
            trigger=data.get("trigger", ""),
            check=data.get("check", ""),
            output=data.get("output", ""),
        )
        print(generate_rule_yaml(incident))

    else:
        interactive_classify()


if __name__ == "__main__":
    main()
