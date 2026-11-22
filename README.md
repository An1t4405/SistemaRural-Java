# SistemaRural-PE · Java

Versión de escritorio en **Java 17+ y Swing**, desarrollada tomando como referencia el proyecto Python `SistemaRural-PE-SOLO-BUSCAR-DNI`. Conserva los módulos funcionales y reglas de negocio descritos en ese proyecto, con clases auxiliares separadas para validaciones y exportación XLSX.

## Ejecutar en Windows
1. Instalar JDK 17 o superior.
2. Descomprimir el ZIP.
3. Abrir la carpeta `SistemaRural-PE-Java`.
4. Ejecutar `ejecutar.bat`.

Compilación manual:
```bat
javac -encoding UTF-8 -d target/classes src/main/java/pe/sistemarural/*.java
java -cp target/classes pe.sistemarural.App
```

## Módulos y funcionalidades
- Inicio de sesión, creación del primer administrador, cambio obligatorio de contraseña temporal y cierre de sesión.
- Contraseñas PBKDF2-HMAC-SHA256 con sal aleatoria, bloqueo de cuenta tras cinco intentos fallidos y gestión de usuarios.
- Roles y permisos administrativos/asistenciales: ADMIN, JEFE, ADMISION, ESTADISTICA, MEDICO, OBSTETRA, ENFERMERA, ODONTOLOGO, PSICOLOGO, NUTRICIONISTA, TEC_ENFERMERIA, TEC_LABORATORIO y TEC_FARMACIA. ADMIN no accede a historias clínicas; Enfermería y demás roles conservan la matriz de permisos del proyecto Python.
- Pacientes: registro y actualización, DNI de 8 dígitos o Carné de Extranjería de 9–12 caracteres, búsqueda exclusiva por DNI, selección/carga de registros, tabla con documentos enmascarados y limpieza de formulario.
- Historias clínicas: alergias, antecedentes y atenciones con fecha, motivo, CMP y validación de código CIE-10.
- Profesionales de salud: registro por DNI, nombres, apellidos, CMP, especialidad y teléfono.
- Citas: lunes a sábado, hasta 90 días, bloques de 30 minutos de 08:00–12:00 y 14:00–18:00, control de citas pasadas, cruces de paciente/profesional y cupos por turno.
- Turnos y tickets: emisión correlativa por fecha, cancelación y estados RESERVADO, EN_ATENCION, COMPLETADO, NO_ASISTIO y CANCELADA; «No asistió» solo desde el inicio de la cita. Las citas pasadas sin cambio manual se muestran como vencidas, sin alterar su estado automáticamente.
- Reportes diario, semanal y mensual con total de atenciones y top 5 diagnósticos CIE-10.
- Exportación de reportes a **Excel `.xlsx` real** (hojas Resumen, Pacientes y Citas), resumen TXT y ficha individual Excel (Paciente, Atenciones y Citas). Los documentos se exportan enmascarados.
- Persistencia cifrada AES-256-GCM y carpetas de exportación creadas automáticamente.

## Pruebas
Compilar y ejecutar las pruebas básicas incluidas:
```bat
javac -encoding UTF-8 -d target/classes src/main/java/pe/sistemarural/*.java src/test/java/pe/sistemarural/*.java
java -cp target/classes pe.sistemarural.SmokeTests
```

Las pruebas Java incluidas cubren validaciones de DNI/CE, fechas reales, CIE-10, horarios y la estructura OOXML del archivo XLSX. El proyecto Python de referencia dispone de su propia batería de 86 pruebas; ese resultado no se atribuye a Java. La interfaz Swing debe probarse en el equipo Windows donde se ejecutará.

## Datos y compatibilidad
Al iniciar se crea `datos/` con `datos-java.enc` y `clave-java.key`. **Conserve ambos archivos juntos y haga copias de seguridad.** La versión Java utiliza un formato de almacenamiento propio: no abre automáticamente `datos.enc`/`clave.key` del proyecto Python y no debe sustituir esos archivos. Para pasar registros de una instalación Python, exporte los datos desde Python y realice una migración controlada; no copie la clave ni el archivo cifrado de un sistema al otro.

Las exportaciones se guardan en `datos/exportaciones/`. No use datos reales en pruebas; el proyecto de referencia utiliza datos ficticios.
