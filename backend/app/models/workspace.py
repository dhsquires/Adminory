"""Workspace and WorkspaceMember models."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Boolean, String, DateTime, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
import enum

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class WorkspacePlan(str, enum.Enum):
    """Workspace plan enumeration."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class WorkspaceRole(str, enum.Enum):
    """Workspace member role enumeration."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Workspace(Base):
    """Workspace model for multi-tenancy."""

    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    plan: Mapped[WorkspacePlan] = mapped_column(
        SQLEnum(WorkspacePlan),
        default=WorkspacePlan.FREE,
        nullable=False
    )

    # SSO configuration
    sso_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sso_enforced: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False  # Require SSO for all logins
    )

    # JSON fields for flexible data
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    workspace_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    # owner = relationship("User", back_populates="owned_workspaces")
    # members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Workspace {self.name} ({self.slug})>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "owner_id": str(self.owner_id),
            "plan": self.plan.value,
            "sso_enabled": self.sso_enabled,
            "sso_enforced": self.sso_enforced,
            "settings": self.settings or {},
            "metadata": self.workspace_metadata or {},
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class WorkspaceMember(Base):
    """Workspace member model for managing team members."""

    __tablename__ = "workspace_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[WorkspaceRole] = mapped_column(
        SQLEnum(WorkspaceRole),
        default=WorkspaceRole.MEMBER,
        nullable=False
    )

    # Custom permissions (JSON)
    permissions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationships
    # workspace = relationship("Workspace", back_populates="members")
    # user = relationship("User", back_populates="workspace_memberships")

    def __repr__(self) -> str:
        """String representation."""
        return f"<WorkspaceMember workspace={self.workspace_id} user={self.user_id} role={self.role}>"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "user_id": str(self.user_id),
            "role": self.role.value,
            "permissions": self.permissions or {},
            "created_at": self.created_at.isoformat(),
        }
