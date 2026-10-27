package pe.sistemarural.seguridad;

import java.util.regex.Pattern;
import pe.sistemarural.errores.ErrorValidacion;

/** Validación y enmascarado del DNI peruano (8 dígitos). */
public final class Dni {
    private static final Pattern PATRON = Pattern.compile("\\d{8}");

    private Dni() {
    }

    /** Devuelve el DNI sin espacios en los extremos o lanza ErrorValidacion. */
    public static String validar(String dni) {
        String limpio = dni == null ? "" : dni.strip();
        if (!PATRON.matcher(limpio).matches()) {
            throw new ErrorValidacion("El DNI debe tener exactamente 8 dígitos numéricos.");
        }
        return limpio;
    }

    /** 12345678 -> ****5678 (DM-01). */
    public static String enmascarar(String dni) {
        return "****" + dni.substring(dni.length() - 4);
    }
}
