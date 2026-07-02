from enum import StrEnum

class UserRole(StrEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"

class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class InvitationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"

class ProjectStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    INACTIVE = "inactive"

TASK_STATE_TRANSITIONS = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS},
    TaskStatus.IN_PROGRESS: {TaskStatus.REVIEW, TaskStatus.DONE},
    TaskStatus.REVIEW: {TaskStatus.IN_PROGRESS, TaskStatus.DONE},
    TaskStatus.DONE: {TaskStatus.TODO}
}