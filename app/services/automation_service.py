import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.automation_rules import AutomationRule
from app.models.tasks import Task
from app.schemas.automation import *
from app.core.database import transaction_scope

def validate_conditions(conditions: dict | None) -> None:

    if not conditions:
        return
    
    valid_fields = set(Task.__table__.columns.keys())
    for key in conditions.keys():
        if key not in valid_fields:
            raise HTTPException(
                status_code= status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail= {
                    "code": "INVALID_CONDITION_FIELD",
                    "message": f"Field '{key}' is not a valid task attribute."
                }
            )
        
async def create_rule(
        db: AsyncSession,
        org_id: uuid.UUID,
        creator_id: uuid.UUID,
        rule_in: AutomationCreateRule
) -> AutomationRule:
    
    validate_conditions(rule_in.conditions)

    async with transaction_scope(db):
        rule = AutomationRule(
            org_id=org_id,
            project_id=rule_in.project_id,
            name=rule_in.name,
            trigger_event=rule_in.trigger_event,
            conditions=rule_in.conditions,
            action_type=rule_in.action_type,
            action_payload=rule_in.action_payload,
            created_by=creator_id
        )
        db.add(rule)
        await db.flush()
        return rule
    
async def list_rules(
    db: AsyncSession,
    org_id: uuid.UUID,
    project_id: uuid.UUID | None = None
) -> list[AutomationRule]:
    
    query = select(AutomationRule).where(AutomationRule.org_id == org_id)
    if project_id is not None:
        query = query.where(AutomationRule.project_id == project_id)
    
    result = await db.scalars(query)
    return list(result.all())

async def get_rule(
    db: AsyncSession,
    org_id: uuid.UUID,
    rule_id: uuid.UUID
) -> AutomationRule:
    
    rule = await db.scalar(
        select(AutomationRule).where(
            AutomationRule.id == rule_id,
            AutomationRule.org_id == org_id
        )
    )
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "AUTOMATION_RULE_NOT_FOUND",
                "message": "Automation rule not found or you do not have access."
            }
        )
    return rule

async def update_rule(
    db: AsyncSession,
    org_id: uuid.UUID,
    rule_id: uuid.UUID,
    rule_in: AutomationRuleUpdate
) -> AutomationRule:
    
    if rule_in.conditions is not None:
        validate_conditions(rule_in.conditions)
        
    async with transaction_scope(db):
        rule = await get_rule(db, org_id, rule_id)
        
        update_data = rule_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)
            
        await db.flush()
        await db.refresh(rule)
        return rule
    
async def delete_rule(
    db: AsyncSession,
    org_id: uuid.UUID,
    rule_id: uuid.UUID
) -> None:
    
    async with transaction_scope(db):
        rule = await get_rule(db, org_id, rule_id)
        await db.delete(rule)