#!/usr/bin/env python3
# Layer: L0 — Operations Script
# AUDIENCE: INTERNAL
# Role: Scaffold a new L5 engine with correct headers and structure
# Reference: PIN-509 Gap 7 — Positive scaffolding

"""
L5 Engine Scaffolding Generator (PIN-509 Gap 7)

Creates a new L5 engine file with correct layer headers, audience classification,
import constraints, and Protocol-based constructor injection pattern.

Usage:
    python3 scripts/ops/new_l5_engine.py <domain> <engine_name>
    python3 scripts/ops/new_l5_engine.py policies enforcement_engine

Output:
    app/hoc/cus/<domain>/L5_engines/<engine_name>.py
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
HOC_CUS = BACKEND_ROOT / "app" / "hoc" / "cus"

TEMPLATE = '''# Layer: L5 — Domain Engine
# AUDIENCE: CUSTOMER
# Role: {role}
# Temporal:
#   Trigger: api
#   Execution: async
# Callers: TODO — declare L4 handler or L2 API caller
# Allowed Imports: L5_schemas (same domain), L6 drivers (via Protocol injection)
# Forbidden Imports: L1, L2, L3, sqlalchemy direct, Session, other domain L6_drivers
# Reference: PIN-509 scaffolding

"""
{class_name} (PIN-509 scaffolded)

PURPOSE:
    TODO: Describe domain-specific purpose.

INTERFACE:
    - {class_name}
    - get_{factory_name}() -> {class_name}

IMPLEMENTATION STATUS:
    Scaffolded. Ready for implementation.
"""

from typing import Any, Protocol


class {class_name}DriverProtocol(Protocol):
    """L6 driver Protocol — define required operations here."""
    ...


class {class_name}:
    """{class_name} — domain engine.

    Accepts L6 driver via Protocol injection. Never receives Session.
    """

    def __init__(self, *, driver: {class_name}DriverProtocol) -> None:
        self._driver = driver


_instance: {class_name} | None = None


def get_{factory_name}(*, driver: {class_name}DriverProtocol) -> {class_name}:
    """Get {class_name} instance with injected driver."""
    return {class_name}(driver=driver)


__all__ = [
    "{class_name}",
    "{class_name}DriverProtocol",
    "get_{factory_name}",
]
'''


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/ops/new_l5_engine.py <domain> <engine_name>")
        print("  e.g. python3 scripts/ops/new_l5_engine.py policies enforcement_engine")
        sys.exit(1)

    domain = sys.argv[1]
    engine_name = sys.argv[2].removesuffix(".py")

    domain_dir = HOC_CUS / domain / "L5_engines"
    if not domain_dir.exists():
        print(f"ERROR: Domain directory does not exist: {domain_dir}")
        sys.exit(1)

    target = domain_dir / f"{engine_name}.py"
    if target.exists():
        print(f"ERROR: File already exists: {target}")
        sys.exit(1)

    # Convert engine_name to class name: foo_bar_engine -> FooBarEngine
    parts = engine_name.replace("_engine", "").split("_")
    class_name = "".join(p.capitalize() for p in parts) + "Engine"
    factory_name = engine_name

    role = f"{class_name} — TODO describe purpose"

    content = TEMPLATE.format(
        role=role,
        class_name=class_name,
        factory_name=factory_name,
    )

    target.write_text(content)
    print(f"Created: {target.relative_to(BACKEND_ROOT)}")
    print(f"  Class: {class_name}")
    print(f"  Factory: get_{factory_name}()")
    print(f"\nNext steps:")
    print(f"  1. Define driver Protocol methods")
    print(f"  2. Create matching L6 driver: scripts/ops/new_l6_driver.py {domain} {engine_name.replace('_engine', '_driver')}")
    print(f"  3. Register in domain SOFTWARE_BIBLE.md")


if __name__ == "__main__":
    main()
