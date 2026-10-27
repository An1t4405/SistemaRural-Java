package pe.sistemarural.modelo;

import java.time.LocalDate;
import java.time.Period;
import pe.sistemarural.errores.ErrorValidacion;

/** Paciente de la posta. Su HistoriaClinica es parte suya (composición). */
public class Paciente extends Persona {
    private static final long serialVersionUID = 1L;

    private final LocalDate fechaNacimiento;
    private String direccion;
    private final HistoriaClinica historia = new HistoriaClinica();

    public Paciente(String dni, String nombres, String apellidos, LocalDate fechaNacimiento,
            String direccion, String telefono) {
        super(dni, nombres, apellidos, telefono);
        if (fechaNacimiento == null) {
            throw new ErrorValidacion("La fecha de nacimiento es obligatoria.");
        }
        if (fechaNacimiento.isAfter(LocalDate.now())) {
            throw new ErrorValidacion("La fecha de nacimiento no puede ser futura.");
        }
        this.fechaNacimiento = fechaNacimiento;
        this.direccion = Validaciones.opcional(direccion);
    }

    public LocalDate getFechaNacimiento() {
        return fechaNacimiento;
    }

    public String getDireccion() {
        return direccion;
    }

    public void setDireccion(String direccion) {
        this.direccion = Validaciones.opcional(direccion);
    }

    public HistoriaClinica getHistoria() {
        return historia;
    }

    public int edad() {
        return Period.between(fechaNacimiento, LocalDate.now()).getYears();
    }

    @Override
    public String rol() {
        return "Paciente";
    }
}
