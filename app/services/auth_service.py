import secrets
from hashlib import sha256
from datetime import datetime, timedelta, UTC

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_tokens import RefreshToken
from app.models.users import User
from app.models.org_members import OrgMember
from app.schemas.user import UserCreate
from app.schemas.auth import *
from app.core.database import get_db, transaction_scope
from app.core.security import hash_password, create_access_token, verify_password, decode_access_token
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.token_repository import TokenRepository

security = HTTPBearer()

from app.core.config import get_settings
settings = get_settings()

async def register_user(db: AsyncSession, user_in: UserCreate):
    async with db.begin():
        existing = await UserRepository.get_by_email(db, user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Registration failed. Please check your credentials."
            )

        hashed = hash_password(user_in.password)
        user = await UserRepository.create(
            db,
            email=user_in.email,
            hashed_password=hashed,
            first_name=user_in.first_name,
            last_name=user_in.last_name
        )

        raw_refresh = secrets.token_urlsafe(32)
        token_hash = sha256(raw_refresh.encode()).hexdigest()
        refresh = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        await RefreshTokenRepository.create(db, refresh)
    
    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "user_id": user.id,
        "email": user.email,
        "access_token": access_token,
        "refresh_token": raw_refresh
    }

async def login_user(db: AsyncSession, email: str, password: str):
    async with db.begin():
        user = await UserRepository.get_by_email(db, email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials!"
            )
        
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials!"
            )
        
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY)
        )

        raw_refresh = secrets.token_urlsafe(32)
        refresh_hash = sha256(raw_refresh.encode()).hexdigest()

        refresh = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRY)
        )

        await RefreshTokenRepository.create(db, refresh)

    return {
        "user_id": user.id,
        "email": user.email,
        "access_token": access_token,
        "refresh_token": raw_refresh
    }
    
async def refresh_token(db: AsyncSession, refresh_token_raw: str):
    token_hash = sha256(refresh_token_raw.encode()).hexdigest()

    async with db.begin():
        stored_token = await RefreshTokenRepository.get_by_hash(db, token_hash)

        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token!"
            )
        
        if stored_token.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked!"
            )
        
        if stored_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired!"
            )
        
        await RefreshTokenRepository.revoke(db, stored_token)

        user = stored_token.user

        new_access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRY)
        )

        new_raw_refresh = secrets.token_urlsafe(32)
        new_hash = sha256(new_raw_refresh.encode()).hexdigest()

        new_refresh = RefreshToken(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRY),
            revoked=False
        )

        await RefreshTokenRepository.create(db, new_refresh)

    return {
        "user_id": user.id,
        "email": user.email,
        "access_token": new_access_token,
        "refresh_token": new_raw_refresh
    }

async def logout_user(db: AsyncSession, refresh_token: str):
    token_hash = sha256(refresh_token.encode()).hexdigest()

    async with db.begin():
        stored_token = await RefreshTokenRepository.get_by_hash(db, token_hash)

        if not stored_token:
            return {
                "detail": "Logged out."
            }
        
        await RefreshTokenRepository.revoke(db, stored_token)

    return {
        "detail": "Logged out."
    }

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)):
    token = credentials.credentials
    payload = decode_access_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token!"
        )
    
    user = await UserRepository.get_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive."
        )
    
    return user

async def generate_api_token(
    db: AsyncSession,
    payload: APITokenCreate,
    current_user: User,
    org_member: OrgMember
) -> APITokenCreatedResponse:
    
    if org_member.role.lower() not in ["owner", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "Only Admin or Owner can create API tokens."
            }
        )

    raw_token = f"fd_{secrets.token_urlsafe(32)}"
    token_hash = sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(UTC) + timedelta(days=payload.expiry_days)

    async with transaction_scope(db):
        token_record = await TokenRepository.create_token(
            db=db,
            user_id=current_user.id,
            token_hash=token_hash,
            name=payload.name,
            expires_at=expires_at
        )

        response_data = APITokenCreatedResponse(
            id=token_record.id,
            name=token_record.name,
            raw_token=raw_token,
            expires_at=token_record.expires_at,
            created_at=token_record.created_at
        )
    return response_data

async def get_active_tokens(db: AsyncSession, user_id: uuid.UUID) -> list[APITokenResponse]:
    
    tokens = await TokenRepository.get_active_tokens_by_user_id(db, user_id)
    response = []
    for t in tokens:
        masked_hash = f"{t.token_hash[:6]}...{t.token_hash[-6:]}"
        response.append(
            APITokenResponse(
                id=t.id,
                name=t.name,
                token_hash_masked=masked_hash,
                expires_at=t.expires_at,
                created_at=t.created_at
            )
        )
    return response

async def revoke_api_token(db: AsyncSession, token_id: uuid.UUID, user_id: uuid.UUID) -> None:
    
    async with transaction_scope(db):
        token_record = await TokenRepository.get_token_by_id_and_user_id(db, token_id, user_id)
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "NOT_FOUND",
                    "message": "Token not found or not owned by you."
                }
            )
        await TokenRepository.delete_token(db, token_record)

