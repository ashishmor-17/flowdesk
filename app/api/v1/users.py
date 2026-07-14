from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.schemas.user import MeResponse, UserUpdatePayload, PasswordUpdate, UserResponse
from app.services import user_service

router = APIRouter(tags=["users"])

@router.get("/users/me", response_model=MeResponse)
@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.get_me_details(db, current_user)

@router.patch("/users/me", response_model=UserResponse)
async def update_profile(
    payload: UserUpdatePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await user_service.update_user_preferences(db, current_user, payload)

@router.post("/users/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await user_service.change_user_password(db, current_user, payload)
