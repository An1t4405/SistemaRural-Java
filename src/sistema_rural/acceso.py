"""Control de acceso: patrón Proxy sobre ServicioClinica.

La interfaz recibe un ServicioProtegido y no el servicio real: antes de cada operación se
comprueba que el rol del usuario tenga el permiso necesario. Lo que no figura en
PERMISO_POR_OPERACION queda DENEGADO por defecto (falla cerrado).
"""
from .errores import PermisoDenegado
from .usuarios import Permiso, Usuario

P = Permiso
PERMISO_POR_OPERACION = {
    "registrar_paciente": P.PACIENTES_REGISTRAR, "actualizar_paciente": P.PACIENTES_EDITAR,
    "buscar_por_dni": P.PACIENTES_VER, "buscar_por_documento": P.PACIENTES_VER, "buscar_por_nombre": P.PACIENTES_VER, "listar_pacientes": P.PACIENTES_VER,
    "registrar_medico": P.PROFESIONALES_GESTIONAR, "obtener_medico": P.PROFESIONALES_VER,
    "listar_medicos": P.PROFESIONALES_VER,
    "obtener_historia": P.HISTORIA_VER, "todas_las_atenciones": P.HISTORIA_VER,
    "actualizar_historia": P.HISTORIA_EDITAR,
    "agendar_cita": P.CITAS_GESTIONAR, "cancelar_cita": P.CITAS_GESTIONAR,
    "listar_citas": P.CITAS_VER, "consultar_cupos": P.CITAS_VER, "horas_disponibles": P.CITAS_VER, "listar_tickets": P.CITAS_VER,
    "cambiar_estado_cita": P.TICKETS_ESTADO, "emitir_ticket": P.TICKETS_EMITIR, "cambiar_estado_ticket": P.TICKETS_ESTADO,
    "generar_reporte": P.REPORTES_VER, "exportar_excel": P.REPORTES_VER,
    "exportar_txt": P.REPORTES_VER, "carpeta_exportaciones": P.CITAS_VER,
    "crear_usuario": P.USUARIOS_GESTIONAR, "listar_usuarios": P.USUARIOS_GESTIONAR,
    "restablecer_clave": P.USUARIOS_GESTIONAR,
}


class ServicioProtegido:
    def __init__(self, servicio, usuario: Usuario):
        self._srv = servicio
        self._usuario = usuario

    def usuario_actual(self) -> Usuario:
        return self._usuario

    def _requerir(self, permiso: Permiso):
        if not self._usuario.esta_activo():
            raise PermisoDenegado("Su cuenta fue desactivada. Cierre la sesión.")
        if not self._usuario.tiene_permiso(permiso):
            raise PermisoDenegado(f"Su rol ({self._usuario.get_rol().nombre}) no tiene permiso para: "
                                  f"{permiso.value.lower()}.")

    def __getattr__(self, nombre):
        if nombre.startswith("_"):
            raise AttributeError(nombre)
        permiso = PERMISO_POR_OPERACION.get(nombre)
        if permiso is None:
            raise PermisoDenegado(f"Operación no autorizada: {nombre}.")
        self._requerir(permiso)
        return getattr(self._srv, nombre)

    # ---- operaciones con reglas propias (siempre actúan sobre el usuario de la sesión)
    def registrar_atencion(self, dni, motivo, diagnostico_cie10, fecha=None, tipo_documento="DNI"):
        """La atención queda a nombre del profesional que inició sesión (su colegiatura)."""
        self._requerir(P.ATENCION_REGISTRAR)
        colegiatura = self._usuario.get_colegiatura()
        if not colegiatura:
            raise PermisoDenegado("Su usuario no tiene una colegiatura vinculada. Pida al administrador que la asigne.")
        return self._srv.registrar_atencion(dni, colegiatura, motivo, diagnostico_cie10, fecha, tipo_documento)

    def exportar_ficha_paciente(self, tipo_documento, numero, ruta=None):
        """Ficha Excel de un paciente. Admisión/secretaría: datos y citas. Con permiso de historia: también la historia."""
        self._requerir(P.PACIENTES_VER)
        con_historia = self._usuario.tiene_permiso(P.HISTORIA_VER)
        return self._srv.exportar_ficha_paciente(tipo_documento, numero, ruta, incluir_historia=con_historia)

    def cambiar_mi_clave(self, actual, nueva):
        self._srv.cambiar_clave(self._usuario.get_nombre_usuario(), actual, nueva)

    def cambiar_estado_usuario(self, nombre_usuario, activo):
        self._requerir(P.USUARIOS_GESTIONAR)
        self._no_propia(nombre_usuario)
        return self._srv.cambiar_estado_usuario(nombre_usuario, activo)

    def cambiar_rol_usuario(self, nombre_usuario, rol):
        self._requerir(P.USUARIOS_GESTIONAR)
        self._no_propia(nombre_usuario)
        return self._srv.cambiar_rol_usuario(nombre_usuario, rol)

    def _no_propia(self, nombre_usuario):
        if str(nombre_usuario).strip().lower() == self._usuario.get_nombre_usuario():
            raise PermisoDenegado("No puede modificar su propia cuenta desde aquí.")
