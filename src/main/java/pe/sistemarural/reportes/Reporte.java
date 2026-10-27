package pe.sistemarural.reportes;

import java.time.LocalDate;
import java.util.Collection;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import pe.sistemarural.modelo.Atencion;

/**
 * Reporte de atenciones (RF-06) con estilo funcional (DM-02): usa filter, map, reduce y
 * lambdas sobre los datos, sin modificar las historias clínicas.
 */
public abstract class Reporte {
    /** Rango de fechas (inclusive) que cubre el reporte. */
    public record Rango(LocalDate desde, LocalDate hasta) {
    }

    private final List<Atencion> atenciones;

    protected Reporte(Collection<Atencion> atenciones) {
        this.atenciones = List.copyOf(atenciones);
    }

    public abstract String nombre();

    protected abstract Rango rango(LocalDate referencia);

    public ResultadoReporte generar(LocalDate referencia) {
        Rango rango = rango(referencia);

        // filter: solo las atenciones del periodo
        List<Atencion> enRango = atenciones.stream()
                .filter(a -> !a.getFecha().isBefore(rango.desde()) && !a.getFecha().isAfter(rango.hasta()))
                .toList();

        // map + collect: cuenta los casos por código CIE-10
        Map<String, Long> conteo = enRango.stream()
                .map(Atencion::getDiagnostico)
                .collect(Collectors.groupingBy(Function.identity(), Collectors.counting()));

        // map + reduce: total de atenciones
        int total = enRango.stream().map(a -> 1).reduce(0, Integer::sum);

        Comparator<Map.Entry<String, Long>> masFrecuentePrimero =
                Comparator.comparing((Map.Entry<String, Long> e) -> e.getValue()).reversed()
                        .thenComparing(e -> e.getKey());
        List<Map.Entry<String, Long>> ranking = conteo.entrySet().stream()
                .sorted(masFrecuentePrimero)
                .limit(5)
                .toList();

        return new ResultadoReporte(nombre(), rango.desde(), rango.hasta(), total, ranking);
    }
}
