"""Workspace Pydantic schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class WorkspaceBase(BaseModel):
    """Base workspace schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = Field(None, min_length=1, max_length=255)


class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a workspace."""
    pass


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    settings: Optional[Dict[str, Any]] = None
    sso_enabled: Optional[bool] = None
    sso_enforced: Optional[bool] = None


class WorkspaceResponse(WorkspaceBase):
    """Schema for workspace response."""
    id: UUID
    owner_id: UUID
    plan: str
    sso_enabled: bool
    sso_enforced: bool
    settings: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    members: list['WorkspaceMemberResponse'] = []
    user_role: Optional[str] = None  # Current user's role in this workspace

    model_config = {"from_attributes": True}


class WorkspaceMemberBase(BaseModel):
    """Base workspace member schema."""
    role: str


class WorkspaceMemberCreate(BaseModel):
    """Schema for adding a member to workspace."""
    user_id: Optional[UUID] = None
    email: Optional[str] = None  # For inviting new users
    role: str = "member"


class WorkspaceMemberUpdate(BaseModel):
    """Schema for updating a workspace member."""
    role: Optional[str] = None
    permissions: Optional[Dict[str, Any]] = None


class WorkspaceMemberResponse(BaseModel):
    """Schema for workspace member response."""
    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: str
    permissions: Dict[str, Any]
    created_at: datetime
    user: Optional[Any] = None  # Will be populated with UserResponse

    model_config = {"from_attributes": True}


class WorkspaceInvite(BaseModel):
    """Schema for workspace invitation."""
    email: str
    role: str = "member"


class WorkspaceWithMembersResponse(WorkspaceResponse):
    """Schema for workspace with members."""
    members: list[WorkspaceMemberResponse] = []


# Resolve forward references (WorkspaceResponse.members refers to a class defined below it)
WorkspaceResponse.model_rebuild()
WorkspaceWithMembersResponse.model_rebuild()
