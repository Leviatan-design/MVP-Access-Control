from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, validator


# Valid roles constant
VALID_ROLES = {"SUPER_ADMIN", "ADMIN_CONDOMINIO", "ADMIN_CASA", "COHABITANTE", "VIGILANTE"}


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    cedula: str = Field(..., min_length=1, max_length=20)
    propiedad_id: Optional[int]
    rol: str = Field(..., description="Rol del usuario")
    password: str = Field(..., min_length=12, max_length=128)

    @validator("rol")
    def validate_role(cls, v):
        if v not in VALID_ROLES:
            raise ValueError(f"Rol inválido. Roles válidos: {', '.join(VALID_ROLES)}")
        return v


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    cedula: str
    propiedad_id: Optional[int]
    rol: str

    class Config:
        from_attributes = True


class CoHabitanteInvitacion(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    cedula: str = Field(..., min_length=1, max_length=20)
    password: str = Field(..., min_length=12, max_length=128)


class InvitacionRegistro(BaseModel):
    token_invitacion: str = Field(..., min_length=1, max_length=128)
    nombre: str = Field(..., min_length=1, max_length=200)
    cedula: str = Field(..., min_length=1, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)


class InvitacionResponse(BaseModel):
    token_invitacion: str
    expira_en: str


class CoHabitanteResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    cedula: str
    propiedad_id: int
    rol: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class PaseCreate(BaseModel):
    propiedad_id: int = Field(..., description="ID de la propiedad")
    visitante_nombre: str = Field(..., min_length=1, max_length=200)
    visitante_cedula: str = Field(..., min_length=1, max_length=20)
    usuario_creador_id: int = Field(..., description="ID del usuario que crea el pase")


class PaseResponse(BaseModel):
    id: int
    propiedad_id: int
    visitante_nombre: str
    visitante_cedula: str
    codigo: str
    estado: str
    created_at: str

    class Config:
        from_attributes = True


class OfflineSyncAction(BaseModel):
    pase_id: int = Field(..., gt=0)
    accion: Literal["entrada", "salida"]
    timestamp: datetime


class OfflineSyncResponse(BaseModel):
    synced_ids: list[int] = Field(default_factory=list)


class MorosidadCSVResponse(BaseModel):
    message: str
    propiedades_actualizadas: int
    errores: list[str] = Field(default_factory=list)


class PropiedadMorosidadUpdate(BaseModel):
    numero_unidad: str
    es_solvente: bool


class AnuncioCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200)
    descripcion: str = Field(..., min_length=1, max_length=2000)
    precio: Optional[Decimal] = Field(default=None, ge=0, max_digits=12, decimal_places=2)


class AnuncioResponse(BaseModel):
    id: int
    titulo: str
    descripcion: str
    precio: Optional[Decimal]
    autor_id: int
    fecha_creacion: datetime
    activo: bool

    class Config:
        from_attributes = True


class ErrorDetail(BaseModel):
    detail: str
