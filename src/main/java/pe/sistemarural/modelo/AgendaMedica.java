package pe.sistemarural.modelo;

import java.io.Serializable;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import pe.sistemarural.errores.CupoAgotado;
import pe.sistemarural.errores.ErrorValidacion;

/** Reúne las citas (agregación) y controla los cupos por turno (DM-04). */
public class AgendaMedica implements Serializable {
    private static final long serialVersionUID = 1L;

    private final int cuposPorTurno;
    private final LinkedHashMap<String, Cita> citas = new LinkedHashMap<>();

    public AgendaMedica(int cuposPorTurno) {
        if (cuposPorTurno <= 0) {
            throw new ErrorValidacion("Los cupos por turno deben ser mayores que cero.");
        }
        this.cuposPorTurno = cuposPorTurno;
    }

    public int getCuposPorTurno() {
        return cuposPorTurno;
    }

    public List<Cita> getCitas() {
        return List.copyOf(citas.values());
    }

    public Cita getCita(String id) {
        return citas.get(id);
    }

    public int cuposDisponibles(Medico medico, LocalDate fecha, Turno turno) {
        long usados = citas.values().stream()
                .filter(Cita::ocupaCupo)
                .filter(c -> c.getMedico().getCmp().equals(medico.getCmp()))
                .filter(c -> c.getFecha().equals(fecha) && c.getTurno() == turno)
                .count();
        return cuposPorTurno - (int) usados;
    }

    public Cita agendar(Paciente paciente, Medico medico, LocalDate fecha, Turno turno) {
        if (fecha == null || turno == null) {
            throw new ErrorValidacion("La fecha y el turno son obligatorios.");
        }
        if (fecha.isBefore(LocalDate.now())) {
            throw new ErrorValidacion("No se puede agendar una cita en una fecha pasada.");
        }
        if (cuposDisponibles(medico, fecha, turno) <= 0) {
            throw new CupoAgotado("Sin cupos con " + medico.nombreCompleto() + " el " + fecha + " (" + turno + ").");
        }
        Cita cita = new Cita(paciente, medico, fecha, turno);
        citas.put(cita.getId(), cita);
        return cita;
    }

    /** Resumen de cupos por turno para un médico y fecha (RF-05). */
    public Map<Turno, Integer> disponibilidad(Medico medico, LocalDate fecha) {
        Map<Turno, Integer> resultado = new java.util.EnumMap<>(Turno.class);
        for (Turno t : Turno.values()) {
            resultado.put(t, cuposDisponibles(medico, fecha, t));
        }
        return resultado;
    }
}
