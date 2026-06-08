## Why

La comunicacion informal entre docentes y coordinacion ocurre hoy fuera del sistema (email, WhatsApp, Slack), lo que fragmenta la trazabilidad de decisiones y novedades. No existe un canal interno donde quede registro de intercambios vinculados al contexto academico del tenant. Esta funcionalidad resuelve la necesidad de una bandeja de mensajeria interna docente <-> coordinacion con soporte de hilos (threads), que permita leer, enviar y responder mensajes sin salir de la plataforma.

## What Changes

- Creacion del modelo `HiloMensaje` (thread) y `Mensaje` con relacion FK al hilo.
- Nuevos endpoints REST para bandeja de entrada, visualizacion de hilos, envio y respuesta dentro del hilo.
- Contador de mensajes no leidos para notificacion interna en la UI.
- Aislamiento multi-tenant: todos los mensajes y threads estan scoped al tenant del usuario autenticado.
- Permisos: solo usuarios del mismo tenant pueden intercambiar mensajes. Lectura y escritura scoped por destinatario/remitente.

## Capabilities

### New Capabilities

- `mensajeria`: Gestion de mensajeria interna con hilos (threads). Incluye envio de mensajes entre usuarios del mismo tenant, respuesta dentro del hilo, bandeja de entrada filtrada por destinatario y contador de no leidos.

### Modified Capabilities

- (ninguna — primera version del modulo)

## Impact

- **Backend**: nuevos modelos SQLAlchemy (`HiloMensaje`, `Mensaje`), repositorio, servicio y router.
- **Permisos**: se requiere el permiso `mensajeria:enviar` (dado a TUTOR, PROFESOR, COORDINADOR, ADMIN segun matriz existente). No se requiere un permiso de lectura explicito porque cada usuario solo ve sus propios mensajes (scope por destinatario/remitente).
- **Unit of Work**: se agrega `MensajeRepository` al catalogo de repositorios del UoW.
- **Dependencia**: C-12 (avisos-tablon) archivado — no hay dependencia tecnica directa, pero el orden de cambios en el roadmap ubica a C-13 despues de C-12.
