"""vulnerabilities table

Revision ID: 0005_vulnerabilities
Revises: 0004_web_assets
Create Date: 2026-01-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_vulnerabilities"
down_revision = "0004_web_assets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vulnerability",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("project.id"),
            nullable=False,
        ),
        sa.Column("target_url", sa.String(length=2048), nullable=False),
        sa.Column("target_host", sa.String(length=255), nullable=True),
        sa.Column("target_ip", sa.String(length=45), nullable=True),
        sa.Column("target_port", sa.Integer(), nullable=True),
        sa.Column("template_id", sa.String(length=255), nullable=False),
        sa.Column("template_name", sa.String(length=512), nullable=True),
        sa.Column("severity", sa.String(length=20), nullable=False, server_default="info"),
        sa.Column("vuln_type", sa.String(length=100), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reference", sa.dialects.postgresql.JSONB(), server_default="[]"),
        sa.Column("tags", sa.dialects.postgresql.JSONB(), server_default="[]"),
        sa.Column("matched_at", sa.String(length=2048), nullable=True),
        sa.Column("matcher_name", sa.String(length=255), nullable=True),
        sa.Column("extracted_results", sa.dialects.postgresql.JSONB(), server_default="[]"),
        sa.Column("curl_command", sa.Text(), nullable=True),
        sa.Column("request", sa.Text(), nullable=True),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="open"),
        sa.Column("is_false_positive", sa.Boolean(), server_default="false"),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fixed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scanner", sa.String(length=50), server_default="nuclei"),
        sa.Column("scan_task_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("raw_output", sa.dialects.postgresql.JSONB(), server_default="{}"),
        sa.Column("first_seen", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("last_seen", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "target_url", "template_id", name="uq_vuln_key"),
    )
    op.create_index("ix_vuln_project_id", "vulnerability", ["project_id"])
    op.create_index("ix_vuln_severity", "vulnerability", ["severity"])
    op.create_index("ix_vuln_status", "vulnerability", ["status"])


def downgrade() -> None:
    op.drop_index("ix_vuln_status", table_name="vulnerability")
    op.drop_index("ix_vuln_severity", table_name="vulnerability")
    op.drop_index("ix_vuln_project_id", table_name="vulnerability")
    op.drop_table("vulnerability")
