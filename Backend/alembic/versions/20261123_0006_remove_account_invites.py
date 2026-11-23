"""remove account invitation tables and states

Revision ID: 20261123_0006
Revises: 20261123_0005
Create Date: 2026-11-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261123_0006"
down_revision: Union[str, Sequence[str], None] = "20261123_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE users SET status = 'active' WHERE status::text = 'invite_pending'"
    )
    op.drop_table("account_invites")

    op.execute("ALTER TABLE users ALTER COLUMN status TYPE text USING status::text")
    op.execute("DROP TYPE user_status")
    op.execute("CREATE TYPE user_status AS ENUM ('active', 'disabled')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN status "
        "TYPE user_status USING status::text::user_status"
    )
    op.alter_column(
        "users",
        "status",
        server_default="active",
        existing_type=sa.Enum(
            "active",
            "disabled",
            name="user_status",
        ),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.execute("ALTER TABLE users ALTER COLUMN status TYPE text USING status::text")
    op.execute("DROP TYPE user_status")
    op.execute(
        "CREATE TYPE user_status AS ENUM "
        "('invite_pending', 'active', 'disabled')"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN status "
        "TYPE user_status USING status::text::user_status"
    )
