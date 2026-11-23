package pe.sistemarural;

import java.nio.file.*;
import java.time.*;
import java.util.*;
import java.util.zip.ZipFile;

/** Pruebas autocontenidas para ejecutar sin instalar frameworks externos. */
public final class SmokeTests {
    public static void main(String[] args) throws Exception {
        int passed=0;
        check(Validaciones.documento("DNI","12345678").equals("12345678"),"DNI válido"); passed++;
        check(Validaciones.documento("CE","AB123456789").equals("AB123456789"),"CE válido"); passed++;
        expect(()->Validaciones.documento("DNI","123"),"DNI inválido"); passed++;
        expect(()->Validaciones.documento("CE","ABC"),"CE inválido"); passed++;
        check(Validaciones.fecha("29/02/2024","fecha").equals(LocalDate.of(2024,2,29)),"fecha bisiesta"); passed++;
        expect(()->Validaciones.fecha("31/02/2025","fecha"),"fecha inexistente"); passed++;
        Validaciones.cie10("E11.9"); check(true,"CIE-10 válido"); passed++;
        expect(()->Validaciones.cie10("diabetes"),"CIE-10 inválido"); passed++;
        LocalDate next=LocalDate.now().plusDays(1); while(next.getDayOfWeek()==DayOfWeek.SUNDAY)next=next.plusDays(1);
        final LocalDate nextDay=next; Validaciones.cita(nextDay,"08:00"); check(true,"cita en horario válido"); passed++;
        expect(()->Validaciones.cita(nextDay,"12:00"),"hora descanso"); passed++;
        Path x=Files.createTempFile("sistemarural-test-",".xlsx");
        LinkedHashMap<String,List<List<String>>> book=new LinkedHashMap<>();book.put("Prueba",List.of(List.of("Campo","Dato"),List.of("Paciente","Prueba")));
        ExcelWriter.write(x,book);try(ZipFile z=new ZipFile(x.toFile())){check(z.getEntry("xl/workbook.xml")!=null&&z.getEntry("xl/worksheets/sheet1.xml")!=null,"estructura XLSX");passed++;}Files.deleteIfExists(x);
        System.out.println("OK: "+passed+" pruebas Java aprobadas.");
    }
    static void check(boolean v,String name){if(!v)throw new AssertionError(name);System.out.println("PASS "+name);}
    static void expect(Runnable r,String name){try{r.run();throw new AssertionError("Debió fallar: "+name);}catch(IllegalArgumentException ok){System.out.println("PASS "+name);}}
}
