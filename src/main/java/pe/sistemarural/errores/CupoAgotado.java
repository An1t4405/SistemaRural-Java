package pe.sistemarural.errores;

/** No hay cupos disponibles para ese médico, fecha y turno (RF-03). */
public class CupoAgotado extends ErrorSistema {
    private static final long serialVersionUID = 1L;

    public CupoAgotado(String mensaje) {
        super(mensaje);
    }
}
