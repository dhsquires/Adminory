"""Async HTTP client for Tray's official and unofficial API surfaces."""

import asyncio
from typing import Any

import httpx

from app.services.tray.config import Region, TraySurface, graphql_host, rest_base
from app.services.tray.embedded import EmbeddedOperationsMixin
from app.services.tray.errors import (
    TrayAuthError,
    TrayError,
    TrayNotFound,
    TrayUnofficialError,
)
from app.services.tray.insights import InsightsOperationsMixin


class TrayClient(EmbeddedOperationsMixin, InsightsOperationsMixin):
    """One credential-aware client over the supported Tray surfaces."""

    _TIMEOUT_S = 10.0
    _RETRY_BACKOFF_S = 0.05

    def __init__(
        self,
        region: Region,
        master_token: str,
        session_bearer: str | None = None,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        graphql_host(region)
        self.region = region
        self.master_token = master_token
        self.session_bearer = session_bearer
        self._http = http or httpx.AsyncClient()
        self._owns_http = http is None

    def __repr__(self) -> str:
        return (
            f"TrayClient(region={self.region!r}, "
            "master_token=<redacted>, session_bearer=<redacted>)"
        )

    async def __aenter__(self) -> "TrayClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the internally created HTTP client."""
        if self._owns_http:
            await self._http.aclose()

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        for attempt in range(2):
            try:
                response = await self._http.request(
                    method,
                    url,
                    headers=headers,
                    json=json,
                    params=params,
                    timeout=self._TIMEOUT_S,
                )
            except httpx.RequestError:
                if attempt == 0:
                    await asyncio.sleep(self._RETRY_BACKOFF_S)
                    continue
                raise

            if response.status_code >= 500 and attempt == 0:
                await asyncio.sleep(self._RETRY_BACKOFF_S)
                continue
            return response

        raise RuntimeError("Tray request retry loop exited unexpectedly")

    async def _graphql(
        self,
        query: str,
        variables: dict[str, Any],
        *,
        token: str,
    ) -> dict[str, Any]:
        surface = TraySurface.EMBEDDED_GRAPHQL
        response = await self._request(
            "POST",
            graphql_host(self.region),
            headers={"Authorization": f"Bearer {token}"},
            json={"query": query, "variables": variables},
        )
        self._raise_official_status(response.status_code, surface)

        try:
            payload = response.json()
        except ValueError as exc:
            raise TrayError(
                "Tray returned invalid GraphQL JSON",
                surface,
                official=True,
                status=response.status_code,
            ) from exc

        if not isinstance(payload, dict):
            raise TrayError(
                "Tray returned an invalid GraphQL payload",
                surface,
                official=True,
                status=response.status_code,
            )
        if payload.get("errors"):
            raise TrayError(
                "Tray GraphQL response contained errors",
                surface,
                official=True,
                status=response.status_code,
            )

        data = payload.get("data")
        if not isinstance(data, dict):
            raise TrayError(
                "Tray GraphQL response did not contain data",
                surface,
                official=True,
                status=response.status_code,
            )
        return data

    async def _rest(
        self,
        method: str,
        path: str,
        *,
        surface: TraySurface,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if surface.is_official:
            raise ValueError("_rest requires an unofficial Tray surface")
        if self.session_bearer is None:
            raise TrayAuthError(
                "A session bearer is required for unofficial Tray APIs",
                surface,
                official=False,
                status=401,
            )

        response = await self._request(
            method,
            f"{rest_base(self.region)}{path}",
            headers={"Authorization": f"Bearer {self.session_bearer}"},
            json=json,
            params=params,
        )
        if response.status_code in (401, 403):
            raise TrayAuthError(
                "Tray rejected the session bearer",
                surface,
                official=False,
                status=response.status_code,
            )
        if not 200 <= response.status_code < 300:
            raise TrayUnofficialError(
                "Unofficial Tray request failed",
                surface,
                status=response.status_code,
            )
        if response.status_code == 204 or not response.content:
            return {}

        try:
            payload = response.json()
        except ValueError as exc:
            raise TrayUnofficialError(
                "Unofficial Tray response was not valid JSON",
                surface,
                status=response.status_code,
            ) from exc

        if isinstance(payload, dict):
            return payload
        return {"data": payload}

    @staticmethod
    def _raise_official_status(status: int, surface: TraySurface) -> None:
        if status in (401, 403):
            raise TrayAuthError(
                "Tray rejected the GraphQL credential",
                surface,
                official=True,
                status=status,
            )
        if status == 404:
            raise TrayNotFound(
                "Tray GraphQL resource was not found",
                surface,
                official=True,
                status=status,
            )
        if not 200 <= status < 300:
            raise TrayError(
                "Tray GraphQL request failed",
                surface,
                official=True,
                status=status,
            )
