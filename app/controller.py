import csv
import io
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Usuario, Propiedad


class MorosidadController:
    """Controlador para gestión de morosidad y carga CSV."""

    @staticmethod
    def parse_boolean_value(value: str) -> bool:
        """
        Convierte valores de cadena a booleano.
        Acepta: true/false, 1/0, si/no, yes/no, y/n (case insensitive).
        """
        if not value:
            return False

        value_lower = value.strip().lower()

        # Valores verdaderos
        if value_lower in {"true", "1", "si", "yes", "y", "verdadero", "v"}:
            return True

        # Valores falsos
        if value_lower in {"false", "0", "no", "n", "falso", "f"}:
            return False

        # Por defecto, si no coincide, asumir False
        return False

    @staticmethod
    def procesar_csv_morosidad(db: Session, csv_content: str) -> dict:
        """
        Procesa un archivo CSV de morosidad y actualiza las propiedades.

        Formato esperado del CSV:
        numero_unidad,es_solvente
        A-12,true
        B-301,false
        SOL-05,true

        Returns:
            dict: {
                "propiedades_actualizadas": int,
                "errores": list[str]
            }
        """
        # Crear un lector CSV desde el contenido string
        csv_file = io.StringIO(csv_content)
        csv_reader = csv.DictReader(csv_file)

        # Validar que el CSV tenga las columnas requeridas
        if not csv_reader.fieldnames or "numero_unidad" not in csv_reader.fieldnames or "es_solvente" not in csv_reader.fieldnames:
            raise HTTPException(
                status_code=400,
                detail="El CSV debe contener las columnas: numero_unidad, es_solvente"
            )

        propiedades_actualizadas = 0
        errores = []

        for row_num, row in enumerate(csv_reader, start=2):  # start=2 porque la fila 1 es el encabezado
            try:
                numero_unidad = row.get("numero_unidad", "").strip()
                es_solvente_str = row.get("es_solvente", "").strip()

                if not numero_unidad:
                    errores.append(f"Fila {row_num}: numero_unidad está vacío")
                    continue

                # Convertir el valor a booleano
                es_solvente = MorosidadController.parse_boolean_value(es_solvente_str)

                # Buscar la propiedad por número de unidad
                propiedad = db.query(Propiedad).filter(
                    Propiedad.numero_unidad == numero_unidad
                ).first()

                if not propiedad:
                    errores.append(f"Fila {row_num}: No se encontró propiedad con unidad {numero_unidad}")
                    continue

                # Actualizar el estado de solvencia
                if propiedad.es_solvente != es_solvente:
                    propiedad.es_solvente = es_solvente
                    propiedades_actualizadas += 1

            except Exception as e:
                errores.append(f"Fila {row_num}: Error al procesar - {str(e)}")

        # Commit de los cambios
        if propiedades_actualizadas > 0:
            db.commit()

        return {
            "propiedades_actualizadas": propiedades_actualizadas,
            "errores": errores
        }

    @staticmethod
    def verificar_solvencia_propiedad(db: Session, propiedad_id: int) -> bool:
        """
        Verifica si una propiedad es solvente.
        Returns True si es solvente, False en caso contrario.
        """
        propiedad = db.query(Propiedad).filter(Propiedad.id == propiedad_id).first()
        if not propiedad:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")

        return propiedad.es_solvente


class UsuarioController:
    """Controlador para gestión de usuarios y habitantes."""

    @staticmethod
    def contar_habitantes_por_propiedad(db: Session, propiedad_id: int) -> int:
        """
        Cuenta el número total de habitantes (ADMIN_CASA + COHABITANTE)
        asociados a una propiedad específica.
        """
        count = (
            db.query(Usuario)
            .filter(
                Usuario.propiedad_id == propiedad_id,
                Usuario.rol.in_(["ADMIN_CASA", "COHABITANTE"])
            )
            .count()
        )
        return count

    @staticmethod
    def validar_limite_habitantes(db: Session, propiedad_id: int, max_habitantes: int = 4) -> None:
        """
        Valida que no se exceda el límite máximo de habitantes por propiedad.
        Lanza HTTPException si se excede el límite.
        """
        count_actual = UsuarioController.contar_habitantes_por_propiedad(db, propiedad_id)
        if count_actual >= max_habitantes:
            raise HTTPException(
                status_code=400,
                detail=f"Límite máximo de {max_habitantes} habitantes alcanzado para esta propiedad"
            )

    @staticmethod
    def verificar_usuario_existe(db: Session, cedula: str) -> bool:
        """Verifica si ya existe un usuario con la cédula proporcionada."""
        return db.query(Usuario).filter(Usuario.cedula == cedula).first() is not None

    @staticmethod
    def crear_usuario(db: Session, nombre: str, email: str, cedula: str, propiedad_id: int, rol: str, password_hash: str) -> Usuario:
        """Crea un nuevo usuario en la base de datos."""
        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            cedula=cedula,
            propiedad_id=propiedad_id,
            rol=rol,
            password_hash=password_hash,
        )
        db.add(nuevo_usuario)
        db.commit()
        db.refresh(nuevo_usuario)
        return nuevo_usuario

    @staticmethod
    def obtener_usuario_por_cedula(db: Session, cedula: str) -> Usuario:
        """Obtiene un usuario por su cédula."""
        usuario = db.query(Usuario).filter(Usuario.cedula == cedula).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return usuario

    @staticmethod
    def obtener_usuarios_por_propiedad(db: Session, propiedad_id: int) -> List[Usuario]:
        """Obtiene todos los usuarios asociados a una propiedad."""
        return db.query(Usuario).filter(Usuario.propiedad_id == propiedad_id).all()

    @staticmethod
    def obtener_usuario_por_id(db: Session, usuario_id: int) -> Usuario:
        """Obtiene un usuario por su ID."""
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return usuario


class PropiedadController:
    """Controlador para gestión de propiedades."""

    @staticmethod
    def obtener_propiedad_por_id(db: Session, propiedad_id: int) -> Propiedad:
        """Obtiene una propiedad por su ID."""
        propiedad = db.query(Propiedad).filter(Propiedad.id == propiedad_id).first()
        if not propiedad:
            raise HTTPException(status_code=404, detail="Propiedad no encontrada")
        return propiedad

    @staticmethod
    def obtener_todas_propiedades(db: Session) -> List[Propiedad]:
        """Obtiene todas las propiedades."""
        return db.query(Propiedad).all()


class CondominioController:
    """Controlador para gestión de condominios."""

    @staticmethod
    def obtener_condominio_por_id(db: Session, condominio_id: int):
        """Obtiene un condominio por su ID."""
        from app.models import Condominio
        condominio = db.query(Condominio).filter(Condominio.id == condominio_id).first()
        if not condominio:
            raise HTTPException(status_code=404, detail="Condominio no encontrado")
        return condominio

    @staticmethod
    def obtener_todos_condominios(db: Session):
        """Obtiene todos los condominios."""
        from app.models import Condominio
        return db.query(Condominio).all()
