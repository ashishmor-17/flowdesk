from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserCreate
from app.schemas.auth import TokenResponse, LoginRequest, RefreshRequest, LogoutRequest
from app.services import auth_service
from app.api.deps import login_rate_limiter

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model= TokenResponse)
async def signup(user_in: UserCreate,db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db,user_in)

@router.post("/login",response_model=TokenResponse, dependencies= [Depends(login_rate_limiter)])
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login_user(
        db,
        payload.email,
        payload.password
    )

@router.post("/refresh",response_model= TokenResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh_token(
        db,
        payload.refresh_token
    )

@router.post("/logout")
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.logout_user(
        db,
        payload.refresh_token
    )
