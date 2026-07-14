import uuid
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
from app.models.user_profiles import UserProfile
from app.models.org_members import OrgMember
from app.models.org_members import OrgMember

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
            full_name=f"{first_name} {last_name}".strip() if last_name else first_name
        )
        db.add(user)
        await db.flush()

        profile = UserProfile(
            user_id=user.id,
            first_name=first_name,
            last_name=last_name,
            preferences={}
        )
        db.add(profile)
        await db.flush()

        return user

    @staticmethod
    async def get_profile_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> UserProfile | None:
        return await db.scalar(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )

    @staticmethod
    async def get_user_org_membership(db: AsyncSession, user_id: uuid.UUID) -> OrgMember | None:
        return await db.scalar(
            select(OrgMember)
            .where(OrgMember.user_id == user_id)
            .options(selectinload(OrgMember.org))
        )

    @staticmethod
    async def update_profile_preferences(db: AsyncSession, profile: UserProfile, preferences: dict) -> UserProfile:
        profile.preferences = {**profile.preferences, **preferences}
        db.add(profile)
        await db.flush()
        return profile

    @staticmethod
    async def update_password(db: AsyncSession, user: User, new_hashed_password: str) -> User:
        user.hashed_password = new_hashed_password
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def refresh_profile(db: AsyncSession, user: User) -> None:
        await db.refresh(user, ["profile"])

