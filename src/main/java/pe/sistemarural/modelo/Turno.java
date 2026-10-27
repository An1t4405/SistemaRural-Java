package pe.sistemarural.modelo;

/** Turnos de atención de la posta. */
public enum Turno {
    MANANA("Mañana"),
    TARDE("Tarde");

    private final String etiqueta;

    Turno(String etiqueta) {
        this.etiqueta = etiqueta;
    }

    @Override
    public String toString() {
        return etiqueta;
    }
}
