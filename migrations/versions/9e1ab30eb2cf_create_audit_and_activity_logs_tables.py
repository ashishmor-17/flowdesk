"""create_audit_and_activity_logs_tables

Revision ID: 9e1ab30eb2cf
Revises: 9e1ab30eb2ce
Create Date: 2026-07-14 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9e1ab30eb2cf'
down_revision: Union[str, None] = '9e1ab30eb2ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    # Create indexes for audit_logs
    op.create_index('ix_audit_logs_org_created', 'audit_logs', ['org_id', 'created_at'])
    op.create_index('ix_audit_logs_entity_created', 'audit_logs', ['entity_type', 'entity_id', 'created_at'])

    # Create activity_logs table
    op.create_table('activity_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('org_id', sa.UUID(), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    # Create indexes for activity_logs
    op.create_index('ix_activity_logs_org_created', 'activity_logs', ['org_id', 'created_at'])
    op.create_index('ix_activity_logs_entity_created', 'activity_logs', ['entity_type', 'entity_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_activity_logs_entity_created', table_name='activity_logs')
    op.drop_index('ix_activity_logs_org_created', table_name='activity_logs')
    op.drop_table('activity_logs')

    op.drop_index('ix_audit_logs_entity_created', table_name='audit_logs')
    op.drop_index('ix_audit_logs_org_created', table_name='audit_logs')
    op.drop_table('audit_logs')
