package pe.sistemarural.servicio;

import java.io.Serializable;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import pe.sistemarural.modelo.AgendaMedica;
import pe.sistemarural.modelo.Medico;
import pe.sistemarural.modelo.Paciente;
import pe.sistemarural.modelo.Ticket;

/** Todo lo que se guarda en disco (se cifra completo antes de escribirse). */
final class DatosClinica implements Serializable {
    private static final long serialVersionUID = 1L;

    final LinkedHashMap<String, Paciente> pacientes = new LinkedHashMap<>(); // clave: hash del DNI
    final LinkedHashMap<String, Medico> medicos = new LinkedHashMap<>();     // clave: CMP
    final ArrayList<Ticket> tickets = new ArrayList<>();
    AgendaMedica agenda;
    HashMap<LocalDate, Integer> contadores = new HashMap<>();

    DatosClinica(int cuposPorTurno) {
        this.agenda = new AgendaMedica(cuposPorTurno);
    }
}
