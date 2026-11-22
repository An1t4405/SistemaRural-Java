"""Carga datos FICTICIOS para probar el sistema antes de tener la posta.
Uso: python cargar_demo.py   (crea datos.enc y clave.key; bórrelos antes de usar datos reales)

Crea también un usuario de ejemplo por cada tipo de personal, todos con la contraseña de demostración
«Posta2026» (solo para probar los roles; NO use estas cuentas con datos reales)."""
from datetime import date, timedelta

from sistema_rural.errores import ErrorSistema
from sistema_rural.servicio import ServicioClinica

CLAVE_DEMO = "Posta2026"
s = ServicioClinica("datos/datos.enc", "datos/clave.key")


def intentar(operacion, *args, **kwargs):
    """Ignora el error si el dato de demostración ya existe (se puede ejecutar varias veces)."""
    try:
        operacion(*args, **kwargs)
    except ErrorSistema:
        pass


# ---- profesionales de salud (colegiatura -> CMP médicos, COP obstetras/odontólogos, CEP enfermeras)
for dni, nom, ape, col, esp in [("40000001", "Rosa", "Quispe Vera", "CMP-1001", "Medicina General"),
                                ("40000002", "Carlos", "Mendoza Ruiz", "CMP-1002", "Obstetricia"),
                                ("40000003", "Lucía", "Paz Ortiz", "CEP-3001", "Enfermería"),
                                ("40000004", "Mario", "Salas Díaz", "COP-4001", "Odontología")]:
    if col not in {m.get_cmp() for m in s.listar_medicos()}:
        s.registrar_medico(dni, nom, ape, col, esp)

# ---- pacientes y atenciones de ejemplo
if not s.listar_pacientes():
    for i, (n, a) in enumerate([("Ana", "Torres Gil"), ("Luis", "Paredes Soto"), ("María", "Castillo Ríos"),
                                ("José", "Alva Núñez"), ("Elena", "Rojas León")]):
        s.registrar_paciente(f"7000000{i}", n, a, date(1985 + i, 3, 10 + i), "Moche, La Libertad", f"95000000{i}")
    for i, cie in enumerate(["J00", "J00", "E11.9", "I10", "J20"]):
        s.registrar_atencion(f"7000000{i}", "CMP-1001", "Consulta de rutina", cie, date.today() - timedelta(days=i))
    manana = date.today() + timedelta(days=1)
    while manana.weekday() == 6:             # la posta no atiende domingos
        manana += timedelta(days=1)
    for i in range(3):
        s.emitir_ticket(s.agendar_cita(f"7000000{i}", "CMP-1001", manana, "MAÑANA").get_id())

# ---- un usuario por tipo de personal (usuario, nombres, apellidos, rol, colegiatura)
for usuario, nom, ape, rol, col in [("admin", "Ana", "Administradora", "ADMIN", ""),
                                    ("jefe", "Pedro", "Vásquez Lara", "JEFE", ""),
                                    ("admision", "Eva", "Ríos Cano", "ADMISION", ""),
                                    ("estadistica", "Iván", "Cruz Mora", "ESTADISTICA", ""),
                                    ("medico", "Rosa", "Quispe Vera", "MEDICO", "CMP-1001"),
                                    ("obstetra", "Carlos", "Mendoza Ruiz", "OBSTETRA", "CMP-1002"),
                                    ("enfermera", "Lucía", "Paz Ortiz", "ENFERMERA", "CEP-3001"),
                                    ("odontologo", "Mario", "Salas Díaz", "ODONTOLOGO", "COP-4001"),
                                    ("tecnica", "Rita", "Gómez Lino", "TEC_ENFERMERIA", ""),
                                    ("laboratorio", "Saúl", "Reyes Pino", "TEC_LABORATORIO", ""),
                                    ("farmacia", "Nora", "Lazo Vega", "TEC_FARMACIA", "")]:
    intentar(s.crear_usuario, usuario, nom, ape, rol, CLAVE_DEMO, col, debe_cambiar_clave=False)

print("Datos de demostración cargados.")
print(f"Usuarios de prueba: admin, jefe, admision, estadistica, medico, obstetra, enfermera, odontologo, "
      f"tecnica, laboratorio, farmacia  |  contraseña: {CLAVE_DEMO}")
