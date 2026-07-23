"""Unofficial Tray Solutions authoring REST operations."""

import os
from typing import Any, Protocol

from app.services.tray.config import TraySurface


class UnofficialWritesDisabled(RuntimeError):
    """Raised before any unofficial authoring write can reach Tray."""


def require_unofficial_writes() -> None:
    """Refuse live unofficial writes unless the explicit safety flag is on."""
    if os.getenv("TRAY_ALLOW_UNOFFICIAL_WRITES", "").lower() not in {
        "1",
        "true",
        "yes",
        "on",
    }:
        raise UnofficialWritesDisabled(
            "Unofficial Tray writes are disabled; "
            "set TRAY_ALLOW_UNOFFICIAL_WRITES=true to confirm the risk"
        )


class RestClient(Protocol):
    async def _rest(
        self,
        method: str,
        path: str,
        *,
        surface: TraySurface,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...


def _with_source(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, "source": "unofficial"}


class SolutionsClient:
    """Thin adapter over ``TrayClient._rest`` for authoring endpoints."""

    def __init__(self, client: RestClient) -> None:
        self.client = client

    async def list(self) -> dict[str, Any]:
        result = await self.client._rest(
            "GET",
            "/v2/solutions",
            surface=TraySurface.SOLUTIONS_AUTHORING,
        )
        return _with_source(result)

    async def get(self, solution_id: str) -> dict[str, Any]:
        result = await self.client._rest(
            "GET",
            f"/v2/solutions/{solution_id}",
            surface=TraySurface.SOLUTIONS_AUTHORING,
        )
        return _with_source(result)

    async def slots(self, solution_id: str) -> dict[str, Any]:
        result = await self.client._rest(
            "GET",
            f"/v1/solutions/{solution_id}/slots",
            surface=TraySurface.SOLUTIONS_AUTHORING,
        )
        return _with_source(result)

    async def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        require_unofficial_writes()
        result = await self.client._rest(
            "POST",
            "/v2/solutions",
            surface=TraySurface.SOLUTIONS_AUTHORING,
            json=payload,
        )
        return _with_source(result)

    async def update(
        self,
        solution_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        require_unofficial_writes()
        result = await self.client._rest(
            "PUT",
            f"/v2/solutions/{solution_id}",
            surface=TraySurface.SOLUTIONS_AUTHORING,
            json=payload,
        )
        return _with_source(result)

    async def preview_release(self, solution_id: str) -> dict[str, Any]:
        require_unofficial_writes()
        result = await self.client._rest(
            "POST",
            f"/v2/solutions/{solution_id}/releases/preview",
            surface=TraySurface.SOLUTIONS_AUTHORING,
        )
        return _with_source(result)

    async def publish(self, solution_id: str) -> dict[str, Any]:
        require_unofficial_writes()
        result = await self.client._rest(
            "POST",
            f"/v2/solutions/{solution_id}/releases",
            surface=TraySurface.SOLUTIONS_AUTHORING,
        )
        return _with_source(result)
