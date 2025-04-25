import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy.exc import IntegrityError

# f-ck me...
PROJECT_ROOT = Path(Path(__file__).parent / os.pardir).resolve()
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))


from common.utils import hash_password
from domain.users.entities import User
from infrastructure.sqlalchemy.repositories import SQLAlchemyUserRepository


async def create_user(username: str, email: str, password: str):
    repo = SQLAlchemyUserRepository()
    user = User(id=None, username=username, email=email, password_hash=hash_password(password))

    try:
        created = await repo.add(user)

    except IntegrityError:
        print("Could not create user: username or email already exists.")
        return
    except Exception as exc:  # noqa: BLE001  # bleh...
        print(f"Unexpected error while creating user: {exc!r}")
        return

    print(f"Created test user: id={created.id}, username={created.username}, email={created.email}")


def main():
    if len(sys.argv) != 4:  # noqa: PLR2004  # magic is fun!
        print("Usage: seed_test_user.py <username> <email> <password>")
        sys.exit(1)

    _, username, email, password = sys.argv

    try:
        asyncio.run(create_user(username, email, password))

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:  # noqa: BLE001  # bleh...
        print(f"Fatal error: {e!r}")
        sys.exit(1)


if __name__ == "__main__":
    main()
