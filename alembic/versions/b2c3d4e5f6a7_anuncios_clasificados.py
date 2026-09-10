"""add classified condominium announcements

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "anuncios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(length=200), nullable=False),
        sa.Column("descripcion", sa.String(length=2000), nullable=False),
        sa.Column("precio", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("autor_id", sa.Integer(), nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["autor_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_anuncios_id"), "anuncios", ["id"], unique=False)
    op.create_index(op.f("ix_anuncios_autor_id"), "anuncios", ["autor_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_anuncios_autor_id"), table_name="anuncios")
    op.drop_index(op.f("ix_anuncios_id"), table_name="anuncios")
    op.drop_table("anuncios")