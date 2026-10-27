package pe.sistemarural.modelo;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;

/**
 * Patrón Singleton: una única fuente de números correlativos por día (CE-03).
 * Es seguro entre hilos (métodos synchronized) y evita números repetidos.
 */
public final class GeneradorTurnos {
    private static final GeneradorTurnos INSTANCIA = new GeneradorTurnos();

    private final Map<LocalDate, Integer> contadores = new HashMap<>();

    private GeneradorTurnos() {
    }

    public static GeneradorTurnos getInstancia() {
        return INSTANCIA;
    }

    public synchronized int siguiente(LocalDate fecha) {
        int numero = contadores.getOrDefault(fecha, 0) + 1;
        contadores.put(fecha, numero);
        return numero;
    }

    public synchronized HashMap<LocalDate, Integer> exportar() {
        return new HashMap<>(contadores);
    }

    public synchronized void restaurar(Map<LocalDate, Integer> guardados) {
        contadores.clear();
        contadores.putAll(guardados);
    }
}
