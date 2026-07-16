import uuid
from datetime import datetime
import io

from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.attachments import TaskAttachmentResponse
from app.models.task_attachments import TaskAttachment
from app.schemas.multipart import *

from app.core.database import get_db
from app.api.deps import get_org_member
from app.models.org_members import OrgMember
from app.schemas.tasks import *
from app.schemas.approval import ApprovalRequestCreate, ApprovalRequestDecision, ApprovalRequestResponse
from app.schemas.time_entry import TimeEntryCreate, TimeEntryResponse
from app.schemas.task_link import TaskLinkCreate, TaskLinkResponse
from app.schemas.activity_log import ActivityLogResponse
from app.services import task_service
from app.services import attachment_service
from app.services import upload_session_service
from app.services import approval_service
from app.services import time_entry_service
from app.services import task_link_service
from app.services.audit_service import AuditService

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=TaskResponse, status_code= status.HTTP_201_CREATED)
async def create_task_route(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    return await task_service.create_task(
        db=db,
        org_id=org_member.org_id,
        creator_id=org_member.user_id,
        task_in=payload
    )

@router.get("",response_model=TaskListResponse)
async def list_tasks_route(

    project_id: uuid.UUID | None = None,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    assigned_to: uuid.UUID | None = None,
    due_date: date | None = None,
    cursor: str | None = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    tasks, next_cursor = await task_service.list_tasks(
        db=db,
        org_id=org_member.org_id,
        project_id=project_id,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        due_date=due_date,
        cursor=cursor,
        limit=limit
    )
    return {"tasks": tasks, "next_cursor": next_cursor}

@router.get("/{id}", response_model=TaskResponse)
async def get_task_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    return await task_service.get_task(
        db=db,
        org_id= org_member.org_id,
        task_id=id
    )

@router.patch("/{id}", response_model= TaskResponse)
async def update_task_route(
    id: uuid.UUID,
    payload: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    return await task_service.update_task(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        task_in=payload,
        actor_id=org_member.user_id
    )

@router.patch("/{id}/status", response_model=TaskResponse)
async def update_task_status_route(
    id: uuid.UUID,
    payload: TaskStatusUpdate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    return await task_service.update_task_status(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        status_in=payload,
        caller_member=org_member
    )

@router.patch("/{id}/assign", response_model= TaskResponse)
async def assign_task_route(
    id: uuid.UUID,
    payload: TaskAssignUpdate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    return await task_service.assign_task(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        payload=payload,
        caller_member=org_member
    )

@router.delete("/{id}", status_code= status.HTTP_204_NO_CONTENT)
async def delete_task_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    await task_service.delete_task(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        caller_member=org_member
    )

@router.post("/{id}/assignees", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def add_task_assignee_route(
    id: uuid.UUID,
    payload: TaskAssigneeCreate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    return await task_service.add_task_assignee(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        payload=payload,
        caller_member=org_member
    )

@router.post("/{id}/watchers", status_code=status.HTTP_201_CREATED)
async def watch_task_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    await task_service.add_task_watcher(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        user_id=org_member.user_id
    )
    return {"message": "Task watched successfully."}

@router.delete("/{id}/watchers/{user_id}", status_code=status.HTTP_200_OK)
async def unwatch_task_route(
    id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    await task_service.remove_task_watcher(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        user_id=user_id,
        caller_member=org_member
    )
    return {"message": "Task unwatched successfully."}


def make_attachment_response(attachment: TaskAttachment) -> TaskAttachmentResponse:
    return TaskAttachmentResponse(
        id=attachment.id,
        task_id=attachment.task_id,
        user_id=attachment.user_id,
        bucket=attachment.bucket,
        object_key=attachment.object_key,
        filename=attachment.filename,
        content_type=attachment.content_type,
        size=attachment.size,
        etag=attachment.etag,
        created_at=attachment.created_at
    )


@router.post("/{id}/attachments", response_model=TaskAttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):

    content = await file.read()
    attachment = await attachment_service.create_attachment(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        filename=file.filename,
        file_content=content,
        uploaded_by=org_member.user_id,
        content_type=file.content_type or "application/octet-stream"
    )
    return make_attachment_response(attachment)


@router.get("/{id}/attachments", response_model=list[TaskAttachmentResponse])
async def list_attachments_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):

    attachments = await attachment_service.list_attachments(
        db=db,
        org_id=org_member.org_id,
        task_id=id
    )
    return [make_attachment_response(a) for a in attachments]


@router.delete("/{id}/attachments/{attachment_id}")
async def delete_attachment_route(
    id: uuid.UUID,
    attachment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):

    await attachment_service.delete_attachment(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        attachment_id=attachment_id,
        user_id=org_member.user_id,
        user_role=org_member.role
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}/attachments/{attachment_id}/download")
async def download_attachment_route(
    id: uuid.UUID,
    attachment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    content, filename = await attachment_service.get_attachment_file(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        attachment_id=attachment_id
    )
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/{id}/attachments/upload/initiate", response_model=UploadSessionInitiateResponse, status_code=status.HTTP_201_CREATED)
async def initiate_upload_session_route(
    id: uuid.UUID,
    payload: UploadSessionInitiateRequest,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    session = await upload_session_service.initiate_session(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        filename=payload.filename,
        file_size=payload.file_size,
        user_id=org_member.user_id
    )
    return UploadSessionInitiateResponse(
        id=session.id,
        user_id=session.user_id,
        upload_id=session.upload_id,
        bucket=session.bucket,
        object_key=session.object_key,
        status=session.status,
        expires_at=session.expires_at,
        created_at=session.created_at
    )


@router.post("/{id}/attachments/upload/{session_id}/parts", response_model=UploadSessionPartResponse)
async def upload_session_part_route(
    id: uuid.UUID,
    session_id: uuid.UUID,
    part_number: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    content = await file.read()
    result = await upload_session_service.upload_part(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        session_id=session_id,
        part_number=part_number,
        content=content
    )
    return UploadSessionPartResponse(
        part_number=result["part_number"],
        status=result["status"]
    )


@router.post("/{id}/attachments/upload/{session_id}/complete", response_model=TaskAttachmentResponse)
async def complete_upload_session_route(
    id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    attachment = await upload_session_service.complete_session(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        session_id=session_id
    )
    return make_attachment_response(attachment)


@router.post("/{id}/attachments/upload/{session_id}/abort", status_code=status.HTTP_204_NO_CONTENT)
async def abort_upload_session_route(
    id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    await upload_session_service.abort_session(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        session_id=session_id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}/attachments/upload/{session_id}", response_model=UploadSessionProgressResponse)
async def get_upload_session_progress_route(
    id: uuid.UUID,
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    
    progress = await upload_session_service.get_session_progress(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        session_id=session_id
    )
    return UploadSessionProgressResponse(
        id=progress["id"],
        filename=progress["filename"],
        file_size=progress["file_size"],
        parts_uploaded=progress["parts_uploaded"],
        expires_at=progress["expires_at"]
    )


@router.post("/{id}/approvals", response_model=ApprovalRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_approval_route(
    id: uuid.UUID,
    payload: ApprovalRequestCreate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    return await approval_service.create_approval_request(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        requestor_id=org_member.user_id,
        approver_id=payload.approver_id
    )


@router.patch("/{id}/approvals/{approval_id}", response_model=ApprovalRequestResponse)
async def decide_approval_route(
    id: uuid.UUID,
    approval_id: uuid.UUID,
    payload: ApprovalRequestDecision,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    return await approval_service.decide_approval_request(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        approval_id=approval_id,
        decider_id=org_member.user_id,
        decider_role=org_member.role,
        status_choice=payload.status,
        comment=payload.comment
    )


@router.get("/{id}/approvals", response_model=list[ApprovalRequestResponse], status_code=status.HTTP_200_OK)
async def list_approvals_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    return await approval_service.list_approvals(db, org_member.org_id, id)



@router.post("/{id}/time-entries", response_model=TimeEntryResponse, status_code=status.HTTP_201_CREATED)
async def log_time_route(
    id: uuid.UUID,
    payload: TimeEntryCreate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    return await time_entry_service.log_time(
        db=db,
        org_id=org_member.org_id,
        task_id=id,
        user_id=org_member.user_id,
        minutes=payload.minutes,
        description=payload.description
    )


@router.get("/{id}/time-entries", response_model=list[TimeEntryResponse])
async def list_time_entries_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    return await time_entry_service.list_time_entries(
        db=db,
        org_id=org_member.org_id,
        task_id=id
    )


@router.post("/{id}/links", response_model=TaskLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link_route(
    id: uuid.UUID,
    payload: TaskLinkCreate,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    return await task_link_service.create_link(
        db=db,
        org_id=org_member.org_id,
        source_task_id=id,
        target_task_id=payload.target_task_id,
        link_type=payload.link_type,
        actor_id=org_member.user_id
    )


@router.delete("/{id}/links/{link_id}", status_code=status.HTTP_200_OK)
async def delete_link_route(
    id: uuid.UUID,
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    await task_link_service.delete_link(
        db=db,
        org_id=org_member.org_id,
        source_task_id=id,
        link_id=link_id,
        actor_id=org_member.user_id
    )


@router.get("/{id}/activity", response_model=list[ActivityLogResponse], status_code=status.HTTP_200_OK)
async def list_task_activity_route(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_member: OrgMember = Depends(get_org_member)
):
    await task_service.get_task(db, org_member.org_id, id)
    return await AuditService.list_task_activity_logs(db, org_member.org_id, id)