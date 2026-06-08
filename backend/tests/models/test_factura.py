"""Tests for Factura model (E20) and EstadoFactura enum.

Pure unit tests — no database required.
"""

import pytest

from app.models.factura import EstadoFactura, Factura


class TestEstadoFactura:
    """EstadoFactura enum: Pendiente/Abonada semantics per RN-39."""

    def test_pendiente_is_default(self):
        assert EstadoFactura.PENDIENTE.value == "Pendiente"

    def test_abonada_value(self):
        assert EstadoFactura.ABONADA.value == "Abonada"

    def test_only_two_states(self):
        """RN-39: Only Pendiente and Abonada exist."""
        members = list(EstadoFactura)
        assert len(members) == 2
        assert EstadoFactura.PENDIENTE in members
        assert EstadoFactura.ABONADA in members

    def test_pendiente_not_abonada(self):
        assert EstadoFactura.PENDIENTE != EstadoFactura.ABONADA


class TestFacturaModel:
    """Factura model structure tests — table metadata, columns, defaults."""

    def test_tablename(self):
        assert Factura.__tablename__ == "facturas"

    def test_periodo_column_type(self):
        """periodo is String(7) for YYYY-MM format."""
        col = Factura.__table__.c["periodo"]
        assert col.type.length == 7

    def test_cargada_at_server_default(self):
        """cargada_at should have a server_default (func.now())."""
        col = Factura.__table__.c["cargada_at"]
        assert col.server_default is not None

    def test_referencia_archivo_max_length(self):
        col = Factura.__table__.c["referencia_archivo"]
        assert col.type.length == 500

    def test_detalle_max_length(self):
        col = Factura.__table__.c["detalle"]
        assert col.type.length == 500

    def test_tenant_id_fk(self):
        col = Factura.__table__.c["tenant_id"]
        assert col.foreign_keys

    def test_usuario_id_fk(self):
        col = Factura.__table__.c["usuario_id"]
        assert col.foreign_keys

    def test_estado_default_pendiente_in_column(self):
        """Column definition should have server_default='Pendiente'."""
        col = Factura.__table__.c["estado"]
        assert col.server_default is not None
        # SQLAlchemy server default text should contain 'Pendiente'
        assert "Pendiente" in str(col.server_default.arg)

    def test_tamano_kb_column_exists(self):
        assert hasattr(Factura, "tamano_kb")

    def test_abonada_at_nullable(self):
        col = Factura.__table__.c["abonada_at"]
        assert col.nullable

    def test_indexes_exist(self):
        expected_indexes = {
            "ix_facturas_tenant_periodo",
            "ix_facturas_usuario_id",
            "ix_facturas_tenant_estado",
        }
        actual_indexes = {idx.name for idx in Factura.__table__.indexes}
        assert expected_indexes.issubset(actual_indexes)
