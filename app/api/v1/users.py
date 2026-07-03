from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.schemas.user import MeResponse
from app.services.notification_service import NotificationService

router = APIRouter(tags=["users"])

@router.get("/me", response_model=MeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    unread_count = await NotificationService.get_unread_count(db, current_user.id)
    
    current_user.unread_notifications_count = unread_count
    return current_user
