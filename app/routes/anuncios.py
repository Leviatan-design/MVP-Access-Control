from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Anuncio, Propiedad, UserRole, Usuario
from app.schemas import AnuncioCreate, AnuncioResponse
from app.security import get_current_user, require_role

router = APIRouter(prefix="/api/v1/anuncios", tags=["anuncios"])


@router.post("", response_model=AnuncioResponse, status_code=status.HTTP_201_CREATED)
def crear_anuncio(
    anuncio_data: AnuncioCreate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(
        require_role([UserRole.ADMIN_CASA, UserRole.COHABITANTE])
    ),
):
    propiedad = (
        db.query(Propiedad)
        .filter(Propiedad.id == usuario_actual.propiedad_id)
        .first()
    )
    if not propiedad or not propiedad.es_solvente:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operación denegada: La propiedad presenta deudas pendientes",
        )

    anuncio = Anuncio(
        titulo=anuncio_data.titulo,
        descripcion=anuncio_data.descripcion,
        precio=anuncio_data.precio,
        autor_id=usuario_actual.id,
    )
    db.add(anuncio)
    db.commit()
    db.refresh(anuncio)
    return anuncio


@router.get("", response_model=list[AnuncioResponse])
def listar_anuncios(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
):
    return (
        db.query(Anuncio)
        .filter(Anuncio.activo.is_(True))
        .order_by(Anuncio.fecha_creacion.desc())
        .all()
    )


@router.delete("/{anuncio_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_anuncio(
    anuncio_id: int,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    anuncio = db.query(Anuncio).filter(Anuncio.id == anuncio_id).first()
    if not anuncio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anuncio no encontrado")

    roles_moderadores = {UserRole.SUPER_ADMIN, UserRole.ADMIN_CONDOMINIO}
    es_moderador = usuario_actual.rol in roles_moderadores
    if anuncio.autor_id != usuario_actual.id and not es_moderador:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este anuncio",
        )

    db.delete(anuncio)
    db.commit()