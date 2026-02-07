"""0012_scan_task_policy_link

Revision ID: 0012_scan_task_policy_link
Revises: 0011_api_risk_workflow
Create Date: 2026-02-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0012_scan_task_policy_link"
down_revision = "0011_api_risk_workflow"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "scan_task",
        sa.Column("scan_policy_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_scan_task_scan_policy_id", "scan_task", ["scan_policy_id"])
    op.create_foreign_key(
        "fk_scan_task_scan_policy_id",
        "scan_task",
        "scan_policy",
        ["scan_policy_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_scan_task_scan_policy_id", "scan_task", type_="foreignkey")
    op.drop_index("ix_scan_task_scan_policy_id", table_name="scan_task")
    op.drop_column("scan_task", "scan_policy_id")
