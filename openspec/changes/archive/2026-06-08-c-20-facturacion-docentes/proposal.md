## Why

Los docentes monotributistas (facturador=true) no se incluyen en la liquidacion general Base+Plus (RN-35). Su pago se gestiona mediante facturas emitidas. Actualmente no existe un modulo para que estos docentes suban sus facturas ni para que FINANZAS las gestione. Esto impide cumplir con F10.5 y separar los flujos contables segun RN-38.

## What Changes

- Nuevo modelo Factura (E20) con estados Pendiente/Abonada
- Endpoint POST /api/docentes/facturas -- subir factura PDF (RF-61)
- Endpoint GET /api/docentes/facturas -- historial del propio docente
- Endpoint GET /api/admin/facturas -- gestion admin con filtros (F10.5)
- Endpoint PUT /api/admin/facturas/{id}/abonar -- marcar abonada + descarga PDF
- Permisos: `facturas:subir` (PROFESOR, TUTOR si facturador=true), `facturas:gestionar` (FINANZAS, ADMIN)
- Validacion: solo usuarios con facturador=true pueden subir facturas
- Integracion con archivos: PDF almacenado con referencia opaca, metadata tamano_kb

## Capabilities

### New Capabilities
- `docente-facturacion`: gestion de facturas de docentes monotributistas -- subida, historial propio, administracion con filtros, marcado como abonada

### Modified Capabilities
- None

## Impact

| Area | Impact | Description |
|------|--------|-------------|
| `app/models/factura.py` | New | Modelo Factura (E20) SQLAlchemy |
| `app/schemas/factura.py` | New | Pydantic schemas request/response |
| `app/repositories/factura.py` | New | Repositorio Factura con filtros y scope tenant |
| `app/services/factura.py` | New | Servicio de facturas con logica de negocio |
| `app/routers/docente/facturas.py` | New | Endpoints para docentes |
| `app/routers/admin/facturas.py` | New | Endpoints para administracion |
| `app/core/permissions.py` | Modified | Nuevos permisos facturas:subir, facturas:gestionar |
| `alembic/versions/XXXX_add_factura.py` | New | Migracion tabla facturas |
| `openspec/specs/docente-facturacion/spec.md` | New | Spec del modulo |
