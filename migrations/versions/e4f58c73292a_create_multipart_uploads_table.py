"""create upload_sessions table and refactor task_attachments

Revision ID: e4f58c73292a
Revises: 9e38d613897b
Create Date: 2026-07-13 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f58c73292a'
down_revision: Union[str, None] = '9e38d613897b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    #  Create upload_sessions table
    op.create_table(
        'upload_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('task_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('upload_id', sa.String(), nullable=False),
        sa.Column('bucket', sa.String(), nullable=False),
        sa.Column('object_key', sa.String(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='UPLOADING'),
        sa.Column('parts_info', sa.JSON(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    #  Alter task_attachments table columns
    op.alter_column('task_attachments', 'uploaded_by', new_column_name='user_id')
    op.alter_column('task_attachments', 'url', new_column_name='object_key')
    op.alter_column('task_attachments', 'file_size', new_column_name='size')

    op.add_column('task_attachments', sa.Column('bucket', sa.String(), nullable=False, server_default='local'))
    op.add_column('task_attachments', sa.Column('content_type', sa.String(), nullable=False, server_default='application/octet-stream'))
    op.add_column('task_attachments', sa.Column('etag', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('task_attachments', 'etag')
    op.drop_column('task_attachments', 'content_type')
    op.drop_column('task_attachments', 'bucket')
    op.alter_column('task_attachments', 'size', new_column_name='file_size')
    op.alter_column('task_attachments', 'object_key', new_column_name='url')
    op.alter_column('task_attachments', 'user_id', new_column_name='uploaded_by')

    op.drop_table('upload_sessions')
