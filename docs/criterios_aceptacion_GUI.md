# Criterios de aceptación de la interfaz (Tema 5.3)

Cada componente interactivo de `VentanaPrincipal` se vincula con un evento (`ActionListener`), su handler y un criterio verificable.

| ID | Componente (pestaña) | Evento → handler | Criterio de aceptación | Cómo se verifica |
|---|---|---|---|---|
| CA-01 | Botón «Registrar» (Pacientes) | clic → `onRegistrarPaciente` | Con DNI de 8 dígitos y datos válidos, el paciente aparece en la tabla con el DNI enmascarado (`****1234`). | Prueba manual + `dniNoQuedaEnTextoPlano` |
| CA-02 | Botón «Registrar» (Pacientes) | clic → `onRegistrarPaciente` | Si el DNI ya existe, se muestra un aviso y no se crea un duplicado (CE-02). | `ce02DniRepetidoEsRechazado` |
| CA-03 | Campo «Nacimiento» | clic en Registrar | Una fecha mal escrita muestra «Fecha inválida» sin cerrar el programa. | Prueba manual |
| CA-04 | Botones «Buscar por DNI» / «Buscar» por nombre | clic → `onBuscarDni`, `onBuscarNombre` | Devuelve el paciente en menos de 3 s (CE-01); si no existe, avisa. | `ce01BusquedaMenorA3Segundos` |
| CA-05 | Botón «Registrar atención» (Historia clínica) | clic → `onRegistrarAtencion` | Solo acepta diagnóstico con formato CIE-10 (ej. `J00`, `E11.9`). | `cie10InvalidoSeRechaza` |
| CA-06 | Botón «Agendar cita» (Citas y turnos) | clic → `onAgendar` | Si no hay cupos para ese médico, fecha y turno, se avisa y no se agenda (RF-03). | `cuposSeAgotanYSeLiberan` |
| CA-07 | Botón «Emitir ticket» | clic → `onEmitir` | El número de turno es correlativo y no se repite (CE-03). | `ce03CienTicketsCorrelativosYUnicos` |
| CA-08 | Botones de estado (Reservado / En atención / Completado) | clic → `onEstado` | El estado del turno cambia y se refleja en la tabla (RF-05). | `ticketCambiaDeEstado` |
| CA-09 | Botón «Generar» (Reportes) | clic → `onReporte` | Muestra total de atenciones y las 5 patologías más frecuentes del periodo elegido (RF-06). | `reportesDiarioSemanalMensual` |
| CA-10 | Cualquier botón | cualquier error | Los errores controlados se muestran en un cuadro de aviso; el programa no se cierra ni pierde datos. | método `ejecutar()` en `VentanaPrincipal` |
