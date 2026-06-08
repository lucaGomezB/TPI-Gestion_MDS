## Context

El modulo de facturacion de docentes monotributistas cubre el flujo contable separado para usuarios con facturador=true (RN-35). C-19 ya implemento Liquidacion con el flag `excluido_por_factura`. Este change agrega el modelo Factura (E20) y los endpoints para subir PDF, consultar historial, y gestionar desde admin. Governance: ALTO (datos financieros).

## Goals / Non-Goals

**Goals:**
- Modelo Factura con persistencia (E20) siguiendo patrones existentes
- Upload de PDF con validacion de tipo y tamano
- Historial del propio docente con filtro por periodo
- Panel admin con filtros (estado, periodo, docente, busqueda libre) y marcado abonada
- Permisos: `facturas:subir` y `facturas:gestionar`
- Almacenamiento de PDF via referencia opaca (mismo patron que ProgramaMateria E16)
- UoW pattern para operaciones de escritura

**Non-Goals:**
- No se modifica Liquidacion ni su calculo (ya implementado en C-19)
- No se implementa almacenamiento S3/local externo -- se usa el mismo mecanismo que E16 (referencia_archivo)
- No hay envio de notificaciones al cambiar estado
- No hay integracion con sistema contable externo
- No hay generacion de reports/estadisticas de facturacion

## Decisions

### Decision 1: File storage reuse existing pattern
Usar el mismo mecanismo de `referencia_archivo` que ProgramaMateria (E16). El archivo se almacena en el filesystem local bajo un directorio configurable, con un UUID como nombre. La referencia opaca evita path traversal.

**Alternativa considerada**: S3 compatible storage -- se descarta por simplicidad y consistencia con C-16 (programas de materia).

### Decision 2: Permiso facturas:subir validado en dos capas
El permiso `facturas:subir` se asigna a PROFESOR y TUTOR, pero la operacion ademas valida `usuario.facturador == true`. Esto evita que docentes en relacion de dependencia suban facturas erroneamente.

**Alternativa**: crear roles separados FACTURANTE -- se descarta por sobreingenieria; el flag facturador en Usuario es suficiente y ya esta modelado.

### Decision 3: PDF validation on upload
El endpoint POST /api/docentes/facturas valida:
- Content-Type: application/pdf
- Tamano maximo: 10 MB (configurable)
- El archivo se almacena y su referencia se guarda en Factura

**Alternativa**: almacenar en base64 en DB -- se descarta por impacto en performance y tamanio de DB.

### Decision 4: Filtros en GET /api/admin/facturas con query params
Se usa filter pattern combinacional: todos los parametros son opcionales y se aplican en AND. El repositorio construye la query dinamicamente con filtros por tenant, estado, periodo, usuario_id y busqueda LIKE en detalle.

### Decision 5: PUT /api/admin/facturas/{id}/abonar con descarga opcional
El query param `?descargar=true` permite que en una sola operacion el admin marque como abonada y reciba el PDF. Si es false, solo actualiza estado.

## Risks / Trade-offs

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| PDF malicioso en upload | Low | Validar Content-Type, limitar tamano, almacenar fuera del webroot |
| Race condition: dos admins marcan misma factura como abonada | Low | WHERE estado='Pendiente' en UPDATE; si ya esta Abonada, 409 Conflict |
| Perdida de archivos PDF en filesystem local | Medium | Documentar en deploy que el directorio de uploads debe tener backup; futuro: migrar a S3 |
| Usuario con facturador=true que no deberia ser facturante | Medium | Solo ADMIN puede cambiar facturador; auditado via AuditLog |
