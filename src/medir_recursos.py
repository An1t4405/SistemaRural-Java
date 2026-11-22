"""Evidencia para CE-01 (búsqueda < 3 s) y RD-03 (< 256 MB de RAM).
Uso: python medir_recursos.py
Para medir la ventana gráfica completa use además el Administrador de tareas (Windows) o `ps`/`top` (Linux)
con main.py abierto y cópielo en el informe."""
import statistics
import tempfile
import time
import tracemalloc
from datetime import date
from pathlib import Path

from sistema_rural.modelos import Paciente
from sistema_rural.servicio import ServicioClinica

try:
    import resource  # solo Linux/macOS
except ImportError:
    resource = None

N_PACIENTES, N_BUSQUEDAS = 2000, 20
with tempfile.TemporaryDirectory() as d:
    tracemalloc.start()
    s = ServicioClinica(Path(d) / "d.enc", Path(d) / "k.key")
    for i in range(N_PACIENTES):
        p = Paciente(f"{30_000_000 + i:08d}", f"Nombre{i}", f"Apellido{i}", date(1990, 1, 1))
        s._pacientes[p.get_dni_hash()] = p
    tiempos = []
    for i in range(0, N_PACIENTES, N_PACIENTES // N_BUSQUEDAS):
        t0 = time.perf_counter()
        s.buscar_por_dni(f"{30_000_000 + i:08d}")
        tiempos.append(time.perf_counter() - t0)
    _, pico = tracemalloc.get_traced_memory()

print(f"Pacientes cargados: {N_PACIENTES} | búsquedas: {len(tiempos)}")
print(f"CE-01  tiempo medio: {statistics.mean(tiempos)*1000:.4f} ms | máximo: {max(tiempos)*1000:.4f} ms | meta: < 3000 ms")
print(f"       resultado: {'CUMPLE' if max(tiempos) < 3 else 'NO CUMPLE'}")
print(f"RD-03  memoria pico (objetos Python): {pico/1024/1024:.2f} MB | meta: < 256 MB")
if resource:
    kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    mb = kb / 1024 if kb < 10**8 else kb / 1024 / 1024  # Linux: KB, macOS: bytes
    print(f"       RAM máxima del proceso: {mb:.1f} MB -> {'CUMPLE' if mb < 256 else 'NO CUMPLE'}")
