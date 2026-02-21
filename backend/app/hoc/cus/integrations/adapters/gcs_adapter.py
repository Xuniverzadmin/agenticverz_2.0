# capability_id: CAP-018
# Layer: L2 — Adapter
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Google Cloud Storage file storage adapter
# Callers: DataIngestionExecutor, ExportService
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-148 (GCS File Storage Adapter)

"""
Google Cloud Storage File Storage Adapter (GAP-148)

Provides integration with Google Cloud Storage:
- Bucket operations
- Resumable uploads for large files
- Signed URLs
- Object lifecycle management
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, AsyncIterator, BinaryIO, Dict, List, Optional

from .base import (
    DownloadResult,
    FileMetadata,
    FileStorageAdapter,
    ListResult,
    UploadResult,
)

logger = logging.getLogger(__name__)


class GCSAdapter(FileStorageAdapter):
    """
    Google Cloud Storage file storage adapter.

    Uses google-cloud-storage with async wrappers.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        project_id: Optional[str] = None,
        credentials_path: Optional[str] = None,
        **kwargs,
    ):
        self._bucket_name = bucket_name or os.getenv("GCS_BUCKET", "aos-storage")
        self._project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self._credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self._client = None
        self._bucket = None

    async def connect(self) -> bool:
        """Connect to GCS."""
        try:
            from google.cloud import storage
            import asyncio

            # Create client in thread pool (sync library)
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(
                None,
                lambda: storage.Client(project=self._project_id),
            )

            # Get or create bucket
            try:
                self._bucket = await loop.run_in_executor(
                    None,
                    lambda: self._client.get_bucket(self._bucket_name),
                )
            except Exception:
                logger.info(f"Creating GCS bucket: {self._bucket_name}")
                self._bucket = await loop.run_in_executor(
                    None,
                    lambda: self._client.create_bucket(self._bucket_name),
                )

            logger.info(f"Connected to GCS bucket: {self._bucket_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to GCS: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from GCS."""
        self._client = None
        self._bucket = None
        logger.info("Disconnected from GCS")

    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        """Upload a file to GCS."""
        if not self._bucket:
            raise RuntimeError("Not connected to GCS")

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            blob = self._bucket.blob(key)

            if content_type:
                blob.content_type = content_type
            if metadata:
                blob.metadata = metadata

            if isinstance(data, bytes):
                await loop.run_in_executor(
                    None,
                    lambda: blob.upload_from_string(data, content_type=content_type),
                )
                size = len(data)
            else:
                await loop.run_in_executor(
                    None,
                    lambda: blob.upload_from_file(data, content_type=content_type),
                )
                data.seek(0, 2)
                size = data.tell()

            # Reload to get metadata
            await loop.run_in_executor(None, blob.reload)

            logger.info(f"Uploaded {key} to GCS ({size} bytes)")
            return UploadResult(
                key=key,
                size=size,
                etag=blob.etag,
                version_id=str(blob.generation),
                location=f"gs://{self._bucket_name}/{key}",
            )

        except Exception as e:
            logger.error(f"GCS upload failed: {e}")
            raise

    async def download(
        self,
        key: str,
    ) -> DownloadResult:
        """Download a file from GCS."""
        if not self._bucket:
            raise RuntimeError("Not connected to GCS")

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            blob = self._bucket.blob(key)

            content = await loop.run_in_executor(
                None,
                blob.download_as_bytes,
            )

            # Get metadata
            await loop.run_in_executor(None, blob.reload)

            metadata = FileMetadata(
                key=key,
                size=blob.size or len(content),
                content_type=blob.content_type,
                last_modified=blob.updated,
                etag=blob.etag,
                metadata=blob.metadata or {},
            )

            logger.debug(f"Downloaded {key} from GCS ({metadata.size} bytes)")
            return DownloadResult(content=content, metadata=metadata)

        except Exception as e:
            logger.error(f"GCS download failed: {e}")
            raise

    async def download_stream(
        self,
        key: str,
        chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """Stream download a file from GCS."""
        if not self._bucket:
            raise RuntimeError("Not connected to GCS")

        import asyncio
        import io

        loop = asyncio.get_event_loop()
        blob = self._bucket.blob(key)

        # Download to buffer and yield chunks
        buffer = io.BytesIO()
        await loop.run_in_executor(
            None,
            lambda: blob.download_to_file(buffer),
        )

        buffer.seek(0)
        while True:
            chunk = buffer.read(chunk_size)
            if not chunk:
                break
            yield chunk

    async def delete(
        self,
        key: str,
    ) -> bool:
        """Delete a file from GCS."""
        if not self._bucket:
            raise RuntimeError("Not connected to GCS")

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            blob = self._bucket.blob(key)

            await loop.run_in_executor(None, blob.delete)

            logger.info(f"Deleted {key} from GCS")
            return True

        except Exception as e:
            logger.error(f"GCS delete failed: {e}")
            return False

    async def delete_many(
        self,
        keys: List[str],
    ) -> int:
        """Delete multiple files from GCS."""
        if not self._bucket:
            raise RuntimeError("Not connected to GCS")

        if not keys:
            return 0

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            deleted_count = 0

            # GCS batch operations
            for key in keys:
                try:
                    blob = self._bucket.blob(key)
                    await loop.run_in_executor(None, blob.delete)
                    deleted_count += 1
                except Exception:
                    pass

            logger.info(f"Deleted {deleted_count} files from GCS")
            return deleted_count

        except Exception as e:
            logger.error(f"GCS delete_many failed: {e}")
            return 0

    async def exists(
        self,
        key: str,
    ) -> bool:
        """Check if a file exists in GCS."""
        if not self._bucket:
            raise RuntimeError("Not connected to GCS")

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            blob = self._bucket.blob(key)

            return await loop.run_in_executor(None, blob.exists)

        except Exception:
            return False

    async def get_metadata(
        self,
        key: str,
    ) -> Optional[FileMetadata]:
        """Get file metadata without downloading content."""
        if not self._bucket:
            raise RuntimeError("Not connected to GCS")

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            blob = self._bucket.blob(key)

            exists = await loop.run_in_executor(None, blob.exists)
            if not exists:
                return None

            await loop.run_in_executor(None, blob.reload)

            return FileMetadata(
                key=key,
                size=blob.size or 0,
                content_type=blob.content_type,
                last_modified=blob.updated,
                etag=blob.etag,
                metadata=blob.metadata or {},
            )

        except Exception:
            return None

    async def list_files(
        self,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        continuation_token: Optional[str] = None,
    ) -> ListResult:
        """List files in GCS."""
        if not self._bucket:
            raise RuntimeError("Not connected to GCS")

        try:
            import asyncio

            loop = asyncio.get_event_loop()

            # Build iterator params
            kwargs: Dict[str, Any] = {"max_results": max_keys}
            if prefix:
                kwargs["prefix"] = prefix
            if continuation_token:
                kwargs["page_token"] = continuation_token

            # List blobs
            blobs_iter = await loop.run_in_executor(
                None,
                lambda: list(self._bucket.list_blobs(**kwargs)),
            )

            files = []
            for blob in blobs_iter[:max_keys]:
                files.append(
                    FileMetadata(
                        key=blob.name,
                        size=blob.size or 0,
                        content_type=blob.content_type,
                        last_modified=blob.updated,
                        etag=blob.etag,
                    )
                )

            # Get next page token if available
            next_token = None
            is_truncated = len(blobs_iter) > max_keys

            return ListResult(
                files=files,
                continuation_token=next_token,
                is_truncated=is_truncated,
            )

        except Exception as e:
            logger.error(f"GCS list failed: {e}")
            return ListResult(files=[])

    async def generate_presigned_url(
        self,
        key: str,
        operation: str = "get",
        expires_in: int = 3600,
    ) -> str:
        """Generate a signed URL for GCS."""
        if not self._bucket:
            raise RuntimeError("Not connected to GCS")

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            blob = self._bucket.blob(key)

            expiration = timedelta(seconds=expires_in)
            method = "GET" if operation == "get" else "PUT"

            url = await loop.run_in_executor(
                None,
                lambda: blob.generate_signed_url(
                    expiration=expiration,
                    method=method,
                    version="v4",
                ),
            )

            return url

        except Exception as e:
            logger.error(f"GCS signed URL generation failed: {e}")
            raise

    async def copy(
        self,
        source_key: str,
        dest_key: str,
    ) -> bool:
        """Copy a file within GCS."""
        if not self._bucket:
            raise RuntimeError("Not connected to GCS")

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            source_blob = self._bucket.blob(source_key)
            dest_blob = self._bucket.blob(dest_key)

            await loop.run_in_executor(
                None,
                lambda: source_blob.reload(),
            )

            await loop.run_in_executor(
                None,
                lambda: self._bucket.copy_blob(source_blob, self._bucket, dest_key),
            )

            logger.info(f"Copied {source_key} to {dest_key} in GCS")
            return True

        except Exception as e:
            logger.error(f"GCS copy failed: {e}")
            return False
