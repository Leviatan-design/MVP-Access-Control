from datetime import datetime
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import InvitacionEstado, InvitacionVivienda, Propiedad, UserRole, Usuario
from app.schemas import InvitacionRegistro, TokenResponse, UsuarioResponse
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username.strip().lower()).first()
    if not usuario or not verify_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(usuario), token_type="bearer")


@router.post("/register/cohabitante", response_model=UsuarioResponse, status_code=201)
def registrar_cohabitante(registro: InvitacionRegistro, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(registro.token_invitacion.encode("utf-8")).hexdigest()
    invitacion = (
        db.query(InvitacionVivienda)
        .filter(InvitacionVivienda.token_invitacion == token_hash)
        .with_for_update()
        .first()
    )
    if (
        not invitacion
        or invitacion.estado != InvitacionEstado.PENDIENTE
        or invitacion.expira_en <= datetime.utcnow()
    ):
        raise HTTPException(status_code=400, detail="La invitación no es válida, está usada o expiró")

    propiedad = (
        db.query(Propiedad)
        .filter(Propiedad.id == invitacion.propiedad_id)
        .with_for_update()
        .first()
    )
    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")
    habitantes = (
        db.query(Usuario.id)
        .filter(
            Usuario.propiedad_id == propiedad.id,
            Usuario.rol.in_([UserRole.ADMIN_CASA, UserRole.COHABITANTE]),
        )
        .scalar()
    )
    if habitantes >= 4:
        raise HTTPException(status_code=400, detail="Límite máximo de 4 habitantes alcanzado para esta propiedad")
    if db.query(Usuario).filter(Usuario.cedula == registro.cedula).first():
        raise HTTPException(status_code=400, detail="Ya existe un usuario con esta cédula")
    email = str(registro.email).lower()
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este email")

    usuario = Usuario(
        nombre=registro.nombre,
        email=email,
        cedula=registro.cedula,
        password_hash=hash_password(registro.password),
        propiedad_id=propiedad.id,
        rol=UserRole.COHABITANTE,
    )
    db.add(usuario)
    invitacion.estado = InvitacionEstado.USADO
    db.commit()
    db.refresh(usuario)
    return usuario