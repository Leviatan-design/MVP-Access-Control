"""initial migration

Revision ID: ce53b854dabb
Revises: 
Create Date: 2026-09-09 16:59:11.279374

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'ce53b854dabb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create condominios table
    op.create_table(
        'condominios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=200), nullable=False),
        sa.Column('direccion', sa.String(length=400), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condominios_id'), 'condominios', ['id'], unique=False)

    # Create propiedades table
    op.create_table(
        'propiedades',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('condominio_id', sa.Integer(), nullable=False),
        sa.Column('numero_unidad', sa.String(length=50), nullable=False),
        sa.Column('es_solvente', sa.Boolean(), nullable=False, server_default='true'),
        sa.ForeignKeyConstraint(['condominio_id'], ['condominios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_propiedades_id'), 'propiedades', ['id'], unique=False)

    # Create usuarios table
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('propiedad_id', sa.Integer(), nullable=True),
        sa.Column('nombre', sa.String(length=200), nullable=False),
        sa.Column('cedula', sa.String(length=20), nullable=False),
        sa.Column('rol', sa.String(length=50), nullable=False),
        sa.CheckConstraint("rol IN ('SUPER_ADMIN', 'ADMIN_CASA', 'COHABITANTE', 'VIGILANTE')", name='check_usuarios_rol'),
        sa.ForeignKeyConstraint(['propiedad_id'], ['propiedades.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('cedula')
    )
    op.create_index(op.f('ix_usuarios_cedula'), 'usuarios', ['cedula'], unique=False)
    op.create_index(op.f('ix_usuarios_id'), 'usuarios', ['id'], unique=False)

    # Create pases table
    op.create_table(
        'pases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('propiedad_id', sa.Integer(), nullable=False),
        sa.Column('visitante_nombre', sa.String(length=200), nullable=False),
        sa.Column('visitante_cedula', sa.String(length=20), nullable=False),
        sa.Column('codigo', sa.String(length=20), nullable=False),
        sa.Column('estado', sa.String(length=50), nullable=False, server_default='PENDIENTE'),
        sa.CheckConstraint("estado IN ('PENDIENTE', 'DENTRO', 'FINALIZADO')", name='check_pases_estado'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['propiedad_id'], ['propiedades.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo')
    )
    op.create_index(op.f('ix_pases_codigo'), 'pases', ['codigo'], unique=False)
    op.create_index(op.f('ix_pases_id'), 'pases', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_index(op.f('ix_pases_id'), table_name='pases')
    op.drop_index(op.f('ix_pases_codigo'), table_name='pases')
    op.drop_table('pases')

    op.drop_index(op.f('ix_usuarios_id'), table_name='usuarios')
    op.drop_index(op.f('ix_usuarios_cedula'), table_name='usuarios')
    op.drop_table('usuarios')

    op.drop_index(op.f('ix_propiedades_id'), table_name='propiedades')
    op.drop_table('propiedades')

    op.drop_index(op.f('ix_condominios_id'), table_name='condominios')
    op.drop_table('condominios')
