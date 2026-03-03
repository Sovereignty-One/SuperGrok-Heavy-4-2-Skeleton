"""Add alerts table

Revision ID: 001_add_alerts
Revises: 
Create Date: 2026-02-12 21:52:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_alerts'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for alert_type
    alert_type_enum = postgresql.ENUM(
        'info', 'warning', 'error', 'security',
        'debugger_touch', 'chain_break', 'lie_detected',
        'override_spoken', 'yuva9v_tripped', 'system',
        name='alerttype'
    )
    alert_type_enum.create(op.get_bind(), checkfirst=True)
    
    # Create alerts table
    op.create_table(
        'alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.Enum(
            'info', 'warning', 'error', 'security',
            'debugger_touch', 'chain_break', 'lie_detected',
            'override_spoken', 'yuva9v_tripped', 'system',
            name='alerttype'
        ), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_dismissed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('source', sa.String(length=100), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('action_url', sa.String(length=500), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('ix_alerts_id', 'alerts', ['id'])
    op.create_index('ix_alerts_user_id', 'alerts', ['user_id'])
    op.create_index('ix_alerts_type', 'alerts', ['type'])
    op.create_index('ix_alerts_is_read', 'alerts', ['is_read'])
    op.create_index('ix_alerts_created_at', 'alerts', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_alerts_created_at', table_name='alerts')
    op.drop_index('ix_alerts_is_read', table_name='alerts')
    op.drop_index('ix_alerts_type', table_name='alerts')
    op.drop_index('ix_alerts_user_id', table_name='alerts')
    op.drop_index('ix_alerts_id', table_name='alerts')
    
    # Drop table
    op.drop_table('alerts')
    
    # Drop enum type
    alert_type_enum = postgresql.ENUM(
        'info', 'warning', 'error', 'security',
        'debugger_touch', 'chain_break', 'lie_detected',
        'override_spoken', 'yuva9v_tripped', 'system',
        name='alerttype'
    )
    alert_type_enum.drop(op.get_bind(), checkfirst=True)
