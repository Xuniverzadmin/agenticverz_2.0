"""
Feature Flag File↔DB Sync Shim

Provides bi-directional sync between file-based feature_flags.json and DB-backed flags.
This is a transitional component for migration from file to DB storage.

Usage:
    # Sync file → DB (initial migration)
    python -m app.config.flag_sync --direction file-to-db

    # Sync DB → file (for canary compatibility)
    python -m app.config.flag_sync --direction db-to-file

    # Check consistency
    python -m app.config.flag_sync --check-only

Design:
    - Uses advisory locks to prevent concurrent modifications
    - Maintains source field to track origin of each flag
    - Creates audit trail of sync operations
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlmodel import Session, select
from sqlalchemy import text

logger = logging.getLogger("nova.config.flag_sync")

# Default paths
DEFAULT_FLAGS_FILE = Path(__file__).parent / "feature_flags.json"


def get_db_session():
    """Get database session."""
    from app.db import engine
    return Session(engine)


def read_file_flags(path: Path = DEFAULT_FLAGS_FILE) -> Dict:
    """Read flags from JSON file."""
    if not path.exists():
        logger.warning(f"Flags file not found: {path}")
        return {"flags": {}, "environments": {}}

    with open(path, 'r') as f:
        return json.load(f)


def write_file_flags(flags: Dict, path: Path = DEFAULT_FLAGS_FILE) -> None:
    """Write flags to JSON file atomically."""
    import tempfile

    dir_path = path.parent
    fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            json.dump(flags, f, indent=2)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, str(path))
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


def acquire_advisory_lock(session: Session, lock_id: int = 12345) -> bool:
    """Acquire PostgreSQL advisory lock."""
    try:
        result = session.execute(text(f"SELECT pg_try_advisory_lock({lock_id})"))
        return result.scalar()
    except Exception as e:
        logger.error(f"Failed to acquire advisory lock: {e}")
        return False


def release_advisory_lock(session: Session, lock_id: int = 12345) -> None:
    """Release PostgreSQL advisory lock."""
    try:
        session.execute(text(f"SELECT pg_advisory_unlock({lock_id})"))
    except Exception as e:
        logger.warning(f"Failed to release advisory lock: {e}")


def sync_file_to_db(
    file_path: Path = DEFAULT_FLAGS_FILE,
    environment: str = "staging",
    changed_by: str = "flag_sync",
    dry_run: bool = False
) -> Tuple[int, int, List[str]]:
    """
    Sync flags from file to database.

    Returns:
        Tuple of (created_count, updated_count, errors)
    """
    from app.db import FeatureFlag

    file_data = read_file_flags(file_path)
    flags = file_data.get("flags", {})
    env_flags = file_data.get("environments", {}).get(environment, {})

    created = 0
    updated = 0
    errors = []

    if dry_run:
        logger.info("[DRY-RUN] Would sync flags to DB")
        for name, config in flags.items():
            enabled = env_flags.get(name, config.get("enabled", False))
            logger.info(f"  {name}: enabled={enabled}")
        return len(flags), 0, []

    session = get_db_session()
    try:
        if not acquire_advisory_lock(session):
            errors.append("Could not acquire advisory lock")
            return 0, 0, errors

        for name, config in flags.items():
            enabled = env_flags.get(name, config.get("enabled", False))

            # Check if flag exists
            stmt = select(FeatureFlag).where(
                FeatureFlag.name == name,
                FeatureFlag.environment == environment
            )
            result = session.exec(stmt).first()
            # Handle both Row tuple and direct model returns
            if result is None:
                existing = None
            elif hasattr(result, 'name'):  # Already a model
                existing = result
            else:  # Row tuple
                existing = result[0]

            if existing:
                # Update if different
                if existing.enabled != enabled:
                    existing.enabled = enabled
                    existing.updated_at = datetime.now(timezone.utc)
                    existing.changed_by = changed_by
                    if enabled:
                        existing.enabled_at = datetime.now(timezone.utc)
                    else:
                        existing.disabled_at = datetime.now(timezone.utc)
                    updated += 1
                    logger.info(f"Updated flag: {name} -> enabled={enabled}")
            else:
                # Create new
                new_flag = FeatureFlag(
                    name=name,
                    enabled=enabled,
                    environment=environment,
                    description=config.get("description", ""),
                    owner=config.get("owner", "platform"),
                    requires_signoff=config.get("requires_m4_signoff", False),
                    changed_by=changed_by,
                )
                if enabled:
                    new_flag.enabled_at = datetime.now(timezone.utc)
                session.add(new_flag)
                created += 1
                logger.info(f"Created flag: {name} -> enabled={enabled}")

        session.commit()
        release_advisory_lock(session)

    except Exception as e:
        session.rollback()
        errors.append(str(e))
        logger.error(f"Sync failed: {e}")
    finally:
        session.close()

    return created, updated, errors


def sync_db_to_file(
    file_path: Path = DEFAULT_FLAGS_FILE,
    environment: str = "staging",
    dry_run: bool = False
) -> Tuple[int, List[str]]:
    """
    Sync flags from database to file.

    Returns:
        Tuple of (synced_count, errors)
    """
    from app.db import FeatureFlag

    errors = []
    session = get_db_session()

    try:
        if not acquire_advisory_lock(session):
            errors.append("Could not acquire advisory lock")
            return 0, errors

        # Read current file
        file_data = read_file_flags(file_path)

        # Query DB flags
        stmt = select(FeatureFlag).where(FeatureFlag.environment == environment)
        db_flags = session.exec(stmt).all()

        synced = 0
        for flag in db_flags:
            # Update environments section
            if environment not in file_data["environments"]:
                file_data["environments"][environment] = {}

            current_value = file_data["environments"][environment].get(flag.name)
            if current_value != flag.enabled:
                file_data["environments"][environment][flag.name] = flag.enabled
                synced += 1
                logger.info(f"Synced {flag.name}: {current_value} -> {flag.enabled}")

            # Also update main flags section
            if flag.name in file_data.get("flags", {}):
                file_data["flags"][flag.name]["enabled"] = flag.enabled

        if dry_run:
            logger.info(f"[DRY-RUN] Would update {synced} flags in file")
        else:
            write_file_flags(file_data, file_path)
            logger.info(f"Wrote {synced} flag updates to {file_path}")

        release_advisory_lock(session)
        return synced, errors

    except Exception as e:
        errors.append(str(e))
        logger.error(f"Sync failed: {e}")
        return 0, errors
    finally:
        session.close()


def check_consistency(
    file_path: Path = DEFAULT_FLAGS_FILE,
    environment: str = "staging"
) -> Tuple[bool, List[str]]:
    """
    Check consistency between file and DB flags.

    Returns:
        Tuple of (is_consistent, differences)
    """
    from app.db import FeatureFlag

    differences = []
    file_data = read_file_flags(file_path)
    env_flags = file_data.get("environments", {}).get(environment, {})
    all_flags = file_data.get("flags", {})

    session = get_db_session()
    try:
        stmt = select(FeatureFlag).where(FeatureFlag.environment == environment)
        results = session.exec(stmt).all()
        # Handle both Row tuple and direct model returns
        db_flags = {}
        for r in results:
            flag = r if hasattr(r, 'name') else r[0]
            db_flags[flag.name] = flag.enabled

        # Check file flags against DB
        for name, config in all_flags.items():
            file_enabled = env_flags.get(name, config.get("enabled", False))
            db_enabled = db_flags.get(name)

            if db_enabled is None:
                differences.append(f"{name}: in file but not in DB")
            elif file_enabled != db_enabled:
                differences.append(f"{name}: file={file_enabled}, db={db_enabled}")

        # Check DB flags not in file
        for name, enabled in db_flags.items():
            if name not in all_flags:
                differences.append(f"{name}: in DB but not in file")

    except Exception as e:
        differences.append(f"Error checking consistency: {e}")
    finally:
        session.close()

    return len(differences) == 0, differences


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Feature flag file↔DB sync")
    parser.add_argument(
        "--direction",
        choices=["file-to-db", "db-to-file"],
        help="Sync direction"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check consistency without syncing"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--environment",
        default="staging",
        help="Environment to sync (default: staging)"
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=DEFAULT_FLAGS_FILE,
        help="Path to feature_flags.json"
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    if args.check_only:
        is_consistent, diffs = check_consistency(args.file, args.environment)
        if is_consistent:
            print("✓ File and DB are consistent")
            sys.exit(0)
        else:
            print("✗ Inconsistencies found:")
            for diff in diffs:
                print(f"  - {diff}")
            sys.exit(1)

    elif args.direction == "file-to-db":
        created, updated, errors = sync_file_to_db(
            args.file, args.environment, dry_run=args.dry_run
        )
        print(f"Created: {created}, Updated: {updated}")
        if errors:
            print(f"Errors: {errors}")
            sys.exit(1)

    elif args.direction == "db-to-file":
        synced, errors = sync_db_to_file(
            args.file, args.environment, dry_run=args.dry_run
        )
        print(f"Synced: {synced}")
        if errors:
            print(f"Errors: {errors}")
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
