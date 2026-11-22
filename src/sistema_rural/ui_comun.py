"""Piezas de interfaz compartidas: manejo de errores, fechas con formato automático y cambio de clave."""
import tkinter as tk
from tkinter import messagebox, ttk

from .errores import ErrorSistema

COLOR_ADMIN = "#1F4E79"        # azul: personal administrativo
COLOR_ASISTENCIAL = "#1E7B5A"  # verde: personal asistencial


def ejecutar(accion, exito=None, padre=None):
    """Ejecuta un handler: los errores controlados se muestran sin cerrar el programa."""
    try:
        resultado = accion()
        if exito:
            messagebox.showinfo("Listo", exito, parent=padre)
        return resultado
    except ErrorSistema as e:
        messagebox.showwarning("Aviso", str(e), parent=padre)
    except Exception as e:  # error inesperado: se informa, no se pierde el trabajo
        messagebox.showerror("Error inesperado", f"{type(e).__name__}: {e}", parent=padre)


def fecha_auto(var: tk.StringVar, entrada: ttk.Entry):
    """Mientras se escribe, deja solo dígitos y pone las barras: 17051990 -> 17/05/1990."""
    def _formatear(*_):
        crudo = var.get()
        if len(crudo) >= 8 and crudo[4:5] == "-":      # se pegó una fecha AAAA-MM-DD: se respeta
            return
        d = "".join(c for c in crudo if c.isdigit())[:8]
        nuevo = d[:2] + ("/" + d[2:4] if len(d) > 2 else "") + ("/" + d[4:] if len(d) > 4 else "")
        if nuevo != crudo:
            var.set(nuevo)
            entrada.icursor("end")
    var.trace_add("write", _formatear)


class DialogoCambiarClave(tk.Toplevel):
    """Ventana modal para cambiar la contraseña. `guardar(actual, nueva)` hace el cambio real."""

    def __init__(self, padre, guardar, obligatorio=False):
        super().__init__(padre)
        self.title("Cambiar contraseña")
        self.resizable(False, False)
        self.transient(padre)
        self.resultado = False
        self._guardar = guardar
        self._vars = {k: tk.StringVar() for k in ("actual", "nueva", "repetir")}
        marco = ttk.Frame(self, padding=16)
        marco.pack()
        fila = 0
        if obligatorio:
            ttk.Label(marco, text="Por seguridad, elija una contraseña nueva antes de continuar.",
                      wraplength=320, foreground="#9A3412").grid(row=fila, column=0, columnspan=2, pady=(0, 8))
            fila += 1
        primera = None
        for clave, texto in (("actual", "Contraseña actual"), ("nueva", "Contraseña nueva"),
                             ("repetir", "Repetir la nueva")):
            ttk.Label(marco, text=texto).grid(row=fila, column=0, sticky="e", padx=4, pady=4)
            e = ttk.Entry(marco, textvariable=self._vars[clave], show="•", width=26)
            e.grid(row=fila, column=1, padx=4, pady=4)
            primera = primera or e
            fila += 1
        ttk.Label(marco, text="Mínimo 8 caracteres, combinando letras y números.",
                  foreground="#555555").grid(row=fila, column=0, columnspan=2, pady=(2, 8))
        botones = ttk.Frame(marco)
        botones.grid(row=fila + 1, column=0, columnspan=2)
        ttk.Button(botones, text="Guardar", command=self._aceptar).pack(side="left", padx=4)
        ttk.Button(botones, text="Cancelar", command=self.destroy).pack(side="left", padx=4)
        self.bind("<Return>", lambda _e: self._aceptar())
        self.bind("<Escape>", lambda _e: self.destroy())
        primera.focus_set()
        self.grab_set()
        self.wait_window()

    def _aceptar(self):
        actual, nueva, repetir = (self._vars[k].get() for k in ("actual", "nueva", "repetir"))

        def accion():
            if nueva != repetir:
                raise ErrorSistema("La contraseña nueva y su repetición no coinciden.")
            self._guardar(actual, nueva)
            return True

        if ejecutar(accion, "Contraseña actualizada.", padre=self):
            self.resultado = True
            self.destroy()
