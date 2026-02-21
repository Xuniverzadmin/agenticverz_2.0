# capability_id: CAP-018
# Layer: L2 — Adapter
# AUDIENCE: CUSTOMER
# Product: system-wide
# Temporal:
#   Trigger: api
#   Execution: async
# Role: Google Cloud Functions serverless adapter
# Callers: SkillExecutor, WorkflowEngine
# Allowed Imports: L4, L6
# Forbidden Imports: L1, L2
# Reference: GAP-150 (Cloud Functions Serverless Adapter)

"""
Google Cloud Functions Serverless Adapter (GAP-150)

Provides integration with Google Cloud Functions:
- HTTP and event-triggered functions
- Async invocation via Pub/Sub
- Response parsing
- Function management
"""

import asyncio
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


class CloudFunctionsAdapter(ServerlessAdapter):
    """
    Google Cloud Functions serverless adapter.

    Uses google-cloud-functions and httpx for async operations.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        region: Optional[str] = None,
        credentials_path: Optional[str] = None,
        **kwargs,
    ):
        self._project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self._region = region or os.getenv("GCP_REGION", "us-central1")
        self._credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self._client = None
        self._http_client = None

    async def connect(self) -> bool:
        """Connect to Google Cloud Functions."""
        try:
            from google.cloud import functions_v2
            import httpx

            # Create the functions client
            loop = asyncio.get_event_loop()
            self._client = await loop.run_in_executor(
                None,
                functions_v2.FunctionServiceClient,
            )

            # Create HTTP client for function invocation
            self._http_client = httpx.AsyncClient(timeout=60.0)

            logger.info(f"Connected to Cloud Functions in {self._project_id}/{self._region}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Cloud Functions: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Cloud Functions."""
        if self._http_client:
            await self._http_client.aclose()
        self._client = None
        self._http_client = None
        logger.info("Disconnected from Cloud Functions")

    async def invoke(
        self,
        request: InvocationRequest,
    ) -> InvocationResult:
        """Invoke a Cloud Function."""
        if not self._client or not self._http_client:
            raise RuntimeError("Not connected to Cloud Functions")

        try:
            import uuid
            from datetime import datetime, timezone

            # Get function URL
            func_info = await self.get_function_info(request.function_name)
            if not func_info:
                return InvocationResult(
                    request_id=str(uuid.uuid4()),
                    status_code=404,
                    error=f"Function not found: {request.function_name}",
                )

            function_url = func_info.arn_or_uri

            # Invoke via HTTP
            start_time = datetime.now(timezone.utc)

            if request.invocation_type == InvocationType.DRY_RUN:
                # Just validate the function exists
                return InvocationResult(
                    request_id=str(uuid.uuid4()),
                    status_code=200,
                    payload={"validated": True},
                )

            # Make HTTP request to function
            headers = {"Content-Type": "application/json"}

            # For async invocation, use background execution
            if request.invocation_type == InvocationType.ASYNC:
                # Fire and forget - don't wait for response
                asyncio.create_task(
                    self._http_client.post(
                        function_url,
                        json=request.payload,
                        headers=headers,
                    )
                )
                return InvocationResult(
                    request_id=str(uuid.uuid4()),
                    status_code=202,
                    payload={"async": True, "function": request.function_name},
                )

            # Sync invocation
            response = await self._http_client.post(
                function_url,
                json=request.payload,
                headers=headers,
                timeout=request.timeout_seconds,
            )

            end_time = datetime.now(timezone.utc)
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Parse response
            payload = None
            error = None

            try:
                if response.content:
                    payload = response.json()
            except json.JSONDecodeError:
                payload = {"raw": response.text}

            if response.status_code >= 400:
                error = payload.get("error", response.text) if isinstance(payload, dict) else response.text

            return InvocationResult(
                request_id=response.headers.get("X-Cloud-Trace-Context", str(uuid.uuid4())),
                status_code=response.status_code,
                payload=payload if not error else None,
                error=error,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Cloud Functions invocation failed: {e}")
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
        """Invoke multiple Cloud Functions concurrently."""
        if not self._client:
            raise RuntimeError("Not connected to Cloud Functions")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def invoke_with_semaphore(request: InvocationRequest) -> InvocationResult:
            async with semaphore:
                return await self.invoke(request)

        tasks = [invoke_with_semaphore(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        processed_results = []
        for result in results:
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
        """Get information about a Cloud Function."""
        if not self._client:
            raise RuntimeError("Not connected to Cloud Functions")

        try:
            loop = asyncio.get_event_loop()

            # Build the full function name
            full_name = f"projects/{self._project_id}/locations/{self._region}/functions/{function_name}"

            func = await loop.run_in_executor(
                None,
                lambda: self._client.get_function(name=full_name),
            )

            # Get the HTTP trigger URL
            url = ""
            if func.service_config and func.service_config.uri:
                url = func.service_config.uri

            return FunctionInfo(
                name=function_name,
                arn_or_uri=url,
                runtime=func.build_config.runtime if func.build_config else None,
                memory_mb=func.service_config.available_memory if func.service_config else None,
                timeout_seconds=func.service_config.timeout_seconds if func.service_config else None,
                description=func.description,
                tags=dict(func.labels) if func.labels else {},
            )

        except Exception as e:
            logger.error(f"Failed to get Cloud Function info: {e}")
            return None

    async def list_functions(
        self,
        prefix: Optional[str] = None,
        max_results: int = 100,
    ) -> List[FunctionInfo]:
        """List Cloud Functions."""
        if not self._client:
            raise RuntimeError("Not connected to Cloud Functions")

        try:
            loop = asyncio.get_event_loop()
            parent = f"projects/{self._project_id}/locations/{self._region}"

            # List functions
            funcs_iter = await loop.run_in_executor(
                None,
                lambda: list(self._client.list_functions(parent=parent)),
            )

            functions = []
            for func in funcs_iter[:max_results]:
                # Extract function name from full name
                name = func.name.split("/")[-1]

                if prefix and not name.startswith(prefix):
                    continue

                # Get the HTTP trigger URL
                url = ""
                if func.service_config and func.service_config.uri:
                    url = func.service_config.uri

                functions.append(
                    FunctionInfo(
                        name=name,
                        arn_or_uri=url,
                        runtime=func.build_config.runtime if func.build_config else None,
                        memory_mb=func.service_config.available_memory if func.service_config else None,
                        timeout_seconds=func.service_config.timeout_seconds if func.service_config else None,
                        description=func.description,
                        tags=dict(func.labels) if func.labels else {},
                    )
                )

            return functions

        except Exception as e:
            logger.error(f"Failed to list Cloud Functions: {e}")
            return []

    async def function_exists(
        self,
        function_name: str,
    ) -> bool:
        """Check if a Cloud Function exists."""
        info = await self.get_function_info(function_name)
        return info is not None
