import os
from datetime import datetime, time
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import Base, SessionLocal, engine, get_db
from app.models import AccessType, Property, Visit, VisitStatus
from app.seed import generate_code, seed_database

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Control de Acceso Residencial", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def visit_to_dict(visit: Visit) -> dict:
    return {
        "id": visit.id,
        "property_id": visit.property_id,
        "property_name": visit.property.name if visit.property else "",
        "property_unit": visit.property.unit if visit.property else "",
        "owner_name": visit.property.owner_name if visit.property else "",
        "visitor_name": visit.visitor_name,
        "visitor_id": visit.visitor_id,
        "access_type": visit.access_type.value,
        "access_type_label": "Peatonal" if visit.access_type == AccessType.PEATONAL else "Vehicular",
        "scheduled_at": visit.scheduled_at.isoformat(),
        "scheduled_at_display": visit.scheduled_at.strftime("%d/%m/%Y %H:%M"),
        "code": visit.code,
        "status": visit.status.value,
        "status_label": {
            VisitStatus.SCHEDULED: "Agendada",
            VisitStatus.INSIDE: "Dentro",
            VisitStatus.EXITED: "Salió",
            VisitStatus.CANCELLED: "Cancelada",
        }[visit.status],
        "entry_at": visit.entry_at.isoformat() if visit.entry_at else None,
        "entry_at_display": visit.entry_at.strftime("%d/%m/%Y %H:%M") if visit.entry_at else None,
        "exit_at": visit.exit_at.isoformat() if visit.exit_at else None,
        "exit_at_display": visit.exit_at.strftime("%d/%m/%Y %H:%M") if visit.exit_at else None,
    }


def today_range() -> tuple[datetime, datetime]:
    now = datetime.now()
    start = datetime.combine(now.date(), time.min)
    end = datetime.combine(now.date(), time.max)
    return start, end


def get_visit_or_404(db: Session, visit_id: int) -> Visit:
    visit = (
        db.query(Visit)
        .options(joinedload(Visit.property))
        .filter(Visit.id == visit_id)
        .first()
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Visita no encontrada")
    return visit


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
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


@app.get("/owner", response_class=HTMLResponse)
def owner_panel(
    request: Request,
    property_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    properties = db.query(Property).order_by(Property.id).all()
    if not properties:
        raise HTTPException(status_code=500, detail="No hay propiedades configuradas")

    selected = property_id or properties[0].id
    selected_property = next((p for p in properties if p.id == selected), properties[0])

    visits = (
        db.query(Visit)
        .options(joinedload(Visit.property))
        .filter(Visit.property_id == selected_property.id)
        .order_by(Visit.scheduled_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "owner.html",
        {
            "request": request,
            "properties": properties,
            "selected_property": selected_property,
            "visits": visits,
            "now_iso": datetime.now().strftime("%Y-%m-%dT%H:%M"),
        },
    )


@app.post("/owner/visits")
def create_visit(
    property_id: int = Form(...),
    visitor_name: str = Form(...),
    visitor_id: str = Form(...),
    access_type: str = Form(...),
    scheduled_at: str = Form(...),
    db: Session = Depends(get_db),
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Propiedad no encontrada")

    try:
        scheduled_dt = datetime.fromisoformat(scheduled_at)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Fecha y hora inválidas") from exc

    if access_type not in {AccessType.PEATONAL.value, AccessType.VEHICULAR.value}:
        raise HTTPException(status_code=400, detail="Tipo de acceso inválido")

    visit = Visit(
        property_id=property_id,
        visitor_name=visitor_name.strip(),
        visitor_id=visitor_id.strip(),
        access_type=AccessType(access_type),
        scheduled_at=scheduled_dt,
        code=generate_code(db),
        status=VisitStatus.SCHEDULED,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)

    return RedirectResponse(url=f"/owner?property_id={property_id}&created={visit.code}", status_code=303)


@app.get("/guard", response_class=HTMLResponse)
def guard_panel(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    start, end = today_range()

    expected = (
        db.query(Visit)
        .options(joinedload(Visit.property))
        .filter(
            Visit.scheduled_at >= start,
            Visit.scheduled_at <= end,
            Visit.status == VisitStatus.SCHEDULED,
        )
        .order_by(Visit.scheduled_at.asc())
        .all()
    )

    inside = (
        db.query(Visit)
        .options(joinedload(Visit.property))
        .filter(Visit.status == VisitStatus.INSIDE)
        .order_by(Visit.entry_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "guard.html",
        {
            "request": request,
            "expected_visits": expected,
            "inside_visits": inside,
        },
    )


@app.get("/api/visits/today")
def api_visits_today(db: Session = Depends(get_db)) -> JSONResponse:
    start, end = today_range()
    visits = (
        db.query(Visit)
        .options(joinedload(Visit.property))
        .filter(
            Visit.scheduled_at >= start,
            Visit.scheduled_at <= end,
            Visit.status == VisitStatus.SCHEDULED,
        )
        .order_by(Visit.scheduled_at.asc())
        .all()
    )
    return JSONResponse([visit_to_dict(v) for v in visits])


@app.get("/api/visits/inside")
def api_visits_inside(db: Session = Depends(get_db)) -> JSONResponse:
    visits = (
        db.query(Visit)
        .options(joinedload(Visit.property))
        .filter(Visit.status == VisitStatus.INSIDE)
        .order_by(Visit.entry_at.desc())
        .all()
    )
    return JSONResponse([visit_to_dict(v) for v in visits])


@app.get("/api/visits/search")
def api_search_visit(code: str = Query(...), db: Session = Depends(get_db)) -> JSONResponse:
    normalized = code.strip().upper()
    visit = (
        db.query(Visit)
        .options(joinedload(Visit.property))
        .filter(Visit.code == normalized)
        .first()
    )
    if not visit:
        raise HTTPException(status_code=404, detail="Código no encontrado")
    return JSONResponse(visit_to_dict(visit))


@app.post("/api/visits/{visit_id}/entry")
def api_mark_entry(visit_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    visit = get_visit_or_404(db, visit_id)
    if visit.status == VisitStatus.EXITED:
        raise HTTPException(status_code=400, detail="La visita ya fue cerrada")
    if visit.status == VisitStatus.INSIDE:
        raise HTTPException(status_code=400, detail="La visita ya está dentro")

    visit.status = VisitStatus.INSIDE
    visit.entry_at = datetime.now()
    db.commit()
    db.refresh(visit)
    return JSONResponse(visit_to_dict(visit))


@app.post("/api/visits/{visit_id}/exit")
def api_mark_exit(visit_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    visit = get_visit_or_404(db, visit_id)
    if visit.status != VisitStatus.INSIDE:
        raise HTTPException(status_code=400, detail="La visita no está dentro del conjunto")

    visit.status = VisitStatus.EXITED
    visit.exit_at = datetime.now()
    db.commit()
    db.refresh(visit)
    return JSONResponse(visit_to_dict(visit))


def run() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
