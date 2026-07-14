import uuid
import re
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.comments import Comment, CommentMention
from app.models.users import User
from app.models.org_members import OrgMember
from app.models.org_members import OrgMember
from app.schemas.comments import *
from app.services.task_service import get_task
from app.core.database import transaction_scope
from app.core.enums import UserRole, NotificationType, NotificationEntityType
from app.services.notification_service import NotificationService
from app.repositories.comment_repository import CommentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.task_watcher_repository import TaskWatcherRepository

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
        comment = await CommentRepository.create(
            db,
            task_id=task_id,
            org_id=org_id,
            author_id=author_id,
            content=payload.content
        )

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

            for user_id in mentioned_ids:
                notified = (user_id == author_id)
                await CommentRepository.create_mention(
                    db,
                    comment_id=comment.id,
                    user_id=user_id,
                    notified=notified
                )
        
        author_user = await UserRepository.get_by_id(db, author_id)
        author_name = author_user.full_name or author_user.email
        preview = payload.content[:100] + ("..." if len(payload.content)>100 else "")

        for user_id in mentioned_ids:
            if user_id != author_id:
                NotificationService.create_notification(
                    org_id=org_id,
                    recipient_id=user_id,
                    type=NotificationType.MENTION,
                    actor_id=author_id,
                    entity_type=NotificationEntityType.COMMENT,
                    entity_id=comment.id,
                    payload={
                        "comment_id": str(comment.id),
                        "task_id": str(task.id),
                        "task_title": task.title,
                        "mentioned_by_name": author_name,
                        "preview": preview
                    }
                )
        
        watchers = await TaskWatcherRepository.list_by_task(db, task.id)
        watcher_ids = {w.user_id for w in watchers}
        recipients_candidates = {task.created_by} | {a.user_id for a in task.assignees if a.user_id is not None} | watcher_ids

        for recipient_id in recipients_candidates:
            if recipient_id != author_id and recipient_id not in mentioned_ids:
                NotificationService.create_notification(
                    org_id=org_id,
                    recipient_id=recipient_id,
                    type=NotificationType.TASK_COMMENT_ADDED,
                    actor_id=author_id,
                    entity_type=NotificationEntityType.COMMENT,
                    entity_id=comment.id,
                    payload={
                        "comment_id": str(comment.id),
                        "task_id": str(task.id),
                        "task_title": task.title,
                        "author_name": author_name,
                        "preview": preview
                    }
                )

        return comment
    
async def list_comments(
        db: AsyncSession,
        org_id: uuid.UUID,
        task_id: uuid.UUID,
        limit: int = 20,
        cursor: str | None = None
) -> tuple[list[Comment], str | None]:
    await get_task(db, org_id, task_id)
    try:
        return await CommentRepository.list_comments(db, task_id, limit, cursor)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_CURSOR",
                "message": str(e)
            }
        )
        
async def get_comment(
        db: AsyncSession,
        org_id: uuid.UUID,
        comment_id: uuid.UUID
) -> Comment:
    comment = await CommentRepository.get_by_id(db, comment_id)
    if not comment or comment.org_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
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
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "Only the author can edit this comment."
                }
            )
        
        if comment.deleted_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
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
        
        newly_mentioned_ids = []
        for uid in new_user_ids:
            if uid not in existing_user_ids:
                notified = (uid == author_id)
                if uid != author_id:
                    notified = True
                    newly_mentioned_ids.append(uid)
                
                await CommentRepository.create_mention(
                    db,
                    comment_id=comment_id,
                    user_id=uid,
                    notified=notified
                )
        
        if newly_mentioned_ids:
            task = await get_task(db, org_id, comment.task_id)
            author_user = await UserRepository.get_by_id(db, author_id)
            author_name = author_user.full_name or author_user.email
            preview = payload.content[:100] + ("..." if len(payload.content) > 100 else "")
            for user_id in newly_mentioned_ids:
                NotificationService.create_notification(
                    org_id=org_id,
                    recipient_id=user_id,
                    type=NotificationType.MENTION,
                    actor_id=author_id,
                    entity_type=NotificationEntityType.COMMENT,
                    entity_id=comment.id,
                    payload={
                        "comment_id": str(comment.id),
                        "task_id": str(task.id),
                        "task_title": task.title,
                        "mentioned_by_name": author_name,
                        "preview": preview
                    }
                )

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
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "You do not have permissions to delete this comment."
                }
            )
        
        if not comment.deleted_at:
            comment.deleted_at = datetime.now(timezone.utc)
