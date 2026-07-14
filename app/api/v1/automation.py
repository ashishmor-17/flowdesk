import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.enums import UserRole
from app.core.errors import ErrorCode
from app.api.deps import get_org_member
from app.models.org_members import OrgMember
from app.schemas.automation import AutomationCreateRule, AutomationRuleUpdate, AutomationRuleResponse, AutomationHistoryResponse
from app.services import automation_service


router = APIRouter(prefix="/automation/rules", tags=["automation"])

@router.post("", response_model=AutomationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule_route(
    payload: AutomationCreateRule,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    if org_member.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.FORBIDDEN,
                "message": "Only organization Admin and Owner can create automation rules."
            }
        )
    
    return await automation_service.create_rule(
        db=db,
        org_id=org_member.org_id,
        creator_id=org_member.user_id,
        rule_in=payload
    )

@router.get("", response_model=dict[str, list[AutomationRuleResponse]])
async def list_rules_route(
    project_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    rules = await automation_service.list_rules(
        db=db,
        org_id=org_member.org_id,
        project_id=project_id
    )
    return {"rules": rules}

@router.get("/{id}", response_model=AutomationRuleResponse)
async def get_rule_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    return await automation_service.get_rule(
        db=db,
        org_id=org_member.org_id,
        rule_id=id
    )

@router.patch("/{id}", response_model=AutomationRuleResponse)
async def update_rule_route(
    id: uuid.UUID,
    payload: AutomationRuleUpdate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    if org_member.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.FORBIDDEN,
                "message": "Only organization Admin and Owner can update automation rules."
            }
        )
    
    return await automation_service.update_rule(
        db=db,
        org_id=org_member.org_id,
        rule_id=id,
        rule_in=payload
    )

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_rule_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    if org_member.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.FORBIDDEN,
                "message": "Only organization Admin and Owner can delete automation rules."
            }
        )
    
    await automation_service.delete_rule(
        db=db,
        org_id=org_member.org_id,
        rule_id=id
    )
    return {"message": "Automation rule deleted successfully"}

@router.get("/{id}/history", response_model=list[AutomationHistoryResponse])
async def get_rule_history_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    if org_member.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.FORBIDDEN,
                "message": "Only organization Admin and Owner can access rule history."
            }
        )
    
    return await automation_service.get_rule_history(
        db=db,
        org_id=org_member.org_id,
        rule_id=id
    )
