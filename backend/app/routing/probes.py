# M17 CARE - Capability Probes
# Real-time capability checking with Redis caching

import asyncio
import json
import logging
import os
import socket
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from .models import (
    PROBE_HARDNESS,
    CapabilityCheckResult,
    CapabilityHardness,
    CapabilityProbeResult,
    ProbeType,
)

logger = logging.getLogger("nova.routing.probes")

# Probe cache TTL in seconds
PROBE_CACHE_TTL = 60  # 1 minute cache
PROBE_TIMEOUT_MS = 100  # 100ms per probe (total <150ms target)


class CapabilityProber:
    """
    Real-time capability probing with Redis caching.

    Probes infrastructure dependencies to ensure agents can execute:
    - SMTP: Mail server reachability
    - DNS: DNS resolution working
    - API_KEY: Required API keys present and valid format
    - S3: Bucket reachability
    - HTTP: HTTP endpoint health
    - REDIS: Redis connectivity
    - DATABASE: Database connectivity
    - AGENT: Agent availability
    - SERVICE: Internal service health
    """

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url if redis_url is not None else os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Optional[redis.Redis] = None

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection (lazy init)."""
        if self._redis is None:
            try:
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
                await self._redis.ping()
            except Exception as e:
                logger.warning(f"Redis not available for probe caching: {e}")
                self._redis = None
        return self._redis

    async def _get_cached(self, cache_key: str) -> Optional[CapabilityProbeResult]:
        """Get cached probe result."""
        try:
            r = await self._get_redis()
            if r:
                cached = await r.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    result = CapabilityProbeResult(
                        probe_type=ProbeType(data["probe_type"]),
                        name=data["name"],
                        available=data["available"],
                        latency_ms=data["latency_ms"],
                        error=data.get("error"),
                        fix_instruction=data.get("fix_instruction"),
                        cached=True,
                        checked_at=datetime.fromisoformat(data["checked_at"]),
                    )
                    return result
        except Exception as e:
            logger.debug(f"Cache get failed: {e}")
        return None

    async def _set_cached(self, cache_key: str, result: CapabilityProbeResult) -> None:
        """Cache probe result."""
        try:
            r = await self._get_redis()
            if r:
                await r.setex(cache_key, PROBE_CACHE_TTL, json.dumps(result.to_dict()))
        except Exception as e:
            logger.debug(f"Cache set failed: {e}")

    def _cache_key(self, probe_type: ProbeType, name: str) -> str:
        """Generate cache key for probe."""
        return f"care:probe:{probe_type.value}:{name}"

    # =========================================================================
    # Individual Probes
    # =========================================================================

    async def probe_smtp(self, host: str = "localhost", port: int = 25) -> CapabilityProbeResult:
        """Probe SMTP server availability."""
        cache_key = self._cache_key(ProbeType.SMTP, f"{host}:{port}")
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        start = time.time()
        try:
            # Check if we can connect to SMTP port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(PROBE_TIMEOUT_MS / 1000)
            result_code = sock.connect_ex((host, port))
            sock.close()

            latency = (time.time() - start) * 1000
            available = result_code == 0

            result = CapabilityProbeResult(
                probe_type=ProbeType.SMTP,
                name=f"{host}:{port}",
                available=available,
                hardness=PROBE_HARDNESS[ProbeType.SMTP],
                latency_ms=latency,
                error=None if available else f"Connection refused (code {result_code})",
                fix_instruction=None if available else f"Ensure SMTP server is running on {host}:{port}",
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            result = CapabilityProbeResult(
                probe_type=ProbeType.SMTP,
                name=f"{host}:{port}",
                available=False,
                hardness=PROBE_HARDNESS[ProbeType.SMTP],
                latency_ms=latency,
                error=str(e),
                fix_instruction=f"Check network connectivity to SMTP server {host}:{port}",
            )

        await self._set_cached(cache_key, result)
        return result

    async def probe_dns(self, hostname: str = "google.com") -> CapabilityProbeResult:
        """Probe DNS resolution."""
        cache_key = self._cache_key(ProbeType.DNS, hostname)
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        start = time.time()
        try:
            socket.gethostbyname(hostname)
            latency = (time.time() - start) * 1000
            result = CapabilityProbeResult(
                probe_type=ProbeType.DNS,
                name=hostname,
                available=True,
                hardness=PROBE_HARDNESS[ProbeType.DNS],
                latency_ms=latency,
            )
        except socket.gaierror as e:
            latency = (time.time() - start) * 1000
            result = CapabilityProbeResult(
                probe_type=ProbeType.DNS,
                name=hostname,
                available=False,
                hardness=PROBE_HARDNESS[ProbeType.DNS],
                latency_ms=latency,
                error=str(e),
                fix_instruction="Check DNS configuration and network connectivity",
            )

        await self._set_cached(cache_key, result)
        return result

    async def probe_api_key(self, key_name: str, env_var: Optional[str] = None) -> CapabilityProbeResult:
        """Probe API key existence and format."""
        env_var = env_var or f"{key_name.upper()}_API_KEY"
        cache_key = self._cache_key(ProbeType.API_KEY, key_name)
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        start = time.time()
        key_value = os.environ.get(env_var)

        if key_value:
            # Basic format validation
            is_valid = len(key_value) >= 8  # Minimal key length
            latency = (time.time() - start) * 1000
            result = CapabilityProbeResult(
                probe_type=ProbeType.API_KEY,
                name=key_name,
                available=is_valid,
                hardness=PROBE_HARDNESS[ProbeType.API_KEY],
                latency_ms=latency,
                error=None if is_valid else f"API key {env_var} appears malformed",
                fix_instruction=None if is_valid else f"Check {env_var} format",
            )
        else:
            latency = (time.time() - start) * 1000
            result = CapabilityProbeResult(
                probe_type=ProbeType.API_KEY,
                name=key_name,
                available=False,
                hardness=PROBE_HARDNESS[ProbeType.API_KEY],
                latency_ms=latency,
                error=f"Missing environment variable: {env_var}",
                fix_instruction=f"Set {env_var} in environment or .env file",
            )

        await self._set_cached(cache_key, result)
        return result

    async def probe_http(self, url: str, timeout_ms: int = PROBE_TIMEOUT_MS) -> CapabilityProbeResult:
        """Probe HTTP endpoint health."""
        cache_key = self._cache_key(ProbeType.HTTP, url)
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        start = time.time()
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout_ms / 1000)) as response:
                    latency = (time.time() - start) * 1000
                    available = 200 <= response.status < 500
                    result = CapabilityProbeResult(
                        probe_type=ProbeType.HTTP,
                        name=url,
                        available=available,
                        hardness=PROBE_HARDNESS[ProbeType.HTTP],
                        latency_ms=latency,
                        error=None if available else f"HTTP {response.status}",
                        fix_instruction=None if available else f"Check endpoint {url}",
                        fallback_available=True,  # HTTP endpoints may have fallbacks
                    )
        except Exception as e:
            latency = (time.time() - start) * 1000
            result = CapabilityProbeResult(
                probe_type=ProbeType.HTTP,
                name=url,
                available=False,
                hardness=PROBE_HARDNESS[ProbeType.HTTP],
                latency_ms=latency,
                error=str(e),
                fix_instruction=f"Ensure {url} is reachable",
                fallback_available=True,  # HTTP endpoints may have fallbacks
            )

        await self._set_cached(cache_key, result)
        return result

    async def probe_redis(self, url: Optional[str] = None) -> CapabilityProbeResult:
        """Probe Redis connectivity."""
        url = url or self.redis_url
        cache_key = self._cache_key(ProbeType.REDIS, url.split("@")[-1] if "@" in url else url)

        start = time.time()
        try:
            r = redis.from_url(url, decode_responses=True)
            await asyncio.wait_for(r.ping(), timeout=PROBE_TIMEOUT_MS / 1000)
            await r.close()
            latency = (time.time() - start) * 1000
            result = CapabilityProbeResult(
                probe_type=ProbeType.REDIS,
                name=url.split("@")[-1] if "@" in url else url,
                available=True,
                hardness=PROBE_HARDNESS[ProbeType.REDIS],  # SOFT - caching only
                latency_ms=latency,
                fallback_available=True,  # Can operate without cache (slower path)
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            result = CapabilityProbeResult(
                probe_type=ProbeType.REDIS,
                name=url.split("@")[-1] if "@" in url else url,
                available=False,
                hardness=PROBE_HARDNESS[ProbeType.REDIS],  # SOFT - won't block routing
                latency_ms=latency,
                error=str(e),
                fix_instruction="Ensure Redis is running (optional - system operates in degraded mode)",
                fallback_available=True,  # Routing continues without caching
            )

        return result

    async def probe_database(self, url: Optional[str] = None) -> CapabilityProbeResult:
        """Probe database connectivity."""
        url = url if url is not None else os.environ.get("DATABASE_URL")
        if not url:
            return CapabilityProbeResult(
                probe_type=ProbeType.DATABASE,
                name="database",
                available=False,
                hardness=PROBE_HARDNESS[ProbeType.DATABASE],  # HARD - required
                error="DATABASE_URL not set",
                fix_instruction="Set DATABASE_URL environment variable",
            )

        # Extract host for cache key (hide password)
        host = url.split("@")[-1].split("/")[0] if "@" in url else "database"
        cache_key = self._cache_key(ProbeType.DATABASE, host)
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        start = time.time()
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            engine.dispose()
            latency = (time.time() - start) * 1000
            result = CapabilityProbeResult(
                probe_type=ProbeType.DATABASE,
                name=host,
                available=True,
                hardness=PROBE_HARDNESS[ProbeType.DATABASE],
                latency_ms=latency,
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            result = CapabilityProbeResult(
                probe_type=ProbeType.DATABASE,
                name=host,
                available=False,
                hardness=PROBE_HARDNESS[ProbeType.DATABASE],  # HARD - blocks routing
                latency_ms=latency,
                error=str(e),
                fix_instruction="Check DATABASE_URL and database connectivity",
            )

        await self._set_cached(cache_key, result)
        return result

    async def probe_agent(self, agent_id: str) -> CapabilityProbeResult:
        """Probe agent availability in registry."""
        cache_key = self._cache_key(ProbeType.AGENT, agent_id)
        cached = await self._get_cached(cache_key)
        if cached:
            return cached

        start = time.time()
        try:
            from ..agents.sba import get_sba_service

            sba_service = get_sba_service()
            agent = sba_service.get_agent(agent_id)
            latency = (time.time() - start) * 1000

            if agent and agent.enabled:
                result = CapabilityProbeResult(
                    probe_type=ProbeType.AGENT,
                    name=agent_id,
                    available=True,
                    hardness=PROBE_HARDNESS[ProbeType.AGENT],  # SOFT - may have fallbacks
                    latency_ms=latency,
                    fallback_available=True,  # Other agents can handle task
                )
            else:
                result = CapabilityProbeResult(
                    probe_type=ProbeType.AGENT,
                    name=agent_id,
                    available=False,
                    hardness=PROBE_HARDNESS[ProbeType.AGENT],  # SOFT - won't block
                    latency_ms=latency,
                    error="Agent not found or disabled" if not agent else "Agent disabled",
                    fix_instruction=f"Register agent {agent_id} or enable it",
                    fallback_available=True,  # Try other agents
                )
        except Exception as e:
            latency = (time.time() - start) * 1000
            result = CapabilityProbeResult(
                probe_type=ProbeType.AGENT,
                name=agent_id,
                available=False,
                hardness=PROBE_HARDNESS[ProbeType.AGENT],  # SOFT
                latency_ms=latency,
                error=str(e),
                fix_instruction=f"Check agent registry for {agent_id}",
                fallback_available=True,
            )

        await self._set_cached(cache_key, result)
        return result

    async def probe_service(self, service_name: str, health_url: str) -> CapabilityProbeResult:
        """Probe internal service health."""
        return await self.probe_http(health_url)

    # =========================================================================
    # Aggregated Capability Check
    # =========================================================================

    async def check_capabilities(
        self,
        dependencies: List[Dict[str, Any]],
        required_api_keys: Optional[List[str]] = None,
        check_database: bool = True,
        check_redis: bool = True,
    ) -> CapabilityCheckResult:
        """
        Check all required capabilities for an agent.

        Hard vs Soft dependency handling:
        - HARD failures (DATABASE, SMTP, DNS, API_KEY, S3) block routing
        - SOFT failures (REDIS, HTTP, AGENT, SERVICE) allow degraded operation

        Args:
            dependencies: List of dependency dicts from SBA schema
            required_api_keys: List of API key names to check
            check_database: Check database connectivity
            check_redis: Check Redis connectivity

        Returns:
            CapabilityCheckResult with all probe results
        """
        probes: List[CapabilityProbeResult] = []
        failed: List[CapabilityProbeResult] = []
        soft_failures: List[CapabilityProbeResult] = []
        hard_failures: List[CapabilityProbeResult] = []
        total_latency = 0.0

        # Build probe tasks
        tasks = []

        # Database probe (HARD dependency)
        if check_database:
            tasks.append(("database", self.probe_database()))

        # Redis probe (SOFT dependency - caching only)
        if check_redis:
            tasks.append(("redis", self.probe_redis()))

        # API key probes (HARD dependencies)
        if required_api_keys:
            for key_name in required_api_keys:
                tasks.append((f"api_key:{key_name}", self.probe_api_key(key_name)))

        # Dependency probes
        for dep in dependencies:
            dep_type = dep.get("type", "service")
            dep_name = dep.get("name", "")

            if dep_type == "agent":
                tasks.append((f"agent:{dep_name}", self.probe_agent(dep_name)))
            elif dep_type == "api":
                # Check API key (HARD)
                tasks.append((f"api_key:{dep_name}", self.probe_api_key(dep_name)))
            elif dep_type == "service":
                # Check service health URL if provided (SOFT)
                health_url = dep.get("health_url")
                if health_url:
                    tasks.append((f"service:{dep_name}", self.probe_http(health_url)))

        # Execute all probes concurrently
        if tasks:
            results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    probe_result = CapabilityProbeResult(
                        probe_type=ProbeType.SERVICE,
                        name=tasks[i][0],
                        available=False,
                        hardness=CapabilityHardness.SOFT,  # Unknown probes default to SOFT
                        error=str(result),
                        fallback_available=True,
                    )
                else:
                    probe_result = result

                probes.append(probe_result)
                total_latency += probe_result.latency_ms

                # Classify failures by hardness
                if not probe_result.available:
                    failed.append(probe_result)
                    if probe_result.is_blocking():
                        hard_failures.append(probe_result)
                    else:
                        soft_failures.append(probe_result)

        # Build error summary (prioritize HARD failures)
        error_summary = None
        if hard_failures:
            errors = [f"[HARD] {p.name}: {p.error}" for p in hard_failures]
            error_summary = "; ".join(errors)
        elif soft_failures:
            errors = [f"[SOFT] {p.name}: {p.error}" for p in soft_failures]
            error_summary = f"Degraded mode: {'; '.join(errors)}"

        # Routing passes if no HARD failures (soft failures allowed)
        routing_passed = len(hard_failures) == 0
        degraded = routing_passed and len(soft_failures) > 0

        if degraded:
            logger.warning(f"CARE operating in degraded mode: {len(soft_failures)} soft dependencies unavailable")

        return CapabilityCheckResult(
            passed=routing_passed,
            probes=probes,
            failed_probes=failed,
            soft_failures=soft_failures,
            hard_failures=hard_failures,
            total_latency_ms=total_latency,
            error_summary=error_summary,
            degraded=degraded,
        )


# =============================================================================
# Singleton
# =============================================================================

_prober: Optional[CapabilityProber] = None


def get_capability_prober() -> CapabilityProber:
    """Get singleton capability prober instance."""
    global _prober
    if _prober is None:
        _prober = CapabilityProber()
    return _prober
