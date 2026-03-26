"""add player_infos.rating

Revision ID: 3f2a1b6c9d10
Revises: 009109da52b2
Create Date: 2026-03-26

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3f2a1b6c9d10"
down_revision: Union[str, Sequence[str], None] = "009109da52b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("player_infos", sa.Column("rating", sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("player_infos", "rating")

