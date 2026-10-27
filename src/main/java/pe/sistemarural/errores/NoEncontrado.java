package pe.sistemarural.errores;

/** No existe el paciente, médico, cita o ticket solicitado. */
public class NoEncontrado extends ErrorSistema {
    private static final long serialVersionUID = 1L;

    public NoEncontrado(String mensaje) {
        super(mensaje);
    }
}
