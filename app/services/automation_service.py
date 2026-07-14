import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation_rules import AutomationRule
from app.models.automation_history import AutomationHistory
from app.models.tasks import Task
from app.schemas.automation import AutomationCreateRule, AutomationRuleUpdate
from app.core.database import transaction_scope
from app.repositories.automation_repository import AutomationRepository

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
        return await AutomationRepository.create(
            db,
            org_id=org_id,
            project_id=rule_in.project_id,
            name=rule_in.name,
            trigger_event=rule_in.trigger_event,
            conditions=rule_in.conditions,
            action_type=rule_in.action_type,
            action_payload=rule_in.action_payload,
            created_by=creator_id
        )
    
async def list_rules(
    db: AsyncSession,
    org_id: uuid.UUID,
    project_id: uuid.UUID | None = None
) -> list[AutomationRule]:
    return await AutomationRepository.list_rules(db, org_id, project_id)

async def get_rule(
    db: AsyncSession,
    org_id: uuid.UUID,
    rule_id: uuid.UUID
) -> AutomationRule:
    rule = await AutomationRepository.get_by_id(db, org_id, rule_id)
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
        await AutomationRepository.delete(db, rule)


async def get_rule_history(
    db: AsyncSession,
    org_id: uuid.UUID,
    rule_id: uuid.UUID
) -> list[AutomationHistory]:
    rule = await get_rule(db, org_id, rule_id)
    return await AutomationRepository.list_history(db, rule.id)
