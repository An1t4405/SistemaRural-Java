package pe.sistemarural.modelo;

import pe.sistemarural.errores.ErrorValidacion;

/** Validaciones comunes de texto para las clases del dominio. */
final class Validaciones {
    private Validaciones() {
    }

    static String obligatorio(String valor, String campo) {
        String limpio = valor == null ? "" : valor.strip();
        if (limpio.isEmpty()) {
            throw new ErrorValidacion("El campo «" + campo + "» es obligatorio.");
        }
        return limpio;
    }

    static String opcional(String valor) {
        return valor == null ? "" : valor.strip();
    }
}
