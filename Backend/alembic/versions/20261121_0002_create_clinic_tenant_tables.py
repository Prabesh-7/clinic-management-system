"""create clinic tenant tables

Revision ID: 20261121_0002
Revises: 20261120_0001
Create Date: 2026-11-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20261121_0002"
down_revision: Union[str, Sequence[str], None] = "20261120_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'clinic_owner'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'receptionist'")
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'accountant'")

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE clinic_status AS ENUM (
                'draft', 'pending_verification', 'active', 'suspended', 'closed'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE membership_role AS ENUM (
                'owner', 'dentist', 'receptionist', 'accountant'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE membership_status AS ENUM (
                'invite_pending', 'active', 'disabled'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    clinic_status = postgresql.ENUM(
        "draft", "pending_verification", "active", "suspended", "closed",
        name="clinic_status", create_type=False,
    )
    membership_role = postgresql.ENUM(
        "owner", "dentist", "receptionist", "accountant",
        name="membership_role", create_type=False,
    )
    membership_status = postgresql.ENUM(
        "invite_pending", "active", "disabled",
        name="membership_status", create_type=False,
    )

    op.create_table(
        "clinics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(220), nullable=False),
        sa.Column("registration_number", sa.String(100), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("timezone", sa.String(100), server_default="Asia/Kathmandu", nullable=False),
        sa.Column("currency", sa.String(3), server_default="NPR", nullable=False),
        sa.Column("status", clinic_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_clinics_slug", "clinics", ["slug"], unique=True)

    op.create_table(
        "clinic_locations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address_line1", sa.String(255), nullable=False),
        sa.Column("address_line2", sa.String(255), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("postal_code", sa.String(20), nullable=True),
        sa.Column("country", sa.String(100), server_default="Nepal", nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clinic_locations_clinic_id", "clinic_locations", ["clinic_id"], unique=False)

    op.create_table(
        "clinic_working_hours",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_location_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("opens_at", sa.Time(), nullable=True),
        sa.Column("closes_at", sa.Time(), nullable=True),
        sa.Column("break_starts_at", sa.Time(), nullable=True),
        sa.Column("break_ends_at", sa.Time(), nullable=True),
        sa.Column("is_closed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.ForeignKeyConstraint(["clinic_location_id"], ["clinic_locations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_location_id", "day_of_week", name="uq_location_day"),
        sa.CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_location_day"),
    )
    op.create_index("ix_clinic_working_hours_clinic_location_id", "clinic_working_hours", ["clinic_location_id"], unique=False)

    op.create_table(
        "clinic_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", membership_role, nullable=False),
        sa.Column("status", membership_status, nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clinic_id", "user_id", name="uq_clinic_membership"),
    )
    op.create_index("ix_clinic_memberships_clinic_id", "clinic_memberships", ["clinic_id"], unique=False)
    op.create_index("ix_clinic_memberships_user_id", "clinic_memberships", ["user_id"], unique=False)

    op.create_table(
        "dentist_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("specialization", sa.String(200), nullable=True),
        sa.Column("qualification", sa.String(300), nullable=True),
        sa.Column("license_number", sa.String(100), nullable=True),
        sa.Column("license_verified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("consultation_duration_minutes", sa.Integer(), server_default="30", nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["clinic_id"], ["clinics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_dentist_profiles_clinic_id", "dentist_profiles", ["clinic_id"], unique=False)

    op.add_column(
        "account_invites",
        sa.Column("clinic_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_account_invites_clinic_id", "account_invites", ["clinic_id"], unique=False)
    op.create_foreign_key(
        "fk_account_invites_clinic_id",
        "account_invites",
        "clinics",
        ["clinic_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_account_invites_clinic_id", "account_invites", type_="foreignkey")
    op.drop_index("ix_account_invites_clinic_id", table_name="account_invites")
    op.drop_column("account_invites", "clinic_id")
    op.drop_index("ix_dentist_profiles_clinic_id", table_name="dentist_profiles")
    op.drop_table("dentist_profiles")
    op.drop_index("ix_clinic_memberships_user_id", table_name="clinic_memberships")
    op.drop_index("ix_clinic_memberships_clinic_id", table_name="clinic_memberships")
    op.drop_table("clinic_memberships")
    op.drop_index("ix_clinic_working_hours_clinic_location_id", table_name="clinic_working_hours")
    op.drop_table("clinic_working_hours")
    op.drop_index("ix_clinic_locations_clinic_id", table_name="clinic_locations")
    op.drop_table("clinic_locations")
    op.drop_index("ix_clinics_slug", table_name="clinics")
    op.drop_table("clinics")
    op.execute("DROP TYPE membership_status")
    op.execute("DROP TYPE membership_role")
    op.execute("DROP TYPE clinic_status")
