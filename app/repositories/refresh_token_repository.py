from sqlalchemy.ext.asyncio import AsyncSession
from app.models.refresh_tokens import RefreshToken
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def create_refresh_token(db: AsyncSession, token: RefreshToken):
    db.add(token)
    await db.flush()
    return token

async def get_refresh_token(db: AsyncSession, token_hash: str):
    result = await db.execute(
        select(RefreshToken)
        .options(selectinload(RefreshToken.user))
        .where(RefreshToken.token_hash == token_hash)
    )
    return result.scalars().first()

async def revoke_token(db: AsyncSession, token: RefreshToken):
    token.revoked=True
    db.add(token)
    await db.flush()
    return token

