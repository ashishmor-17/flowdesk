"""create_task_links_table

Revision ID: 9e1ab30eb2ce
Revises: 9e1ab30eb2cd
Create Date: 2026-07-14 12:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e1ab30eb2ce'
down_revision: Union[str, None] = '9e1ab30eb2cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('task_links',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('org_id', sa.UUID(), nullable=False),
    sa.Column('source_task_id', sa.UUID(), nullable=False),
    sa.Column('target_task_id', sa.UUID(), nullable=False),
    sa.Column('link_type', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['source_task_id'], ['tasks.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['target_task_id'], ['tasks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('task_links')
