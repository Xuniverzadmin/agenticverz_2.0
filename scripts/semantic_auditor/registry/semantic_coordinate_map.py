# Layer: L8 - Catalyst / Meta
# Product: system-wide
# Temporal:
#   Trigger: cli|scheduled
#   Execution: sync
# Role: Semantic Coordinate Map
# Authority: None (observational only)
# Callers: semantic_auditor.runner, semantic_auditor.correlation
# Contract: SEMANTIC_AUDITOR_ARCHITECTURE.md

"""
Semantic Coordinate Map

Maps files to their semantic coordinates:
- File -> Layer
- File -> Role
- File -> Domain

This provides the semantic location of every file in the codebase.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from ..scanner.file_classifier import FileClassifier, LayerLevel, FileRole


@dataclass
class SemanticCoordinate:
    """Semantic coordinate for a file."""

    file_path: Path
    layer: LayerLevel
    role: FileRole
    domain: Optional[str]

    def as_tuple(self) -> Tuple[str, str, Optional[str]]:
        """Return coordinates as (layer, role, domain) tuple."""
        return (self.layer.value, self.role.value, self.domain)

    def __repr__(self) -> str:
        return f"({self.layer.value}, {self.role.value}, {self.domain or 'None'})"


class SemanticCoordinateMap:
    """Maps files to their semantic coordinates."""

    def __init__(self):
        """Initialize the coordinate map."""
        self.classifier = FileClassifier()
        self._coordinates: Dict[Path, SemanticCoordinate] = {}
        self._by_layer: Dict[LayerLevel, List[Path]] = {}
        self._by_role: Dict[FileRole, List[Path]] = {}
        self._by_domain: Dict[str, List[Path]] = {}

    def map_file(self, file_path: Path) -> SemanticCoordinate:
        """
        Map a file to its semantic coordinates.

        Args:
            file_path: Path to the file

        Returns:
            SemanticCoordinate for the file
        """
        if file_path in self._coordinates:
            return self._coordinates[file_path]

        classification = self.classifier.classify(file_path)

        coordinate = SemanticCoordinate(
            file_path=file_path,
            layer=classification.layer,
            role=classification.role,
            domain=classification.domain,
        )

        self._coordinates[file_path] = coordinate
        self._index_coordinate(coordinate)

        return coordinate

    def _index_coordinate(self, coordinate: SemanticCoordinate) -> None:
        """Index a coordinate for fast lookup."""
        # Index by layer
        if coordinate.layer not in self._by_layer:
            self._by_layer[coordinate.layer] = []
        self._by_layer[coordinate.layer].append(coordinate.file_path)

        # Index by role
        if coordinate.role not in self._by_role:
            self._by_role[coordinate.role] = []
        self._by_role[coordinate.role].append(coordinate.file_path)

        # Index by domain
        if coordinate.domain:
            if coordinate.domain not in self._by_domain:
                self._by_domain[coordinate.domain] = []
            self._by_domain[coordinate.domain].append(coordinate.file_path)

    def map_files(self, file_paths: List[Path]) -> Dict[Path, SemanticCoordinate]:
        """
        Map multiple files to their coordinates.

        Args:
            file_paths: List of file paths

        Returns:
            Dict mapping paths to coordinates
        """
        for file_path in file_paths:
            self.map_file(file_path)

        return self._coordinates

    def get_coordinate(self, file_path: Path) -> Optional[SemanticCoordinate]:
        """Get the coordinate for a file."""
        return self._coordinates.get(file_path)

    def get_files_in_layer(self, layer: LayerLevel) -> List[Path]:
        """Get all files in a layer."""
        return self._by_layer.get(layer, [])

    def get_files_with_role(self, role: FileRole) -> List[Path]:
        """Get all files with a role."""
        return self._by_role.get(role, [])

    def get_files_in_domain(self, domain: str) -> List[Path]:
        """Get all files in a domain."""
        return self._by_domain.get(domain, [])

    def get_all_layers(self) -> Set[LayerLevel]:
        """Get all layers that have files."""
        return set(self._by_layer.keys())

    def get_all_domains(self) -> Set[str]:
        """Get all domains that have files."""
        return set(self._by_domain.keys())

    def get_layer_summary(self) -> Dict[str, int]:
        """Get count of files per layer."""
        return {layer.value: len(files) for layer, files in self._by_layer.items()}

    def get_domain_summary(self) -> Dict[str, int]:
        """Get count of files per domain."""
        return {domain: len(files) for domain, files in self._by_domain.items()}

    def clear(self) -> None:
        """Clear all mappings."""
        self._coordinates.clear()
        self._by_layer.clear()
        self._by_role.clear()
        self._by_domain.clear()
