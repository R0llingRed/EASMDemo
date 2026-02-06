"""0009_fix_project_fk_names

Revision ID: 0009
Revises: 0008
Create Date: 2026-02-06
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

_PROJECT_FK_TABLES = [
    "risk_factors",
    "asset_risk_scores",
    "notification_channels",
    "alert_policies",
    "alert_records",
]


def _replace_fk_if_needed(table_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for fk in inspector.get_foreign_keys(table_name):
        constrained_columns = fk.get("constrained_columns") or []
        referred_table = fk.get("referred_table")
        fk_name = fk.get("name")

        if constrained_columns != ["project_id"]:
            continue
        if referred_table != "projects":
            continue
        if not fk_name:
            continue

        op.drop_constraint(fk_name, table_name, type_="foreignkey")
        op.create_foreign_key(
            fk_name,
            table_name,
            "project",
            ["project_id"],
            ["id"],
            ondelete="CASCADE",
        )


def upgrade() -> None:
    for table_name in _PROJECT_FK_TABLES:
        _replace_fk_if_needed(table_name)


def downgrade() -> None:
    # No-op: downgrade would re-introduce invalid FK targets (`projects.id`).
    pass
