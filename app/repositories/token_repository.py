import uuid
from datetime import datetime, UTC
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.api_tokens import APIToken

class TokenRepository:
    @staticmethod
    async def create_token(
        db: AsyncSession,
        user_id: uuid.UUID,
        token_hash: str,
        name: str,
        expires_at: datetime
    ) -> APIToken:
        token = APIToken(
            user_id=user_id,
            token_hash=token_hash,
            name=name,
            expires_at=expires_at
        )
        db.add(token)
        await db.flush()
        return token

    @staticmethod
    async def get_by_hash(db: AsyncSession, token_hash: str) -> APIToken | None:
        return await db.scalar(
            select(APIToken).where(APIToken.token_hash == token_hash)
        )

    @staticmethod
    async def get_active_tokens_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> list[APIToken]:
        result = await db.scalars(
            select(APIToken)
            .where(
                APIToken.user_id == user_id,
                APIToken.expires_at > datetime.now(UTC)
            )
        )
        return list(result.all())

    @staticmethod
    async def get_token_by_id_and_user_id(
        db: AsyncSession,
        token_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> APIToken | None:
        return await db.scalar(
            select(APIToken).where(
                APIToken.id == token_id,
                APIToken.user_id == user_id
            )
        )

    @staticmethod
    async def delete_token(db: AsyncSession, token: APIToken) -> None:
        await db.delete(token)
