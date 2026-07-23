"""Dependencies shared by the internal Tray operations routes."""

from fastapi import Depends, HTTPException, status

from app.api.deps import get_current_user
from app.models.user import User


async def require_ops_role(
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow only internal operators and administrators."""
    role = current_user.role
    role_value = role.value if hasattr(role, "value") else str(role)
    if role_value not in {"ops", "admin", "super_admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tray operations access requires an admin or ops role",
        )
    return current_user
