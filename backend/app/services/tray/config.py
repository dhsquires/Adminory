"""Tray API surface and region configuration."""

from enum import Enum
from typing import Literal


Region = Literal["us", "eu", "ap"]

_GRAPHQL_HOSTS: dict[Region, str] = {
    "us": "https://tray.io/graphql",
    "eu": "https://eu1.tray.io/graphql",
    "ap": "https://ap1.tray.io/graphql",
}


def graphql_host(region: Region) -> str:
    """Return the Embedded GraphQL endpoint for a Tray region."""
    try:
        return _GRAPHQL_HOSTS[region]
    except KeyError as exc:
        raise ValueError(f"Unsupported Tray region: {region!r}") from exc


def rest_base(region: Region) -> str:
    """Return the shared base URL for Tray's unofficial REST surfaces."""
    graphql_host(region)
    return "https://api.tray.io"


class TraySurface(str, Enum):
    """Known Tray API surfaces."""

    EMBEDDED_GRAPHQL = "embedded_graphql"
    INSIGHTS = "insights"
    APIM = "apim"
    SOLUTIONS_AUTHORING = "solutions_authoring"

    @property
    def is_official(self) -> bool:
        """Whether Tray officially documents and supports this surface."""
        return self is TraySurface.EMBEDDED_GRAPHQL
