# Layer: L2 — Adapter
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Base class for file storage adapters
# Callers: File storage adapter implementations
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-147, GAP-148

"""
File Storage Base Adapter

Provides abstract interface for file storage operations.
All file storage adapters must implement this interface.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator, BinaryIO, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
    """Metadata for a stored file."""

    key: str
    size: int
    content_type: Optional[str] = None
    last_modified: Optional[datetime] = None
    etag: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "key": self.key,
            "size": self.size,
            "content_type": self.content_type,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "etag": self.etag,
            "metadata": self.metadata,
        }


@dataclass
class UploadResult:
    """Result of an upload operation."""

    key: str
    size: int
    etag: Optional[str] = None
    version_id: Optional[str] = None
    location: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.key is not None


@dataclass
class DownloadResult:
    """Result of a download operation."""

    content: bytes
    metadata: FileMetadata

    @property
    def success(self) -> bool:
        return len(self.content) > 0


@dataclass
class ListResult:
    """Result of a list operation."""

    files: List[FileMetadata]
    continuation_token: Optional[str] = None
    is_truncated: bool = False


class FileStorageAdapter(ABC):
    """
    Abstract base class for file storage adapters.

    All file storage implementations must implement these methods.
    """

    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to the file storage.

        Returns:
            True if connected successfully
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the file storage."""
        pass

    @abstractmethod
    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        """
        Upload a file to storage.

        Args:
            key: Storage key/path
            data: File data (bytes or file-like object)
            content_type: MIME type
            metadata: Custom metadata

        Returns:
            UploadResult
        """
        pass

    @abstractmethod
    async def download(
        self,
        key: str,
    ) -> DownloadResult:
        """
        Download a file from storage.

        Args:
            key: Storage key/path

        Returns:
            DownloadResult
        """
        pass

    @abstractmethod
    async def download_stream(
        self,
        key: str,
        chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """
        Stream download a file from storage.

        Args:
            key: Storage key/path
            chunk_size: Size of each chunk

        Yields:
            Chunks of file data
        """
        pass

    @abstractmethod
    async def delete(
        self,
        key: str,
    ) -> bool:
        """
        Delete a file from storage.

        Args:
            key: Storage key/path

        Returns:
            True if deleted
        """
        pass

    @abstractmethod
    async def delete_many(
        self,
        keys: List[str],
    ) -> int:
        """
        Delete multiple files from storage.

        Args:
            keys: List of storage keys/paths

        Returns:
            Number of files deleted
        """
        pass

    @abstractmethod
    async def exists(
        self,
        key: str,
    ) -> bool:
        """
        Check if a file exists in storage.

        Args:
            key: Storage key/path

        Returns:
            True if exists
        """
        pass

    @abstractmethod
    async def get_metadata(
        self,
        key: str,
    ) -> Optional[FileMetadata]:
        """
        Get file metadata without downloading content.

        Args:
            key: Storage key/path

        Returns:
            FileMetadata or None if not found
        """
        pass

    @abstractmethod
    async def list_files(
        self,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        continuation_token: Optional[str] = None,
    ) -> ListResult:
        """
        List files in storage.

        Args:
            prefix: Optional key prefix filter
            max_keys: Maximum number of results
            continuation_token: Token for pagination

        Returns:
            ListResult
        """
        pass

    @abstractmethod
    async def generate_presigned_url(
        self,
        key: str,
        operation: str = "get",  # get or put
        expires_in: int = 3600,
    ) -> str:
        """
        Generate a presigned URL for direct access.

        Args:
            key: Storage key/path
            operation: "get" for download, "put" for upload
            expires_in: URL expiration in seconds

        Returns:
            Presigned URL
        """
        pass

    @abstractmethod
    async def copy(
        self,
        source_key: str,
        dest_key: str,
    ) -> bool:
        """
        Copy a file within storage.

        Args:
            source_key: Source key/path
            dest_key: Destination key/path

        Returns:
            True if copied
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if the file storage is healthy.

        Returns:
            True if healthy
        """
        try:
            await self.list_files(max_keys=1)
            return True
        except Exception as e:
            logger.warning(f"File storage health check failed: {e}")
            return False
