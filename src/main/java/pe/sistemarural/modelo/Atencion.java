package pe.sistemarural.modelo;

import java.io.Serializable;
import java.time.LocalDate;
import java.util.Locale;
import java.util.regex.Pattern;
import pe.sistemarural.errores.ErrorValidacion;
import pe.sistemarural.seguridad.Cifrador;

/** Una consulta registrada: fecha, motivo y diagnóstico CIE-10 (cifrado). */
public class Atencion implements Serializable {
    private static final long serialVersionUID = 1L;
    private static final Pattern CIE10 = Pattern.compile("[A-TV-Z]\\d{2}(\\.\\d{1,2})?");

    private final LocalDate fecha;
    private final String motivo;
    private final String diagnosticoCifrado;
    private final String cmpMedico;

    public Atencion(LocalDate fecha, String motivo, String diagnosticoCie10, String cmpMedico) {
        String diagnostico = diagnosticoCie10 == null ? "" : diagnosticoCie10.strip().toUpperCase(Locale.ROOT);
        if (!CIE10.matcher(diagnostico).matches()) {
            throw new ErrorValidacion("Diagnóstico inválido: use un código CIE-10 (ej. J00 o E11.9).");
        }
        this.fecha = fecha;
        this.motivo = Validaciones.obligatorio(motivo, "motivo");
        this.diagnosticoCifrado = Cifrador.actual().cifrar(diagnostico);
        this.cmpMedico = cmpMedico;
    }

    public LocalDate getFecha() {
        return fecha;
    }

    public String getMotivo() {
        return motivo;
    }

    public String getCmpMedico() {
        return cmpMedico;
    }

    public String getDiagnostico() {
        return Cifrador.actual().descifrar(diagnosticoCifrado);
    }
}
