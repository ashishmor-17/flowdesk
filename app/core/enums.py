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

class NotificationType(StrEnum):
    TASK_ASSIGNED = "task_assigned"
    TASK_UNASSIGNED = "task_unassigned"
    TASK_STATUS_CHANGE = "task_status_change"
    TASK_COMMENT_ADDED = "task_comment_added"
    TASK_OVERDUE = "task_overdue"
    MENTION = "mention"
    ORG_INVITE = "org_invite"
    AUTOMATION = "automation"

class NotificationEntityType(StrEnum):
    TASK = "task"
    COMMENT = "comment"
    INVITATION = "invitation"

class AutomationTriggerEvent(StrEnum):
    TASK_CREATED = "TASK_CREATED"
    STATUS_CHANGED = "STATUS_CHANGED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_OVERDUE = "TASK_OVERDUE"
class AutomationActionType(StrEnum):
    NOTIFY_USER = "NOTIFY_USER"
    NOTIFY_ROLE = "NOTIFY_ROLE"
    CHANGE_STATUS = "CHANGE_STATUS"
    SEND_EMAIL = "SEND_EMAIL"

TASK_STATE_TRANSITIONS = {
    TaskStatus.TODO: {TaskStatus.IN_PROGRESS},
    TaskStatus.IN_PROGRESS: {TaskStatus.REVIEW, TaskStatus.DONE},
    TaskStatus.REVIEW: {TaskStatus.IN_PROGRESS, TaskStatus.DONE},
    TaskStatus.DONE: {TaskStatus.TODO}
}