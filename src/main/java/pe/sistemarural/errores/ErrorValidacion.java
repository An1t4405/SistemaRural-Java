package pe.sistemarural.errores;

/** Un dato ingresado no cumple el formato esperado. */
public class ErrorValidacion extends ErrorSistema {
    private static final long serialVersionUID = 1L;

    public ErrorValidacion(String mensaje) {
        super(mensaje);
    }
}
