package pe.sistemarural.seguridad;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.attribute.PosixFilePermissions;
import java.security.GeneralSecurityException;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.Base64;
import java.util.HexFormat;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.Mac;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import pe.sistemarural.errores.ErrorSistema;
import pe.sistemarural.errores.ErrorValidacion;

/**
 * Protección de datos personales (RD-02, Ley N.° 29733).
 * <ul>
 *   <li>Cifra con AES-256-GCM (cifrado autenticado: detecta si el dato fue alterado).</li>
 *   <li>Calcula el hash HMAC-SHA256 del DNI para buscar y detectar duplicados sin exponerlo.</li>
 * </ul>
 * La clave se guarda en un archivo local (clave.key) que no debe subirse a GitHub.
 */
public final class Cifrador {
    private static final int TAM_IV = 12;
    private static final int TAM_ETIQUETA_BITS = 128;
    private static Cifrador actual;

    private final SecretKey clave;
    private final byte[] salHash;
    private final SecureRandom azar = new SecureRandom();

    public Cifrador(Path rutaClave) {
        try {
            byte[] bytes;
            if (Files.exists(rutaClave)) {
                bytes = Base64.getDecoder().decode(Files.readString(rutaClave).strip());
            } else {
                KeyGenerator generador = KeyGenerator.getInstance("AES");
                generador.init(256);
                bytes = generador.generateKey().getEncoded();
                Files.writeString(rutaClave, Base64.getEncoder().encodeToString(bytes));
                try {
                    Files.setPosixFilePermissions(rutaClave, PosixFilePermissions.fromString("rw-------"));
                } catch (UnsupportedOperationException | IOException ignorada) {
                    // Windows no usa permisos POSIX: se ignora.
                }
            }
            this.clave = new SecretKeySpec(bytes, "AES");
            MessageDigest sha = MessageDigest.getInstance("SHA-256");
            sha.update("hash-dni|".getBytes(StandardCharsets.UTF_8));
            this.salHash = sha.digest(bytes);
        } catch (GeneralSecurityException | IOException | IllegalArgumentException e) {
            throw new ErrorSistema("No se pudo preparar el cifrado: " + e.getMessage(), e);
        }
    }

    /** Cifrador global que usan las clases del dominio. */
    public static synchronized Cifrador configurar(Path rutaClave) {
        actual = new Cifrador(rutaClave);
        return actual;
    }

    public static synchronized Cifrador actual() {
        if (actual == null) {
            configurar(Path.of("clave.key"));
        }
        return actual;
    }

    public byte[] cifrarBytes(byte[] datos) {
        try {
            byte[] iv = new byte[TAM_IV];
            azar.nextBytes(iv);
            Cipher cifra = Cipher.getInstance("AES/GCM/NoPadding");
            cifra.init(Cipher.ENCRYPT_MODE, clave, new GCMParameterSpec(TAM_ETIQUETA_BITS, iv));
            byte[] cifrado = cifra.doFinal(datos);
            byte[] salida = Arrays.copyOf(iv, TAM_IV + cifrado.length);
            System.arraycopy(cifrado, 0, salida, TAM_IV, cifrado.length);
            return salida;
        } catch (GeneralSecurityException e) {
            throw new ErrorSistema("No se pudo cifrar la información.", e);
        }
    }

    public byte[] descifrarBytes(byte[] datos) {
        try {
            if (datos.length <= TAM_IV) {
                throw new ErrorValidacion("Los datos cifrados están incompletos o dañados.");
            }
            Cipher cifra = Cipher.getInstance("AES/GCM/NoPadding");
            cifra.init(Cipher.DECRYPT_MODE, clave,
                    new GCMParameterSpec(TAM_ETIQUETA_BITS, datos, 0, TAM_IV));
            return cifra.doFinal(datos, TAM_IV, datos.length - TAM_IV);
        } catch (GeneralSecurityException e) {
            throw new ErrorValidacion("No se pudo descifrar: clave incorrecta o dato alterado.");
        }
    }

    public String cifrar(String texto) {
        return Base64.getEncoder().encodeToString(cifrarBytes(texto.getBytes(StandardCharsets.UTF_8)));
    }

    public String descifrar(String token) {
        return new String(descifrarBytes(Base64.getDecoder().decode(token)), StandardCharsets.UTF_8);
    }

    public String hashDni(String dni) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(salHash, "HmacSHA256"));
            return HexFormat.of().formatHex(mac.doFinal(dni.getBytes(StandardCharsets.UTF_8)));
        } catch (GeneralSecurityException e) {
            throw new ErrorSistema("No se pudo calcular el hash del DNI.", e);
        }
    }
}
