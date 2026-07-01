import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.enums import UserRole
from app.core.errors import ErrorCode
from app.api.deps import get_org_member
from app.models.org_members import OrgMember
from app.models.projects import Project
from app.schemas.projects import *
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("", response_model= ProjectResponse, status_code= status.HTTP_201_CREATED)
async def create_project_route(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    if org_member.role not in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(
            status_code= status.HTTP_403_FORBIDDEN,
            detail= {
                "code": ErrorCode.FORBIDDEN,
                "message": "Only organizations Admin and Owner can create projects."
            }
        )
    
    return await project_service.create_project(
        db=db,
        org_id=org_member.org_id,
        creator_id=org_member.user_id,
        project_in=payload
    )

@router.get("", response_model=ProjectListResponse)
async def list_projects_route(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    status_enum = None
    if status is not None:
        try:
            status_enum = ProjectStatus(status.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "VALIDATION_ERROR",
                    "message": f"Status must be one of: ACTIVE, ARCHIVED"
                }
            )

    projects = await project_service.list_projects(
        db=db,
        org_id=org_member.org_id,
        status=status_enum
    )

    return {"projects": projects}

@router.get("/{id}", response_model=ProjectResponse)
async def get_project_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    return await project_service.get_project(
        db=db,
        org_id=org_member.org_id,
        project_id=id
    )

@router.patch("/{id}", response_model=ProjectResponse)
async def update_project_route(
    id: uuid.UUID,
    payload: ProjectUpdate,
    db: AsyncSession =Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    if org_member.role not in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(
            status_code= status.HTTP_403_FORBIDDEN,
            detail= {
                "code": ErrorCode.FORBIDDEN,
                "message": "Only organizations Admin and Owner can update projects."
            }
        )
    
    return await project_service.update_project(
        db=db,
        org_id=org_member.org_id,
        project_id=id,
        project_in=payload
    )

@router.patch("/{id}/archive", response_model=ProjectArchiveResponse)
async def archive_project_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    if org_member.role not in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(
            status_code= status.HTTP_403_FORBIDDEN,
            detail= {
                "code": ErrorCode.FORBIDDEN,
                "message": "Only organizations Admin and Owner can archive projects."
            }
        )
    
    project = await project_service.archive_project(
        db=db,
        org_id=org_member.org_id,
        project_id=id
    )
    return ProjectArchiveResponse(
        id=project.id,
        status=project.status.value.upper()
    )

@router.delete("/{id}", status_code= status.HTTP_200_OK)
async def delete_project_route(
    id: uuid.UUID,
    cascade: bool = False,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    if org_member.role != UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": ErrorCode.FORBIDDEN,
                "message": "Only organization Owners can delete projects."
            }
        )
        
    await project_service.delete_project(
        db=db,
        org_id=org_member.org_id,
        project_id=id,
        cascade=cascade
    )
    return {"message": "Project deleted"}