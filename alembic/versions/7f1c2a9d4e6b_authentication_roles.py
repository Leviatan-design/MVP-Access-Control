"""add authentication fields and role enum

Revision ID: 7f1c2a9d4e6b
Revises: ce53b854dabb
Create Date: 2026-09-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7f1c2a9d4e6b"
down_revision: Union[str, None] = "ce53b854dabb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    role_enum = sa.Enum(
        "SUPER_ADMIN",
        "ADMIN_CONDOMINIO",
        "ADMIN_CASA",
        "COHABITANTE",
        "VIGILANTE",
        name="user_role",
    )
    role_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("usuarios", sa.Column("email", sa.String(length=320), nullable=True))
    op.add_column("usuarios", sa.Column("password_hash", sa.String(length=255), nullable=True))
    op.execute(
        "UPDATE usuarios SET email = lower(cedula) || '@legacy.flowlogic.local', "
        "password_hash = '$2b$12$C6UzMDM.H6dfI/f/IKcEe.9Rz3D0s7eYxM0JmYQ2E8h6k6m2J8M1e' "
        "WHERE email IS NULL OR password_hash IS NULL"
    )
    op.alter_column("usuarios", "email", nullable=False)
    op.alter_column("usuarios", "password_hash", nullable=False)
    op.create_index(op.f("ix_usuarios_email"), "usuarios", ["email"], unique=True)

    op.drop_constraint("check_usuarios_rol", "usuarios", type_="check")
    op.alter_column(
        "usuarios",
        "rol",
        existing_type=sa.String(length=50),
        type_=role_enum,
        postgresql_using="rol::text::user_role",
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "usuarios",
        "rol",
        existing_type=sa.Enum(name="user_role"),
        type_=sa.String(length=50),
        postgresql_using="rol::text",
        existing_nullable=False,
    )
    op.create_check_constraint(
        "check_usuarios_rol",
        "usuarios",
        "rol IN ('SUPER_ADMIN', 'ADMIN_CASA', 'COHABITANTE', 'VIGILANTE')",
    )
    op.drop_index(op.f("ix_usuarios_email"), table_name="usuarios")
    op.drop_column("usuarios", "password_hash")
    op.drop_column("usuarios", "email")
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)