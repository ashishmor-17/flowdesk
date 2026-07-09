import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import User

class UserRepository:
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        
        return await db.scalar(
            select(User).where(User.email == email)
        )

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
        
        return await db.get(User, user_id)

    @staticmethod
    async def create(
        db: AsyncSession,
        *,
        email: str,
        hashed_password: str,
        first_name: str,
        last_name: str | None = None
    ) -> User:
        
        user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name
        )
        db.add(user)
        await db.flush()
        return user
