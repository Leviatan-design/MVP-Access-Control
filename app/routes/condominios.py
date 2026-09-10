from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import MorosidadCSVResponse
from app.controller import MorosidadController
from app.models import UserRole, Usuario
from app.security import require_role

router = APIRouter(prefix="/api/v1/condominio", tags=["condominios"])


@router.post("/morosidad/cargar-csv", response_model=MorosidadCSVResponse)
async def cargar_csv_morosidad(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN_CONDOMINIO]))
):
    """
    Endpoint protegido para SUPER_ADMIN para cargar archivo CSV de morosidad.

    El CSV debe tener el formato:
    numero_unidad,es_solvente
    A-12,true
    B-301,false
    SOL-05,true

    Valores aceptados para es_solvente:
    - true/false
    - 1/0
    - si/no
    - yes/no
    - y/n
    """
    # Validar que sea un archivo CSV
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un CSV"
        )

    # Leer el contenido del archivo
    contenido = await file.read()
    contenido_str = contenido.decode('utf-8')

    # Procesar el CSV
    resultado = MorosidadController.procesar_csv_morosidad(db, contenido_str)

    return MorosidadCSVResponse(
        message=f"Procesamiento completado. {resultado['propiedades_actualizadas']} propiedades actualizadas.",
        propiedades_actualizadas=resultado["propiedades_actualizadas"],
        errores=resultado["errores"]
    )


@router.get("/morosidad/propiedades")
def obtener_propiedades_morosidad(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_role([UserRole.SUPER_ADMIN, UserRole.ADMIN_CONDOMINIO]))
):
    """
    Obtiene el estado de morosidad de todas las propiedades.
    Solo accesible para SUPER_ADMIN.
    """
    from app.models import Propiedad
    from sqlalchemy.orm import joinedload

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
