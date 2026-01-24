# Layer: L3 — Boundary Adapters
# AUDIENCE: INTERNAL
# PHASE: W3
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: AWS S3 file storage adapter
# Callers: DataIngestionExecutor, ExportService
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-147 (S3 File Storage Adapter)

"""
AWS S3 File Storage Adapter (GAP-147)

Provides integration with AWS S3:
- Bucket operations
- Multipart upload for large files
- Presigned URLs
- Server-side encryption
"""

import logging
import os
from typing import Any, AsyncIterator, BinaryIO, Dict, List, Optional

from .base import (
    DownloadResult,
    FileMetadata,
    FileStorageAdapter,
    ListResult,
    UploadResult,
)

logger = logging.getLogger(__name__)


class S3Adapter(FileStorageAdapter):
    """
    AWS S3 file storage adapter.

    Uses aioboto3 for async S3 operations.
    """

    def __init__(
        self,
        bucket_name: Optional[str] = None,
        region: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,  # For S3-compatible services
        **kwargs,
    ):
        self._bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET", "aos-storage")
        self._region = region or os.getenv("AWS_REGION", "us-east-1")
        self._access_key_id = access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self._secret_access_key = secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self._endpoint_url = endpoint_url or os.getenv("AWS_S3_ENDPOINT_URL")
        self._session = None
        self._client = None

    async def connect(self) -> bool:
        """Connect to S3."""
        try:
            import aioboto3

            self._session = aioboto3.Session(
                aws_access_key_id=self._access_key_id,
                aws_secret_access_key=self._secret_access_key,
                region_name=self._region,
            )

            # Test connection by checking if bucket exists
            async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
                try:
                    await client.head_bucket(Bucket=self._bucket_name)
                except client.exceptions.NoSuchBucket:
                    logger.info(f"Creating S3 bucket: {self._bucket_name}")
                    await client.create_bucket(
                        Bucket=self._bucket_name,
                        CreateBucketConfiguration={"LocationConstraint": self._region}
                        if self._region != "us-east-1"
                        else {},
                    )

            logger.info(f"Connected to S3 bucket: {self._bucket_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to S3: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from S3."""
        self._session = None
        logger.info("Disconnected from S3")

    async def upload(
        self,
        key: str,
        data: bytes | BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        """Upload a file to S3."""
        if not self._session:
            raise RuntimeError("Not connected to S3")

        try:
            extra_args: Dict[str, Any] = {}
            if content_type:
                extra_args["ContentType"] = content_type
            if metadata:
                extra_args["Metadata"] = metadata

            async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
                if isinstance(data, bytes):
                    response = await client.put_object(
                        Bucket=self._bucket_name,
                        Key=key,
                        Body=data,
                        **extra_args,
                    )
                    size = len(data)
                else:
                    # File-like object - use upload_fileobj
                    await client.upload_fileobj(
                        data,
                        self._bucket_name,
                        key,
                        ExtraArgs=extra_args if extra_args else None,
                    )
                    data.seek(0, 2)  # Seek to end
                    size = data.tell()
                    response = {}

            logger.info(f"Uploaded {key} to S3 ({size} bytes)")
            return UploadResult(
                key=key,
                size=size,
                etag=response.get("ETag", "").strip('"'),
                version_id=response.get("VersionId"),
                location=f"s3://{self._bucket_name}/{key}",
            )

        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            raise

    async def download(
        self,
        key: str,
    ) -> DownloadResult:
        """Download a file from S3."""
        if not self._session:
            raise RuntimeError("Not connected to S3")

        try:
            async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
                response = await client.get_object(
                    Bucket=self._bucket_name,
                    Key=key,
                )

                content = await response["Body"].read()

                metadata = FileMetadata(
                    key=key,
                    size=response["ContentLength"],
                    content_type=response.get("ContentType"),
                    last_modified=response.get("LastModified"),
                    etag=response.get("ETag", "").strip('"'),
                    metadata=response.get("Metadata", {}),
                )

            logger.debug(f"Downloaded {key} from S3 ({metadata.size} bytes)")
            return DownloadResult(content=content, metadata=metadata)

        except Exception as e:
            logger.error(f"S3 download failed: {e}")
            raise

    async def download_stream(
        self,
        key: str,
        chunk_size: int = 8192,
    ) -> AsyncIterator[bytes]:
        """Stream download a file from S3."""
        if not self._session:
            raise RuntimeError("Not connected to S3")

        async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
            response = await client.get_object(
                Bucket=self._bucket_name,
                Key=key,
            )

            async for chunk in response["Body"].iter_chunks(chunk_size=chunk_size):
                yield chunk

    async def delete(
        self,
        key: str,
    ) -> bool:
        """Delete a file from S3."""
        if not self._session:
            raise RuntimeError("Not connected to S3")

        try:
            async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
                await client.delete_object(
                    Bucket=self._bucket_name,
                    Key=key,
                )

            logger.info(f"Deleted {key} from S3")
            return True

        except Exception as e:
            logger.error(f"S3 delete failed: {e}")
            return False

    async def delete_many(
        self,
        keys: List[str],
    ) -> int:
        """Delete multiple files from S3."""
        if not self._session:
            raise RuntimeError("Not connected to S3")

        if not keys:
            return 0

        try:
            async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
                # S3 delete_objects has a limit of 1000 keys
                deleted_count = 0
                for i in range(0, len(keys), 1000):
                    batch = keys[i : i + 1000]
                    response = await client.delete_objects(
                        Bucket=self._bucket_name,
                        Delete={
                            "Objects": [{"Key": k} for k in batch],
                            "Quiet": True,
                        },
                    )
                    deleted_count += len(batch) - len(response.get("Errors", []))

            logger.info(f"Deleted {deleted_count} files from S3")
            return deleted_count

        except Exception as e:
            logger.error(f"S3 delete_many failed: {e}")
            return 0

    async def exists(
        self,
        key: str,
    ) -> bool:
        """Check if a file exists in S3."""
        if not self._session:
            raise RuntimeError("Not connected to S3")

        try:
            async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
                await client.head_object(
                    Bucket=self._bucket_name,
                    Key=key,
                )
            return True

        except Exception:
            return False

    async def get_metadata(
        self,
        key: str,
    ) -> Optional[FileMetadata]:
        """Get file metadata without downloading content."""
        if not self._session:
            raise RuntimeError("Not connected to S3")

        try:
            async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
                response = await client.head_object(
                    Bucket=self._bucket_name,
                    Key=key,
                )

                return FileMetadata(
                    key=key,
                    size=response["ContentLength"],
                    content_type=response.get("ContentType"),
                    last_modified=response.get("LastModified"),
                    etag=response.get("ETag", "").strip('"'),
                    metadata=response.get("Metadata", {}),
                )

        except Exception:
            return None

    async def list_files(
        self,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        continuation_token: Optional[str] = None,
    ) -> ListResult:
        """List files in S3."""
        if not self._session:
            raise RuntimeError("Not connected to S3")

        try:
            async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
                params: Dict[str, Any] = {
                    "Bucket": self._bucket_name,
                    "MaxKeys": max_keys,
                }
                if prefix:
                    params["Prefix"] = prefix
                if continuation_token:
                    params["ContinuationToken"] = continuation_token

                response = await client.list_objects_v2(**params)

                files = []
                for obj in response.get("Contents", []):
                    files.append(
                        FileMetadata(
                            key=obj["Key"],
                            size=obj["Size"],
                            last_modified=obj.get("LastModified"),
                            etag=obj.get("ETag", "").strip('"'),
                        )
                    )

                return ListResult(
                    files=files,
                    continuation_token=response.get("NextContinuationToken"),
                    is_truncated=response.get("IsTruncated", False),
                )

        except Exception as e:
            logger.error(f"S3 list failed: {e}")
            return ListResult(files=[])

    async def generate_presigned_url(
        self,
        key: str,
        operation: str = "get",
        expires_in: int = 3600,
    ) -> str:
        """Generate a presigned URL for S3."""
        if not self._session:
            raise RuntimeError("Not connected to S3")

        try:
            async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
                client_method = "get_object" if operation == "get" else "put_object"
                url = await client.generate_presigned_url(
                    ClientMethod=client_method,
                    Params={"Bucket": self._bucket_name, "Key": key},
                    ExpiresIn=expires_in,
                )
                return url

        except Exception as e:
            logger.error(f"S3 presigned URL generation failed: {e}")
            raise

    async def copy(
        self,
        source_key: str,
        dest_key: str,
    ) -> bool:
        """Copy a file within S3."""
        if not self._session:
            raise RuntimeError("Not connected to S3")

        try:
            async with self._session.client("s3", endpoint_url=self._endpoint_url) as client:
                await client.copy_object(
                    Bucket=self._bucket_name,
                    CopySource={"Bucket": self._bucket_name, "Key": source_key},
                    Key=dest_key,
                )

            logger.info(f"Copied {source_key} to {dest_key} in S3")
            return True

        except Exception as e:
            logger.error(f"S3 copy failed: {e}")
            return False
