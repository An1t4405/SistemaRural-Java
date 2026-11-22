"""Pantalla de inicio de sesión. En el primer uso pide crear la cuenta del Administrador."""
import tkinter as tk
from tkinter import ttk

from .errores import ErrorSistema
from .servicio import ServicioClinica
from .ui_comun import COLOR_ADMIN, DialogoCambiarClave, ejecutar


class VentanaLogin(tk.Tk):
    def __init__(self, servicio: ServicioClinica):
        super().__init__()
        self._srv = servicio
        self.usuario = None                      # se llena si el ingreso fue exitoso
        self._primer_uso = not servicio.hay_usuarios()
        self._vars: dict[str, tk.StringVar] = {}
        self.title("SistemaRural-PE · Iniciar sesión")
        self.resizable(False, False)

        cab = tk.Frame(self, bg=COLOR_ADMIN)
        cab.pack(fill="x")
        tk.Label(cab, text="SistemaRural-PE", bg=COLOR_ADMIN, fg="white", font=("Segoe UI", 18, "bold")).pack(pady=(14, 0))
        tk.Label(cab, text="Posta Médica Rural", bg=COLOR_ADMIN, fg="#D6E4F0", font=("Segoe UI", 10)).pack(pady=(0, 14))

        marco = ttk.Frame(self, padding=22)
        marco.pack()
        if self._primer_uso:
            ttk.Label(marco, text="Primer uso: cree la cuenta del Administrador del sistema.",
                      wraplength=340, font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10))
            campos = [("l_usuario", "Usuario", False), ("l_nom", "Nombres", False), ("l_ape", "Apellidos", False),
                      ("l_clave", "Contraseña", True), ("l_clave2", "Repetir contraseña", True)]
            texto_boton = "Crear administrador e ingresar"
        else:
            campos = [("l_usuario", "Usuario", False), ("l_clave", "Contraseña", True)]
            texto_boton = "Ingresar"
        primera = None
        for i, (clave, texto, oculto) in enumerate(campos, start=1):
            ttk.Label(marco, text=texto).grid(row=i, column=0, sticky="e", padx=6, pady=5)
            self._vars[clave] = tk.StringVar()
            e = ttk.Entry(marco, textvariable=self._vars[clave], width=28, show="•" if oculto else "")
            e.grid(row=i, column=1, padx=6, pady=5)
            primera = primera or e
        ttk.Button(marco, text=texto_boton, command=self._on_ingresar).grid(
            row=len(campos) + 1, column=0, columnspan=2, pady=(14, 4), ipadx=10, ipady=3)
        if self._primer_uso:
            ttk.Label(marco, text="Mínimo 8 caracteres, combinando letras y números.", foreground="#555555").grid(
                row=len(campos) + 2, column=0, columnspan=2)
        ttk.Label(self, text=f"Datos: {servicio.ruta_datos()}", foreground="#777777", wraplength=380,
                  font=("Segoe UI", 8)).pack(padx=10, pady=(0, 8))
        self.bind("<Return>", lambda _e: self._on_ingresar())
        primera.focus_set()
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.winfo_height()) // 3
        self.geometry(f"+{x}+{y}")

    def _on_ingresar(self):
        def accion():
            nombre, clave = self._vars["l_usuario"].get(), self._vars["l_clave"].get()   # la clave no se recorta
            if self._primer_uso:
                if clave != self._vars["l_clave2"].get():
                    raise ErrorSistema("Las contraseñas no coinciden.")
                self._srv.crear_primer_administrador(nombre, self._vars["l_nom"].get(), self._vars["l_ape"].get(), clave)
            u = self._srv.autenticar(nombre, clave)
            if u.debe_cambiar_clave():
                dlg = DialogoCambiarClave(self, lambda actual, nueva: self._srv.cambiar_clave(
                    u.get_nombre_usuario(), actual, nueva), obligatorio=True)
                if not dlg.resultado:
                    raise ErrorSistema("Debe cambiar su contraseña para poder ingresar.")
            self.usuario = u
            self.destroy()
        ejecutar(accion, padre=self)
