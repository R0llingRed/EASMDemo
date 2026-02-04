"""DAG orchestration models

Revision ID: 0007_dag_orchestration
Revises: 0006_reliability
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0007_dag_orchestration"
down_revision = "0006_reliability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # DAG Template table
    op.create_table(
        "dag_template",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("nodes", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("edges", postgresql.JSONB, server_default="[]"),
        sa.Column("is_system", sa.Boolean, default=False, index=True),
        sa.Column("enabled", sa.Boolean, default=True, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Scan Policy table
    op.create_table(
        "scan_policy",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("scan_config", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "dag_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dag_template.id"),
            nullable=True,
        ),
        sa.Column("is_default", sa.Boolean, default=False, index=True),
        sa.Column("enabled", sa.Boolean, default=True, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # DAG Execution table
    op.create_table(
        "dag_execution",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "dag_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dag_template.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("trigger_type", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("trigger_event", postgresql.JSONB, server_default="{}"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending", index=True),
        sa.Column("node_states", postgresql.JSONB, server_default="{}"),
        sa.Column("node_task_ids", postgresql.JSONB, server_default="{}"),
        sa.Column("input_config", postgresql.JSONB, server_default="{}"),
        sa.Column("error_message", sa.Text),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Event Trigger table
    op.create_table(
        "event_trigger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("event_type", sa.String(64), nullable=False, index=True),
        sa.Column("filter_config", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "dag_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("dag_template.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("dag_config", postgresql.JSONB, server_default="{}"),
        sa.Column("enabled", sa.Boolean, default=True, index=True),
        sa.Column(
            "trigger_count",
            postgresql.JSONB,
            server_default='{"total": 0, "success": 0, "failed": 0}',
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("event_trigger")
    op.drop_table("dag_execution")
    op.drop_table("scan_policy")
    op.drop_table("dag_template")
