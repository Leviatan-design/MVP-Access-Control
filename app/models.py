from datetime import datetime

from enum import Enum as PythonEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, PythonEnum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN_CONDOMINIO = "ADMIN_CONDOMINIO"
    ADMIN_CASA = "ADMIN_CASA"
    COHABITANTE = "COHABITANTE"
    VIGILANTE = "VIGILANTE"


class InvitacionEstado(str, PythonEnum):
    PENDIENTE = "PENDIENTE"
    USADO = "USADO"


class Condominio(Base):
    __tablename__ = "condominios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    direccion = Column(String(400), nullable=False)

    propiedades = relationship("Propiedad", back_populates="condominio")


class Propiedad(Base):
    __tablename__ = "propiedades"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id"), nullable=False)
    numero_unidad = Column(String(50), nullable=False)
    es_solvente = Column(Boolean, default=True, nullable=False)

    condominio = relationship("Condominio", back_populates="propiedades")
    usuarios = relationship("Usuario", back_populates="propiedad")
    pases = relationship("Pase", back_populates="propiedad")
    invitaciones = relationship("InvitacionVivienda", back_populates="propiedad")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    propiedad_id = Column(Integer, ForeignKey("propiedades.id"), nullable=True)
    nombre = Column(String(200), nullable=False)
    email = Column(String(320), unique=True, nullable=False, index=True)
    cedula = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(Enum(UserRole, name="user_role", native_enum=True), nullable=False)

    propiedad = relationship("Propiedad", back_populates="usuarios")
    anuncios = relationship("Anuncio", back_populates="autor", cascade="all, delete-orphan")


class Anuncio(Base):
    __tablename__ = "anuncios"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(String(2000), nullable=False)
    precio = Column(Numeric(12, 2), nullable=True)
    autor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.utcnow)
    activo = Column(Boolean, nullable=False, default=True)

    autor = relationship("Usuario", back_populates="anuncios")


class InvitacionVivienda(Base):
    __tablename__ = "invitaciones_vivienda"

    id = Column(Integer, primary_key=True, index=True)
    propiedad_id = Column(Integer, ForeignKey("propiedades.id"), nullable=False, index=True)
    token_invitacion = Column(String(64), unique=True, nullable=False, index=True)
    estado = Column(
        Enum(InvitacionEstado, name="invitacion_estado", native_enum=True),
        nullable=False,
        default=InvitacionEstado.PENDIENTE,
    )
    creado_en = Column(DateTime, nullable=False, default=datetime.utcnow)
    expira_en = Column(DateTime, nullable=False)

    propiedad = relationship("Propiedad", back_populates="invitaciones")


class Pase(Base):
    __tablename__ = "pases"

    id = Column(Integer, primary_key=True, index=True)
    propiedad_id = Column(Integer, ForeignKey("propiedades.id"), nullable=False)
    visitante_nombre = Column(String(200), nullable=False)
    visitante_cedula = Column(String(20), nullable=False)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    estado = Column(String(50), default="PENDIENTE", nullable=False)  # PENDIENTE, DENTRO, FINALIZADO
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    propiedad = relationship("Propiedad", back_populates="pases")
