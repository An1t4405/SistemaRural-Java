package pe.sistemarural;

import java.nio.file.Path;
import javax.swing.JOptionPane;
import javax.swing.SwingUtilities;
import javax.swing.UIManager;
import pe.sistemarural.servicio.ServicioClinica;
import pe.sistemarural.ui.VentanaPrincipal;

/** Punto de entrada: abre la ventana principal de SistemaRural-PE. */
public final class Main {
    private Main() {
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception ignorada) {
                // si falla, se usa el aspecto por defecto de Java
            }
            try {
                ServicioClinica servicio = new ServicioClinica(Path.of("datos.enc"), Path.of("clave.key"), 10);
                new VentanaPrincipal(servicio).setVisible(true);
            } catch (RuntimeException e) {
                JOptionPane.showMessageDialog(null,
                        "No se pudo iniciar el sistema:\n" + e.getMessage()
                                + "\n\nSi cambió o perdió clave.key, borre datos.enc y clave.key para empezar de cero.",
                        "Error al iniciar", JOptionPane.ERROR_MESSAGE);
            }
        });
    }
}
