"""Testing...

Revision ID: 6f35d642fb4d
Revises: 0278215fd252
Create Date: 2025-04-16 15:19:00.010149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f35d642fb4d'
down_revision: Union[str, None] = '0278215fd252'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
