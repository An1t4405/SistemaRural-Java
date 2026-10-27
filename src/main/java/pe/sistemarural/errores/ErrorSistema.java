package pe.sistemarural.errores;

/** Base de todos los errores controlados del sistema. */
public class ErrorSistema extends RuntimeException {
    private static final long serialVersionUID = 1L;

    public ErrorSistema(String mensaje) {
        super(mensaje);
    }

    public ErrorSistema(String mensaje, Throwable causa) {
        super(mensaje, causa);
    }
}
