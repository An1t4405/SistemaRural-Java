"""Usuarios, roles y permisos (control de acceso basado en roles, RD-02).

- Cada ROL agrupa un conjunto de PERMISOS; el sistema pregunta por permisos, no por roles.
- Las contraseñas nunca se guardan: solo su hash PBKDF2-HMAC-SHA256 con sal aleatoria.
- Tras MAX_INTENTOS fallos la cuenta se bloquea MINUTOS_BLOQUEO minutos.
"""
import hashlib
import hmac
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from .errores import ErrorValidacion

ITERACIONES = 600_000
MAX_INTENTOS = 5
MINUTOS_BLOQUEO = 5
GRUPO_ADMIN = "Administrativo"
GRUPO_ASISTENCIAL = "Asistencial"


class Permiso(Enum):
    """Cada permiso es una acción concreta; su valor es el texto que ve el usuario."""
    PACIENTES_VER = "Consultar pacientes"
    PACIENTES_REGISTRAR = "Registrar pacientes nuevos"
    PACIENTES_EDITAR = "Actualizar datos de pacientes"
    HISTORIA_VER = "Ver historias clínicas"
    HISTORIA_EDITAR = "Registrar alergias y antecedentes"
    ATENCION_REGISTRAR = "Registrar atenciones y diagnósticos (CIE-10)"
    PROFESIONALES_VER = "Consultar profesionales de salud"
    PROFESIONALES_GESTIONAR = "Registrar profesionales de salud"
    CITAS_VER = "Consultar citas, turnos y cupos"
    CITAS_GESTIONAR = "Agendar y cancelar citas"
    TICKETS_EMITIR = "Emitir tickets de turno"
    TICKETS_ESTADO = "Actualizar el estado de los turnos"
    REPORTES_VER = "Generar reportes de atención"
    USUARIOS_GESTIONAR = "Administrar usuarios y roles"


@dataclass(frozen=True)
class Rol:
    codigo: str
    nombre: str
    grupo: str
    descripcion: str
    permisos: frozenset


_P = Permiso
# Conjunto base del personal que atiende pacientes (sin reportes)
_CLINICO = frozenset({_P.PACIENTES_VER, _P.HISTORIA_VER, _P.HISTORIA_EDITAR, _P.ATENCION_REGISTRAR,
                      _P.PROFESIONALES_VER, _P.CITAS_VER, _P.TICKETS_ESTADO})

_ROLES = (
    # ---------------------------------------------------------------- administrativo
    Rol("ADMIN", "Administrador del sistema", GRUPO_ADMIN,
        "Administra el sistema, registra profesionales, gestiona citas y turnos y consulta reportes. "
        "No accede a las historias clínicas.",
        # En una posta pequeña, el administrador también puede registrar y corregir
        # datos demográficos de pacientes. El acceso a historias clínicas sigue restringido.
        frozenset({_P.USUARIOS_GESTIONAR, _P.PROFESIONALES_VER, _P.PROFESIONALES_GESTIONAR,
                   _P.PACIENTES_VER, _P.PACIENTES_REGISTRAR, _P.PACIENTES_EDITAR,
                   _P.CITAS_VER, _P.CITAS_GESTIONAR, _P.TICKETS_EMITIR, _P.TICKETS_ESTADO, _P.REPORTES_VER})),
    Rol("JEFE", "Jefe del establecimiento", GRUPO_ADMIN,
        "Supervisa la posta: consulta pacientes, profesionales, citas y reportes. No modifica datos.",
        frozenset({_P.PACIENTES_VER, _P.PROFESIONALES_VER, _P.CITAS_VER, _P.REPORTES_VER})),
    Rol("ADMISION", "Admisión (personal administrativo)", GRUPO_ADMIN,
        "Recibe y registra a los pacientes, agenda y cancela citas y emite los tickets de turno.",
        frozenset({_P.PACIENTES_VER, _P.PACIENTES_REGISTRAR, _P.PACIENTES_EDITAR, _P.PROFESIONALES_VER,
                   _P.CITAS_VER, _P.CITAS_GESTIONAR, _P.TICKETS_EMITIR, _P.TICKETS_ESTADO})),
    Rol("ESTADISTICA", "Estadística e informática", GRUPO_ADMIN,
        "Consulta pacientes y genera los reportes de atención para los informes del establecimiento.",
        frozenset({_P.PACIENTES_VER, _P.PROFESIONALES_VER, _P.CITAS_VER, _P.REPORTES_VER})),
    # ---------------------------------------------------------------- asistencial
    Rol("MEDICO", "Médico(a)", GRUPO_ASISTENCIAL,
        "Atiende consultas: revisa y completa la historia clínica, registra atenciones con diagnóstico "
        "CIE-10 y genera reportes.",
        _CLINICO | {_P.REPORTES_VER}),
    Rol("OBSTETRA", "Obstetra", GRUPO_ASISTENCIAL,
        "Atiende control prenatal, planificación familiar y partos: revisa la historia clínica, registra "
        "sus atenciones y genera reportes.",
        _CLINICO | {_P.REPORTES_VER}),
    Rol("ENFERMERA", "Enfermero(a)", GRUPO_ASISTENCIAL,
        "Realiza triaje, procedimientos y controles (CRED, vacunas): revisa la historia clínica, registra "
        "alergias y antecedentes y sus atenciones.",
        _CLINICO),
    Rol("ODONTOLOGO", "Odontólogo(a)", GRUPO_ASISTENCIAL,
        "Atiende la salud bucal: revisa la historia clínica y registra sus atenciones.", _CLINICO),
    Rol("PSICOLOGO", "Psicólogo(a)", GRUPO_ASISTENCIAL,
        "Atiende salud mental: revisa la historia clínica y registra sus atenciones.", _CLINICO),
    Rol("NUTRICIONISTA", "Nutricionista", GRUPO_ASISTENCIAL,
        "Atiende consejería nutricional: revisa la historia clínica y registra sus atenciones.", _CLINICO),
    Rol("TEC_ENFERMERIA", "Técnico(a) de enfermería", GRUPO_ASISTENCIAL,
        "Apoya a enfermería: consulta pacientes y citas y actualiza el estado de los turnos (en atención, "
        "completado). No accede a la historia clínica.",
        frozenset({_P.PACIENTES_VER, _P.PROFESIONALES_VER, _P.CITAS_VER, _P.TICKETS_ESTADO})),
    Rol("TEC_LABORATORIO", "Técnico(a) de laboratorio", GRUPO_ASISTENCIAL,
        "Consulta los datos del paciente y sus citas para identificar a quien se toman las muestras. "
        "No accede a la historia clínica.",
        frozenset({_P.PACIENTES_VER, _P.PROFESIONALES_VER, _P.CITAS_VER})),
    Rol("TEC_FARMACIA", "Técnico(a) de farmacia", GRUPO_ASISTENCIAL,
        "Consulta los datos del paciente y sus citas para la entrega de medicamentos. "
        "No accede a la historia clínica.",
        frozenset({_P.PACIENTES_VER, _P.PROFESIONALES_VER, _P.CITAS_VER})),
)
ROLES: dict[str, Rol] = {r.codigo: r for r in _ROLES}


# ----------------------------------------------------------------- contraseñas
def validar_nombre_usuario(nombre) -> str:
    n = str(nombre).strip().lower()
    if not (4 <= len(n) <= 20) or not all(c.isascii() and (c.isalnum() or c in "._") for c in n):
        raise ErrorValidacion("El usuario debe tener de 4 a 20 caracteres: letras, números, punto o guion bajo "
                              "(sin espacios ni tildes).")
    return n


def validar_clave_segura(clave, nombre_usuario: str = "") -> str:
    clave = str(clave)
    if len(clave) < 8:
        raise ErrorValidacion("La contraseña debe tener al menos 8 caracteres.")
    if len(clave) > 128:
        raise ErrorValidacion("La contraseña es demasiado larga (máximo 128 caracteres).")
    if not (any(c.isalpha() for c in clave) and any(c.isdigit() for c in clave)):
        raise ErrorValidacion("La contraseña debe combinar letras y números.")
    if nombre_usuario and clave.lower() == str(nombre_usuario).strip().lower():
        raise ErrorValidacion("La contraseña no puede ser igual al nombre de usuario.")
    return clave


def hashear_clave(clave: str) -> str:
    sal = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), sal, ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${sal.hex()}${h.hex()}"


def verificar_clave(clave: str, almacenado: str) -> bool:
    try:
        algoritmo, iteraciones, sal, esperado = almacenado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        h = hashlib.pbkdf2_hmac("sha256", clave.encode("utf-8"), bytes.fromhex(sal), int(iteraciones))
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(h.hex(), esperado)


def _obligatorio(valor, campo):
    valor = str(valor).strip()
    if not valor:
        raise ErrorValidacion(f"El campo «{campo}» es obligatorio.")
    return valor


# ----------------------------------------------------------------- usuario
class Usuario:
    """Cuenta de acceso. La colegiatura (CMP/COP/CEP...) la vincula con un profesional registrado."""

    def __init__(self, nombre_usuario, nombres, apellidos, rol_codigo, clave_hash, colegiatura="",
                 activo=True, debe_cambiar_clave=False, ultimo_acceso: datetime | None = None,
                 intentos_fallidos=0, bloqueado_hasta: datetime | None = None):
        if rol_codigo not in ROLES:
            raise ErrorValidacion("Rol desconocido.")
        self._nombre_usuario = validar_nombre_usuario(nombre_usuario)
        self._nombres = _obligatorio(nombres, "nombres")
        self._apellidos = _obligatorio(apellidos, "apellidos")
        self._rol = rol_codigo
        self._clave_hash = clave_hash
        self._colegiatura = str(colegiatura).strip()
        self._activo = bool(activo)
        self._debe_cambiar = bool(debe_cambiar_clave)
        self._ultimo_acceso = ultimo_acceso
        self._intentos = int(intentos_fallidos)
        self._bloqueado_hasta = bloqueado_hasta

    # consultas
    def get_nombre_usuario(self): return self._nombre_usuario
    def get_nombres(self): return self._nombres
    def get_apellidos(self): return self._apellidos
    def nombre_completo(self): return f"{self._apellidos}, {self._nombres}"
    def get_rol(self) -> Rol: return ROLES[self._rol]
    def get_colegiatura(self): return self._colegiatura
    def esta_activo(self): return self._activo
    def debe_cambiar_clave(self): return self._debe_cambiar
    def get_ultimo_acceso(self): return self._ultimo_acceso
    def tiene_permiso(self, permiso: Permiso) -> bool: return permiso in ROLES[self._rol].permisos
    def verificar(self, clave: str) -> bool: return verificar_clave(clave, self._clave_hash)

    def bloqueado(self, ahora: datetime) -> bool:
        return self._bloqueado_hasta is not None and ahora < self._bloqueado_hasta

    def get_bloqueado_hasta(self): return self._bloqueado_hasta

    # cambios
    def set_rol(self, rol_codigo):
        if rol_codigo not in ROLES:
            raise ErrorValidacion("Rol desconocido.")
        self._rol = rol_codigo

    def set_activo(self, activo: bool):
        self._activo = bool(activo)

    def set_clave_hash(self, clave_hash: str, temporal: bool = False):
        self._clave_hash = clave_hash
        self._debe_cambiar = temporal

    def registrar_acceso(self, ahora: datetime):
        self._ultimo_acceso, self._intentos, self._bloqueado_hasta = ahora, 0, None

    def registrar_fallo(self, ahora: datetime) -> int:
        """Suma un intento fallido; devuelve los intentos que quedan (0 = cuenta bloqueada)."""
        self._intentos += 1
        if self._intentos >= MAX_INTENTOS:
            self._bloqueado_hasta = ahora + timedelta(minutes=MINUTOS_BLOQUEO)
            self._intentos = 0
            return 0
        return MAX_INTENTOS - self._intentos

    def desbloquear(self):
        self._intentos, self._bloqueado_hasta = 0, None

    # persistencia (el archivo completo ya va cifrado)
    def to_dict(self):
        iso = lambda d: d.isoformat() if d else None  # noqa: E731
        return {"usuario": self._nombre_usuario, "nombres": self._nombres, "apellidos": self._apellidos,
                "rol": self._rol, "clave_hash": self._clave_hash, "colegiatura": self._colegiatura,
                "activo": self._activo, "debe_cambiar_clave": self._debe_cambiar,
                "ultimo_acceso": iso(self._ultimo_acceso), "intentos_fallidos": self._intentos,
                "bloqueado_hasta": iso(self._bloqueado_hasta)}

    @classmethod
    def from_dict(cls, d):
        leer = lambda v: datetime.fromisoformat(v) if v else None  # noqa: E731
        return cls(d["usuario"], d["nombres"], d["apellidos"], d["rol"], d["clave_hash"],
                   d.get("colegiatura", ""), d.get("activo", True), d.get("debe_cambiar_clave", False),
                   leer(d.get("ultimo_acceso")), d.get("intentos_fallidos", 0), leer(d.get("bloqueado_hasta")))
