"""Database model and credential adapter for Tray integrations."""

from datetime import datetime
from typing import cast
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.services.tray.config import Region
from app.services.tray.tokens import CredentialProvider
from app.utils.encryption import decrypt_string, encrypt_string


class TrayCredential(Base):
    """Encrypted, workspace-scoped credentials for Tray."""

    __tablename__ = "tray_credential"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        primary_key=True,
    )
    region: Mapped[str] = mapped_column(String(8), nullable=False, default="us")
    master_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    session_bearer_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def set_master_token(self, token: str) -> None:
        """Encrypt and store the required Tray master token."""
        self.master_token_encrypted = encrypt_string(token)

    def get_master_token(self) -> str:
        """Decrypt the stored Tray master token."""
        return decrypt_string(self.master_token_encrypted)

    def set_session_bearer(self, bearer: str | None) -> None:
        """Encrypt and store the optional unofficial-surface bearer."""
        self.session_bearer_encrypted = (
            encrypt_string(bearer) if bearer is not None else None
        )

    def get_session_bearer(self) -> str | None:
        """Decrypt the optional unofficial-surface bearer."""
        if self.session_bearer_encrypted is None:
            return None
        return decrypt_string(self.session_bearer_encrypted)

    @property
    def master_token(self) -> str:
        """Plaintext master token facade; never persisted directly."""
        return self.get_master_token()

    @master_token.setter
    def master_token(self, token: str) -> None:
        self.set_master_token(token)

    @property
    def session_bearer(self) -> str | None:
        """Plaintext bearer facade; never persisted directly."""
        return self.get_session_bearer()

    @session_bearer.setter
    def session_bearer(self, bearer: str | None) -> None:
        self.set_session_bearer(bearer)


class TrayCredentialProvider(CredentialProvider):
    """Track-1 credential provider backed by one workspace credential row."""

    def __init__(self, credential: TrayCredential) -> None:
        self.credential = credential

    def _require_workspace(self, workspace_id: str) -> None:
        if str(self.credential.workspace_id) != str(workspace_id):
            raise KeyError(f"No Tray credential for workspace {workspace_id}")

    def get_master_token(self, workspace_id: str) -> str:
        self._require_workspace(workspace_id)
        return self.credential.get_master_token()

    def get_session_bearer(self, workspace_id: str) -> str | None:
        self._require_workspace(workspace_id)
        return self.credential.get_session_bearer()

    def get_region(self, workspace_id: str) -> Region:
        self._require_workspace(workspace_id)
        return cast(Region, self.credential.region)
