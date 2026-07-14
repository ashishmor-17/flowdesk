import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import transaction_scope
from app.core.security import verify_password, hash_password
from app.models.users import User
from app.repositories.user_repository import UserRepository
from app.services.notification_service import NotificationService
from app.schemas.user import UserUpdatePayload, PasswordUpdate

async def get_me_details(db: AsyncSession, user: User) -> User:
    await UserRepository.refresh_profile(db, user)
    unread_count = await NotificationService.get_unread_count(db, user.id)
    user.unread_notifications_count = unread_count
    
    org_member = await UserRepository.get_user_org_membership(db, user.id)
    user.org_id = org_member.org_id if org_member else None
    user.org_name = org_member.org.name if org_member and org_member.org else None
    return user

async def update_user_preferences(
    db: AsyncSession,
    user: User,
    payload: UserUpdatePayload
) -> User:
    async with transaction_scope(db):
        await UserRepository.refresh_profile(db, user)
        profile = user.profile
        new_prefs = payload.preferences.model_dump(exclude_unset=True)
        await UserRepository.update_profile_preferences(db, profile, new_prefs)
    return user

async def change_user_password(
    db: AsyncSession,
    user: User,
    payload: PasswordUpdate
) -> None:
    if not verify_password(payload.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Invalid old password."
            }
        )
    async with transaction_scope(db):
        new_hash = hash_password(payload.new_password)
        await UserRepository.update_password(db, user, new_hash)
