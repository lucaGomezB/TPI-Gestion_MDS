## Why

Profesores y tutores necesitan gestionar los encuentros sincronicos virtuales (clases, consultas) con sus alumnos de forma estructurada, ya sea como eventos recurrentes semanales o encuentros unicos. Adicionalmente, los tutores registran guardias de atencion a alumnos que deben ser consultables por coordinacion. Actualmente no existe un modulo dedicado para esto, lo que obliga a usar herramientas externas sin integracion ni trazabilidad.

## What Changes

- Nuevos modelos `SlotEncuentro`, `InstanciaEncuentro` y `Guardia` con sus migraciones
- Creacion de slots recurrentes (genera N instancias automaticamente) y encuentros unicos
- Edicion individual de instancias de encuentro (estado, meet, video, comentario) sin afectar al slot ni otras instancias
- Generacion de snippet HTML/Markdown embebible para publicar en Moodle
- Vista transversal de todos los encuentros del tenant para coordinacion/admin
- Registro y consulta de guardias por materia
- Permisos RBAC integrados: PROFESOR y COORDINADOR pueden gestionar encuentros; TUTOR registra sus guardias

## Capabilities

### New Capabilities
- `encuentros`: Gestion de slots de encuentro recurrentes y unicos, instancias, edicion individual, generacion de embed HTML para Moodle y vista transversal.
- `guardias`: Registro y consulta de guardias de atencion a alumnos.

### Modified Capabilities

None. This is a new module with no existing spec changes.

## Impact

- **Backend**: Nuevos modelos, repositorios, servicios y routers en `backend/app/models/`, `backend/app/repositories/`, `backend/app/services/`, `backend/app/api/v1/`
- **Base de datos**: Nueva migracion Alembic (010) con tablas `slots_encuentro`, `instancias_encuentro`, `guardias`
- **Dependencias**: Depende de C-05 (roles-asignaciones) para la FK a `Asignacion`
- **Permisos**: Se agregaran acciones de permiso `encuentros:*` y `guardias:*` en la matriz RBAC
