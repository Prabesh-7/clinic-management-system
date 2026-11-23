"""use direct clinic owner identity

Revision ID: 20261123_0005
Revises: 20261121_0004
Create Date: 2026-11-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261123_0005"
down_revision: Union[str, Sequence[str], None] = "20261121_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "clinics",
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    op.execute(
        """
        UPDATE clinics AS clinic
        SET owner_user_id = membership.user_id
        FROM clinic_memberships AS membership
        WHERE membership.clinic_id = clinic.id
          AND membership.role = 'owner'
          AND membership.status = 'active'
        """
    )

    op.create_index(
        "ix_clinics_owner_user_id",
        "clinics",
        ["owner_user_id"],
        unique=True,
    )
    op.create_foreign_key(
        "fk_clinics_owner_user_id_users",
        "clinics",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="NO ACTION",
    )

    op.drop_index("ix_clinic_memberships_user_id", table_name="clinic_memberships")
    op.drop_index("ix_clinic_memberships_clinic_id", table_name="clinic_memberships")
    op.drop_table("clinic_memberships")
    op.execute("DROP TYPE membership_status")
    op.execute("DROP TYPE membership_role")


def downgrade() -> None:
    op.execute("CREATE TYPE membership_role AS ENUM ('owner')")
    op.execute(
        "CREATE TYPE membership_status AS ENUM "
        "('invite_pending', 'active', 'disabled')"
    )
    membership_role = postgresql.ENUM(
        "owner",
        name="membership_role",
        create_type=False,
    )
    membership_status = postgresql.ENUM(
        "invite_pending",
        "active",
        "disabled",
        name="membership_status",
        create_type=False,
    )
    op.create_table(
        "clinic_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", membership_role, nullable=False),
        sa.Column("status", membership_status, nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["clinic_id"],
            ["clinics.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "user_id", name="uq_clinic_membership"),
    )
    op.execute(
        """
        INSERT INTO clinic_memberships (
            id, clinic_id, user_id, role, status, is_primary
        )
        SELECT
            gen_random_uuid(),
            id,
            owner_user_id,
            'owner',
            'active',
            true
        FROM clinics
        WHERE owner_user_id IS NOT NULL
        """
    )
    op.create_index(
        "ix_clinic_memberships_clinic_id",
        "clinic_memberships",
        ["clinic_id"],
        unique=False,
    )
    op.create_index(
        "ix_clinic_memberships_user_id",
        "clinic_memberships",
        ["user_id"],
        unique=False,
    )

    op.drop_constraint(
        "fk_clinics_owner_user_id_users",
        "clinics",
        type_="foreignkey",
    )
    op.drop_index("ix_clinics_owner_user_id", table_name="clinics")
    op.drop_column("clinics", "owner_user_id")
