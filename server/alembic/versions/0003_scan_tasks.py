"""scan tasks and results

Revision ID: 0003_scan_tasks
Revises: 0002_assets
Create Date: 2026-01-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_scan_tasks"
down_revision = "0002_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # scan_task table
    op.create_table(
        "scan_task",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.Column("task_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("progress", sa.Integer(), server_default="0"),
        sa.Column("total_targets", sa.Integer(), server_default="0"),
        sa.Column("completed_targets", sa.Integer(), server_default="0"),
        sa.Column("config", sa.dialects.postgresql.JSONB(), server_default="{}"),
        sa.Column("result_summary", sa.dialects.postgresql.JSONB(), server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_scan_task_project_id", "scan_task", ["project_id"])
    op.create_index("ix_scan_task_task_type", "scan_task", ["task_type"])
    op.create_index("ix_scan_task_status", "scan_task", ["status"])

    # subdomain table
    op.create_table(
        "subdomain",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.Column("root_domain", sa.String(length=255), nullable=False),
        sa.Column("subdomain", sa.String(length=512), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=True),
        sa.Column("ip_addresses", sa.dialects.postgresql.JSONB(), server_default="[]"),
        sa.Column("cname", sa.Text(), nullable=True),
        sa.Column("is_cdn", sa.Boolean(), server_default="false"),
        sa.Column("cdn_provider", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="active"),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "subdomain", name="uq_subdomain_key"),
    )
    op.create_index("ix_subdomain_project_id", "subdomain", ["project_id"])
    op.create_index("ix_subdomain_root_domain", "subdomain", ["root_domain"])
    op.create_index("ix_subdomain_subdomain", "subdomain", ["subdomain"])

    # ip_address table
    op.create_table(
        "ip_address",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.Column("ip", sa.String(length=45), nullable=False),
        sa.Column("source", sa.String(length=128), nullable=True),
        sa.Column("asn", sa.String(length=64), nullable=True),
        sa.Column("asn_org", sa.String(length=255), nullable=True),
        sa.Column("country", sa.String(length=16), nullable=True),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("is_cdn", sa.Boolean(), server_default="false"),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "ip", name="uq_ip_address_key"),
    )
    op.create_index("ix_ip_address_project_id", "ip_address", ["project_id"])
    op.create_index("ix_ip_address_ip", "ip_address", ["ip"])

    # port table
    op.create_table(
        "port",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ip_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ip_address.id"),
            nullable=False,
        ),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column("protocol", sa.String(length=16), server_default="tcp"),
        sa.Column("state", sa.String(length=32), nullable=True),
        sa.Column("service", sa.String(length=128), nullable=True),
        sa.Column("version", sa.String(length=255), nullable=True),
        sa.Column("banner", sa.Text(), nullable=True),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("ip_id", "port", "protocol", name="uq_port_key"),
    )
    op.create_index("ix_port_ip_id", "port", ["ip_id"])


def downgrade() -> None:
    op.drop_index("ix_port_ip_id", table_name="port")
    op.drop_table("port")

    op.drop_index("ix_ip_address_ip", table_name="ip_address")
    op.drop_index("ix_ip_address_project_id", table_name="ip_address")
    op.drop_table("ip_address")

    op.drop_index("ix_subdomain_subdomain", table_name="subdomain")
    op.drop_index("ix_subdomain_root_domain", table_name="subdomain")
    op.drop_index("ix_subdomain_project_id", table_name="subdomain")
    op.drop_table("subdomain")

    op.drop_index("ix_scan_task_status", table_name="scan_task")
    op.drop_index("ix_scan_task_task_type", table_name="scan_task")
    op.drop_index("ix_scan_task_project_id", table_name="scan_task")
    op.drop_table("scan_task")
