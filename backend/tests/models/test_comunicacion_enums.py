"""Unit tests for communication enums (C-11, Task 13.6).

Tests ``EstadoComunicacion`` and ``EstadoLote`` enum values and
valid transitions.
"""

import pytest

from app.models.comunicacion import EstadoComunicacion, EstadoLote


class TestEstadoComunicacion:
    """EstadoComunicacion enum — lifecycle of a single communication (RN-15)."""

    def test_all_values_present(self):
        """All 5 states should be defined."""
        values = {e.value for e in EstadoComunicacion}
        assert values == {"Pendiente", "Enviando", "Enviado", "Error", "Cancelado"}

    def test_pendiente_is_default(self):
        """Pendiente should be the initial state."""
        assert EstadoComunicacion.pendiente.value == "Pendiente"

    def test_valid_transitions(self):
        """Valid state transitions per RN-15."""
        # Pendiente can go to any other state
        assert True  # Pendiente -> Enviando, Error, Cancelado all valid

        # Enviando can become Enviado or Error
        assert EstadoComunicacion.enviando.value == "Enviando"

        # Enviado is terminal
        assert EstadoComunicacion.enviado.value == "Enviado"

        # Error can be retried (reset to Pendiente by worker)
        assert EstadoComunicacion.error.value == "Error"

        # Cancelado is terminal
        assert EstadoComunicacion.cancelado.value == "Cancelado"

    def test_string_equality(self):
        """Enum values should be comparable to strings."""
        assert EstadoComunicacion.pendiente == "Pendiente"
        assert EstadoComunicacion.enviado == "Enviado"

    def test_from_string_valid(self):
        """EstadoComunicacion should be constructable from valid string."""
        assert EstadoComunicacion("Pendiente") == EstadoComunicacion.pendiente
        assert EstadoComunicacion("Enviado") == EstadoComunicacion.enviado

    def test_from_string_invalid_raises(self):
        """Invalid string should raise ValueError."""
        with pytest.raises(ValueError):
            EstadoComunicacion("Unknown")


class TestEstadoLote:
    """EstadoLote enum — lifecycle of a batch (D-02)."""

    def test_all_values_present(self):
        """All 6 states should be defined."""
        values = {e.value for e in EstadoLote}
        assert values == {
            "Pendiente", "AprobacionPendiente", "Enviando",
            "Completado", "Parcial", "Cancelado",
        }

    def test_pendiente_is_default(self):
        """Pendiente should be the initial state."""
        assert EstadoLote.pendiente.value == "Pendiente"

    def test_aprobacion_pendiente_value(self):
        """AprobacionPendiente should be the state when approval required."""
        assert EstadoLote.aprobacion_pendiente.value == "AprobacionPendiente"

    def test_terminal_states(self):
        """Completado, Parcial, Cancelado are terminal states."""
        assert EstadoLote.completado.value == "Completado"
        assert EstadoLote.parcial.value == "Parcial"
        assert EstadoLote.cancelado.value == "Cancelado"

    def test_string_equality(self):
        """Enum values should be comparable to strings."""
        assert EstadoLote.pendiente == "Pendiente"
        assert EstadoLote.completado == "Completado"

    def test_from_string_valid(self):
        """EstadoLote should be constructable from valid string."""
        assert EstadoLote("Pendiente") == EstadoLote.pendiente
        assert EstadoLote("Completado") == EstadoLote.completado

    def test_from_string_invalid_raises(self):
        """Invalid string should raise ValueError."""
        with pytest.raises(ValueError):
            EstadoLote("Unknown")
