import asyncio
import getpass
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import get_session_factory
from app.models.user import User, UserRole, UserStatus


async def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: python scripts/create_admin.py "
            "<username> <email> <full-name>"
        )
        return 2

    username, email, full_name = sys.argv[1:]
    password = getpass.getpass("Admin password: ")
    confirmation = getpass.getpass("Confirm admin password: ")

    if password != confirmation:
        print("Passwords do not match.", file=sys.stderr)
        return 2

    session_factory = get_session_factory()
    async with session_factory() as session:
        existing = await session.execute(
            select(User).where(
                (User.username == username)
                | (User.email == email.lower())
            )
        )
        if existing.scalar_one_or_none() is not None:
            print("Username or email already exists.", file=sys.stderr)
            return 3

        admin = User(
            username=username,
            email=email.lower(),
            full_name=full_name,
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            password_hash=hash_password(password),
        )
        session.add(admin)
        await session.commit()

    print("Admin account created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
