package pe.sistemarural;

import java.time.*;
import java.time.format.*;
import java.util.Locale;

/** Reglas de validación equivalentes al dominio Python. */
public final class Validaciones {
    private Validaciones() {}
    public static String documento(String tipo,String numero){String t=tipo==null?"":tipo.trim().toUpperCase(Locale.ROOT);String n=numero==null?"":numero.trim();if(t.equals("DNI")&&!n.matches("\\d{8}"))throw new IllegalArgumentException("El DNI debe tener exactamente 8 dígitos numéricos.");if(t.equals("CE")&&!n.matches("[A-Za-z0-9]{9,12}"))throw new IllegalArgumentException("El Carné de Extranjería debe tener entre 9 y 12 caracteres alfanuméricos.");if(!t.equals("DNI")&&!t.equals("CE"))throw new IllegalArgumentException("Tipo de documento no válido.");return n;}
    public static LocalDate fecha(String s,String campo){try{return LocalDate.parse(s.trim(),DateTimeFormatter.ofPattern("dd/MM/uuuu").withResolverStyle(ResolverStyle.STRICT));}catch(Exception e){throw new IllegalArgumentException(campo+": use DD/MM/AAAA y una fecha real.");}}
    public static void nacimiento(LocalDate d){if(d.isAfter(LocalDate.now())||d.isBefore(LocalDate.now().minusYears(120)))throw new IllegalArgumentException("La fecha de nacimiento no es válida.");}
    public static void cie10(String s){String v=s==null?"":s.trim().toUpperCase(Locale.ROOT);if(!v.matches("[A-Z][0-9][0-9A-Z](\\.[0-9A-Z]{1,4})?"))throw new IllegalArgumentException("El diagnóstico debe tener un código CIE-10 válido (ej. J00 o E11.9).");}
    public static void cita(LocalDate d,String h){if(d.isBefore(LocalDate.now())||d.isAfter(LocalDate.now().plusDays(90))||d.getDayOfWeek()==DayOfWeek.SUNDAY)throw new IllegalArgumentException("La cita debe ser de lunes a sábado y dentro de los próximos 90 días.");if(h==null||!h.matches("(?:08|09|10|11):(?:00|30)|(?:14|15|16|17):(?:00|30)"))throw new IllegalArgumentException("Horario válido: 08:00–11:30 y 14:00–17:30, cada 30 minutos.");if(!LocalDateTime.of(d,LocalTime.parse(h)).isAfter(LocalDateTime.now()))throw new IllegalArgumentException("No se puede reservar una hora que ya pasó.");}
}
