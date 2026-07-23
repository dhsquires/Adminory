"""Contract tests for the Tray HTTP client and API operations."""

import asyncio
import json

import httpx
import pytest
import respx

from app.services.tray import (
    TrayAuthError,
    TrayClient,
    TrayError,
    TraySurface,
    TrayUnofficialError,
)
from app.services.tray.config import graphql_host


def test_graphql_host_by_region() -> None:
    assert graphql_host("us") == "https://tray.io/graphql"
    assert graphql_host("eu") == "https://eu1.tray.io/graphql"
    assert graphql_host("ap") == "https://ap1.tray.io/graphql"


def test_graphql_returns_data_and_reports_graphql_errors() -> None:
    async def exercise() -> None:
        async with httpx.AsyncClient() as http:
            client = TrayClient("us", "master-secret", http=http)
            with respx.mock(assert_all_called=True) as mock:
                route = mock.post("https://tray.io/graphql")
                route.side_effect = [
                    httpx.Response(200, json={"data": {"viewer": {"id": "viewer-1"}}}),
                    httpx.Response(
                        200,
                        json={"errors": [{"message": "not allowed"}], "data": None},
                    ),
                ]

                data = await client._graphql(
                    "query Viewer { viewer { id } }",
                    {},
                    token="user",
                )
                assert data == {"viewer": {"id": "viewer-1"}}

                with pytest.raises(TrayError) as exc_info:
                    await client._graphql("query Viewer { viewer { id } }", {}, token="user")

                assert exc_info.value.official is True
                assert exc_info.value.surface is TraySurface.EMBEDDED_GRAPHQL

    asyncio.run(exercise())


def test_authorize_uses_master_token_and_returns_access_token() -> None:
    async def exercise() -> None:
        async with httpx.AsyncClient() as http:
            client = TrayClient("eu", "master-token-value", http=http)
            with respx.mock(assert_all_called=True) as mock:
                route = mock.post("https://eu1.tray.io/graphql").mock(
                    return_value=httpx.Response(
                        200,
                        json={"data": {"authorize": {"accessToken": "minted-user-token"}}},
                    )
                )

                result = await client.authorize("tray-user-1")

                assert result["accessToken"] == "minted-user-token"
                request = route.calls[0].request
                assert request.headers["Authorization"] == "Bearer master-token-value"
                body = json.loads(request.content)
                assert body["variables"] == {"input": {"userId": "tray-user-1"}}

    asyncio.run(exercise())


def test_insights_kpis_has_unofficial_provenance_and_500_is_safe() -> None:
    async def exercise() -> None:
        async with httpx.AsyncClient() as http:
            client = TrayClient(
                "ap",
                "master-secret",
                session_bearer="session-secret",
                http=http,
            )
            with respx.mock(assert_all_called=True) as mock:
                route = mock.post("https://api.tray.io/insights/v1/executions/kpis")
                route.side_effect = [
                    httpx.Response(200, json={"total": 42}),
                    httpx.Response(500, json={"error": "temporary"}),
                    httpx.Response(500, json={"error": "still failing"}),
                ]

                result = await client.kpis()
                assert result == {"total": 42, "source": "unofficial"}

                with pytest.raises(TrayUnofficialError) as exc_info:
                    await client.kpis()

                assert exc_info.value.official is False
                assert exc_info.value.surface is TraySurface.INSIGHTS
                assert route.call_count == 3

    asyncio.run(exercise())


def test_unauthorized_responses_raise_auth_error_on_both_surface_types() -> None:
    async def exercise() -> None:
        async with httpx.AsyncClient() as http:
            client = TrayClient(
                "us",
                "master-secret",
                session_bearer="session-secret",
                http=http,
            )
            with respx.mock(assert_all_called=True) as mock:
                graphql = mock.post("https://tray.io/graphql").mock(
                    return_value=httpx.Response(401)
                )
                insights = mock.post(
                    "https://api.tray.io/insights/v1/executions/kpis"
                ).mock(return_value=httpx.Response(401))

                with pytest.raises(TrayAuthError) as official_error:
                    await client.authorize("tray-user")
                assert official_error.value.official is True

                with pytest.raises(TrayAuthError) as unofficial_error:
                    await client.kpis()
                assert unofficial_error.value.official is False
                assert graphql.called
                assert insights.called

    asyncio.run(exercise())


def test_token_values_are_redacted_from_client_and_error_strings() -> None:
    master_token = "master-token-do-not-leak"
    session_token = "session-token-do-not-leak"
    client = TrayClient("us", master_token, session_bearer=session_token)
    rendered_client = repr(client)

    error = TrayError(
        f"remote echoed {master_token} and {session_token}",
        TraySurface.EMBEDDED_GRAPHQL,
        official=True,
        status=400,
    )
    rendered_error = str(error)

    assert master_token not in rendered_client
    assert session_token not in rendered_client
    assert master_token not in rendered_error
    assert session_token not in rendered_error

    asyncio.run(client.aclose())
