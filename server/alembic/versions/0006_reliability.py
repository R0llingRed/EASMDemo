"""reliability enhancements

Revision ID: 0006_reliability
Revises: 0005_vulnerabilities
Create Date: 2026-01-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0006_reliability"
down_revision = "0005_vulnerabilities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add fingerprint_hash to subdomain
    op.add_column(
        "subdomain",
        sa.Column("fingerprint_hash", sa.String(32), nullable=True),
    )

    # Add fingerprint_hash to ip_address
    op.add_column(
        "ip_address",
        sa.Column("fingerprint_hash", sa.String(32), nullable=True),
    )

    # Add fingerprint_hash to web_asset
    op.add_column(
        "web_asset",
        sa.Column("fingerprint_hash", sa.String(32), nullable=True),
    )

    # Add rate_limit_config to project
    op.add_column(
        "project",
        sa.Column(
            "rate_limit_config",
            sa.dialects.postgresql.JSONB,
            nullable=True,
            server_default='{"max_requests_per_second": 10, "max_concurrent_scans": 5}',
        ),
    )

    # Add confidence to vulnerability
    op.add_column(
        "vulnerability",
        sa.Column("confidence", sa.Integer, nullable=True, server_default="50"),
    )

    # Create indexes
    op.create_index(
        "ix_subdomain_fingerprint_hash",
        "subdomain",
        ["fingerprint_hash"],
        unique=False,
    )
    op.create_index(
        "ix_ip_address_fingerprint_hash",
        "ip_address",
        ["fingerprint_hash"],
        unique=False,
    )
    op.create_index(
        "ix_web_asset_fingerprint_hash",
        "web_asset",
        ["fingerprint_hash"],
        unique=False,
    )

    # Add priority to scan_task
    op.add_column(
        "scan_task",
        sa.Column("priority", sa.Integer, nullable=True, server_default="5"),
    )
    op.create_index("ix_scan_task_priority", "scan_task", ["priority"])


def downgrade() -> None:
    op.drop_index("ix_scan_task_priority", table_name="scan_task")
    op.drop_column("scan_task", "priority")
    op.drop_index("ix_web_asset_fingerprint_hash", table_name="web_asset")
    op.drop_index("ix_ip_address_fingerprint_hash", table_name="ip_address")
    op.drop_index("ix_subdomain_fingerprint_hash", table_name="subdomain")
    op.drop_column("vulnerability", "confidence")
    op.drop_column("project", "rate_limit_config")
    op.drop_column("web_asset", "fingerprint_hash")
    op.drop_column("ip_address", "fingerprint_hash")
    op.drop_column("subdomain", "fingerprint_hash")
