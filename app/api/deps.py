import uuid
from datetime import datetime, UTC
from hashlib import sha256
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.redis import redis_client
from app.models.users import User
from app.models.org_members import OrgMember
from app.models.api_tokens import APIToken
from app.repositories.user_repository import UserRepository
from app.repositories.token_repository import TokenRepository

reusable_oauth2 = HTTPBearer()

from app.core.config import get_settings
settings = get_settings()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    api_key = request.headers.get("x-api-key") or request.headers.get("X-API-Key")
    if api_key:
        key_hash = sha256(api_key.encode()).hexdigest()
        
        token_record = await TokenRepository.get_by_hash(db, key_hash)
        
        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "UNAUTHORIZED",
                    "message": "Invalid API key."
                }
            )
            
        if token_record.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "UNAUTHORIZED",
                    "message": "API key has expired."
                }
            )
            
        user = await UserRepository.get_by_id(db, token_record.user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "UNAUTHORIZED",
                    "message": "User associated with API key is inactive or not found."
                }
            )

            
        return user

    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise credentials_exception
        
    token_str = auth_header.split(" ")[1]
    
    try:
        payload = jwt.decode(
            token_str,
            settings.JWT_SECRET.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
            
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception
        
    user = await UserRepository.get_by_id(db, user_id)
    if user is None:
        raise credentials_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    return user

    
async def get_current_org_id(x_org_id: str = Header(..., alias="X-Org-Id")) -> uuid.UUID:
    try:
        return uuid.UUID(x_org_id)
    except ValueError:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail= "Invalid X-Org-Id header format"
        )
    
async def get_org_member(
        org_id: uuid.UUID = Depends(get_current_org_id),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
) -> OrgMember:
    member = await db.scalar(
        select(OrgMember)
        .where(
            OrgMember.org_id == org_id,
            OrgMember.user_id == current_user.id
        )
    )
    if not member:
        raise HTTPException(
            status_code= status.HTTP_403_FORBIDDEN,
            detail= {
                "code": "FORBIDDEN",
                "message": "You are not a member of this organization."
            }
        )
    return member

async def invite_rate_limiter(current_user: User = Depends(get_current_user)):
    if not settings.RATE_LIMIT_ENABLED:
        return
    
    key = f"rate_limit:invite:{current_user.id}"
    attempts = await redis_client.incr(key)
    if attempts == 1:
        await redis_client.expire(key, 60)
    if attempts > 10:
        ttl = await redis_client.ttl(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Too many invitations sent. Please try again in {ttl} seconds."
            }
        )

async def comments_rate_limter(current_user: User = Depends(get_current_user)):
    if not settings.RATE_LIMIT_ENABLED:
        return
    
    key = f"rate_limit:comment:{current_user.id}"
    attempts = await redis_client.incr(key)
    if attempts == 1:
        await redis_client.expire(key,60)
    if attempts > 30:
        ttl = await redis_client.ttl(key)
        raise HTTPException(
            status_code= status.HTTP_429_TOO_MANY_REQUESTS,
            detail= {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Too many comments sent. Please try again in {ttl} seconds."
            }
        )
    