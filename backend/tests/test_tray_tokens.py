"""Tests for Tray user-token caching."""

import asyncio
from unittest.mock import AsyncMock

from app.services.tray.config import Region
from app.services.tray.tokens import InMemoryCache, UserTokenStore


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeCredentialProvider:
    def get_master_token(self, workspace_id: str) -> str:
        return f"master-for-{workspace_id}"

    def get_session_bearer(self, workspace_id: str) -> str | None:
        return None

    def get_region(self, workspace_id: str) -> Region:
        return "us"


def test_user_token_store_caches_refreshes_and_expires_tokens() -> None:
    async def exercise() -> None:
        clock = FakeClock()
        cache = InMemoryCache(clock=clock)
        client = type("FakeTrayClient", (), {})()
        client.authorize = AsyncMock(
            side_effect=[
                {"accessToken": "token-1"},
                {"accessToken": "token-2"},
                {"accessToken": "token-3"},
            ]
        )
        store = UserTokenStore(
            client,
            cache,
            FakeCredentialProvider(),
            ttl_s=10,
        )

        first = await store.get_user_token("workspace-1", "tray-user-1")
        cached = await store.get_user_token("workspace-1", "tray-user-1")

        assert first == "token-1"
        assert cached == "token-1"
        assert client.authorize.await_count == 1

        refreshed = await store.get_user_token(
            "workspace-1",
            "tray-user-1",
            force_refresh=True,
        )
        assert refreshed == "token-2"
        assert client.authorize.await_count == 2

        clock.advance(10)
        expired = await store.get_user_token("workspace-1", "tray-user-1")
        assert expired == "token-3"
        assert client.authorize.await_count == 3

    asyncio.run(exercise())
