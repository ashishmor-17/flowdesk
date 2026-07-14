"""create_approval_requests_table

Revision ID: 7da3d9e83f2a
Revises: 6cadda8a3e7c
Create Date: 2026-07-14 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7da3d9e83f2a'
down_revision: Union[str, None] = '6cadda8a3e7c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('approval_requests',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('task_id', sa.UUID(), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('requestor_id', sa.UUID(), nullable=False),
    sa.Column('approver_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('comment', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['requestor_id'], ['users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('approval_requests')
