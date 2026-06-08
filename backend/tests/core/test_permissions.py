"""Tests for core.permissions — RBAC permissions matrix and require_permission."""

import pytest
from app.core.permissions import ROL_PERMISSIONS, require_permission


class TestPermissionsMatrix:
    """RBAC permissions matrix (Task 6.1)."""

    def test_all_roles_defined(self):
        """All 7 roles should be defined in the matrix."""
        expected_roles = {
            "ALUMNO", "TUTOR", "PROFESOR", "COORDINADOR",
            "ADMIN", "FINANZAS", "NEXO",
        }
        assert set(ROL_PERMISSIONS.keys()) == expected_roles

    def test_aviso_confirmar_all_roles(self):
        """All roles should have aviso:confirmar permission."""
        for role_name, permissions in ROL_PERMISSIONS.items():
            assert "aviso:confirmar" in permissions, (
                f"Role {role_name} should have aviso:confirmar"
            )

    def test_admins_have_tenant_configurar(self):
        """ADMIN role should have tenant:configurar."""
        assert "tenant:configurar" in ROL_PERMISSIONS["ADMIN"]

    def test_finanzas_have_liquidacion_calcular(self):
        """FINANZAS role should have liquidaciones:calcular."""
        assert "liquidaciones:calcular" in ROL_PERMISSIONS["FINANZAS"]

    def test_alumno_has_estado_academico_ver_propio(self):
        """ALUMNO role should have estado_academico:ver_propio."""
        assert "estado_academico:ver_propio" in ROL_PERMISSIONS["ALUMNO"]

    def test_alumno_no_calificaciones_importar(self):
        """ALUMNO should NOT have calificaciones:importar."""
        assert "calificaciones:importar" not in ROL_PERMISSIONS["ALUMNO"]

    def test_profesor_has_calificaciones_importar(self):
        """PROFESOR should have calificaciones:importar."""
        assert "calificaciones:importar" in ROL_PERMISSIONS["PROFESOR"]

    def test_admin_has_facturas_gestionar(self):
        """ADMIN should have facturas:gestionar."""
        assert "facturas:gestionar" in ROL_PERMISSIONS["ADMIN"]

    def test_finanzas_has_facturas_gestionar(self):
        """FINANZAS should have facturas:gestionar."""
        assert "facturas:gestionar" in ROL_PERMISSIONS["FINANZAS"]

    def test_profesor_has_facturas_subir(self):
        """PROFESOR should have facturas:subir."""
        assert "facturas:subir" in ROL_PERMISSIONS["PROFESOR"]

    def test_tutor_has_facturas_subir(self):
        """TUTOR should have facturas:subir."""
        assert "facturas:subir" in ROL_PERMISSIONS["TUTOR"]

    def test_alumno_does_not_have_facturas_subir(self):
        """ALUMNO should NOT have facturas:subir."""
        assert "facturas:subir" not in ROL_PERMISSIONS["ALUMNO"]

    def test_nexo_does_not_have_facturas_subir(self):
        """NEXO should NOT have facturas:subir."""
        assert "facturas:subir" not in ROL_PERMISSIONS["NEXO"]

    def test_nexo_has_minimal_permissions(self):
        """NEXO should have minimal permissions in MVP."""
        nexo_perms = ROL_PERMISSIONS["NEXO"]
        assert "aviso:confirmar" in nexo_perms
        assert "avisos:ver" in nexo_perms
        assert "avisos:ack" in nexo_perms
        # NEXO should NOT have admin permissions
        assert "avisos:publicar" not in nexo_perms

    def test_coordinador_has_equipo_docente_asignar(self):
        """COORDINADOR should have equipo_docente:asignar."""
        assert "equipo_docente:asignar" in ROL_PERMISSIONS["COORDINADOR"]

    def test_estructura_academica_admin_only(self):
        """estructura_academica:gestionar should be ADMIN only."""
        for role_name, permissions in ROL_PERMISSIONS.items():
            if role_name == "ADMIN":
                assert "estructura_academica:gestionar" in permissions
            else:
                assert "estructura_academica:gestionar" not in permissions, (
                    f"Role {role_name} should NOT have estructura_academica:gestionar"
                )


class TestRequirePermission:
    """require_permission dependency factory (Task 6.2)."""

    def test_admin_has_tenant_configurar(self):
        """ADMIN should pass require_permission('tenant:configurar')."""
        checker = require_permission("tenant:configurar")
        # It should not raise for ADMIN
        assert checker(["ADMIN"]) is True

    def test_alumno_lacks_calificaciones_importar(self):
        """ALUMNO should fail require_permission('calificaciones:importar')."""
        checker = require_permission("calificaciones:importar")
        assert checker(["ALUMNO"]) is False

    def test_multiple_roles_union(self):
        """User with ALUMNO+TUTOR should pass if TUTOR has the permission."""
        checker = require_permission("atrasados:ver")
        # TUTOR has atrasados:ver, so union should pass
        assert checker(["ALUMNO", "TUTOR"]) is True

    def test_no_roles_fails(self):
        """User with empty roles should fail any permission check."""
        checker = require_permission("aviso:confirmar")
        assert checker([]) is False

    def test_unknown_role_ignored(self):
        """Unknown roles should be ignored (not crash)."""
        checker = require_permission("aviso:confirmar")
        assert checker(["UNKNOWN_ROLE"]) is False

    def test_rol_finanzas_has_liquidacion_cerrar(self):
        """FINANZAS should pass require_permission('liquidaciones:cerrar')."""
        checker = require_permission("liquidaciones:cerrar")
        assert checker(["FINANZAS"]) is True

    def test_admin_lacks_liquidacion_cerrar(self):
        """ADMIN should fail require_permission('liquidaciones:cerrar')."""
        checker = require_permission("liquidaciones:cerrar")
        assert checker(["ADMIN"]) is False

    def test_rol_no_existente_no_crashea(self):
        """A role not in the matrix should be silently ignored."""
        checker = require_permission("aviso:confirmar")
        assert checker(["NEXO_EXTRAÑO"]) is False

    # ── Task 1.1: equipo_docente:ver permission ───────────────────────

    def test_coordinador_has_equipo_docente_ver(self):
        """COORDINADOR should have equipo_docente:ver (Task 1.1)."""
        assert "equipo_docente:ver" in ROL_PERMISSIONS["COORDINADOR"]

    def test_admin_has_equipo_docente_ver(self):
        """ADMIN should have equipo_docente:ver (Task 1.1)."""
        assert "equipo_docente:ver" in ROL_PERMISSIONS["ADMIN"]

    def test_profesor_lacks_equipo_docente_asignar(self):
        """PROFESOR should NOT have equipo_docente:asignar."""
        assert "equipo_docente:asignar" not in ROL_PERMISSIONS["PROFESOR"]

    def test_profesor_lacks_equipo_docente_ver(self):
        """PROFESOR should NOT have equipo_docente:ver."""
        assert "equipo_docente:ver" not in ROL_PERMISSIONS["PROFESOR"]


class TestCommunicationPermissions:
    """comunicacion permissions (C-11, Task 1.1-1.2)."""

    def test_profesor_has_comunicacion_enviar(self):
        """PROFESOR should have comunicacion:enviar."""
        assert "comunicacion:enviar" in ROL_PERMISSIONS["PROFESOR"]

    def test_coordinador_has_comunicacion_enviar(self):
        """COORDINADOR should have comunicacion:enviar."""
        assert "comunicacion:enviar" in ROL_PERMISSIONS["COORDINADOR"]

    def test_admin_has_comunicacion_enviar(self):
        """ADMIN should have comunicacion:enviar."""
        assert "comunicacion:enviar" in ROL_PERMISSIONS["ADMIN"]

    def test_alumno_lacks_comunicacion_enviar(self):
        """ALUMNO should NOT have comunicacion:enviar."""
        assert "comunicacion:enviar" not in ROL_PERMISSIONS["ALUMNO"]

    def test_coordinador_has_comunicacion_aprobar(self):
        """COORDINADOR should have comunicacion:aprobar."""
        assert "comunicacion:aprobar" in ROL_PERMISSIONS["COORDINADOR"]

    def test_admin_has_comunicacion_aprobar(self):
        """ADMIN should have comunicacion:aprobar."""
        assert "comunicacion:aprobar" in ROL_PERMISSIONS["ADMIN"]

    def test_profesor_lacks_comunicacion_aprobar(self):
        """PROFESOR should NOT have comunicacion:aprobar."""
        assert "comunicacion:aprobar" not in ROL_PERMISSIONS["PROFESOR"]

    def test_require_permission_enviar(self):
        """require_permission('comunicacion:enviar') should pass for PROFESOR."""
        checker = require_permission("comunicacion:enviar")
        assert checker(["PROFESOR"]) is True

    def test_require_permission_enviar_rejected(self):
        """require_permission('comunicacion:enviar') should fail for ALUMNO."""
        checker = require_permission("comunicacion:enviar")
        assert checker(["ALUMNO"]) is False

    def test_require_permission_aprobar(self):
        """require_permission('comunicacion:aprobar') should pass for ADMIN."""
        checker = require_permission("comunicacion:aprobar")
        assert checker(["ADMIN"]) is True

    def test_require_permission_aprobar_rejected(self):
        """require_permission('comunicacion:aprobar') should fail for PROFESOR."""
        checker = require_permission("comunicacion:aprobar")
        assert checker(["PROFESOR"]) is False


class TestEncuentroPermissions:
    """encuentros permissions (C-14, Task 6.1)."""

    def test_profesor_has_encuentros_crear(self):
        """PROFESOR should have encuentros:crear."""
        assert "encuentros:crear" in ROL_PERMISSIONS["PROFESOR"]

    def test_profesor_has_encuentros_editar(self):
        """PROFESOR should have encuentros:editar."""
        assert "encuentros:editar" in ROL_PERMISSIONS["PROFESOR"]

    def test_coordinador_has_encuentros_ver_todas(self):
        """COORDINADOR should have encuentros:ver_todas."""
        assert "encuentros:ver_todas" in ROL_PERMISSIONS["COORDINADOR"]

    def test_admin_has_encuentros_ver_todas(self):
        """ADMIN should have encuentros:ver_todas."""
        assert "encuentros:ver_todas" in ROL_PERMISSIONS["ADMIN"]

    def test_profesor_lacks_encuentros_ver_todas(self):
        """PROFESOR should NOT have encuentros:ver_todas."""
        assert "encuentros:ver_todas" not in ROL_PERMISSIONS["PROFESOR"]

    def test_alumno_lacks_encuentros_crear(self):
        """ALUMNO should NOT have encuentros:crear."""
        assert "encuentros:crear" not in ROL_PERMISSIONS["ALUMNO"]

    def test_require_permission_encuentros_crear_profesor(self):
        """require_permission('encuentros:crear') should pass for PROFESOR."""
        checker = require_permission("encuentros:crear")
        assert checker(["PROFESOR"]) is True

    def test_require_permission_encuentros_crear_alumno(self):
        """require_permission('encuentros:crear') should fail for ALUMNO."""
        checker = require_permission("encuentros:crear")
        assert checker(["ALUMNO"]) is False


class TestGuardiaPermissions:
    """guardias permissions (C-14, Task 6.1)."""

    def test_profesor_has_guardias_registrar(self):
        """PROFESOR should have guardias:registrar."""
        assert "guardias:registrar" in ROL_PERMISSIONS["PROFESOR"]

    def test_tutor_has_guardias_registrar(self):
        """TUTOR should have guardias:registrar."""
        assert "guardias:registrar" in ROL_PERMISSIONS["TUTOR"]

    def test_coordinador_has_guardias_ver_todas(self):
        """COORDINADOR should have guardias:ver_todas."""
        assert "guardias:ver_todas" in ROL_PERMISSIONS["COORDINADOR"]

    def test_admin_has_guardias_ver_todas(self):
        """ADMIN should have guardias:ver_todas."""
        assert "guardias:ver_todas" in ROL_PERMISSIONS["ADMIN"]

    def test_profesor_lacks_guardias_ver_todas(self):
        """PROFESOR should NOT have guardias:ver_todas."""
        assert "guardias:ver_todas" not in ROL_PERMISSIONS["PROFESOR"]

    def test_alumno_lacks_guardias_registrar(self):
        """ALUMNO should NOT have guardias:registrar."""
        assert "guardias:registrar" not in ROL_PERMISSIONS["ALUMNO"]

    def test_require_permission_guardias_registrar_profesor(self):
        """require_permission('guardias:registrar') should pass for PROFESOR."""
        checker = require_permission("guardias:registrar")
        assert checker(["PROFESOR"]) is True

    def test_require_permission_guardias_registrar_alumno(self):
        """require_permission('guardias:registrar') should fail for ALUMNO."""
        checker = require_permission("guardias:registrar")
        assert checker(["ALUMNO"]) is False
