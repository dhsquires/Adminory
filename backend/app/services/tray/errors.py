"""Safe exception types for Tray API failures."""

from app.services.tray.config import TraySurface


class TrayError(Exception):
    """Base Tray failure that does not render remote content or credentials."""

    def __init__(
        self,
        message: str,
        surface: TraySurface,
        official: bool,
        status: int | None = None,
    ) -> None:
        self.message = message
        self.surface = surface
        self.official = official
        self.status = status
        super().__init__(message)

    def __str__(self) -> str:
        status = f", status={self.status}" if self.status is not None else ""
        return f"{type(self).__name__}(surface={self.surface.value}{status})"


class TrayAuthError(TrayError):
    """Tray rejected or could not receive the required credential."""


class TrayNotFound(TrayError):
    """An official Tray resource was not found."""


class TrayUnofficialError(TrayError):
    """A request to an unofficial Tray API surface failed."""

    def __init__(
        self,
        message: str,
        surface: TraySurface,
        status: int | None = None,
    ) -> None:
        super().__init__(message, surface, official=False, status=status)
