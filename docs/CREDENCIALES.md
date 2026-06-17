# Credenciales de prueba

> Entorno local de desarrollo. Las credenciales se crean al ejecutar el seed inicial.

## Base de datos

| Parametro | Valor |
|-----------|-------|
| Host | `localhost:5432` |
| Base de datos | `activia_trace` |
| Usuario | `activia` |
| Password | `activia` |
| URL completa | `postgresql+asyncpg://activia:activia@localhost:5432/activia_trace` |

## Usuario ADMIN

| Campo | Valor |
|-------|-------|
| Email | `admin@tupad.edu.ar` |
| Password | `admin123456` |
| Rol | ADMIN |
| Tenant | TUPAD |

## Roles disponibles

El seed crea 7 roles dentro del tenant TUPAD:

| Rol | Descripcion |
|-----|-------------|
| ALUMNO | Estudiante que cursa materias |
| TUTOR | Auxiliar / ayudante de catedra |
| PROFESOR | Docente a cargo de una o mas comisiones |
| COORDINADOR | Responsable de un conjunto de materias o cohorte |
| NEXO | Rol de articulacion / enlace transversal |
| ADMIN | Administrador del sistema dentro del tenant |
| FINANZAS | Responsable de liquidaciones y honorarios |

## Endpoints

| Servicio | URL |
|----------|-----|
| API Backend | `http://localhost:8000` |
| API Docs (Swagger) | `http://localhost:8000/docs` |
| Frontend | `http://localhost:5173` (dev) / `http://localhost` (Docker) |
| n8n | `http://localhost:5678` |

## Login

```bash
# Con curl
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@tupad.edu.ar", "password": "admin123456"}'
```

Respuesta esperada:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

## Seguridad

- **JWT**: access token expira en 15 minutos, refresh token rota en cada uso
- **2FA TOTP**: opcional, deshabilitado por defecto para el usuario ADMIN
- **Argon2id**: hashing de passwords
- **AES-256**: cifrado en reposo para datos PII (email, DNI, CUIL, CBU)

**Importante**: las claves `SECRET_KEY` y `ENCRYPTION_KEY` en `backend/.env` son para desarrollo local. En produccion deben reemplazarse por valores seguros.
