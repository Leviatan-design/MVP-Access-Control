import random
import os
import secrets
import string
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Condominio, Propiedad, Usuario, Pase
from app.security import hash_password


def ensure_super_admin(db: Session) -> None:
    """Crea el acceso de desarrollo una sola vez, incluso con datos ya existentes."""
    email = os.environ.get("SUPER_ADMIN_EMAIL", "dev@flowlogic.com").strip().lower()
    if db.query(Usuario).filter(Usuario.email == email).first():
        return

    password = os.environ.get("SUPER_ADMIN_PASSWORD") or secrets.token_urlsafe(24)
    db.add(Usuario(
        propiedad_id=None,
        nombre="Administrador de Desarrollo",
        email=email,
        cedula="SUPER-ADMIN-001",
        password_hash=hash_password(password),
        rol="SUPER_ADMIN",
    ))
    db.commit()
    print(f"SUPER_ADMIN inicial creado: {email} | contraseña: {password}")


def generate_code(db: Session) -> str:
    """Genera un código único para pases."""
    while True:
        letters = "".join(random.choices(string.ascii_uppercase, k=3))
        digits = "".join(random.choices(string.digits, k=3))
        code = f"{letters}-{digits}"
        exists = db.query(Pase).filter(Pase.codigo == code).first()
        if not exists:
            return code


def seed_database(db: Session) -> None:
    """Inicializa la base de datos con datos de ejemplo."""
    ensure_super_admin(db)
    # Solo sembrar si no hay datos
    if db.query(Condominio).count() > 0:
        return

    # Crear condominio
    condominio = Condominio(
        nombre="Conjunto Residencial FlowLogic",
        direccion="Av. Principal #123, Ciudad"
    )
    db.add(condominio)
    db.flush()

    # Crear propiedades
    propiedades = [
        Propiedad(
            condominio_id=condominio.id,
            numero_unidad="A-12",
            es_solvente=True
        ),
        Propiedad(
            condominio_id=condominio.id,
            numero_unidad="B-301",
            es_solvente=True
        ),
        Propiedad(
            condominio_id=condominio.id,
            numero_unidad="SOL-05",
            es_solvente=True
        ),
    ]
    db.add_all(propiedades)
    db.flush()

    # Crear usuarios (ADMIN_CASA para cada propiedad)
    usuarios = [
        Usuario(
            propiedad_id=propiedades[0].id,
            nombre="María González",
            email="maria.gonzalez@example.com",
            cedula="V-12345678",
            password_hash=hash_password("Demo-FlowLogic-2026!"),
            rol="ADMIN_CASA",
        ),
        Usuario(
            propiedad_id=propiedades[1].id,
            nombre="Carlos Ruiz",
            email="carlos.ruiz@example.com",
            cedula="V-87654321",
            password_hash=hash_password("Demo-FlowLogic-2026!"),
            rol="ADMIN_CASA",
        ),
        Usuario(
            propiedad_id=propiedades[2].id,
            nombre="Ana Martínez",
            email="ana.martinez@example.com",
            cedula="V-99887766",
            password_hash=hash_password("Demo-FlowLogic-2026!"),
            rol="ADMIN_CASA",
        ),
    ]
    db.add_all(usuarios)
    db.flush()

    # Crear algunos co-habitantes de ejemplo
    cohabitantes = [
        Usuario(
            propiedad_id=propiedades[0].id,
            nombre="Juan González",
            email="juan.gonzalez@example.com",
            cedula="V-12345679",
            password_hash=hash_password("Demo-FlowLogic-2026!"),
            rol="COHABITANTE",
        ),
        Usuario(
            propiedad_id=propiedades[1].id,
            nombre="Laura Ruiz",
            email="laura.ruiz@example.com",
            cedula="V-87654322",
            password_hash=hash_password("Demo-FlowLogic-2026!"),
            rol="COHABITANTE",
        ),
    ]
    db.add_all(cohabitantes)

    # Crear algunos pases de ejemplo
    now = datetime.now()
    pases = [
        Pase(
            propiedad_id=propiedades[0].id,
            visitante_nombre="Pedro López",
            visitante_cedula="V-55555555",
            codigo=generate_code(db),
            estado="PENDIENTE",
            created_at=now
        ),
        Pase(
            propiedad_id=propiedades[1].id,
            visitante_nombre="Roberto Díaz",
            visitante_cedula="V-66666666",
            codigo=generate_code(db),
            estado="DENTRO",
            created_at=now - timedelta(hours=1)
        ),
    ]
    db.add_all(pases)

    db.commit()
    print("Base de datos inicializada con datos de ejemplo")
