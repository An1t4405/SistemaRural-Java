# SistemaRural-PE

Módulo de software de código abierto para digitalizar el registro de pacientes, historias clínicas,
citas, turnos y reportes de una posta médica rural (Python 3 + Tkinter).

## Instalación y uso
```
pip install -r requirements.txt
python cargar_demo.py     # (opcional) datos y usuarios FICTICIOS para probar
python main.py            # abre el inicio de sesión y luego el menú según el rol
python ver_datos.py       # muestra el contenido descifrado de datos.enc (solo con datos de prueba)
python -m pytest -v       # pruebas automatizadas (CE-01, CE-02, CE-03, RD-02...)
python medir_recursos.py  # evidencia de CE-01 y RD-03
```
En Linux puede faltar Tkinter: `sudo apt install python3-tk`.
**Primer uso:** si no hay usuarios, `main.py` pide crear la cuenta del Administrador. Con `cargar_demo.py` se crean
cuentas de prueba (`admin`, `admision`, `medico`, `enfermera`, `tecnica`...) con la contraseña de demostración `Posta2026`.
**Importante:** los archivos se guardan en la carpeta `datos/`: `datos.enc` contiene la información cifrada y
`clave.key` es la llave de cifrado. Sin ella no se puede abrir la información; haga una copia segura de ambos
y no suba la carpeta `datos/` a GitHub. Para Excel se utiliza `openpyxl` (incluido en `requirements.txt`).

## Estructura (trazabilidad con el informe)
| Archivo | Contenido | Requisito |
|---|---|---|
| `sistema_rural/seguridad.py` | Cifrado Fernet, hash HMAC de DNI/CE, enmascarado | RD-02, DM-01, DM-05 |
| `sistema_rural/modelos.py` | Persona (abstracta), Paciente, Medico, HistoriaClinica, Atencion, AgendaMedica, Cita, Ticket, **GeneradorTurnos (Singleton)** | DD-01, RF-01 a RF-05 |
| `sistema_rural/reportes.py` | Reporte (abstracta), Diario/Semanal/Mensual, **ReporteFactory** (map/filter/reduce/lambda) | DD-02, RF-06 |
| `sistema_rural/servicio.py` | ServicioClinica: operaciones + persistencia cifrada | RF-01 a RF-06 |
| `sistema_rural/usuarios.py` | Roles, permisos, Usuario, hash de contraseñas (PBKDF2), bloqueo por intentos | RD-02 |
| `sistema_rural/acceso.py` | **ServicioProtegido (Proxy)**: verifica el permiso del rol en cada operación | RD-02 |
| `sistema_rural/fechas.py` | Validación de fechas (formato, existencia, reglas de negocio) | RD-04 |
| `sistema_rural/login.py`, `ui_comun.py` | Inicio de sesión, cambio de contraseña, fechas con formato automático | DD-03 |
| `sistema_rural/interfaz.py` | VentanaPrincipal: menú y pestañas según el rol; solo handlers que delegan al servicio protegido | DD-03, RD-04 |
| `tests/test_acceso.py` | pytest: login, roles/permisos, fechas | RD-02 |
| `tests/test_sistema.py` | pytest | CE-01, CE-02, CE-03 |

## Paradigmas
- **POO**: entidades del dominio con atributos privados (`_x`) y getters/setters; herencia, composición, agregación.
- **Funcional**: reportes y búsquedas con `map`, `filter`, `reduce`, `lambda`, sin modificar las historias.
- **Eventos**: `Tkinter` con handlers (`_on_*`) y `try/except` central en `_ejecutar`.
- **Estructurado**: validaciones y secuencias dentro de los métodos (DD-04).

## Documentos de apoyo para el informe
- `docs/roles_y_permisos.md`: roles, matriz de permisos, reglas de seguridad y de fechas.
- `docs/criterios_aceptacion_GUI.md`: componente → evento → criterio → prueba (Tema 5.3).
- `docs/calidad_codigo_y_SOLID.md`: SOLID, buenas prácticas, funciones de orden superior y reflexión sobre usuarios ([1.5]).
- `docs/resultado_pruebas.txt`: resultado de `pytest -v` (vuelva a generarlo con `python -m pytest -v > docs/resultado_pruebas.txt` tras los cambios de roles).

## Subir el repositorio a GitHub (debe ser público)
```
git remote add origin https://github.com/SU_USUARIO/SistemaRural-PE.git
git branch -M main
git push -u origin main
```
Los datos del sistema son **ficticios** (`cargar_demo.py`); no se usan datos reales de pacientes.


## Mejoras operativas
- **Identificación:** los pacientes pueden registrarse con DNI (8 dígitos) o Carné de Extranjería (9 a 12 caracteres alfanuméricos); el tipo y número se cifran y se muestran enmascarados. Los registros antiguos con DNI siguen siendo compatibles.
- **Agenda por hora:** citas de 30 minutos, de 08:00 a 12:00 y de 14:00 a 18:00. No se ofrecen citas durante el descanso (12:00–14:00), ni fuera del horario. Un mismo profesional no puede tener citas que se crucen; profesionales distintos sí pueden atender a la misma hora.
- **Compatibilidad:** los registros antiguos que solo almacenaban el turno se pueden cargar; las nuevas citas conservan la hora exacta.
- **Exportación:** desde Reportes se puede guardar un libro Excel (`.xlsx`) con hojas de pacientes y citas, y un resumen de actividad `.txt`. El documento se exporta enmascarado.
- **Almacenamiento organizado:** la aplicación crea automáticamente `datos/` al iniciar y almacena allí el archivo cifrado y la clave.
- **Carpeta de exportaciones:** todo Excel/TXT se guarda por defecto en `datos/exportaciones/` (se crea sola) con fecha y hora en el nombre.
- **Ficha del paciente en Excel:** en la pestaña Pacientes, escriba el documento y pulse «Descargar ficha (Excel)». Admisión/secretaría obtiene datos personales y citas; los roles con acceso a historia clínica reciben además alergias, antecedentes y atenciones. El documento sale enmascarado.
- **Validación de horarios:** citas de 30 min (08:00–11:30 y 14:00–17:30, lunes a sábado); no se cruzan las citas de un mismo profesional **ni las de un mismo paciente con otro profesional**; no se acepta una hora que ya pasó hoy.
- **Validación de fechas:** se rechazan fechas inexistentes (31/02), pasadas, domingos o a más de 90 días; la fecha de nacimiento no puede ser futura.
- **Estados de la cita:** RESERVADO → EN_ATENCION → COMPLETADO, además de NO_ASISTIO y CANCELADA. El estado no cambia solo con la hora: una cita pasada que nadie marcó se muestra como «VENCIDA (sin atender)» hasta que admisión o el profesional la marque como Completado o No asistió (No asistió solo desde la hora de la cita).
- **Formularios:** tras registrar o actualizar un paciente, profesional o atención con éxito, los campos se vacían para el siguiente registro (si hay un error, se conservan para corregirlos). En Pacientes hay además un botón «Limpiar formulario».
- **Uso por secretaría:** el rol `ADMISION` registra pacientes, agenda/cancela citas, emite tickets y descarga fichas, sin acceso a historias clínicas.


## Días y horario de atención

La agenda permite reservar citas de lunes a sábado. Los domingos se consideran días no laborables y el sistema rechaza las reservas en esas fechas. Se mantienen los turnos de 08:00 a 12:00 y de 14:00 a 18:00, con citas de 30 minutos.


## Uso de la pestaña Pacientes (flujo corregido)
- Para modificar un registro, seleccione primero al paciente en la tabla: sus datos y documento se cargarán en el formulario. Luego pulse **Actualizar**.
- **Buscar por DNI** consulta el tipo y número de documento ingresados y carga el registro en el formulario.
- **Buscar** requiere escribir un nombre o apellido; si no hay coincidencias, muestra un aviso.
- **Ver todos** vuelve a mostrar la lista completa.
- La tabla conserva el documento enmascarado; el identificador interno usado para seleccionar una fila es un hash y no revela el documento real.
