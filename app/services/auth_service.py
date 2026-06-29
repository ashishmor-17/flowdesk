import secrets
from hashlib import sha256
from datetime import datetime, timedelta, UTC

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User
from app.models.refresh_tokens import RefreshToken
from app.schemas.user import UserCreate
from app.core.database import get_db
from app.core.security import hash_password, create_access_token, verify_password, decode_access_token
from app.repositories.user_repository import get_user_by_email, create_user, get_user_by_id
from app.repositories.refresh_token_repository import create_refresh_token, revoke_token, get_refresh_token

security= HTTPBearer()

from app.core.config import get_settings
settings = get_settings()

async def register_user(db, user_in: UserCreate):
    async with db.begin():
        existing = await get_user_by_email(db, user_in.email)
        if existing:
            raise HTTPException(
                status_code= status.HTTP_409_CONFLICT,
                detail= "Registration failed. Please check your credentials."
            )

        hashed = hash_password(user_in.password)

        user = User(
            email=user_in.email,
            hashed_password=hashed,
            first_name=user_in.first_name,
            last_name=user_in.last_name
        )

        await create_user(db, user)
        raw_refresh = secrets.token_urlsafe(32)
        token_hash = sha256(raw_refresh.encode()).hexdigest()
        refresh = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        await create_refresh_token(db, refresh)
    
    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "user_id": user.id,
        "email": user.email,
        "access_token": access_token,
        "refresh_token": raw_refresh
    }

async def login_user(db, email: str, password:str):
    async with db.begin():
        user = await get_user_by_email(db, email)

        if not user:
            raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail= "Invalid credentials!"
            )
        
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail= "Invalid credentials!"
            )
        
        access_token = create_access_token(
            data= {"sub": str(user.id)},
            expires_delta= timedelta(minutes= settings.ACCESS_TOKEN_EXPIRY)
        )

        raw_refresh = secrets.token_urlsafe(32)
        refresh_hash = sha256(raw_refresh.encode()).hexdigest()

        refresh = RefreshToken(
            user_id = user.id,
            token_hash = refresh_hash,
            expires_at = datetime.utcnow() + timedelta(days= settings.REFRESH_TOKEN_EXPIRY)
        )

        await create_refresh_token(db, refresh)

    return {
        "user_id": user.id,
        "email": user.email,
        "access_token": access_token,
        "refresh_token": raw_refresh
    }
    
async def refresh_token(db, refresh_token_raw: str):
    token_hash = sha256(refresh_token_raw.encode()).hexdigest()

    async with db.begin():
        stored_token = await get_refresh_token(db, token_hash)

        if not stored_token:
            raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail= "Invalid refresh token!"
            )
        
        if stored_token.revoked:
            raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail= "Refresh token revoked!"
            )
        
        if stored_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail= "Refresh token expired!"
            )
        
        await revoke_token(db, stored_token)

        user = stored_token.user

        new_access_token = create_access_token(
            data= {"sub": str(user.id)},
            expires_delta= timedelta(minutes= settings.ACCESS_TOKEN_EXPIRY)
        )

        new_raw_refresh = secrets.token_urlsafe(32)
        new_hash = sha256(new_raw_refresh.encode()).hexdigest()

        new_refresh = RefreshToken(
            user_id= user.id,
            token_hash= new_hash,
            expires_at= datetime.utcnow() + timedelta(days= settings.REFRESH_TOKEN_EXPIRY),
            revoked= False
        )

        await create_refresh_token(db, new_refresh)

    return {
        "user_id": user.id,
        "email": user.email,
        "access_token": new_access_token,
        "refresh_token": new_raw_refresh
    }

async def logout_user(db, refresh_token: str):
    token_hash = sha256(refresh_token.encode()).hexdigest()

    async with db.begin():
        stored_token = await get_refresh_token(db, token_hash)

        if not stored_token:
            return {
                "detail": "Logged out."
            }
        
        await revoke_token(db, stored_token)

    return {
        "detail": "Logged out."
    }

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)):
    token = credentials.credentials

    payload = decode_access_token(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "Invalid token!"
        )
    
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "User not found."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail= "User inactive."
        )
    
    return user