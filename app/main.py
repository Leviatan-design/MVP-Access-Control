import os
from datetime import datetime, time
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal, get_db
from app.models import Condominio, Propiedad, Usuario, Pase
from app.routes.usuarios import router as usuarios_router
from app.routes.pases import router as pases_router
from app.routes.condominios import router as condominios_router
from app.routes.propiedades import router as propiedades_router
from app.seed import seed_database

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Access Pass - FlowLogic", version="2.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# Incluir nuevas rutas de gestión de usuarios
app.include_router(usuarios_router)
app.include_router(pases_router)
app.include_router(condominios_router)
app.include_router(propiedades_router)


def pase_to_dict(pase: Pase) -> dict:
    """Convierte un objeto Pase a diccionario para respuesta JSON."""
    return {
        "id": pase.id,
        "propiedad_id": pase.propiedad_id,
        "visitante_nombre": pase.visitante_nombre,
        "visitante_cedula": pase.visitante_cedula,
        "codigo": pase.codigo,
        "estado": pase.estado,
        "created_at": pase.created_at.isoformat() if pase.created_at else None,
    }


def today_range() -> tuple[datetime, datetime]:
    now = datetime.now()
    start = datetime.combine(now.date(), time.min)
    end = datetime.combine(now.date(), time.max)
    return start, end


def get_pase_or_404(db: Session, pase_id: int) -> Pase:
    """Obtiene un pase por ID o lanza 404."""
    pase = (
        db.query(Pase)
        .options(joinedload(Pase.propiedad))
        .filter(Pase.id == pase_id)
        .first()
    )
    if not pase:
        raise HTTPException(status_code=404, detail="Pase no encontrado")
    return pase


@app.on_event("startup")
def on_startup() -> None:
    # No crear tablas automáticamente - usar Alembic para migraciones
    # Solo sembrar datos si es necesario
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "access-control"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/guard", response_class=HTMLResponse)
def guard_panel(request: Request) -> HTMLResponse:
    """Panel de vigilante optimizado para tablets."""
    return templates.TemplateResponse("guard.html", {"request": request})


@app.get("/owner", response_class=HTMLResponse)
def owner_panel(request: Request) -> HTMLResponse:
    """Panel de propietario con gestión de vivienda y pases."""
    return templates.TemplateResponse("owner.html", {"request": request})


# Nuevos endpoints para Pases (adaptación del sistema anterior)
@app.get("/api/pases/today")
def api_pases_today(db: Session = Depends(get_db)) -> JSONResponse:
    """Obtiene pases creados hoy."""
    start, end = today_range()
    pases = (
        db.query(Pase)
        .options(joinedload(Pase.propiedad))
        .filter(
            Pase.created_at >= start,
            Pase.created_at <= end,
            Pase.estado == "PENDIENTE"
        )
        .order_by(Pase.created_at.asc())
        .all()
    )
    return JSONResponse([pase_to_dict(p) for p in pases])


@app.get("/api/pases/inside")
def api_pases_inside(db: Session = Depends(get_db)) -> JSONResponse:
    """Obtiene pases con estado DENTRO."""
    pases = (
        db.query(Pase)
        .options(joinedload(Pase.propiedad))
        .filter(Pase.estado == "DENTRO")
        .order_by(Pase.created_at.desc())
        .all()
    )
    return JSONResponse([pase_to_dict(p) for p in pases])


@app.get("/api/pases/search")
def api_search_pase(codigo: str = Query(...), db: Session = Depends(get_db)) -> JSONResponse:
    """Busca un pase por código."""
    normalized = codigo.strip().upper()
    pase = (
        db.query(Pase)
        .options(joinedload(Pase.propiedad))
        .filter(Pase.codigo == normalized)
        .first()
    )
    if not pase:
        raise HTTPException(status_code=404, detail="Código no encontrado")
    return JSONResponse(pase_to_dict(pase))


@app.post("/api/pases/{pase_id}/entry")
def api_mark_entry(pase_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    """Marca un pase como DENTRO."""
    pase = get_pase_or_404(db, pase_id)
    if pase.estado == "FINALIZADO":
        raise HTTPException(status_code=400, detail="El pase ya fue finalizado")
    if pase.estado == "DENTRO":
        raise HTTPException(status_code=400, detail="El pase ya está marcado como DENTRO")

    pase.estado = "DENTRO"
    db.commit()
    db.refresh(pase)
    return JSONResponse(pase_to_dict(pase))


@app.post("/api/pases/{pase_id}/exit")
def api_mark_exit(pase_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    """Marca un pase como FINALIZADO."""
    pase = get_pase_or_404(db, pase_id)
    if pase.estado != "DENTRO":
        raise HTTPException(status_code=400, detail="El pase no está marcado como DENTRO")

    pase.estado = "FINALIZADO"
    db.commit()
    db.refresh(pase)
    return JSONResponse(pase_to_dict(pase))


# Endpoint de creación de pases con validación financiera
@app.post("/api/pases/crear")
def api_crear_pase(
    propiedad_id: int,
    visitante_nombre: str,
    visitante_cedula: str,
    usuario_creador_id: int,
    db: Session = Depends(get_db)
) -> JSONResponse:
    """
    Crea un nuevo pase con validación financiera.
    Verifica que la propiedad sea solvente antes de crear el pase.
    """
    from app.controller import MorosidadController, PropiedadController

    # Verificar que la propiedad existe
    PropiedadController.obtener_propiedad_por_id(db, propiedad_id)

    # VALIDACIÓN FINANCIERA: Verificar que la propiedad sea solvente
    if not MorosidadController.verificar_solvencia_propiedad(db, propiedad_id):
        raise HTTPException(
            status_code=403,
            detail="Generación de pases bloqueada por saldo pendiente en la unidad"
        )

    # Generar código único
    from app.seed import generate_code
    codigo = generate_code(db)

    # Crear el pase
    nuevo_pase = Pase(
        propiedad_id=propiedad_id,
        visitante_nombre=visitante_nombre,
        visitante_cedula=visitante_cedula,
        codigo=codigo,
        estado="PENDIENTE"
    )

    db.add(nuevo_pase)
    db.commit()
    db.refresh(nuevo_pase)

    return JSONResponse(pase_to_dict(nuevo_pase))


def run() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
