## Context

Actualmente el sistema cuenta con los modelos base (Tenant, Usuario, Materia, Carrera, Cohorte) y el modulo de asignaciones docentes (C-05), que provee la entidad `Asignacion` vinculando usuarios con roles y contexto academico. No existe un modulo para gestionar encuentros sincronicos ni guardias.

El change C-14 agrega tres nuevas entidades: `SlotEncuentro` (plantilla de recurrencia), `InstanciaEncuentro` (encuentro concreto) y `Guardia` (registro de atencion). Estas entidades se integran con la estructura academica existente via FKs a `Materia` y `Asignacion`.

## Goals / Non-Goals

**Goals:**
- Proveer CRUD de slots de encuentro recurrentes con generacion automatica de N instancias
- Proveer creacion de encuentros unicos (sin recurrencia)
- Permitir edicion individual de instancias de encuentro (estado, meet_url, video_url, comentario) sin afectar al slot ni otras instancias
- Generar snippet HTML/Markdown embebible para publicar en Moodle
- Vista transversal de todos los encuentros del tenant para COORDINADOR y ADMIN
- Registro y consulta de guardias por materia
- Migracion Alembic 010 con tablas `slots_encuentro`, `instancias_encuentro`, `guardias`

**Non-Goals:**
- Integracion con calendarios externos (Google Calendar, Outlook) — queda para future change
- Notificaciones automaticas sobre cambios de estado en encuentros — se manejara via C-11 (cola comunicaciones)
- Export masivo de encuentros a formato CSV/PDF
- Edicion en lote de multiples instancias simultaneamente
- Asignacion automatica de guardias

## Decisions

### Decision 1: Slot vs. Instancia como modelos separados (no denormalizados)

**Decision**: Mantener `SlotEncuentro` e `InstanciaEncuentro` como modelos separados con FK de instancia a slot (nullable).

**Rationale**: RN-14 exige que cada instancia tenga estado independiente del slot. Si se denormalizara todo en una sola tabla, la recurrencia seria implicita y dificil de modificar. La separacion permite:
- Modificar el titulo/meet_url del slot y propagar a instancias futuras sin tocar las pasadas
- Cancelar una instancia individual sin afectar la recurrencia
- Crear instancias independientes (sin slot) para encuentros extraordinarios

**Alternativa considerada**: Tabla unica con `slot_id` como jerarquia de padre-hijo. Se descarto porque complica la semantica de "instancia sin slot".

### Decision 2: Generacion de instancias eager (sincronica) al crear slot

**Decision**: Al crear un slot recurrente, las N instancias se generan sincronicamente en la misma transaccion.

**Rationale**: Para las cantidades esperadas (tipicamente 12-16 semanas por cuatrimestre), generar todas las instancias en el momento es trivial (< 100ms). Esto simplifica la logica: no se necesita worker async ni logica de "instancias faltantes" al consultar.

**Alternativa considerada**: Generacion lazy (bajo demanda al consultar). Se descarto porque complica las queries de listado y la edicion individual.

### Decision 3: Snippet HTML generado como string template (sin motor de templates)

**Decision**: La generacion del snippet HTML/Markdown para Moodle se implementa como una funcion pura que recibe una lista de instancias y devuelve un string formateado.

**Rationale**: Es un formato de salida simple (tabla HTML o lista Markdown). No justifica integrar un motor de templates (Jinja2) solo para esto. La funcion se coloca en el servicio de encuentros.

**Alternativa considerada**: Jinja2 template. Sobredimensionado para el caso de uso.

### Decision 4: Guardia como entidad independiente (no como tipo de encuentro)

**Decision**: `Guardia` es un modelo separado de `InstanciaEncuentro`, con sus propios atributos (dia, horario texto, estado, comentarios).

**Rationale**: Las guardias tienen semantica diferente a los encuentros: no tienen meet_url, no generan instancias, no se embeden en Moodle. Mezclarlos en una misma jerarquia complicaria ambos dominios.

### Decision 5: Permisos RBAC con acciones especificas

**Decision**: Se agregan las siguientes acciones de permiso:
- `encuentros:crear` — crear slots e instancias (PROFESOR, COORDINADOR)
- `encuentros:editar` — editar instancias (PROFESOR, COORDINADOR)
- `encuentros:ver_todas` — vista transversal (COORDINADOR, ADMIN)
- `guardias:registrar` — registrar guardia propia (TUTOR, PROFESOR)
- `guardias:ver_todas` — consultar guardias de cualquier materia (COORDINADOR, ADMIN)

**Rationale**: Sigue el patron existente en C-03 de `modulo:accion`. Se mantiene granularidad sin excederse.

## Risks / Trade-offs

- **[Risk] Generacion eager de instancias**: Si un slot se crea con `cant_semanas=52`, se generan 52 instancias en una transaccion. Para el caso tipico (12-16 semanas) es aceptable. Si en el futuro se requieren recurrencias largas, se puede migrar a generacion lazy.
- **[Risk] Snippet HTML sin sanitizacion**: El `meet_url` ingresado por el usuario debe sanearse para evitar XSS en el snippet embebido en Moodle. Se aplicara escape HTML a todos los campos.
- **[Trade-off] Sin edicion en lote**: La edicion es individual por instancia (RN-14 explicita que cada instancia es independiente). No se contempla edicion masiva, aunque podria agregarse como mejora futura.
- **[Trade-off] Guardia con horario en texto libre**: El campo `horario` de Guardia es texto libre (ej: "14:00-14:45") en lugar de hora estructurada. Esto da flexibilidad para horarios no convencionales pero pierde capacidad de ordenamiento/filtrado por hora. Se acepta como trade-off deliberado por simplicidad.
