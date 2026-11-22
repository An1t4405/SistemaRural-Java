"""Muestra los pacientes guardados en datos.enc (descifrados).
Uso: ponga este archivo junto a main.py y ejecútelo (botón ▶ de VS Code o `py ver_datos.py`).
OJO: muestra el DNI completo. Úselo solo con datos ficticios."""
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))  # para encontrar sistema_rural aunque se ejecute desde otra carpeta

from sistema_rural import seguridad  # noqa: E402

# Busca el formato actual (datos/) y el formato antiguo junto al proyecto.
candidatas = [AQUI / "datos", AQUI, Path.cwd() / "datos", Path.cwd(), AQUI.parent]
carpeta = next((d for d in candidatas if (d / "datos.enc").exists() and (d / "clave.key").exists()), None)
if carpeta is None:
    print("No encontré datos.enc y clave.key.")
    print("Primero ejecute main.py (y registre un paciente) o cargar_demo.py.")
    print("Carpetas donde busqué:")
    for d in dict.fromkeys(candidatas):
        print("  -", d)
    sys.exit(1)

print(f"Leyendo: {carpeta / 'datos.enc'}")
c = seguridad.configurar(str(carpeta / "clave.key"))
datos = json.loads(c.descifrar_bytes((carpeta / "datos.enc").read_bytes()))

pacientes = datos["pacientes"]
print(f"\n=== PACIENTES GUARDADOS: {len(pacientes)} ===\n")
for i, p in enumerate(pacientes, 1):
    print(f"{i}. {p['apellidos']}, {p['nombres']}")
    print(f"   DNI: {p['dni']}  |  Nacimiento: {p['fecha_nacimiento']}")
    print(f"   Teléfono: {p['telefono'] or '-'}  |  Dirección: {p['direccion'] or '-'}")
    h = p["historia"]
    print(f"   Alergias: {h['alergias'] or '-'}  |  Antecedentes: {h['antecedentes'] or '-'}")
    for a in h["atenciones"]:
        print(f"   · Atención {a['fecha']}: {a['motivo']} (CIE-10: {a['diagnostico']})")
    print()

usuarios = datos.get("usuarios", [])
print(f"=== USUARIOS DEL SISTEMA: {len(usuarios)} (las contraseñas no se muestran: solo se guarda su hash) ===\n")
for u in usuarios:
    print(f"- {u['usuario']:14s} {u['apellidos']}, {u['nombres']}  |  rol: {u['rol']}  |  colegiatura: {u['colegiatura'] or '-'}  |  {'activo' if u['activo'] else 'DESACTIVADO'}")
