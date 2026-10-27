package pe.sistemarural.modelo;

import java.io.Serializable;
import java.time.LocalDate;
import pe.sistemarural.errores.ErrorValidacion;

/** Turno digital con número correlativo y estado (RF-04, RF-05). */
public class Ticket implements Serializable {
    private static final long serialVersionUID = 1L;

    private final Cita cita;
    private final LocalDate fecha;
    private final int numero;

    public Ticket(Cita cita) {
        this.cita = cita;
        this.fecha = cita.getFecha();
        this.numero = GeneradorTurnos.getInstancia().siguiente(fecha);
    }

    public int getNumero() {
        return numero;
    }

    public LocalDate getFecha() {
        return fecha;
    }

    public Cita getCita() {
        return cita;
    }

    public EstadoCita getEstado() {
        return cita.getEstado();
    }

    public void cambiarEstado(EstadoCita nuevo) {
        if (nuevo == null || !nuevo.esEstadoDeTicket()) {
            throw new ErrorValidacion("Estado inválido. Opciones: Reservado, En atención o Completado.");
        }
        cita.setEstado(nuevo);
    }
}
