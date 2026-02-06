"""0011_api_risk_workflow

Revision ID: 0011_api_risk_workflow
Revises: 0010_js_api_deep_analysis
Create Date: 2026-02-06
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0011_api_risk_workflow"
down_revision = "0010_js_api_deep_analysis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("api_risk_finding", sa.Column("updated_by", sa.String(length=255), nullable=True))
    op.add_column(
        "api_risk_finding",
        sa.Column("resolution_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "api_risk_finding",
        sa.Column(
            "status_history",
            postgresql.JSONB(),
            nullable=True,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("api_risk_finding", "status_history")
    op.drop_column("api_risk_finding", "resolution_notes")
    op.drop_column("api_risk_finding", "updated_by")
