"""Read-only internal API for the Tray Embedded estate."""

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from app.api.tray_deps import require_ops_role
from app.services.tray.estate import load_estate


router = APIRouter()


async def estate_loader(
    request: Request,
    workspace_id: str | None = Query(default=None),
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> dict[str, Any]:
    """Resolve workspace context and invoke the injectable estate loader."""
    state_workspace_id = getattr(request.state, "workspace_id", None)
    resolved = workspace_id or x_workspace_id or state_workspace_id
    if resolved is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context is required",
        )
    return await load_estate(str(resolved))


# Friendly alias for callers that name dependency overrides by intent.
get_estate = estate_loader


def _value(item: Any, name: str, default: Any = None) -> Any:
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _serialized(item: Any) -> Any:
    if hasattr(item, "model_dump"):
        return item.model_dump()
    return item


def _overview_payload(estate: dict[str, Any]) -> dict[str, Any]:
    overview = _serialized(estate.get("overview", {}))
    payload = dict(overview) if isinstance(overview, dict) else {}
    payload.setdefault(
        "triage",
        [_serialized(signal) for signal in estate.get("triage", [])],
    )
    payload.setdefault("signal_counts", estate.get("signal_counts", {}))
    return payload


@router.get("/overview")
async def overview(
    _: Any = Depends(require_ops_role),
    estate: dict[str, Any] = Depends(estate_loader),
) -> dict[str, Any]:
    """Return aggregate estate health and the ranked triage queue."""
    return _overview_payload(estate)


@router.get("/solutions")
async def solutions(
    _: Any = Depends(require_ops_role),
    estate: dict[str, Any] = Depends(estate_loader),
) -> list[Any]:
    """Return the solution registry."""
    return [_serialized(item) for item in estate.get("solutions", [])]


def _matches_state(instance: Any, expected: str) -> bool:
    state = _value(instance, "state")
    enabled = _value(instance, "enabled", False)
    health = _value(instance, "health")
    health_status = _value(health, "status")
    return expected.lower() in {
        str(state).lower(),
        "enabled" if enabled else "disabled",
        str(health_status).lower(),
    }


def _matches_config(instance: Any, expected: str) -> bool:
    complete = bool(_value(instance, "config_complete", True))
    normalized = expected.lower()
    if normalized in {"complete", "configured", "healthy", "true"}:
        return complete
    if normalized in {"missing", "misconfigured", "incomplete", "false"}:
        return not complete
    return False


def _matches_auth(instance: Any, expected: str) -> bool:
    normalized = expected.lower()
    token_expired = bool(_value(instance, "token_expired", False))
    auth_broken = bool(_value(instance, "auth_broken", False))
    auth_healthy = bool(_value(instance, "auth_healthy", True))
    token_status = str(_value(instance, "token_status", "")).lower()
    if normalized == "expired":
        return token_expired or token_status == "expired"
    if normalized in {"broken", "unhealthy"}:
        return auth_broken or not auth_healthy
    if normalized in {"healthy", "active"}:
        return auth_healthy and not auth_broken and not token_expired
    return normalized == token_status


def _matches_error(instance: Any, expected: str) -> bool:
    health = _value(instance, "health")
    status_value = str(_value(health, "status", "")).lower()
    reasons = _value(health, "reasons", []) or []
    has_error = "error_spike" in reasons or status_value == "critical"
    normalized = expected.lower()
    if normalized in {"true", "error", "spike", "critical"}:
        return has_error
    if normalized in {"false", "none", "healthy"}:
        return not has_error
    return False


@router.get("/instances")
async def instances(
    state: str | None = None,
    config: str | None = None,
    auth: str | None = None,
    error: str | None = None,
    solution: str | None = None,
    user: str | None = None,
    _: Any = Depends(require_ops_role),
    estate: dict[str, Any] = Depends(estate_loader),
) -> list[Any]:
    """Return health-scored instances matching the requested filters."""
    rows = list(estate.get("instances", []))
    if state is not None:
        rows = [item for item in rows if _matches_state(item, state)]
    if config is not None:
        rows = [item for item in rows if _matches_config(item, config)]
    if auth is not None:
        rows = [item for item in rows if _matches_auth(item, auth)]
    if error is not None:
        rows = [item for item in rows if _matches_error(item, error)]
    if solution is not None:
        rows = [
            item
            for item in rows
            if solution
            in {
                str(_value(item, "solution_id", "")),
                str(_value(item, "solution_name", "")),
            }
        ]
    if user is not None:
        rows = [
            item
            for item in rows
            if user
            in {
                str(_value(item, "user_id", "")),
                str(_value(item, "external_user_id", "")),
            }
        ]
    return [_serialized(item) for item in rows]


@router.get("/instances/{instance_id}")
async def instance_detail(
    instance_id: str,
    _: Any = Depends(require_ops_role),
    estate: dict[str, Any] = Depends(estate_loader),
) -> Any:
    """Return one instance with workflow, slot, and execution detail."""
    for instance in estate.get("instances", []):
        if str(_value(instance, "id")) == instance_id:
            return _serialized(instance)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Tray solution instance not found",
    )


@router.get("/users")
async def users(
    _: Any = Depends(require_ops_role),
    estate: dict[str, Any] = Depends(estate_loader),
) -> list[Any]:
    """Return end users and their token/authentication health."""
    return [_serialized(item) for item in estate.get("users", [])]


@router.get("/insights/kpis")
async def insights_kpis(
    _: Any = Depends(require_ops_role),
    estate: dict[str, Any] = Depends(estate_loader),
) -> list[Any]:
    """Return execution KPI summaries."""
    return [_serialized(item) for item in estate.get("kpis", [])]


@router.get("/insights/timeseries")
async def insights_timeseries(
    _: Any = Depends(require_ops_role),
    estate: dict[str, Any] = Depends(estate_loader),
) -> Any:
    """Return the raw, provenance-marked Insights timeseries."""
    return _serialized(estate.get("timeseries", {"data": [], "source": "unofficial"}))
