import uuid
import re
import base64
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID

from app.models.comments import Comment, CommentMention
from app.models.users import User
from app.models.org_members import OrgMember
from app.models.tasks import Task
from app.schemas.comments import *
from app.services.task_service import get_task
from app.services.org_service import transaction_scope
from app.core.enums import UserRole

async def extract_mentions(content: str) -> list[str]:

    return re.findall(r'@([a-zA-Z0-9_.-]+)', content)

async def create_comment(
        db: AsyncSession,
        org_id: uuid.UUID,
        task_id: uuid.UUID,
        author_id: uuid.UUID,
        payload: CommentCreate
) -> Comment:
    
    async with transaction_scope(db):
        task = await get_task(db, org_id, task_id)
        comment = Comment(
            task_id=task_id,
            org_id=org_id,
            author_id=author_id,
            content=payload.content
        )
        db.add(comment)
        await db.flush()

        usernames = await extract_mentions(payload.content)
        if usernames:
            query = (
                select(User.id)
                .join(OrgMember, OrgMember.user_id == User.id)
                .where(
                    OrgMember.org_id == org_id,
                    func.split_part(User.email, "@", 1).in_(usernames)
                )
            )

            res = await db.execute(query)
            mentioned_ids = [row[0] for row in res.all()]

            for user_id in mentioned_ids:
                notified = (user_id == author_id)
                mention = CommentMention(
                    comment_id=comment.id,
                    mentioned_user_id=user_id,
                    notified=notified
                )
                db.add(mention)

        return comment
    
async def list_comments(
        db: AsyncSession,
        org_id: uuid.UUID,
        task_id: uuid.UUID,
        limit: int = 20,
        cursor: str | None = None
) -> tuple[list[Comment], str | None]:
    
    await get_task(db, org_id, task_id)

    query = (
        select(Comment)
        .where(
            Comment.task_id == task_id,
            Comment.org_id == org_id
        )
        .order_by(Comment.created_at.asc(), Comment.id.asc())
    )

    if cursor:
        try:
            decoded = base64.b64decode(cursor.encode()).decode()
            cursor_time_str, cursor_id_str = decoded.split("_")
            cursor_time = datetime.fromisoformat(cursor_time_str)
            cursor_id = uuid.UUID(cursor_id_str)

            query = query.where(
                or_(
                    Comment.created_at > cursor_time,
                    and_(
                        Comment.created_at == cursor_time,
                        Comment.id > cursor_id
                    )
                )
            )
        except Exception:
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail= {
                    "code": "INVALID_CURSOR",
                    "message": "Invalid pagination cursor."
                }
            )
    result = await db.execute(query.limit(limit+1))
    comments = list(result.scalars().all())

    next_cursor = None
    if len(comments) > limit:
        next_comments = comments[:limit]
        last_comment = next_comments[-1]
        cursor_str = f"{last_comment.created_at.isoformat()}_{last_comment.id}"
        next_cursor = base64.b64encode(cursor_str.encode()).decode()
        comments = next_comments
    return comments, next_cursor
        
async def get_comment(
        db: AsyncSession,
        org_id: uuid.UUID,
        comment_id: uuid.UUID
) -> Comment:
    
    query = select(Comment).where(
        Comment.id == comment_id,
        Comment.org_id == org_id
    )

    res = await db.execute(query)
    comment = res.scalar_one_or_none()
    if not comment:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= {
                "code": "COMMENT_NOT_FOUND",
                "message": "Comment not found or does not belong to this organization."
            }
        )
    
    return comment

async def update_comment(
        db: AsyncSession,
        org_id: uuid.UUID,
        comment_id: uuid.UUID,
        author_id: uuid.UUID,
        payload: CommentUpdate
) -> Comment:
    
    async with transaction_scope(db):
        comment = await get_comment(db, org_id, comment_id)
        
        if comment.author_id != author_id:
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail= {
                    "code": "FORBIDDEN",
                    "message": "Only the author can edit this comment."
                }
            )
        
        if comment.deleted_at:
            raise HTTPException(
                status_code= status.HTTP_400_BAD_REQUEST,
                detail= {
                    "code": "COMMENT_DELETED",
                    "message": "Cannot edit a deleted comment."
                }
            )
        
        if comment.content == payload.content:
            return comment
        
        comment.content = payload.content
        comment.edited_at = datetime.now(timezone.utc)

        usernames = await extract_mentions(payload.content)
        mentioned_ids = []
        if usernames:
            query = (
                select(User.id)
                .join(OrgMember, OrgMember.user_id == User.id)
                .where(
                    OrgMember.org_id == org_id,
                    func.split_part(User.email, "@", 1).in_(usernames)
                )
            )
            res = await db.execute(query)
            mentioned_ids = [row[0] for row in res.all()]

        existing_query = select(CommentMention).where(CommentMention.comment_id == comment_id)
        existing_res = await db.execute(existing_query)
        existing_mentions = list(existing_res.scalars().all())

        existing_user_ids = {m.mentioned_user_id for m in existing_mentions}
        new_user_ids = set(mentioned_ids)

        for m in existing_mentions:
            if m.mentioned_user_id not in new_user_ids:
                await db.delete(m)
        
        for uid in new_user_ids:
            if uid not in existing_user_ids:
                notified = (uid == author_id)
                new_mention = CommentMention(
                    comment_id=comment_id,
                    mentioned_user_id=uid,
                    notified=notified
                )
                db.add(new_mention)

        return comment
    
async def delete_comment(
        db: AsyncSession,
        org_id: uuid.UUID,
        comment_id: uuid.UUID,
        caller_member: OrgMember
) -> None:
    
    async with transaction_scope(db):
        comment = await get_comment(db, org_id, comment_id)

        is_author = (comment.author_id == caller_member.user_id)
        is_admin_or_owner = (caller_member.role in (UserRole.ADMIN, UserRole.OWNER))

        if not (is_author or is_admin_or_owner):
            raise HTTPException(
                status_code= status.HTTP_403_FORBIDDEN,
                detail= {
                    "code": "FORBIDDEN",
                    "message": "You do not have permissions to delete this comment."
                }
            )
        
        if not comment.deleted_at:
            comment.deleted_at = datetime.now(timezone.utc)

