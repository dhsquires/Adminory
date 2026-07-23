"""Read-only orchestration for a workspace's Tray estate."""

import asyncio
from collections import Counter
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.tray import TrayCredential, TrayCredentialProvider
from app.schemas.tray import (
    EndUserDTO,
    KpiSummary,
    SolutionDTO,
    SolutionInstanceDTO,
)
from app.services.tray.client import TrayClient
from app.services.tray.health import estate_overview, score_instance


def _first(value: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in value and value[key] is not None:
            return value[key]
    return default


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _as_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("items", "data", "nodes", "solutionInstances", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = _as_items(value)
            if nested:
                return nested
    return []


def _solution(value: dict[str, Any]) -> SolutionDTO:
    current_version = _first(value, "version", "versionNumber")
    latest_version = _first(value, "latestVersion", "latest_version", default=current_version)
    return SolutionDTO(
        id=str(_first(value, "id", "solutionId", default="")),
        name=str(_first(value, "name", "title", default="")),
        state=_first(value, "state", "status"),
        version=str(current_version) if current_version is not None else None,
        latest_version=str(latest_version) if latest_version is not None else None,
        active_instances=int(
            _first(value, "activeInstances", "active_instances", default=0)
        ),
        drift=bool(
            _first(value, "drift", "versionDrift", "version_drift", default=False)
            or (
                current_version is not None
                and latest_version is not None
                and str(current_version) != str(latest_version)
            )
        ),
        source="official",
    )


def _instance(value: dict[str, Any]) -> SolutionInstanceDTO:
    enabled = bool(_first(value, "enabled", default=False))
    missing_config = _first(
        value,
        "missingRequiredConfig",
        "missing_required_config",
        default=[],
    )
    if not isinstance(missing_config, list):
        missing_config = []
    token_status = _first(value, "tokenStatus", "token_status")
    auth_healthy = bool(
        _first(value, "authHealthy", "auth_healthy", default=True)
    )
    auth_broken = bool(
        _first(value, "authBroken", "auth_broken", default=not auth_healthy)
    )

    return SolutionInstanceDTO(
        id=str(_first(value, "id", "solutionInstanceId", default="")),
        name=str(_first(value, "name", "title", default="")),
        solution_id=_first(value, "solutionId", "solution_id"),
        solution_name=_first(value, "solutionName", "solution_name"),
        user_id=_first(value, "userId", "user_id"),
        external_user_id=_first(value, "externalUserId", "external_user_id"),
        enabled=enabled,
        ever_enabled=bool(
            _first(value, "everEnabled", "ever_enabled", default=enabled)
        ),
        state=_first(value, "state", "status"),
        version=(
            str(_first(value, "version", "solutionVersion"))
            if _first(value, "version", "solutionVersion") is not None
            else None
        ),
        config_complete=bool(
            _first(
                value,
                "configComplete",
                "config_complete",
                default=not missing_config,
            )
        ),
        missing_required_config=[str(item) for item in missing_config],
        auth_healthy=auth_healthy,
        auth_broken=auth_broken,
        token_expired=bool(
            _first(value, "tokenExpired", "token_expired", default=False)
            or (str(token_status).lower() == "expired")
        ),
        token_status=str(token_status) if token_status is not None else None,
        created_at=_as_datetime(_first(value, "createdAt", "created_at")),
        workflows=list(_first(value, "workflows", default=[]) or []),
        config_slots=list(
            _first(value, "configSlots", "config_slots", "configValues", default=[])
            or []
        ),
        auth_slots=list(
            _first(value, "authSlots", "auth_slots", "authValues", default=[]) or []
        ),
        recent_executions=list(
            _first(value, "recentExecutions", "recent_executions", default=[]) or []
        ),
        source="official",
    )


def _kpi(value: dict[str, Any]) -> KpiSummary:
    executions = int(
        _first(value, "executions", "totalExecutions", "total", default=0) or 0
    )
    failed = int(_first(value, "failed", "failures", "errors", default=0) or 0)
    successful = int(
        _first(
            value,
            "successful",
            "successes",
            "successfulExecutions",
            default=max(executions - failed, 0),
        )
        or 0
    )
    error_rate_value = _first(value, "errorRate", "error_rate")
    success_rate_value = _first(value, "successRate", "success_rate")
    error_rate = (
        float(error_rate_value)
        if error_rate_value is not None
        else failed / executions if executions else 0.0
    )
    success_rate = (
        float(success_rate_value)
        if success_rate_value is not None
        else successful / executions if executions else 1.0
    )
    instance_id = _first(value, "solutionInstanceId", "instanceId", "instance_id")
    return KpiSummary(
        instance_id=str(instance_id) if instance_id is not None else None,
        executions=executions,
        successful=successful,
        failed=failed,
        success_rate=success_rate,
        error_rate=error_rate,
        source="unofficial",
    )


def _users(instances: list[SolutionInstanceDTO]) -> list[EndUserDTO]:
    grouped: dict[str, list[SolutionInstanceDTO]] = {}
    for instance in instances:
        identifier = instance.external_user_id or instance.user_id
        if identifier is not None:
            grouped.setdefault(identifier, []).append(instance)

    return [
        EndUserDTO(
            external_user_id=identifier,
            user_id=next(
                (instance.user_id for instance in user_instances if instance.user_id),
                None,
            ),
            token_status=(
                "expired"
                if any(instance.token_expired for instance in user_instances)
                else "active"
            ),
            instance_count=len(user_instances),
            auth_healthy=all(instance.auth_healthy for instance in user_instances),
            source="official",
        )
        for identifier, user_instances in grouped.items()
    ]


async def _credential(workspace_id: str) -> TrayCredential:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(TrayCredential).where(
                TrayCredential.workspace_id == workspace_id,
            )
        )
        credential = result.scalar_one_or_none()
    if credential is None:
        raise LookupError(f"Tray credentials are not configured for {workspace_id}")
    return credential


async def load_estate(workspace_id: str) -> dict[str, Any]:
    """Load official estate data and optional unofficial execution insights."""
    credential = await _credential(workspace_id)
    provider = TrayCredentialProvider(credential)
    master_token = provider.get_master_token(workspace_id)
    session_bearer = provider.get_session_bearer(workspace_id)

    async with TrayClient(
        provider.get_region(workspace_id),
        master_token,
        session_bearer=session_bearer,
    ) as client:
        solution_rows, instance_rows = await asyncio.gather(
            client.solutions(master_token),
            client.solution_instances(master_token),
        )

        raw_kpis: dict[str, Any] = {}
        raw_instance_kpis: dict[str, Any] = {}
        timeseries: dict[str, Any] = {"data": [], "source": "unofficial"}
        if session_bearer is not None:
            raw_kpis, raw_instance_kpis, timeseries = await asyncio.gather(
                client.kpis(),
                client.list_solution_instances(),
                client.timeseries(),
            )

    solutions = [_solution(row) for row in solution_rows]
    instances = [_instance(row) for row in instance_rows]
    instance_counts = Counter(
        instance.solution_id for instance in instances if instance.enabled
    )
    solutions = [
        solution.model_copy(
            update={"active_instances": instance_counts.get(solution.id, 0)}
        )
        for solution in solutions
    ]

    kpis = [_kpi(row) for row in _as_items(raw_instance_kpis)]
    if not kpis and raw_kpis:
        kpis = [_kpi(raw_kpis)]
    kpi_by_instance = {
        kpi.instance_id: kpi for kpi in kpis if kpi.instance_id is not None
    }
    instances = [
        instance.model_copy(
            update={"health": score_instance(instance, kpi_by_instance.get(instance.id))}
        )
        for instance in instances
    ]
    users = _users(instances)
    overview = estate_overview(instances, users, solutions, kpis)

    return {
        "overview": overview,
        "solutions": solutions,
        "instances": instances,
        "users": users,
        "kpis": kpis,
        "timeseries": timeseries,
        "triage": overview.triage,
        "signal_counts": overview.signal_counts,
    }
