# backend/alembic/versions/add_api_tracking_tables.py
"""Add API tracking tables

Revision ID: add_api_tracking
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import DateTime, func

# revision identifiers, used by Alembic.
revision = 'add_api_tracking'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create api_calls table
    op.create_table(
        'api_calls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('route_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=func.now()),
        sa.Column('response_time', sa.Float(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['route_id'], ['routes.id'], )
    )
    op.create_index(op.f('ix_api_calls_timestamp'), 'api_calls', ['timestamp'], unique=False)
    
    # Create api_quota_usage table
    op.create_table(
        'api_quota_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('calls_made', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('successful_calls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_calls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=func.now(), onupdate=func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date')
    )
    op.create_index(op.f('ix_api_quota_usage_date'), 'api_quota_usage', ['date'], unique=True)
    
    # Add last_scanned_at column to routes table if it doesn't exist
    try:
        op.add_column('routes', sa.Column('last_scanned_at', sa.DateTime(), nullable=True))
    except:
        pass  # Column might already exist

def downgrade():
    op.drop_index(op.f('ix_api_quota_usage_date'), table_name='api_quota_usage')
    op.drop_table('api_quota_usage')
    op.drop_index(op.f('ix_api_calls_timestamp'), table_name='api_calls')
    op.drop_table('api_calls')
    
    try:
        op.drop_column('routes', 'last_scanned_at')
    except:
        pass