package pe.sistemarural.modelo;

/** Profesional de salud que atiende en la posta. */
public class Medico extends Persona {
    private static final long serialVersionUID = 1L;

    private final String cmp;
    private final String especialidad;

    public Medico(String dni, String nombres, String apellidos, String cmp, String especialidad, String telefono) {
        super(dni, nombres, apellidos, telefono);
        this.cmp = Validaciones.obligatorio(cmp, "CMP");
        this.especialidad = Validaciones.obligatorio(especialidad, "especialidad");
    }

    public String getCmp() {
        return cmp;
    }

    public String getEspecialidad() {
        return especialidad;
    }

    @Override
    public String rol() {
        return "Médico";
    }
}
