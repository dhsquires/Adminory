"""Credential provider contracts and user-token caching."""

import time
from collections.abc import Callable
from typing import Protocol

from app.services.tray.config import Region


USER_TOKEN_TTL_S = 36 * 60 * 60


class CredentialProvider(Protocol):
    """Provides per-workspace Tray credentials without prescribing storage."""

    def get_master_token(self, workspace_id: str) -> str:
        """Return a workspace's Tray master token."""
        ...

    def get_session_bearer(self, workspace_id: str) -> str | None:
        """Return a workspace's optional unofficial-surface bearer."""
        ...

    def get_region(self, workspace_id: str) -> Region:
        """Return a workspace's Tray region."""
        ...


class CacheBackend(Protocol):
    """Minimal cache operations required by the user-token store."""

    def get(self, key: str) -> str | None:
        """Return an unexpired value, if present."""
        ...

    def set(self, key: str, value: str, ttl_s: float) -> None:
        """Store a value for a number of seconds."""
        ...

    def delete(self, key: str) -> None:
        """Delete a value if present."""
        ...


class InMemoryCache:
    """Process-local cache for tests and development."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._values: dict[str, tuple[str, float]] = {}

    def get(self, key: str) -> str | None:
        item = self._values.get(key)
        if item is None:
            return None

        value, expires_at = item
        if expires_at <= self._clock():
            self.delete(key)
            return None
        return value

    def set(self, key: str, value: str, ttl_s: float) -> None:
        self._values[key] = (value, self._clock() + ttl_s)

    def delete(self, key: str) -> None:
        self._values.pop(key, None)


class UserTokenStore:
    """Mint and cache short-lived Tray end-user access tokens."""

    def __init__(
        self,
        client: object,
        cache: CacheBackend,
        provider: CredentialProvider,
        *,
        ttl_s: float = USER_TOKEN_TTL_S,
    ) -> None:
        self.client = client
        self.cache = cache
        self.provider = provider
        self.ttl_s = ttl_s

    async def get_user_token(
        self,
        workspace_id: str,
        tray_user_id: str,
        *,
        force_refresh: bool = False,
    ) -> str:
        """Return a cached user token or mint a fresh one."""
        key = f"tray:usertoken:{workspace_id}:{tray_user_id}"
        if not force_refresh:
            cached = self.cache.get(key)
            if cached is not None:
                return cached

        authorize = getattr(self.client, "authorize")
        result = await authorize(tray_user_id)
        token = result.get("accessToken")
        if not isinstance(token, str) or not token:
            raise ValueError("Tray authorize response did not include an access token")

        self.cache.set(key, token, self.ttl_s)
        return token
