"""Add SuspensionLog audit table

Revision ID: 0609ec198727
Revises: 4d9139cfe04c
Create Date: 2026-09-21 23:21:43.693248

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0609ec198727'
down_revision = '4d9139cfe04c'
branch_labels = None
depends_on = None


def upgrade():
    # Only create the new suspension_logs audit table
    op.create_table('suspension_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('faculty_id', sa.Integer(), nullable=False),
    sa.Column('event_type', sa.String(length=20), nullable=False),
    sa.Column('reason', sa.String(length=512), nullable=True),
    sa.Column('suspended_until', sa.DateTime(), nullable=True),
    sa.Column('strike_count', sa.Integer(), nullable=False),
    sa.Column('lifted_by_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['faculty_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['lifted_by_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('suspension_logs')
