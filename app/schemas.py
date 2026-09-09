from pydantic import BaseModel, Field, validator


# Valid roles constant
VALID_ROLES = {"SUPER_ADMIN", "ADMIN_CASA", "COHABITANTE", "VIGILANTE"}


class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    cedula: str = Field(..., min_length=1, max_length=20)
    propiedad_id: int
    rol: str = Field(..., description="Rol del usuario")

    @validator("rol")
    def validate_role(cls, v):
        if v not in VALID_ROLES:
            raise ValueError(f"Rol inválido. Roles válidos: {', '.join(VALID_ROLES)}")
        return v


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    cedula: str
    propiedad_id: int
    rol: str

    class Config:
        from_attributes = True


class CoHabitanteInvitacion(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    cedula: str = Field(..., min_length=1, max_length=20)


class CoHabitanteResponse(BaseModel):
    id: int
    nombre: str
    cedula: str
    propiedad_id: int
    rol: str

    class Config:
        from_attributes = True


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


class MorosidadCSVResponse(BaseModel):
    message: str
    propiedades_actualizadas: int
    errores: list[str] = Field(default_factory=list)


class PropiedadMorosidadUpdate(BaseModel):
    numero_unidad: str
    es_solvente: bool


class ErrorDetail(BaseModel):
    detail: str
