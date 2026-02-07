"""0008_risk_and_alerts

Revision ID: 0008
Revises: 0007_dag_orchestration
Create Date: 2026-02-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0008'
down_revision = '0007_dag_orchestration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Risk Factors table
    op.create_table(
        'risk_factors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('max_score', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('factor_type', sa.String(50), nullable=False),
        sa.Column('calculation_rule', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_risk_factors_project_id', 'risk_factors', ['project_id'])
    op.create_index('ix_risk_factors_factor_type', 'risk_factors', ['factor_type'])

    # Asset Risk Scores table
    op.create_table(
        'asset_risk_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('asset_type', sa.String(50), nullable=False),
        sa.Column('asset_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('severity_level', sa.String(20), nullable=False, server_default="'low'"),
        sa.Column('factor_scores', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('risk_summary', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('calculated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_asset_risk_scores_project_id', 'asset_risk_scores', ['project_id'])
    op.create_index('ix_asset_risk_scores_asset', 'asset_risk_scores', ['asset_type', 'asset_id'])
    op.create_index('ix_asset_risk_scores_severity', 'asset_risk_scores', ['severity_level'])
    op.create_index('ix_asset_risk_scores_total', 'asset_risk_scores', ['total_score'])

    # Notification Channels table
    op.create_table(
        'notification_channels',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('channel_type', sa.String(50), nullable=False),
        sa.Column('config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_test_at', sa.DateTime(), nullable=True),
        sa.Column('last_test_success', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notification_channels_project_id', 'notification_channels', ['project_id'])
    op.create_index('ix_notification_channels_type', 'notification_channels', ['channel_type'])

    # Alert Policies table
    op.create_table(
        'alert_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('conditions', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('severity_threshold', sa.String(20), nullable=False, server_default="'high'"),
        sa.Column('channel_ids', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('notification_template', sa.Text(), nullable=True),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('aggregation_window', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('max_alerts_per_hour', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alert_policies_project_id', 'alert_policies', ['project_id'])
    op.create_index('ix_alert_policies_enabled', 'alert_policies', ['enabled'])

    # Alert Records table
    op.create_table(
        'alert_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('target_type', sa.String(50), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(20), nullable=False, server_default="'pending'"),
        sa.Column('acknowledged_by', sa.String(255), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('notification_results', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('aggregation_key', sa.String(255), nullable=True),
        sa.Column('aggregated_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_id'], ['alert_policies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alert_records_project_id', 'alert_records', ['project_id'])
    op.create_index('ix_alert_records_policy_id', 'alert_records', ['policy_id'])
    op.create_index('ix_alert_records_status', 'alert_records', ['status'])
    op.create_index('ix_alert_records_severity', 'alert_records', ['severity'])
    op.create_index('ix_alert_records_created_at', 'alert_records', ['created_at'])
    op.create_index(
        'ix_alert_records_aggregation',
        'alert_records',
        ['aggregation_key', 'created_at'],
    )


def downgrade() -> None:
    op.drop_table('alert_records')
    op.drop_table('alert_policies')
    op.drop_table('notification_channels')
    op.drop_table('asset_risk_scores')
    op.drop_table('risk_factors')
