# Roles y permisos de SistemaRural-PE

Cada rol agrupa permisos; el sistema comprueba el **permiso** en cada operación (patrón Proxy, `acceso.py`).
Lo que no está permitido queda **denegado por defecto**. Principio de mínimo privilegio: solo el personal que atiende pacientes ve las historias clínicas.

## Roles

### Personal administrativo

- **Administrador del sistema** (`ADMIN`): Administra el sistema: crea usuarios y asigna roles, registra a los profesionales y consulta reportes. No accede a las historias clínicas.
- **Jefe del establecimiento** (`JEFE`): Supervisa la posta: consulta pacientes, profesionales, citas y reportes. No modifica datos.
- **Admisión (personal administrativo)** (`ADMISION`): Recibe y registra a los pacientes, agenda y cancela citas y emite los tickets de turno.
- **Estadística e informática** (`ESTADISTICA`): Consulta pacientes y genera los reportes de atención para los informes del establecimiento.

### Personal asistencial

- **Médico(a)** (`MEDICO`): Atiende consultas: revisa y completa la historia clínica, registra atenciones con diagnóstico CIE-10 y genera reportes.
- **Obstetra** (`OBSTETRA`): Atiende control prenatal, planificación familiar y partos: revisa la historia clínica, registra sus atenciones y genera reportes.
- **Enfermero(a)** (`ENFERMERA`): Realiza triaje, procedimientos y controles (CRED, vacunas): revisa la historia clínica, registra alergias y antecedentes y sus atenciones.
- **Odontólogo(a)** (`ODONTOLOGO`): Atiende la salud bucal: revisa la historia clínica y registra sus atenciones.
- **Psicólogo(a)** (`PSICOLOGO`): Atiende salud mental: revisa la historia clínica y registra sus atenciones.
- **Nutricionista** (`NUTRICIONISTA`): Atiende consejería nutricional: revisa la historia clínica y registra sus atenciones.
- **Técnico(a) de enfermería** (`TEC_ENFERMERIA`): Apoya a enfermería: consulta pacientes y citas y actualiza el estado de los turnos (en atención, completado). No accede a la historia clínica.
- **Técnico(a) de laboratorio** (`TEC_LABORATORIO`): Consulta los datos del paciente y sus citas para identificar a quien se toman las muestras. No accede a la historia clínica.
- **Técnico(a) de farmacia** (`TEC_FARMACIA`): Consulta los datos del paciente y sus citas para la entrega de medicamentos. No accede a la historia clínica.

## Matriz de permisos

| Permiso | Administrador del sistema | Jefe del establecimiento | Admisión (personal administrativo) | Estadística e informática | Médico(a) | Obstetra | Enfermero(a) | Odontólogo(a) | Psicólogo(a) | Nutricionista | Técnico(a) de enfermería | Técnico(a) de laboratorio | Técnico(a) de farmacia |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Consultar pacientes | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Registrar pacientes nuevos |  |  | ✔ |  |  |  |  |  |  |  |  |  |  |
| Actualizar datos de pacientes |  |  | ✔ |  |  |  |  |  |  |  |  |  |  |
| Ver historias clínicas |  |  |  |  | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |
| Registrar alergias y antecedentes |  |  |  |  | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |
| Registrar atenciones y diagnósticos (CIE-10) |  |  |  |  | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |  |
| Consultar profesionales de salud | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Registrar profesionales de salud | ✔ |  |  |  |  |  |  |  |  |  |  |  |  |
| Consultar citas, turnos y cupos | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Agendar y cancelar citas | ✔ |  | ✔ |  |  |  |  |  |  |  |  |  |  |
| Emitir tickets de turno |  |  | ✔ |  |  |  |  |  |  |  |  |  |  |
| Actualizar el estado de los turnos |  |  | ✔ |  | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |  |  |
| Generar reportes de atención | ✔ | ✔ |  | ✔ | ✔ | ✔ |  |  |  |  |  |  |  |
| Administrar usuarios y roles | ✔ |  |  |  |  |  |  |  |  |  |  |  |  |

## Reglas de seguridad del acceso

- Contraseñas: mínimo 8 caracteres con letras y números; se guardan solo como hash PBKDF2-HMAC-SHA256 con sal aleatoria.
- Bloqueo de 5 minutos tras 5 intentos fallidos; mensaje genérico ante usuario o contraseña incorrectos.
- Las cuentas nuevas y las restablecidas usan una contraseña temporal: se debe cambiar al primer ingreso.
- Siempre debe quedar al menos un administrador activo; nadie puede desactivarse a sí mismo.
- Las atenciones se registran a nombre del profesional que inició sesión (su colegiatura).
- Una cuenta desactivada o con rol cambiado pierde (o cambia) sus permisos de inmediato, aunque tenga la sesión abierta.

## Reglas de fechas

- Se escriben como DD/MM/AAAA (también se acepta AAAA-MM-DD); se rechazan fechas inexistentes como 31/02.
- Nacimiento: no puede ser futuro ni implicar más de 120 años.
- Citas: no pueden ser pasadas ni con más de 90 días de anticipación.
- Atenciones: no pueden ser futuras ni anteriores al nacimiento del paciente.
- Reportes: la fecha de referencia no puede ser futura.


## Ajuste de usabilidad (noviembre de 2026)

El rol **Administrador del sistema** también puede registrar y actualizar los datos básicos
(demográficos y de contacto) de pacientes, para facilitar el trabajo en establecimientos pequeños.
Este permiso no habilita el acceso a historias clínicas ni a diagnósticos: esa información continúa
reservada al personal asistencial autorizado. El rol **Administrador** también puede gestionar citas y turnos para facilitar pruebas y operación en una posta pequeña, sin acceder a historias clínicas. El rol **Admisión** mantiene sus permisos de recepción, registro de pacientes y gestión de citas.

La pantalla Inicio se simplificó: se retiró la lista de permisos y la descripción extensa del rol,
porque son información administrativa que no necesita mostrarse durante el trabajo cotidiano.


## Identificación de pacientes

El formulario admite dos tipos de documento: DNI (8 dígitos) y Carné de Extranjería (9 a 12 caracteres alfanuméricos). El tipo y número se guardan cifrados; la tabla y las exportaciones muestran únicamente el número enmascarado. Los registros antiguos se interpretan como DNI para conservar la compatibilidad.
