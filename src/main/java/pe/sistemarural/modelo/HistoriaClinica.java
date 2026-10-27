package pe.sistemarural.modelo;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import pe.sistemarural.seguridad.Cifrador;

/** Alergias y antecedentes (cifrados) y lista de atenciones. Vive dentro del Paciente. */
public class HistoriaClinica implements Serializable {
    private static final long serialVersionUID = 1L;

    private String alergiasCifradas;
    private String antecedentesCifrados;
    private final ArrayList<Atencion> atenciones = new ArrayList<>();

    public HistoriaClinica() {
        setAlergias("");
        setAntecedentes("");
    }

    public String getAlergias() {
        return Cifrador.actual().descifrar(alergiasCifradas);
    }

    public void setAlergias(String alergias) {
        this.alergiasCifradas = Cifrador.actual().cifrar(Validaciones.opcional(alergias));
    }

    public String getAntecedentes() {
        return Cifrador.actual().descifrar(antecedentesCifrados);
    }

    public void setAntecedentes(String antecedentes) {
        this.antecedentesCifrados = Cifrador.actual().cifrar(Validaciones.opcional(antecedentes));
    }

    /** Copia de solo lectura: la lista interna no se expone (encapsulamiento). */
    public List<Atencion> getAtenciones() {
        return List.copyOf(atenciones);
    }

    public void agregarAtencion(Atencion atencion) {
        atenciones.add(atencion);
    }
}
