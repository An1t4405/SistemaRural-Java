package pe.sistemarural.servicio;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputFilter;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.LocalDate;
import java.util.Collection;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import pe.sistemarural.errores.DniDuplicado;
import pe.sistemarural.errores.ErrorSistema;
import pe.sistemarural.errores.ErrorValidacion;
import pe.sistemarural.errores.NoEncontrado;
import pe.sistemarural.modelo.Atencion;
import pe.sistemarural.modelo.Cita;
import pe.sistemarural.modelo.EstadoCita;
import pe.sistemarural.modelo.GeneradorTurnos;
import pe.sistemarural.modelo.Medico;
import pe.sistemarural.modelo.Paciente;
import pe.sistemarural.modelo.Ticket;
import pe.sistemarural.modelo.Turno;
import pe.sistemarural.reportes.ReporteFactory;
import pe.sistemarural.reportes.ResultadoReporte;
import pe.sistemarural.seguridad.Cifrador;
import pe.sistemarural.seguridad.Dni;

/**
 * Concentra las operaciones del sistema (RF-01 a RF-06). La interfaz solo llama a este servicio.
 * Todo el archivo de datos se guarda cifrado (RD-02).
 */
public class ServicioClinica {
    /** Solo se permite leer clases propias y tipos básicos de Java (defensa al deserializar). */
    private static final ObjectInputFilter FILTRO = ObjectInputFilter.Config.createFilter(
            "pe.sistemarural.**;java.lang.*;java.util.*;java.time.*;!*");

    /** Cupos disponibles y totales de un turno. */
    public record Cupo(int disponibles, int total) {
    }

    private final Cifrador cifrador;
    private final Path rutaDatos;
    private DatosClinica datos;

    public ServicioClinica(Path rutaDatos, Path rutaClave, int cuposPorTurno) {
        this.cifrador = Cifrador.configurar(rutaClave);
        this.rutaDatos = rutaDatos;
        this.datos = new DatosClinica(cuposPorTurno);
        GeneradorTurnos.getInstancia().restaurar(Map.of());
        if (Files.exists(rutaDatos)) {
            cargar();
        }
    }

    // ------------------------------------------------ RF-01 pacientes
    public Paciente registrarPaciente(String dni, String nombres, String apellidos, LocalDate nacimiento,
            String direccion, String telefono) {
        Paciente nuevo = new Paciente(dni, nombres, apellidos, nacimiento, direccion, telefono);
        if (datos.pacientes.containsKey(nuevo.getDniHash())) {
            throw new DniDuplicado("Ya existe un paciente registrado con ese DNI."); // CE-02
        }
        datos.pacientes.put(nuevo.getDniHash(), nuevo);
        guardar();
        return nuevo;
    }

    /** Carga masiva: agrega varios pacientes y guarda una sola vez. */
    public void importarPacientes(Collection<Paciente> pacientes) {
        for (Paciente p : pacientes) {
            if (datos.pacientes.putIfAbsent(p.getDniHash(), p) != null) {
                throw new DniDuplicado("Hay un DNI repetido en la importación.");
            }
        }
        guardar();
    }

    public Paciente actualizarPaciente(String dni, String nombres, String apellidos, String direccion,
            String telefono) {
        Paciente p = buscarPorDni(dni);
        if (nombres != null) {
            p.setNombres(nombres);
        }
        if (apellidos != null) {
            p.setApellidos(apellidos);
        }
        if (direccion != null) {
            p.setDireccion(direccion);
        }
        if (telefono != null) {
            p.setTelefono(telefono);
        }
        guardar();
        return p;
    }

    /** Búsqueda por DNI en tiempo constante (mapa por hash) → CE-01. */
    public Paciente buscarPorDni(String dni) {
        Paciente p = datos.pacientes.get(cifrador.hashDni(Dni.validar(dni)));
        if (p == null) {
            throw new NoEncontrado("No existe un paciente con ese DNI.");
        }
        return p;
    }

    public List<Paciente> buscarPorNombre(String texto) {
        String t = texto.strip().toLowerCase();
        return datos.pacientes.values().stream()
                .filter(p -> p.nombreCompleto().toLowerCase().contains(t))
                .sorted((a, b) -> a.nombreCompleto().compareToIgnoreCase(b.nombreCompleto()))
                .toList();
    }

    public List<Paciente> listarPacientes() {
        return buscarPorNombre("");
    }

    // ------------------------------------------------ médicos
    public Medico registrarMedico(String dni, String nombres, String apellidos, String cmp, String especialidad,
            String telefono) {
        if (cmp != null && datos.medicos.containsKey(cmp.strip())) {
            throw new ErrorValidacion("Ya existe un médico con ese CMP.");
        }
        Medico m = new Medico(dni, nombres, apellidos, cmp, especialidad, telefono);
        datos.medicos.put(m.getCmp(), m);
        guardar();
        return m;
    }

    public Medico obtenerMedico(String cmp) {
        Medico m = cmp == null ? null : datos.medicos.get(cmp.strip());
        if (m == null) {
            throw new NoEncontrado("No existe un médico con ese CMP.");
        }
        return m;
    }

    public List<Medico> listarMedicos() {
        return datos.medicos.values().stream()
                .sorted((a, b) -> a.nombreCompleto().compareToIgnoreCase(b.nombreCompleto()))
                .toList();
    }

    // ------------------------------------------------ RF-02 historia clínica
    public void actualizarHistoria(String dni, String alergias, String antecedentes) {
        var historia = buscarPorDni(dni).getHistoria();
        if (alergias != null) {
            historia.setAlergias(alergias);
        }
        if (antecedentes != null) {
            historia.setAntecedentes(antecedentes);
        }
        guardar();
    }

    public Atencion registrarAtencion(String dni, String cmp, String motivo, String diagnosticoCie10,
            LocalDate fecha) {
        Paciente p = buscarPorDni(dni);
        Medico m = obtenerMedico(cmp);
        Atencion a = new Atencion(fecha == null ? LocalDate.now() : fecha, motivo, diagnosticoCie10, m.getCmp());
        p.getHistoria().agregarAtencion(a);
        guardar();
        return a;
    }

    public List<Atencion> todasLasAtenciones() {
        return datos.pacientes.values().stream()
                .flatMap(p -> p.getHistoria().getAtenciones().stream())
                .toList();
    }

    // ------------------------------------------------ RF-03 citas
    public Cita agendarCita(String dni, String cmp, LocalDate fecha, Turno turno) {
        Cita cita = datos.agenda.agendar(buscarPorDni(dni), obtenerMedico(cmp), fecha, turno);
        guardar();
        return cita;
    }

    public void cancelarCita(String idCita) {
        Cita cita = datos.agenda.getCita(idCita);
        if (cita == null) {
            throw new NoEncontrado("No existe esa cita.");
        }
        cita.setEstado(EstadoCita.CANCELADA);
        guardar();
    }

    public List<Cita> listarCitas() {
        return datos.agenda.getCitas().stream()
                .sorted((a, b) -> a.getFecha().equals(b.getFecha())
                        ? a.getTurno().compareTo(b.getTurno())
                        : a.getFecha().compareTo(b.getFecha()))
                .toList();
    }

    // ------------------------------------------------ RF-04 tickets
    public Ticket emitirTicket(String idCita) {
        Cita cita = datos.agenda.getCita(idCita);
        if (cita == null || !cita.ocupaCupo()) {
            throw new NoEncontrado("La cita no existe o está cancelada.");
        }
        if (datos.tickets.stream().anyMatch(t -> t.getCita() == cita)) {
            throw new ErrorValidacion("Esa cita ya tiene un ticket emitido.");
        }
        Ticket t = new Ticket(cita);
        datos.tickets.add(t);
        guardar();
        return t;
    }

    public Ticket cambiarEstadoTicket(LocalDate fecha, int numero, EstadoCita estado) {
        Ticket t = datos.tickets.stream()
                .filter(x -> x.getFecha().equals(fecha) && x.getNumero() == numero)
                .findFirst()
                .orElseThrow(() -> new NoEncontrado("No existe ese ticket."));
        t.cambiarEstado(estado);
        guardar();
        return t;
    }

    /** Tickets de una fecha (o todos si fecha es null), ordenados por fecha y número. */
    public List<Ticket> listarTickets(LocalDate fecha) {
        return datos.tickets.stream()
                .filter(t -> fecha == null || t.getFecha().equals(fecha))
                .sorted((a, b) -> a.getFecha().equals(b.getFecha())
                        ? Integer.compare(a.getNumero(), b.getNumero())
                        : a.getFecha().compareTo(b.getFecha()))
                .toList();
    }

    // ------------------------------------------------ RF-05 disponibilidad
    public Map<Turno, Cupo> consultarCupos(String cmp, LocalDate fecha) {
        Medico m = obtenerMedico(cmp);
        int total = datos.agenda.getCuposPorTurno();
        Map<Turno, Cupo> resultado = new EnumMap<>(Turno.class);
        datos.agenda.disponibilidad(m, fecha).forEach((turno, libres) -> resultado.put(turno, new Cupo(libres, total)));
        return resultado;
    }

    // ------------------------------------------------ RF-06 reportes
    public ResultadoReporte generarReporte(String tipo, LocalDate fecha) {
        return ReporteFactory.crear(tipo, todasLasAtenciones()).generar(fecha == null ? LocalDate.now() : fecha);
    }

    // ------------------------------------------------ persistencia cifrada
    public void guardar() {
        datos.contadores = GeneradorTurnos.getInstancia().exportar();
        try (ByteArrayOutputStream salida = new ByteArrayOutputStream();
                ObjectOutputStream objetos = new ObjectOutputStream(salida)) {
            objetos.writeObject(datos);
            objetos.flush();
            Path temporal = rutaDatos.resolveSibling(rutaDatos.getFileName() + ".tmp");
            Files.write(temporal, cifrador.cifrarBytes(salida.toByteArray()));
            Files.move(temporal, rutaDatos, StandardCopyOption.REPLACE_EXISTING); // no deja el archivo a medias
        } catch (IOException e) {
            throw new ErrorSistema("No se pudo guardar la información: " + e.getMessage(), e);
        }
    }

    private void cargar() {
        try {
            byte[] claro = cifrador.descifrarBytes(Files.readAllBytes(rutaDatos));
            try (ObjectInputStream objetos = new ObjectInputStream(new ByteArrayInputStream(claro))) {
                objetos.setObjectInputFilter(FILTRO);
                datos = (DatosClinica) objetos.readObject();
            }
            GeneradorTurnos.getInstancia().restaurar(datos.contadores);
        } catch (IOException | ClassNotFoundException | ClassCastException e) {
            throw new ErrorSistema("No se pudo leer el archivo de datos: " + e.getMessage(), e);
        }
    }
}
