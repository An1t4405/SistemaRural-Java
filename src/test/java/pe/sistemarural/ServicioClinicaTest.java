package pe.sistemarural;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import pe.sistemarural.errores.CupoAgotado;
import pe.sistemarural.errores.DniDuplicado;
import pe.sistemarural.errores.ErrorValidacion;
import pe.sistemarural.errores.NoEncontrado;
import pe.sistemarural.modelo.EstadoCita;
import pe.sistemarural.modelo.GeneradorTurnos;
import pe.sistemarural.modelo.Paciente;
import pe.sistemarural.modelo.Persona;
import pe.sistemarural.modelo.Ticket;
import pe.sistemarural.modelo.Turno;
import pe.sistemarural.reportes.ReporteDiario;
import pe.sistemarural.reportes.ReporteFactory;
import pe.sistemarural.reportes.ReporteMensual;
import pe.sistemarural.reportes.ReporteSemanal;
import pe.sistemarural.reportes.ResultadoReporte;
import pe.sistemarural.servicio.ServicioClinica;

/** Pruebas automatizadas: CE-01, CE-02, CE-03, RD-02, RF-03, RF-06 y patrones de diseño. */
class ServicioClinicaTest {
    private static final LocalDate NAC = LocalDate.of(1990, 5, 17);
    private static final LocalDate MANANA = LocalDate.now().plusDays(1);

    @TempDir
    Path carpeta;
    ServicioClinica srv;

    @BeforeEach
    void preparar() {
        srv = nuevoServicio(3);
        srv.registrarMedico("40000001", "Rosa", "Quispe", "CMP-1001", "Medicina General", "");
    }

    private ServicioClinica nuevoServicio(int cupos) {
        return new ServicioClinica(carpeta.resolve("datos.enc"), carpeta.resolve("clave.key"), cupos);
    }

    /** Servicio con archivos propios (no reutiliza los datos del servicio de cada prueba). */
    private ServicioClinica servicioAparte(int cupos) {
        return new ServicioClinica(carpeta.resolve("aparte.enc"), carpeta.resolve("aparte.key"), cupos);
    }

    private static String dni(int n) {
        return String.format("%08d", n);
    }

    // ------------------------------------------------------------- RD-02
    @Test
    void dniNoQuedaEnTextoPlano() {
        Paciente p = srv.registrarPaciente("12345678", "Ana", "Torres", NAC, "", "");
        assertEquals("****5678", p.getDniEnmascarado());
        assertTrue(p.coincideDni("12345678"));
        assertFalse(p.coincideDni("87654321"));
    }

    @Test
    void archivoDeDatosEstaCifrado() throws IOException {
        srv.registrarPaciente("12345678", "Ana", "Torres", NAC, "", "");
        srv.actualizarHistoria("12345678", "Penicilina", null);
        srv.registrarAtencion("12345678", "CMP-1001", "Fiebre", "J00", null);
        String crudo = new String(Files.readAllBytes(carpeta.resolve("datos.enc")), StandardCharsets.ISO_8859_1);
        for (String secreto : List.of("12345678", "Penicilina", "J00", "Torres")) {
            assertFalse(crudo.contains(secreto), "Se encontró en claro: " + secreto);
        }
    }

    @Test
    void persistenciaIdaYVuelta() {
        srv.registrarPaciente("12345678", "Ana", "Torres", NAC, "", "");
        srv.registrarAtencion("12345678", "CMP-1001", "Tos", "J20", null);
        srv.emitirTicket(srv.agendarCita("12345678", "CMP-1001", MANANA, Turno.MANANA).getId());

        ServicioClinica otro = nuevoServicio(3);
        assertEquals("J20", otro.buscarPorDni("12345678").getHistoria().getAtenciones().get(0).getDiagnostico());
        assertEquals(1, otro.listarTickets(null).get(0).getNumero());
        Ticket nuevo = otro.emitirTicket(otro.agendarCita("12345678", "CMP-1001", MANANA, Turno.TARDE).getId());
        assertEquals(2, nuevo.getNumero()); // el correlativo continúa tras reiniciar
    }

    // ------------------------------------------------------------- validaciones
    @ParameterizedTest
    @ValueSource(strings = {"1234567", "123456789", "1234567a", "", "12 45678"})
    void dniInvalidoSeRechaza(String malo) {
        assertThrows(ErrorValidacion.class, () -> srv.registrarPaciente(malo, "Ana", "Torres", NAC, "", ""));
    }

    @Test
    void cie10InvalidoSeRechaza() {
        srv.registrarPaciente("12345678", "Ana", "Torres", NAC, "", "");
        assertThrows(ErrorValidacion.class, () -> srv.registrarAtencion("12345678", "CMP-1001", "Dolor", "XYZ", null));
    }

    @Test
    void pacienteInexistente() {
        assertThrows(NoEncontrado.class, () -> srv.buscarPorDni("99999999"));
    }

    // ------------------------------------------------------------- CE-02
    @Test
    void ce02DniRepetidoEsRechazado() {
        srv.registrarPaciente("12345678", "Ana", "Torres", NAC, "", "");
        assertThrows(DniDuplicado.class, () -> srv.registrarPaciente("12345678", "Otra", "Persona", NAC, "", ""));
        assertEquals(1, srv.listarPacientes().size());
    }

    // ------------------------------------------------------------- RF-03 / RF-05
    @Test
    void cuposSeAgotanYSeLiberan() {
        for (int i = 1; i <= 4; i++) {
            srv.registrarPaciente(dni(i), "P" + i, "Prueba", NAC, "", "");
        }
        List<String> ids = new ArrayList<>();
        for (int i = 1; i <= 3; i++) {
            ids.add(srv.agendarCita(dni(i), "CMP-1001", MANANA, Turno.MANANA).getId());
        }
        ServicioClinica.Cupo cupo = srv.consultarCupos("CMP-1001", MANANA).get(Turno.MANANA);
        assertEquals(0, cupo.disponibles());
        assertEquals(3, cupo.total());
        assertThrows(CupoAgotado.class, () -> srv.agendarCita(dni(4), "CMP-1001", MANANA, Turno.MANANA));
        srv.cancelarCita(ids.get(0));
        srv.agendarCita(dni(4), "CMP-1001", MANANA, Turno.MANANA); // el cupo liberado se puede reusar
    }

    @Test
    void noSeAgendaEnElPasado() {
        srv.registrarPaciente("12345678", "Ana", "Torres", NAC, "", "");
        assertThrows(ErrorValidacion.class,
                () -> srv.agendarCita("12345678", "CMP-1001", LocalDate.now().minusDays(1), Turno.MANANA));
    }

    // ------------------------------------------------------------- CE-03
    @Test
    void ce03CienTicketsCorrelativosYUnicos() {
        ServicioClinica s = servicioAparte(100);
        s.registrarMedico("40000002", "Carlos", "Mendoza", "CMP-1002", "Obstetricia", "");
        for (int i = 0; i < 100; i++) {
            String d = dni(10_000_000 + i);
            s.registrarPaciente(d, "P" + i, "Prueba", NAC, "", "");
            s.emitirTicket(s.agendarCita(d, "CMP-1002", MANANA, Turno.MANANA).getId());
        }
        List<Integer> numeros = s.listarTickets(MANANA).stream().map(Ticket::getNumero).toList();
        assertEquals(100, numeros.size());
        for (int i = 0; i < 100; i++) {
            assertEquals(i + 1, numeros.get(i));
        }
        assertEquals(100, numeros.stream().distinct().count());
    }

    @Test
    void ticketCambiaDeEstado() {
        srv.registrarPaciente("12345678", "Ana", "Torres", NAC, "", "");
        Ticket t = srv.emitirTicket(srv.agendarCita("12345678", "CMP-1001", MANANA, Turno.MANANA).getId());
        srv.cambiarEstadoTicket(MANANA, t.getNumero(), EstadoCita.EN_ATENCION);
        assertEquals(EstadoCita.EN_ATENCION, t.getEstado());
        assertThrows(ErrorValidacion.class,
                () -> srv.cambiarEstadoTicket(MANANA, t.getNumero(), EstadoCita.CANCELADA));
    }

    // ------------------------------------------------------------- CE-01
    @Test
    void ce01BusquedaMenorA3Segundos() {
        ServicioClinica s = servicioAparte(10);
        List<Paciente> lote = new ArrayList<>();
        for (int i = 0; i < 1000; i++) {
            lote.add(new Paciente(dni(20_000_000 + i), "Nombre" + i, "Apellido" + i, NAC, "", ""));
        }
        s.importarPacientes(lote);
        long peor = 0;
        int busquedas = 0;
        for (int i = 0; i < 1000; i += 50) {
            long t0 = System.nanoTime();
            s.buscarPorDni(dni(20_000_000 + i));
            peor = Math.max(peor, System.nanoTime() - t0);
            busquedas++;
        }
        assertEquals(20, busquedas);
        assertTrue(peor < 3_000_000_000L, "La búsqueda tardó " + peor / 1_000_000 + " ms");
    }

    // ------------------------------------------------------------- RF-06
    @Test
    void reportesDiarioSemanalMensual() {
        srv.registrarPaciente("12345678", "Ana", "Torres", NAC, "", "");
        LocalDate hoy = LocalDate.of(2026, 10, 14); // miércoles
        Object[][] casos = {{0, "J00"}, {0, "J00"}, {1, "E11.9"}, {-5, "J00"}, {-20, "I10"}};
        for (Object[] c : casos) {
            srv.registrarAtencion("12345678", "CMP-1001", "Consulta", (String) c[1], hoy.plusDays((int) c[0]));
        }
        ResultadoReporte d = srv.generarReporte("diario", hoy);
        ResultadoReporte s = srv.generarReporte("semanal", hoy);
        ResultadoReporte m = srv.generarReporte("mensual", hoy);
        assertEquals(2, d.totalAtenciones());
        assertEquals(3, s.totalAtenciones()); // lunes 12 al domingo 18
        assertEquals(4, m.totalAtenciones()); // octubre 2026 (la de -20 cae en septiembre)
        assertEquals("J00", m.patologiasFrecuentes().get(0).getKey());
        assertEquals(3L, m.patologiasFrecuentes().get(0).getValue());
        assertThrows(ErrorValidacion.class, () -> srv.generarReporte("anual", hoy));
    }

    @Test
    void busquedaPorNombre() {
        srv.registrarPaciente("12345678", "Ana", "Torres", NAC, "", "");
        srv.registrarPaciente("12345679", "Luis", "Torres", NAC, "", "");
        assertEquals(2, srv.buscarPorNombre("torres").size());
        assertEquals(1, srv.buscarPorNombre("luis").size());
    }

    // ------------------------------------------------------------- patrones y encapsulamiento
    @Test
    void singletonGeneradorTurnosEsUnaSolaInstancia() {
        assertSame(GeneradorTurnos.getInstancia(), GeneradorTurnos.getInstancia());
    }

    @Test
    void factoryCreaElReporteCorrecto() {
        assertInstanceOf(ReporteDiario.class, ReporteFactory.crear("diario", List.of()));
        assertInstanceOf(ReporteSemanal.class, ReporteFactory.crear("Semanal", List.of()));
        assertInstanceOf(ReporteMensual.class, ReporteFactory.crear("MENSUAL", List.of()));
    }

    @Test
    void personaEsAbstracta() {
        assertTrue(java.lang.reflect.Modifier.isAbstract(Persona.class.getModifiers()));
    }

    @Test
    void settersValidanLosDatos() {
        Paciente p = srv.registrarPaciente("12345678", "Ana", "Torres", NAC, "", "");
        assertThrows(ErrorValidacion.class, () -> p.setNombres("   "));
        p.setTelefono(" 955123456 ");
        assertEquals("955123456", p.getTelefono());
        assertNotNull(p.getHistoria());
    }
}
