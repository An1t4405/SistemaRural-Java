package pe.sistemarural.reportes;

import java.time.LocalDate;
import java.util.Collection;
import pe.sistemarural.modelo.Atencion;

/** Atenciones del mes de la fecha de referencia. */
public class ReporteMensual extends Reporte {
    public ReporteMensual(Collection<Atencion> atenciones) {
        super(atenciones);
    }

    @Override
    public String nombre() {
        return "Mensual";
    }

    @Override
    protected Rango rango(LocalDate ref) {
        return new Rango(ref.withDayOfMonth(1), ref.withDayOfMonth(ref.lengthOfMonth()));
    }
}
