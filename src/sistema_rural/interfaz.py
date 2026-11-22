"""Interfaz gráfica (DD-03): handlers de eventos que delegan en el servicio protegido.

El menú se arma según el rol: cada pestaña y cada botón aparece solo si el rol tiene el permiso
correspondiente. La seguridad real está en acceso.py; aquí solo se evita mostrar lo que no aplica.
Las fechas se escriben como DD/MM/AAAA y se validan con fechas.py.
"""
import tkinter as tk
from datetime import date, datetime
from tkinter import filedialog, messagebox, simpledialog, ttk

from . import fechas
from .errores import ErrorSistema
from .modelos import ESTADOS_TICKET, TURNOS
from .reportes import ReporteFactory
from .ui_comun import COLOR_ADMIN, COLOR_ASISTENCIAL, DialogoCambiarClave, ejecutar, fecha_auto
from .usuarios import GRUPO_ADMIN, ROLES, Permiso

P = Permiso
_ETIQUETA_ESTADO = {"NO_ASISTIO": "No asistió", "EN_ATENCION": "En atención"}


CAMPOS_PACIENTE = ("p_dni", "p_nom", "p_ape", "p_nac", "p_dir", "p_tel")


class VentanaPrincipal(tk.Tk):
    def __init__(self, servicio, usuario):
        super().__init__()
        self._srv, self._usr = servicio, usuario
        self._rol = usuario.get_rol()
        self.cerrar_sesion = False                 # True si el usuario pidió "Cerrar sesión"
        self.title("SistemaRural-PE · Posta Médica Rural")
        self.geometry("1040x700")
        self.minsize(900, 600)
        self._vars: dict[str, tk.StringVar] = {}
        self._entradas: dict[str, ttk.Entry] = {}
        self._paginas: dict[str, ttk.Frame] = {}
        self._rol_por_nombre = {r.nombre: r.codigo for r in ROLES.values()}
        self._t_pac = self._t_med = self._t_cit = self._t_usr = self._cb_medico = None   # existen solo si el rol ve esa pestaña

        self._armar_encabezado()
        self._nb = ttk.Notebook(self)
        self._nb.pack(fill="both", expand=True, padx=8, pady=8)
        modulos = [("Inicio", None, self._tab_inicio), ("Pacientes", P.PACIENTES_VER, self._tab_pacientes),
                   ("Historia clínica", P.HISTORIA_VER, self._tab_historia),
                   ("Profesionales", P.PROFESIONALES_VER, self._tab_profesionales),
                   ("Citas y turnos", P.CITAS_VER, self._tab_citas), ("Reportes", P.REPORTES_VER, self._tab_reportes),
                   ("Usuarios", P.USUARIOS_GESTIONAR, self._tab_usuarios)]
        permitidos = [m for m in modulos if m[1] is None or self._puede(m[1])]
        self._titulos = [t for t, _, _ in permitidos]
        for titulo, _, constructor in permitidos:
            marco = ttk.Frame(self._nb, padding=10)
            self._nb.add(marco, text=titulo)
            self._paginas[titulo] = marco
            constructor(marco)
        self._armar_menu()
        self._refrescar_todo()

    # ------------------------------------------------------------ utilidades
    def _puede(self, permiso: Permiso) -> bool:
        return self._usr.tiene_permiso(permiso)

    def _var(self, nombre, inicial="") -> tk.StringVar:
        self._vars[nombre] = tk.StringVar(value=inicial)
        return self._vars[nombre]

    def _limpiar(self, *claves):
        """Vacía los campos del formulario (se usa solo cuando la operación salió bien)."""
        for clave in claves:
            self._vars[clave].set("")
        if claves and claves[0] in self._entradas:
            self._entradas[claves[0]].focus_set()          # deja el cursor listo para el siguiente registro

    def _v(self, nombre) -> str:
        return self._vars[nombre].get().strip()

    def _campos(self, marco, etiquetas, fila0=0, columnas=2, ocultos=(), fechas_=()):
        """Crea pares etiqueta+entrada. etiquetas: [(clave, texto)]. `fechas_`: claves que llevan DD/MM/AAAA."""
        for i, (clave, texto) in enumerate(etiquetas):
            f, c = fila0 + i // columnas, (i % columnas) * 2
            ttk.Label(marco, text=texto).grid(row=f, column=c, sticky="e", padx=4, pady=3)
            e = ttk.Entry(marco, textvariable=self._var(clave), width=26, show="•" if clave in ocultos else "")
            e.grid(row=f, column=c + 1, sticky="w", padx=4, pady=3)
            self._entradas[clave] = e
            if clave in fechas_:
                fecha_auto(self._vars[clave], e)

    def _boton(self, marco, texto, comando, permiso=None, activo=True):
        b = ttk.Button(marco, text=texto, command=comando)
        if (permiso is not None and not self._puede(permiso)) or not activo:
            b.state(["disabled"])
        b.pack(side="left", padx=3)
        return b

    def _tabla(self, marco, columnas, alto=8):
        t = ttk.Treeview(marco, columns=[c for c, _ in columnas], show="headings", height=alto, selectmode="browse")
        for c, texto in columnas:
            t.heading(c, text=texto)
            t.column(c, width=120, anchor="w")
        t.pack(fill="both", expand=True, pady=6)
        return t

    @staticmethod
    def _llenar(tabla, filas, iids=None):
        tabla.delete(*tabla.get_children())
        for i, f in enumerate(filas):
            tabla.insert("", "end", iid=iids[i] if iids else None, values=f)

    def _fecha(self, clave, campo, hoy_si_vacia=False) -> date:
        if hoy_si_vacia and not self._v(clave):
            return date.today()
        return fechas.parsear_fecha(self._v(clave), campo)

    # ------------------------------------------------------------ encabezado y menú
    def _armar_encabezado(self):
        color = COLOR_ADMIN if self._rol.grupo == GRUPO_ADMIN else COLOR_ASISTENCIAL
        barra = tk.Frame(self, bg=color)
        barra.pack(fill="x")
        tk.Label(barra, text="SistemaRural-PE · Posta Médica Rural", bg=color, fg="white",
                 font=("Segoe UI", 13, "bold")).pack(side="left", padx=12, pady=8)
        der = tk.Frame(barra, bg=color)
        der.pack(side="right", padx=8)
        tk.Label(der, text=f"{self._usr.nombre_completo()}  ·  {self._rol.nombre}", bg=color, fg="white",
                 font=("Segoe UI", 10)).pack(side="left", padx=8)
        ttk.Button(der, text="Cambiar contraseña", command=self._on_cambiar_clave).pack(side="left", padx=3)
        ttk.Button(der, text="Cerrar sesión", command=self._on_cerrar_sesion).pack(side="left", padx=3)

    def _armar_menu(self):
        barra = tk.Menu(self)
        sesion = tk.Menu(barra, tearoff=0)
        sesion.add_command(label="Cambiar contraseña", command=self._on_cambiar_clave)
        sesion.add_command(label="Cerrar sesión", command=self._on_cerrar_sesion)
        sesion.add_separator()
        sesion.add_command(label="Salir", command=self.destroy)
        barra.add_cascade(label="Sesión", menu=sesion)
        modulos = tk.Menu(barra, tearoff=0)
        for titulo in self._titulos:
            modulos.add_command(label=titulo, command=lambda t=titulo: self._ir_a(t))
        barra.add_cascade(label="Módulos", menu=modulos)
        self.config(menu=barra)

    def _ir_a(self, titulo):
        self._nb.select(self._paginas[titulo])

    def _on_cambiar_clave(self):
        DialogoCambiarClave(self, lambda actual, nueva: self._srv.cambiar_mi_clave(actual, nueva))

    def _on_cerrar_sesion(self):
        if messagebox.askyesno("Cerrar sesión", "¿Desea cerrar la sesión?", parent=self):
            self.cerrar_sesion = True
            self.destroy()

    # ------------------------------------------------------------ inicio (menú del rol)
    def _tab_inicio(self, m):
        """Inicio sencillo: bienvenida y orientación breve, sin explicar permisos al personal."""
        ttk.Label(m, text=f"¡Bienvenida(o), {self._usr.get_nombres()}!",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w", pady=(8, 4))
        ttk.Label(m, text="Seleccione una pestaña superior para trabajar con pacientes, profesionales, "
                         "citas y reportes.", wraplength=940, justify="left").pack(anchor="w", pady=(2, 12))

        # Accesos directos opcionales: se muestran solo los módulos disponibles para la cuenta.
        accesos = ttk.LabelFrame(m, text="Accesos directos", padding=12)
        accesos.pack(fill="x", anchor="n")
        for titulo in self._titulos:
            if titulo != "Inicio":
                ttk.Button(accesos, text=titulo, command=lambda t=titulo: self._ir_a(t)).pack(
                    side="left", padx=4, pady=4, ipadx=8, ipady=3)
        if not self._usr.get_colegiatura() and self._puede(P.ATENCION_REGISTRAR):
            ttk.Label(m, text="Aviso: su usuario no tiene una colegiatura vinculada, por lo que aún no puede "
                              "registrar atenciones. Pida al administrador que la asigne.",
                      foreground="#9A3412", wraplength=940).pack(anchor="w", pady=(10, 0))


    # ------------------------------------------------------------ RF-01 pacientes
    def _tab_pacientes(self, m):
        form = ttk.LabelFrame(m, text="Datos del paciente", padding=8)
        form.pack(fill="x")
        ttk.Label(form, text="Tipo de documento").grid(row=0, column=0, sticky="e", padx=4, pady=3)
        ttk.Combobox(form, textvariable=self._var("p_tipo_doc", "DNI"), values=("DNI", "CE"),
                     width=23, state="readonly").grid(row=0, column=1, sticky="w", padx=4, pady=3)
        self._campos(form, [("p_dni", "N.º documento"), ("p_nom", "Nombres"), ("p_ape", "Apellidos"),
                            ("p_nac", "Nacimiento (DD/MM/AAAA)"), ("p_dir", "Dirección"), ("p_tel", "Teléfono")],
                     fila0=1, fechas_=("p_nac",))
        bt = ttk.Frame(m)
        bt.pack(fill="x", pady=6)
        self._boton(bt, "Registrar", self._on_registrar_paciente, P.PACIENTES_REGISTRAR)
        self._boton(bt, "Actualizar", self._on_actualizar_paciente, P.PACIENTES_EDITAR)
        self._boton(bt, "Buscar por DNI", self._on_buscar_dni, P.PACIENTES_VER)
        self._boton(bt, "Ver todos", self._refrescar_pacientes, P.PACIENTES_VER)
        self._boton(bt, "Limpiar formulario", lambda: self._limpiar(*CAMPOS_PACIENTE))
        self._boton(bt, "Descargar ficha (Excel)", self._on_exportar_ficha, P.PACIENTES_VER)
        self._t_pac = self._tabla(m, [("dni", "Documento"), ("nombre", "Paciente"), ("nac", "Nacimiento"), ("edad", "Edad"),
                                      ("tel", "Teléfono"), ("dir", "Dirección")])
        # Al seleccionar una fila, cargar el paciente completo en el formulario.
        # El identificador interno evita depender del documento enmascarado que se muestra en pantalla.
        self._t_pac.bind("<<TreeviewSelect>>", self._on_seleccionar_paciente)

    def _on_registrar_paciente(self):
        def accion():
            # Comprobar primero los campos obligatorios para no mostrar errores
            # de formato (por ejemplo, fecha vacía) cuando el formulario está vacío.
            obligatorios = (
                ("p_dni", "Número de documento"),
                ("p_nom", "Nombres"),
                ("p_ape", "Apellidos"),
                ("p_nac", "Fecha de nacimiento"),
            )
            faltantes = [etiqueta for clave, etiqueta in obligatorios if not self._v(clave)]
            if faltantes:
                messagebox.showwarning(
                    "Datos incompletos",
                    "Complete los siguientes campos obligatorios:\n\n• " + "\n• ".join(faltantes),
                    parent=self,
                )
                return

            self._srv.registrar_paciente(self._v("p_dni"), self._v("p_nom"), self._v("p_ape"),
                                         self._fecha("p_nac", "Fecha de nacimiento"),
                                         self._v("p_dir"), self._v("p_tel"), self._v("p_tipo_doc"))
            self._limpiar(*CAMPOS_PACIENTE)
            self._vars["p_tipo_doc"].set("DNI")
            self._refrescar_pacientes()
        ejecutar(accion, "Paciente registrado.", self)

    def _on_actualizar_paciente(self):
        def accion():   # un campo vacío significa "dejar como está"
            self._srv.actualizar_paciente(self._v("p_dni"), self._v("p_nom") or None, self._v("p_ape") or None,
                                          self._v("p_dir") or None, self._v("p_tel") or None, self._v("p_tipo_doc"))
            self._limpiar(*CAMPOS_PACIENTE)
            self._vars["p_tipo_doc"].set("DNI")
            self._refrescar_pacientes()
        ejecutar(accion, "Datos actualizados.", self)

    def _on_buscar_dni(self):
        def accion():
            numero = self._v("p_dni")
            if not numero:
                messagebox.showwarning("Búsqueda por DNI", "Ingrese el número de DNI para realizar la búsqueda.", parent=self)
                return
            if self._v("p_tipo_doc") != "DNI":
                messagebox.showwarning("Búsqueda por DNI", "Seleccione DNI como tipo de documento.", parent=self)
                return
            # El servicio valida que el DNI tenga exactamente 8 dígitos y localiza
            # al paciente por su hash; nunca se compara contra el DNI enmascarado.
            p = self._srv.buscar_por_dni(numero)
            self._mostrar_pacientes([p])
            self._vars["p_tipo_doc"].set("DNI")
            for clave, valor in (("p_nom", p.get_nombres()), ("p_ape", p.get_apellidos()), ("p_dir", p.get_direccion()),
                                 ("p_tel", p.get_telefono()), ("p_nac", fechas.formatear(p.get_fecha_nacimiento()))):
                self._vars[clave].set(valor)
            self._t_pac.selection_set(p.get_dni_hash())
            self._t_pac.focus(p.get_dni_hash())
            self._t_pac.see(p.get_dni_hash())
        ejecutar(accion, padre=self)

    def _on_exportar_ficha(self):
        """Descarga en Excel los datos del paciente cuyo documento está escrito en el formulario."""
        def accion():
            ruta = self._srv.exportar_ficha_paciente(self._v("p_tipo_doc"), self._v("p_dni"))
            messagebox.showinfo("Ficha exportada", f"Archivo guardado en:\n{ruta}", parent=self)
        ejecutar(accion, padre=self)

    def _carpeta_export(self):
        try:
            return self._srv.carpeta_exportaciones()
        except Exception:
            return None

    def _mostrar_pacientes(self, pacientes):
        pacientes = list(pacientes)
        filas = [(f"{p.get_tipo_documento()} {p.get_dni_enmascarado()}", p.nombre_completo(),
                  fechas.formatear(p.get_fecha_nacimiento()), p.edad(),
                  p.get_telefono(), p.get_direccion()) for p in pacientes]
        # Usar el hash como iid: nunca se expone el documento real en la tabla.
        self._llenar(self._t_pac, filas, iids=[p.get_dni_hash() for p in pacientes])

    def _on_seleccionar_paciente(self, _evento=None):
        seleccion = self._t_pac.selection()
        if not seleccion:
            return
        try:
            paciente = next(p for p in self._srv.listar_pacientes()
                            if p.get_dni_hash() == seleccion[0])
            self._vars["p_tipo_doc"].set(paciente.get_tipo_documento())
            self._vars["p_dni"].set(paciente.get_numero_documento())
            self._vars["p_nom"].set(paciente.get_nombres())
            self._vars["p_ape"].set(paciente.get_apellidos())
            self._vars["p_nac"].set(fechas.formatear(paciente.get_fecha_nacimiento()))
            self._vars["p_dir"].set(paciente.get_direccion())
            self._vars["p_tel"].set(paciente.get_telefono())
        except (StopIteration, KeyError):
            return

    def _refrescar_pacientes(self):
        self._mostrar_pacientes(self._srv.listar_pacientes())

    # ------------------------------------------------------------ RF-02 historia
    def _tab_historia(self, m):
        editar = self._puede(P.HISTORIA_EDITAR)
        top = ttk.LabelFrame(m, text="Paciente", padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Documento").grid(row=0, column=0, sticky="e", padx=4, pady=3)
        ttk.Combobox(top, textvariable=self._var("h_tipo_doc", "DNI"), values=("DNI", "CE"),
                     width=7, state="readonly").grid(row=0, column=1, sticky="w", padx=4, pady=3)
        self._campos(top, [("h_dni", "N.º documento"), ("h_ale", "Alergias"), ("h_ant", "Antecedentes")],
                     fila0=1, columnas=3)
        if not editar:
            for clave in ("h_ale", "h_ant"):
                self._entradas[clave].state(["readonly"])
        bt = ttk.Frame(top)
        bt.grid(row=1, column=0, columnspan=6, sticky="w", pady=4)
        self._boton(bt, "Cargar historia", self._on_cargar_historia)
        self._boton(bt, "Guardar alergias/antecedentes", self._on_guardar_historia, P.HISTORIA_EDITAR)
        nueva = ttk.LabelFrame(m, text="Nueva atención", padding=8)
        nueva.pack(fill="x", pady=6)
        col = self._usr.get_colegiatura()
        ttk.Label(nueva, text=f"Se registrará a nombre de: {self._usr.nombre_completo()} · "
                              f"Colegiatura: {col or 'sin vincular'}").grid(row=0, column=0, columnspan=4, sticky="w", padx=4)
        self._campos(nueva, [("a_mot", "Motivo de consulta"), ("a_cie", "Diagnóstico CIE-10")], fila0=1)
        bt2 = ttk.Frame(nueva)
        bt2.grid(row=2, column=0, columnspan=4, sticky="w", pady=4)
        self._boton(bt2, "Registrar atención", self._on_registrar_atencion, P.ATENCION_REGISTRAR, activo=bool(col))
        self._t_aten = self._tabla(m, [("fecha", "Fecha"), ("motivo", "Motivo"), ("diag", "Diagnóstico"), ("medico", "Profesional")])

    def _on_cargar_historia(self):
        def accion():
            h = self._srv.obtener_historia(self._v("h_dni"), self._v("h_tipo_doc"))
            self._vars["h_ale"].set(h.get_alergias())
            self._vars["h_ant"].set(h.get_antecedentes())
            self._llenar(self._t_aten, [(fechas.formatear(a.get_fecha()), a.get_motivo(), a.get_diagnostico(),
                                         a.get_cmp_medico()) for a in h.get_atenciones()])
        ejecutar(accion, padre=self)

    def _on_guardar_historia(self):
        ejecutar(lambda: self._srv.actualizar_historia(self._v("h_dni"), self._v("h_ale"), self._v("h_ant"), self._v("h_tipo_doc")),
                 "Historia clínica actualizada.", self)

    def _on_registrar_atencion(self):
        def accion():
            self._srv.registrar_atencion(self._v("h_dni"), self._v("a_mot"), self._v("a_cie"),
                                         tipo_documento=self._v("h_tipo_doc"))
            self._vars["a_mot"].set("")
            self._vars["a_cie"].set("")
            self._on_cargar_historia()
        ejecutar(accion, "Atención registrada.", self)

    # ------------------------------------------------------------ profesionales de salud
    def _tab_profesionales(self, m):
        if self._puede(P.PROFESIONALES_GESTIONAR):
            form = ttk.LabelFrame(m, text="Nuevo profesional de salud", padding=8)
            form.pack(fill="x")
            self._campos(form, [("m_dni", "DNI"), ("m_cmp", "Colegiatura (CMP/COP/CEP)"), ("m_nom", "Nombres"),
                                ("m_ape", "Apellidos"), ("m_esp", "Profesión / especialidad"), ("m_tel", "Teléfono")])
            bt = ttk.Frame(m)
            bt.pack(fill="x", pady=6)
            self._boton(bt, "Registrar profesional", self._on_registrar_medico)
        self._t_med = self._tabla(m, [("cmp", "Colegiatura"), ("nombre", "Profesional"), ("esp", "Profesión / especialidad")])

    def _on_registrar_medico(self):
        def accion():
            self._srv.registrar_medico(self._v("m_dni"), self._v("m_nom"), self._v("m_ape"), self._v("m_cmp"),
                                       self._v("m_esp"), self._v("m_tel"))
            self._limpiar("m_dni", "m_cmp", "m_nom", "m_ape", "m_esp", "m_tel")
            self._refrescar_medicos()
        ejecutar(accion, "Profesional registrado.", self)

    def _refrescar_medicos(self):
        medicos = self._srv.listar_medicos()
        self._llenar(self._t_med, [(x.get_cmp(), x.nombre_completo(), x.get_especialidad()) for x in medicos])
        if self._cb_medico is not None:
            self._cb_medico["values"] = [x.get_cmp() for x in medicos]

    # ------------------------------------------------------------ RF-03/04/05 citas y turnos
    def _tab_citas(self, m):
        form = ttk.LabelFrame(m, text="Agendar cita", padding=8)
        form.pack(fill="x")
        ttk.Label(form, text="Documento").grid(row=0, column=0, sticky="e", padx=4, pady=3)
        ttk.Combobox(form, textvariable=self._var("c_tipo_doc", "DNI"), values=("DNI", "CE"),
                     width=7, state="readonly").grid(row=0, column=1, padx=3)
        ttk.Entry(form, textvariable=self._var("c_dni"), width=12).grid(row=0, column=2, padx=3)
        ttk.Label(form, text="Profesional (colegiatura)").grid(row=0, column=3, sticky="e", padx=4)
        self._cb_medico = ttk.Combobox(form, textvariable=self._var("c_cmp"), width=12, state="readonly")
        self._cb_medico.grid(row=0, column=4, padx=3)
        ttk.Label(form, text="Fecha (DD/MM/AAAA)").grid(row=0, column=5, sticky="e", padx=4)
        e = ttk.Entry(form, textvariable=self._var("c_fecha", fechas.formatear(date.today())), width=11)
        e.grid(row=0, column=6, padx=3)
        fecha_auto(self._vars["c_fecha"], e)
        ttk.Label(form, text="Hora (30 min)").grid(row=0, column=7, sticky="e", padx=4)
        horas = [f"{h:02d}:{mi:02d}" for h in range(8, 12) for mi in (0, 30)] + [
            f"{h:02d}:{mi:02d}" for h in range(14, 18) for mi in (0, 30)]
        self._cb_hora = ttk.Combobox(form, textvariable=self._var("c_turno", horas[0]),
                                    values=horas, width=7, state="readonly")
        self._cb_hora.grid(row=0, column=8, padx=3)
        bt = ttk.Frame(m)
        bt.pack(fill="x", pady=4)
        self._boton(bt, "Agendar cita", self._on_agendar, P.CITAS_GESTIONAR)
        self._boton(bt, "Emitir ticket de la cita elegida", self._on_emitir, P.TICKETS_EMITIR)
        self._boton(bt, "Cancelar cita elegida", self._on_cancelar, P.CITAS_GESTIONAR)
        self._boton(bt, "Ver cupos", self._on_cupos)
        self._boton(bt, "Actualizar lista", self._refrescar_citas)
        self._lbl_cupos = ttk.Label(m, text="Cupos: —")
        self._lbl_cupos.pack(anchor="w")
        self._t_cit = self._tabla(m, [("id", "ID cita"), ("pac", "Paciente"), ("med", "Profesional"), ("fecha", "Fecha"),
                                      ("hora", "Hora"), ("ticket", "N.º turno"), ("estado", "Estado")], alto=9)
        est = ttk.Frame(m)
        est.pack(fill="x")
        ttk.Label(est, text="Cambiar estado del turno elegido a:").pack(side="left")
        for estado in ESTADOS_TICKET:
            self._boton(est, _ETIQUETA_ESTADO.get(estado, estado.replace("_", " ").title()),
                        lambda x=estado: self._on_estado(x), P.TICKETS_ESTADO)

    def _cita_elegida(self):
        sel = self._t_cit.selection()
        if not sel:
            raise ErrorSistema("Seleccione primero una cita de la tabla.")
        return sel[0], self._t_cit.item(sel[0], "values")      # sel[0] es el ID de la cita (texto exacto)

    def _on_agendar(self):
        def accion():
            self._srv.agendar_cita(self._v("c_dni"), self._v("c_cmp"), self._fecha("c_fecha", "Fecha de la cita"),
                                   self._v("c_turno"), self._v("c_tipo_doc"))
            self._limpiar("c_dni")                      # médico, fecha y hora se conservan para agendar varias citas seguidas
            self._refrescar_citas()
            self._on_cupos()
        ejecutar(accion, "Cita agendada.", self)

    def _on_emitir(self):
        def accion():
            t = self._srv.emitir_ticket(self._cita_elegida()[0])
            self._refrescar_citas()
            messagebox.showinfo("Ticket emitido", f"Su número de turno es el {t.get_numero():03d}.", parent=self)
        ejecutar(accion, padre=self)

    def _on_cancelar(self):
        def accion():
            self._srv.cancelar_cita(self._cita_elegida()[0])
            self._refrescar_citas()
            self._on_cupos()
        ejecutar(accion, "Cita cancelada.", self)

    def _on_cupos(self):
        def accion():
            cupos = self._srv.consultar_cupos(self._v("c_cmp"), self._fecha("c_fecha", "Fecha", hoy_si_vacia=True))
            self._lbl_cupos.config(text="Cupos disponibles → " + "   ".join(f"{t}: {d}/{tot}" for t, (d, tot) in cupos.items()))
        ejecutar(accion, padre=self)

    def _on_estado(self, estado):
        def accion():
            id_cita, fila = self._cita_elegida()
            if estado == "NO_ASISTIO":                      # no exige ticket: el paciente pudo no llegar nunca
                self._srv.cambiar_estado_cita(id_cita, estado)
                self._refrescar_citas()
                return
            if fila[5] in ("", None):
                raise ErrorSistema("Esa cita aún no tiene ticket. Emítalo primero.")
            self._srv.cambiar_estado_ticket(fechas.parsear_fecha(fila[3], "Fecha"), int(fila[5]), estado)
            self._refrescar_citas()
        ejecutar(accion, padre=self)

    def _refrescar_citas(self):
        numeros = {t.get_cita().get_id(): f"{t.get_numero():03d}" for t in self._srv.listar_tickets()}
        citas = sorted(self._srv.listar_citas(), key=lambda c: (c.get_fecha(), c.get_hora()))
        filas = [(c.get_id(), c.get_paciente().get_dni_enmascarado(), c.get_medico().get_cmp(),
                  fechas.formatear(c.get_fecha()), c.get_hora(), numeros.get(c.get_id(), ""), c.estado_visible()) for c in citas]
        previa = self._t_cit.selection()
        self._llenar(self._t_cit, filas, iids=[c.get_id() for c in citas])
        if previa and self._t_cit.exists(previa[0]):               # conserva la cita elegida tras refrescar
            self._t_cit.selection_set(previa[0])

    # ------------------------------------------------------------ RF-06 reportes
    def _tab_reportes(self, m):
        bar = ttk.Frame(m)
        bar.pack(fill="x")
        ttk.Label(bar, text="Tipo").pack(side="left", padx=4)
        ttk.Combobox(bar, textvariable=self._var("r_tipo", "diario"), values=ReporteFactory.tipos_disponibles(),
                     width=10, state="readonly").pack(side="left")
        ttk.Label(bar, text="Fecha de referencia (DD/MM/AAAA)").pack(side="left", padx=6)
        e = ttk.Entry(bar, textvariable=self._var("r_fecha", fechas.formatear(date.today())), width=12)
        e.pack(side="left")
        fecha_auto(self._vars["r_fecha"], e)
        self._boton(bar, "Generar", self._on_reporte)
        self._boton(bar, "Exportar Excel", self._on_exportar_excel)
        self._boton(bar, "Guardar resumen TXT", self._on_exportar_txt)
        self._txt = tk.Text(m, height=20, state="disabled", wrap="word")
        self._txt.pack(fill="both", expand=True, pady=8)

    def _on_reporte(self):
        def accion():
            r = self._srv.generar_reporte(self._v("r_tipo"), self._fecha("r_fecha", "Fecha de referencia"))
            lineas = [f"Reporte {r['tipo']}: {r['desde']:%d/%m/%Y} al {r['hasta']:%d/%m/%Y}",
                      f"Atenciones realizadas: {r['total_atenciones']}", "", "Patologías más frecuentes (CIE-10):"]
            lineas += [f"  {i}. {cod}  —  {n} caso(s)" for i, (cod, n) in enumerate(r["patologias_frecuentes"], 1)] \
                or ["  (sin atenciones en el periodo)"]
            self._txt.config(state="normal")
            self._txt.delete("1.0", "end")
            self._txt.insert("1.0", "\n".join(lineas))
            self._txt.config(state="disabled")
        ejecutar(accion, padre=self)

    def _on_exportar_excel(self):
        ruta = filedialog.asksaveasfilename(parent=self, title="Guardar archivo Excel",
                                            defaultextension=".xlsx",
                                            filetypes=[("Libro de Excel", "*.xlsx")],
                                            initialfile="reporte_posta.xlsx", initialdir=self._carpeta_export())
        if not ruta:
            return
        ejecutar(lambda: self._srv.exportar_excel(ruta), "Archivo Excel exportado correctamente.", self)

    def _on_exportar_txt(self):
        ruta = filedialog.asksaveasfilename(parent=self, title="Guardar resumen de texto",
                                            defaultextension=".txt",
                                            filetypes=[("Archivo de texto", "*.txt")],
                                            initialfile="resumen_posta.txt", initialdir=self._carpeta_export())
        if not ruta:
            return
        ejecutar(lambda: self._srv.exportar_txt(ruta), "Resumen TXT guardado correctamente.", self)

    # ------------------------------------------------------------ usuarios y roles (solo administrador)
    def _tab_usuarios(self, m):
        form = ttk.LabelFrame(m, text="Nuevo usuario", padding=8)
        form.pack(fill="x")
        self._campos(form, [("u_usr", "Usuario"), ("u_nom", "Nombres"), ("u_ape", "Apellidos"),
                            ("u_col", "Colegiatura (si atiende)"), ("u_cla", "Contraseña temporal")],
                     columnas=3, ocultos=("u_cla",))
        ttk.Label(form, text="Rol").grid(row=1, column=4, sticky="e", padx=4, pady=3)
        ttk.Combobox(form, textvariable=self._var("u_rol"), values=list(self._rol_por_nombre), width=30,
                     state="readonly").grid(row=1, column=5, sticky="w", padx=4)
        bt = ttk.Frame(m)
        bt.pack(fill="x", pady=6)
        self._boton(bt, "Crear usuario", self._on_crear_usuario)
        self._boton(bt, "Activar / desactivar elegido", self._on_estado_usuario)
        self._boton(bt, "Cambiar rol del elegido (usa el rol de arriba)", self._on_cambiar_rol)
        self._boton(bt, "Restablecer contraseña", self._on_restablecer)
        ttk.Label(m, text="El usuario nuevo deberá cambiar su contraseña temporal la primera vez que ingrese. "
                          "Si el rol atiende pacientes, registre antes al profesional en la pestaña Profesionales "
                          "y escriba aquí su colegiatura.", foreground="#555555", wraplength=980).pack(anchor="w")
        self._t_usr = self._tabla(m, [("usr", "Usuario"), ("nom", "Nombre"), ("rol", "Rol"), ("grupo", "Grupo"),
                                      ("col", "Colegiatura"), ("est", "Estado"), ("acc", "Último acceso")], alto=10)

    def _usuario_elegido(self) -> str:
        sel = self._t_usr.selection()
        if not sel:
            raise ErrorSistema("Seleccione primero un usuario de la tabla.")
        return sel[0]

    def _on_crear_usuario(self):
        def accion():
            rol = self._rol_por_nombre.get(self._v("u_rol"))
            if rol is None:
                raise ErrorSistema("Elija el rol del usuario.")
            self._srv.crear_usuario(self._v("u_usr"), self._v("u_nom"), self._v("u_ape"), rol,
                                    self._vars["u_cla"].get(), self._v("u_col"))
            for clave in ("u_usr", "u_nom", "u_ape", "u_col", "u_cla"):
                self._vars[clave].set("")
            self._refrescar_usuarios()
        ejecutar(accion, "Usuario creado. Deberá cambiar su contraseña al ingresar.", self)

    def _on_estado_usuario(self):
        def accion():
            nombre = self._usuario_elegido()
            actual = next(u for u in self._srv.listar_usuarios() if u.get_nombre_usuario() == nombre)
            self._srv.cambiar_estado_usuario(nombre, not actual.esta_activo())
            self._refrescar_usuarios()
        ejecutar(accion, padre=self)

    def _on_cambiar_rol(self):
        def accion():
            rol = self._rol_por_nombre.get(self._v("u_rol"))
            if rol is None:
                raise ErrorSistema("Elija arriba el rol nuevo.")
            self._srv.cambiar_rol_usuario(self._usuario_elegido(), rol)
            self._refrescar_usuarios()
        ejecutar(accion, "Rol actualizado.", self)

    def _on_restablecer(self):
        def accion():
            nombre = self._usuario_elegido()
            nueva = simpledialog.askstring("Restablecer contraseña", f"Contraseña temporal para «{nombre}»:",
                                           show="•", parent=self)
            if nueva is None:
                return
            self._srv.restablecer_clave(nombre, nueva)
            messagebox.showinfo("Listo", "Contraseña restablecida. Deberá cambiarla al ingresar.", parent=self)
        ejecutar(accion, padre=self)

    def _refrescar_usuarios(self):
        ahora = datetime.now()
        usuarios = self._srv.listar_usuarios()
        estado = lambda u: ("Bloqueado" if u.bloqueado(ahora) else "Activo") if u.esta_activo() else "Desactivado"  # noqa: E731
        self._llenar(self._t_usr, [(u.get_nombre_usuario(), u.nombre_completo(), u.get_rol().nombre, u.get_rol().grupo,
                                    u.get_colegiatura() or "—", estado(u), fechas.formatear_fecha_hora(u.get_ultimo_acceso()))
                                   for u in usuarios], iids=[u.get_nombre_usuario() for u in usuarios])

    # ------------------------------------------------------------
    def _refrescar_todo(self):
        if self._t_pac is not None:
            self._refrescar_pacientes()
        if self._t_med is not None:
            self._refrescar_medicos()
        if self._t_cit is not None:
            self._refrescar_citas()
        if self._t_usr is not None:
            self._refrescar_usuarios()
