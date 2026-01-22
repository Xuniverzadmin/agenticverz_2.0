# Layer: L3 — Boundary Adapters
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: File storage adapters for object storage
# Callers: DataIngestionExecutor, ExportService
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-147, GAP-148 (File Storage Adapters)

"""
File Storage Adapters (GAP-147, GAP-148)

Provides adapters for object storage:
- AWS S3 (GAP-147)
- Google Cloud Storage (GAP-148)

Features:
- Unified interface for file operations
- Streaming upload/download
- Presigned URLs
- Multipart upload
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import FileStorageAdapter
    from .s3_adapter import S3Adapter
    from .gcs_adapter import GCSAdapter

__all__ = [
    "FileStorageAdapter",
    "S3Adapter",
    "GCSAdapter",
    "get_file_storage_adapter",
    "FileStorageType",
]


from enum import Enum


class FileStorageType(str, Enum):
    """Supported file storage types."""
    S3 = "s3"
    GCS = "gcs"
    LOCAL = "local"


def get_file_storage_adapter(
    storage_type: FileStorageType,
    **config,
):
    """
    Factory function to get a file storage adapter.

    Args:
        storage_type: Type of file storage
        **config: Storage-specific configuration

    Returns:
        FileStorageAdapter instance
    """
    if storage_type == FileStorageType.S3:
        from .s3_adapter import S3Adapter
        return S3Adapter(**config)
    elif storage_type == FileStorageType.GCS:
        from .gcs_adapter import GCSAdapter
        return GCSAdapter(**config)
    else:
        raise ValueError(f"Unsupported file storage type: {storage_type}")
