# Instruction-Aware Embedding Composer (IAEC) v3.2
"""
Deterministic embedding combiner with 4-slot architecture:
- Instruction slot: encodes task type (summarize, extract, analyze, etc.)
- Query slot: encodes user intent
- Context slot: encodes retrieved/system context
- Temporal slot: encodes version/epoch for drift control
- Policy slot: encodes governance hierarchy

v3.2 Improvements (Production Scale Ready):
- TRANSFORM DAG MANAGER: Canonical paths, graph pruning, transitive collapsing
- CORRECTION COOLDOWN: Monotonic correction policy prevents oscillation loops
- POLICY FOLDING SOFTMAX: Normalized weights for deep stacks
- WHITENING VERSIONING: Declared in every IAEC output for audit replay

v3.1 Improvements (MN-OS Production Ready):
- TEMPORAL MEDIATION: Cross-version embedding transformation for safe mixing
- 5-LEVEL POLICY ENCODING: L0-L4 hierarchy with folding operator
- CORRECTIVE ACTION: Prescriptive mismatch resolution with confidence scores
- WHITENING PERSISTENCE: Version-locked storage for slot decorrelation
- All v3.0 features (reversibility, temporal signature, deep mismatch, self-verifier)

v3.0 Features (preserved):
- REVERSIBLE decomposition for weighted mode (stores slot basis vectors)
- Temporal signature micro-slot (32 dims) for model version drift control
- Deep mismatch detection (embedding-level cosine similarity)
- Operational policy slot encoding (deterministic hash → 32 dims)
- Self-verifier for slot integrity checking
- Full audit trail for M20 constitutional compliance

PIN-082 Enhancement: IAEC v3.2 for MN-OS
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

import numpy as np
from prometheus_client import Counter, Histogram

logger = logging.getLogger("nova.memory.iaec")

# =============================================================================
# Configuration
# =============================================================================

EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "1536"))

# v3.0: 4-slot architecture with temporal signature
# Total = instruction + query + context + temporal + policy
TEMPORAL_SLOT_SIZE = 32  # Temporal signature dimensions
POLICY_SLOT_SIZE = 32  # Policy encoding dimensions
METADATA_SLOT_SIZE = TEMPORAL_SLOT_SIZE + POLICY_SLOT_SIZE  # 64 dims for metadata

# Main content slots share remaining dimensions
CONTENT_DIMENSIONS = EMBEDDING_DIMENSIONS - METADATA_SLOT_SIZE  # 1472 for 1536-dim
SEGMENT_SIZE = CONTENT_DIMENSIONS // 3  # ~490 for each content slot

# Anti-collapse parameters
VALUE_CLAMP_MIN = -3.0
VALUE_CLAMP_MAX = 3.0
MIN_VECTOR_NORM = 0.1
COLLAPSE_THRESHOLD = 0.95

# Mismatch detection (v3.0: embedding-driven threshold)
MISMATCH_THRESHOLD = 0.3  # Cosine similarity below this = mismatch
DEEP_MISMATCH_THRESHOLD = 0.5  # For embedding-based detection
CORRECTIVE_ACTION_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for corrective action

# Temporal signature version
IAEC_VERSION = "3.2.0"  # v3.2: DAG manager, cooldown, softmax folding, whitening versioning
SLOT_STRUCTURE_VERSION = 4  # 4-slot architecture
EMBEDDING_MODEL_FAMILY = os.getenv("EMBEDDING_MODEL_FAMILY", "openai")
EMBEDDING_MODEL_VERSION = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# Whitening matrix persistence
WHITENING_STORAGE_DIR = os.getenv("IAEC_WHITENING_DIR", "/tmp/iaec")
WHITENING_VERSION_FILE = "whitening_v{version}.npz"

# Policy hierarchy levels (v3.1: 5-level)
POLICY_LEVEL_GLOBAL = 0
POLICY_LEVEL_ORG = 1
POLICY_LEVEL_AGENT_CLASS = 2
POLICY_LEVEL_AGENT_INSTANCE = 3
POLICY_LEVEL_TASK = 4
POLICY_HIERARCHY_DEPTH = 5

# v3.2: Correction cooldown settings
CORRECTION_COOLDOWN_WINDOW_SECONDS = int(os.getenv("IAEC_CORRECTION_COOLDOWN", "60"))
CORRECTION_MAX_PER_WINDOW = int(os.getenv("IAEC_CORRECTION_MAX_PER_WINDOW", "3"))

# v3.2: Transform DAG settings
TRANSFORM_DAG_MAX_VERSIONS = int(os.getenv("IAEC_TRANSFORM_DAG_MAX_VERSIONS", "10"))
TRANSFORM_DAG_CANONICAL_VERSION = os.getenv("IAEC_CANONICAL_VERSION", IAEC_VERSION)


# Instruction types supported
class InstructionType(str, Enum):
    SUMMARIZE = "summarize"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    REWRITE = "rewrite"
    QA = "qa"
    COMPARE = "compare"
    CLASSIFY = "classify"
    GENERATE = "generate"
    ROUTE = "route"
    DEFAULT = "default"


# Learned weights per instruction type: (instruction, query, context)
INSTRUCTION_WEIGHTS: Dict[str, Tuple[float, float, float]] = {
    "summarize": (0.2, 0.5, 0.3),
    "extract": (0.4, 0.4, 0.2),
    "analyze": (0.3, 0.4, 0.3),
    "rewrite": (0.3, 0.5, 0.2),
    "qa": (0.1, 0.6, 0.3),
    "compare": (0.2, 0.4, 0.4),
    "classify": (0.5, 0.3, 0.2),
    "generate": (0.4, 0.4, 0.2),
    "route": (0.6, 0.3, 0.1),
    "default": (0.33, 0.34, 0.33),
}

# Cross-instruction normalization coefficients
INSTRUCTION_NORM_COEFFICIENTS: Dict[str, float] = {
    "summarize": 1.0,
    "extract": 0.98,
    "analyze": 1.02,
    "rewrite": 0.99,
    "qa": 1.05,
    "compare": 0.97,
    "classify": 0.96,
    "generate": 1.01,
    "route": 0.95,
    "default": 1.0,
}

# Instruction prompts for embedding
INSTRUCTION_PROMPTS: Dict[str, str] = {
    "summarize": "task: summarize the content concisely",
    "extract": "task: extract key entities and information",
    "analyze": "task: perform deep analysis and reasoning",
    "rewrite": "task: rewrite for clarity and improvement",
    "qa": "task: answer the question accurately",
    "compare": "task: compare and contrast items",
    "classify": "task: classify into appropriate categories",
    "generate": "task: generate new content based on input",
    "route": "task: route to appropriate handler",
    "default": "task: process the input",
}

# Instruction-Query compatibility (legacy keyword-based, kept for fallback)
INSTRUCTION_QUERY_COMPATIBILITY: Dict[str, List[str]] = {
    "summarize": ["summary", "brief", "key points", "overview", "tldr", "condense"],
    "extract": ["extract", "find", "get", "pull", "identify", "list", "entities"],
    "analyze": ["analyze", "explain", "why", "how", "reason", "understand", "deep"],
    "rewrite": ["rewrite", "rephrase", "improve", "edit", "revise", "clarify"],
    "qa": ["what", "who", "where", "when", "how", "why", "?", "answer", "tell me"],
    "compare": ["compare", "difference", "versus", "vs", "contrast", "better"],
    "classify": ["classify", "categorize", "type", "kind", "which", "label"],
    "generate": ["generate", "create", "write", "compose", "make", "produce"],
    "route": ["route", "send", "forward", "assign", "handler", "which agent"],
}


# =============================================================================
# Metrics
# =============================================================================

IAEC_COMPOSITIONS = Counter(
    "aos_iaec_compositions_total",
    "Total IAEC embedding compositions",
    ["mode", "instruction", "version"],
)

IAEC_DECOMPOSITIONS = Counter(
    "aos_iaec_decompositions_total",
    "Total IAEC embedding decompositions",
    ["mode", "success"],
)

IAEC_CACHE_HITS = Counter(
    "aos_iaec_instruction_cache_hits_total",
    "IAEC instruction embedding cache hits",
)

IAEC_COMPOSITION_LATENCY = Histogram(
    "aos_iaec_composition_latency_seconds",
    "IAEC composition latency",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.5],
)

IAEC_COLLAPSE_EVENTS = Counter(
    "aos_iaec_collapse_events_total",
    "Times anti-collapse safeguards activated",
    ["type"],
)

IAEC_MISMATCH_WARNINGS = Counter(
    "aos_iaec_mismatch_warnings_total",
    "Instruction-query mismatch warnings",
    ["instruction", "detection_method"],
)

IAEC_WHITENING_APPLIED = Counter(
    "aos_iaec_whitening_applied_total",
    "Times slot whitening was applied",
)

IAEC_INTEGRITY_CHECKS = Counter(
    "aos_iaec_integrity_checks_total",
    "Slot integrity verification checks",
    ["result"],  # pass, fail, error
)

IAEC_TEMPORAL_MISMATCHES = Counter(
    "aos_iaec_temporal_mismatches_total",
    "Temporal signature version mismatches detected",
)

IAEC_TEMPORAL_MEDIATIONS = Counter(
    "aos_iaec_temporal_mediations_total",
    "Cross-version embedding mediations performed",
    ["from_version", "to_version"],
)

IAEC_CORRECTIVE_ACTIONS = Counter(
    "aos_iaec_corrective_actions_total",
    "Corrective action prescriptions issued",
    ["original_instruction", "suggested_instruction"],
)

IAEC_POLICY_FOLDING = Counter(
    "aos_iaec_policy_folding_total",
    "Multi-level policy folding operations",
    ["depth"],
)

IAEC_WHITENING_LOADS = Counter(
    "aos_iaec_whitening_loads_total",
    "Whitening matrix disk loads",
    ["result"],  # success, fail, compute_new
)

# v3.2 metrics
IAEC_DAG_TRANSFORMS = Counter(
    "aos_iaec_dag_transforms_total",
    "Transform DAG operations",
    ["operation"],  # prune, collapse, canonical_path
)

IAEC_CORRECTION_COOLDOWNS = Counter(
    "aos_iaec_correction_cooldowns_total",
    "Correction cooldown events (oscillation prevention)",
    ["reason"],  # window_limit, monotonic_block
)

IAEC_POLICY_SOFTMAX = Counter(
    "aos_iaec_policy_softmax_total",
    "Policy folding with softmax normalization",
)


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class TemporalSignature:
    """
    Temporal signature for drift control (32 dimensions).
    Encodes version information to detect model/weight drift.
    """

    epoch_hash: str  # Hash of current epoch/timestamp
    model_family: str  # e.g., "openai", "voyage", "cohere"
    model_version: str  # e.g., "text-embedding-3-small"
    iaec_version: str  # e.g., "3.0.0"
    slot_structure_version: int  # e.g., 4 (4-slot architecture)

    # The encoded 32-dim vector
    vector: Optional[np.ndarray] = None

    def encode(self) -> np.ndarray:
        """Encode temporal signature into 32-dim deterministic vector."""
        # Create deterministic hash from all version info
        sig_data = f"{self.model_family}|{self.model_version}|{self.iaec_version}|{self.slot_structure_version}"
        sig_hash = hashlib.sha256(sig_data.encode()).digest()

        # Convert to 32 floats in range [-1, 1]
        vector = np.zeros(TEMPORAL_SLOT_SIZE, dtype=np.float32)
        for i in range(TEMPORAL_SLOT_SIZE):
            # Use bytes from hash to create deterministic values
            byte_val = sig_hash[i % len(sig_hash)]
            vector[i] = (byte_val / 127.5) - 1.0  # Map [0, 255] to [-1, 1]

        # Add epoch component (last 8 dims)
        epoch_hash = hashlib.sha256(self.epoch_hash.encode()).digest()[:8]
        for i in range(8):
            vector[TEMPORAL_SLOT_SIZE - 8 + i] = (epoch_hash[i] / 127.5) - 1.0

        self.vector = vector / np.linalg.norm(vector)  # Normalize
        return self.vector

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch_hash": self.epoch_hash,
            "model_family": self.model_family,
            "model_version": self.model_version,
            "iaec_version": self.iaec_version,
            "slot_structure_version": self.slot_structure_version,
        }

    @classmethod
    def current(cls) -> "TemporalSignature":
        """Create temporal signature for current epoch."""
        epoch = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return cls(
            epoch_hash=epoch,
            model_family=EMBEDDING_MODEL_FAMILY,
            model_version=EMBEDDING_MODEL_VERSION,
            iaec_version=IAEC_VERSION,
            slot_structure_version=SLOT_STRUCTURE_VERSION,
        )

    def is_compatible(self, other: "TemporalSignature") -> bool:
        """Check if two temporal signatures are compatible (same version)."""
        return (
            self.model_family == other.model_family
            and self.model_version == other.model_version
            and self.slot_structure_version == other.slot_structure_version
        )

    def version_key(self) -> str:
        """Generate unique version key for mediation lookup."""
        return f"{self.model_family}:{self.model_version}:{self.iaec_version}:{self.slot_structure_version}"


# =============================================================================
# Temporal Mediator (v3.2) - Transform DAG Manager
# =============================================================================


class TemporalMediator:
    """
    Transform DAG Manager for cross-version embedding transformation.

    v3.2 Features:
    - CANONICAL PATH: All transforms route through canonical version to avoid O(n²) matrices
    - VERSION GRAPH PRUNING: Removes stale versions beyond retention window
    - TRANSITIVE COLLAPSING: A→B→C collapses to A→C automatically
    - MERGE POINTS: Multiple paths converge to canonical version

    Critical for:
    - Migrating embeddings across model upgrades
    - Loading older agent states
    - Reading long-term memory files

    Without mediation, mixing embeddings from different epochs can poison routing.
    """

    def __init__(self):
        # Transformation matrices: (old_version_key, new_version_key) -> matrix
        self._transform_matrices: Dict[Tuple[str, str], np.ndarray] = {}
        self._current_signature: Optional[TemporalSignature] = None

        # v3.2: DAG management
        self._canonical_version: str = TRANSFORM_DAG_CANONICAL_VERSION
        self._version_graph: Dict[str, List[str]] = {}  # adjacency list
        self._version_timestamps: Dict[str, float] = {}  # for pruning

    def set_current_signature(self, sig: TemporalSignature):
        """Set the current target temporal signature."""
        self._current_signature = sig
        # v3.2: Update canonical if current is newer
        if sig.iaec_version == IAEC_VERSION:
            self._canonical_version = sig.version_key()

    def register_transform(
        self,
        from_sig: TemporalSignature,
        to_sig: TemporalSignature,
        transform_matrix: np.ndarray,
    ):
        """Register a transformation matrix between two versions."""
        key = (from_sig.version_key(), to_sig.version_key())
        self._transform_matrices[key] = transform_matrix

        # v3.2: Update version graph
        from_key = from_sig.version_key()
        to_key = to_sig.version_key()
        if from_key not in self._version_graph:
            self._version_graph[from_key] = []
        if to_key not in self._version_graph[from_key]:
            self._version_graph[from_key].append(to_key)

        # Track timestamps for pruning
        import time

        self._version_timestamps[from_key] = time.time()
        self._version_timestamps[to_key] = time.time()

        logger.info(f"TemporalMediator: Registered transform {from_key} -> {to_key}")

    def compute_transform(
        self,
        from_sig: TemporalSignature,
        to_sig: TemporalSignature,
        sample_embeddings_old: np.ndarray,
        sample_embeddings_new: np.ndarray,
    ) -> np.ndarray:
        """
        Compute transformation matrix from sample embeddings.

        Uses least squares to find best linear transform from old -> new space.
        """
        if sample_embeddings_old.shape != sample_embeddings_new.shape:
            raise ValueError("Sample embedding shapes must match")

        # Solve A @ transform = B for transform (least squares)
        # Transform maps old embeddings to new embedding space
        transform, _, _, _ = np.linalg.lstsq(
            sample_embeddings_old.T @ sample_embeddings_old + np.eye(sample_embeddings_old.shape[1]) * 1e-6,
            sample_embeddings_old.T @ sample_embeddings_new,
            rcond=None,
        )

        self.register_transform(from_sig, to_sig, transform)
        return transform

    def can_mediate(self, from_sig: TemporalSignature, to_sig: Optional[TemporalSignature] = None) -> bool:
        """Check if mediation is possible between versions."""
        if to_sig is None:
            to_sig = self._current_signature
        if to_sig is None:
            return False

        if from_sig.is_compatible(to_sig):
            return True  # No mediation needed

        # v3.2: Check direct path first
        key = (from_sig.version_key(), to_sig.version_key())
        if key in self._transform_matrices:
            return True

        # v3.2: Check canonical path (from -> canonical -> to)
        path = self._find_canonical_path(from_sig.version_key(), to_sig.version_key())
        return path is not None

    def _find_canonical_path(self, from_key: str, to_key: str) -> Optional[List[str]]:
        """
        v3.2: Find canonical transformation path.

        Routes through canonical version to avoid O(n²) transform matrices.
        Returns path as list of version keys, or None if no path exists.
        """
        # Direct path exists
        if (from_key, to_key) in self._transform_matrices:
            return [from_key, to_key]

        # Try canonical routing: from -> canonical -> to
        canonical = self._canonical_version
        if from_key == canonical or to_key == canonical:
            return None  # Already trying canonical, no other path

        has_to_canonical = (from_key, canonical) in self._transform_matrices
        has_from_canonical = (canonical, to_key) in self._transform_matrices

        if has_to_canonical and has_from_canonical:
            IAEC_DAG_TRANSFORMS.labels(operation="canonical_path").inc()
            return [from_key, canonical, to_key]

        return None

    def mediate(
        self,
        embedding: np.ndarray,
        from_sig: TemporalSignature,
        to_sig: Optional[TemporalSignature] = None,
    ) -> Tuple[np.ndarray, bool]:
        """
        Transform embedding from old version to new version.

        v3.2: Uses canonical path routing to avoid O(n²) transform matrices.

        Returns:
            Tuple of (transformed_embedding, was_mediated)
            If compatible or no transform available, returns original.
        """
        if to_sig is None:
            to_sig = self._current_signature
        if to_sig is None:
            return embedding, False

        if from_sig.is_compatible(to_sig):
            return embedding, False  # No mediation needed

        from_key = from_sig.version_key()
        to_key = to_sig.version_key()

        # v3.2: Find path (direct or canonical)
        path = self._find_canonical_path(from_key, to_key)
        if path is None:
            IAEC_TEMPORAL_MISMATCHES.inc()
            logger.warning(f"TemporalMediator: No transform path from {from_key} to {to_key} - MIXING MAY BE UNSAFE")
            return embedding, False

        # Apply transforms along path
        transformed = embedding.copy()
        for i in range(len(path) - 1):
            key = (path[i], path[i + 1])
            if key not in self._transform_matrices:
                return embedding, False

            transform = self._transform_matrices[key]
            transformed = transformed @ transform

        # Re-normalize
        norm = np.linalg.norm(transformed)
        if norm > 0:
            transformed = transformed / norm

        IAEC_TEMPORAL_MEDIATIONS.labels(from_version=from_key, to_version=to_key).inc()

        return transformed, True

    def collapse_transitive(self, from_key: str, via_key: str, to_key: str) -> bool:
        """
        v3.2: Collapse transitive transforms (A→B→C becomes A→C).

        Reduces error amplification from chained transforms.
        Returns True if collapsed successfully.
        """
        key_ab = (from_key, via_key)
        key_bc = (via_key, to_key)
        key_ac = (from_key, to_key)

        if key_ab not in self._transform_matrices or key_bc not in self._transform_matrices:
            return False

        # Compose transforms: A→C = A→B @ B→C
        transform_ab = self._transform_matrices[key_ab]
        transform_bc = self._transform_matrices[key_bc]
        transform_ac = transform_ab @ transform_bc

        self._transform_matrices[key_ac] = transform_ac
        IAEC_DAG_TRANSFORMS.labels(operation="collapse").inc()

        logger.info(f"TemporalMediator: Collapsed {from_key} -> {via_key} -> {to_key}")
        return True

    def prune_old_versions(self, max_versions: int = TRANSFORM_DAG_MAX_VERSIONS) -> int:
        """
        v3.2: Remove stale versions beyond retention window.

        Keeps most recent versions and canonical version.
        Returns number of versions pruned.
        """
        if len(self._version_timestamps) <= max_versions:
            return 0

        # Sort by timestamp, keep newest + canonical
        sorted_versions = sorted(self._version_timestamps.items(), key=lambda x: x[1], reverse=True)

        keep_versions = set()
        keep_versions.add(self._canonical_version)
        for v, _ in sorted_versions[:max_versions]:
            keep_versions.add(v)

        # Remove transforms involving pruned versions
        pruned = 0
        keys_to_remove = []
        for from_key, to_key in self._transform_matrices.keys():
            if from_key not in keep_versions or to_key not in keep_versions:
                keys_to_remove.append((from_key, to_key))

        for key in keys_to_remove:
            del self._transform_matrices[key]
            pruned += 1

        # Update graph
        for v in list(self._version_graph.keys()):
            if v not in keep_versions:
                del self._version_graph[v]
                del self._version_timestamps[v]

        if pruned > 0:
            IAEC_DAG_TRANSFORMS.labels(operation="prune").inc()
            logger.info(f"TemporalMediator: Pruned {pruned} transforms")

        return pruned

    def get_dag_stats(self) -> Dict[str, Any]:
        """v3.2: Get DAG statistics for monitoring."""
        return {
            "num_versions": len(self._version_timestamps),
            "num_transforms": len(self._transform_matrices),
            "canonical_version": self._canonical_version,
            "max_versions": TRANSFORM_DAG_MAX_VERSIONS,
            "version_keys": list(self._version_timestamps.keys()),
        }

    def serialize(self) -> bytes:
        """Serialize all transformation matrices for persistence."""
        data = {
            "transforms": {f"{k[0]}|{k[1]}": v.tolist() for k, v in self._transform_matrices.items()},
            "current_version": self._current_signature.version_key() if self._current_signature else None,
        }
        return json.dumps(data).encode()

    @classmethod
    def deserialize(cls, data: bytes) -> "TemporalMediator":
        """Deserialize transformation matrices."""
        mediator = cls()
        d = json.loads(data.decode())

        for key_str, matrix in d.get("transforms", {}).items():
            from_key, to_key = key_str.split("|")
            mediator._transform_matrices[(from_key, to_key)] = np.array(matrix, dtype=np.float32)

        return mediator


@dataclass
class PolicyEncoding:
    """
    Policy slot encoding (32 dimensions) with 5-level hierarchy support.

    Hierarchy levels (v3.1):
    - L0: Global system policy (MN-OS constitutional rules)
    - L1: Organization policy (tenant/org settings)
    - L2: Agent-class policy (category-level defaults)
    - L3: Agent-instance policy (specific agent config)
    - L4: Task-level temporary policy (runtime overrides)

    Supports policy stacking and folding for multi-level inheritance.
    """

    policy_id: Optional[str] = None
    policy_version: int = 1
    hierarchy_level: int = 0  # 0=global, 1=org, 2=agent-class, 3=agent-instance, 4=task

    # The encoded 32-dim vector
    vector: Optional[np.ndarray] = None

    # Stacked policies (v3.1: multi-level)
    stacked_policies: Optional[List["PolicyEncoding"]] = None

    def encode(self) -> np.ndarray:
        """Encode single policy into 32-dim deterministic vector."""
        vector = np.zeros(POLICY_SLOT_SIZE, dtype=np.float32)

        if self.policy_id is None:
            # Null policy = zero vector (allows mixing)
            self.vector = vector
            return vector

        # Create deterministic hash from policy info
        policy_data = f"{self.policy_id}|{self.policy_version}|{self.hierarchy_level}"
        policy_hash = hashlib.sha256(policy_data.encode()).digest()

        # Convert to 32 floats (dims 5-31 for policy content)
        for i in range(5, POLICY_SLOT_SIZE):
            byte_val = policy_hash[i % len(policy_hash)]
            vector[i] = (byte_val / 127.5) - 1.0

        # Encode hierarchy level in first 5 dims (one-hot for L0-L4)
        vector[0:5] = 0
        if self.hierarchy_level < POLICY_HIERARCHY_DEPTH:
            vector[self.hierarchy_level] = 1.0

        self.vector = vector / max(np.linalg.norm(vector), 0.01)
        return self.vector

    def stack(self, child_policy: "PolicyEncoding") -> "PolicyEncoding":
        """
        Stack a child policy on top of this policy.

        Child policies have higher hierarchy levels and can override parent settings.
        """
        if self.stacked_policies is None:
            self.stacked_policies = [self]

        self.stacked_policies.append(child_policy)
        return self

    @staticmethod
    def fold(policies: List["PolicyEncoding"], use_softmax: bool = True) -> np.ndarray:
        """
        Fold multiple policies into a single 32-dim vector.

        v3.2: Uses softmax normalization to handle deep stacks properly.

        Folding rules:
        - Higher hierarchy levels have higher weight
        - Task-level (L4) can fully override lower levels
        - Each level contributes weighted portion
        - v3.2: Softmax ensures weights sum to 1.0 regardless of stack depth

        Problem solved: If someone stacks 5 task-level overrides,
        their cumulative weight should not exceed upper-level policies
        disproportionately.

        Returns combined policy vector.
        """
        if not policies:
            return np.zeros(POLICY_SLOT_SIZE, dtype=np.float32)

        # Sort by hierarchy level (lower levels first)
        sorted_policies = sorted(policies, key=lambda p: p.hierarchy_level)

        # Base weights: higher levels have more influence
        # These are "scores" that will be softmax-normalized
        level_base_scores = {
            POLICY_LEVEL_GLOBAL: 1.0,
            POLICY_LEVEL_ORG: 2.0,
            POLICY_LEVEL_AGENT_CLASS: 3.0,
            POLICY_LEVEL_AGENT_INSTANCE: 4.0,
            POLICY_LEVEL_TASK: 5.0,
        }

        # Compute raw scores for each policy
        raw_scores = []
        for policy in sorted_policies:
            if policy.vector is None:
                policy.encode()
            raw_scores.append(level_base_scores.get(policy.hierarchy_level, 1.0))

        # v3.2: Apply softmax normalization
        if use_softmax and len(raw_scores) > 1:
            # Softmax: exp(score) / sum(exp(scores))
            raw_scores_np = np.array(raw_scores, dtype=np.float32)
            # Subtract max for numerical stability
            exp_scores = np.exp(raw_scores_np - np.max(raw_scores_np))
            weights = exp_scores / np.sum(exp_scores)
            IAEC_POLICY_SOFTMAX.inc()
        else:
            # Single policy or softmax disabled: normalize to sum=1
            total = sum(raw_scores)
            weights = [s / total for s in raw_scores] if total > 0 else raw_scores

        # Fold with normalized weights
        folded = np.zeros(POLICY_SLOT_SIZE, dtype=np.float32)
        for policy, weight in zip(sorted_policies, weights):
            folded += policy.vector * weight

        # Re-normalize the final vector
        norm = np.linalg.norm(folded)
        if norm > 0:
            folded = folded / norm

        IAEC_POLICY_FOLDING.labels(depth=str(len(sorted_policies))).inc()

        return folded

    def get_folded_vector(self) -> np.ndarray:
        """Get the folded vector from stacked policies."""
        if self.stacked_policies:
            return PolicyEncoding.fold(self.stacked_policies)
        if self.vector is None:
            self.encode()
        return self.vector

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "hierarchy_level": self.hierarchy_level,
            "hierarchy_name": self._level_name(),
            "stacked_count": len(self.stacked_policies) if self.stacked_policies else 1,
        }

    def _level_name(self) -> str:
        """Human-readable hierarchy level name."""
        names = {
            POLICY_LEVEL_GLOBAL: "global",
            POLICY_LEVEL_ORG: "org",
            POLICY_LEVEL_AGENT_CLASS: "agent-class",
            POLICY_LEVEL_AGENT_INSTANCE: "agent-instance",
            POLICY_LEVEL_TASK: "task",
        }
        return names.get(self.hierarchy_level, "unknown")

    @classmethod
    def from_id(cls, policy_id: Optional[str], version: int = 1, level: int = 0) -> "PolicyEncoding":
        """Create policy encoding from ID."""
        enc = cls(policy_id=policy_id, policy_version=version, hierarchy_level=level)
        enc.encode()
        return enc

    @classmethod
    def from_stack(
        cls,
        global_policy: Optional[str] = None,
        org_policy: Optional[str] = None,
        agent_class_policy: Optional[str] = None,
        agent_instance_policy: Optional[str] = None,
        task_policy: Optional[str] = None,
    ) -> "PolicyEncoding":
        """
        Create a stacked policy encoding from all hierarchy levels.

        Only non-None policies are included in the stack.
        """
        policies = []

        if global_policy:
            policies.append(cls.from_id(global_policy, level=POLICY_LEVEL_GLOBAL))
        if org_policy:
            policies.append(cls.from_id(org_policy, level=POLICY_LEVEL_ORG))
        if agent_class_policy:
            policies.append(cls.from_id(agent_class_policy, level=POLICY_LEVEL_AGENT_CLASS))
        if agent_instance_policy:
            policies.append(cls.from_id(agent_instance_policy, level=POLICY_LEVEL_AGENT_INSTANCE))
        if task_policy:
            policies.append(cls.from_id(task_policy, level=POLICY_LEVEL_TASK))

        if not policies:
            return cls.from_id(None)

        root = policies[0]
        root.stacked_policies = policies
        root.vector = cls.fold(policies)

        return root


@dataclass
class SlotBasis:
    """
    Stores original slot vectors for reversible decomposition.
    Required for weighted mode reconstruction.
    """

    instruction_vector: np.ndarray
    query_vector: np.ndarray
    context_vector: np.ndarray
    weights: Tuple[float, float, float]

    # Metadata slots
    temporal_vector: np.ndarray
    policy_vector: np.ndarray

    def to_bytes(self) -> bytes:
        """Serialize slot basis for storage."""
        data = {
            "i": self.instruction_vector.tolist(),
            "q": self.query_vector.tolist(),
            "c": self.context_vector.tolist(),
            "w": list(self.weights),
            "t": self.temporal_vector.tolist(),
            "p": self.policy_vector.tolist(),
        }
        return json.dumps(data).encode()

    @classmethod
    def from_bytes(cls, data: bytes) -> "SlotBasis":
        """Deserialize slot basis."""
        d = json.loads(data.decode())
        return cls(
            instruction_vector=np.array(d["i"], dtype=np.float32),
            query_vector=np.array(d["q"], dtype=np.float32),
            context_vector=np.array(d["c"], dtype=np.float32),
            weights=tuple(d["w"]),
            temporal_vector=np.array(d["t"], dtype=np.float32),
            policy_vector=np.array(d["p"], dtype=np.float32),
        )


@dataclass
class CompositeEmbedding:
    """Result of IAEC composition with full provenance and reversibility."""

    # The composed embedding vector
    vector: np.ndarray

    # Composition mode used
    mode: Literal["segmented", "weighted", "hybrid"]

    # Instruction type
    instruction: str

    # Weights used (for weighted mode)
    weights: Optional[Tuple[float, float, float]] = None

    # Normalization coefficient applied
    norm_coefficient: float = 1.0

    # Component hashes for cache verification
    instruction_hash: Optional[str] = None
    query_hash: Optional[str] = None
    context_hash: Optional[str] = None

    # Provenance hash (cryptographic identity)
    provenance_hash: Optional[str] = None

    # Mismatch scores (v3.0: both keyword and embedding-based)
    mismatch_score: float = 0.0
    deep_mismatch_score: float = 0.0  # Embedding-based

    # Anti-collapse flags
    collapse_prevented: bool = False
    values_clamped: bool = False

    # Timestamp for temporal tracking
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Policy slot (v3.0: full encoding)
    policy_id: Optional[str] = None
    policy_encoding: Optional[PolicyEncoding] = None

    # Temporal signature (v3.0: for drift control)
    temporal_signature: Optional[TemporalSignature] = None

    # Slot basis for reversibility (v3.0)
    slot_basis: Optional[SlotBasis] = None
    slot_basis_hash: Optional[str] = None  # For verification

    # Integrity verification
    integrity_verified: bool = False
    reconstruction_error: float = 0.0

    # IAEC version
    iaec_version: str = IAEC_VERSION

    # v3.2: Whitening versioning for audit replay
    whitening_basis_id: Optional[str] = None  # Unique ID for whitening matrix
    whitening_version: Optional[str] = None  # Version of whitening matrix used

    def to_list(self) -> List[float]:
        """Convert to list for JSON serialization."""
        return self.vector.tolist()

    @property
    def dimensions(self) -> int:
        return len(self.vector)

    def to_provenance_dict(self) -> Dict[str, Any]:
        """Export provenance metadata for verification."""
        return {
            "provenance_hash": self.provenance_hash,
            "instruction": self.instruction,
            "mode": self.mode,
            "weights": list(self.weights) if self.weights else None,
            "norm_coefficient": self.norm_coefficient,
            "instruction_hash": self.instruction_hash,
            "query_hash": self.query_hash,
            "context_hash": self.context_hash,
            "mismatch_score": self.mismatch_score,
            "deep_mismatch_score": self.deep_mismatch_score,
            "collapse_prevented": self.collapse_prevented,
            "values_clamped": self.values_clamped,
            "created_at": self.created_at,
            "policy_id": self.policy_id,
            "policy_encoding": self.policy_encoding.to_dict() if self.policy_encoding else None,
            "temporal_signature": self.temporal_signature.to_dict() if self.temporal_signature else None,
            "slot_basis_hash": self.slot_basis_hash,
            "integrity_verified": self.integrity_verified,
            "reconstruction_error": self.reconstruction_error,
            "dimensions": self.dimensions,
            "iaec_version": self.iaec_version,
            # v3.2: Whitening versioning for audit replay
            "whitening_basis_id": self.whitening_basis_id,
            "whitening_version": self.whitening_version,
        }

    def can_decompose(self) -> bool:
        """Check if this embedding can be decomposed."""
        return self.slot_basis is not None or self.mode == "segmented"


@dataclass
class DecomposedEmbedding:
    """Result of IAEC decomposition with all 4 slots."""

    instruction_slot: np.ndarray
    query_slot: np.ndarray
    context_slot: np.ndarray
    temporal_slot: np.ndarray
    policy_slot: np.ndarray

    # Verification
    is_valid: bool = True
    reconstruction_error: float = 0.0
    temporal_compatible: bool = True

    # Original mode
    source_mode: str = "segmented"

    def to_dict(self) -> Dict[str, Any]:
        """Export decomposed slots."""
        return {
            "instruction_slot": self.instruction_slot.tolist(),
            "query_slot": self.query_slot.tolist(),
            "context_slot": self.context_slot.tolist(),
            "temporal_slot": self.temporal_slot.tolist(),
            "policy_slot": self.policy_slot.tolist(),
            "is_valid": self.is_valid,
            "reconstruction_error": self.reconstruction_error,
            "temporal_compatible": self.temporal_compatible,
            "source_mode": self.source_mode,
        }


@dataclass
class MismatchWarning:
    """
    Warning for instruction-query semantic mismatch with corrective action.

    v3.1: Includes prescriptive corrective_action for M18/M19 governance integration.
    """

    instruction: str
    query: str
    score: float
    deep_score: float  # Embedding-based score
    suggested_instruction: Optional[str] = None
    detection_method: str = "hybrid"  # "keyword", "embedding", "hybrid", "none"
    message: str = ""

    # v3.1: Corrective action prescription for governance flow
    corrective_action: Optional["CorrectiveAction"] = None


@dataclass
class CorrectiveAction:
    """
    Prescriptive corrective action for mismatch resolution.

    Ties IAEC directly into M18/M19 governance flow by providing
    not just detection but prescription.

    v3.2: Includes cooldown tracking to prevent oscillation loops.
    """

    # The corrected instruction to use
    suggested_instruction: str

    # Confidence score (0-1) - above CORRECTIVE_ACTION_CONFIDENCE_THRESHOLD to prescribe
    confidence: float

    # Whether this action should be automatically applied
    should_auto_correct: bool = False

    # Reason for the correction
    reason: str = ""

    # Alternative suggestions (ranked by confidence)
    alternatives: List[Tuple[str, float]] = field(default_factory=list)

    # Governance metadata
    governance_rule: Optional[str] = None  # Which M19 rule triggered this

    # v3.2: Cooldown tracking
    cooldown_blocked: bool = False  # True if action was blocked by cooldown
    cooldown_reason: Optional[str] = None  # Reason for cooldown block

    def to_dict(self) -> Dict[str, Any]:
        return {
            "suggested_instruction": self.suggested_instruction,
            "confidence": self.confidence,
            "should_auto_correct": self.should_auto_correct,
            "reason": self.reason,
            "alternatives": self.alternatives,
            "governance_rule": self.governance_rule,
            "cooldown_blocked": self.cooldown_blocked,
            "cooldown_reason": self.cooldown_reason,
        }


# =============================================================================
# Correction Cooldown (v3.2) - Oscillation Prevention
# =============================================================================


class CorrectionCooldown:
    """
    v3.2: Prevents oscillation loops in corrective actions.

    Scenario prevented:
        1. user query → "summarize"
        2. IAEC corrects → "extract"
        3. agent produces summary-like output
        4. IAEC sees mismatch → back to "summarize"
        5. LOOP

    Prevention mechanisms:
    - Cooldown window: Max N corrections per window period
    - Monotonic correction: Once corrected A→B, blocks B→A within window
    """

    def __init__(self):
        # Recent corrections: (original, suggested, timestamp)
        self._recent_corrections: List[Tuple[str, str, float]] = []
        # Monotonic correction pairs: blocked reverse corrections
        self._blocked_pairs: Dict[Tuple[str, str], float] = {}

    def can_correct(
        self,
        original_instruction: str,
        suggested_instruction: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a correction is allowed.

        Returns (allowed, reason) - reason is None if allowed.
        """
        import time

        now = time.time()
        cutoff = now - CORRECTION_COOLDOWN_WINDOW_SECONDS

        # Clean up old entries
        self._recent_corrections = [(o, s, t) for o, s, t in self._recent_corrections if t > cutoff]
        self._blocked_pairs = {k: v for k, v in self._blocked_pairs.items() if v > cutoff}

        # Check 1: Window limit (max corrections per window)
        if len(self._recent_corrections) >= CORRECTION_MAX_PER_WINDOW:
            IAEC_CORRECTION_COOLDOWNS.labels(reason="window_limit").inc()
            return (
                False,
                f"Correction limit ({CORRECTION_MAX_PER_WINDOW}) reached within {CORRECTION_COOLDOWN_WINDOW_SECONDS}s window",
            )

        # Check 2: Monotonic correction (prevent reverse oscillation)
        reverse_key = (suggested_instruction, original_instruction)
        if reverse_key in self._blocked_pairs:
            IAEC_CORRECTION_COOLDOWNS.labels(reason="monotonic_block").inc()
            return (
                False,
                f"Reverse correction blocked: {suggested_instruction}→{original_instruction} already corrected to opposite within window",
            )

        return True, None

    def record_correction(self, original_instruction: str, suggested_instruction: str):
        """Record a correction that was applied."""
        import time

        now = time.time()

        # Record the correction
        self._recent_corrections.append((original_instruction, suggested_instruction, now))

        # Block the reverse direction (monotonic policy)
        forward_key = (original_instruction, suggested_instruction)
        self._blocked_pairs[forward_key] = now

        logger.debug(
            f"CorrectionCooldown: Recorded {original_instruction}→{suggested_instruction}, "
            f"blocked reverse until {now + CORRECTION_COOLDOWN_WINDOW_SECONDS}"
        )

    def get_cooldown_state(self) -> Dict[str, Any]:
        """Get current cooldown state for debugging."""
        import time

        now = time.time()
        cutoff = now - CORRECTION_COOLDOWN_WINDOW_SECONDS

        return {
            "recent_corrections": [
                {"from": o, "to": s, "age_seconds": now - t} for o, s, t in self._recent_corrections if t > cutoff
            ],
            "blocked_pairs": [
                {"pair": f"{k[0]}→{k[1]}", "expires_in": v - cutoff}
                for k, v in self._blocked_pairs.items()
                if v > cutoff
            ],
            "window_seconds": CORRECTION_COOLDOWN_WINDOW_SECONDS,
            "max_per_window": CORRECTION_MAX_PER_WINDOW,
            "remaining_corrections": max(0, CORRECTION_MAX_PER_WINDOW - len(self._recent_corrections)),
        }


# Global cooldown instance (singleton per process)
_correction_cooldown: Optional[CorrectionCooldown] = None


def get_correction_cooldown() -> CorrectionCooldown:
    """Get global correction cooldown instance."""
    global _correction_cooldown
    if _correction_cooldown is None:
        _correction_cooldown = CorrectionCooldown()
    return _correction_cooldown


@dataclass
class IntegrityCheckResult:
    """Result of slot integrity verification."""

    passed: bool
    reconstruction_error: float
    temporal_match: bool
    policy_match: bool
    slot_norms_valid: bool
    details: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Core IAEC Class v3.0
# =============================================================================


class InstructionAwareEmbeddingComposer:
    """
    Instruction-Aware Embedding Composer (IAEC) v3.0

    MN-OS Ready with:
    - 4-slot architecture (instruction, query, context, temporal+policy)
    - Reversible weighted mode decomposition
    - Temporal signature for drift control
    - Deep embedding-based mismatch detection
    - Operational policy encoding
    - Self-verification for slot integrity

    Usage:
        composer = InstructionAwareEmbeddingComposer()
        await composer.initialize()

        # Compose with full provenance
        result = await composer.compose(
            instruction="summarize",
            query="What are the key points?",
            context="Long document text...",
            mode="weighted",
            policy_id="pol_001"
        )

        # Decompose back to slots
        slots = composer.decompose(result)

        # Verify integrity
        check = composer.verify_integrity(result)
    """

    def __init__(self, embedding_fn=None):
        self._embedding_fn = embedding_fn
        self._instruction_cache: Dict[str, np.ndarray] = {}
        self._instruction_raw_cache: Dict[str, np.ndarray] = {}  # For mismatch detection
        self._initialized = False

        # Whitening matrix for slot decorrelation
        self._whitening_matrix: Optional[np.ndarray] = None

        # Normalization stats
        self._instruction_norms: Dict[str, float] = {}

        # Current temporal signature
        self._temporal_signature: Optional[TemporalSignature] = None

    async def initialize(self):
        """Pre-compute and cache all instruction embeddings."""
        if self._initialized:
            return

        if self._embedding_fn is None:
            from app.memory.vector_store import get_embedding

            self._embedding_fn = get_embedding

        logger.info("IAEC v3.0: Pre-computing instruction embeddings...")

        # Initialize temporal signature
        self._temporal_signature = TemporalSignature.current()
        self._temporal_signature.encode()

        raw_embeddings = []

        for instr_type, prompt in INSTRUCTION_PROMPTS.items():
            try:
                embedding = await self._embedding_fn(prompt, use_cache=True)
                vec = np.array(embedding, dtype=np.float32)
                norm = np.linalg.norm(vec)
                self._instruction_norms[instr_type] = norm

                # Store raw for mismatch detection
                self._instruction_raw_cache[instr_type] = vec.copy()

                # Normalize for composition
                normalized = self._normalize(vec)
                self._instruction_cache[instr_type] = normalized
                raw_embeddings.append(vec)

                logger.debug(f"IAEC: Cached instruction '{instr_type}' (norm={norm:.4f})")
            except Exception as e:
                logger.warning(f"IAEC: Failed to cache instruction '{instr_type}': {e}")

        # Compute whitening matrix for slot decorrelation
        if len(raw_embeddings) >= 3:
            self._compute_whitening_matrix(np.array(raw_embeddings))

        self._initialized = True
        logger.info(
            f"IAEC v3.1: Initialized with {len(self._instruction_cache)} instructions, "
            f"temporal={self._temporal_signature.iaec_version}"
        )

    def _get_whitening_path(self) -> str:
        """Get path for whitening matrix storage."""
        version_key = self._temporal_signature.version_key() if self._temporal_signature else "unknown"
        safe_key = version_key.replace(":", "_").replace("/", "_")
        return os.path.join(WHITENING_STORAGE_DIR, f"whitening_{safe_key}.npz")

    def _load_whitening_matrix(self) -> bool:
        """
        Load whitening matrix from disk if available and version-compatible.

        Returns True if loaded successfully, False otherwise.
        """
        try:
            path = self._get_whitening_path()
            if not os.path.exists(path):
                IAEC_WHITENING_LOADS.labels(result="not_found").inc()
                return False

            data = np.load(path, allow_pickle=True)

            # Verify version compatibility
            stored_version = str(data.get("iaec_version", "unknown"))
            stored_model = str(data.get("model_version", "unknown"))

            if stored_version != IAEC_VERSION or stored_model != EMBEDDING_MODEL_VERSION:
                logger.warning(
                    f"IAEC: Whitening matrix version mismatch "
                    f"(stored: {stored_version}/{stored_model}, current: {IAEC_VERSION}/{EMBEDDING_MODEL_VERSION})"
                )
                IAEC_WHITENING_LOADS.labels(result="version_mismatch").inc()
                return False

            self._whitening_matrix = data["matrix"]
            self._whitening_mean = data.get("mean")

            logger.info(f"IAEC: Loaded whitening matrix from {path}")
            IAEC_WHITENING_LOADS.labels(result="success").inc()
            return True

        except Exception as e:
            logger.warning(f"IAEC: Failed to load whitening matrix: {e}")
            IAEC_WHITENING_LOADS.labels(result="error").inc()
            return False

    def _save_whitening_matrix(self):
        """
        Save whitening matrix to disk with version locking.

        The matrix is immutable per-version - never overwritten.
        """
        try:
            os.makedirs(WHITENING_STORAGE_DIR, exist_ok=True)
            path = self._get_whitening_path()

            # Don't overwrite existing (immutable per-version)
            if os.path.exists(path):
                logger.debug(f"IAEC: Whitening matrix already exists at {path}, skipping save")
                return

            np.savez_compressed(
                path,
                matrix=self._whitening_matrix,
                mean=self._whitening_mean if hasattr(self, "_whitening_mean") else None,
                iaec_version=IAEC_VERSION,
                model_version=EMBEDDING_MODEL_VERSION,
                model_family=EMBEDDING_MODEL_FAMILY,
                slot_structure=SLOT_STRUCTURE_VERSION,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

            logger.info(f"IAEC: Saved whitening matrix to {path}")

        except Exception as e:
            logger.warning(f"IAEC: Failed to save whitening matrix: {e}")

    def _compute_whitening_matrix(self, embeddings: np.ndarray, force_recompute: bool = False):
        """
        Compute PCA whitening matrix for slot decorrelation.

        v3.1: Persistent storage with version locking.
        - First tries to load from disk
        - If not found or version mismatch, computes new
        - Saves computed matrix (immutable per-version)
        """
        # Try to load existing matrix first (unless forced)
        if not force_recompute and self._load_whitening_matrix():
            return

        # Compute new whitening matrix
        try:
            logger.info("IAEC: Computing new whitening matrix...")
            IAEC_WHITENING_LOADS.labels(result="compute_new").inc()

            self._whitening_mean = np.mean(embeddings, axis=0)
            centered = embeddings - self._whitening_mean
            cov = np.cov(centered.T)

            # Use deterministic eigenvalue decomposition
            eigenvalues, eigenvectors = np.linalg.eigh(cov)
            epsilon = 1e-5
            D_inv_sqrt = np.diag(1.0 / np.sqrt(eigenvalues + epsilon))
            self._whitening_matrix = D_inv_sqrt @ eigenvectors.T

            # Save for future use (immutable per-version)
            self._save_whitening_matrix()

            logger.info("IAEC: Whitening matrix computed for slot decorrelation")

        except Exception as e:
            logger.warning(f"IAEC: Could not compute whitening matrix: {e}")
            self._whitening_matrix = None

    def get_whitening_info(self) -> Dict[str, Any]:
        """Get information about current whitening matrix."""
        return {
            "available": self._whitening_matrix is not None,
            "shape": self._whitening_matrix.shape if self._whitening_matrix is not None else None,
            "storage_path": self._get_whitening_path() if self._temporal_signature else None,
            "iaec_version": IAEC_VERSION,
            "model_version": EMBEDDING_MODEL_VERSION,
        }

    def _normalize(self, vec: np.ndarray) -> np.ndarray:
        """L2 normalize a vector with anti-collapse safeguard."""
        norm = np.linalg.norm(vec)

        if norm < MIN_VECTOR_NORM:
            IAEC_COLLAPSE_EVENTS.labels(type="norm_too_low").inc()
            vec = vec + np.random.randn(len(vec)) * 0.01
            norm = np.linalg.norm(vec)

        if norm == 0:
            return vec

        return vec / norm

    def _clamp_values(self, vec: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Clamp extreme values to prevent collapse."""
        clamped = np.clip(vec, VALUE_CLAMP_MIN, VALUE_CLAMP_MAX)
        was_clamped = not np.array_equal(clamped, vec)

        if was_clamped:
            IAEC_COLLAPSE_EVENTS.labels(type="value_clamped").inc()

        return clamped, was_clamped

    def _hash_text(self, text: str) -> str:
        """Compute short hash for cache verification."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _compute_provenance_hash(
        self,
        instruction: str,
        query: str,
        context: Optional[str],
        mode: str,
        weights: Tuple[float, float, float],
        policy_id: Optional[str],
    ) -> str:
        """Compute cryptographic provenance hash for composite identity."""
        data = {
            "instruction": instruction,
            "query_hash": self._hash_text(query),
            "context_hash": self._hash_text(context) if context else None,
            "mode": mode,
            "weights": weights,
            "policy_id": policy_id,
            "dimensions": EMBEDDING_DIMENSIONS,
            "segment_size": SEGMENT_SIZE,
            "iaec_version": IAEC_VERSION,
        }
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:32]

    def _get_instruction_embedding(self, instruction: str) -> np.ndarray:
        """Get cached instruction embedding."""
        if instruction not in self._instruction_cache:
            instruction = "default"

        IAEC_CACHE_HITS.inc()
        return self._instruction_cache[instruction]

    def _get_instruction_raw(self, instruction: str) -> np.ndarray:
        """Get raw instruction embedding for mismatch detection."""
        if instruction not in self._instruction_raw_cache:
            instruction = "default"
        return self._instruction_raw_cache[instruction]

    async def _detect_mismatch_deep(
        self,
        instruction: str,
        query_embedding: np.ndarray,
    ) -> Tuple[float, Optional[str], Optional[CorrectiveAction]]:
        """
        Deep mismatch detection using embedding cosine similarity.

        v3.1: Returns corrective action with confidence for M18/M19 governance.
        v3.2: Applies cooldown to prevent oscillation loops.

        Returns:
            Tuple of (mismatch_score, suggested_instruction, corrective_action)
            mismatch_score: 0 = perfect match, 1 = complete mismatch
            corrective_action: Prescription if confidence > threshold (may be cooldown-blocked)
        """
        instr_vec = self._get_instruction_raw(instruction)

        # Cosine similarity between instruction and query
        similarity = np.dot(instr_vec, query_embedding) / (
            np.linalg.norm(instr_vec) * np.linalg.norm(query_embedding) + 1e-8
        )

        # Compute similarity for ALL instruction types
        all_scores: List[Tuple[str, float]] = [(instruction, float(similarity))]

        for instr, instr_emb in self._instruction_raw_cache.items():
            if instr == instruction:
                continue
            sim = np.dot(instr_emb, query_embedding) / (
                np.linalg.norm(instr_emb) * np.linalg.norm(query_embedding) + 1e-8
            )
            all_scores.append((instr, float(sim)))

        # Sort by similarity (descending)
        all_scores.sort(key=lambda x: x[1], reverse=True)

        best_instruction, best_similarity = all_scores[0]

        # Mismatch score: 1 - similarity (higher = more mismatch)
        mismatch_score = 1.0 - max(0, similarity)

        suggested = best_instruction if best_instruction != instruction else None

        # Build corrective action if confidence is sufficient
        corrective_action = None
        if suggested and best_similarity > similarity:
            # Confidence = how much better the suggested instruction is
            confidence = float(best_similarity - similarity)

            # Normalize confidence to 0-1 range
            confidence = min(1.0, max(0.0, confidence * 2))  # Scale up for better range

            # Build alternatives list (top 3 excluding current)
            alternatives = [(instr, float(score)) for instr, score in all_scores[1:4] if instr != instruction]

            should_auto_correct = confidence >= CORRECTIVE_ACTION_CONFIDENCE_THRESHOLD

            # v3.2: Check cooldown before allowing correction
            cooldown_blocked = False
            cooldown_reason = None

            if should_auto_correct:
                cooldown = get_correction_cooldown()
                can_correct, reason = cooldown.can_correct(instruction, suggested)

                if not can_correct:
                    cooldown_blocked = True
                    cooldown_reason = reason
                    should_auto_correct = False  # Block auto-correct
                    logger.info(f"IAEC: Correction {instruction}→{suggested} blocked: {reason}")
                else:
                    # Record the correction (will be applied)
                    cooldown.record_correction(instruction, suggested)

            corrective_action = CorrectiveAction(
                suggested_instruction=suggested,
                confidence=confidence,
                should_auto_correct=should_auto_correct,
                reason=f"Query semantics match '{suggested}' better than '{instruction}' "
                f"(similarity: {best_similarity:.3f} vs {similarity:.3f})",
                alternatives=alternatives,
                governance_rule="M19/IAEC-SEMANTIC-ALIGNMENT" if should_auto_correct else None,
                cooldown_blocked=cooldown_blocked,
                cooldown_reason=cooldown_reason,
            )

            if should_auto_correct and not cooldown_blocked:
                IAEC_CORRECTIVE_ACTIONS.labels(original_instruction=instruction, suggested_instruction=suggested).inc()

        return mismatch_score, suggested, corrective_action

    def _detect_mismatch_keyword(self, instruction: str, query: str) -> Tuple[float, Optional[str]]:
        """Legacy keyword-based mismatch detection."""
        query_lower = query.lower()

        keywords = INSTRUCTION_QUERY_COMPATIBILITY.get(instruction, [])
        matches = sum(1 for kw in keywords if kw in query_lower)
        compatibility = matches / max(len(keywords), 1)

        best_instruction = instruction
        best_score = compatibility

        for instr, kws in INSTRUCTION_QUERY_COMPATIBILITY.items():
            if instr == instruction:
                continue
            instr_matches = sum(1 for kw in kws if kw in query_lower)
            instr_score = instr_matches / max(len(kws), 1)
            if instr_score > best_score:
                best_score = instr_score
                best_instruction = instr

        mismatch_score = 1.0 - compatibility
        suggested = best_instruction if best_instruction != instruction and best_score > compatibility else None

        return mismatch_score, suggested

    def _check_context_dominance(
        self,
        instr_vec: np.ndarray,
        query_vec: np.ndarray,
        ctx_vec: np.ndarray,
        composed: np.ndarray,
    ) -> bool:
        """Check if context is dominating the composed vector."""
        if np.linalg.norm(ctx_vec) < MIN_VECTOR_NORM:
            return False

        ctx_sim = np.dot(composed, ctx_vec)
        query_sim = np.dot(composed, query_vec)

        if ctx_sim > COLLAPSE_THRESHOLD and ctx_sim > query_sim * 1.5:
            IAEC_COLLAPSE_EVENTS.labels(type="context_dominant").inc()
            return True

        return False

    def _rebalance_collapsed(
        self,
        instr: np.ndarray,
        query: np.ndarray,
        ctx: np.ndarray,
        instruction: str,
    ) -> np.ndarray:
        """Rebalance a collapsed vector by boosting instruction/query."""
        wi, wq, wc = INSTRUCTION_WEIGHTS.get(instruction, (0.33, 0.34, 0.33))

        wc_new = wc * 0.5
        boost = (wc - wc_new) / 2
        wi_new = wi + boost
        wq_new = wq + boost

        composed = wi_new * instr + wq_new * query + wc_new * ctx
        logger.debug("IAEC: Rebalanced collapsed vector")
        return composed

    async def compose(
        self,
        instruction: str,
        query: str,
        context: Optional[str] = None,
        mode: Literal["segmented", "weighted", "hybrid"] = "weighted",
        policy_id: Optional[str] = None,
        policy_version: int = 1,
        policy_level: int = 0,
        detect_mismatch: bool = True,
        store_basis: bool = True,  # v3.0: store slot basis for reversibility
    ) -> CompositeEmbedding:
        """
        Compose a structured embedding with full v3.0 features.

        Args:
            instruction: Instruction type (summarize, extract, etc.)
            query: User query/input
            context: Optional context text
            mode: Composition mode
            policy_id: Policy identifier for governance
            policy_version: Policy version number
            policy_level: Hierarchy level (0=global, 1=org, 2=team, 3=agent)
            detect_mismatch: Whether to check instruction-query compatibility
            store_basis: Whether to store slot basis for reversible decomposition

        Returns:
            CompositeEmbedding with full provenance and reversibility
        """
        import time

        start = time.perf_counter()

        if not self._initialized:
            await self.initialize()

        # Normalize instruction type
        instruction = instruction.lower()
        if instruction not in INSTRUCTION_WEIGHTS:
            instruction = "default"

        # Get instruction embedding (cached)
        instr_vec = self._get_instruction_embedding(instruction)

        # Embed query
        query_raw = await self._embedding_fn(query, use_cache=True)
        query_vec_full = np.array(query_raw, dtype=np.float32)
        query_vec = self._normalize(query_vec_full)

        # Detect mismatch (v3.0: both methods)
        mismatch_score = 0.0
        deep_mismatch_score = 0.0
        suggested_instruction = None

        corrective_action = None
        if detect_mismatch:
            # Keyword-based (legacy)
            mismatch_score, kw_suggested = self._detect_mismatch_keyword(instruction, query)

            # Embedding-based (v3.1) with corrective action
            deep_mismatch_score, emb_suggested, corrective_action = await self._detect_mismatch_deep(
                instruction, query_vec_full
            )

            # Use embedding-based suggestion if confident
            suggested_instruction = emb_suggested if deep_mismatch_score > DEEP_MISMATCH_THRESHOLD else kw_suggested

            if deep_mismatch_score > DEEP_MISMATCH_THRESHOLD:
                IAEC_MISMATCH_WARNINGS.labels(instruction=instruction, detection_method="embedding").inc()
                logger.warning(
                    f"IAEC: Deep mismatch detected (instruction={instruction}, "
                    f"score={deep_mismatch_score:.2f}, suggested={suggested_instruction})"
                )
                if corrective_action and corrective_action.should_auto_correct:
                    logger.warning(
                        f"IAEC: Corrective action prescribed: {corrective_action.reason} "
                        f"(confidence={corrective_action.confidence:.2f})"
                    )
            elif mismatch_score > MISMATCH_THRESHOLD:
                IAEC_MISMATCH_WARNINGS.labels(instruction=instruction, detection_method="keyword").inc()

        # Embed context (or use zeros)
        if context and context.strip():
            ctx_raw = await self._embedding_fn(context, use_cache=True)
            ctx_vec = self._normalize(np.array(ctx_raw, dtype=np.float32))
        else:
            ctx_vec = np.zeros(EMBEDDING_DIMENSIONS, dtype=np.float32)

        # Get weights
        weights = INSTRUCTION_WEIGHTS.get(instruction, INSTRUCTION_WEIGHTS["default"])

        # Create temporal signature
        temporal_sig = TemporalSignature.current()
        temporal_vec = temporal_sig.encode()

        # Create policy encoding
        policy_enc = PolicyEncoding.from_id(policy_id, policy_version, policy_level)
        policy_vec = policy_enc.vector

        # Compose based on mode
        if mode == "segmented":
            composed = self._compose_segmented(instr_vec, query_vec, ctx_vec, temporal_vec, policy_vec)
        else:  # weighted or hybrid
            composed = self._compose_weighted(instr_vec, query_vec, ctx_vec, temporal_vec, policy_vec, instruction)

        # Anti-collapse: clamp extreme values
        composed, values_clamped = self._clamp_values(composed)

        # Anti-collapse: check context dominance
        collapse_prevented = self._check_context_dominance(instr_vec, query_vec, ctx_vec, composed)

        if collapse_prevented:
            composed = self._rebalance_collapsed(instr_vec, query_vec, ctx_vec, instruction)
            # Re-add metadata slots
            composed = self._add_metadata_slots(composed, temporal_vec, policy_vec)

        # Apply cross-instruction normalization
        norm_coef = INSTRUCTION_NORM_COEFFICIENTS.get(instruction, 1.0)
        # Only apply to content portion
        composed[:CONTENT_DIMENSIONS] = composed[:CONTENT_DIMENSIONS] * norm_coef

        # Final L2 normalization (content portion only, preserve metadata)
        content_portion = composed[:CONTENT_DIMENSIONS]
        content_norm = np.linalg.norm(content_portion)
        if content_norm > 0:
            composed[:CONTENT_DIMENSIONS] = content_portion / content_norm

        # Store slot basis for reversibility (v3.0)
        slot_basis = None
        slot_basis_hash = None
        if store_basis and mode in ("weighted", "hybrid"):
            slot_basis = SlotBasis(
                instruction_vector=instr_vec.copy(),
                query_vector=query_vec.copy(),
                context_vector=ctx_vec.copy(),
                weights=weights,
                temporal_vector=temporal_vec.copy(),
                policy_vector=policy_vec.copy(),
            )
            slot_basis_hash = hashlib.sha256(slot_basis.to_bytes()).hexdigest()[:16]

        # Compute provenance hash
        provenance_hash = self._compute_provenance_hash(instruction, query, context, mode, weights, policy_id)

        # Verify integrity
        reconstruction_error = 0.0
        if slot_basis is not None:
            # Verify we can reconstruct
            reconstructed = self._reconstruct_from_basis(slot_basis, instruction)
            reconstruction_error = np.linalg.norm(composed - reconstructed)

        # Track metrics
        latency = time.perf_counter() - start
        IAEC_COMPOSITION_LATENCY.observe(latency)
        IAEC_COMPOSITIONS.labels(mode=mode, instruction=instruction, version="3.2").inc()

        # v3.2: Generate whitening metadata for audit replay
        whitening_basis_id = None
        whitening_version = None
        if self._whitening_matrix is not None:
            # Generate stable ID from whitening matrix hash
            matrix_hash = hashlib.sha256(self._whitening_matrix.tobytes()).hexdigest()[:16]
            whitening_basis_id = f"wht_{EMBEDDING_MODEL_FAMILY}_{matrix_hash}"
            whitening_version = f"{IAEC_VERSION}/{EMBEDDING_MODEL_VERSION}/{SLOT_STRUCTURE_VERSION}"

        return CompositeEmbedding(
            vector=composed,
            mode=mode,
            instruction=instruction,
            weights=weights,
            norm_coefficient=norm_coef,
            instruction_hash=self._hash_text(INSTRUCTION_PROMPTS.get(instruction, "")),
            query_hash=self._hash_text(query),
            context_hash=self._hash_text(context) if context else None,
            provenance_hash=provenance_hash,
            mismatch_score=mismatch_score,
            deep_mismatch_score=deep_mismatch_score,
            collapse_prevented=collapse_prevented,
            values_clamped=values_clamped,
            policy_id=policy_id,
            policy_encoding=policy_enc,
            temporal_signature=temporal_sig,
            slot_basis=slot_basis,
            slot_basis_hash=slot_basis_hash,
            integrity_verified=reconstruction_error < 0.01,
            reconstruction_error=reconstruction_error,
            iaec_version=IAEC_VERSION,
            whitening_basis_id=whitening_basis_id,
            whitening_version=whitening_version,
        )

    def _compose_segmented(
        self,
        instr: np.ndarray,
        query: np.ndarray,
        ctx: np.ndarray,
        temporal: np.ndarray,
        policy: np.ndarray,
    ) -> np.ndarray:
        """
        Compose using dimensional segmentation (4-slot v3.0).

        Layout: [instruction | query | context | temporal | policy]
        """
        return np.concatenate(
            [
                instr[:SEGMENT_SIZE],
                query[:SEGMENT_SIZE],
                ctx[:SEGMENT_SIZE],
                temporal,
                policy,
            ]
        )

    def _compose_weighted(
        self,
        instr: np.ndarray,
        query: np.ndarray,
        ctx: np.ndarray,
        temporal: np.ndarray,
        policy: np.ndarray,
        instruction: str,
    ) -> np.ndarray:
        """Compose using learned weights with metadata slots."""
        wi, wq, wc = INSTRUCTION_WEIGHTS.get(instruction, (0.33, 0.34, 0.33))

        # Weighted blend for content
        content = wi * instr[:CONTENT_DIMENSIONS] + wq * query[:CONTENT_DIMENSIONS] + wc * ctx[:CONTENT_DIMENSIONS]

        # Concatenate with metadata slots
        return np.concatenate([content, temporal, policy])

    def _add_metadata_slots(
        self,
        composed: np.ndarray,
        temporal: np.ndarray,
        policy: np.ndarray,
    ) -> np.ndarray:
        """Add/replace metadata slots to composed vector."""
        composed[CONTENT_DIMENSIONS : CONTENT_DIMENSIONS + TEMPORAL_SLOT_SIZE] = temporal
        composed[CONTENT_DIMENSIONS + TEMPORAL_SLOT_SIZE :] = policy
        return composed

    def _reconstruct_from_basis(
        self,
        basis: SlotBasis,
        instruction: str,
    ) -> np.ndarray:
        """Reconstruct composed vector from slot basis."""
        wi, wq, wc = basis.weights

        content = (
            wi * basis.instruction_vector[:CONTENT_DIMENSIONS]
            + wq * basis.query_vector[:CONTENT_DIMENSIONS]
            + wc * basis.context_vector[:CONTENT_DIMENSIONS]
        )

        # Normalize content
        content = content / max(np.linalg.norm(content), 1e-8)

        # Apply norm coefficient
        norm_coef = INSTRUCTION_NORM_COEFFICIENTS.get(instruction, 1.0)
        content = content * norm_coef
        content = content / max(np.linalg.norm(content), 1e-8)

        return np.concatenate([content, basis.temporal_vector, basis.policy_vector])

    def decompose(
        self,
        embedding: Union[CompositeEmbedding, np.ndarray],
        verify: bool = True,
    ) -> DecomposedEmbedding:
        """
        Decompose a composite embedding back into slots (v3.0).

        For segmented mode: Direct extraction from dimensional regions
        For weighted mode: Uses stored slot basis if available

        Args:
            embedding: CompositeEmbedding or raw vector
            verify: Whether to verify reconstruction

        Returns:
            DecomposedEmbedding with all 4 slots
        """
        if isinstance(embedding, CompositeEmbedding):
            vec = embedding.vector
            mode = embedding.mode
            slot_basis = embedding.slot_basis
            temporal_sig = embedding.temporal_signature
        else:
            vec = embedding
            mode = "segmented"  # Assume segmented for raw vectors
            slot_basis = None
            temporal_sig = None

        # Segmented mode: direct extraction
        if mode == "segmented" or slot_basis is None:
            instr_slot = vec[:SEGMENT_SIZE]
            query_slot = vec[SEGMENT_SIZE : 2 * SEGMENT_SIZE]
            ctx_slot = vec[2 * SEGMENT_SIZE : 3 * SEGMENT_SIZE]
            temporal_slot = vec[CONTENT_DIMENSIONS : CONTENT_DIMENSIONS + TEMPORAL_SLOT_SIZE]
            policy_slot = vec[CONTENT_DIMENSIONS + TEMPORAL_SLOT_SIZE :]

            IAEC_DECOMPOSITIONS.labels(mode="segmented", success="true").inc()

            # Check temporal compatibility
            temporal_compatible = True
            if temporal_sig is not None and self._temporal_signature is not None:
                temporal_compatible = temporal_sig.is_compatible(self._temporal_signature)
                if not temporal_compatible:
                    IAEC_TEMPORAL_MISMATCHES.inc()

            return DecomposedEmbedding(
                instruction_slot=instr_slot,
                query_slot=query_slot,
                context_slot=ctx_slot,
                temporal_slot=temporal_slot,
                policy_slot=policy_slot,
                is_valid=True,
                reconstruction_error=0.0,
                temporal_compatible=temporal_compatible,
                source_mode="segmented",
            )

        # Weighted mode: use slot basis for true decomposition
        IAEC_DECOMPOSITIONS.labels(mode="weighted", success="true").inc()

        # Extract metadata slots (these are unchanged)
        temporal_slot = vec[CONTENT_DIMENSIONS : CONTENT_DIMENSIONS + TEMPORAL_SLOT_SIZE]
        policy_slot = vec[CONTENT_DIMENSIONS + TEMPORAL_SLOT_SIZE :]

        # Use original slot vectors from basis
        instr_slot = slot_basis.instruction_vector[:SEGMENT_SIZE]
        query_slot = slot_basis.query_vector[:SEGMENT_SIZE]
        ctx_slot = slot_basis.context_vector[:SEGMENT_SIZE]

        # Verify reconstruction
        reconstruction_error = 0.0
        is_valid = True

        if verify:
            reconstructed = self._reconstruct_from_basis(slot_basis, embedding.instruction)
            reconstruction_error = np.linalg.norm(vec - reconstructed)
            is_valid = reconstruction_error < 0.05  # Tolerance for floating point

        # Check temporal compatibility
        temporal_compatible = True
        if temporal_sig is not None and self._temporal_signature is not None:
            temporal_compatible = temporal_sig.is_compatible(self._temporal_signature)
            if not temporal_compatible:
                IAEC_TEMPORAL_MISMATCHES.inc()

        return DecomposedEmbedding(
            instruction_slot=instr_slot,
            query_slot=query_slot,
            context_slot=ctx_slot,
            temporal_slot=temporal_slot,
            policy_slot=policy_slot,
            is_valid=is_valid,
            reconstruction_error=reconstruction_error,
            temporal_compatible=temporal_compatible,
            source_mode="weighted",
        )

    def verify_integrity(
        self,
        embedding: CompositeEmbedding,
    ) -> IntegrityCheckResult:
        """
        Verify slot integrity of a composite embedding (v3.0).

        Checks:
        - Slot basis can reconstruct the vector
        - Temporal signature matches current epoch
        - Policy encoding is valid
        - All slot norms are within bounds
        """
        details = {}

        # Check slot basis
        if embedding.slot_basis is not None:
            reconstructed = self._reconstruct_from_basis(embedding.slot_basis, embedding.instruction)
            reconstruction_error = np.linalg.norm(embedding.vector - reconstructed)
            reconstruction_ok = reconstruction_error < 0.05
            details["reconstruction_error"] = float(reconstruction_error)
            details["reconstruction_ok"] = reconstruction_ok
        else:
            reconstruction_error = 0.0
            reconstruction_ok = embedding.mode == "segmented"
            details["reconstruction_ok"] = reconstruction_ok
            details["reason"] = "no_slot_basis" if not reconstruction_ok else "segmented_mode"

        # Check temporal signature
        temporal_match = True
        if embedding.temporal_signature is not None and self._temporal_signature is not None:
            temporal_match = embedding.temporal_signature.is_compatible(self._temporal_signature)
            details["temporal_signature"] = embedding.temporal_signature.to_dict()
            details["current_temporal"] = self._temporal_signature.to_dict()
        details["temporal_match"] = temporal_match

        # Check policy encoding
        policy_match = True
        if embedding.policy_encoding is not None:
            policy_match = embedding.policy_encoding.vector is not None
            details["policy_encoding"] = embedding.policy_encoding.to_dict()
        details["policy_match"] = policy_match

        # Check slot norms
        decomposed = self.decompose(embedding, verify=False)
        norms = {
            "instruction": float(np.linalg.norm(decomposed.instruction_slot)),
            "query": float(np.linalg.norm(decomposed.query_slot)),
            "context": float(np.linalg.norm(decomposed.context_slot)),
            "temporal": float(np.linalg.norm(decomposed.temporal_slot)),
            "policy": float(np.linalg.norm(decomposed.policy_slot)),
        }
        details["slot_norms"] = norms

        # Norms should be reasonable (not collapsed)
        slot_norms_valid = all(
            n > MIN_VECTOR_NORM * 0.5 or k in ("context", "policy")  # context/policy can be zero
            for k, n in norms.items()
        )
        details["slot_norms_valid"] = slot_norms_valid

        # Overall result
        passed = reconstruction_ok and temporal_match and policy_match and slot_norms_valid

        # Track metrics
        IAEC_INTEGRITY_CHECKS.labels(result="pass" if passed else "fail").inc()

        return IntegrityCheckResult(
            passed=passed,
            reconstruction_error=reconstruction_error,
            temporal_match=temporal_match,
            policy_match=policy_match,
            slot_norms_valid=slot_norms_valid,
            details=details,
        )

    def verify_provenance(
        self,
        embedding: CompositeEmbedding,
        instruction: str,
        query: str,
        context: Optional[str],
    ) -> bool:
        """Verify that a composite embedding matches its claimed provenance."""
        expected_hash = self._compute_provenance_hash(
            instruction,
            query,
            context,
            embedding.mode,
            embedding.weights,
            embedding.policy_id,
        )
        return embedding.provenance_hash == expected_hash

    def similarity(
        self,
        a: Union[CompositeEmbedding, np.ndarray],
        b: Union[CompositeEmbedding, np.ndarray],
        mode: Literal["cosine", "instruction_weighted", "slot_weighted"] = "cosine",
        instruction: Optional[str] = None,
    ) -> float:
        """Compute similarity between two embeddings."""
        vec_a = a.vector if isinstance(a, CompositeEmbedding) else a
        vec_b = b.vector if isinstance(b, CompositeEmbedding) else b

        if mode == "cosine":
            return float(np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b) + 1e-8))

        elif mode == "instruction_weighted":
            if instruction is None:
                instruction = "default"

            wi, wq, wc = INSTRUCTION_WEIGHTS.get(instruction, (0.33, 0.34, 0.33))

            a_dec = self.decompose(a, verify=False)
            b_dec = self.decompose(b, verify=False)

            sim_instr = np.dot(self._normalize(a_dec.instruction_slot), self._normalize(b_dec.instruction_slot))
            sim_query = np.dot(self._normalize(a_dec.query_slot), self._normalize(b_dec.query_slot))
            sim_ctx = np.dot(self._normalize(a_dec.context_slot), self._normalize(b_dec.context_slot))

            return float(wi * sim_instr + wq * sim_query + wc * sim_ctx)

        elif mode == "slot_weighted":
            a_dec = self.decompose(a, verify=False)
            b_dec = self.decompose(b, verify=False)

            similarities = []
            for a_slot, b_slot in [
                (a_dec.instruction_slot, b_dec.instruction_slot),
                (a_dec.query_slot, b_dec.query_slot),
                (a_dec.context_slot, b_dec.context_slot),
            ]:
                a_norm = self._normalize(a_slot)
                b_norm = self._normalize(b_slot)
                similarities.append(np.dot(a_norm, b_norm))

            return float(np.mean(similarities))

        else:
            raise ValueError(f"Unknown similarity mode: {mode}")

    def get_instruction_types(self) -> List[str]:
        """Get list of supported instruction types."""
        return list(INSTRUCTION_PROMPTS.keys())

    def get_weights(self, instruction: str) -> Tuple[float, float, float]:
        """Get weights for an instruction type."""
        return INSTRUCTION_WEIGHTS.get(instruction, INSTRUCTION_WEIGHTS["default"])

    def get_segment_info(self) -> Dict[str, Any]:
        """Get segmentation configuration info (v3.0)."""
        return {
            "iaec_version": IAEC_VERSION,
            "embedding_dimensions": EMBEDDING_DIMENSIONS,
            "content_dimensions": CONTENT_DIMENSIONS,
            "segment_size": SEGMENT_SIZE,
            "temporal_slot_size": TEMPORAL_SLOT_SIZE,
            "policy_slot_size": POLICY_SLOT_SIZE,
            "slot_structure_version": SLOT_STRUCTURE_VERSION,
            "slots": {
                "instruction": {"start": 0, "end": SEGMENT_SIZE},
                "query": {"start": SEGMENT_SIZE, "end": 2 * SEGMENT_SIZE},
                "context": {"start": 2 * SEGMENT_SIZE, "end": 3 * SEGMENT_SIZE},
                "temporal": {"start": CONTENT_DIMENSIONS, "end": CONTENT_DIMENSIONS + TEMPORAL_SLOT_SIZE},
                "policy": {"start": CONTENT_DIMENSIONS + TEMPORAL_SLOT_SIZE, "end": EMBEDDING_DIMENSIONS},
            },
            "temporal_signature": self._temporal_signature.to_dict() if self._temporal_signature else None,
        }


# =============================================================================
# Singleton & Factory
# =============================================================================

_iaec_instance: Optional[InstructionAwareEmbeddingComposer] = None


async def get_iaec() -> InstructionAwareEmbeddingComposer:
    """Get singleton IAEC instance."""
    global _iaec_instance
    if _iaec_instance is None:
        _iaec_instance = InstructionAwareEmbeddingComposer()
        await _iaec_instance.initialize()
    return _iaec_instance


# =============================================================================
# Convenience Functions
# =============================================================================


async def compose_embedding(
    instruction: str,
    query: str,
    context: Optional[str] = None,
    mode: Literal["segmented", "weighted"] = "weighted",
    policy_id: Optional[str] = None,
) -> List[float]:
    """Convenience function to compose an embedding."""
    iaec = await get_iaec()
    result = await iaec.compose(instruction, query, context, mode, policy_id)
    return result.to_list()


async def compose_for_routing(
    instruction: str,
    query: str,
    context: Optional[str] = None,
) -> List[float]:
    """Compose embedding optimized for routing decisions."""
    return await compose_embedding(instruction, query, context, mode="segmented")


async def compose_for_search(
    instruction: str,
    query: str,
    context: Optional[str] = None,
) -> List[float]:
    """Compose embedding optimized for semantic search."""
    return await compose_embedding(instruction, query, context, mode="weighted")


async def decompose_embedding(
    embedding: Union[CompositeEmbedding, np.ndarray, List[float]],
) -> Dict[str, Any]:
    """Decompose an embedding back to slots."""
    iaec = await get_iaec()
    if isinstance(embedding, list):
        embedding = np.array(embedding, dtype=np.float32)
    result = iaec.decompose(embedding)
    return result.to_dict()


async def check_instruction_query_match(
    instruction: str,
    query: str,
) -> MismatchWarning:
    """
    Check if instruction and query are semantically compatible.
    Uses both keyword and embedding-based detection (v3.1).

    v3.1: Includes corrective_action with confidence for M18/M19 governance.
    """
    iaec = await get_iaec()

    # Keyword-based
    kw_score, kw_suggested = iaec._detect_mismatch_keyword(instruction, query)

    # Embedding-based with corrective action (v3.1)
    query_raw = await iaec._embedding_fn(query, use_cache=True)
    query_vec = np.array(query_raw, dtype=np.float32)
    deep_score, deep_suggested, corrective_action = await iaec._detect_mismatch_deep(instruction, query_vec)

    # Use deep suggestion if confident
    suggested = deep_suggested if deep_score > DEEP_MISMATCH_THRESHOLD else kw_suggested

    # Determine detection method
    if deep_score > DEEP_MISMATCH_THRESHOLD:
        method = "embedding"
    elif kw_score > MISMATCH_THRESHOLD:
        method = "keyword"
    else:
        method = "none"

    warning = MismatchWarning(
        instruction=instruction,
        query=query,
        score=float(kw_score),
        deep_score=float(deep_score),
        suggested_instruction=suggested,
        detection_method=method,
        corrective_action=corrective_action,
    )

    if deep_score > DEEP_MISMATCH_THRESHOLD:
        confidence_str = f"{corrective_action.confidence:.1%}" if corrective_action else f"{1 - deep_score:.1%}"
        warning.message = (
            f"Embedding analysis suggests query is a '{suggested}' task but instruction is '{instruction}'. "
            f"Consider using instruction='{suggested}' for better results. (confidence: {confidence_str})"
        )
    elif kw_score > MISMATCH_THRESHOLD:
        warning.message = (
            f"Keyword analysis suggests mismatch. Consider using instruction='{suggested}' for better results."
        )
    else:
        warning.message = "Instruction and query appear compatible."

    return warning


async def verify_embedding_integrity(
    embedding: CompositeEmbedding,
) -> Dict[str, Any]:
    """Verify slot integrity of an embedding."""
    iaec = await get_iaec()
    result = iaec.verify_integrity(embedding)
    return {
        "passed": result.passed,
        "reconstruction_error": result.reconstruction_error,
        "temporal_match": result.temporal_match,
        "policy_match": result.policy_match,
        "slot_norms_valid": result.slot_norms_valid,
        "details": result.details,
    }
