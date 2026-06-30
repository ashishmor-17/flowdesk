from enum import StrEnum

class ErrorCode(StrEnum):
    SLUG_TAKEN = "slug_taken"
    ALREADY_MEMBER = "already_member"
    FORBIDDEN = "forbidden"
    INVITE_NOT_FOUND = "invite_not_found"
    INVITE_EXPIRED = "invite_expired"
