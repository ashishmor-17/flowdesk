"""add cascade to tasks and comments

Revision ID: f8e3f9479b12
Revises: 0fa609bb7e67
Create Date: 2026-07-13 12:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8e3f9479b12'
down_revision: Union[str, None] = '0fa609bb7e67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update task and comment org_id FK constraints to support CASCADE
    op.drop_constraint('tasks_org_id_fkey', 'tasks', type_='foreignkey')
    op.create_foreign_key('tasks_org_id_fkey', 'tasks', 'organizations', ['org_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('comments_org_id_fkey', 'comments', type_='foreignkey')
    op.create_foreign_key('comments_org_id_fkey', 'comments', 'organizations', ['org_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Restore comments and tasks FKs
    op.drop_constraint('comments_org_id_fkey', 'comments', type_='foreignkey')
    op.create_foreign_key('comments_org_id_fkey', 'comments', 'organizations', ['org_id'], ['id'])
    op.drop_constraint('tasks_org_id_fkey', 'tasks', type_='foreignkey')
    op.create_foreign_key('tasks_org_id_fkey', 'tasks', 'organizations', ['org_id'], ['id'])
