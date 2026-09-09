from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


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


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    propiedad_id = Column(Integer, ForeignKey("propiedades.id"), nullable=True)
    nombre = Column(String(200), nullable=False)
    cedula = Column(String(20), unique=True, nullable=False, index=True)
    rol = Column(String(50), nullable=False)  # SUPER_ADMIN, ADMIN_CASA, COHABITANTE, VIGILANTE

    propiedad = relationship("Propiedad", back_populates="usuarios")


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
