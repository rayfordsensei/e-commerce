"""Testing...

Revision ID: e0d0c5b23b3b
Revises: 6f35d642fb4d
Create Date: 2025-04-16 15:40:05.934492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0d0c5b23b3b'
down_revision: Union[str, None] = '6f35d642fb4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
