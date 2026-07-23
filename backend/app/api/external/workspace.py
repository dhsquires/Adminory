"""Workspace management API endpoints."""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db
from app.models.user import User
from app.services.workspace import WorkspaceService
from app.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    data: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new workspace.

    The authenticated user becomes the workspace owner.
    """
    service = WorkspaceService(db)
    workspace = await service.create_workspace(data, current_user.id)

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        owner_id=workspace.owner_id,
        plan=workspace.plan.value,
        sso_enabled=workspace.sso_enabled,
        sso_enforced=workspace.sso_enforced,
        settings=workspace.settings or {},
        metadata=workspace.workspace_metadata or {},
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        members=[],
    )


@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all workspaces the current user is a member of.
    """
    service = WorkspaceService(db)
    workspaces = await service.get_user_workspaces(current_user.id)

    # For each workspace, get the user's role
    result = []
    for workspace in workspaces:
        role = await service.get_user_workspace_role(workspace.id, current_user.id)
        result.append(
            WorkspaceResponse(
                id=workspace.id,
                name=workspace.name,
                slug=workspace.slug,
                owner_id=workspace.owner_id,
                plan=workspace.plan.value,
                sso_enabled=workspace.sso_enabled,
                sso_enforced=workspace.sso_enforced,
                settings=workspace.settings or {},
                metadata=workspace.workspace_metadata or {},
                created_at=workspace.created_at,
                updated_at=workspace.updated_at,
                members=[],
                user_role=role.value if role else None,
            )
        )

    return result


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get workspace details.

    User must be a member of the workspace.
    """
    service = WorkspaceService(db)

    # Check if user has access
    has_access = await service.check_workspace_permission(workspace_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace",
        )

    workspace = await service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    # Get user's role
    role = await service.get_user_workspace_role(workspace_id, current_user.id)

    # Get members
    members = await service.get_workspace_members(workspace_id)
    member_responses = [
        WorkspaceMemberResponse(
            id=member.id,
            workspace_id=member.workspace_id,
            user_id=member.user_id,
            role=member.role.value,
            permissions=member.permissions or {},
            created_at=member.created_at,
        )
        for member in members
    ]

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        owner_id=workspace.owner_id,
        plan=workspace.plan.value,
        sso_enabled=workspace.sso_enabled,
        sso_enforced=workspace.sso_enforced,
        settings=workspace.settings or {},
        metadata=workspace.workspace_metadata or {},
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        members=member_responses,
        user_role=role.value if role else None,
    )


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: UUID,
    data: WorkspaceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update workspace settings.

    Requires OWNER or ADMIN role.
    """
    service = WorkspaceService(db)
    workspace = await service.update_workspace(workspace_id, data, current_user.id)

    # Get user's role
    role = await service.get_user_workspace_role(workspace_id, current_user.id)

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        owner_id=workspace.owner_id,
        plan=workspace.plan.value,
        sso_enabled=workspace.sso_enabled,
        sso_enforced=workspace.sso_enforced,
        settings=workspace.settings or {},
        metadata=workspace.workspace_metadata or {},
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        members=[],
        user_role=role.value if role else None,
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a workspace.

    Only the workspace owner can delete the workspace.
    """
    service = WorkspaceService(db)
    await service.delete_workspace(workspace_id, current_user.id)
    return None


@router.get("/{workspace_id}/members", response_model=List[WorkspaceMemberResponse])
async def list_workspace_members(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all members of a workspace.

    User must be a member of the workspace.
    """
    service = WorkspaceService(db)

    # Check if user has access
    has_access = await service.check_workspace_permission(workspace_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace",
        )

    members = await service.get_workspace_members(workspace_id)

    return [
        WorkspaceMemberResponse(
            id=member.id,
            workspace_id=member.workspace_id,
            user_id=member.user_id,
            role=member.role.value,
            permissions=member.permissions or {},
            created_at=member.created_at,
        )
        for member in members
    ]


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_workspace_member(
    workspace_id: UUID,
    data: WorkspaceMemberCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a member to the workspace.

    Requires OWNER or ADMIN role.
    """
    service = WorkspaceService(db)
    member = await service.add_member(workspace_id, data, current_user.id)

    return WorkspaceMemberResponse(
        id=member.id,
        workspace_id=member.workspace_id,
        user_id=member.user_id,
        role=member.role.value,
        permissions=member.permissions or {},
        created_at=member.created_at,
    )


@router.delete(
    "/{workspace_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_workspace_member(
    workspace_id: UUID,
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a member from the workspace.

    Requires OWNER or ADMIN role.
    Cannot remove the workspace owner.
    """
    service = WorkspaceService(db)
    await service.remove_member(workspace_id, member_id, current_user.id)
    return None


@router.get("/by-slug/{slug}", response_model=WorkspaceResponse)
async def get_workspace_by_slug(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get workspace by slug.

    User must be a member of the workspace.
    """
    service = WorkspaceService(db)
    workspace = await service.get_workspace_by_slug(slug)

    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )

    # Check if user has access
    has_access = await service.check_workspace_permission(workspace.id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this workspace",
        )

    # Get user's role
    role = await service.get_user_workspace_role(workspace.id, current_user.id)

    # Get members
    members = await service.get_workspace_members(workspace.id)
    member_responses = [
        WorkspaceMemberResponse(
            id=member.id,
            workspace_id=member.workspace_id,
            user_id=member.user_id,
            role=member.role.value,
            permissions=member.permissions or {},
            created_at=member.created_at,
        )
        for member in members
    ]

    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        owner_id=workspace.owner_id,
        plan=workspace.plan.value,
        sso_enabled=workspace.sso_enabled,
        sso_enforced=workspace.sso_enforced,
        settings=workspace.settings or {},
        metadata=workspace.workspace_metadata or {},
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        members=member_responses,
        user_role=role.value if role else None,
    )
