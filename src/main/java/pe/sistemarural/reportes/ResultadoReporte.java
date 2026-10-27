package pe.sistemarural.reportes;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/** Resultado inmutable de un reporte (record de Java). */
public record ResultadoReporte(String tipo, LocalDate desde, LocalDate hasta, int totalAtenciones,
        List<Map.Entry<String, Long>> patologiasFrecuentes) {
}
