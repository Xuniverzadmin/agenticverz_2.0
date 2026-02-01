# Layer: L4 — HOC Spine (Schema)
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: import-time
#   Execution: sync
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: none
#   Writes: none
# Role: Artifact API schemas (pure Pydantic DTOs)
# Callers: API routes, engines
# Allowed Imports: None (foundational)
# Forbidden Imports: L1, L2, L3, L4, L6 (no DB), sqlalchemy
# Reference: PIN-470, API Schemas
# NOTE: Reclassified L6→L5 (2026-01-24) - Pure Pydantic schemas, no boundary crossing

# Artifact Schemas
# Pydantic models for run outputs and artifacts

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

def _utc_now() -> datetime:
    """UTC timestamp (inlined to keep schemas pure — no service imports)."""
    return datetime.now(timezone.utc)


class ArtifactType(str, Enum):
    """Type of artifact produced by a run."""

    JSON = "json"  # Structured JSON data
    TEXT = "text"  # Plain text
    HTML = "html"  # HTML content
    MARKDOWN = "markdown"  # Markdown text
    CSV = "csv"  # CSV data
    IMAGE = "image"  # Image file
    PDF = "pdf"  # PDF document
    FILE = "file"  # Generic file
    LOG = "log"  # Execution log
    BLOB = "blob"  # Binary blob


class StorageBackend(str, Enum):
    """Where the artifact is stored."""

    INLINE = "inline"  # Stored directly in database (small)
    POSTGRES = "postgres"  # Stored in Postgres BYTEA
    S3 = "s3"  # S3-compatible object storage
    LOCAL = "local"  # Local filesystem


class Artifact(BaseModel):
    """An artifact produced by a run or step.

    Artifacts capture outputs, files, and data produced
    during execution for later retrieval and analysis.
    """

    artifact_id: str = Field(description="Unique artifact identifier")
    run_id: str = Field(description="Run that produced this artifact")
    step_id: Optional[str] = Field(default=None, description="Step that produced this artifact")

    # Type and content
    artifact_type: ArtifactType = Field(description="Type of artifact")
    name: str = Field(description="Artifact name/label")
    description: Optional[str] = Field(default=None, description="Human-readable description")

    # Storage location
    storage_backend: StorageBackend = Field(default=StorageBackend.INLINE, description="Where artifact is stored")
    storage_path: Optional[str] = Field(default=None, description="Path/key in storage backend")

    # Content (for inline storage)
    content_json: Optional[Dict[str, Any]] = Field(default=None, description="JSON content (for JSON artifacts)")
    content_text: Optional[str] = Field(
        default=None, max_length=100000, description="Text content (for text/html/markdown)"
    )

    # File metadata
    mime_type: Optional[str] = Field(default=None, description="MIME type for files")
    size_bytes: Optional[int] = Field(default=None, ge=0, description="Size in bytes")
    checksum: Optional[str] = Field(default=None, description="SHA256 checksum")
    encoding: Optional[str] = Field(default=None, description="Text encoding if applicable")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")

    # Timestamps
    created_at: datetime = Field(default_factory=_utc_now, description="Creation timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration timestamp (for cleanup)")

    @property
    def is_inline(self) -> bool:
        """Check if content is stored inline."""
        return self.storage_backend == StorageBackend.INLINE

    @property
    def has_content(self) -> bool:
        """Check if artifact has content available."""
        return self.content_json is not None or self.content_text is not None or self.storage_path is not None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "artifact_id": "art-abc123",
                "run_id": "run-xyz789",
                "step_id": "fetch",
                "artifact_type": "json",
                "name": "api_response",
                "description": "Response from API call",
                "storage_backend": "inline",
                "content_json": {"status": "ok", "data": [1, 2, 3]},
                "size_bytes": 128,
                "tags": ["api", "response"],
            }
        }
    )

    def get_inline_content(self) -> Optional[Any]:
        """Get inline content if available."""
        if self.content_json is not None:
            return self.content_json
        if self.content_text is not None:
            return self.content_text
        return None


class ArtifactReference(BaseModel):
    """Lightweight reference to an artifact.

    Used when you need to reference an artifact without
    loading its full content.
    """

    artifact_id: str = Field(description="Artifact ID")
    run_id: str = Field(description="Run ID")
    artifact_type: ArtifactType = Field(description="Type")
    name: str = Field(description="Name")
    size_bytes: Optional[int] = Field(default=None)
    created_at: datetime = Field(default_factory=_utc_now)

    @classmethod
    def from_artifact(cls, artifact: Artifact) -> "ArtifactReference":
        """Create reference from full artifact."""
        return cls(
            artifact_id=artifact.artifact_id,
            run_id=artifact.run_id,
            artifact_type=artifact.artifact_type,
            name=artifact.name,
            size_bytes=artifact.size_bytes,
            created_at=artifact.created_at,
        )
