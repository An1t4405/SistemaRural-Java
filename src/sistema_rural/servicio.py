"""ServicioClinica: concentra las operaciones del sistema (RF-01 a RF-06).

La interfaz solo llama a este servicio (DD-03). Todo el archivo de datos se
guarda cifrado (RD-02).
"""
import json
import os
from datetime import date, datetime
from itertools import chain
from pathlib import Path

from . import fechas, seguridad
from .errores import (CredencialesInvalidas, CuentaBloqueada, DNIDuplicado, ErrorValidacion,
                      NoEncontrado)
from .modelos import (AgendaMedica, Atencion, Cita, ESTADOS_TICKET, GeneradorTurnos, Medico, Paciente, Ticket)
from .reportes import ReporteFactory
from .usuarios import (ROLES, Usuario, hashear_clave, validar_clave_segura,
                       validar_nombre_usuario)

_MSG_CREDENCIALES = "Usuario o contraseña incorrectos."


class ServicioClinica:
    def __init__(self, ruta_datos="datos.enc", ruta_clave="clave.key", cupos_por_turno=10):
        self._ruta = Path(ruta_datos)
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        self._carpeta_export = self._ruta.parent / "exportaciones"   # Excel y TXT generados
        self._carpeta_export.mkdir(parents=True, exist_ok=True)
        Path(ruta_clave).parent.mkdir(parents=True, exist_ok=True)
        self._cif = seguridad.configurar(ruta_clave)
        self._pacientes: dict[str, Paciente] = {}   # clave: hash del DNI (búsqueda O(1))
        self._medicos: dict[str, Medico] = {}       # clave: CMP
        self._agenda = AgendaMedica(cupos_por_turno)
        self._tickets: list[Ticket] = []
        self._usuarios: dict[str, Usuario] = {}      # clave: nombre de usuario (minúsculas)
        GeneradorTurnos().restaurar({})
        if self._ruta.exists():
            self.cargar()

    # ------------------------------------------------ RF-01 pacientes
    def registrar_paciente(self, dni, nombres, apellidos, fecha_nacimiento, direccion="", telefono="", tipo_documento="DNI") -> Paciente:
        nuevo = Paciente(dni, nombres, apellidos, fecha_nacimiento, direccion, telefono, tipo_documento)
        if nuevo.get_dni_hash() in self._pacientes:
            raise DNIDuplicado("Ya existe un paciente registrado con ese documento.")  # CE-02
        self._pacientes[nuevo.get_dni_hash()] = nuevo
        self.guardar()
        return nuevo

    def actualizar_paciente(self, dni, nombres=None, apellidos=None, direccion=None, telefono=None, tipo_documento="DNI") -> Paciente:
        p = self.buscar_por_documento(tipo_documento, dni)
        if nombres is not None: p.set_nombres(nombres)
        if apellidos is not None: p.set_apellidos(apellidos)
        if direccion is not None: p.set_direccion(direccion)
        if telefono is not None: p.set_telefono(telefono)
        self.guardar()
        return p

    def buscar_por_dni(self, dni) -> Paciente:
        return self.buscar_por_documento("DNI", dni)

    def buscar_por_documento(self, tipo_documento, numero) -> Paciente:
        tipo, numero = seguridad.validar_documento(tipo_documento, numero)
        p = self._pacientes.get(self._cif.hash_documento(tipo, numero))
        if p is None:
            raise NoEncontrado(f"No existe un paciente con ese {('DNI' if tipo == 'DNI' else 'Carné de Extranjería')}.")
        return p

    def buscar_por_nombre(self, texto: str) -> list[Paciente]:
        t = texto.strip().lower()
        return sorted(filter(lambda p: t in p.nombre_completo().lower(), self._pacientes.values()),
                      key=lambda p: p.nombre_completo())

    def listar_pacientes(self): return sorted(self._pacientes.values(), key=lambda p: p.nombre_completo())

    # ------------------------------------------------ médicos
    def registrar_medico(self, dni, nombres, apellidos, cmp, especialidad, telefono="") -> Medico:
        if cmp.strip() in self._medicos:
            raise ErrorValidacion("Ya existe un médico con ese CMP.")
        m = Medico(dni, nombres, apellidos, cmp, especialidad, telefono)
        self._medicos[m.get_cmp()] = m
        self.guardar()
        return m

    def obtener_medico(self, cmp) -> Medico:
        try:
            return self._medicos[str(cmp).strip()]
        except KeyError:
            raise NoEncontrado("No existe un médico con ese CMP.") from None

    def listar_medicos(self): return sorted(self._medicos.values(), key=lambda m: m.nombre_completo())

    # ------------------------------------------------ RF-02 historia clínica
    def obtener_historia(self, dni, tipo_documento="DNI"):
        return self.buscar_por_documento(tipo_documento, dni).get_historia()

    def actualizar_historia(self, dni, alergias=None, antecedentes=None, tipo_documento="DNI"):
        h = self.buscar_por_documento(tipo_documento, dni).get_historia()
        if alergias is not None: h.set_alergias(alergias)
        if antecedentes is not None: h.set_antecedentes(antecedentes)
        self.guardar()

    def registrar_atencion(self, dni, cmp, motivo, diagnostico_cie10, fecha: date | None = None, tipo_documento="DNI") -> Atencion:
        p, m = self.buscar_por_documento(tipo_documento, dni), self.obtener_medico(cmp)
        f = fechas.validar_fecha_atencion(fecha or date.today(), p.get_fecha_nacimiento())
        a = Atencion(f, motivo, diagnostico_cie10, m.get_cmp())
        p.get_historia().agregar_atencion(a)
        self.guardar()
        return a

    def todas_las_atenciones(self):
        return chain.from_iterable(p.get_historia().get_atenciones() for p in self._pacientes.values())

    # ------------------------------------------------ RF-03 citas
    def agendar_cita(self, dni, cmp, fecha: date, turno: str, tipo_documento="DNI") -> Cita:
        """Agenda una cita de 30 minutos para paciente identificado por DNI o CE."""
        cita = self._agenda.agendar(self.buscar_por_documento(tipo_documento, dni), self.obtener_medico(cmp), fecha, turno)
        self.guardar()
        return cita

    def cancelar_cita(self, id_cita):
        cita = self._agenda.get_cita(id_cita)
        if cita is None:
            raise NoEncontrado("No existe esa cita.")
        cita.set_estado("CANCELADA")
        self.guardar()

    def cambiar_estado_cita(self, id_cita, estado, ahora: datetime | None = None):
        """Marca una cita (con o sin ticket). NO_ASISTIO solo desde que empieza la hora de la cita."""
        cita = self._agenda.get_cita(id_cita)
        if cita is None:
            raise NoEncontrado("No existe esa cita.")
        if estado not in ESTADOS_TICKET:
            raise ErrorValidacion(f"Estado inválido. Opciones: {', '.join(ESTADOS_TICKET)}.")
        if cita.get_estado() == "CANCELADA":
            raise ErrorValidacion("La cita está cancelada.")
        if estado == "NO_ASISTIO" and cita.inicio() > (ahora or datetime.now()):
            raise ErrorValidacion("Aún no llega la hora de la cita; no se puede marcar como «No asistió».")
        cita.set_estado(estado)
        self.guardar()
        return cita

    def listar_citas(self, fecha: date | None = None):
        return [c for c in self._agenda.get_citas() if fecha is None or c.get_fecha() == fecha]

    # ------------------------------------------------ RF-04 tickets
    def emitir_ticket(self, id_cita) -> Ticket:
        cita = self._agenda.get_cita(id_cita)
        if cita is None or not cita.ocupa_cupo():
            raise NoEncontrado("La cita no existe o está cancelada.")
        if any(t.get_cita() is cita for t in self._tickets):
            raise ErrorValidacion("Esa cita ya tiene un ticket emitido.")
        t = Ticket(cita)
        self._tickets.append(t)
        self.guardar()
        return t

    def cambiar_estado_ticket(self, fecha: date, numero: int, estado: str):
        for t in self._tickets:
            if t.get_fecha() == fecha and t.get_numero() == numero:
                t.cambiar_estado(estado)
                self.guardar()
                return t
        raise NoEncontrado("No existe ese ticket.")

    def listar_tickets(self, fecha: date | None = None):
        return sorted(filter(lambda t: fecha is None or t.get_fecha() == fecha, self._tickets),
                      key=lambda t: (t.get_fecha(), t.get_numero()))

    # ------------------------------------------------ RF-05 disponibilidad
    def consultar_cupos(self, cmp, fecha: date) -> dict:
        """{turno: (disponibles, total)} para un médico y fecha."""
        m = self.obtener_medico(cmp)
        total = min(self._agenda.get_cupos_por_turno(), self._agenda.horas_por_turno())
        return {t: (self._agenda.cupos_disponibles(m, fecha, t), total) for t in ("MAÑANA", "TARDE")}

    def horas_disponibles(self, cmp, fecha: date):
        return self._agenda.horas_disponibles(self.obtener_medico(cmp), fecha)

    # ------------------------------------------------ RF-06 reportes
    def carpeta_exportaciones(self) -> str:
        return str(self._carpeta_export)

    def _ruta_salida(self, ruta, nombre_defecto: str) -> Path:
        """Sin ruta -> datos/exportaciones/<nombre con fecha y hora>."""
        if ruta:
            return Path(ruta)
        base, ext = nombre_defecto.rsplit(".", 1)
        return self._carpeta_export / f"{base}_{datetime.now():%Y%m%d_%H%M%S}.{ext}"

    def exportar_ficha_paciente(self, tipo_documento, numero, ruta=None, incluir_historia=False):
        """Descarga en Excel los datos de UN paciente: datos personales, citas y (si el rol lo permite)
        alergias, antecedentes y atenciones. El documento sale enmascarado."""
        try:
            from openpyxl import Workbook
        except ImportError as exc:
            raise ErrorValidacion("Para exportar a Excel instale openpyxl: pip install openpyxl.") from exc
        p = self.buscar_por_documento(tipo_documento, numero)
        wb = Workbook()
        h = wb.active
        h.title = "Paciente"
        h.append(["Campo", "Dato"])
        for fila in (("Tipo de documento", p.get_tipo_documento()), ("Documento", p.get_dni_enmascarado()),
                     ("Apellidos y nombres", p.nombre_completo()),
                     ("Fecha de nacimiento", p.get_fecha_nacimiento().strftime("%d/%m/%Y")),
                     ("Edad", p.edad()), ("Dirección", p.get_direccion()), ("Teléfono", p.get_telefono()),
                     ("Exportado el", datetime.now().strftime("%d/%m/%Y %H:%M"))):
            h.append(list(fila))
        c = wb.create_sheet("Citas")
        c.append(["Fecha", "Hora", "Fin", "Profesional", "Colegiatura", "Estado"])
        for x in sorted((x for x in self.listar_citas() if x.get_paciente() is p), key=lambda x: (x.get_fecha(), x.get_hora())):
            c.append([x.get_fecha().strftime("%d/%m/%Y"), x.get_hora(), x.get_hora_fin(),
                      x.get_medico().nombre_completo(), x.get_medico().get_cmp(), x.estado_visible()])
        if incluir_historia:
            hist = p.get_historia()
            a = wb.create_sheet("Historia clínica")
            a.append(["Alergias", hist.get_alergias()])
            a.append(["Antecedentes", hist.get_antecedentes()])
            a.append([])
            a.append(["Fecha", "Motivo", "Diagnóstico CIE-10", "Colegiatura del profesional"])
            for t in hist.get_atenciones():
                a.append([t.get_fecha().strftime("%d/%m/%Y"), t.get_motivo(), t.get_diagnostico(), t.get_cmp_medico()])
        self._dar_formato(wb)
        destino = self._ruta_salida(ruta, "ficha_paciente.xlsx")
        wb.save(destino)
        return str(destino)

    @staticmethod
    def _dar_formato(wb):
        for hoja in wb.worksheets:
            hoja.freeze_panes = "A2"
            for columna in hoja.columns:
                letra = columna[0].column_letter
                hoja.column_dimensions[letra].width = min(40, max(14, max(len(str(c.value or "")) for c in columna) + 2))

    def exportar_excel(self, ruta=None):
        """Exporta listados operativos; DNI siempre enmascarado."""
        try:
            from openpyxl import Workbook
        except ImportError as exc:
            raise ErrorValidacion("Para exportar a Excel instale openpyxl: pip install openpyxl.") from exc
        wb = Workbook()
        pacientes = wb.active
        pacientes.title = "Pacientes"
        pacientes.append(["Tipo documento", "Documento", "Paciente", "Fecha de nacimiento", "Teléfono"])
        for p in self.listar_pacientes():
            pacientes.append([p.get_tipo_documento(), p.get_dni_enmascarado(), p.nombre_completo(),
                              p.get_fecha_nacimiento().strftime("%d/%m/%Y"), p.get_telefono()])
        citas = wb.create_sheet("Citas")
        citas.append(["Fecha", "Hora", "Fin", "Paciente", "Profesional", "Colegiatura", "Estado"])
        for c in sorted(self.listar_citas(), key=lambda x: (x.get_fecha(), x.get_hora())):
            citas.append([c.get_fecha().strftime("%d/%m/%Y"), c.get_hora(), c.get_hora_fin(),
                          c.get_paciente().get_dni_enmascarado(), c.get_medico().nombre_completo(),
                          c.get_medico().get_cmp(), c.estado_visible()])
        for hoja in wb.worksheets:
            hoja.freeze_panes = "A2"
            hoja.auto_filter.ref = hoja.dimensions
            for columna in hoja.columns:
                letra = columna[0].column_letter
                hoja.column_dimensions[letra].width = min(36, max(14, max(len(str(c.value or "")) for c in columna) + 2))
        destino = self._ruta_salida(ruta, "reporte_posta.xlsx")
        wb.save(destino)
        return str(destino)

    def exportar_txt(self, ruta=None):
        """Genera un resumen de actividad sin exponer el DNI."""
        lineas = ["SISTEMA RURAL-PE | RESUMEN DE REGISTROS",
                  f"Generado: {datetime.now():%d/%m/%Y %H:%M}",
                  f"Pacientes registrados: {len(self._pacientes)}",
                  f"Profesionales registrados: {len(self._medicos)}", "",
                  "CITAS", "Fecha       Hora  Fin    Paciente       Profesional                 Estado"]
        citas = sorted(self.listar_citas(), key=lambda x: (x.get_fecha(), x.get_hora()))
        for c in citas:
            lineas.append(f"{c.get_fecha():%d/%m/%Y}  {c.get_hora():5} {c.get_hora_fin():5} "
                          f"{c.get_paciente().get_dni_enmascarado():14} "
                          f"{c.get_medico().nombre_completo():28} {c.estado_visible()}")
        destino = self._ruta_salida(ruta, "resumen_posta.txt")
        destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
        return str(destino)

    def generar_reporte(self, tipo: str, fecha: date | None = None) -> dict:
        ref = fechas.validar_fecha_reporte(fecha or date.today())
        return ReporteFactory.crear(tipo, self.todas_las_atenciones()).generar(ref)

    # ------------------------------------------------ usuarios, roles y acceso
    def hay_usuarios(self) -> bool:
        return bool(self._usuarios)

    def ruta_datos(self) -> Path:
        return self._ruta.resolve()

    def crear_primer_administrador(self, nombre_usuario, nombres, apellidos, clave) -> Usuario:
        """Solo funciona mientras no exista ningún usuario (primer uso del sistema)."""
        if self._usuarios:
            raise ErrorValidacion("Ya existe un administrador. Inicie sesión.")
        return self._agregar_usuario(nombre_usuario, nombres, apellidos, "ADMIN", clave, "", False)

    def crear_usuario(self, nombre_usuario, nombres, apellidos, rol, clave, colegiatura="",
                      debe_cambiar_clave=True) -> Usuario:
        return self._agregar_usuario(nombre_usuario, nombres, apellidos, rol, clave, colegiatura, debe_cambiar_clave)

    def _agregar_usuario(self, nombre_usuario, nombres, apellidos, rol, clave, colegiatura, debe_cambiar) -> Usuario:
        clave_usuario = validar_nombre_usuario(nombre_usuario)
        if clave_usuario in self._usuarios:
            raise ErrorValidacion("Ese nombre de usuario ya existe.")
        if rol not in ROLES:
            raise ErrorValidacion("Rol desconocido.")
        validar_clave_segura(clave, clave_usuario)
        colegiatura = str(colegiatura).strip()
        if colegiatura and colegiatura not in self._medicos:
            raise NoEncontrado(f"La colegiatura {colegiatura} no está en la lista de profesionales. "
                               "Regístrela primero en la pestaña Profesionales.")
        u = Usuario(clave_usuario, nombres, apellidos, rol, hashear_clave(clave), colegiatura,
                    debe_cambiar_clave=debe_cambiar)
        self._usuarios[clave_usuario] = u
        self.guardar()
        return u

    def listar_usuarios(self):
        return sorted(self._usuarios.values(), key=lambda u: u.nombre_completo())

    def _obtener_usuario(self, nombre_usuario) -> Usuario:
        u = self._usuarios.get(str(nombre_usuario).strip().lower())
        if u is None:
            raise NoEncontrado("No existe ese usuario.")
        return u

    def _admins_activos(self) -> int:
        return sum(1 for u in self._usuarios.values() if u.get_rol().codigo == "ADMIN" and u.esta_activo())

    def _es_ultimo_admin(self, u: Usuario) -> bool:
        return u.get_rol().codigo == "ADMIN" and u.esta_activo() and self._admins_activos() <= 1

    def cambiar_estado_usuario(self, nombre_usuario, activo: bool):
        u = self._obtener_usuario(nombre_usuario)
        if not activo and self._es_ultimo_admin(u):
            raise ErrorValidacion("Debe quedar al menos un administrador activo.")
        u.set_activo(activo)
        if activo:
            u.desbloquear()
        self.guardar()

    def cambiar_rol_usuario(self, nombre_usuario, rol):
        u = self._obtener_usuario(nombre_usuario)
        if rol not in ROLES:
            raise ErrorValidacion("Rol desconocido.")
        if rol != "ADMIN" and self._es_ultimo_admin(u):
            raise ErrorValidacion("Debe quedar al menos un administrador activo.")
        u.set_rol(rol)
        self.guardar()

    def restablecer_clave(self, nombre_usuario, nueva_clave):
        """El administrador fija una clave temporal; el usuario deberá cambiarla al ingresar."""
        u = self._obtener_usuario(nombre_usuario)
        validar_clave_segura(nueva_clave, u.get_nombre_usuario())
        u.set_clave_hash(hashear_clave(nueva_clave), temporal=True)
        u.desbloquear()
        self.guardar()

    def cambiar_clave(self, nombre_usuario, actual, nueva):
        u = self._obtener_usuario(nombre_usuario)
        if not u.verificar(actual):
            raise CredencialesInvalidas("La contraseña actual no es correcta.")
        if actual == nueva:
            raise ErrorValidacion("La contraseña nueva debe ser distinta de la actual.")
        validar_clave_segura(nueva, u.get_nombre_usuario())
        u.set_clave_hash(hashear_clave(nueva), temporal=False)
        self.guardar()

    def autenticar(self, nombre_usuario, clave, ahora: datetime | None = None) -> Usuario:
        """Valida credenciales. Mensaje genérico ante error; bloqueo temporal tras varios fallos."""
        ahora = ahora or datetime.now()
        u = self._usuarios.get(str(nombre_usuario).strip().lower())
        if u is None:
            hashear_clave(str(clave))                      # mismo costo que un usuario real
            raise CredencialesInvalidas(_MSG_CREDENCIALES)
        if u.bloqueado(ahora):
            raise CuentaBloqueada("Cuenta bloqueada por varios intentos fallidos. "
                                  f"Intente de nuevo a las {u.get_bloqueado_hasta():%H:%M}.")
        if not u.verificar(str(clave)):
            quedan = u.registrar_fallo(ahora)
            self.guardar()
            if quedan == 0:
                raise CuentaBloqueada("Demasiados intentos fallidos: cuenta bloqueada unos minutos.")
            raise CredencialesInvalidas(f"{_MSG_CREDENCIALES} Intentos restantes: {quedan}.")
        if not u.esta_activo():
            raise CredencialesInvalidas("Su cuenta está desactivada. Consulte al administrador.")
        u.registrar_acceso(ahora)
        self.guardar()
        return u

    # ------------------------------------------------ persistencia cifrada
    def guardar(self):
        datos = {
            "pacientes": [p.to_dict() for p in self._pacientes.values()],
            "medicos": [m.to_dict() for m in self._medicos.values()],
            "cupos_por_turno": self._agenda.get_cupos_por_turno(),
            "citas": [c.to_dict() for c in self._agenda.get_citas()],
            "tickets": [t.to_dict() for t in self._tickets],
            "contadores": GeneradorTurnos().exportar(),
            "usuarios": [u.to_dict() for u in self._usuarios.values()],
        }
        crudo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        tmp = self._ruta.with_suffix(".tmp")
        tmp.write_bytes(self._cif.cifrar_bytes(crudo))
        os.replace(tmp, self._ruta)  # escritura atómica: no deja el archivo a medias

    def cargar(self):
        datos = json.loads(self._cif.descifrar_bytes(self._ruta.read_bytes()))
        self._pacientes = {p.get_dni_hash(): p for p in map(Paciente.from_dict, datos["pacientes"])}
        self._medicos = {m.get_cmp(): m for m in map(Medico.from_dict, datos["medicos"])}
        self._agenda = AgendaMedica(datos.get("cupos_por_turno", 10))
        for c in datos["citas"]:
            self._agenda.agregar_existente(Cita(self._pacientes[c["paciente"]], self._medicos[c["medico"]],
                                                date.fromisoformat(c["fecha"]), c.get("hora", c["turno"]), c["id"], c["estado"]))
        self._tickets = [Ticket(self._agenda.get_cita(t["cita"]), t["numero"], date.fromisoformat(t["fecha"]))
                         for t in datos["tickets"]]
        GeneradorTurnos().restaurar(datos.get("contadores", {}))
        self._usuarios = {u.get_nombre_usuario(): u for u in map(Usuario.from_dict, datos.get("usuarios", []))}
