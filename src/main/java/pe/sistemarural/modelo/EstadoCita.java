package pe.sistemarural.modelo;

/** Estados de una cita/turno. CANCELADA libera el cupo. */
public enum EstadoCita {
    RESERVADO("Reservado"),
    EN_ATENCION("En atención"),
    COMPLETADO("Completado"),
    CANCELADA("Cancelada");

    private final String etiqueta;

    EstadoCita(String etiqueta) {
        this.etiqueta = etiqueta;
    }

    /** Los tickets solo pasan por Reservado, En atención y Completado. */
    public boolean esEstadoDeTicket() {
        return this != CANCELADA;
    }

    @Override
    public String toString() {
        return etiqueta;
    }
}
