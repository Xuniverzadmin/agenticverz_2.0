# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Repository File Walker
# Authority: None (observational only)
# Callers: semantic_auditor.runner
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Repository Walker

Walks the repository and filters executable Python files for analysis.
Respects common ignore patterns (venv, __pycache__, etc.).
"""

from pathlib import Path
from typing import Iterator, Set, Optional, List
import os


class RepoWalker:
    """Walks a repository and yields Python files for analysis."""

    # Directories to skip during traversal
    DEFAULT_IGNORE_DIRS: Set[str] = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        "node_modules",
        ".tox",
        "dist",
        "build",
        "*.egg-info",
        ".eggs",
    }

    # File patterns to skip
    DEFAULT_IGNORE_FILES: Set[str] = {
        "conftest.py",
    }

    def __init__(
        self,
        root_path: str,
        ignore_dirs: Optional[Set[str]] = None,
        ignore_files: Optional[Set[str]] = None,
    ):
        """
        Initialize the repository walker.

        Args:
            root_path: Root directory to start walking from
            ignore_dirs: Additional directories to ignore (merged with defaults)
            ignore_files: Additional files to ignore (merged with defaults)
        """
        self.root_path = Path(root_path).resolve()
        self.ignore_dirs = self.DEFAULT_IGNORE_DIRS.copy()
        self.ignore_files = self.DEFAULT_IGNORE_FILES.copy()

        if ignore_dirs:
            self.ignore_dirs.update(ignore_dirs)
        if ignore_files:
            self.ignore_files.update(ignore_files)

    def _should_ignore_dir(self, dir_path: Path) -> bool:
        """Check if a directory should be ignored."""
        dir_name = dir_path.name
        return dir_name in self.ignore_dirs or dir_name.startswith(".")

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if a file should be ignored."""
        return file_path.name in self.ignore_files

    def _is_python_file(self, file_path: Path) -> bool:
        """Check if a file is a Python file."""
        return file_path.suffix == ".py" and file_path.is_file()

    def walk(self) -> Iterator[Path]:
        """
        Walk the repository and yield Python file paths.

        Yields:
            Path objects for each Python file found
        """
        if not self.root_path.exists():
            return

        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)

            # Filter out ignored directories (modify in place to prevent descent)
            dirs[:] = [
                d for d in dirs if not self._should_ignore_dir(root_path / d)
            ]

            # Sort for deterministic ordering
            dirs.sort()
            files.sort()

            for file_name in files:
                file_path = root_path / file_name
                if self._is_python_file(file_path) and not self._should_ignore_file(
                    file_path
                ):
                    yield file_path

    def walk_domain(self, domain: str) -> Iterator[Path]:
        """
        Walk only files in a specific domain directory.

        Args:
            domain: Domain name to filter by (e.g., 'auth', 'billing')

        Yields:
            Path objects for each Python file in the domain
        """
        domain_path = self.root_path / domain
        if not domain_path.exists():
            # Try looking in common locations
            for subdir in ["app", "src"]:
                alt_path = self.root_path / subdir / domain
                if alt_path.exists():
                    domain_path = alt_path
                    break

        if not domain_path.exists():
            return

        original_root = self.root_path
        self.root_path = domain_path
        try:
            yield from self.walk()
        finally:
            self.root_path = original_root

    def walk_changed_since(
        self, since: str, changed_files: Optional[List[str]] = None
    ) -> Iterator[Path]:
        """
        Walk only files changed since a given reference.

        In Phase 1, this is a simplified implementation that accepts
        a list of changed files directly. Future phases may integrate
        with git directly.

        Args:
            since: Reference point (commit hash, tag, or date)
            changed_files: Optional list of changed file paths

        Yields:
            Path objects for changed Python files
        """
        if changed_files is None:
            # In Phase 1, we don't integrate with git directly
            # Return all files as a fallback
            yield from self.walk()
            return

        for file_str in changed_files:
            file_path = Path(file_str)
            if not file_path.is_absolute():
                file_path = self.root_path / file_path

            if self._is_python_file(file_path) and file_path.exists():
                yield file_path

    def get_file_count(self) -> int:
        """Return the total count of Python files."""
        return sum(1 for _ in self.walk())

    def get_relative_path(self, file_path: Path) -> Path:
        """Get the relative path of a file from the root."""
        try:
            return file_path.relative_to(self.root_path)
        except ValueError:
            return file_path
