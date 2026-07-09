import uuid
from sqlalchemy.dialects.postgresql import UUID
from fastapi import APIRouter, HTTPException, status, Header, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.org_members import OrgMember
from app.schemas.comments import *
from app.services import comment_service
from app.api.deps import get_org_member, comments_rate_limter

router = APIRouter(tags=["comments"])

@router.post("/tasks/{id}/comments", response_model=CommentResponse, status_code= status.HTTP_201_CREATED, dependencies= [Depends(comments_rate_limter)])
async def create_comment_route(
    id: uuid.UUID,
    comment_in: CommentCreate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    return await comment_service.create_comment(
        db=db,
        org_id=org_member.org_id,
        author_id=org_member.user_id,
        task_id=id,
        payload=comment_in
    )

@router.get("/tasks/{id}/comments", response_model= CommentsListResponse)
async def list_comments_route(
    id: uuid.UUID,
    limit: int = 20,
    cursor: str | None = None,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    comments, next_cursor = await comment_service.list_comments(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        limit=limit,
        cursor=cursor
    )
    return {
        "comments": comments,
        "next_cursor": next_cursor
    }

@router.patch("/comments/{id}", response_model=CommentResponse)
async def update_comment_route(
    id: uuid.UUID,
    comment_in: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    return await comment_service.update_comment(
        db=db,
        org_id=org_member.org_id,
        comment_id=id,
        author_id=org_member.user_id,
        payload=comment_in
    )

@router.delete("/comments/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    await comment_service.delete_comment(
        db=db,
        org_id=org_member.org_id,
        comment_id=id,
        caller_member=org_member
    )