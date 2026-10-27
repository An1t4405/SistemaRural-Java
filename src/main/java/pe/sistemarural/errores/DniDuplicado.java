package pe.sistemarural.errores;

/** Ya existe un paciente con ese DNI (CE-02). */
public class DniDuplicado extends ErrorSistema {
    private static final long serialVersionUID = 1L;

    public DniDuplicado(String mensaje) {
        super(mensaje);
    }
}
