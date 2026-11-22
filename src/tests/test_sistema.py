"""Pruebas automatizadas: CE-01, CE-02, CE-03, RD-02, RF-03, RF-06."""
import time
from datetime import date, timedelta

import pytest

from sistema_rural.errores import CupoAgotado, DNIDuplicado, ErrorValidacion, NoEncontrado
from sistema_rural.servicio import ServicioClinica

NAC = date(1990, 5, 17)
MAÑANA = date.today() + timedelta(days=1)
if MAÑANA.weekday() == 6:                       # la posta no atiende domingos
    MAÑANA += timedelta(days=1)


def dni(n: int) -> str:
    return f"{n:08d}"


@pytest.fixture
def srv(tmp_path):
    s = ServicioClinica(tmp_path / "datos.enc", tmp_path / "clave.key", cupos_por_turno=3)
    s.registrar_medico("40000001", "Rosa", "Quispe", "CMP-1001", "Medicina General")
    return s


# ---------------------------------------------------------------- RD-02
def test_dni_no_queda_en_texto_plano(srv):
    p = srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    assert p.get_dni_enmascarado() == "****5678"
    assert "12345678" not in str(vars(p))          # ni cifrado ni hash lo contienen en claro
    assert p.coincide_dni("12345678") and not p.coincide_dni("87654321")


def test_archivo_de_datos_esta_cifrado(srv, tmp_path):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    srv.actualizar_historia("12345678", alergias="Penicilina")
    srv.registrar_atencion("12345678", "CMP-1001", "Fiebre", "J00")
    crudo = (tmp_path / "datos.enc").read_bytes()
    # Se buscan fragmentos suficientemente largos para evitar falsos positivos
    # por coincidencias casuales en el texto Base64 del cifrado.
    for secreto in (b"12345678", b"Penicilina", b'"diagnostico": "J00"', b"Torres"):
        assert secreto not in crudo


def test_persistencia_ida_y_vuelta(srv, tmp_path):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    srv.registrar_atencion("12345678", "CMP-1001", "Tos", "J20")
    cita = srv.agendar_cita("12345678", "CMP-1001", MAÑANA, "MAÑANA")
    srv.emitir_ticket(cita.get_id())
    otro = ServicioClinica(tmp_path / "datos.enc", tmp_path / "clave.key", cupos_por_turno=3)
    assert otro.buscar_por_dni("12345678").get_historia().get_atenciones()[0].get_diagnostico() == "J20"
    assert [t.get_numero() for t in otro.listar_tickets()] == [1]
    nuevo = otro.emitir_ticket(otro.agendar_cita("12345678", "CMP-1001", MAÑANA, "TARDE").get_id())
    assert nuevo.get_numero() == 2   # el correlativo continúa tras reiniciar


# ---------------------------------------------------------------- validaciones
@pytest.mark.parametrize("malo", ["1234567", "123456789", "1234567a", "", "12 45678"])
def test_dni_invalido_se_rechaza(srv, malo):
    with pytest.raises(ErrorValidacion):
        srv.registrar_paciente(malo, "Ana", "Torres", NAC)


def test_cie10_invalido_se_rechaza(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    with pytest.raises(ErrorValidacion):
        srv.registrar_atencion("12345678", "CMP-1001", "Dolor", "XYZ")


def test_paciente_inexistente(srv):
    with pytest.raises(NoEncontrado):
        srv.buscar_por_dni("99999999")


# ---------------------------------------------------------------- CE-02
def test_ce02_dni_repetido_es_rechazado(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    with pytest.raises(DNIDuplicado):
        srv.registrar_paciente("12345678", "Otra", "Persona", NAC)
    assert len(srv.listar_pacientes()) == 1


# ---------------------------------------------------------------- RF-03 / RF-05
def test_cupos_se_agotan_y_se_liberan(srv):
    for i in range(1, 5):
        srv.registrar_paciente(dni(i), f"P{i}", "Prueba", NAC)
    citas = [srv.agendar_cita(dni(i), "CMP-1001", MAÑANA, "MAÑANA") for i in range(1, 4)]
    assert srv.consultar_cupos("CMP-1001", MAÑANA)["MAÑANA"] == (0, 3)
    with pytest.raises(CupoAgotado):
        srv.agendar_cita(dni(4), "CMP-1001", MAÑANA, "MAÑANA")
    srv.cancelar_cita(citas[0].get_id())
    srv.agendar_cita(dni(4), "CMP-1001", MAÑANA, "MAÑANA")   # el cupo liberado se puede reusar



def test_no_se_agendan_citas_los_domingo(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    domingo = date.today() + timedelta(days=(6 - date.today().weekday()) % 7 or 7)
    with pytest.raises(ErrorValidacion, match="domingos"):
        srv.agendar_cita("12345678", "CMP-1001", domingo, "08:00")


def test_se_permiten_citas_lunes_a_sabado(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    proxima_fecha = date.today() + timedelta(days=1)
    while proxima_fecha.weekday() == 6:
        proxima_fecha += timedelta(days=1)
    cita = srv.agendar_cita("12345678", "CMP-1001", proxima_fecha, "08:00")
    assert cita.get_fecha() == proxima_fecha

def test_no_se_agenda_en_el_pasado(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    with pytest.raises(ErrorValidacion):
        srv.agendar_cita("12345678", "CMP-1001", date.today() - timedelta(days=1), "MAÑANA")


# ---------------------------------------------------------------- CE-03
def test_ce03_cien_tickets_correlativos_y_unicos(tmp_path):
    s = ServicioClinica(tmp_path / "d.enc", tmp_path / "k.key", cupos_por_turno=100)
    s.registrar_medico("40000001", "Rosa", "Quispe", "CMP-1001", "Medicina General")
    for i in range(100):
        s.registrar_paciente(dni(10_000_000 + i), f"P{i}", "Prueba", NAC)
        fecha = MAÑANA
        dias_habiles = 0
        while dias_habiles < i // 16:
            fecha += timedelta(days=1)
            if fecha.weekday() != 6:
                dias_habiles += 1
        if fecha.weekday() == 6:
            fecha += timedelta(days=1)
        hora = ("08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
                "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00", "17:30")[i % 16]
        s.emitir_ticket(s.agendar_cita(dni(10_000_000 + i), "CMP-1001", fecha, hora).get_id())
    for fecha in {t.get_fecha() for t in s.listar_tickets()}:
        numeros = [t.get_numero() for t in s.listar_tickets(fecha)]
        assert numeros == list(range(1, len(numeros) + 1))
    assert len({(t.get_fecha(), t.get_numero()) for t in s.listar_tickets()}) == 100


def test_ticket_cambia_de_estado(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    t = srv.emitir_ticket(srv.agendar_cita("12345678", "CMP-1001", MAÑANA, "MAÑANA").get_id())
    srv.cambiar_estado_ticket(MAÑANA, t.get_numero(), "EN_ATENCION")
    assert t.get_estado() == "EN_ATENCION"
    with pytest.raises(ErrorValidacion):
        srv.cambiar_estado_ticket(MAÑANA, t.get_numero(), "INVENTADO")


# ---------------------------------------------------------------- CE-01
def test_ce01_busqueda_menor_a_3_segundos(tmp_path):
    s = ServicioClinica(tmp_path / "d.enc", tmp_path / "k.key")
    # 1000 pacientes (muy por encima de lo que atiende la posta); se guarda una vez al final
    from sistema_rural.modelos import Paciente
    for i in range(1000):
        p = Paciente(dni(20_000_000 + i), f"Nombre{i}", f"Apellido{i}", NAC)
        s._pacientes[p.get_dni_hash()] = p
    tiempos = []
    for i in range(0, 1000, 50):   # 20 búsquedas
        t0 = time.perf_counter()
        s.buscar_por_dni(dni(20_000_000 + i))
        tiempos.append(time.perf_counter() - t0)
    assert len(tiempos) == 20 and max(tiempos) < 3.0


# ---------------------------------------------------------------- RF-06
def test_reportes_diario_semanal_mensual(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    hoy = date(2026, 10, 14)  # miércoles
    for dias, cie in [(0, "J00"), (0, "J00"), (1, "E11.9"), (-5, "J00"), (-20, "I10")]:
        srv.registrar_atencion("12345678", "CMP-1001", "Consulta", cie, fecha=hoy + timedelta(days=dias))
    d, s, m = (srv.generar_reporte(t, hoy) for t in ("diario", "semanal", "mensual"))
    assert d["total_atenciones"] == 2
    assert s["total_atenciones"] == 3       # lunes 12 al domingo 18
    assert m["total_atenciones"] == 4       # octubre 2026 (la de -20 cae en septiembre)
    assert m["patologias_frecuentes"][0] == ("J00", 3)
    with pytest.raises(ErrorValidacion):
        srv.generar_reporte("anual", hoy)


def test_busqueda_por_nombre(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    srv.registrar_paciente("12345679", "Luis", "Torres", NAC)
    assert len(srv.buscar_por_nombre("torres")) == 2
    assert len(srv.buscar_por_nombre("luis")) == 1


# ---------------------------------------------------------------- patrones y encapsulamiento (rúbrica EF)
def test_singleton_generador_turnos_es_una_sola_instancia():
    from sistema_rural.modelos import GeneradorTurnos
    assert GeneradorTurnos() is GeneradorTurnos()


def test_factory_crea_el_reporte_correcto():
    from sistema_rural.reportes import ReporteDiario, ReporteFactory, ReporteMensual, ReporteSemanal
    assert isinstance(ReporteFactory.crear("diario", []), ReporteDiario)
    assert isinstance(ReporteFactory.crear("Semanal", []), ReporteSemanal)
    assert isinstance(ReporteFactory.crear("MENSUAL", []), ReporteMensual)


def test_persona_es_abstracta():
    from sistema_rural.modelos import Persona
    with pytest.raises(TypeError):
        Persona("12345678", "Ana", "Torres")


def test_setters_validan_los_datos(srv):
    p = srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    with pytest.raises(ErrorValidacion):
        p.set_nombres("   ")
    p.set_telefono(" 955123456 ")
    assert p.get_telefono() == "955123456"


def test_citas_respetan_horarios_y_no_se_superponen(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    srv.registrar_paciente("12345679", "Luis", "Rojas", NAC)
    cita = srv.agendar_cita("12345678", "CMP-1001", MAÑANA, "08:00")
    assert cita.get_hora_fin() == "08:30"
    with pytest.raises(CupoAgotado):
        srv.agendar_cita("12345679", "CMP-1001", MAÑANA, "08:00")
    with pytest.raises(ErrorValidacion):
        srv.agendar_cita("12345679", "CMP-1001", MAÑANA, "12:00")
    with pytest.raises(ErrorValidacion):
        srv.agendar_cita("12345679", "CMP-1001", MAÑANA, "17:45")
    srv.agendar_cita("12345679", "CMP-1001", MAÑANA, "08:30")


def test_diferentes_medicos_pueden_atender_a_la_misma_hora(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    srv.registrar_paciente("12345679", "Luis", "Rojas", NAC)
    srv.registrar_medico("40000002", "Luis", "Paz", "CMP-1002", "Pediatría")
    srv.agendar_cita("12345678", "CMP-1001", MAÑANA, "09:00")
    srv.agendar_cita("12345679", "CMP-1002", MAÑANA, "09:00")


def test_persistencia_de_hora_de_cita(srv, tmp_path):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    cita = srv.agendar_cita("12345678", "CMP-1001", MAÑANA, "14:30")
    otro = ServicioClinica(srv.ruta_datos(), tmp_path / "clave.key")
    assert otro.listar_citas()[0].get_hora() == "14:30"


def test_exportaciones_txt_y_excel(srv, tmp_path):
    pytest.importorskip("openpyxl")
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    srv.agendar_cita("12345678", "CMP-1001", MAÑANA, "08:00")
    txt, xlsx = tmp_path / "resumen.txt", tmp_path / "reporte.xlsx"
    srv.exportar_txt(txt)
    srv.exportar_excel(xlsx)
    assert "****5678" in txt.read_text(encoding="utf-8")
    assert xlsx.exists() and xlsx.stat().st_size > 0


def test_carnet_extranjeria_se_registra_y_se_busca(srv):
    p = srv.registrar_paciente("AB123456789", "Sofia", "Rojas", NAC, tipo_documento="CE")
    assert p.get_tipo_documento() == "CE"
    assert p.get_dni_enmascarado().endswith("6789")
    assert srv.buscar_por_documento("CE", "AB123456789").nombre_completo() == "Rojas, Sofia"
    with pytest.raises(ErrorValidacion):
        srv.buscar_por_dni("AB123456789")


def test_carnet_extranjeria_invalido_se_rechaza(srv):
    with pytest.raises(ErrorValidacion):
        srv.registrar_paciente("12345", "Sofia", "Rojas", NAC, tipo_documento="CE")


def test_persistencia_de_paciente_con_ce(srv, tmp_path):
    srv.registrar_paciente("AB123456789", "Sofia", "Rojas", NAC, tipo_documento="CE")
    otro = ServicioClinica(tmp_path / "datos.enc", tmp_path / "clave.key", cupos_por_turno=3)
    assert otro.buscar_por_documento("CE", "AB123456789").get_tipo_documento() == "CE"


def test_cita_puede_agendarse_con_carnet_extranjeria(srv):
    srv.registrar_paciente("AB123456789", "Sofia", "Rojas", NAC, tipo_documento="CE")
    cita = srv.agendar_cita("AB123456789", "CMP-1001", MAÑANA, "15:30", "CE")
    assert cita.get_paciente().get_tipo_documento() == "CE"
    assert cita.get_hora() == "15:30"


# ---------------------------------------------------------------- mejoras: horarios, exportaciones
def test_txt_tiene_saltos_de_linea_reales(srv, tmp_path):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    srv.agendar_cita("12345678", "CMP-1001", MAÑANA, "09:00")
    ruta = srv.exportar_txt(tmp_path / "r.txt")
    texto = open(ruta, encoding="utf-8").read()
    assert "\\n" not in texto and len(texto.splitlines()) >= 7
    assert "12345678" not in texto


def test_exportaciones_van_a_la_carpeta_por_defecto(srv, tmp_path):
    from pathlib import Path
    r1, r2 = srv.exportar_txt(), srv.exportar_excel()
    assert Path(r1).parent == tmp_path / "exportaciones" == Path(srv.carpeta_exportaciones())
    assert Path(r1).exists() and Path(r2).exists()


def test_paciente_no_puede_tener_dos_citas_cruzadas(srv):
    srv.registrar_medico("40000002", "Luis", "Paz", "CMP-1002", "Pediatría")
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    srv.agendar_cita("12345678", "CMP-1001", MAÑANA, "09:00")
    with pytest.raises(CupoAgotado):
        srv.agendar_cita("12345678", "CMP-1002", MAÑANA, "09:00")
    srv.agendar_cita("12345678", "CMP-1002", MAÑANA, "09:30")      # otra hora sí se puede


def test_cita_cancelada_libera_al_paciente(srv):
    srv.registrar_medico("40000002", "Luis", "Paz", "CMP-1002", "Pediatría")
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    c = srv.agendar_cita("12345678", "CMP-1001", MAÑANA, "09:00")
    srv.cancelar_cita(c.get_id())
    srv.agendar_cita("12345678", "CMP-1002", MAÑANA, "09:00")


def test_hora_que_ya_paso_hoy_se_rechaza():
    from datetime import datetime
    from sistema_rural.modelos import AgendaMedica, Medico, Paciente
    ag = AgendaMedica()
    m = Medico("40000001", "Rosa", "Quispe", "CMP-1001", "Medicina General")
    p = Paciente("12345678", "Ana", "Torres", NAC)
    ahora = datetime(2030, 3, 4, 10, 15)          # lunes
    with pytest.raises(ErrorValidacion):
        ag.agendar(p, m, ahora.date(), "10:00", ahora)
    assert ag.agendar(p, m, ahora.date(), "10:30", ahora).get_hora() == "10:30"


def test_horas_fuera_de_horario_y_fecha_imposible(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    for hora in ("07:30", "12:00", "13:00", "18:00", "09:10"):
        with pytest.raises(ErrorValidacion):
            srv.agendar_cita("12345678", "CMP-1001", MAÑANA, hora)
    from sistema_rural import fechas
    for malo in ("31/02/2027", "32/01/2027", "00/10/2027", "2027-13-01"):
        with pytest.raises(ErrorValidacion):
            fechas.parsear_fecha(malo, "Fecha")


def test_ficha_excel_del_paciente_y_permisos(srv, tmp_path):
    from openpyxl import load_workbook
    from sistema_rural.acceso import ServicioProtegido
    from sistema_rural.usuarios import Usuario
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC, "Jr. Lima 1", "999888777")
    srv.agendar_cita("12345678", "CMP-1001", MAÑANA, "09:00")
    srv.crear_usuario("secre", "Secretaria", "Prueba", "ADMISION", "Clave#12345", debe_cambiar_clave=False)
    srv.crear_usuario("doctor1", "Doctor", "Prueba", "MEDICO", "Clave#12345", "CMP-1001", debe_cambiar_clave=False)
    sec = ServicioProtegido(srv, srv.autenticar("secre", "Clave#12345"))
    wb = load_workbook(sec.exportar_ficha_paciente("DNI", "12345678", tmp_path / "f.xlsx"))
    assert wb.sheetnames == ["Paciente", "Citas"]
    celdas = [c.value for fila in wb["Paciente"].iter_rows() for c in fila]
    assert "12345678" not in celdas and "999888777" in celdas
    doc = ServicioProtegido(srv, srv.autenticar("doctor1", "Clave#12345"))
    assert "Historia clínica" in load_workbook(doc.exportar_ficha_paciente("DNI", "12345678", tmp_path / "g.xlsx")).sheetnames


# ---------------------------------------------------------------- estado según la hora
def test_cita_pasada_se_muestra_vencida_pero_no_cambia_sola(srv):
    from datetime import datetime, timedelta as td
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    c = srv.agendar_cita("12345678", "CMP-1001", MAÑANA, "09:00")
    assert c.estado_visible() == "RESERVADO"
    despues = datetime.combine(MAÑANA, datetime.min.time()) + td(hours=9, minutes=31)
    assert c.estado_visible(despues) == "VENCIDA (sin atender)"
    assert c.get_estado() == "RESERVADO"                      # el estado real lo cambia una persona


def test_no_asistio_solo_cuando_llego_la_hora(srv):
    from datetime import datetime, timedelta as td
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    c = srv.agendar_cita("12345678", "CMP-1001", MAÑANA, "09:00")
    with pytest.raises(ErrorValidacion):
        srv.cambiar_estado_cita(c.get_id(), "NO_ASISTIO")
    despues = datetime.combine(MAÑANA, datetime.min.time()) + td(hours=9, minutes=40)
    srv.cambiar_estado_cita(c.get_id(), "NO_ASISTIO", despues)
    assert c.get_estado() == "NO_ASISTIO"
    with pytest.raises(ErrorValidacion):
        srv.cambiar_estado_cita(c.get_id(), "INVENTADO", despues)
