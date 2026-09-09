from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CoHabitanteInvitacion,
    CoHabitanteResponse,
    UsuarioCreate,
    UsuarioResponse,
)
from app.controller import UsuarioController, PropiedadController

router = APIRouter(prefix="/api/v1/usuarios", tags=["usuarios"])


@router.post("/crear", response_model=UsuarioResponse, status_code=201)
def crear_usuario(usuario_data: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo usuario con el rol especificado.
    Solo permite roles válidos: SUPER_ADMIN, ADMIN_CASA, COHABITANTE, VIGILANTE.
    """
    # Verificar que la propiedad existe
    PropiedadController.obtener_propiedad_por_id(db, usuario_data.propiedad_id)

    # Verificar que la cédula no esté duplicada
    if UsuarioController.verificar_usuario_existe(db, usuario_data.cedula):
        raise HTTPException(status_code=400, detail="Ya existe un usuario con esta cédula")

    # Validar límite de habitantes si es ADMIN_CASA o COHABITANTE
    if usuario_data.rol in ["ADMIN_CASA", "COHABITANTE"]:
        UsuarioController.validar_limite_habitantes(db, usuario_data.propiedad_id)

    # Crear usuario
    nuevo_usuario = UsuarioController.crear_usuario(
        db=db,
        nombre=usuario_data.nombre,
        cedula=usuario_data.cedula,
        propiedad_id=usuario_data.propiedad_id,
        rol=usuario_data.rol
    )

    return nuevo_usuario


@router.post("/vivienda/invitar", response_model=CoHabitanteResponse, status_code=201)
def invitar_cohabitante(
    invitacion: CoHabitanteInvitacion,
    propiedad_id: int,
    usuario_autorizador_id: int,
    db: Session = Depends(get_db)
):
    """
    Endpoint para que un ADMIN_CASA invite/registre un nuevo COHABITANTE
    bajo su misma propiedad.

    Reglas:
    - El usuario autorizador debe tener rol ADMIN_CASA
    - El nuevo usuario se crea automáticamente con rol COHABITANTE
    - Máximo 4 habitantes por propiedad (ADMIN_CASA + COHABITANTES)
    """
    # Verificar que el usuario autorizador existe y es ADMIN_CASA
    usuario_autorizador = UsuarioController.obtener_usuario_por_id(db, usuario_autorizador_id)
    if usuario_autorizador.rol != "ADMIN_CASA":
        raise HTTPException(
            status_code=403,
            detail="Solo usuarios con rol ADMIN_CASA pueden invitar co-habitantes"
        )

    # Verificar que el usuario autorizador pertenece a la propiedad especificada
    if usuario_autorizador.propiedad_id != propiedad_id:
        raise HTTPException(
            status_code=403,
            detail="El usuario autorizador no pertenece a la propiedad especificada"
        )

    # Verificar que la propiedad existe
    PropiedadController.obtener_propiedad_por_id(db, propiedad_id)

    # Verificar que la cédula no esté duplicada
    if UsuarioController.verificar_usuario_existe(db, invitacion.cedula):
        raise HTTPException(status_code=400, detail="Ya existe un usuario con esta cédula")

    # Validar límite de habitantes (máximo 4)
    UsuarioController.validar_limite_habitantes(db, propiedad_id, max_habitantes=4)

    # Crear el nuevo co-habitante
    nuevo_cohabitante = UsuarioController.crear_usuario(
        db=db,
        nombre=invitacion.nombre,
        cedula=invitacion.cedula,
        propiedad_id=propiedad_id,
        rol="COHABITANTE"
    )

    return nuevo_cohabitante


@router.get("/vivienda/{propiedad_id}/habitantes", response_model=list[UsuarioResponse])
def obtener_habitantes_por_propiedad(propiedad_id: int, db: Session = Depends(get_db)):
    """
    Obtiene todos los habitantes (ADMIN_CASA + COHABITANTE) de una propiedad.
    """
    # Verificar que la propiedad existe
    PropiedadController.obtener_propiedad_por_id(db, propiedad_id)

    usuarios = UsuarioController.obtener_usuarios_por_propiedad(db, propiedad_id)
    # Filtrar solo ADMIN_CASA y COHABITANTE
    habitantes = [u for u in usuarios if u.rol in ["ADMIN_CASA", "COHABITANTE"]]
    return habitantes


@router.get("/vivienda/{propiedad_id}/conteo")
def contar_habitantes(propiedad_id: int, db: Session = Depends(get_db)):
    """
    Obtiene el conteo actual de habitantes en una propiedad.
    """
    # Verificar que la propiedad existe
    PropiedadController.obtener_propiedad_por_id(db, propiedad_id)

    conteo = UsuarioController.contar_habitantes_por_propiedad(db, propiedad_id)
    return {
        "propiedad_id": propiedad_id,
        "conteo_habitantes": conteo,
        "limite_maximo": 4,
        "cupos_disponibles": max(0, 4 - conteo)
    }


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Obtiene un usuario por su ID."""
    return UsuarioController.obtener_usuario_por_id(db, usuario_id)


@router.get("/cedula/{cedula}", response_model=UsuarioResponse)
def obtener_usuario_por_cedula(cedula: str, db: Session = Depends(get_db)):
    """Obtiene un usuario por su cédula."""
    return UsuarioController.obtener_usuario_por_cedula(db, cedula)
