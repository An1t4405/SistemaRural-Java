"""Validación de fechas: formato, existencia en el calendario y reglas de negocio.

En pantalla se escribe DD/MM/AAAA (formato peruano); también se acepta AAAA-MM-DD.
Las reglas (nacimiento, citas, atenciones, reportes) viven aquí para que las use
tanto la interfaz como el dominio y las pruebas.
"""
import re
from datetime import date, datetime, timedelta

from .errores import ErrorValidacion

EDAD_MAXIMA = 120      # años: más que eso se considera un error de digitación
MAX_DIAS_CITA = 90     # no se agenda con más de 90 días de anticipación

_DMA = re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$")
_AMD = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})$")


def parsear_fecha(texto, campo: str = "Fecha") -> date:
    """Convierte texto en fecha o lanza ErrorValidacion con un mensaje claro."""
    t = str(texto).strip()
    if not t:
        raise ErrorValidacion(f"«{campo}»: ingrese la fecha en formato DD/MM/AAAA (ej. 17/05/1990).")
    m = _DMA.match(t)
    if m:
        dia, mes, anio = map(int, m.groups())
    else:
        m = _AMD.match(t)
        if not m:
            raise ErrorValidacion(f"«{campo}»: formato inválido ({t}). Use DD/MM/AAAA (ej. 17/05/1990).")
        anio, mes, dia = map(int, m.groups())
    try:
        return date(anio, mes, dia)
    except ValueError:
        raise ErrorValidacion(f"«{campo}»: la fecha {t} no existe en el calendario (revise el día y el mes).") from None


def formatear(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def formatear_fecha_hora(dt: datetime | None) -> str:
    return dt.strftime("%d/%m/%Y %H:%M") if dt else "—"


def edad_en(nacimiento: date, hoy: date) -> int:
    return hoy.year - nacimiento.year - ((hoy.month, hoy.day) < (nacimiento.month, nacimiento.day))


def validar_nacimiento(d: date, hoy: date | None = None) -> date:
    hoy = hoy or date.today()
    if d > hoy:
        raise ErrorValidacion("La fecha de nacimiento no puede ser futura.")
    if edad_en(d, hoy) > EDAD_MAXIMA:
        raise ErrorValidacion(f"La fecha de nacimiento no es creíble: la edad superaría los {EDAD_MAXIMA} años.")
    return d


def validar_fecha_cita(d: date, hoy: date | None = None) -> date:
    hoy = hoy or date.today()
    if d < hoy:
        raise ErrorValidacion("No se puede agendar una cita en una fecha pasada.")
    if d.weekday() == 6:
        raise ErrorValidacion("La posta médica no atiende los domingos. Seleccione una fecha de lunes a sábado.")
    limite = hoy + timedelta(days=MAX_DIAS_CITA)
    if d > limite:
        raise ErrorValidacion(f"Solo se agenda con hasta {MAX_DIAS_CITA} días de anticipación (hasta el {formatear(limite)}).")
    return d


def validar_fecha_atencion(d: date, nacimiento: date, hoy: date | None = None) -> date:
    hoy = hoy or date.today()
    if d > hoy:
        raise ErrorValidacion("La fecha de la atención no puede ser futura.")
    if d < nacimiento:
        raise ErrorValidacion("La fecha de la atención no puede ser anterior al nacimiento del paciente.")
    return d


def validar_fecha_reporte(d: date, hoy: date | None = None) -> date:
    hoy = hoy or date.today()
    if d > hoy:
        raise ErrorValidacion("La fecha de referencia del reporte no puede ser futura.")
    return d
