# Layer: L3 — Boundary Adapters
# AUDIENCE: INTERNAL
# PHASE: W3
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: AWS Lambda serverless adapter
# Callers: SkillExecutor, WorkflowEngine
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-149 (AWS Lambda Serverless Adapter)

"""
AWS Lambda Serverless Adapter (GAP-149)

Provides integration with AWS Lambda:
- Sync and async invocation
- Payload encoding/decoding
- Log retrieval
- Function management
"""

import asyncio
import base64
import json
import logging
import os
from typing import Any, Dict, List, Optional

from .base import (
    FunctionInfo,
    InvocationRequest,
    InvocationResult,
    InvocationType,
    ServerlessAdapter,
)

logger = logging.getLogger(__name__)


class LambdaAdapter(ServerlessAdapter):
    """
    AWS Lambda serverless adapter.

    Uses aioboto3 for async Lambda operations.
    """

    def __init__(
        self,
        region: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        **kwargs,
    ):
        self._region = region or os.getenv("AWS_REGION", "us-east-1")
        self._access_key_id = access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self._secret_access_key = secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self._session = None

    async def connect(self) -> bool:
        """Connect to AWS Lambda."""
        try:
            import aioboto3

            self._session = aioboto3.Session(
                aws_access_key_id=self._access_key_id,
                aws_secret_access_key=self._secret_access_key,
                region_name=self._region,
            )

            # Test connection
            async with self._session.client("lambda") as client:
                await client.list_functions(MaxItems=1)

            logger.info(f"Connected to AWS Lambda in {self._region}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to AWS Lambda: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from AWS Lambda."""
        self._session = None
        logger.info("Disconnected from AWS Lambda")

    async def invoke(
        self,
        request: InvocationRequest,
    ) -> InvocationResult:
        """Invoke a Lambda function."""
        if not self._session:
            raise RuntimeError("Not connected to AWS Lambda")

        try:
            import uuid
            from datetime import datetime, timezone

            async with self._session.client("lambda") as client:
                # Determine invocation type
                invocation_type_map = {
                    InvocationType.SYNC: "RequestResponse",
                    InvocationType.ASYNC: "Event",
                    InvocationType.DRY_RUN: "DryRun",
                }

                response = await client.invoke(
                    FunctionName=request.function_name,
                    InvocationType=invocation_type_map.get(request.invocation_type, "RequestResponse"),
                    Payload=json.dumps(request.payload).encode(),
                    LogType="Tail" if request.invocation_type == InvocationType.SYNC else "None",
                )

                # Parse response
                request_id = response.get("ResponseMetadata", {}).get("RequestId", str(uuid.uuid4()))
                status_code = response.get("StatusCode", 500)

                # Read payload
                payload = None
                error = None
                if "Payload" in response:
                    payload_bytes = await response["Payload"].read()
                    if payload_bytes:
                        try:
                            payload = json.loads(payload_bytes.decode())
                            # Check for Lambda error
                            if "errorMessage" in payload:
                                error = payload.get("errorMessage")
                                payload = None
                        except json.JSONDecodeError:
                            payload = {"raw": payload_bytes.decode()}

                # Check for function error
                if response.get("FunctionError"):
                    error = response.get("FunctionError")

                # Parse logs (base64 encoded)
                logs = None
                if "LogResult" in response:
                    try:
                        logs = base64.b64decode(response["LogResult"]).decode()
                    except Exception:
                        pass

                return InvocationResult(
                    request_id=request_id,
                    status_code=status_code,
                    payload=payload,
                    error=error,
                    logs=logs,
                )

        except Exception as e:
            logger.error(f"Lambda invocation failed: {e}")
            import uuid
            return InvocationResult(
                request_id=str(uuid.uuid4()),
                status_code=500,
                error=str(e),
            )

    async def invoke_batch(
        self,
        requests: List[InvocationRequest],
        max_concurrent: int = 10,
    ) -> List[InvocationResult]:
        """Invoke multiple Lambda functions concurrently."""
        if not self._session:
            raise RuntimeError("Not connected to AWS Lambda")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def invoke_with_semaphore(request: InvocationRequest) -> InvocationResult:
            async with semaphore:
                return await self.invoke(request)

        tasks = [invoke_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                import uuid
                processed_results.append(
                    InvocationResult(
                        request_id=str(uuid.uuid4()),
                        status_code=500,
                        error=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results

    async def get_function_info(
        self,
        function_name: str,
    ) -> Optional[FunctionInfo]:
        """Get information about a Lambda function."""
        if not self._session:
            raise RuntimeError("Not connected to AWS Lambda")

        try:
            async with self._session.client("lambda") as client:
                response = await client.get_function(FunctionName=function_name)

                config = response.get("Configuration", {})

                return FunctionInfo(
                    name=config.get("FunctionName", function_name),
                    arn_or_uri=config.get("FunctionArn", ""),
                    runtime=config.get("Runtime"),
                    memory_mb=config.get("MemorySize"),
                    timeout_seconds=config.get("Timeout"),
                    last_modified=config.get("LastModified"),
                    description=config.get("Description"),
                    tags=response.get("Tags", {}),
                )

        except Exception as e:
            logger.error(f"Failed to get Lambda function info: {e}")
            return None

    async def list_functions(
        self,
        prefix: Optional[str] = None,
        max_results: int = 100,
    ) -> List[FunctionInfo]:
        """List Lambda functions."""
        if not self._session:
            raise RuntimeError("Not connected to AWS Lambda")

        try:
            functions = []
            marker = None

            async with self._session.client("lambda") as client:
                while len(functions) < max_results:
                    params: Dict[str, Any] = {"MaxItems": min(50, max_results - len(functions))}
                    if marker:
                        params["Marker"] = marker

                    response = await client.list_functions(**params)

                    for func in response.get("Functions", []):
                        name = func.get("FunctionName", "")
                        if prefix and not name.startswith(prefix):
                            continue

                        functions.append(
                            FunctionInfo(
                                name=name,
                                arn_or_uri=func.get("FunctionArn", ""),
                                runtime=func.get("Runtime"),
                                memory_mb=func.get("MemorySize"),
                                timeout_seconds=func.get("Timeout"),
                                last_modified=func.get("LastModified"),
                                description=func.get("Description"),
                            )
                        )

                    marker = response.get("NextMarker")
                    if not marker:
                        break

            return functions[:max_results]

        except Exception as e:
            logger.error(f"Failed to list Lambda functions: {e}")
            return []

    async def function_exists(
        self,
        function_name: str,
    ) -> bool:
        """Check if a Lambda function exists."""
        info = await self.get_function_info(function_name)
        return info is not None
