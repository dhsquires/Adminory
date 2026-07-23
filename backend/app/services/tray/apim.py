"""Unofficial Tray APIM / Connectivity REST operations."""

from typing import Any

from app.services.tray.config import TraySurface
from app.services.tray.solutions import (
    RestClient,
    _with_source,
    require_unofficial_writes,
)


class ApimClient:
    """Thin adapter over ``TrayClient._rest`` for APIM endpoints."""

    def __init__(self, client: RestClient) -> None:
        self.client = client

    async def list_operations(self) -> dict[str, Any]:
        result = await self.client._rest(
            "GET",
            "/private/v1/operations",
            surface=TraySurface.APIM,
        )
        return _with_source(result)

    async def list_roles(self) -> dict[str, Any]:
        result = await self.client._rest(
            "GET",
            "/private/v1/roles",
            surface=TraySurface.APIM,
        )
        return _with_source(result)

    async def list_clients(self) -> dict[str, Any]:
        result = await self.client._rest(
            "GET",
            "/private/v1/clients",
            surface=TraySurface.APIM,
        )
        return _with_source(result)

    async def create_operation(self, payload: dict[str, Any]) -> dict[str, Any]:
        require_unofficial_writes()
        result = await self.client._rest(
            "POST",
            "/private/v1/operations",
            surface=TraySurface.APIM,
            json=payload,
        )
        return _with_source(result)

    async def create_role(self, payload: dict[str, Any]) -> dict[str, Any]:
        require_unofficial_writes()
        result = await self.client._rest(
            "POST",
            "/private/v1/roles",
            surface=TraySurface.APIM,
            json=payload,
        )
        return _with_source(result)

    async def create_client(self, payload: dict[str, Any]) -> dict[str, Any]:
        require_unofficial_writes()
        result = await self.client._rest(
            "POST",
            "/private/v1/clients",
            surface=TraySurface.APIM,
            json=payload,
        )
        return _with_source(result)
