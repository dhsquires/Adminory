"""Read-only internal API for the Tray Embedded estate."""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any
from collections.abc import AsyncIterator
from urllib.parse import quote

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status

from app.api.tray_deps import require_ops_role
from app.models.tray import TrayCredentialProvider
from app.schemas.tray import (
    InstanceConfigUpdate,
    MutationResult,
    ProvisionUserIn,
    WizardUrlIn,
    validate_config_against_slots,
)
from app.services.tray.client import TrayClient
from app.services.tray.errors import TrayError
from app.services.tray.estate import _credential, load_estate
from app.services.tray.solutions import (
    SolutionsClient,
    UnofficialWritesDisabled,
    require_unofficial_writes,
)


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
    try:
        return await load_estate(str(resolved))
    except TrayError as exc:
        # Upstream Tray call failed (e.g. rejected/expired credentials). Surface a
        # clean gateway error with provenance; never leak token material.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Tray {exc.surface.value} call failed (status {exc.status}); "
            f"{'official' if exc.official else 'unofficial'} surface. "
            "Verify the workspace's Tray credentials.",
        ) from exc


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


@dataclass(frozen=True)
class TrayClientFactory:
    """Lazily open workspace-scoped credentials only for confirmed writes."""

    workspace_id: str

    @asynccontextmanager
    async def open(self) -> AsyncIterator[TrayClient]:
        credential = await _credential(self.workspace_id)
        provider = TrayCredentialProvider(credential)
        async with TrayClient(
            provider.get_region(self.workspace_id),
            provider.get_master_token(self.workspace_id),
            session_bearer=provider.get_session_bearer(self.workspace_id),
        ) as client:
            yield client


async def mutation_client_factory(
    request: Request,
    workspace_id: str | None = Query(default=None),
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> TrayClientFactory:
    """Resolve a lazy mutation client without touching Tray during dry-runs."""
    state_workspace_id = getattr(request.state, "workspace_id", None)
    resolved = workspace_id or x_workspace_id or state_workspace_id
    if resolved is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workspace context is required",
        )
    return TrayClientFactory(str(resolved))


def _mutation_result(
    would_send: dict[str, Any],
    *,
    confirm: bool,
    warning: str | None = None,
    result: dict[str, Any] | None = None,
) -> MutationResult:
    payload = dict(would_send)
    if result is not None:
        payload["result"] = result
    return MutationResult(
        dry_run=not confirm,
        would_send=payload,
        applied=confirm,
        warning=warning,
    )


def _find_instance(estate: dict[str, Any], instance_id: str) -> Any:
    for instance in estate.get("instances", []):
        if str(_value(instance, "id")) == instance_id:
            return instance
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Tray solution instance not found",
    )


def _instance_user_id(instance: Any) -> str:
    user_id = _value(instance, "user_id") or _value(instance, "userId")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The Tray instance does not include a user ID",
        )
    return str(user_id)


async def _mint_user_token(client: TrayClient, user_id: str) -> str:
    authorized = await client.authorize(user_id)
    token = authorized.get("accessToken")
    if not isinstance(token, str) or not token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Tray authorize did not return a user access token",
        )
    return token


@router.post(
    "/instances/{instance_id}/enable",
    response_model=MutationResult,
)
async def enable_instance(
    instance_id: str,
    confirm: bool = Query(default=False),
    _: Any = Depends(require_ops_role),
    estate: dict[str, Any] = Depends(estate_loader),
    factory: TrayClientFactory = Depends(mutation_client_factory),
) -> MutationResult:
    instance = _find_instance(estate, instance_id)
    user_id = _instance_user_id(instance)
    try:
        validate_config_against_slots(
            InstanceConfigUpdate(enable=True),
            {
                "config_slots": _value(instance, "config_slots", []) or [],
                "auth_slots": _value(instance, "auth_slots", []) or [],
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    would_send = {
        "operation": "updateSolutionInstance",
        "input": {"solutionInstanceId": instance_id, "enabled": True},
        "token_scope": "user",
    }
    if not confirm:
        return _mutation_result(would_send, confirm=False)
    async with factory.open() as client:
        user_token = await _mint_user_token(client, user_id)
        result = await client.update_solution_instance(
            instance_id,
            enabled=True,
            user_token=user_token,
        )
    return _mutation_result(would_send, confirm=True, result=result)


@router.post(
    "/instances/{instance_id}/disable",
    response_model=MutationResult,
)
async def disable_instance(
    instance_id: str,
    confirm: bool = Query(default=False),
    _: Any = Depends(require_ops_role),
    estate: dict[str, Any] = Depends(estate_loader),
    factory: TrayClientFactory = Depends(mutation_client_factory),
) -> MutationResult:
    instance = _find_instance(estate, instance_id)
    user_id = _instance_user_id(instance)
    would_send = {
        "operation": "updateSolutionInstance",
        "input": {"solutionInstanceId": instance_id, "enabled": False},
        "token_scope": "user",
    }
    if not confirm:
        return _mutation_result(would_send, confirm=False)
    async with factory.open() as client:
        user_token = await _mint_user_token(client, user_id)
        result = await client.update_solution_instance(
            instance_id,
            enabled=False,
            user_token=user_token,
        )
    return _mutation_result(would_send, confirm=True, result=result)


DELETE_WARNING = (
    "Deleting this instance halts its workflows mid-execution and cannot be undone."
)


@router.delete(
    "/instances/{instance_id}",
    response_model=MutationResult,
)
async def delete_instance(
    instance_id: str,
    confirm: bool = Query(default=False),
    _: Any = Depends(require_ops_role),
    estate: dict[str, Any] = Depends(estate_loader),
    factory: TrayClientFactory = Depends(mutation_client_factory),
) -> MutationResult:
    instance = _find_instance(estate, instance_id)
    user_id = _instance_user_id(instance)
    would_send = {
        "operation": "deleteSolutionInstance",
        "input": {"solutionInstanceId": instance_id},
        "token_scope": "user",
    }
    if not confirm:
        return _mutation_result(
            would_send,
            confirm=False,
            warning=DELETE_WARNING,
        )
    async with factory.open() as client:
        user_token = await _mint_user_token(client, user_id)
        result = await client.delete_solution_instance(
            instance_id,
            user_token=user_token,
        )
    return _mutation_result(
        would_send,
        confirm=True,
        warning=DELETE_WARNING,
        result=result,
    )


@router.post(
    "/instances/{instance_id}/config",
    response_model=MutationResult,
)
async def update_instance_config(
    instance_id: str,
    update: InstanceConfigUpdate,
    confirm: bool = Query(default=False),
    _: Any = Depends(require_ops_role),
    estate: dict[str, Any] = Depends(estate_loader),
    factory: TrayClientFactory = Depends(mutation_client_factory),
) -> MutationResult:
    instance = _find_instance(estate, instance_id)
    slots = {
        "config_slots": _value(instance, "config_slots", []) or [],
        "auth_slots": _value(instance, "auth_slots", []) or [],
    }
    try:
        validate_config_against_slots(update, slots)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    config_values = [item.model_dump() for item in update.config_values]
    auth_values = [item.model_dump() for item in update.auth_values]
    wire_input: dict[str, Any] = {
        "solutionInstanceId": instance_id,
        "configValues": config_values,
        "authValues": auth_values,
        "errorOnEnablingWithMissingValues": True,
    }
    would_send: dict[str, Any] = {
        "operation": "updateSolutionInstance",
        "input": wire_input,
        "token_scope": "user",
    }
    if update.enable is not None:
        would_send["follow_up"] = {
            "operation": "updateSolutionInstance",
            "input": {
                "solutionInstanceId": instance_id,
                "enabled": update.enable,
            },
        }
    if not confirm:
        return _mutation_result(would_send, confirm=False)

    user_id = _instance_user_id(instance)
    async with factory.open() as client:
        user_token = await _mint_user_token(client, user_id)
        result = await client.set_instance_config(
            instance_id,
            config_values,
            auth_values,
            user_token=user_token,
        )
        if update.enable is not None:
            result = await client.update_solution_instance(
                instance_id,
                enabled=update.enable,
                user_token=user_token,
            )
    return _mutation_result(would_send, confirm=True, result=result)


@router.post("/users", response_model=MutationResult)
async def provision_user(
    user: ProvisionUserIn,
    confirm: bool = Query(default=False),
    _: Any = Depends(require_ops_role),
    factory: TrayClientFactory = Depends(mutation_client_factory),
) -> MutationResult:
    would_send = {
        "operations": ["createExternalUser", "authorize"],
        "input": {
            "name": user.name,
            "externalUserId": user.externalUserId,
        },
        "token_scope": "master",
    }
    if not confirm:
        return _mutation_result(would_send, confirm=False)
    async with factory.open() as client:
        created = await client.create_external_user(
            user.name,
            user.externalUserId,
        )
        user_id = created.get("userId")
        if not isinstance(user_id, str) or not user_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Tray createExternalUser did not return a user ID",
            )
        await _mint_user_token(client, user_id)
    return _mutation_result(
        would_send,
        confirm=True,
        result={"userId": user_id, "source": "official"},
    )


@router.post("/users/{user_id}/reauthorize", response_model=MutationResult)
async def reauthorize_user(
    user_id: str,
    confirm: bool = Query(default=False),
    _: Any = Depends(require_ops_role),
    factory: TrayClientFactory = Depends(mutation_client_factory),
) -> MutationResult:
    would_send = {
        "operation": "authorize",
        "input": {"userId": user_id},
        "token_scope": "master",
    }
    if not confirm:
        return _mutation_result(would_send, confirm=False)
    async with factory.open() as client:
        await _mint_user_token(client, user_id)
    return _mutation_result(
        would_send,
        confirm=True,
        result={"reauthorized": True, "source": "official"},
    )


@router.post("/users/{user_id}/wizard-url", response_model=MutationResult)
async def generate_wizard_url(
    user_id: str,
    identifiers: WizardUrlIn,
    confirm: bool = Query(default=False),
    _: Any = Depends(require_ops_role),
    factory: TrayClientFactory = Depends(mutation_client_factory),
) -> MutationResult:
    would_send = {
        "operation": "generateAuthorizationCode",
        "input": {"userId": user_id},
        "wizard": {
            "solution_id": identifiers.solution_id,
            "instance_id": identifiers.instance_id,
        },
        "token_scope": "master",
    }
    if not confirm:
        return _mutation_result(would_send, confirm=False)
    async with factory.open() as client:
        generated = await client.generate_authorization_code(user_id)
    code = generated.get("authorizationCode")
    if not isinstance(code, str) or not code:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Tray did not return a Config Wizard authorization code",
        )
    wizard_url = (
        "https://embedded.tray.io/external/solutions/"
        f"{quote(identifiers.solution_id, safe='')}/configure/"
        f"{quote(identifiers.instance_id, safe='')}?code={quote(code, safe='')}"
    )
    return _mutation_result(
        would_send,
        confirm=True,
        result={"wizard_url": wizard_url, "source": "official"},
    )


@router.post("/solutions/{solution_id}/publish", response_model=MutationResult)
async def publish_solution(
    solution_id: str,
    confirm: bool = Query(default=False),
    _: Any = Depends(require_ops_role),
    factory: TrayClientFactory = Depends(mutation_client_factory),
) -> MutationResult:
    would_send = {
        "operation": "publishSolution",
        "solutionId": solution_id,
        "source": "unofficial",
    }
    if not confirm:
        return _mutation_result(would_send, confirm=False)
    try:
        require_unofficial_writes()
        async with factory.open() as client:
            result = await SolutionsClient(client).publish(solution_id)
    except UnofficialWritesDisabled as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return _mutation_result(would_send, confirm=True, result=result)
