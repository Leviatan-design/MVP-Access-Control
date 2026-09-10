from datetime import datetime, timedelta
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    InvitacionResponse,
    UsuarioCreate,
    UsuarioResponse,
)
from app.controller import UsuarioController, PropiedadController
from app.security import hash_password, require_role
from app.models import InvitacionEstado, InvitacionVivienda, Propiedad, UserRole, Usuario

router = APIRouter(prefix="/api/v1/usuarios", tags=["usuarios"])


@router.post("/crear", response_model=UsuarioResponse, status_code=201)
def crear_usuario(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN_CONDOMINIO])),
):
    """
    Crea un nuevo usuario con el rol especificado.
    Solo permite roles válidos: SUPER_ADMIN, ADMIN_CASA, COHABITANTE, VIGILANTE.
    """
    # Verificar que la propiedad existe
    PropiedadController.obtener_propiedad_por_id(db, usuario_data.propiedad_id)

    # Verificar que la cédula no esté duplicada
    if UsuarioController.verificar_usuario_existe(db, usuario_data.cedula):
        raise HTTPException(status_code=400, detail="Ya existe un usuario con esta cédula")
    if db.query(Usuario).filter(Usuario.email == usuario_data.email).first():
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")

    # Validar límite de habitantes si es ADMIN_CASA o COHABITANTE
    if usuario_data.rol in ["ADMIN_CASA", "COHABITANTE"]:
        UsuarioController.validar_limite_habitantes(db, usuario_data.propiedad_id)

    # Crear usuario
    nuevo_usuario = UsuarioController.crear_usuario(
        db=db,
        nombre=usuario_data.nombre,
        email=str(usuario_data.email).lower(),
        cedula=usuario_data.cedula,
        propiedad_id=usuario_data.propiedad_id,
        rol=usuario_data.rol,
        password_hash=hash_password(usuario_data.password),
    )

    return nuevo_usuario


@router.post("/vivienda/generar-invitacion", response_model=InvitacionResponse, status_code=201)
def generar_invitacion(
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(require_role([UserRole.ADMIN_CASA])),
):
    propiedad = (
        db.query(Propiedad)
        .filter(Propiedad.id == usuario_actual.propiedad_id)
        .with_for_update()
        .first()
    )
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    UsuarioController.validar_limite_habitantes(db, propiedad.id, max_habitantes=4)

    token = secrets.token_urlsafe(32)
    invitacion = InvitacionVivienda(
        propiedad_id=propiedad.id,
        token_invitacion=hashlib.sha256(token.encode("utf-8")).hexdigest(),
        estado=InvitacionEstado.PENDIENTE,
        expira_en=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(invitacion)
    db.commit()
    return InvitacionResponse(token_invitacion=token, expira_en=invitacion.expira_en.isoformat())


@router.delete("/vivienda/habitante/{usuario_id}", status_code=204)
def eliminar_habitante(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(require_role([UserRole.ADMIN_CASA])),
):
    if usuario_id == usuario_actual.id:
        raise HTTPException(status_code=400, detail="Un ADMIN_CASA no puede eliminarse a sí mismo")
    habitante = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not habitante:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if habitante.rol != UserRole.COHABITANTE or habitante.propiedad_id != usuario_actual.propiedad_id:
        raise HTTPException(status_code=403, detail="El usuario no es un cohabitante de su propiedad")
    db.delete(habitante)
    db.commit()


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
