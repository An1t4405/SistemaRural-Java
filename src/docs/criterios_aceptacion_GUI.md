# Criterios de aceptación de la interfaz (Tema 5.3)

Cada componente interactivo de `VentanaPrincipal` se vincula con un evento, su handler y un criterio verificable.

| ID | Componente (pestaña) | Evento → handler | Criterio de aceptación | Cómo se verifica |
|---|---|---|---|---|
| CA-01 | Botón «Registrar» (Pacientes) | clic → `_on_registrar_paciente` | Con DNI de 8 dígitos y datos válidos, el paciente aparece en la tabla con el DNI enmascarado (`****1234`). | Prueba manual + `test_dni_no_queda_en_texto_plano` |
| CA-02 | Botón «Registrar» (Pacientes) | clic → `_on_registrar_paciente` | Si el DNI ya existe, se muestra un aviso y no se crea un duplicado (CE-02). | `test_ce02_dni_repetido_es_rechazado` |
| CA-03 | Campo «Nacimiento» | clic en Registrar | Una fecha mal escrita muestra «Fecha inválida» sin cerrar el programa. | Prueba manual |
| CA-04 | Botón «Buscar por DNI» / «Buscar» por nombre | clic → `_on_buscar_dni`, `_on_buscar_nombre` | Devuelve el paciente en menos de 3 s (CE-01); si no existe, avisa. | `test_ce01_busqueda_menor_a_3_segundos` |
| CA-05 | Botón «Registrar atención» (Historia clínica) | clic → `_on_registrar_atencion` | Solo acepta diagnóstico con formato CIE-10 (ej. `J00`, `E11.9`). | `test_cie10_invalido_se_rechaza` |
| CA-06 | Botón «Agendar cita» (Citas y turnos) | clic → `_on_agendar` | Si no hay cupos para ese médico, fecha y turno, se avisa y no se agenda (RF-03). | `test_cupos_se_agotan_y_se_liberan` |
| CA-07 | Botón «Emitir ticket» | clic → `_on_emitir` | El número de turno es correlativo y no se repite (CE-03). | `test_ce03_cien_tickets_correlativos_y_unicos` |
| CA-08 | Botones de estado (Reservado / En atención / Completado) | clic → `_on_estado` | El estado del turno cambia y se refleja en la tabla (RF-05). | `test_ticket_cambia_de_estado` |
| CA-09 | Botón «Generar» (Reportes) | clic → `_on_reporte` | Muestra total de atenciones y las 5 patologías más frecuentes del periodo elegido (RF-06). | `test_reportes_diario_semanal_mensual` |
| CA-10 | Cualquier botón | cualquier error | Los errores controlados se muestran en un cuadro de aviso; el programa no se cierra ni pierde datos. | `_ejecutar()` en `interfaz.py` |

| CA-11 | Selector «Hora (30 min)» (Citas y turnos) | clic → `_on_agendar` | Solo agenda dentro de 08:00–12:00 y 14:00–18:00; bloquea cruces para el mismo profesional. | `test_citas_respetan_horarios_y_no_se_superponen` |
| CA-12 | Botones «Exportar Excel» y «Guardar resumen TXT» (Reportes) | clic → `_on_exportar_excel`, `_on_exportar_txt` | Guarda los listados y resumen con DNI enmascarado. | `test_exportaciones_txt_y_excel` |
