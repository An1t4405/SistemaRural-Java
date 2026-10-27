package pe.sistemarural.modelo;

import java.io.Serializable;
import java.time.LocalDate;
import java.util.UUID;

/** Cita con fecha, turno y estado. Asociada a un Paciente y a un Médico. */
public class Cita implements Serializable {
    private static final long serialVersionUID = 1L;

    private final String id = UUID.randomUUID().toString().substring(0, 8);
    private final Paciente paciente;
    private final Medico medico;
    private final LocalDate fecha;
    private final Turno turno;
    private EstadoCita estado = EstadoCita.RESERVADO;

    public Cita(Paciente paciente, Medico medico, LocalDate fecha, Turno turno) {
        this.paciente = paciente;
        this.medico = medico;
        this.fecha = fecha;
        this.turno = turno;
    }

    public String getId() {
        return id;
    }

    public Paciente getPaciente() {
        return paciente;
    }

    public Medico getMedico() {
        return medico;
    }

    public LocalDate getFecha() {
        return fecha;
    }

    public Turno getTurno() {
        return turno;
    }

    public EstadoCita getEstado() {
        return estado;
    }

    public void setEstado(EstadoCita estado) {
        this.estado = estado;
    }

    public boolean ocupaCupo() {
        return estado != EstadoCita.CANCELADA;
    }
}
