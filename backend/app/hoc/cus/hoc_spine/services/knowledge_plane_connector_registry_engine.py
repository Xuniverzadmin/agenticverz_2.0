# Layer: L4 — HOC Spine (Engine)
# AUDIENCE: INTERNAL
# Product: system-wide
# Temporal:
#   Trigger: api|worker (mediated retrieval)
#   Execution: async
# Lifecycle:
#   Emits: none
#   Subscribes: none
# Data Access:
#   Reads: knowledge_plane_registry (SSOT)
#   Writes: none
# Role: Resolve mediated retrieval plane_id -> connector binding (Phase 4)
# Callers: hoc_spine RetrievalMediator wiring
# Allowed Imports: hoc_spine drivers, hoc_spine orchestrator session context, app.models facts
# Forbidden Imports: L2 routes

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.hoc.cus.hoc_spine.drivers.knowledge_plane_registry_driver import KnowledgePlaneRegistryDriver
from app.hoc.cus.hoc_spine.orchestrator.operation_registry import get_async_session_context
from app.models.knowledge_lifecycle import KnowledgePlaneLifecycleState


@dataclass(frozen=True)
class UnsupportedConnector:
    """Placeholder connector when no runtime connector exists for a binding."""

    id: str
    connector_type: str
    connector_id: str

    async def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise RuntimeError(
            "Connector runtime not implemented for this knowledge plane binding. "
            f"connector_type={self.connector_type} connector_id={self.connector_id}"
        )


class HocCredentialServiceAdapter:
    """Adapter: hoc_spine CusCredentialService -> integrations CredentialService protocol."""

    def __init__(self, *, tenant_id: str) -> None:
        from app.hoc.cus.hoc_spine.services.cus_credential_engine import CusCredentialService

        self._svc = CusCredentialService()
        self._tenant_id = tenant_id

    async def get(self, credential_ref: str):
        from app.hoc.cus.integrations.L5_engines.types import Credential

        # resolve_credential is sync; keep adapter async for protocol compatibility.
        value = self._svc.resolve_credential(tenant_id=self._tenant_id, credential_ref=credential_ref)
        return Credential(value=value)


def _build_sql_gateway_connector(
    *,
    tenant_id: str,
    connector_id: str,
    plane_name: str,
    plane_config: Dict[str, Any],
):
    """
    Build a SqlGatewayService connector from plane config.

    Expected config keys:
    - connection_string_ref: str (credential ref)
    - templates: dict[str, {sql, parameters, ...}] (template registry)
    - allowed_templates: list[str] (optional; defaults to templates keys)
    """
    from app.hoc.cus.integrations.L5_engines.sql_gateway import (
        ParameterSpec,
        ParameterType,
        QueryTemplate,
        SqlGatewayConfig,
        SqlGatewayService,
    )
    from app.hoc.cus.integrations.L6_drivers.sql_gateway_driver import get_sql_gateway_driver

    connection_string_ref = str(plane_config.get("connection_string_ref") or "")
    if not connection_string_ref:
        raise RuntimeError("Missing connection_string_ref in knowledge plane config")

    templates_raw = plane_config.get("templates") or {}
    if not isinstance(templates_raw, dict):
        raise RuntimeError("Invalid templates config (expected object)")

    allowed_templates = plane_config.get("allowed_templates")
    if not isinstance(allowed_templates, list):
        allowed_templates = list(templates_raw.keys())

    template_registry: Dict[str, QueryTemplate] = {}
    for template_id, t in templates_raw.items():
        if not isinstance(t, dict):
            continue

        params_raw = t.get("parameters") or []
        parameters: list[ParameterSpec] = []
        if isinstance(params_raw, list):
            for p in params_raw:
                if not isinstance(p, dict) or "name" not in p or "param_type" not in p:
                    continue
                parameters.append(
                    ParameterSpec(
                        name=str(p["name"]),
                        param_type=ParameterType(str(p["param_type"])),
                        required=bool(p.get("required", True)),
                        default=p.get("default"),
                        description=str(p.get("description", "")),
                        max_length=p.get("max_length"),
                        min_value=p.get("min_value"),
                        max_value=p.get("max_value"),
                    )
                )

        template_registry[str(template_id)] = QueryTemplate(
            id=str(template_id),
            name=str(t.get("name") or template_id),
            description=str(t.get("description") or ""),
            sql=str(t.get("sql") or ""),
            parameters=parameters,
            read_only=bool(t.get("read_only", True)),
            max_rows=int(t.get("max_rows", plane_config.get("max_rows", 1000))),
            timeout_seconds=int(t.get("timeout_seconds", plane_config.get("timeout_seconds", 30))),
        )

    cfg = SqlGatewayConfig(
        id=str(connector_id),
        name=str(plane_name),
        connection_string_ref=connection_string_ref,
        allowed_templates=[str(x) for x in allowed_templates],
        max_rows=int(plane_config.get("max_rows", 1000)),
        max_result_bytes=int(plane_config.get("max_result_bytes", 5 * 1024 * 1024)),
        timeout_seconds=int(plane_config.get("timeout_seconds", 30)),
        read_only=bool(plane_config.get("read_only", True)),
        tenant_id=str(tenant_id),
    )

    return SqlGatewayService(
        config=cfg,
        template_registry=template_registry,
        credential_service=HocCredentialServiceAdapter(tenant_id=tenant_id),
        driver=get_sql_gateway_driver(),
    )


class DbKnowledgePlaneConnectorRegistry:
    """
    ConnectorRegistry backed by the canonical knowledge_plane_registry SSOT.

    Contract:
    - Only ACTIVE governed planes are resolvable.
    - Connector identity is derived from the registry binding.
    """

    def __init__(self, driver: Optional[KnowledgePlaneRegistryDriver] = None) -> None:
        self._driver = driver or KnowledgePlaneRegistryDriver()

    async def resolve(self, tenant_id: str, plane_id: str):
        async with get_async_session_context() as session:
            record = await self._driver.get_by_id(session, tenant_id=tenant_id, plane_id=plane_id)

        if record is None:
            return None

        if KnowledgePlaneLifecycleState(record.lifecycle_state_value) != KnowledgePlaneLifecycleState.ACTIVE:
            return None

        config = record.config if isinstance(record.config, dict) else {}
        connector_type = str(record.connector_type).lower()

        # Phase 6: build runtime connectors for supported bindings.
        if connector_type in ("sql", "sql_gateway"):
            return _build_sql_gateway_connector(
                tenant_id=tenant_id,
                connector_id=record.connector_id,
                plane_name=record.plane_name,
                plane_config=config,
            )

        return UnsupportedConnector(
            id=record.connector_id,
            connector_type=record.connector_type,
            connector_id=record.connector_id,
        )


_connector_registry: Optional[DbKnowledgePlaneConnectorRegistry] = None


def get_db_knowledge_plane_connector_registry() -> DbKnowledgePlaneConnectorRegistry:
    global _connector_registry
    if _connector_registry is None:
        _connector_registry = DbKnowledgePlaneConnectorRegistry()
    return _connector_registry


__all__ = [
    "DbKnowledgePlaneConnectorRegistry",
    "UnsupportedConnector",
    "get_db_knowledge_plane_connector_registry",
]
