# app/result.py
"""
ScrapingResult — Dataclass tipado que reemplaza al dict devuelto por procesar_aplicacion().

Ventajas sobre dict:
  - Autocompletado e inspección de tipos
  - Sin .get() con defaults manuales
  - Métodos helper (has_errors, has_uncontrolled, etc.)
  - Backward-compatible a través de __getitem__ y to_dict()
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class ScrapingResult:
    """
    Resultado de procesar una aplicación: errores clasificados y separados
    en nuevos vs. ya avisados anteriormente.
    """

    app_key: str
    app_name: str
    dia: date
    fecha_str: str

    no_controlados_nuevos: list[str] = field(default_factory=list)
    no_controlados_avisados: list[str] = field(default_factory=list)
    controlados_nuevos: list[str] = field(default_factory=list)
    controlados_avisados: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------ helpers

    def has_errors(self) -> bool:
        """True si hay al menos un error (controlado o no), nuevo o avisado."""
        return bool(
            self.no_controlados_nuevos
            or self.no_controlados_avisados
            or self.controlados_nuevos
            or self.controlados_avisados
        )

    def has_uncontrolled(self) -> bool:
        """True si hay errores no-controlados (nuevos o avisados)."""
        return bool(self.no_controlados_nuevos or self.no_controlados_avisados)

    def has_new_errors(self) -> bool:
        """True si hay errores nuevos (de cualquier tipo) que aún no fueron avisados."""
        return bool(self.no_controlados_nuevos or self.controlados_nuevos)

    @property
    def total_no_controlados(self) -> int:
        return len(self.no_controlados_nuevos) + len(self.no_controlados_avisados)

    @property
    def total_controlados(self) -> int:
        return len(self.controlados_nuevos) + len(self.controlados_avisados)

    # ------------------------------------------------ backward-compatibility ---

    def to_dict(self) -> dict:
        """
        Serialización a dict para código externo que todavía usa
        resultado.get("no_controlados_nuevos", []).
        """
        return {
            "app_key": self.app_key,
            "app_name": self.app_name,
            "dia": self.dia,
            "fecha_str": self.fecha_str,
            "no_controlados_nuevos": self.no_controlados_nuevos,
            "no_controlados_avisados": self.no_controlados_avisados,
            "controlados_nuevos": self.controlados_nuevos,
            "controlados_avisados": self.controlados_avisados,
        }

    def __getitem__(self, key: str):
        """Permite resultado["app_key"] igual que un dict (backward-compat)."""
        return self.to_dict()[key]

    def get(self, key: str, default=None):
        """Permite resultado.get("app_key", ...) igual que un dict (backward-compat)."""
        return self.to_dict().get(key, default)
