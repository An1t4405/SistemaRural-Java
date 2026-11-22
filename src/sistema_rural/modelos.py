"""Clases del dominio (DD-01): POO con atributos privados y getters/setters.

Convención: los atributos se escriben con guion bajo (-atributo en el UML) y
se acceden solo mediante get_/set_. Los datos sensibles se guardan cifrados.
"""
import re
import threading
import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta

from . import fechas, seguridad
from .errores import CupoAgotado, ErrorValidacion

TURNOS = ("MAÑANA", "TARDE")
ESTADOS_TICKET = ("RESERVADO", "EN_ATENCION", "COMPLETADO", "NO_ASISTIO")
_CIE10 = re.compile(r"^[A-TV-Z]\d{2}(\.\d{1,2})?$")


def _texto_obligatorio(valor: str, campo: str) -> str:
    valor = str(valor).strip()
    if not valor:
        raise ErrorValidacion(f"El campo «{campo}» es obligatorio.")
    return valor


# ----------------------------------------------------------------- Personas
class Persona(ABC):
    """Datos comunes de pacientes y médicos. El DNI nunca queda en texto plano."""

    def __init__(self, dni, nombres, apellidos, telefono="", tipo_documento="DNI"):
        tipo_documento, dni = seguridad.validar_documento(tipo_documento, dni)
        c = seguridad.cifrador()
        self._dni_cifrado = c.cifrar(dni)
        self._tipo_documento = tipo_documento
        self._dni_hash = c.hash_documento(tipo_documento, dni)
        self._nombres = _texto_obligatorio(nombres, "nombres")
        self._apellidos = _texto_obligatorio(apellidos, "apellidos")
        self._telefono = str(telefono).strip()

    # getters / setters
    def get_nombres(self): return self._nombres
    def set_nombres(self, v): self._nombres = _texto_obligatorio(v, "nombres")
    def get_apellidos(self): return self._apellidos
    def set_apellidos(self, v): self._apellidos = _texto_obligatorio(v, "apellidos")
    def get_telefono(self): return self._telefono
    def set_telefono(self, v): self._telefono = str(v).strip()
    def get_dni_hash(self): return self._dni_hash
    def get_tipo_documento(self): return self._tipo_documento
    def get_numero_documento(self): return self._get_dni()
    def nombre_completo(self): return f"{self._apellidos}, {self._nombres}"

    def _get_dni(self) -> str:
        """Uso interno (persistencia). La interfaz usa get_dni_enmascarado()."""
        return seguridad.cifrador().descifrar(self._dni_cifrado)

    def get_dni_enmascarado(self) -> str:
        return seguridad.enmascarar_dni(self._get_dni())

    def coincide_dni(self, dni: str) -> bool:
        return self.coincide_documento("DNI", dni)

    def coincide_documento(self, tipo: str, numero: str) -> bool:
        """Compara por hash, sin exponer el número."""
        try:
            tipo, numero = seguridad.validar_documento(tipo, numero)
        except ErrorValidacion:
            return False
        return self._dni_hash == seguridad.cifrador().hash_documento(tipo, numero)

    @abstractmethod
    def rol(self) -> str: ...


class Medico(Persona):
    def __init__(self, dni, nombres, apellidos, cmp, especialidad, telefono=""):
        super().__init__(dni, nombres, apellidos, telefono)
        self._cmp = _texto_obligatorio(cmp, "CMP")
        self._especialidad = _texto_obligatorio(especialidad, "especialidad")

    def get_cmp(self): return self._cmp
    def get_especialidad(self): return self._especialidad
    def rol(self): return "Médico"

    def to_dict(self):
        return {"dni": self._get_dni(), "nombres": self._nombres, "apellidos": self._apellidos,
                "telefono": self._telefono, "cmp": self._cmp, "especialidad": self._especialidad}

    @classmethod
    def from_dict(cls, d):
        return cls(d["dni"], d["nombres"], d["apellidos"], d["cmp"], d["especialidad"], d.get("telefono", ""))


class Atencion:
    """Una consulta registrada: fecha, motivo y diagnóstico CIE-10 (cifrado)."""

    def __init__(self, fecha: date, motivo: str, diagnostico_cie10: str, cmp_medico: str):
        diag = str(diagnostico_cie10).strip().upper()
        if not _CIE10.fullmatch(diag):
            raise ErrorValidacion("Diagnóstico inválido: use un código CIE-10 (ej. J00 o E11.9).")
        self._fecha = fecha
        self._motivo = _texto_obligatorio(motivo, "motivo")
        self._diagnostico = seguridad.cifrador().cifrar(diag)
        self._cmp_medico = cmp_medico

    def get_fecha(self): return self._fecha
    def get_motivo(self): return self._motivo
    def get_cmp_medico(self): return self._cmp_medico
    def get_diagnostico(self): return seguridad.cifrador().descifrar(self._diagnostico)

    def to_dict(self):
        return {"fecha": self._fecha.isoformat(), "motivo": self._motivo,
                "diagnostico": self.get_diagnostico(), "cmp_medico": self._cmp_medico}

    @classmethod
    def from_dict(cls, d):
        return cls(date.fromisoformat(d["fecha"]), d["motivo"], d["diagnostico"], d["cmp_medico"])


class HistoriaClinica:
    """Alergias, antecedentes (cifrados) y lista de atenciones. Vive dentro del Paciente."""

    def __init__(self, alergias="", antecedentes=""):
        self._alergias = ""
        self._antecedentes = ""
        self._atenciones: list[Atencion] = []
        self.set_alergias(alergias)
        self.set_antecedentes(antecedentes)

    def get_alergias(self): return seguridad.cifrador().descifrar(self._alergias)
    def set_alergias(self, v): self._alergias = seguridad.cifrador().cifrar(str(v).strip())
    def get_antecedentes(self): return seguridad.cifrador().descifrar(self._antecedentes)
    def set_antecedentes(self, v): self._antecedentes = seguridad.cifrador().cifrar(str(v).strip())
    def get_atenciones(self): return tuple(self._atenciones)
    def agregar_atencion(self, atencion: Atencion): self._atenciones.append(atencion)

    def to_dict(self):
        return {"alergias": self.get_alergias(), "antecedentes": self.get_antecedentes(),
                "atenciones": [a.to_dict() for a in self._atenciones]}

    @classmethod
    def from_dict(cls, d):
        h = cls(d.get("alergias", ""), d.get("antecedentes", ""))
        for a in d.get("atenciones", []):
            h.agregar_atencion(Atencion.from_dict(a))
        return h


class Paciente(Persona):
    def __init__(self, dni, nombres, apellidos, fecha_nacimiento: date, direccion="", telefono="", tipo_documento="DNI"):
        super().__init__(dni, nombres, apellidos, telefono, tipo_documento)
        self._fecha_nacimiento = fechas.validar_nacimiento(fecha_nacimiento)
        self._direccion = str(direccion).strip()
        self._historia = HistoriaClinica()  # composición: nace y muere con el paciente

    def get_fecha_nacimiento(self): return self._fecha_nacimiento
    def get_direccion(self): return self._direccion
    def set_direccion(self, v): self._direccion = str(v).strip()
    def get_historia(self): return self._historia
    def rol(self): return "Paciente"

    def edad(self, hoy: date | None = None) -> int:
        hoy = hoy or date.today()
        n = self._fecha_nacimiento
        return hoy.year - n.year - ((hoy.month, hoy.day) < (n.month, n.day))

    def to_dict(self):
        return {"dni": self._get_dni(), "tipo_documento": self._tipo_documento, "nombres": self._nombres, "apellidos": self._apellidos,
                "telefono": self._telefono, "fecha_nacimiento": self._fecha_nacimiento.isoformat(),
                "direccion": self._direccion, "historia": self._historia.to_dict()}

    @classmethod
    def from_dict(cls, d):
        p = cls(d["dni"], d["nombres"], d["apellidos"], date.fromisoformat(d["fecha_nacimiento"]),
                d.get("direccion", ""), d.get("telefono", ""), d.get("tipo_documento", "DNI"))
        p._historia = HistoriaClinica.from_dict(d.get("historia", {}))
        return p


# ------------------------------------------------------------ Citas y turnos
class Cita:
    """Cita de 30 minutos con fecha, hora de inicio y estado."""

    def __init__(self, paciente: Paciente, medico: Medico, fecha: date, turno: str,
                 id_cita=None, estado="RESERVADO"):
        if estado not in ESTADOS_TICKET + ("CANCELADA",):
            raise ErrorValidacion("Estado de cita inválido.")
        self._id = id_cita or uuid.uuid4().hex[:8]
        self._paciente, self._medico = paciente, medico
        self._fecha = fecha
        # Compatibilidad: los registros antiguos solo guardaban MAÑANA/TARDE.
        if turno in TURNOS:
            self._hora = "08:00" if turno == "MAÑANA" else "14:00"
        else:
            self._hora = str(turno).strip()
        minutos = self._validar_hora(self._hora)
        self._hora = f"{minutos // 60:02d}:{minutos % 60:02d}"
        self._estado = estado

    @staticmethod
    def _validar_hora(hora):
        try:
            h, m = map(int, hora.split(":"))
            minutos = h * 60 + m
        except (ValueError, AttributeError):
            raise ErrorValidacion("Seleccione una hora válida.") from None
        manana = 8 * 60 <= minutos and minutos + 30 <= 12 * 60
        tarde = 14 * 60 <= minutos and minutos + 30 <= 18 * 60
        if m not in (0, 30) or not (manana or tarde):
            raise ErrorValidacion("Las citas son de 30 minutos: 08:00–11:30 o 14:00–17:30.")
        return minutos

    def get_id(self): return self._id
    def get_paciente(self): return self._paciente
    def get_medico(self): return self._medico
    def get_fecha(self): return self._fecha
    def get_hora(self): return self._hora
    def get_hora_fin(self):
        h, m = map(int, self._hora.split(":"))
        total = h * 60 + m + 30
        return f"{total // 60:02d}:{total % 60:02d}"
    def get_turno(self): return "MAÑANA" if self._hora < "12:00" else "TARDE"
    def get_estado(self): return self._estado

    def inicio(self) -> datetime:
        h, m = map(int, self._hora.split(":"))
        return datetime.combine(self._fecha, datetime.min.time()).replace(hour=h, minute=m)

    def estado_visible(self, ahora: datetime | None = None) -> str:
        """Si la hora ya pasó y nadie la marcó, se muestra VENCIDA (el estado guardado no cambia solo)."""
        ahora = ahora or datetime.now()
        if self._estado == "RESERVADO" and self.inicio() + timedelta(minutes=30) <= ahora:
            return "VENCIDA (sin atender)"
        return self._estado

    def set_estado(self, estado):
        if estado not in ESTADOS_TICKET + ("CANCELADA",):
            raise ErrorValidacion("Estado de cita inválido.")
        self._estado = estado
    def ocupa_cupo(self): return self._estado != "CANCELADA"

    def to_dict(self):
        return {"id": self._id, "paciente": self._paciente.get_dni_hash(), "medico": self._medico.get_cmp(),
                "fecha": self._fecha.isoformat(), "turno": self.get_turno(), "hora": self._hora,
                "estado": self._estado}


class AgendaMedica:
    """Controla cupos por turno y evita cruces de horario por profesional."""

    HORAS = tuple([f"{h:02d}:{m:02d}" for h in range(8, 12) for m in (0, 30)] +
                  [f"{h:02d}:{m:02d}" for h in range(14, 18) for m in (0, 30)])

    def __init__(self, cupos_por_turno: int = 10):
        self._cupos = cupos_por_turno
        self._citas: dict[str, Cita] = {}

    def get_cupos_por_turno(self): return self._cupos

    @staticmethod
    def _turno_de(hora: str) -> str:
        return "MAÑANA" if hora < "12:00" else "TARDE"

    def horas_por_turno(self) -> int:
        """Cantidad de horarios de 30 min que tiene un turno (8 por turno)."""
        return sum(1 for h in self.HORAS if self._turno_de(h) == "MAÑANA")
    def get_citas(self): return tuple(self._citas.values())
    def get_cita(self, id_cita): return self._citas.get(id_cita)

    def cupos_disponibles(self, medico: Medico, fecha: date, turno: str) -> int:
        usados = sum(1 for c in self._citas.values()
                     if c.ocupa_cupo() and c.get_medico() is medico and c.get_fecha() == fecha
                     and c.get_turno() == turno)
        libres = sum(1 for h in self.HORAS if self._turno_de(h) == turno) - usados
        return max(0, min(self._cupos - usados, libres))

    def horas_disponibles(self, medico: Medico, fecha: date):
        ocupadas = {c.get_hora() for c in self._citas.values()
                    if c.ocupa_cupo() and c.get_medico() is medico and c.get_fecha() == fecha}
        return tuple(h for h in self.HORAS if h not in ocupadas)

    def agendar(self, paciente: Paciente, medico: Medico, fecha: date, turno: str, ahora: datetime | None = None) -> Cita:
        ahora = ahora or datetime.now()
        fechas.validar_fecha_cita(fecha, ahora.date())
        if turno in TURNOS:
            candidatas = [h for h in self.HORAS if ("MAÑANA" if h < "12:00" else "TARDE") == turno]
            ocupadas = set(self.HORAS) - set(self.horas_disponibles(medico, fecha))
            hora = next((h for h in candidatas if h not in ocupadas), None)
            if hora is None:
                raise CupoAgotado(f"No hay horarios disponibles en el turno {turno}.")
        else:
            hora = str(turno).strip()
        inicio = Cita._validar_hora(hora)
        hora = f"{inicio // 60:02d}:{inicio % 60:02d}"
        if self.cupos_disponibles(medico, fecha, "MAÑANA" if hora < "12:00" else "TARDE") <= 0:
            raise CupoAgotado(f"Sin cupos con {medico.nombre_completo()} el {fecha:%d/%m/%Y}.")
        fin = inicio + 30
        if fecha == ahora.date() and inicio <= ahora.hour * 60 + ahora.minute:
            raise ErrorValidacion(f"La hora {hora} de hoy ya pasó. Elija un horario posterior a las {ahora:%H:%M}.")
        for existente in self._citas.values():
            if not existente.ocupa_cupo() or existente.get_medico() is not medico or existente.get_fecha() != fecha:
                continue
            otro_inicio = Cita._validar_hora(existente.get_hora())
            if inicio < otro_inicio + 30 and otro_inicio < fin:
                raise CupoAgotado(f"El profesional ya tiene una cita de {existente.get_hora()} a {existente.get_hora_fin()}.")
        for existente in self._citas.values():       # el mismo paciente no puede estar en dos citas a la vez
            if not existente.ocupa_cupo() or existente.get_paciente() is not paciente or existente.get_fecha() != fecha:
                continue
            otro_inicio = Cita._validar_hora(existente.get_hora())
            if inicio < otro_inicio + 30 and otro_inicio < fin:
                raise CupoAgotado(f"El paciente ya tiene una cita de {existente.get_hora()} a {existente.get_hora_fin()} "
                                  f"con {existente.get_medico().nombre_completo()}.")
        cita = Cita(paciente, medico, fecha, hora)
        self._citas[cita.get_id()] = cita
        return cita

    def agregar_existente(self, cita: Cita): self._citas[cita.get_id()] = cita


class GeneradorTurnos:
    """Singleton: una única fuente de números correlativos por día (CE-03)."""

    _instancia = None
    _candado = threading.Lock()

    def __new__(cls):
        with cls._candado:
            if cls._instancia is None:
                obj = super().__new__(cls)
                obj._contadores = {}
                cls._instancia = obj
            return cls._instancia

    def siguiente(self, fecha: date) -> int:
        with self._candado:
            clave = fecha.isoformat()
            self._contadores[clave] = self._contadores.get(clave, 0) + 1
            return self._contadores[clave]

    def exportar(self): return dict(self._contadores)

    def restaurar(self, contadores: dict):
        with self._candado:
            self._contadores = dict(contadores)


class Ticket:
    """Turno digital con número correlativo y estado (RF-04, RF-05)."""

    def __init__(self, cita: Cita, numero: int | None = None, fecha: date | None = None):
        self._cita = cita
        self._fecha = fecha or cita.get_fecha()
        self._numero = numero if numero is not None else GeneradorTurnos().siguiente(self._fecha)  # dependencia

    def get_numero(self): return self._numero
    def get_fecha(self): return self._fecha
    def get_cita(self): return self._cita
    def get_estado(self): return self._cita.get_estado()
    def cambiar_estado(self, estado):
        if estado not in ESTADOS_TICKET:
            raise ErrorValidacion(f"Estado inválido. Opciones: {', '.join(ESTADOS_TICKET)}.")
        self._cita.set_estado(estado)

    def to_dict(self):
        return {"numero": self._numero, "fecha": self._fecha.isoformat(), "cita": self._cita.get_id()}
