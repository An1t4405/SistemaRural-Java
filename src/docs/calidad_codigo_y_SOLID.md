# Calidad del código, SOLID y buenas prácticas (insumo para [1.5] del informe)

## Principios SOLID aplicados (con ejemplos del código)
| Principio | Dónde se ve | Explicación |
|---|---|---|
| **S** – Responsabilidad única | `seguridad.py` solo cifra/hashea; `reportes.py` solo calcula reportes; `Ticket` solo representa un turno; `GeneradorTurnos` solo numera. | Cada módulo/clase tiene una razón para cambiar. |
| **O** – Abierto/cerrado | `ReporteFactory` + subclases de `Reporte` | Agregar un `ReporteAnual` = una subclase nueva y una entrada en `_tipos`; no se toca la interfaz ni el servicio. |
| **L** – Sustitución de Liskov | `ReporteDiario/Semanal/Mensual` sustituyen a `Reporte`; `Paciente` y `Medico` sustituyen a `Persona`. | El servicio llama `generar()` sin saber qué subclase es. |

**Limitaciones honestas (úselas en [1.6]):** `ServicioClinica` concentra operaciones *y* persistencia, lo que no cumple del todo S;
la interfaz depende directamente de la clase concreta `ServicioClinica` (D de SOLID solo parcial). Recomendación: extraer un
`RepositorioCifrado` y definir una interfaz (`Protocol`) para el servicio.

## Buenas prácticas (con ejemplos)
1. **Legibilidad y nombres en español** descriptivos: `cupos_disponibles`, `registrar_atencion`, `coincide_dni`.
2. **Modularidad**: paquete `sistema_rural` con módulos separados (`modelos`, `servicio`, `reportes`, `seguridad`, `interfaz`).
3. **Comentarios y docstrings estructurados en español** en cada módulo y clase.
4. **Manejo de errores propio**: jerarquía `ErrorSistema` → `ErrorValidacion`, `DNIDuplicado`, `NoEncontrado`, `CupoAgotado`.
5. **Encapsulamiento**: atributos con `_`, acceso con `get_`/`set_`, validación dentro de los setters.
6. **Funciones puras / inmutabilidad en reportes**: reciben una tupla de atenciones y devuelven un resultado sin modificarlas.
7. **Escritura atómica** de datos (`os.replace`) para no dejar el archivo a medias si falla la luz.
8. **Pruebas automatizadas** (pytest) que verifican los criterios CE-01, CE-02 y CE-03.

## Funciones de orden superior usadas sobre datos del sistema
- `filter` + `lambda`: `Reporte.generar` (atenciones del periodo) y `buscar_por_nombre`.
- `map` + `lambda`: `Reporte.generar` (extrae el diagnóstico de cada atención) y la carga de pacientes/médicos.
- `reduce`: `Reporte.generar` (cuenta casos por diagnóstico).
- `sorted(key=lambda ...)`: listados de pacientes, médicos y tickets.

## Consecuencias reales de baja calidad o exposición de datos (reflexión para [1.5])
- **Pacientes:** un diagnóstico o alergia filtrados pueden causar discriminación y pérdida de confianza; una historia duplicada o
  asociada al paciente equivocado puede derivar en un tratamiento incorrecto (por ejemplo, ignorar una alergia a la penicilina).
- **Personal de salud:** un sistema que falla o se cuelga en plena consulta añade carga y los expone a errores; sin pruebas, cada
  cambio puede romper algo sin que nadie lo note.
- **Datos personales (Ley N.° 29733):** los datos de salud son sensibles; por eso aquí el DNI, las alergias, los antecedentes y los
  diagnósticos se cifran, el DNI se muestra enmascarado y el archivo completo se guarda cifrado.
