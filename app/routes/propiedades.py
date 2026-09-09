from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.controller import PropiedadController
from app.models import Propiedad

router = APIRouter(prefix="/api/v1/propiedades", tags=["propiedades"])


@router.get("/{propiedad_id}")
def obtener_propiedad(propiedad_id: int, db: Session = Depends(get_db)):
    """Obtiene una propiedad por su ID con información completa."""
    propiedad = (
        db.query(Propiedad)
        .options(joinedload(Propiedad.condominio))
        .filter(Propiedad.id == propiedad_id)
        .first()
    )

    if not propiedad:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    return {
        "id": propiedad.id,
        "numero_unidad": propiedad.numero_unidad,
        "es_solvente": propiedad.es_solvente,
        "condominio_id": propiedad.condominio_id,
        "condominio_nombre": propiedad.condominio.nombre if propiedad.condominio else None
    }


@router.get("/")
def obtener_todas_propiedades(db: Session = Depends(get_db)):
    """Obtiene todas las propiedades."""
    propiedades = (
        db.query(Propiedad)
        .options(joinedload(Propiedad.condominio))
        .all()
    )

    return [
        {
            "id": p.id,
            "numero_unidad": p.numero_unidad,
            "es_solvente": p.es_solvente,
            "condominio_id": p.condominio_id,
            "condominio_nombre": p.condominio.nombre if p.condominio else None
        }
        for p in propiedades
    ]
