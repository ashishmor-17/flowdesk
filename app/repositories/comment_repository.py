import uuid
import base64
from datetime import datetime
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.comments import Comment, CommentMention
from app.models.users import User
from app.models.org_members import OrgMember

class CommentRepository:
    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        task_id: uuid.UUID,
        org_id: uuid.UUID,
        author_id: uuid.UUID,
        content: str
    ) -> Comment:
        comment = Comment(
            task_id=task_id,
            org_id=org_id,
            author_id=author_id,
            content=content
        )
        db.add(comment)
        await db.flush()
        return comment

    @staticmethod
    async def create_mention(
        db: AsyncSession,
        *,
        comment_id: uuid.UUID,
        user_id: uuid.UUID,
        notified: bool = False
    ) -> CommentMention:
        mention = CommentMention(
            comment_id=comment_id,
            mentioned_user_id=user_id,
            notified=notified
        )
        db.add(mention)
        await db.flush()
        return mention

    @staticmethod
    async def get_by_id(db: AsyncSession, comment_id: uuid.UUID) -> Comment | None:
        return await db.get(Comment, comment_id)

    @staticmethod
    async def list_comments(
        db: AsyncSession,
        task_id: uuid.UUID,
        limit: int = 20,
        cursor: str | None = None
    ) -> tuple[list[Comment], str | None]:
        query = (
            select(Comment)
            .where(Comment.task_id == task_id)
            .options(
                selectinload(Comment.author),
                selectinload(Comment.mentions)
            )
            .order_by(Comment.created_at.desc(), Comment.id.desc())
        )

        if cursor:
            try:
                decoded = base64.b64decode(cursor.encode()).decode()
                cursor_time_str, cursor_id_str = decoded.split("_")
                cursor_time = datetime.fromisoformat(cursor_time_str)
                cursor_id = uuid.UUID(cursor_id_str)

                query = query.where(
                    or_(
                        Comment.created_at < cursor_time,
                        and_(
                            Comment.created_at == cursor_time,
                            Comment.id < cursor_id
                        )
                    )
                )
            except Exception:
                raise ValueError("Invalid pagination cursor")

        result = await db.execute(query.limit(limit + 1))
        comments = list(result.scalars().all())

        next_cursor = None
        if len(comments) > limit:
            comments = comments[:limit]
            last_comment = comments[-1]
            cursor_str = f"{last_comment.created_at.isoformat()}_{last_comment.id}"
            next_cursor = base64.b64encode(cursor_str.encode()).decode()

        return comments, next_cursor

    @staticmethod
    async def delete(db: AsyncSession, comment: Comment) -> None:
        await db.delete(comment)

    @staticmethod
    async def get_mentioned_user_ids_by_usernames(
        db: AsyncSession,
        org_id: uuid.UUID,
        usernames: list[str]
    ) -> list[uuid.UUID]:
        query = (
            select(User.id)
            .join(OrgMember, OrgMember.user_id == User.id)
            .where(
                OrgMember.org_id == org_id,
                or_(
                    func.split_part(User.email, "@", 1).in_(usernames),
                    User.email.in_(usernames)
                )
            )
        )
        res = await db.execute(query)
        return [row[0] for row in res.all()]

    @staticmethod
    async def get_mentions_for_comment(
        db: AsyncSession,
        comment_id: uuid.UUID
    ) -> list[CommentMention]:
        query = select(CommentMention).where(CommentMention.comment_id == comment_id)
        res = await db.execute(query)
        return list(res.scalars().all())

    @staticmethod
    async def delete_mention(db: AsyncSession, mention: CommentMention) -> None:
        await db.delete(mention)
