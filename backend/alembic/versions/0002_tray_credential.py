"""Create Tray credential table.

Revision ID: 0002_tray_credential
Revises: 002
Create Date: 2026-07-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_tray_credential"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create workspace-scoped encrypted Tray credentials."""
    op.create_table(
        "tray_credential",
        sa.Column(
            "workspace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("region", sa.String(8), nullable=False, server_default="us"),
        sa.Column("master_token_encrypted", sa.Text(), nullable=False),
        sa.Column("session_bearer_encrypted", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Drop workspace-scoped encrypted Tray credentials."""
    op.drop_table("tray_credential")
