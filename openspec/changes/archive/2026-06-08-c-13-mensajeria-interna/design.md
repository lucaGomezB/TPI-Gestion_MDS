## Context

La mensajeria interna entre docentes y coordinacion es un requerimiento funcional del sistema (F3.4, F11.2) que permite la comunicacion asincronica dentro del tenant sin depender de canales externos (email, WhatsApp). Actualmente no existe este modulo. Se construye como una nueva capacidad dentro de la arquitectura existente, reutilizando los patrones de Clean Architecture, UoW y repositorios que ya estan consolidados en el proyecto.

El modelo de datos sigue las entidades E14 (HiloMensaje) y E15 (Mensaje) definidas en la KB, con relacion 1:N entre hilos y mensajes. No hay relacion con C-12 (avisos-tablon) a nivel funcional — la dependencia en el roadmap es por orden de implementacion.

## Goals / Non-Goals

**Goals:**
- Proveer endpoints REST para bandeja de entrada del usuario autenticado (mensajes recibidos).
- Permitir envio de mensajes directos entre usuarios del mismo tenant.
- Soportar hilos (threads) agrupando mensajes con el mismo asunto.
- Proveer respuesta dentro del hilo existente.
- Exponer contador de mensajes no leidos para notificacion.
- Aislamiento multi-tenant: mensajes de un tenant jamas visibles para otro.
- Soft-delete solo para el usuario (no hard-delete del mensaje): un mensaje marcado como eliminado por el destinatario no desaparece para el remitente.

**Non-Goals:**
- Chat en tiempo real / WebSockets (comunicacion asincronica, no sincronica).
- Grupos de mensajeria mas alla del hilo 1:1.
- Archivos adjuntos en mensajes (fuera de scope; puede agregarse en version futura).
- Notificaciones push o email (solo contador interno de no leidos).
- Mensajeria con ALUMNO (solo entre docentes y coordinacion).

## Decisions

### Decision 1: Hilo como entidad separada (no inferido del asunto)

- **Opcion A (elegida)**: `HiloMensaje` como entidad independiente con `id`, `tenant_id`, `asunto`, `participantes` (JSONB). `Mensaje` tiene FK `hilo_id`.
- **Opcion B**: Hilo inferido agrupando mensajes por `asunto` + `remitente_id` + `destinatario_id`.
- **Razon**: La opcion A permite manejar el ciclo de vida del hilo (creacion explicita, cierre, archivado) sin depender de heuristicas sobre el asunto. JSONB en `participantes` permite saber rapidamente quienes participan sin joins multiples. Sigue el patron de modelos de mensajeria probados (similar al modelo de threads en redes sociales).

### Decision 2: Participantes como JSONB array en HiloMensaje

- **Alternativa**: Tabla intermedia `HiloParticipante` con FK a `HiloMensaje` y `Usuario`.
- **Razon**: JSONB simplifica el modelo para el caso de uso actual (siempre 2 participantes: remitente y destinatario). La validacion de que ambos pertenecen al mismo tenant se hace en el servicio. Si en el futuro se requieren grupos (3+ participantes), se migrara a tabla intermedia. JSONB es soportado nativamente por PostgreSQL y el ORM lo maneja como `dict`.

### Decision 3: Contador de no leidos como query agregada, no columna cache

- **Alternativa**: Columna `no_leidos` cacheada en `HiloMensaje` o `Usuario`.
- **Razon**: Para el volumen de mensajeria esperado (decenas, no miles por usuario), `SELECT COUNT(*) WHERE destinatario_id = :uid AND leido = false` es eficiente con un indice compuesto `(destinatario_id, leido, tenant_id)`. Evita problemas de consistencia eventual (cache desincronizada). Se migrara a cache solo si hay evidencia de degradacion.

### Decision 4: Soft-delete por usuario via tabla de eliminaciones

- **Alternativa**: Columna `deleted_at` en `Mensaje` (eliminacion global).
- **Razon**: En mensajeria, eliminar un mensaje para un usuario no debe afectar al otro. Se implementa una tabla `mensaje_eliminado` (o columna `eliminado_por_remitente` / `eliminado_por_destinatario`) para borrado logico por usuario. Esto es consistente con el comportamiento esperado de bandejas de entrada.

### Decision 5: Permiso de envio via `mensajeria:enviar`

- Se agrega el permiso `mensajeria:enviar` a la matriz de permisos del sistema (RBAC). La lectura esta implicitamente autorizada porque solo se muestran mensajes donde el usuario autenticado es remitente o destinatario. No se requiere un permiso de lectura separado.
- Roles con permiso: TUTOR, PROFESOR, COORDINADOR, ADMIN.
- La implementacion reutiliza el decorador o dependency `require_permission` existente en `app/core/permissions.py`.

## Risks / Trade-offs

- [JSONB vs tabla intermedia] JSONB para participantes es pragmatico ahora pero requerira migracion si se soportan grupos de 3+ participantes. Mitigacion: la capa de servicio abstrae el acceso a participantes, por lo que el cambio afectaria solo al repositorio y al modelo, no a los endpoints.
- [Sin archivos adjuntos] La decision de no incluir adjuntos en esta version puede generar solicitudes tempranas de usuarios. Mitigacion: el modelo de `Mensaje` incluye `cuerpo: Text`, dejando espacio para un futuro campo `archivos: JSONB` sin romper compatibilidad.
- [Contador de no leidos por query] En tenants con muchos usuarios y alta carga de mensajeria, el COUNT indexado puede degradarse. Mitigacion: monitorear con OpenTelemetry; migrar a columna cache si el tiempo de respuesta supera 100ms.
