from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.users import User
from app.models.org_members import OrgMember
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

    # Fetch user's organization membership with eager organization loading
    org_member = await db.scalar(
        select(OrgMember)
        .where(OrgMember.user_id == current_user.id)
        .options(selectinload(OrgMember.org))
    )
    current_user.org_id = org_member.org_id if org_member else None
    current_user.org_name = org_member.org.name if org_member and org_member.org else None

    return current_user
