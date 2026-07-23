"""Hermetic safety tests for Tray mutation endpoints."""

from contextlib import asynccontextmanager
import json
from types import SimpleNamespace
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.testclient import TestClient
import httpx
import pytest
import respx

from app.api.internal import tray as tray_router
from app.api.tray_deps import require_ops_role
from app.schemas.tray import (
    ConfigValueIn,
    InstanceConfigUpdate,
    validate_config_against_slots,
)
from app.services.tray.client import TrayClient


class TestClientFactory:
    @asynccontextmanager
    async def open(self) -> AsyncIterator[TrayClient]:
        async with httpx.AsyncClient() as http:
            yield TrayClient(
                "us",
                "master-token",
                session_bearer="session-bearer",
                http=http,
            )


def fixture_estate() -> dict[str, object]:
    return {
        "instances": [
            {
                "id": "instance-1",
                "user_id": "user-1",
                "solution_id": "solution-1",
                "config_slots": [
                    {
                        "externalId": "required-name",
                        "title": "Required name",
                        "required": True,
                        "value": "Existing",
                    },
                    {
                        "externalId": "region",
                        "title": "Region",
                        "required": False,
                    },
                ],
                "auth_slots": [
                    {
                        "externalId": "crm-auth",
                        "title": "CRM",
                        "required": True,
                    }
                ],
            }
        ]
    }


def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(tray_router.router, prefix="/api/internal/tray")

    async def fake_ops_user() -> SimpleNamespace:
        return SimpleNamespace(role="ops")

    async def fake_estate() -> dict[str, object]:
        return fixture_estate()

    async def fake_factory() -> TestClientFactory:
        return TestClientFactory()

    app.dependency_overrides[require_ops_role] = fake_ops_user
    app.dependency_overrides[tray_router.estate_loader] = fake_estate
    app.dependency_overrides[tray_router.mutation_client_factory] = fake_factory
    return app


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("post", "/instances/instance-1/enable", None),
        ("post", "/instances/instance-1/disable", None),
        ("delete", "/instances/instance-1", None),
        (
            "post",
            "/instances/instance-1/config",
            {
                "config_values": [
                    {"externalId": "required-name", "value": "Acme"}
                ],
                "auth_values": [
                    {"externalId": "crm-auth", "authId": "auth-1"}
                ],
            },
        ),
        (
            "post",
            "/users",
            {"name": "Ada", "externalUserId": "customer-ada"},
        ),
        ("post", "/users/user-1/reauthorize", None),
        (
            "post",
            "/users/user-1/wizard-url",
            {"solution_id": "solution-1", "instance_id": "instance-1"},
        ),
        ("post", "/solutions/solution-1/publish", None),
    ],
)
def test_every_mutation_defaults_to_dry_run_without_http_write(
    method: str,
    path: str,
    body: dict[str, object] | None,
) -> None:
    with respx.mock(assert_all_called=False) as mock:
        graphql = mock.post("https://tray.io/graphql").mock(
            return_value=httpx.Response(500)
        )
        unofficial = mock.post(
            "https://api.tray.io/v2/solutions/solution-1/releases"
        ).mock(return_value=httpx.Response(500))
        with TestClient(build_app()) as client:
            response = client.request(
                method,
                f"/api/internal/tray{path}?workspace_id=workspace-1",
                json=body,
            )

    assert response.status_code == 200
    assert response.json()["dry_run"] is True
    assert response.json()["applied"] is False
    assert graphql.call_count == 0
    assert unofficial.call_count == 0


def test_confirmed_enable_mints_user_token_and_updates_instance() -> None:
    with respx.mock(assert_all_called=True) as mock:
        graphql = mock.post("https://tray.io/graphql")
        graphql.side_effect = [
            httpx.Response(
                200,
                json={"data": {"authorize": {"accessToken": "user-token"}}},
            ),
            httpx.Response(
                200,
                json={
                    "data": {
                        "updateSolutionInstance": {
                            "solutionInstance": {
                                "id": "instance-1",
                                "enabled": True,
                            }
                        }
                    }
                },
            ),
        ]
        with TestClient(build_app()) as client:
            response = client.post(
                "/api/internal/tray/instances/instance-1/enable"
                "?workspace_id=workspace-1&confirm=true"
            )

    assert response.status_code == 200
    assert response.json()["dry_run"] is False
    assert response.json()["applied"] is True
    assert graphql.call_count == 2
    authorize_request, update_request = [call.request for call in graphql.calls]
    assert authorize_request.headers["Authorization"] == "Bearer master-token"
    assert update_request.headers["Authorization"] == "Bearer user-token"
    update_body = json.loads(update_request.content)
    assert update_body["variables"]["input"] == {
        "solutionInstanceId": "instance-1",
        "enabled": True,
    }


def test_confirmed_config_update_calls_live_graphql_with_slot_shapes() -> None:
    with respx.mock(assert_all_called=True) as mock:
        graphql = mock.post("https://tray.io/graphql")
        graphql.side_effect = [
            httpx.Response(
                200,
                json={"data": {"authorize": {"accessToken": "user-token"}}},
            ),
            httpx.Response(
                200,
                json={
                    "data": {
                        "updateSolutionInstance": {
                            "solutionInstance": {"id": "instance-1"}
                        }
                    }
                },
            ),
        ]
        with TestClient(build_app()) as client:
            response = client.post(
                "/api/internal/tray/instances/instance-1/config"
                "?workspace_id=workspace-1&confirm=true",
                json={
                    "config_values": [
                        {"externalId": "required-name", "value": "Acme"}
                    ],
                    "auth_values": [
                        {"externalId": "crm-auth", "authId": "auth-1"}
                    ],
                },
            )

    assert response.status_code == 200
    assert response.json()["applied"] is True
    update_request = graphql.calls[1].request
    body = json.loads(update_request.content)
    assert body["variables"]["input"] == {
        "solutionInstanceId": "instance-1",
        "configValues": [{"externalId": "required-name", "value": "Acme"}],
        "authValues": [{"externalId": "crm-auth", "authId": "auth-1"}],
        "errorOnEnablingWithMissingValues": True,
    }


def test_config_validator_rejects_unknown_external_id() -> None:
    update = InstanceConfigUpdate(
        config_values=[ConfigValueIn(externalId="unknown", value="value")]
    )

    with pytest.raises(ValueError, match="Unknown Solution slot"):
        validate_config_against_slots(
            update,
            [{"externalId": "known", "required": False}],
        )


def test_config_validator_rejects_missing_required_value_when_enabling() -> None:
    update = InstanceConfigUpdate(config_values=[], enable=True)

    with pytest.raises(ValueError, match="Required config slot"):
        validate_config_against_slots(
            update,
            [{"externalId": "required-name", "required": True}],
        )


def test_unofficial_publish_is_refused_when_flag_is_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TRAY_ALLOW_UNOFFICIAL_WRITES", raising=False)
    with respx.mock(assert_all_called=False) as mock:
        publish = mock.post(
            "https://api.tray.io/v2/solutions/solution-1/releases"
        ).mock(return_value=httpx.Response(200, json={"id": "release-1"}))
        with TestClient(build_app()) as client:
            response = client.post(
                "/api/internal/tray/solutions/solution-1/publish"
                "?workspace_id=workspace-1&confirm=true"
            )

    assert response.status_code == 409
    assert "disabled" in response.json()["detail"].lower()
    assert publish.call_count == 0
