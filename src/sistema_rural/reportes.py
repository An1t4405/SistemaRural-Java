"""Reportes de atención (RF-06) con estilo funcional (DD-02, DM-02).

Solo leen la colección de atenciones: usan filter/map/reduce y lambdas,
sin modificar las historias clínicas.
"""
from abc import ABC, abstractmethod
from datetime import date, timedelta
from functools import reduce

from .errores import ErrorValidacion


def _acumular(conteo: dict, codigo: str) -> dict:
    conteo[codigo] = conteo.get(codigo, 0) + 1
    return conteo


class Reporte(ABC):
    nombre = "Reporte"

    def __init__(self, atenciones):
        self._atenciones = tuple(atenciones)

    @abstractmethod
    def rango(self, ref: date) -> tuple[date, date]: ...

    def generar(self, ref: date) -> dict:
        ini, fin = self.rango(ref)
        en_rango = tuple(filter(lambda a: ini <= a.get_fecha() <= fin, self._atenciones))
        codigos = map(lambda a: a.get_diagnostico(), en_rango)
        conteo = reduce(_acumular, codigos, {})
        ranking = sorted(conteo.items(), key=lambda kv: (-kv[1], kv[0]))
        return {"tipo": self.nombre, "desde": ini, "hasta": fin, "total_atenciones": len(en_rango),
                "patologias_frecuentes": ranking[:5]}


class ReporteDiario(Reporte):
    nombre = "Diario"
    def rango(self, ref): return ref, ref


class ReporteSemanal(Reporte):
    nombre = "Semanal"
    def rango(self, ref):
        lunes = ref - timedelta(days=ref.weekday())
        return lunes, lunes + timedelta(days=6)


class ReporteMensual(Reporte):
    nombre = "Mensual"
    def rango(self, ref):
        ini = ref.replace(day=1)
        siguiente = (ini + timedelta(days=32)).replace(day=1)
        return ini, siguiente - timedelta(days=1)


class ReporteFactory:
    """Factory: crea el reporte según el tipo, sin que el cliente conozca las clases."""

    _tipos = {"diario": ReporteDiario, "semanal": ReporteSemanal, "mensual": ReporteMensual}

    @classmethod
    def tipos_disponibles(cls): return tuple(cls._tipos)

    @classmethod
    def crear(cls, tipo: str, atenciones) -> Reporte:
        try:
            return cls._tipos[tipo.lower()](atenciones)
        except KeyError:
            raise ErrorValidacion(f"Tipo de reporte desconocido: {tipo}") from None
