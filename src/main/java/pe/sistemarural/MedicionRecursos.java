package pe.sistemarural;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import pe.sistemarural.modelo.Paciente;
import pe.sistemarural.servicio.ServicioClinica;

/**
 * Evidencia para CE-01 (búsqueda menor a 3 s) y RD-03 (menos de 256 MB de memoria).
 * Usa archivos temporales: no toca sus datos reales.
 */
public final class MedicionRecursos {
    private static final int PACIENTES = 2000;
    private static final int BUSQUEDAS = 20;

    private MedicionRecursos() {
    }

    public static void main(String[] args) throws Exception {
        Path carpeta = Files.createTempDirectory("sistemarural-medicion");
        ServicioClinica s = new ServicioClinica(carpeta.resolve("d.enc"), carpeta.resolve("k.key"), 10);
        List<Paciente> lote = new ArrayList<>();
        for (int i = 0; i < PACIENTES; i++) {
            lote.add(new Paciente(String.format("%08d", 30_000_000 + i), "Nombre" + i, "Apellido" + i,
                    LocalDate.of(1990, 1, 1), "", ""));
        }
        s.importarPacientes(lote);

        long peor = 0;
        long suma = 0;
        for (int i = 0; i < PACIENTES; i += PACIENTES / BUSQUEDAS) {
            long t0 = System.nanoTime();
            s.buscarPorDni(String.format("%08d", 30_000_000 + i));
            long dt = System.nanoTime() - t0;
            peor = Math.max(peor, dt);
            suma += dt;
        }
        Runtime rt = Runtime.getRuntime();
        double usadoMb = (rt.totalMemory() - rt.freeMemory()) / 1024.0 / 1024.0;
        System.out.printf("Pacientes cargados: %d | búsquedas: %d%n", PACIENTES, BUSQUEDAS);
        System.out.printf("CE-01  tiempo medio: %.4f ms | máximo: %.4f ms | meta: < 3000 ms -> %s%n",
                suma / (double) BUSQUEDAS / 1e6, peor / 1e6, peor < 3_000_000_000L ? "CUMPLE" : "NO CUMPLE");
        System.out.printf("RD-03  memoria usada por la JVM: %.1f MB | meta: < 256 MB -> %s%n",
                usadoMb, usadoMb < 256 ? "CUMPLE" : "NO CUMPLE");
    }
}
