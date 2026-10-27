# SistemaRural-PE (versión Java)

Módulo de software de código abierto para digitalizar el registro de pacientes, historias clínicas, citas, turnos y reportes de una
posta médica rural. **Java 17 + Swing + Maven**, sin librerías externas (solo JUnit 5 para las pruebas).

## Abrir y ejecutar en Apache NetBeans
Requisitos: **JDK 17 o superior** (NetBeans → *Tools → Java Platforms* para verificar) e internet la primera vez (Maven descarga JUnit).

1. *File → Open Project…* y elija la carpeta `SistemaRural-PE-Java` (se reconoce por el ícono de Maven).
2. Espere a que NetBeans termine de cargar (barra de progreso abajo a la derecha).
3. **Datos de ejemplo (opcional):** en *Projects → Source Packages → pe.sistemarural*, clic derecho en `CargarDemo.java` → *Run File* (Shift+F6).
4. **Abrir el sistema:** clic derecho en el proyecto → *Run* (F6), o clic derecho en `Main.java` → *Run File*.
5. **Pruebas automáticas:** clic derecho en el proyecto → *Test* (Alt+F6). Los resultados salen en la ventana *Test Results*.
6. **Evidencia de CE-01 y RD-03:** clic derecho en `MedicionRecursos.java` → *Run File*.

Los archivos `datos.enc` y `clave.key` se crean en la carpeta del proyecto. **Sin `clave.key` no se pueden recuperar los datos**:
respáldelos y no los suba a GitHub (ya están en `.gitignore`). Todos los datos de ejemplo son **ficticios**.

## Estructura (trazabilidad con el informe)
| Paquete / clase | Contenido | Requisito |
|---|---|---|
| `seguridad.Cifrador`, `seguridad.Dni` | Cifrado AES-256-GCM, hash HMAC del DNI, enmascarado | RD-02, DM-01, DM-05 |
| `modelo` | `Persona` (abstracta), `Paciente`, `Medico`, `HistoriaClinica`, `Atencion`, `AgendaMedica`, `Cita`, `Ticket`, **`GeneradorTurnos` (Singleton)** | DD-01, RF-01 a RF-05 |
| `reportes` | `Reporte` (abstracta), Diario/Semanal/Mensual, **`ReporteFactory`** (streams: filter/map/reduce) | DD-02, RF-06 |
| `servicio.ServicioClinica` | Operaciones del sistema + persistencia cifrada | RF-01 a RF-06 |
| `ui.VentanaPrincipal` | Swing: solo handlers de eventos que delegan al servicio | DD-03, RD-04 |
| `src/test/.../ServicioClinicaTest` | JUnit 5 | CE-01, CE-02, CE-03 |

## Paradigmas
- **POO**: clases con atributos privados y getters/setters; herencia, composición, agregación.
- **Funcional**: reportes y búsquedas con `Stream` (`filter`, `map`, `reduce`) y lambdas, sin modificar las historias.
- **Eventos**: Swing con `ActionListener` (handlers `on...`) y un `try/catch` central en `ejecutar()`.

## Documentos de apoyo para el informe
- `docs/criterios_aceptacion_GUI.md`: componente → evento → criterio → prueba (Tema 5.3).
- `docs/calidad_codigo_y_SOLID.md`: SOLID, buenas prácticas, funciones de orden superior y reflexión sobre usuarios ([1.5]).
- `docs/resultado_pruebas.txt`: resultado de la ejecución de las pruebas (evidencia de pruebas automatizadas).

## Subir el repositorio a GitHub (debe ser público)
```
git remote add origin https://github.com/SU_USUARIO/SistemaRural-PE.git
git branch -M main
git push -u origin main
```
