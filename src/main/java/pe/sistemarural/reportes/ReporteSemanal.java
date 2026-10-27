package pe.sistemarural.reportes;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.temporal.TemporalAdjusters;
import java.util.Collection;
import pe.sistemarural.modelo.Atencion;

/** Atenciones de la semana (lunes a domingo) de la fecha de referencia. */
public class ReporteSemanal extends Reporte {
    public ReporteSemanal(Collection<Atencion> atenciones) {
        super(atenciones);
    }

    @Override
    public String nombre() {
        return "Semanal";
    }

    @Override
    protected Rango rango(LocalDate ref) {
        LocalDate lunes = ref.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
        return new Rango(lunes, lunes.plusDays(6));
    }
}
