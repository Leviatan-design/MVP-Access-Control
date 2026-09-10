"""add one-time housing invitations

Revision ID: a1b2c3d4e5f6
Revises: 7f1c2a9d4e6b
Create Date: 2026-09-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "7f1c2a9d4e6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    invitacion_estado = sa.Enum("PENDIENTE", "USADO", name="invitacion_estado")
    invitacion_estado.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "invitaciones_vivienda",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("propiedad_id", sa.Integer(), nullable=False),
        sa.Column("token_invitacion", sa.String(length=64), nullable=False),
        sa.Column("estado", invitacion_estado, nullable=False),
        sa.Column("creado_en", sa.DateTime(), nullable=False),
        sa.Column("expira_en", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["propiedad_id"], ["propiedades.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_invitacion"),
    )
    op.create_index(op.f("ix_invitaciones_vivienda_id"), "invitaciones_vivienda", ["id"], unique=False)
    op.create_index(op.f("ix_invitaciones_vivienda_propiedad_id"), "invitaciones_vivienda", ["propiedad_id"], unique=False)
    op.create_index(op.f("ix_invitaciones_vivienda_token_invitacion"), "invitaciones_vivienda", ["token_invitacion"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_invitaciones_vivienda_token_invitacion"), table_name="invitaciones_vivienda")
    op.drop_index(op.f("ix_invitaciones_vivienda_propiedad_id"), table_name="invitaciones_vivienda")
    op.drop_index(op.f("ix_invitaciones_vivienda_id"), table_name="invitaciones_vivienda")
    op.drop_table("invitaciones_vivienda")
    sa.Enum(name="invitacion_estado").drop(op.get_bind(), checkfirst=True)