package pe.sistemarural.modelo;

import java.io.Serializable;
import pe.sistemarural.seguridad.Cifrador;
import pe.sistemarural.seguridad.Dni;

/** Datos comunes de pacientes y médicos. El DNI nunca queda en texto plano. */
public abstract class Persona implements Serializable {
    private static final long serialVersionUID = 1L;

    private final String dniCifrado;
    private final String dniHash;
    private String nombres;
    private String apellidos;
    private String telefono;

    protected Persona(String dni, String nombres, String apellidos, String telefono) {
        String limpio = Dni.validar(dni);
        Cifrador cifrador = Cifrador.actual();
        this.dniCifrado = cifrador.cifrar(limpio);
        this.dniHash = cifrador.hashDni(limpio);
        this.nombres = Validaciones.obligatorio(nombres, "nombres");
        this.apellidos = Validaciones.obligatorio(apellidos, "apellidos");
        this.telefono = Validaciones.opcional(telefono);
    }

    public final String getNombres() {
        return nombres;
    }

    public final void setNombres(String nombres) {
        this.nombres = Validaciones.obligatorio(nombres, "nombres");
    }

    public final String getApellidos() {
        return apellidos;
    }

    public final void setApellidos(String apellidos) {
        this.apellidos = Validaciones.obligatorio(apellidos, "apellidos");
    }

    public final String getTelefono() {
        return telefono;
    }

    public final void setTelefono(String telefono) {
        this.telefono = Validaciones.opcional(telefono);
    }

    public final String getDniHash() {
        return dniHash;
    }

    public final String nombreCompleto() {
        return apellidos + ", " + nombres;
    }

    /** Lo que se muestra en pantalla: ****5678. */
    public final String getDniEnmascarado() {
        return Dni.enmascarar(Cifrador.actual().descifrar(dniCifrado));
    }

    /** Compara por hash, sin exponer el número (DM-05). */
    public final boolean coincideDni(String dni) {
        try {
            return dniHash.equals(Cifrador.actual().hashDni(Dni.validar(dni)));
        } catch (pe.sistemarural.errores.ErrorValidacion e) {
            return false;
        }
    }

    public abstract String rol();
}
