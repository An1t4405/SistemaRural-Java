package pe.sistemarural.ui;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import java.awt.Insets;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JComboBox;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTabbedPane;
import javax.swing.JTable;
import javax.swing.JTextArea;
import javax.swing.JTextField;
import javax.swing.table.DefaultTableModel;
import pe.sistemarural.errores.ErrorSistema;
import pe.sistemarural.modelo.Atencion;
import pe.sistemarural.modelo.Cita;
import pe.sistemarural.modelo.EstadoCita;
import pe.sistemarural.modelo.HistoriaClinica;
import pe.sistemarural.modelo.Medico;
import pe.sistemarural.modelo.Paciente;
import pe.sistemarural.modelo.Ticket;
import pe.sistemarural.modelo.Turno;
import pe.sistemarural.reportes.ReporteFactory;
import pe.sistemarural.reportes.ResultadoReporte;
import pe.sistemarural.servicio.ServicioClinica;

/**
 * Interfaz gráfica (DD-03): solo handlers de eventos que delegan en ServicioClinica.
 * No hay lógica de negocio aquí; el DNI solo se muestra enmascarado.
 */
public class VentanaPrincipal extends JFrame {
    private static final long serialVersionUID = 1L;

    /** Tabla de solo lectura con su panel de desplazamiento. */
    private static final class Tabla {
        final DefaultTableModel modelo;
        final JTable tabla;
        final JScrollPane panel;

        Tabla(String... columnas) {
            modelo = new DefaultTableModel(columnas, 0) {
                private static final long serialVersionUID = 1L;

                @Override
                public boolean isCellEditable(int fila, int columna) {
                    return false;
                }
            };
            tabla = new JTable(modelo);
            tabla.setRowHeight(24);
            panel = new JScrollPane(tabla);
        }

        void llenar(List<Object[]> filas) {
            modelo.setRowCount(0);
            filas.forEach(modelo::addRow);
        }

        /** Valor de una columna en la fila elegida, o null si no hay selección. */
        String elegido(int columna) {
            int fila = tabla.getSelectedRow();
            return fila < 0 ? null : String.valueOf(modelo.getValueAt(fila, columna));
        }
    }

    private final ServicioClinica servicio;

    // Pacientes
    private final JTextField pDni = new JTextField(14);
    private final JTextField pNombres = new JTextField(14);
    private final JTextField pApellidos = new JTextField(14);
    private final JTextField pNacimiento = new JTextField(14);
    private final JTextField pDireccion = new JTextField(14);
    private final JTextField pTelefono = new JTextField(14);
    private final JTextField pBusqueda = new JTextField(14);
    private final Tabla tablaPacientes = new Tabla("DNI", "Paciente", "Edad", "Teléfono", "Dirección");
    // Historia clínica
    private final JTextField hDni = new JTextField(14);
    private final JTextField hAlergias = new JTextField(14);
    private final JTextField hAntecedentes = new JTextField(14);
    private final JTextField aCmp = new JTextField(14);
    private final JTextField aMotivo = new JTextField(14);
    private final JTextField aCie = new JTextField(14);
    private final Tabla tablaAtenciones = new Tabla("Fecha", "Motivo", "Diagnóstico", "CMP");
    // Médicos
    private final JTextField mDni = new JTextField(14);
    private final JTextField mCmp = new JTextField(14);
    private final JTextField mNombres = new JTextField(14);
    private final JTextField mApellidos = new JTextField(14);
    private final JTextField mEspecialidad = new JTextField(14);
    private final JTextField mTelefono = new JTextField(14);
    private final Tabla tablaMedicos = new Tabla("CMP", "Médico", "Especialidad");
    // Citas y turnos
    private final JTextField cDni = new JTextField(10);
    private final JComboBox<String> cMedico = new JComboBox<>();
    private final JTextField cFecha = new JTextField(LocalDate.now().toString(), 9);
    private final JComboBox<Turno> cTurno = new JComboBox<>(Turno.values());
    private final JLabel lblCupos = new JLabel("Cupos: —");
    private final Tabla tablaCitas = new Tabla("ID cita", "Paciente", "Médico", "Fecha", "Turno", "N.º turno", "Estado");
    // Reportes
    private final JComboBox<String> rTipo = new JComboBox<>(ReporteFactory.tiposDisponibles().toArray(new String[0]));
    private final JTextField rFecha = new JTextField(LocalDate.now().toString(), 10);
    private final JTextArea rTexto = new JTextArea();

    public VentanaPrincipal(ServicioClinica servicio) {
        super("SistemaRural-PE · Posta Médica Rural");
        this.servicio = servicio;
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setSize(1000, 680);
        setMinimumSize(new Dimension(860, 560));
        setLocationRelativeTo(null);

        JTabbedPane pestanas = new JTabbedPane();
        pestanas.addTab("Pacientes", pestanaPacientes());
        pestanas.addTab("Historia clínica", pestanaHistoria());
        pestanas.addTab("Médicos", pestanaMedicos());
        pestanas.addTab("Citas y turnos", pestanaCitas());
        pestanas.addTab("Reportes", pestanaReportes());
        add(pestanas);
        refrescarTodo();
    }

    // ------------------------------------------------------------ utilidades
    private static JPanel formulario(String titulo, Object... pares) {
        JPanel panel = new JPanel(new GridBagLayout());
        panel.setBorder(BorderFactory.createTitledBorder(titulo));
        GridBagConstraints c = new GridBagConstraints();
        c.insets = new Insets(3, 5, 3, 5);
        c.anchor = GridBagConstraints.EAST;
        int fila = 0;
        int col = 0;
        for (int i = 0; i < pares.length; i += 2) {
            c.gridy = fila;
            c.gridx = col;
            c.anchor = GridBagConstraints.EAST;
            panel.add(new JLabel((String) pares[i]), c);
            c.gridx = col + 1;
            c.anchor = GridBagConstraints.WEST;
            panel.add((JTextField) pares[i + 1], c);
            col += 2;
            if (col >= 4) {
                col = 0;
                fila++;
            }
        }
        return panel;
    }

    private static JButton boton(String texto, Runnable accion) {
        JButton b = new JButton(texto);
        b.addActionListener(e -> accion.run());
        return b;
    }

    private static JPanel conMargen(JPanel interior) {
        interior.setBorder(BorderFactory.createEmptyBorder(8, 8, 8, 8));
        return interior;
    }

    private static String texto(JTextField campo) {
        return campo.getText().strip();
    }

    private static LocalDate fecha(JTextField campo, boolean obligatoria) {
        String t = texto(campo);
        if (t.isEmpty()) {
            if (obligatoria) {
                throw new ErrorSistema("Ingrese la fecha en formato AAAA-MM-DD (ej. 1990-05-17).");
            }
            return LocalDate.now();
        }
        try {
            return LocalDate.parse(t);
        } catch (DateTimeParseException e) {
            throw new ErrorSistema("Fecha inválida. Use el formato AAAA-MM-DD (ej. 2026-11-03).");
        }
    }

    /** Muestra un mensaje al usuario. Se puede sobrescribir (por ejemplo, en pruebas de la interfaz). */
    protected void mostrar(String titulo, String mensaje, int tipo) {
        JOptionPane.showMessageDialog(this, mensaje, titulo, tipo);
    }

    /** Envuelve cada handler: los errores controlados se avisan sin cerrar el programa. */
    private void ejecutar(Runnable accion, String exito) {
        try {
            accion.run();
            if (exito != null) {
                mostrar("Listo", exito, JOptionPane.INFORMATION_MESSAGE);
            }
        } catch (ErrorSistema e) {
            mostrar("Revise los datos", e.getMessage(), JOptionPane.WARNING_MESSAGE);
        } catch (RuntimeException e) { // error inesperado: se informa, no se pierde el trabajo
            mostrar("Error inesperado", e.getClass().getSimpleName() + ": " + e.getMessage(), JOptionPane.ERROR_MESSAGE);
        }
    }

    private void refrescarTodo() {
        refrescarPacientes();
        refrescarMedicos();
        refrescarCitas();
    }

    // ------------------------------------------------------------ RF-01 pacientes
    private JPanel pestanaPacientes() {
        JPanel raiz = conMargen(new JPanel(new BorderLayout(6, 6)));
        raiz.add(formulario("Datos del paciente", "DNI (8 dígitos)", pDni, "Nombres", pNombres,
                "Apellidos", pApellidos, "Nacimiento (AAAA-MM-DD)", pNacimiento,
                "Dirección", pDireccion, "Teléfono", pTelefono), BorderLayout.NORTH);
        JPanel centro = new JPanel(new BorderLayout(4, 4));
        JPanel botones = new JPanel(new FlowLayout(FlowLayout.LEFT));
        botones.add(boton("Registrar", this::onRegistrarPaciente));
        botones.add(boton("Actualizar", this::onActualizarPaciente));
        botones.add(boton("Buscar por DNI", this::onBuscarDni));
        botones.add(new JLabel("   Buscar por nombre:"));
        botones.add(pBusqueda);
        botones.add(boton("Buscar", this::onBuscarNombre));
        botones.add(boton("Ver todos", this::refrescarPacientes));
        centro.add(botones, BorderLayout.NORTH);
        centro.add(tablaPacientes.panel, BorderLayout.CENTER);
        raiz.add(centro, BorderLayout.CENTER);
        return raiz;
    }

    private void onRegistrarPaciente() {
        ejecutar(() -> {
            servicio.registrarPaciente(texto(pDni), texto(pNombres), texto(pApellidos), fecha(pNacimiento, true),
                    texto(pDireccion), texto(pTelefono));
            refrescarPacientes();
        }, "Paciente registrado.");
    }

    private void onActualizarPaciente() {
        ejecutar(() -> {
            String nombres = texto(pNombres);
            String apellidos = texto(pApellidos);
            servicio.actualizarPaciente(texto(pDni), nombres.isEmpty() ? null : nombres,
                    apellidos.isEmpty() ? null : apellidos, texto(pDireccion), texto(pTelefono));
            refrescarPacientes();
        }, "Datos actualizados.");
    }

    private void onBuscarDni() {
        ejecutar(() -> mostrarPacientes(List.of(servicio.buscarPorDni(texto(pDni)))), null);
    }

    private void onBuscarNombre() {
        ejecutar(() -> mostrarPacientes(servicio.buscarPorNombre(texto(pBusqueda))), null);
    }

    private void mostrarPacientes(List<Paciente> pacientes) {
        List<Object[]> filas = pacientes.stream()
                .map(p -> new Object[] {p.getDniEnmascarado(), p.nombreCompleto(), p.edad(), p.getTelefono(),
                        p.getDireccion()})
                .toList();
        tablaPacientes.llenar(filas);
    }

    private void refrescarPacientes() {
        mostrarPacientes(servicio.listarPacientes());
    }

    // ------------------------------------------------------------ RF-02 historia clínica
    private JPanel pestanaHistoria() {
        JPanel raiz = conMargen(new JPanel(new BorderLayout(6, 6)));
        JPanel arriba = new JPanel();
        arriba.setLayout(new javax.swing.BoxLayout(arriba, javax.swing.BoxLayout.Y_AXIS));
        arriba.add(formulario("Paciente", "DNI del paciente", hDni, "Alergias", hAlergias,
                "Antecedentes", hAntecedentes));
        JPanel b1 = new JPanel(new FlowLayout(FlowLayout.LEFT));
        b1.add(boton("Cargar historia", this::onCargarHistoria));
        b1.add(boton("Guardar alergias/antecedentes", this::onGuardarHistoria));
        arriba.add(b1);
        arriba.add(formulario("Nueva atención", "CMP del médico", aCmp, "Motivo", aMotivo,
                "Diagnóstico CIE-10", aCie));
        JPanel b2 = new JPanel(new FlowLayout(FlowLayout.LEFT));
        b2.add(boton("Registrar atención", this::onRegistrarAtencion));
        arriba.add(b2);
        raiz.add(arriba, BorderLayout.NORTH);
        raiz.add(tablaAtenciones.panel, BorderLayout.CENTER);
        return raiz;
    }

    private void onCargarHistoria() {
        ejecutar(() -> {
            HistoriaClinica h = servicio.buscarPorDni(texto(hDni)).getHistoria();
            hAlergias.setText(h.getAlergias());
            hAntecedentes.setText(h.getAntecedentes());
            List<Object[]> filas = new ArrayList<>();
            for (Atencion a : h.getAtenciones()) {
                filas.add(new Object[] {a.getFecha(), a.getMotivo(), a.getDiagnostico(), a.getCmpMedico()});
            }
            tablaAtenciones.llenar(filas);
        }, null);
    }

    private void onGuardarHistoria() {
        ejecutar(() -> servicio.actualizarHistoria(texto(hDni), texto(hAlergias), texto(hAntecedentes)),
                "Historia clínica actualizada.");
    }

    private void onRegistrarAtencion() {
        ejecutar(() -> {
            servicio.registrarAtencion(texto(hDni), texto(aCmp), texto(aMotivo), texto(aCie), null);
            onCargarHistoria();
        }, "Atención registrada.");
    }

    // ------------------------------------------------------------ médicos
    private JPanel pestanaMedicos() {
        JPanel raiz = conMargen(new JPanel(new BorderLayout(6, 6)));
        JPanel arriba = new JPanel(new BorderLayout());
        arriba.add(formulario("Nuevo médico", "DNI", mDni, "CMP", mCmp, "Nombres", mNombres,
                "Apellidos", mApellidos, "Especialidad", mEspecialidad, "Teléfono", mTelefono), BorderLayout.NORTH);
        JPanel b = new JPanel(new FlowLayout(FlowLayout.LEFT));
        b.add(boton("Registrar médico", this::onRegistrarMedico));
        arriba.add(b, BorderLayout.SOUTH);
        raiz.add(arriba, BorderLayout.NORTH);
        raiz.add(tablaMedicos.panel, BorderLayout.CENTER);
        return raiz;
    }

    private void onRegistrarMedico() {
        ejecutar(() -> {
            servicio.registrarMedico(texto(mDni), texto(mNombres), texto(mApellidos), texto(mCmp),
                    texto(mEspecialidad), texto(mTelefono));
            refrescarMedicos();
        }, "Médico registrado.");
    }

    private void refrescarMedicos() {
        List<Medico> medicos = servicio.listarMedicos();
        tablaMedicos.llenar(medicos.stream()
                .map(m -> new Object[] {m.getCmp(), m.nombreCompleto(), m.getEspecialidad()}).toList());
        cMedico.removeAllItems();
        medicos.forEach(m -> cMedico.addItem(m.getCmp()));
    }

    // ------------------------------------------------------------ RF-03/04/05 citas y turnos
    private JPanel pestanaCitas() {
        JPanel raiz = conMargen(new JPanel(new BorderLayout(6, 6)));
        JPanel arriba = new JPanel();
        arriba.setLayout(new javax.swing.BoxLayout(arriba, javax.swing.BoxLayout.Y_AXIS));
        JPanel form = new JPanel(new FlowLayout(FlowLayout.LEFT));
        form.setBorder(BorderFactory.createTitledBorder("Agendar cita"));
        form.add(new JLabel("DNI paciente"));
        form.add(cDni);
        form.add(new JLabel("Médico (CMP)"));
        form.add(cMedico);
        form.add(new JLabel("Fecha (AAAA-MM-DD)"));
        form.add(cFecha);
        form.add(new JLabel("Turno"));
        form.add(cTurno);
        arriba.add(form);
        JPanel botones = new JPanel(new FlowLayout(FlowLayout.LEFT));
        botones.add(boton("Agendar cita", this::onAgendar));
        botones.add(boton("Emitir ticket de la cita elegida", this::onEmitir));
        botones.add(boton("Cancelar cita elegida", this::onCancelar));
        botones.add(boton("Ver cupos", this::onCupos));
        botones.add(boton("Actualizar lista", this::refrescarCitas));
        arriba.add(botones);
        JPanel cupos = new JPanel(new FlowLayout(FlowLayout.LEFT));
        cupos.add(lblCupos);
        arriba.add(cupos);
        raiz.add(arriba, BorderLayout.NORTH);
        raiz.add(tablaCitas.panel, BorderLayout.CENTER);

        JPanel estados = new JPanel(new FlowLayout(FlowLayout.LEFT));
        estados.add(new JLabel("Cambiar estado del turno elegido a:"));
        for (EstadoCita e : EstadoCita.values()) {
            if (e.esEstadoDeTicket()) {
                estados.add(boton(e.toString(), () -> onEstado(e)));
            }
        }
        raiz.add(estados, BorderLayout.SOUTH);
        return raiz;
    }

    private String citaElegida() {
        String id = tablaCitas.elegido(0);
        if (id == null) {
            throw new ErrorSistema("Seleccione primero una cita de la tabla.");
        }
        return id;
    }

    private String cmpElegido() {
        Object cmp = cMedico.getSelectedItem();
        if (cmp == null) {
            throw new ErrorSistema("Primero registre un médico en la pestaña «Médicos».");
        }
        return cmp.toString();
    }

    private void onAgendar() {
        ejecutar(() -> {
            servicio.agendarCita(texto(cDni), cmpElegido(), fecha(cFecha, false), (Turno) cTurno.getSelectedItem());
            refrescarCitas();
            onCupos();
        }, "Cita agendada.");
    }

    private void onEmitir() {
        ejecutar(() -> {
            Ticket t = servicio.emitirTicket(citaElegida());
            refrescarCitas();
            mostrar("Ticket emitido", String.format("Su número de turno es el %03d.", t.getNumero()),
                    JOptionPane.INFORMATION_MESSAGE);
        }, null);
    }

    private void onCancelar() {
        ejecutar(() -> {
            servicio.cancelarCita(citaElegida());
            refrescarCitas();
            onCupos();
        }, "Cita cancelada.");
    }

    private void onCupos() {
        ejecutar(() -> {
            Map<Turno, ServicioClinica.Cupo> cupos = servicio.consultarCupos(cmpElegido(), fecha(cFecha, false));
            StringBuilder sb = new StringBuilder("Cupos disponibles →");
            cupos.forEach((turno, c) -> sb.append("   ").append(turno).append(": ")
                    .append(c.disponibles()).append('/').append(c.total()));
            lblCupos.setText(sb.toString());
        }, null);
    }

    private void onEstado(EstadoCita estado) {
        ejecutar(() -> {
            citaElegida();
            String numero = tablaCitas.elegido(5);
            if (numero == null || numero.isBlank()) {
                throw new ErrorSistema("Esa cita aún no tiene ticket. Emítalo primero.");
            }
            servicio.cambiarEstadoTicket(LocalDate.parse(tablaCitas.elegido(3)), Integer.parseInt(numero), estado);
            refrescarCitas();
        }, null);
    }

    private void refrescarCitas() {
        String previa = tablaCitas.elegido(0); // conserva la cita elegida tras refrescar
        Map<String, Integer> numeros = new java.util.HashMap<>();
        servicio.listarTickets(null).forEach(t -> numeros.put(t.getCita().getId(), t.getNumero()));
        List<Object[]> filas = new ArrayList<>();
        for (Cita c : servicio.listarCitas()) {
            Integer n = numeros.get(c.getId());
            filas.add(new Object[] {c.getId(), c.getPaciente().getDniEnmascarado(), c.getMedico().getCmp(),
                    c.getFecha(), c.getTurno(), n == null ? "" : n, c.getEstado()});
        }
        tablaCitas.llenar(filas);
        if (previa != null) {
            for (int i = 0; i < tablaCitas.modelo.getRowCount(); i++) {
                if (previa.equals(String.valueOf(tablaCitas.modelo.getValueAt(i, 0)))) {
                    tablaCitas.tabla.setRowSelectionInterval(i, i);
                }
            }
        }
    }

    // ------------------------------------------------------------ RF-06 reportes
    private JPanel pestanaReportes() {
        JPanel raiz = conMargen(new JPanel(new BorderLayout(6, 6)));
        JPanel barra = new JPanel(new FlowLayout(FlowLayout.LEFT));
        barra.add(new JLabel("Tipo"));
        barra.add(rTipo);
        barra.add(new JLabel("Fecha de referencia (AAAA-MM-DD)"));
        barra.add(rFecha);
        barra.add(boton("Generar", this::onReporte));
        raiz.add(barra, BorderLayout.NORTH);
        rTexto.setEditable(false);
        rTexto.setFont(new java.awt.Font(java.awt.Font.MONOSPACED, java.awt.Font.PLAIN, 14));
        raiz.add(new JScrollPane(rTexto), BorderLayout.CENTER);
        return raiz;
    }

    private void onReporte() {
        ejecutar(() -> {
            ResultadoReporte r = servicio.generarReporte((String) rTipo.getSelectedItem(), fecha(rFecha, false));
            StringBuilder sb = new StringBuilder();
            sb.append("Reporte ").append(r.tipo()).append(": ").append(r.desde()).append(" al ").append(r.hasta())
                    .append('\n');
            sb.append("Atenciones realizadas: ").append(r.totalAtenciones()).append("\n\n");
            sb.append("Patologías más frecuentes (CIE-10):\n");
            if (r.patologiasFrecuentes().isEmpty()) {
                sb.append("  (sin atenciones en el periodo)\n");
            }
            int puesto = 1;
            for (Map.Entry<String, Long> e : r.patologiasFrecuentes()) {
                sb.append("  ").append(puesto++).append(". ").append(e.getKey()).append("  —  ")
                        .append(e.getValue()).append(" caso(s)\n");
            }
            rTexto.setText(sb.toString());
        }, null);
    }
}
