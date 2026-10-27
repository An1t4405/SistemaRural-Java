# Calidad del código, SOLID y buenas prácticas (insumo para [1.5] del informe)

## Principios SOLID aplicados (con ejemplos del código)
| Principio | Dónde se ve | Explicación |
|---|---|---|
| **S** – Responsabilidad única | `Cifrador` solo cifra/hashea; `Dni` solo valida; `Reporte` solo calcula reportes; `Ticket` solo representa un turno; `GeneradorTurnos` solo numera. | Cada clase tiene una única razón para cambiar. |
| **O** – Abierto/cerrado | `ReporteFactory` + subclases de `Reporte` | Agregar un `ReporteAnual` = una subclase nueva y una línea en `TIPOS`; no se toca la interfaz ni el servicio. |
| **L** – Sustitución de Liskov | `ReporteDiario/Semanal/Mensual` sustituyen a `Reporte`; `Paciente` y `Medico` sustituyen a `Persona`. | El servicio llama `generar()` sin saber qué subclase es. |

**Limitaciones honestas (úselas en [1.6]):**
- `ServicioClinica` concentra operaciones *y* persistencia, lo que no cumple del todo S.
- La interfaz depende directamente de la clase concreta `ServicioClinica` (D de SOLID solo parcial).
- La persistencia usa serialización de Java cifrada con AES-GCM; funciona y es segura frente a manipulación (el cifrado
  autenticado detecta cambios, y se limita qué clases pueden leerse con `ObjectInputFilter`), pero un formato como JSON o una base
  de datos sería más portable y fácil de migrar.

Recomendación: extraer un `RepositorioCifrado` y definir una interfaz para el servicio.

## Buenas prácticas (con ejemplos)
1. **Legibilidad y nombres en español** descriptivos: `cuposDisponibles`, `registrarAtencion`, `coincideDni`.
2. **Modularidad**: paquetes `modelo`, `servicio`, `reportes`, `seguridad`, `errores`, `ui`.
3. **Comentarios Javadoc estructurados en español** en cada clase.
4. **Manejo de errores propio**: jerarquía `ErrorSistema` → `ErrorValidacion`, `DniDuplicado`, `NoEncontrado`, `CupoAgotado`.
5. **Encapsulamiento**: atributos `private`, acceso con getters/setters, validación dentro de los setters, listas devueltas como copias de solo lectura.
6. **Inmutabilidad / funciones sin efectos secundarios**: los reportes devuelven un `record` inmutable y no modifican las historias.
7. **Escritura atómica** de datos (`Files.move` desde un archivo temporal) para no dejar el archivo a medias si falla la luz.
8. **Pruebas automatizadas** (JUnit 5) que verifican CE-01, CE-02 y CE-03.

## Funciones de orden superior (streams y lambdas) sobre datos del sistema
- `filter` + lambda: `Reporte.generar` (atenciones del periodo), `buscarPorNombre`, `AgendaMedica.cuposDisponibles`.
- `map` + lambda / referencia a método: `Atencion::getDiagnostico` en `Reporte.generar` y filas de las tablas.
- `reduce`: `Reporte.generar` (total de atenciones) y `collect(groupingBy(...))` para contar por diagnóstico.
- `sorted(...)` con comparadores lambda en listados de pacientes, médicos, citas y tickets.

## Consecuencias reales de baja calidad o exposición de datos (reflexión para [1.5])
- **Pacientes:** un diagnóstico o alergia filtrados pueden causar discriminación y pérdida de confianza; una historia duplicada o
  asociada al paciente equivocado puede derivar en un tratamiento incorrecto (por ejemplo, ignorar una alergia a la penicilina).
- **Personal de salud:** un sistema que falla o se cuelga en plena consulta añade carga y los expone a errores; sin pruebas, cada
  cambio puede romper algo sin que nadie lo note.
- **Datos personales (Ley N.° 29733):** los datos de salud son sensibles; por eso aquí el DNI, las alergias, los antecedentes y los
  diagnósticos se cifran, el DNI se muestra enmascarado y el archivo completo se guarda cifrado.
