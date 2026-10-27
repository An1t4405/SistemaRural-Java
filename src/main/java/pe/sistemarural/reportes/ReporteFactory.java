package pe.sistemarural.reportes;

import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import pe.sistemarural.errores.ErrorValidacion;
import pe.sistemarural.modelo.Atencion;

/**
 * Patrón Factory: crea el reporte según el tipo pedido, sin que quien lo usa conozca las
 * clases concretas. Agregar un tipo nuevo = una subclase y una línea en TIPOS (abierto/cerrado).
 */
public final class ReporteFactory {
    private static final Map<String, Function<Collection<Atencion>, Reporte>> TIPOS = new LinkedHashMap<>();

    static {
        TIPOS.put("diario", ReporteDiario::new);
        TIPOS.put("semanal", ReporteSemanal::new);
        TIPOS.put("mensual", ReporteMensual::new);
    }

    private ReporteFactory() {
    }

    public static Set<String> tiposDisponibles() {
        return TIPOS.keySet();
    }

    public static Reporte crear(String tipo, Collection<Atencion> atenciones) {
        Function<Collection<Atencion>, Reporte> fabrica = tipo == null ? null : TIPOS.get(tipo.toLowerCase(Locale.ROOT));
        if (fabrica == null) {
            throw new ErrorValidacion("Tipo de reporte desconocido: " + tipo);
        }
        return fabrica.apply(atenciones);
    }
}
