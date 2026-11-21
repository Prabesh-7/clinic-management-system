"""simplify account and membership roles

Revision ID: 20261121_0004
Revises: 20261121_0003
Create Date: 2026-11-21
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20261121_0004"
down_revision: Union[str, Sequence[str], None] = "20261121_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("dentist_profiles")

    op.execute(
        "UPDATE users SET role = 'dental' "
        "WHERE role::text IN ('clinic_owner', 'receptionist', 'accountant')"
    )

    op.execute("ALTER TABLE users ALTER COLUMN role TYPE text USING role::text")
    op.execute("DROP TYPE user_role")
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'dental')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN role "
        "TYPE user_role USING role::text::user_role"
    )

    op.execute(
        "UPDATE clinic_memberships SET role = 'owner' "
        "WHERE role::text != 'owner'"
    )
    op.execute(
        "ALTER TABLE clinic_memberships "
        "ALTER COLUMN role TYPE text USING role::text"
    )
    op.execute("DROP TYPE membership_role")
    op.execute("CREATE TYPE membership_role AS ENUM ('owner')")
    op.execute(
        "ALTER TABLE clinic_memberships "
        "ALTER COLUMN role TYPE membership_role USING role::text::membership_role"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE clinic_memberships "
        "ALTER COLUMN role TYPE text USING role::text"
    )
    op.execute("DROP TYPE membership_role")
    op.execute(
        "CREATE TYPE membership_role AS ENUM "
        "('owner', 'dentist', 'receptionist', 'accountant')"
    )
    op.execute(
        "ALTER TABLE clinic_memberships "
        "ALTER COLUMN role TYPE membership_role USING role::text::membership_role"
    )

    op.execute("ALTER TABLE users ALTER COLUMN role TYPE text USING role::text")
    op.execute("DROP TYPE user_role")
    op.execute(
        "CREATE TYPE user_role AS ENUM "
        "('admin', 'clinic_owner', 'dental', 'receptionist', 'accountant')"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN role "
        "TYPE user_role USING role::text::user_role"
    )
