import random
import string
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import AccessType, Property, Visit, VisitStatus


def generate_code(db: Session) -> str:
    while True:
        letters = "".join(random.choices(string.ascii_uppercase, k=3))
        digits = "".join(random.choices(string.digits, k=3))
        code = f"{letters}-{digits}"
        exists = db.query(Visit).filter(Visit.code == code).first()
        if not exists:
            return code


def seed_database(db: Session) -> None:
    if db.query(Property).count() > 0:
        return

    properties = [
        Property(name="Casa 12 Bloque A", unit="A-12", owner_name="María González"),
        Property(name="Apartamento 301 Torre B", unit="B-301", owner_name="Carlos Ruiz"),
        Property(name="Casa 5 Conjunto Sol", unit="SOL-05", owner_name="Ana Martínez"),
    ]
    db.add_all(properties)
    db.flush()

    now = datetime.now()
    today_morning = now.replace(hour=9, minute=0, second=0, microsecond=0)

    scheduled_visits = [
        {
            "property_id": properties[0].id,
            "visitor_name": "Pedro López",
            "visitor_id": "V-12345678",
            "access_type": AccessType.PEATONAL,
            "scheduled_at": today_morning + timedelta(hours=2),
            "code": "ACC-902",
            "status": VisitStatus.SCHEDULED,
        },
        {
            "property_id": properties[0].id,
            "visitor_name": "Laura Sánchez",
            "visitor_id": "V-87654321",
            "access_type": AccessType.VEHICULAR,
            "scheduled_at": today_morning + timedelta(hours=4),
            "code": "VIS-415",
            "status": VisitStatus.SCHEDULED,
        },
        {
            "property_id": properties[1].id,
            "visitor_name": "Roberto Díaz",
            "visitor_id": "V-11223344",
            "access_type": AccessType.PEATONAL,
            "scheduled_at": today_morning + timedelta(hours=1),
            "code": "ENT-733",
            "status": VisitStatus.SCHEDULED,
        },
        {
            "property_id": properties[2].id,
            "visitor_name": "Sofía Herrera",
            "visitor_id": "V-99887766",
            "access_type": AccessType.VEHICULAR,
            "scheduled_at": today_morning + timedelta(hours=6),
            "code": "PAS-128",
            "status": VisitStatus.SCHEDULED,
        },
    ]

    inside_visits = [
        {
            "property_id": properties[1].id,
            "visitor_name": "Miguel Torres",
            "visitor_id": "V-55443322",
            "access_type": AccessType.PEATONAL,
            "scheduled_at": today_morning - timedelta(hours=1),
            "code": "ING-556",
            "status": VisitStatus.INSIDE,
            "entry_at": today_morning - timedelta(minutes=45),
        },
        {
            "property_id": properties[2].id,
            "visitor_name": "Diana Vega",
            "visitor_id": "V-66778899",
            "access_type": AccessType.VEHICULAR,
            "scheduled_at": today_morning - timedelta(minutes=30),
            "code": "AUT-789",
            "status": VisitStatus.INSIDE,
            "entry_at": today_morning - timedelta(minutes=15),
        },
    ]

    for data in scheduled_visits + inside_visits:
        visit = Visit(**data)
        db.add(visit)

    db.commit()
