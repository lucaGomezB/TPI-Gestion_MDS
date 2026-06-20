# activia-trace

Sistema de gestion academica multi-tenant para la Tecnicatura Universitaria en Programacion a Distancia (TUPAD).

## Stack

| Capa | Tecnologia |
|------|------------|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| Base de datos | PostgreSQL 16 |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query |
| Infraestructura | Docker + Docker Compose |

Documentacion completa: [`knowledge-base/`](knowledge-base/), [`docs/`](docs/), [`CHANGES.md`](CHANGES.md).

---

## Requisitos

### Con Docker (recomendado)
- Docker Engine 24+
- Docker Compose v2

### Sin Docker (desarrollo local)
- Python 3.13
- Node.js 22+
- PostgreSQL 16

---

## Instalacion y ejecucion

### Con Docker

```bash
# 1. Clonar el repositorio
git clone <repo-url>
cd TPI-Gestion_MDS

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con valores reales (SECRET_KEY, ENCRYPTION_KEY, etc.)

# 3. Levantar todos los servicios
docker compose up --build -d
```

Servicios disponibles:
| Servicio | URL |
|----------|-----|
| Frontend | http://localhost |
| API Backend | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| n8n | http://localhost:5678 |

```bash
# 4. Ejecutar migraciones (con los servicios ya levantados)
docker compose exec app alembic upgrade head

# 5. Cargar seed inicial (tenant TUPAD + usuario ADMIN)
docker compose exec app python -c "from app.seed import run; import asyncio; asyncio.run(run())"

# 6. Detener servicios
docker compose down
```

### Sin Docker (desarrollo local)

#### Backend

```bash
cd backend

# Crear y activar entorno virtual
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt  # solo para desarrollo/tests

# Configurar variables de entorno
# Copiar .env.example desde la raiz del proyecto a backend/.env
# y configurar DATABASE_URL apuntando a tu PostgreSQL local
cp ../.env.example .env

# Base de datos: asegurarse de que PostgreSQL 16 este corriendo en localhost:5432
# La URL por defecto espera: postgresql+asyncpg://activia:activia@localhost:5432/activia_trace

# Ejecutar migraciones
alembic upgrade head

# Cargar seed inicial
python -c "from app.seed import run; import asyncio; asyncio.run(run())"

# Iniciar servidor de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo (con proxy a la API en :8000)
npm run dev
```

El frontend estara disponible en `http://localhost:5173` con hot reload.

---

## Tests

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm test
```

---

## Estructura del proyecto

```
TPI-Gestion_MDS/
├── backend/
│   ├── app/            # Codigo fuente FastAPI (Clean Architecture)
│   ├── alembic/        # Migraciones de base de datos
│   ├── tests/          # Tests del backend
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── features/   # Modulos feature-based (auth, materias, equipos, etc.)
│   │   ├── shared/     # Componentes y servicios compartidos
│   │   └── components/ # Layout principal, sidebar, rutas protegidas
│   ├── tests/          # Tests del frontend
│   ├── package.json
│   └── Dockerfile
├── knowledge-base/     # Documentacion de dominio
├── docs/               # Documentacion tecnica
├── docker-compose.yml  # Orquestacion de servicios
├── .env.example        # Variables de entorno de ejemplo
└── CHANGES.md          # Roadmap de implementacion
```
