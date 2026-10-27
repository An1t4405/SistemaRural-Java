package pe.sistemarural;

import java.nio.file.Path;
import java.time.LocalDate;
import pe.sistemarural.modelo.Turno;
import pe.sistemarural.servicio.ServicioClinica;

/**
 * Carga datos FICTICIOS para probar el sistema antes de tener la posta.
 * Ejecutar este archivo (clic derecho → Run File) una sola vez.
 */
public final class CargarDemo {
    private CargarDemo() {
    }

    public static void main(String[] args) {
        ServicioClinica s = new ServicioClinica(Path.of("datos.enc"), Path.of("clave.key"), 10);
        if (!s.listarMedicos().isEmpty()) {
            System.out.println("Ya hay datos cargados; no se agregó nada. Borre datos.enc y clave.key para reiniciar.");
            return;
        }
        s.registrarMedico("40000001", "Rosa", "Quispe Vera", "CMP-1001", "Medicina General", "");
        s.registrarMedico("40000002", "Carlos", "Mendoza Ruiz", "CMP-1002", "Obstetricia", "");
        String[][] nombres = {{"Ana", "Torres Gil"}, {"Luis", "Paredes Soto"}, {"María", "Castillo Ríos"},
            {"José", "Alva Núñez"}, {"Elena", "Rojas León"}};
        String[] diagnosticos = {"J00", "J00", "E11.9", "I10", "J20"};
        for (int i = 0; i < nombres.length; i++) {
            String dni = "7000000" + i;
            s.registrarPaciente(dni, nombres[i][0], nombres[i][1], LocalDate.of(1985 + i, 3, 10 + i),
                    "Moche, La Libertad", "95000000" + i);
            s.registrarAtencion(dni, "CMP-1001", "Consulta de rutina", diagnosticos[i], LocalDate.now().minusDays(i));
        }
        LocalDate manana = LocalDate.now().plusDays(1);
        for (int i = 0; i < 3; i++) {
            s.emitirTicket(s.agendarCita("7000000" + i, "CMP-1001", manana, Turno.MANANA).getId());
        }
        System.out.println("Datos de demostración cargados.");
    }
}
