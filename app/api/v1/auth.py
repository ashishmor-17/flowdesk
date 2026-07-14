import secrets
from hashlib import sha256
from datetime import datetime, timedelta, UTC
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.api_tokens import APIToken
from app.models.org_members import OrgMember
from app.models.users import User
from app.api.deps import get_current_user, get_org_member
from app.schemas.user import UserCreate
from app.schemas.auth import *
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model= TokenResponse)
async def signup(user_in: UserCreate,db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(db,user_in)

@router.post("/login",response_model=TokenResponse)
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

@router.post("/tokens", response_model=APITokenCreatedResponse)
async def create_api_token(
    payload: APITokenCreate,
    current_user: User = Depends(get_current_user),
    org_member: OrgMember = Depends(get_org_member),
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.generate_api_token(db, payload, current_user, org_member)


@router.get("/tokens", response_model=List[APITokenResponse])
async def list_api_tokens(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await auth_service.get_active_tokens(db, current_user.id)


@router.delete("/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_token(
    token_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await auth_service.revoke_api_token(db, token_id, current_user.id)

