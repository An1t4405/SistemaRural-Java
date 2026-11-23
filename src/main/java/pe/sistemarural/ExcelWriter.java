package pe.sistemarural;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Generador XLSX OOXML sin dependencias externas. */
public final class ExcelWriter {
    private ExcelWriter() {}
    public static void write(Path file, LinkedHashMap<String,List<List<String>>> sheets) throws IOException {
        Files.createDirectories(file.toAbsolutePath().getParent());
        try (ZipOutputStream z = new ZipOutputStream(Files.newOutputStream(file), StandardCharsets.UTF_8)) {
            entry(z,"[Content_Types].xml", contentTypes(sheets.size()));
            entry(z,"_rels/.rels","<?xml version=\"1.0\" encoding=\"UTF-8\"?><Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\"><Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"xl/workbook.xml\"/></Relationships>");
            StringBuilder wb=new StringBuilder("<?xml version=\"1.0\" encoding=\"UTF-8\"?><workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\"><sheets>");
            StringBuilder rel=new StringBuilder("<?xml version=\"1.0\" encoding=\"UTF-8\"?><Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">");
            int i=1; for(String name:sheets.keySet()){wb.append("<sheet name=\"").append(xml(name)).append("\" sheetId=\"").append(i).append("\" r:id=\"rId").append(i).append("\"/>");rel.append("<Relationship Id=\"rId").append(i).append("\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet\" Target=\"worksheets/sheet").append(i).append(".xml\"/>");i++;}
            wb.append("</sheets></workbook>");rel.append("</Relationships>");entry(z,"xl/workbook.xml",wb.toString());entry(z,"xl/_rels/workbook.xml.rels",rel.toString());
            i=1;for(List<List<String>> rows:sheets.values()){StringBuilder x=new StringBuilder("<?xml version=\"1.0\" encoding=\"UTF-8\"?><worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><sheetData>");int rn=1;for(List<String> row:rows){x.append("<row r=\"").append(rn).append("\">");for(int c=0;c<row.size();c++){String ref=col(c+1)+rn;x.append("<c r=\"").append(ref).append("\" t=\"inlineStr\"><is><t xml:space=\"preserve\">").append(xml(Objects.toString(row.get(c),""))).append("</t></is></c>");}x.append("</row>");rn++;}x.append("</sheetData></worksheet>");entry(z,"xl/worksheets/sheet"+i+".xml",x.toString());i++;}
        }
    }
    private static String contentTypes(int n){StringBuilder s=new StringBuilder("<?xml version=\"1.0\" encoding=\"UTF-8\"?><Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Default Extension=\"xml\" ContentType=\"application/xml\"/><Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/>");for(int i=1;i<=n;i++)s.append("<Override PartName=\"/xl/worksheets/sheet").append(i).append(".xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/>");return s.append("</Types>").toString();}
    private static void entry(ZipOutputStream z,String name,String value)throws IOException{z.putNextEntry(new ZipEntry(name));z.write(value.getBytes(StandardCharsets.UTF_8));z.closeEntry();}
    private static String col(int n){StringBuilder s=new StringBuilder();while(n>0){int r=(n-1)%26;s.insert(0,(char)('A'+r));n=(n-1)/26;}return s.toString();}
    private static String xml(String s){return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\"","&quot;").replace("'","&apos;");}
}
