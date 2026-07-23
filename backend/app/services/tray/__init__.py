"""Tray client, configuration, and safe error exports."""

from app.services.tray.client import TrayClient
from app.services.tray.config import Region, TraySurface
from app.services.tray.errors import (
    TrayAuthError,
    TrayError,
    TrayNotFound,
    TrayUnofficialError,
)

__all__ = [
    "Region",
    "TrayAuthError",
    "TrayClient",
    "TrayError",
    "TrayNotFound",
    "TraySurface",
    "TrayUnofficialError",
]
