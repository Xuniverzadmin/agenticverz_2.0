# Artifact Storage
# Provides storage backends for run artifacts (files, blobs, etc.)

import hashlib
import json
import logging
import os
import shutil
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union
from urllib.parse import urlparse

from ..schemas.artifact import ArtifactType, StorageBackend
from pydantic import BaseModel, Field

logger = logging.getLogger("nova.storage.artifact")


class StoredArtifact(BaseModel):
    """Metadata for a stored artifact."""
    artifact_id: str = Field(description="Unique artifact identifier")
    run_id: str = Field(description="Run that produced this artifact")
    filename: str = Field(description="Original filename")
    artifact_type: ArtifactType = Field(description="Type of artifact")
    storage_backend: StorageBackend = Field(description="Storage backend used")
    storage_uri: str = Field(description="URI to retrieve artifact")
    size_bytes: int = Field(ge=0, description="Size in bytes")
    checksum: str = Field(description="SHA256 checksum")
    content_type: str = Field(description="MIME content type")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ArtifactStore(ABC):
    """Abstract base class for artifact storage backends."""

    @abstractmethod
    def store(
        self,
        run_id: str,
        content: Union[bytes, str, BinaryIO],
        filename: str,
        artifact_type: ArtifactType = ArtifactType.BLOB,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StoredArtifact:
        """Store an artifact and return its metadata.

        Args:
            run_id: The run this artifact belongs to
            content: The artifact content (bytes, string, or file-like object)
            filename: Original filename or identifier
            artifact_type: Type of artifact
            metadata: Optional additional metadata

        Returns:
            StoredArtifact metadata including storage URI
        """
        pass

    @abstractmethod
    def retrieve(self, artifact_id: str) -> bytes:
        """Retrieve artifact content by ID.

        Args:
            artifact_id: Unique artifact identifier

        Returns:
            Artifact content as bytes
        """
        pass

    @abstractmethod
    def get_metadata(self, artifact_id: str) -> Optional[StoredArtifact]:
        """Get artifact metadata without retrieving content.

        Args:
            artifact_id: Unique artifact identifier

        Returns:
            StoredArtifact metadata or None if not found
        """
        pass

    @abstractmethod
    def list_by_run(self, run_id: str) -> List[StoredArtifact]:
        """List all artifacts for a run.

        Args:
            run_id: Run ID to list artifacts for

        Returns:
            List of StoredArtifact metadata
        """
        pass

    @abstractmethod
    def delete(self, artifact_id: str) -> bool:
        """Delete an artifact.

        Args:
            artifact_id: Artifact ID to delete

        Returns:
            True if deleted, False if not found
        """
        pass

    def _generate_id(self, run_id: str, filename: str) -> str:
        """Generate a unique artifact ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        content = f"{run_id}:{filename}:{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _compute_checksum(self, content: bytes) -> str:
        """Compute SHA256 checksum of content."""
        return hashlib.sha256(content).hexdigest()


class LocalArtifactStore(ArtifactStore):
    """Local filesystem artifact storage.

    Stores artifacts in a local directory, suitable for development
    and single-node deployments.
    """

    def __init__(self, base_path: str = "/tmp/nova_artifacts"):
        """Initialize local storage.

        Args:
            base_path: Base directory for artifact storage
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._metadata_path = self.base_path / "_metadata"
        self._metadata_path.mkdir(exist_ok=True)
        logger.info(f"LocalArtifactStore initialized at {self.base_path}")

    def store(
        self,
        run_id: str,
        content: Union[bytes, str, BinaryIO],
        filename: str,
        artifact_type: ArtifactType = ArtifactType.BLOB,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StoredArtifact:
        """Store artifact in local filesystem."""
        # Normalize content to bytes
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        elif hasattr(content, "read"):
            content_bytes = content.read()
        else:
            content_bytes = content

        # Generate artifact ID and paths
        artifact_id = self._generate_id(run_id, filename)
        run_dir = self.base_path / run_id
        run_dir.mkdir(exist_ok=True)

        artifact_path = run_dir / f"{artifact_id}_{filename}"
        storage_uri = f"file://{artifact_path}"

        # Write content
        artifact_path.write_bytes(content_bytes)

        # Create artifact metadata
        artifact = StoredArtifact(
            artifact_id=artifact_id,
            run_id=run_id,
            filename=filename,
            artifact_type=artifact_type,
            storage_backend=StorageBackend.LOCAL,
            storage_uri=storage_uri,
            size_bytes=len(content_bytes),
            checksum=self._compute_checksum(content_bytes),
            content_type=self._infer_content_type(filename, artifact_type),
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
        )

        # Store metadata
        metadata_file = self._metadata_path / f"{artifact_id}.json"
        metadata_file.write_text(artifact.model_dump_json())

        logger.info(
            "artifact_stored",
            extra={
                "artifact_id": artifact_id,
                "run_id": run_id,
                "filename": filename,
                "size_bytes": len(content_bytes),
                "backend": "local",
            }
        )

        return artifact

    def retrieve(self, artifact_id: str) -> bytes:
        """Retrieve artifact content from local filesystem."""
        artifact = self.get_metadata(artifact_id)
        if not artifact:
            raise FileNotFoundError(f"Artifact not found: {artifact_id}")

        # Parse file path from URI
        path = urlparse(artifact.storage_uri).path
        return Path(path).read_bytes()

    def get_metadata(self, artifact_id: str) -> Optional[StoredArtifact]:
        """Get artifact metadata."""
        metadata_file = self._metadata_path / f"{artifact_id}.json"
        if not metadata_file.exists():
            return None

        data = json.loads(metadata_file.read_text())
        return StoredArtifact(**data)

    def list_by_run(self, run_id: str) -> List[StoredArtifact]:
        """List all artifacts for a run."""
        artifacts = []
        for metadata_file in self._metadata_path.glob("*.json"):
            data = json.loads(metadata_file.read_text())
            if data.get("run_id") == run_id:
                artifacts.append(StoredArtifact(**data))
        return sorted(artifacts, key=lambda a: a.created_at, reverse=True)

    def delete(self, artifact_id: str) -> bool:
        """Delete artifact from local filesystem."""
        artifact = self.get_metadata(artifact_id)
        if not artifact:
            return False

        # Delete content file
        path = urlparse(artifact.storage_uri).path
        content_path = Path(path)
        if content_path.exists():
            content_path.unlink()

        # Delete metadata
        metadata_file = self._metadata_path / f"{artifact_id}.json"
        if metadata_file.exists():
            metadata_file.unlink()

        logger.info("artifact_deleted", extra={"artifact_id": artifact_id})
        return True

    def _infer_content_type(self, filename: str, artifact_type: ArtifactType) -> str:
        """Infer content type from filename and type."""
        ext = Path(filename).suffix.lower()
        content_types = {
            ".json": "application/json",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".html": "text/html",
            ".xml": "application/xml",
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".zip": "application/zip",
        }
        return content_types.get(ext, "application/octet-stream")


class S3ArtifactStore(ArtifactStore):
    """S3-compatible artifact storage.

    Supports AWS S3, MinIO, and other S3-compatible storage services.
    """

    def __init__(
        self,
        bucket: str,
        endpoint_url: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "us-east-1",
        prefix: str = "artifacts/",
    ):
        """Initialize S3 storage.

        Args:
            bucket: S3 bucket name
            endpoint_url: Custom endpoint (for MinIO, etc.)
            access_key: AWS access key (or from env)
            secret_key: AWS secret key (or from env)
            region: AWS region
            prefix: Key prefix for all artifacts
        """
        self.bucket = bucket
        self.endpoint_url = endpoint_url
        self.prefix = prefix.rstrip("/") + "/"
        self._client = None

        # Store credentials for lazy initialization
        self._access_key = access_key or os.getenv("AWS_ACCESS_KEY_ID")
        self._secret_key = secret_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self._region = region

        logger.info(
            "S3ArtifactStore initialized",
            extra={
                "bucket": bucket,
                "endpoint": endpoint_url or "aws",
                "prefix": prefix,
            }
        )

    def _get_client(self):
        """Lazy-load boto3 client."""
        if self._client is None:
            try:
                import boto3
                from botocore.config import Config

                config = Config(
                    signature_version="s3v4",
                    retries={"max_attempts": 3, "mode": "adaptive"},
                )

                self._client = boto3.client(
                    "s3",
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self._access_key,
                    aws_secret_access_key=self._secret_key,
                    region_name=self._region,
                    config=config,
                )
            except ImportError:
                raise ImportError("boto3 required for S3 storage: pip install boto3")

        return self._client

    def store(
        self,
        run_id: str,
        content: Union[bytes, str, BinaryIO],
        filename: str,
        artifact_type: ArtifactType = ArtifactType.BLOB,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StoredArtifact:
        """Store artifact in S3."""
        # Normalize content to bytes
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        elif hasattr(content, "read"):
            content_bytes = content.read()
        else:
            content_bytes = content

        # Generate artifact ID and key
        artifact_id = self._generate_id(run_id, filename)
        s3_key = f"{self.prefix}{run_id}/{artifact_id}_{filename}"
        storage_uri = f"s3://{self.bucket}/{s3_key}"

        # Determine content type
        content_type = self._infer_content_type(filename, artifact_type)

        # Upload to S3
        client = self._get_client()
        client.put_object(
            Bucket=self.bucket,
            Key=s3_key,
            Body=content_bytes,
            ContentType=content_type,
            Metadata={
                "artifact_id": artifact_id,
                "run_id": run_id,
                "artifact_type": artifact_type.value,
                "checksum": self._compute_checksum(content_bytes),
            },
        )

        # Also store metadata as a sidecar JSON
        metadata_key = f"{self.prefix}_metadata/{artifact_id}.json"
        artifact = StoredArtifact(
            artifact_id=artifact_id,
            run_id=run_id,
            filename=filename,
            artifact_type=artifact_type,
            storage_backend=StorageBackend.S3,
            storage_uri=storage_uri,
            size_bytes=len(content_bytes),
            checksum=self._compute_checksum(content_bytes),
            content_type=content_type,
            metadata=metadata or {},
            created_at=datetime.now(timezone.utc),
        )

        client.put_object(
            Bucket=self.bucket,
            Key=metadata_key,
            Body=artifact.model_dump_json().encode(),
            ContentType="application/json",
        )

        logger.info(
            "artifact_stored",
            extra={
                "artifact_id": artifact_id,
                "run_id": run_id,
                "filename": filename,
                "size_bytes": len(content_bytes),
                "backend": "s3",
                "bucket": self.bucket,
            }
        )

        return artifact

    def retrieve(self, artifact_id: str) -> bytes:
        """Retrieve artifact content from S3."""
        artifact = self.get_metadata(artifact_id)
        if not artifact:
            raise FileNotFoundError(f"Artifact not found: {artifact_id}")

        # Parse S3 key from URI
        parsed = urlparse(artifact.storage_uri)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")

        client = self._get_client()
        response = client.get_object(Bucket=bucket, Key=key)
        return response["Body"].read()

    def get_metadata(self, artifact_id: str) -> Optional[StoredArtifact]:
        """Get artifact metadata from S3."""
        client = self._get_client()
        metadata_key = f"{self.prefix}_metadata/{artifact_id}.json"

        try:
            response = client.get_object(Bucket=self.bucket, Key=metadata_key)
            data = json.loads(response["Body"].read().decode())
            return StoredArtifact(**data)
        except client.exceptions.NoSuchKey:
            return None
        except Exception as e:
            logger.warning(f"Failed to get metadata: {e}")
            return None

    def list_by_run(self, run_id: str) -> List[StoredArtifact]:
        """List all artifacts for a run from S3."""
        client = self._get_client()
        prefix = f"{self.prefix}_metadata/"

        artifacts = []
        paginator = client.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                try:
                    response = client.get_object(Bucket=self.bucket, Key=obj["Key"])
                    data = json.loads(response["Body"].read().decode())
                    if data.get("run_id") == run_id:
                        artifacts.append(StoredArtifact(**data))
                except Exception as e:
                    logger.warning(f"Failed to read metadata: {e}")

        return sorted(artifacts, key=lambda a: a.created_at, reverse=True)

    def delete(self, artifact_id: str) -> bool:
        """Delete artifact from S3."""
        artifact = self.get_metadata(artifact_id)
        if not artifact:
            return False

        client = self._get_client()

        # Delete content
        parsed = urlparse(artifact.storage_uri)
        content_key = parsed.path.lstrip("/")
        client.delete_object(Bucket=self.bucket, Key=content_key)

        # Delete metadata
        metadata_key = f"{self.prefix}_metadata/{artifact_id}.json"
        client.delete_object(Bucket=self.bucket, Key=metadata_key)

        logger.info("artifact_deleted", extra={"artifact_id": artifact_id})
        return True

    def _infer_content_type(self, filename: str, artifact_type: ArtifactType) -> str:
        """Infer content type from filename and type."""
        ext = Path(filename).suffix.lower()
        content_types = {
            ".json": "application/json",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".html": "text/html",
            ".xml": "application/xml",
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".zip": "application/zip",
        }
        return content_types.get(ext, "application/octet-stream")


# Singleton instance
_store: Optional[ArtifactStore] = None


def get_artifact_store() -> ArtifactStore:
    """Get the configured artifact store instance.

    Configuration via environment variables:
    - ARTIFACT_BACKEND: 'local' or 's3' (default: local)
    - ARTIFACT_LOCAL_PATH: Path for local storage
    - ARTIFACT_S3_BUCKET: S3 bucket name
    - ARTIFACT_S3_ENDPOINT: S3 endpoint URL (for MinIO)
    - ARTIFACT_S3_PREFIX: Key prefix
    """
    global _store
    if _store is None:
        backend = os.getenv("ARTIFACT_BACKEND", "local").lower()

        if backend == "s3":
            _store = S3ArtifactStore(
                bucket=os.getenv("ARTIFACT_S3_BUCKET", "nova-artifacts"),
                endpoint_url=os.getenv("ARTIFACT_S3_ENDPOINT"),
                prefix=os.getenv("ARTIFACT_S3_PREFIX", "artifacts/"),
            )
        else:
            _store = LocalArtifactStore(
                base_path=os.getenv("ARTIFACT_LOCAL_PATH", "/tmp/nova_artifacts")
            )

    return _store
