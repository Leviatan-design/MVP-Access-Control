# Control de Acceso Residencial — MVP Demo

Aplicación web full-stack para gestionar visitas en conjuntos residenciales. Incluye panel de propietario (agendar visitas y generar pases con QR) y panel de garita (búsqueda, escaneo QR, entradas/salidas).

## Stack

- **Backend:** Python 3.12 + FastAPI + Uvicorn
- **Frontend:** Jinja2 + TailwindCSS (CDN) + JavaScript nativo
- **Base de datos:** SQLite con datos semilla automáticos
- **Contenedor:** Docker (imagen slim)

## Funcionalidades

| Módulo | Descripción |
|--------|-------------|
| Inicio | Selector rápido de rol (Propietario / Vigilante) sin contraseñas |
| Propietario | Formulario de visita, código de 6 caracteres (ej. `ACC-902`), QR dinámico, lista de visitas |
| Garita | Búsqueda por código, escáner QR por cámara, listas en vivo, botones de entrada/salida |

### Datos de prueba (seed)

Al iniciar la aplicación se crean automáticamente:

- 3 propiedades residenciales
- 4 visitas esperadas para hoy
- 2 visitas en estado "Dentro del conjunto"

## Ejecución local con Docker

### Requisitos

- Docker Desktop (o Docker Engine + Docker Compose)

### Pasos

```bash
# 1. Construir la imagen
docker build -t access-control .

# 2. Ejecutar el contenedor
docker run --rm -p 8080:8080 -e PORT=8080 access-control
```

Abre en el navegador: **http://localhost:8080**

### Verificar salud

```bash
curl http://localhost:8080/health
```

Respuesta esperada: `{"status":"ok","service":"access-control"}`

## Ejecución local sin Docker

### Requisitos

- Python 3.12+

### Pasos

```bash
# Crear entorno virtual (opcional pero recomendado)
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
set PORT=8080
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

En Linux/macOS usa `export PORT=8080` en lugar de `set PORT=8080`.

## Despliegue en Render.com (plan gratuito)

### Opción A: Blueprint (render.yaml)

1. Sube este repositorio a GitHub, GitLab o Bitbucket.
2. En [Render Dashboard](https://dashboard.render.com), haz clic en **New → Blueprint**.
3. Conecta el repositorio. Render detectará `render.yaml` automáticamente.
4. Confirma el despliegue. Render construirá la imagen Docker y publicará el servicio.

### Opción B: Web Service manual

1. **New → Web Service** en Render.
2. Conecta tu repositorio.
3. Configura:
   - **Runtime:** Docker
   - **Plan:** Free
   - **Health Check Path:** `/health`
4. Variables de entorno (opcionales):
   - `DATA_DIR` = `/app/data`
   - `PORT` — Render la inyecta automáticamente; no es necesario definirla manualmente.
5. Haz clic en **Create Web Service**.

### Notas para Render Free Tier

- El disco es **efímero**: los datos SQLite se reinician en cada redeploy.
- El servicio entra en **sleep** tras inactividad (~15 min). La primera petición puede tardar unos segundos.
- El escaneo QR requiere **HTTPS** (Render lo provee) y permiso de cámara en el navegador.

## Estructura del proyecto

```
.
├── app/
│   ├── main.py           # Rutas FastAPI y API REST
│   ├── database.py       # Configuración SQLite
│   ├── models.py         # Modelos Property y Visit
│   ├── seed.py           # Datos de prueba
│   ├── static/           # Archivos estáticos
│   └── templates/        # Plantillas Jinja2
│       ├── base.html
│       ├── index.html
│       ├── owner.html
│       └── guard.html
├── Dockerfile
├── render.yaml
├── requirements.txt
└── README.md
```

## API REST

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/visits/today` | Visitas esperadas hoy |
| GET | `/api/visits/inside` | Visitantes dentro |
| GET | `/api/visits/search?code=ACC-902` | Buscar por código |
| POST | `/api/visits/{id}/entry` | Registrar entrada |
| POST | `/api/visits/{id}/exit` | Registrar salida |

## Códigos de prueba

Puedes probar en el panel de garita con estos códigos precargados:

| Código | Visitante | Estado |
|--------|-----------|--------|
| ACC-902 | Pedro López | Agendada |
| VIS-415 | Laura Sánchez | Agendada |
| ENT-733 | Roberto Díaz | Agendada |
| PAS-128 | Sofía Herrera | Agendada |
| ING-556 | Miguel Torres | Dentro |
| AUT-789 | Diana Vega | Dentro |

## Licencia

Proyecto demo — uso libre para pruebas y demostraciones.
