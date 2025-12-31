# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Semantic Contract Index
# Authority: None (observational only)
# Callers: semantic_auditor.runner, semantic_auditor.correlation
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Semantic Contract Index

Maintains an index of all semantic contracts in the codebase.
Knows which contracts exist and which domains are frozen.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import re


@dataclass
class ContractEntry:
    """An entry in the contract index."""

    name: str
    file_path: Path
    domain: Optional[str] = None
    layer: Optional[str] = None
    is_frozen: bool = False
    is_draft: bool = False
    last_modified: Optional[str] = None


class SemanticContractIndex:
    """Index of semantic contracts in the codebase."""

    # Pattern to find contract files
    CONTRACT_FILE_PATTERNS = [
        "**/CONTRACT*.md",
        "**/*_CONTRACT.md",
        "**/SEMANTIC_*.md",
    ]

    def __init__(self, docs_root: Optional[Path] = None):
        """
        Initialize the contract index.

        Args:
            docs_root: Root directory for documentation
        """
        self.docs_root = docs_root
        self._contracts: Dict[str, ContractEntry] = {}
        self._frozen_domains: Set[str] = set()

    def scan(self, root_path: Optional[Path] = None) -> None:
        """
        Scan for contract files and build the index.

        Args:
            root_path: Root path to scan (defaults to docs_root)
        """
        scan_path = root_path or self.docs_root
        if not scan_path or not scan_path.exists():
            return

        for pattern in self.CONTRACT_FILE_PATTERNS:
            for contract_file in scan_path.glob(pattern):
                self._index_contract(contract_file)

    def _index_contract(self, file_path: Path) -> None:
        """Index a single contract file."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except (IOError, UnicodeDecodeError):
            return

        entry = ContractEntry(
            name=file_path.stem,
            file_path=file_path,
        )

        # Parse contract metadata
        for line in content.split("\n"):
            line_lower = line.lower()

            # Extract domain
            if "domain:" in line_lower:
                match = re.search(r"domain:\s*(\w+)", line, re.IGNORECASE)
                if match:
                    entry.domain = match.group(1)

            # Extract layer
            if "layer:" in line_lower:
                match = re.search(r"layer:\s*(L\d+)", line, re.IGNORECASE)
                if match:
                    entry.layer = match.group(1)

            # Check for frozen status
            if "frozen" in line_lower or "locked" in line_lower:
                if "status:" in line_lower or "state:" in line_lower:
                    entry.is_frozen = True

            # Check for draft status
            if "draft" in line_lower:
                if "status:" in line_lower or "state:" in line_lower:
                    entry.is_draft = True

        self._contracts[entry.name] = entry

        if entry.is_frozen and entry.domain:
            self._frozen_domains.add(entry.domain)

    def get_contract(self, name: str) -> Optional[ContractEntry]:
        """Get a contract by name."""
        return self._contracts.get(name)

    def get_all_contracts(self) -> List[ContractEntry]:
        """Get all indexed contracts."""
        return list(self._contracts.values())

    def get_contracts_for_domain(self, domain: str) -> List[ContractEntry]:
        """Get all contracts for a domain."""
        return [
            c for c in self._contracts.values()
            if c.domain == domain
        ]

    def get_frozen_domains(self) -> Set[str]:
        """Get set of frozen domains."""
        return self._frozen_domains.copy()

    def is_domain_frozen(self, domain: str) -> bool:
        """Check if a domain is frozen."""
        return domain in self._frozen_domains

    def get_contracts_for_layer(self, layer: str) -> List[ContractEntry]:
        """Get all contracts for a layer."""
        return [
            c for c in self._contracts.values()
            if c.layer == layer
        ]

    def get_active_contracts(self) -> List[ContractEntry]:
        """Get all non-draft contracts."""
        return [
            c for c in self._contracts.values()
            if not c.is_draft
        ]

    def clear(self) -> None:
        """Clear the index."""
        self._contracts.clear()
        self._frozen_domains.clear()
