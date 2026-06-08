## Context

El modulo de coloquios gestiona el ciclo completo de evaluaciones orales: creacion de convocatorias con dias y cupos, reserva de turnos por alumnos, y registro de resultados. Actualmente el sistema no contempla este flujo; coordinadores lo gestionan fuera del sistema. El diseno se alinea con los patrones existentes en el proyecto: modelos SQLAlchemy con mixins (AppModel, TimestampMixin, TenantMixin), repositorios con scope de tenant, servicios con UnitOfWork, y schemas Pydantic con `extra='forbid'`.

Los modelos conceptuales E14 (Evaluacion), ReservaEvaluacion y ResultadoEvaluacion ya estan definidos en la KB (04_modelo_de_datos.md). Este cambio produce una implementacion especializada para coloquios que se aparta ligeramente del modelo conceptual generico para adaptarse a las necesidades especificas del dominio: JSONB para dias con cupos auto-decrecientes, y ausencia de cohorte_id (los coloquios se crean por materia sin depender de una cohorte particular).

## Goals / Non-Goals

**Goals:**
- Proveer modelos SQLAlchemy para Evaluacion (coloquio), ReservaEvaluacion y ResultadoEvaluacion
- Implementar 6 endpoints REST que cubran el flujo completo: crear convocatoria, importar alumnos, reservar turno, consultar agenda, registrar resultados, metricas admin
- Seguir los patrones existentes: modelo -> repositorio -> servicio -> router, con UnitOfWork, permisos y auditoria
- Proveer migracion Alembic para las 3 nuevas tablas

**Non-Goals:**
- No incluye UI frontend (solo API)
- No incluye envio de notificaciones automaticas al reservar (se hara en cambio futuro)
- No incluye integracion con el LMS para coloquios
- No modifica modelos existentes (se crean tablas nuevas)

## Decisions

### D-01: Modelos separados vs. extender E14 generico

**Decision**: Crear modelos SQLAlchemy dedicados (`EvaluacionColoquio`, `ReservaColoquio`, `ResultadoColoquio`) en lugar de reutilizar el modelo conceptual E14 generico.

**Rationale**: El modelo E14 conceptual (`tipo`, `instancia`, `dias_disponibles`) no se ajusta a los requerimientos de coloquio: se necesita JSONB para dias con cupos individuales, campo `creado_por` para trazabilidad del creador, y `activa` para control de vigencia. Separar en tablas dedicadas evita acoplar el modelo generico a necesidades especificas de coloquio y permite evolucionar independientemente.

### D-02: Alumno_id como FK a Usuario (no EntradaPadron)

**Decision**: `alumno_id` en ReservaColoquio y ResultadoColoquio es FK a `usuarios.id` (nullable en Resultado).

**Rationale**: La reserva requiere autenticacion del alumno -> el alumno tiene usuario en el sistema. EntradaPadron puede tener `usuario_id` nulo (alumnos sin cuenta), pero para reservar necesitan cuenta. Usar FK directa a Usuario simplifica el modelo y evita FK polimorfica.

### D-03: Tabla `evaluaciones_coloquio` con JSONB `dias`

**Decision**: El campo `dias` es JSONB con estructura `[{"fecha": "2026-07-01", "cupos": 10, "reservados": 0}]`.

**Rationale**: Las fechas de coloquio son flexibles (el coordinador define dias y cupos variables). JSONB permite schema-less dentro del JSON, facilita la consulta de cupos restantes, y es consistente con otros usos de JSONB en el proyecto (configuracion del tenant, permisos de roles).

### D-04: Namespace de rutas bajo `/api/materias/{id}/coloquios` y `/api/coloquios/{id}`

**Decision**: Las rutas de gestion (crear, importar) van bajo `/api/materias/{id}/coloquios` porque requieren contexto de materia. Las rutas de operacion (reservar, agenda, resultados) van bajo `/api/coloquios/{id}` porque operan sobre una evaluacion existente.

### D-05: Mecanismo de cupos auto-decrecientes

**Decision**: Al crear una reserva, el servicio decrementa el contador `cupos` del dia correspondiente en el JSONB. Si `reservados >= cupos`, rechaza la reserva con 409 Conflict.

**Rationale**: La logica de concurrencia se maneja a nivel de aplicacion con optimistic locking (version del registro o mediante update atomico del JSONB). Para la primera version, el chequeo en el servicio es suficiente dado que el volumen de reservas simultaneas es bajo.

## Risks / Trade-offs

- **Concurrencia en cupos**: Dos alumnos reservando el ultimo cupo simultaneamente podrian generar race condition. En la primera version se mitiga con validacion en servicio + transaccion SQL. Para alta concurrencia, migrar a optimistic locking con columna `version`.
- **JSONB no validado por la BD**: El campo `dias` JSONB no tiene schema fijo. La validacion recae en Pydantic y en el servicio. Si el schema interno cambia, habra que migrar los JSON existentes.
- **Aislamiento multi-tenant**: Todos los filtros de repositorio incluyen `tenant_id`. Una omision expondria datos entre tenants.

## Open Questions

- ¿Se necesita `cohorte_id` en EvaluacionColoquio? La tarea no lo incluye, pero el modelo conceptual E14 lo tiene. Se omite en este cambio; se agrega si surge necesidad.
- ¿Alumno_id en ReservaEvaluacion podria referenciar EntradaPadron para alumnos sin cuenta? Se decidio FK a Usuario, pero queda como pregunta abierta para coordinacion con el equipo funcional.
