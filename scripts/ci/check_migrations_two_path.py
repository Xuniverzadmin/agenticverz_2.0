#!/usr/bin/env python3
"""
CI guard: two-path migration validation.

Path A: clean DB -> `alembic upgrade head`
Path B: ORM bootstrap (init_db) -> `alembic stamp head`

Requires:
  - DATABASE_URL
  - DB_ROLE=staging

Outputs:
  - Pass/fail with head verification for both paths.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from sqlalchemy import create_engine, text


def _mask_url(url: str) -> str:
    if "@" not in url:
        return url
    prefix, rest = url.split("@", 1)
    if ":" in prefix:
        prefix = prefix.rsplit(":", 1)[0]
    return f"{prefix}:****@{rest}"


def _parse_db_name(url: str) -> str:
    parsed = urlparse(url)
    dbname = parsed.path.lstrip("/")
    if not dbname:
        raise RuntimeError("DATABASE_URL must include a database name")
    return dbname


def _build_url(url: str, dbname: str) -> str:
    parsed = urlparse(url)
    new_path = f"/{dbname}"
    rebuilt = parsed._replace(path=new_path)
    return urlunparse(rebuilt)


def _admin_url(url: str) -> str:
    return _build_url(url, "postgres")


def _safe_db_name(name: str) -> str:
    if not re.match(r"^[a-zA-Z0-9_]+$", name):
        raise RuntimeError(f"Unsafe database name: {name}")
    return name


def _run(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    result = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")


def _get_head_revision(cwd: Path, env: dict[str, str]) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "heads", "-q"],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise RuntimeError("Failed to get alembic heads")
    heads = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(heads) != 1:
        raise RuntimeError(f"Expected 1 head, found {len(heads)}: {heads}")
    return heads[0]


def _get_current_revision(cwd: Path, env: dict[str, str]) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "current", "-q"],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise RuntimeError("Failed to get alembic current")

    output = result.stdout.strip()
    # Common formats: "<rev>" or "Rev: <rev>" or "<rev> (head)"
    match = re.search(r"Rev:\s*([A-Za-z0-9_]+)", output)
    if match:
        return match.group(1)
    match = re.search(r"^([A-Za-z0-9_]+)(\s|$)", output)
    if match:
        return match.group(1)
    raise RuntimeError(f"Could not parse current revision from output: {output}")


def _create_db(conn, name: str) -> None:
    _safe_db_name(name)
    conn.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = :name"), {"name": name})
    conn.execute(text(f"DROP DATABASE IF EXISTS {name}"))
    conn.execute(text(f"CREATE DATABASE {name}"))


def _drop_db(conn, name: str) -> None:
    _safe_db_name(name)
    conn.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = :name"), {"name": name})
    conn.execute(text(f"DROP DATABASE IF EXISTS {name}"))


def main() -> int:
    database_url = os.getenv("DATABASE_URL", "")
    db_role = os.getenv("DB_ROLE", "")

    if not database_url:
        raise SystemExit("DATABASE_URL is required")
    if db_role != "staging":
        raise SystemExit("DB_ROLE must be 'staging' for CI migration checks")

    repo_root = Path(__file__).resolve().parents[2]
    backend_dir = repo_root / "backend"

    base_db = _parse_db_name(database_url)
    suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    base_prefix = base_db[:24]
    db_a = f"{base_prefix}_ci_a_{suffix}"
    db_b = f"{base_prefix}_ci_b_{suffix}"

    admin_url = _admin_url(database_url)
    engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    print("Two-path migration check (CI)")
    print(f"Admin URL: {_mask_url(admin_url)}")

    keep = os.getenv("KEEP_CI_MIGRATION_DBS", "false").lower() == "true"

    try:
        with engine.connect() as conn:
            _create_db(conn, db_a)
            _create_db(conn, db_b)

        env_common = os.environ.copy()
        env_common["DB_ROLE"] = "staging"
        env_common.setdefault("DB_AUTHORITY", "local")
        env_common.setdefault("PYTHONPATH", ".")

        head_rev = _get_head_revision(backend_dir, env_common)
        print(f"Head revision: {head_rev}")

        # Path A: clean DB -> alembic upgrade head
        env_a = env_common.copy()
        env_a["DATABASE_URL"] = _build_url(database_url, db_a)
        print(f"Path A DB: {_mask_url(env_a['DATABASE_URL'])}")
        _run([sys.executable, "-m", "alembic", "upgrade", "head"], backend_dir, env_a)
        current_a = _get_current_revision(backend_dir, env_a)
        if current_a != head_rev:
            raise RuntimeError(f"Path A revision mismatch: {current_a} != {head_rev}")

        # Path B: ORM bootstrap -> alembic stamp head
        env_b = env_common.copy()
        env_b["DATABASE_URL"] = _build_url(database_url, db_b)
        print(f"Path B DB: {_mask_url(env_b['DATABASE_URL'])}")
        _run([sys.executable, "-c", "from app.db import init_db; init_db()"], backend_dir, env_b)
        _run([sys.executable, "-m", "alembic", "stamp", "head"], backend_dir, env_b)
        current_b = _get_current_revision(backend_dir, env_b)
        if current_b != head_rev:
            raise RuntimeError(f"Path B revision mismatch: {current_b} != {head_rev}")

        print("Two-path migration check: PASS")
        return 0

    finally:
        if keep:
            print("KEEP_CI_MIGRATION_DBS=true — preserving temp DBs")
        else:
            try:
                with engine.connect() as conn:
                    _drop_db(conn, db_a)
                    _drop_db(conn, db_b)
            except Exception as drop_err:
                print(f"Warning: failed to drop temp DBs: {drop_err}")
        # Do not swallow exceptions; let failures propagate.


if __name__ == "__main__":
    raise SystemExit(main())
