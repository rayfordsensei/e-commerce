from pathlib import Path

from alembic import command
from alembic.config import Config


def run_migrations():
    # config = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
    config = Config(Path(Path(__file__).parent / "alembic.ini"))
    command.upgrade(config, "head")
