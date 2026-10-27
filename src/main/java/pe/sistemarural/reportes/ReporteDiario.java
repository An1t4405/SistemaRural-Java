package pe.sistemarural.reportes;

import java.time.LocalDate;
import java.util.Collection;
import pe.sistemarural.modelo.Atencion;

/** Atenciones de un solo día. */
public class ReporteDiario extends Reporte {
    public ReporteDiario(Collection<Atencion> atenciones) {
        super(atenciones);
    }

    @Override
    public String nombre() {
        return "Diario";
    }

    @Override
    protected Rango rango(LocalDate ref) {
        return new Rango(ref, ref);
    }
}
