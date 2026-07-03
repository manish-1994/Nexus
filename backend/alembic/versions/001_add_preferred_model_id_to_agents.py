"""add_preferred_model_id_to_agents

Revision ID: 001
Revises:
Create Date: 2026-07-03

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("preferred_model_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_agents_preferred_model",
        "agents",
        "models",
        ["preferred_model_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_agents_preferred_model", "agents", type_="foreignkey")
    op.drop_column("agents", "preferred_model_id")
