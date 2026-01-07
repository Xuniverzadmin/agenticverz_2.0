#!/usr/bin/env python3
"""
Golden File Archival and Key Rotation Tool

Features:
1. Archive golden files older than N days to S3/local archive
2. Re-sign golden files with new secret key
3. Verify golden file integrity
4. Cleanup orphaned signature files

Usage:
    # Archive files older than 90 days
    python golden_archival.py archive --days 90 --dest s3://bucket/archive/

    # Re-sign all golden files with new key
    python golden_archival.py resign --new-secret $NEW_SECRET

    # Verify all golden files
    python golden_archival.py verify

    # Cleanup orphaned .sig files
    python golden_archival.py cleanup
"""

import argparse
import hashlib
import hmac
import logging
import os
import shutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Default paths
DEFAULT_GOLDEN_DIR = os.getenv("GOLDEN_DIR", "/var/lib/aos/golden")
DEFAULT_ARCHIVE_DIR = os.getenv("GOLDEN_ARCHIVE_DIR", "/var/lib/aos/golden-archive")
GOLDEN_SECRET = os.getenv("GOLDEN_SECRET", "")


class GoldenArchiver:
    """Handles golden file archival and key rotation."""

    def __init__(self, golden_dir: str, secret: str):
        self.golden_dir = Path(golden_dir)
        self.secret = secret

    def list_golden_files(self, older_than_days: Optional[int] = None) -> List[Path]:
        """List all golden .jsonl files, optionally filtered by age."""
        if not self.golden_dir.exists():
            return []

        files = list(self.golden_dir.glob("**/*.jsonl"))

        if older_than_days is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
            files = [f for f in files if datetime.fromtimestamp(f.stat().st_mtime, timezone.utc) < cutoff]

        return sorted(files)

    def compute_signature(self, filepath: Path) -> str:
        """Compute HMAC-SHA256 signature for a file."""
        with open(filepath, "rb") as f:
            data = f.read()
        return hmac.new(self.secret.encode(), data, hashlib.sha256).hexdigest()

    def verify_file(self, filepath: Path) -> Tuple[bool, str]:
        """
        Verify a golden file's signature.

        Returns:
            (valid, message) tuple
        """
        sig_path = Path(str(filepath) + ".sig")

        if not sig_path.exists():
            return False, f"Missing signature file: {sig_path}"

        with open(sig_path, "r") as f:
            stored_sig = f.read().strip()

        computed_sig = self.compute_signature(filepath)

        if stored_sig == computed_sig:
            return True, "Valid"
        else:
            return False, f"Signature mismatch (stored={stored_sig[:16]}..., computed={computed_sig[:16]}...)"

    def sign_file(self, filepath: Path, new_secret: Optional[str] = None) -> str:
        """
        Sign a golden file, optionally with a new secret.

        Returns:
            The signature that was written
        """
        secret = new_secret or self.secret

        with open(filepath, "rb") as f:
            data = f.read()

        sig = hmac.new(secret.encode(), data, hashlib.sha256).hexdigest()

        sig_path = Path(str(filepath) + ".sig")
        tmp_sig_path = Path(str(sig_path) + ".tmp")

        # Atomic write
        with open(tmp_sig_path, "w") as f:
            f.write(sig)
        os.replace(tmp_sig_path, sig_path)

        return sig

    def archive_files(self, files: List[Path], dest_dir: str, delete_after: bool = False) -> int:
        """
        Archive golden files to destination directory.

        Args:
            files: List of files to archive
            dest_dir: Destination directory (local path or s3:// URL)
            delete_after: Whether to delete source files after archiving

        Returns:
            Number of files archived
        """
        if dest_dir.startswith("s3://"):
            return self._archive_to_s3(files, dest_dir, delete_after)
        else:
            return self._archive_to_local(files, dest_dir, delete_after)

    def _archive_to_local(self, files: List[Path], dest_dir: str, delete_after: bool) -> int:
        """Archive to local directory."""
        dest_path = Path(dest_dir)
        dest_path.mkdir(parents=True, exist_ok=True)

        archived = 0
        for filepath in files:
            # Create month-based subdirectory
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime, timezone.utc)
            month_dir = dest_path / mtime.strftime("%Y%m")
            month_dir.mkdir(exist_ok=True)

            # Copy file and signature
            dest_file = month_dir / filepath.name
            shutil.copy2(filepath, dest_file)

            sig_path = Path(str(filepath) + ".sig")
            if sig_path.exists():
                shutil.copy2(sig_path, month_dir / sig_path.name)

            if delete_after:
                filepath.unlink()
                if sig_path.exists():
                    sig_path.unlink()

            archived += 1
            logger.info(f"Archived: {filepath.name} -> {month_dir}")

        return archived

    def _archive_to_s3(self, files: List[Path], s3_url: str, delete_after: bool) -> int:
        """Archive to S3 bucket."""
        try:
            import boto3
        except ImportError:
            logger.error("boto3 not installed. Run: pip install boto3")
            return 0

        # Parse S3 URL
        parts = s3_url.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        prefix = parts[1] if len(parts) > 1 else ""

        s3 = boto3.client("s3")
        archived = 0

        for filepath in files:
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime, timezone.utc)
            month_prefix = mtime.strftime("%Y%m")

            # Upload file
            key = f"{prefix}/{month_prefix}/{filepath.name}".lstrip("/")
            s3.upload_file(str(filepath), bucket, key)

            # Upload signature
            sig_path = Path(str(filepath) + ".sig")
            if sig_path.exists():
                sig_key = f"{prefix}/{month_prefix}/{sig_path.name}".lstrip("/")
                s3.upload_file(str(sig_path), bucket, sig_key)

            if delete_after:
                filepath.unlink()
                if sig_path.exists():
                    sig_path.unlink()

            archived += 1
            logger.info(f"Archived to S3: {filepath.name} -> s3://{bucket}/{key}")

        return archived

    def resign_all(self, new_secret: str, verify_old: bool = True) -> Tuple[int, int]:
        """
        Re-sign all golden files with a new secret.

        Args:
            new_secret: New secret key to use
            verify_old: Whether to verify with old key before re-signing

        Returns:
            (resigned_count, failed_count) tuple
        """
        files = self.list_golden_files()
        resigned = 0
        failed = 0

        for filepath in files:
            try:
                # Optionally verify with old key first
                if verify_old:
                    valid, msg = self.verify_file(filepath)
                    if not valid:
                        logger.warning(f"Skipping {filepath.name}: {msg}")
                        failed += 1
                        continue

                # Re-sign with new key
                self.sign_file(filepath, new_secret)
                resigned += 1
                logger.info(f"Re-signed: {filepath.name}")

            except Exception as e:
                logger.error(f"Failed to re-sign {filepath.name}: {e}")
                failed += 1

        return resigned, failed

    def verify_all(self) -> Tuple[int, int, List[str]]:
        """
        Verify all golden files.

        Returns:
            (valid_count, invalid_count, invalid_files) tuple
        """
        files = self.list_golden_files()
        valid = 0
        invalid = 0
        invalid_files = []

        for filepath in files:
            is_valid, msg = self.verify_file(filepath)
            if is_valid:
                valid += 1
            else:
                invalid += 1
                invalid_files.append(f"{filepath.name}: {msg}")
                logger.warning(f"Invalid: {filepath.name} - {msg}")

        return valid, invalid, invalid_files

    def cleanup_orphaned(self, dry_run: bool = True) -> List[Path]:
        """
        Find and optionally remove orphaned .sig files.

        Returns:
            List of orphaned signature files
        """
        if not self.golden_dir.exists():
            return []

        sig_files = list(self.golden_dir.glob("**/*.sig"))
        orphaned = []

        for sig_path in sig_files:
            # Check if corresponding .jsonl exists
            jsonl_path = Path(str(sig_path).replace(".sig", ""))
            if not jsonl_path.exists():
                orphaned.append(sig_path)
                if not dry_run:
                    sig_path.unlink()
                    logger.info(f"Removed orphaned: {sig_path.name}")
                else:
                    logger.info(f"Would remove orphaned: {sig_path.name}")

        return orphaned


def cmd_archive(args):
    """Archive command handler."""
    archiver = GoldenArchiver(args.golden_dir, GOLDEN_SECRET)

    files = archiver.list_golden_files(older_than_days=args.days)
    logger.info(f"Found {len(files)} files older than {args.days} days")

    if not files:
        logger.info("No files to archive")
        return 0

    if args.dry_run:
        for f in files:
            logger.info(f"Would archive: {f.name}")
        return 0

    archived = archiver.archive_files(files, args.dest, delete_after=args.delete)
    logger.info(f"Archived {archived} files to {args.dest}")
    return 0


def cmd_resign(args):
    """Resign command handler."""
    if not args.new_secret:
        logger.error("--new-secret is required")
        return 1

    archiver = GoldenArchiver(args.golden_dir, GOLDEN_SECRET)

    if args.dry_run:
        files = archiver.list_golden_files()
        logger.info(f"Would re-sign {len(files)} files")
        return 0

    resigned, failed = archiver.resign_all(args.new_secret, verify_old=not args.skip_verify)

    logger.info(f"Re-signed: {resigned}, Failed: {failed}")
    return 0 if failed == 0 else 1


def cmd_verify(args):
    """Verify command handler."""
    archiver = GoldenArchiver(args.golden_dir, GOLDEN_SECRET)

    valid, invalid, invalid_files = archiver.verify_all()

    logger.info(f"Valid: {valid}, Invalid: {invalid}")

    if invalid > 0:
        logger.error("Invalid files:")
        for f in invalid_files:
            logger.error(f"  {f}")
        return 1

    return 0


def cmd_cleanup(args):
    """Cleanup command handler."""
    archiver = GoldenArchiver(args.golden_dir, GOLDEN_SECRET)

    orphaned = archiver.cleanup_orphaned(dry_run=args.dry_run)

    if orphaned:
        action = "Would remove" if args.dry_run else "Removed"
        logger.info(f"{action} {len(orphaned)} orphaned signature files")
    else:
        logger.info("No orphaned signature files found")

    return 0


def main():
    parser = argparse.ArgumentParser(description="Golden file archival and key rotation tool")
    parser.add_argument(
        "--golden-dir", default=DEFAULT_GOLDEN_DIR, help=f"Golden files directory (default: {DEFAULT_GOLDEN_DIR})"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Archive command
    archive_parser = subparsers.add_parser("archive", help="Archive old golden files")
    archive_parser.add_argument("--days", type=int, default=90, help="Archive files older than N days")
    archive_parser.add_argument("--dest", default=DEFAULT_ARCHIVE_DIR, help="Destination directory or S3 URL")
    archive_parser.add_argument("--delete", action="store_true", help="Delete source files after archiving")
    archive_parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    archive_parser.set_defaults(func=cmd_archive)

    # Resign command
    resign_parser = subparsers.add_parser("resign", help="Re-sign golden files with new key")
    resign_parser.add_argument("--new-secret", help="New secret key (or set NEW_GOLDEN_SECRET env)")
    resign_parser.add_argument("--skip-verify", action="store_true", help="Skip verification with old key")
    resign_parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    resign_parser.set_defaults(func=cmd_resign)

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify all golden files")
    verify_parser.set_defaults(func=cmd_verify)

    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Remove orphaned signature files")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    cleanup_parser.set_defaults(func=cmd_cleanup)

    args = parser.parse_args()

    # Handle NEW_GOLDEN_SECRET env for resign
    if args.command == "resign" and not args.new_secret:
        args.new_secret = os.getenv("NEW_GOLDEN_SECRET")

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
