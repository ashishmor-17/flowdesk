from sqlalchemy.ext.asyncio import AsyncSession
from app.models.refresh_tokens import RefreshToken
from sqlalchemy import select
from sqlalchemy.orm import selectinload

class RefreshTokenRepository:
    @staticmethod
    async def create(db: AsyncSession, token: RefreshToken) -> RefreshToken:
        db.add(token)
        await db.flush()
        return token

    @staticmethod
    async def get_by_hash(db: AsyncSession, token_hash: str) -> RefreshToken | None:
        result = await db.execute(
            select(RefreshToken)
            .options(selectinload(RefreshToken.user))
            .where(RefreshToken.token_hash == token_hash)
        )
        return result.scalars().first()

    @staticmethod
    async def revoke(db: AsyncSession, token: RefreshToken) -> RefreshToken:
        token.revoked = True
        db.add(token)
        await db.flush()
        return token
