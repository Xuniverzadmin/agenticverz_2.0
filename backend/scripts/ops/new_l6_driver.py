#!/usr/bin/env python3
# Layer: L0 — Operations Script
# AUDIENCE: INTERNAL
# Role: Scaffold a new L6 driver with correct headers and structure
# Reference: PIN-509 Gap 7 — Positive scaffolding

"""
L6 Driver Scaffolding Generator (PIN-509 Gap 7)

Creates a new L6 driver file with correct layer headers, audience classification,
and session-based DB access pattern.

Usage:
    python3 scripts/ops/new_l6_driver.py <domain> <driver_name>
    python3 scripts/ops/new_l6_driver.py policies enforcement_driver

Output:
    app/hoc/cus/<domain>/L6_drivers/<driver_name>.py
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
HOC_CUS = BACKEND_ROOT / "app" / "hoc" / "cus"

TEMPLATE = '''# Layer: L6 — Domain Driver
# AUDIENCE: CUSTOMER
# Role: {role}
# Temporal:
#   Trigger: engine
#   Execution: async
# Callers: {engine_caller}
# Allowed Imports: L5_schemas (types), L7 models (app.models.*), sqlalchemy
# Forbidden Imports: L5_engines, L2, L4, app.db
# Reference: PIN-509 scaffolding

"""
{class_name} (PIN-509 scaffolded)

PURPOSE:
    TODO: Describe DB operations this driver provides.

INTERFACE:
    - {class_name}
    - get_{factory_name}(session) -> {class_name}
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class {class_name}:
    """{class_name} — L6 DB driver.

    Owns session. Implements Protocol defined in L5_schemas.
    """

    def __init__(self, session: "AsyncSession") -> None:
        self._session = session


def get_{factory_name}(session: "AsyncSession") -> {class_name}:
    """Get {class_name} instance."""
    return {class_name}(session)


__all__ = [
    "{class_name}",
    "get_{factory_name}",
]
'''


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/ops/new_l6_driver.py <domain> <driver_name>")
        print("  e.g. python3 scripts/ops/new_l6_driver.py policies enforcement_driver")
        sys.exit(1)

    domain = sys.argv[1]
    driver_name = sys.argv[2].removesuffix(".py")

    domain_dir = HOC_CUS / domain / "L6_drivers"
    if not domain_dir.exists():
        print(f"ERROR: Domain directory does not exist: {domain_dir}")
        sys.exit(1)

    target = domain_dir / f"{driver_name}.py"
    if target.exists():
        print(f"ERROR: File already exists: {target}")
        sys.exit(1)

    parts = driver_name.replace("_driver", "").split("_")
    class_name = "".join(p.capitalize() for p in parts) + "Driver"
    factory_name = driver_name
    engine_caller = f"{domain}/L5_engines (via Protocol injection)"
    role = f"{class_name} — TODO describe DB operations"

    content = TEMPLATE.format(
        role=role,
        class_name=class_name,
        factory_name=factory_name,
        engine_caller=engine_caller,
    )

    target.write_text(content)
    print(f"Created: {target.relative_to(BACKEND_ROOT)}")
    print(f"  Class: {class_name}")
    print(f"  Factory: get_{factory_name}()")
    print(f"\nNext steps:")
    print(f"  1. Implement DB operations matching L5 Protocol")
    print(f"  2. Register in domain SOFTWARE_BIBLE.md")


if __name__ == "__main__":
    main()
