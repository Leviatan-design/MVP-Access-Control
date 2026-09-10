from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.schemas import OfflineSyncAction, OfflineSyncResponse, PaseCreate, PaseResponse
from app.controller import UsuarioController, PropiedadController, MorosidadController
from app.models import Pase, Usuario
from app.seed import generate_code

router = APIRouter(prefix="/api/v1/pases", tags=["pases"])


@router.post("/crear", response_model=PaseResponse, status_code=201)
def crear_pase(pase_data: PaseCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo pase para un visitante.

    Validaciones:
    - La propiedad debe existir
    - El usuario creador debe existir
    - La propiedad debe ser solvente (es_solvente == True)
    - No puede haber cédulas duplicadas en el mismo día (opcional)
    """
    # Verificar que la propiedad existe
    PropiedadController.obtener_propiedad_por_id(db, pase_data.propiedad_id)

    # Verificar que el usuario creador existe
    usuario_creador = UsuarioController.obtener_usuario_por_id(db, pase_data.usuario_creador_id)

    # VALIDACIÓN FINANCIERA: Verificar que la propiedad sea solvente
    if not MorosidadController.verificar_solvencia_propiedad(db, pase_data.propiedad_id):
        raise HTTPException(
            status_code=403,
            detail="Generación de pases bloqueada por saldo pendiente en la unidad"
        )

    # Generar código único para el pase
    codigo = generate_code(db)

    # Crear el pase
    nuevo_pase = Pase(
        propiedad_id=pase_data.propiedad_id,
        visitante_nombre=pase_data.visitante_nombre,
        visitante_cedula=pase_data.visitante_cedula,
        codigo=codigo,
        estado="PENDIENTE"
    )

    db.add(nuevo_pase)
    db.commit()
    db.refresh(nuevo_pase)

    return nuevo_pase


@router.get("/buscar/{codigo}", response_model=PaseResponse)
def buscar_pase_por_codigo(codigo: str, db: Session = Depends(get_db)):
    """
    Busca un pase por su código corto (ej: ACC-902).
    Solo devuelve pases con estado PENDIENTE.
    """
    normalized = codigo.strip().upper()
    pase = (
        db.query(Pase)
        .options(joinedload(Pase.propiedad))
        .filter(Pase.codigo == normalized, Pase.estado == "PENDIENTE")
        .first()
    )

    if not pase:
        raise HTTPException(
            status_code=404,
            detail="Pase no encontrado o no está en estado PENDIENTE"
        )

    return pase


@router.patch("/{pase_id}/entrada", response_model=PaseResponse)
def registrar_entrada(pase_id: int, db: Session = Depends(get_db)):
    """
    Cambia el estado del pase de PENDIENTE a DENTRO
    y registra la estampa de tiempo de entrada.
    """
    pase = (
        db.query(Pase)
        .options(joinedload(Pase.propiedad))
        .filter(Pase.id == pase_id)
        .first()
    )

    if not pase:
        raise HTTPException(status_code=404, detail="Pase no encontrado")

    if pase.estado != "PENDIENTE":
        raise HTTPException(
            status_code=400,
            detail=f"No se puede registrar entrada. Estado actual: {pase.estado}"
        )

    pase.estado = "DENTRO"
    # Nota: Podríamos agregar un campo entrada_at si lo necesitamos en el modelo
    db.commit()
    db.refresh(pase)

    return pase


@router.patch("/{pase_id}/salida", response_model=PaseResponse)
def registrar_salida(pase_id: int, db: Session = Depends(get_db)):
    """
    Cambia el estado del pase de DENTRO a FINALIZADO
    y registra la hora de salida.
    """
    pase = (
        db.query(Pase)
        .options(joinedload(Pase.propiedad))
        .filter(Pase.id == pase_id)
        .first()
    )

    if not pase:
        raise HTTPException(status_code=404, detail="Pase no encontrado")

    if pase.estado != "DENTRO":
        raise HTTPException(
            status_code=400,
            detail=f"No se puede registrar salida. Estado actual: {pase.estado}"
        )

    pase.estado = "FINALIZADO"
    # Nota: Podríamos agregar un campo salida_at si lo necesitamos en el modelo
    db.commit()
    db.refresh(pase)

    return pase


@router.post("/sync-offline", response_model=OfflineSyncResponse)
def sincronizar_pases_offline(
    acciones: list[OfflineSyncAction],
    db: Session = Depends(get_db),
):
    """Aplica las acciones acumuladas por el panel de garita en una transacción."""
    synced_ids = []

    with db.begin():
        for accion in acciones:
            pase = (
                db.query(Pase)
                .filter(Pase.id == accion.pase_id)
                .with_for_update()
                .first()
            )

            if not pase:
                raise HTTPException(status_code=404, detail=f"Pase no encontrado: {accion.pase_id}")

            expected_state = "PENDIENTE" if accion.accion == "entrada" else "DENTRO"
            applied_state = "DENTRO" if accion.accion == "entrada" else "FINALIZADO"
            if pase.estado == expected_state:
                pase.estado = applied_state
            elif pase.estado != applied_state:
                raise HTTPException(
                    status_code=400,
                    detail=f"No se puede registrar {accion.accion} para el pase {accion.pase_id}. Estado actual: {pase.estado}",
                )

            if accion.pase_id not in synced_ids:
                synced_ids.append(accion.pase_id)

    return OfflineSyncResponse(synced_ids=synced_ids)


@router.get("/propiedad/{propiedad_id}", response_model=list[PaseResponse])
def obtener_pases_por_propiedad(propiedad_id: int, db: Session = Depends(get_db)):
    """Obtiene todos los pases asociados a una propiedad."""
    # Verificar que la propiedad existe
    PropiedadController.obtener_propiedad_por_id(db, propiedad_id)

    pases = (
        db.query(Pase)
        .options(joinedload(Pase.propiedad))
        .filter(Pase.propiedad_id == propiedad_id)
        .order_by(Pase.created_at.desc())
        .all()
    )

    return pases


@router.get("/activos", response_model=list[PaseResponse])
def obtener_pases_activos(db: Session = Depends(get_db)):
    """Obtiene todos los pases con estado DENTRO (visitantes activos)."""
    pases = (
        db.query(Pase)
        .options(joinedload(Pase.propiedad))
        .filter(Pase.estado == "DENTRO")
        .order_by(Pase.created_at.desc())
        .all()
    )

    return pases


@router.get("/{pase_id}", response_model=PaseResponse)
def obtener_pase(pase_id: int, db: Session = Depends(get_db)):
    """Obtiene un pase por su ID."""
    pase = (
        db.query(Pase)
        .options(joinedload(Pase.propiedad))
        .filter(Pase.id == pase_id)
        .first()
    )

    if not pase:
        raise HTTPException(status_code=404, detail="Pase no encontrado")

    return pase


@router.get("/codigo/{codigo}", response_model=PaseResponse)
def obtener_pase_por_codigo(codigo: str, db: Session = Depends(get_db)):
    """Obtiene un pase por su código (sin filtro de estado)."""
    normalized = codigo.strip().upper()
    pase = (
        db.query(Pase)
        .options(joinedload(Pase.propiedad))
        .filter(Pase.codigo == normalized)
        .first()
    )

    if not pase:
        raise HTTPException(status_code=404, detail="Pase no encontrado")

    return pase
