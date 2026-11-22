"""Excepciones propias del sistema."""


class ErrorSistema(Exception):
    """Base de todos los errores controlados del sistema."""


class ErrorValidacion(ErrorSistema):
    """Un dato ingresado no cumple el formato esperado."""


class DNIDuplicado(ErrorSistema):
    """Ya existe un paciente con ese DNI (CE-02)."""


class NoEncontrado(ErrorSistema):
    """No existe el paciente, médico o ticket solicitado."""


class CupoAgotado(ErrorSistema):
    """No hay cupos disponibles para ese médico, fecha y turno (RF-03)."""


class PermisoDenegado(ErrorSistema):
    """El rol del usuario no permite esa operación (control de acceso por rol)."""


class CredencialesInvalidas(ErrorSistema):
    """Usuario o contraseña incorrectos, o cuenta desactivada."""


class CuentaBloqueada(ErrorSistema):
    """Demasiados intentos fallidos: la cuenta queda bloqueada unos minutos."""
