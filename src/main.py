"""Punto de entrada: python main.py  (abre el inicio de sesión y luego el menú según el rol)"""
from sistema_rural.acceso import ServicioProtegido
from sistema_rural.interfaz import VentanaPrincipal
from sistema_rural.login import VentanaLogin
from sistema_rural.servicio import ServicioClinica


def main():
    servicio = ServicioClinica("datos/datos.enc", "datos/clave.key")
    while True:
        login = VentanaLogin(servicio)
        login.mainloop()
        if login.usuario is None:          # cerró la ventana de login: salir
            break
        app = VentanaPrincipal(ServicioProtegido(servicio, login.usuario), login.usuario)
        app.mainloop()
        if not app.cerrar_sesion:          # cerró la ventana principal: salir
            break                          # (si pidió "Cerrar sesión" se vuelve al login)


if __name__ == "__main__":
    main()
