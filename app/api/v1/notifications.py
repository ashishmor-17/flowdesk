import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.schemas.notification import NotificationListResponse, NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    cursor: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    notifications, next_cursor = await NotificationService.list_notifications(
        db, current_user.id, limit=limit, cursor=cursor
    )
    return {"notifications": notifications, "next_cursor": next_cursor}

@router.patch("/{id}/read", response_model=NotificationResponse)
async def mark_as_read(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    return await NotificationService.mark_as_read(db, current_user.id, id)

@router.patch("/read-all", status_code=status.HTTP_200_OK)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    await NotificationService.mark_all_as_read(db, current_user.id)
    return {"message": "All notifications marked as read"}
