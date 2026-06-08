## Why

El sistema necesita gestionar el ciclo completo de coloquios (evaluaciones orales): desde la creacion de convocatorias con dias y cupos disponibles, pasando por la reserva de turnos por parte de los alumnos, hasta el registro de resultados con notas. Actualmente no existe ningun modulo que cubra este flujo, lo que obliga a coordinadores a gestionar coloquios fuera del sistema. Implementar este modulo cierra la brecha entre la planificacion de evaluaciones (Epica 5) y la liquidacion de honorarios (Epica 10), ya que las guardias de coloquio son insumo para el calculo de liquidaciones.

## What Changes

- **Nuevos modelos SQLAlchemy**: Evaluacion (especializado para coloquio con dias JSONB y cupos), ReservaEvaluacion (reserva de turno con confirmacion), ResultadoEvaluacion (registro de nota) -- todos multi-tenant con UUID PK y mixins base.
- **Nuevos endpoints REST** para el flujo completo de convocatorias, reservas, agenda y resultados.
- **Nuevo panel de metricas** para administracion global de coloquios.
- **Migracion Alembic** para las tres nuevas tablas.

## Capabilities

### New Capabilities
- `coloquios`: Gestion completa de convocatorias de coloquio (creacion, importacion de alumnos, reservas, agenda, resultados, metricas)

### Modified Capabilities
- `core-models`: UPDATE -- E14 (Evaluacion) se extiende con variante especializada para coloquio con JSONB dias/cupos, creado_por, activa. ReservaEvaluacion y ResultadoEvaluacion se agregan como nuevas entidades.

## Impact

- **Backend**: Nuevos modelos en `app/models/coloquio.py`, nuevos repositorios, servicios y routers.
- **Base de datos**: Nueva migracion Alembic con tablas `evaluaciones`, `reservas_evaluacion`, `resultados_evaluacion`.
- **Dependencias**: Requiere C-14 (encuentros-guardias) archivado -- comparte patron de repositorio, mixins base y UoW.
- **Auth**: Nuevos permisos `coloquios:crear`, `coloquios:importar`, `coloquios:reservar`, `coloquios:resultados`, `coloquios:metricas`.
- **Auditoria**: Nueva accion `COLOQUIO_CREAR`, `COLOQUIO_RESERVAR`, `COLOQUIO_RESULTADO`.
