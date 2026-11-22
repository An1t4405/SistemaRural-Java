"""Pruebas de login, roles/permisos y validación de fechas."""
from datetime import date, datetime, timedelta

import pytest

from sistema_rural import fechas, usuarios
from sistema_rural.acceso import PERMISO_POR_OPERACION, ServicioProtegido
from sistema_rural.errores import (CredencialesInvalidas, CuentaBloqueada, ErrorValidacion, NoEncontrado,
                                   PermisoDenegado)
from sistema_rural.servicio import ServicioClinica
from sistema_rural.usuarios import MAX_INTENTOS, ROLES, Permiso

NAC = date(1990, 5, 17)
MAÑANA = date.today() + timedelta(days=1)
if MAÑANA.weekday() == 6:                       # la posta no atiende domingos
    MAÑANA += timedelta(days=1)
CLAVE = "Posta2026"


@pytest.fixture(autouse=True)
def hash_rapido(monkeypatch):
    monkeypatch.setattr(usuarios, "ITERACIONES", 1000)   # solo para que las pruebas sean veloces


@pytest.fixture
def srv(tmp_path):
    s = ServicioClinica(tmp_path / "datos.enc", tmp_path / "clave.key", cupos_por_turno=3)
    s.registrar_medico("40000001", "Rosa", "Quispe", "CMP-1001", "Medicina General")
    s.crear_primer_administrador("admin", "Ana", "Admin", "Clave2026")
    return s


def entrar(srv, nombre, rol, colegiatura=""):
    srv.crear_usuario(nombre, "Nombre", "Apellido", rol, CLAVE, colegiatura, debe_cambiar_clave=False)
    return ServicioProtegido(srv, srv.autenticar(nombre, CLAVE))


# ---------------------------------------------------------------- login
def test_primer_administrador_solo_una_vez(tmp_path):
    s = ServicioClinica(tmp_path / "d.enc", tmp_path / "k.key")
    assert not s.hay_usuarios()
    s.crear_primer_administrador("admin", "Ana", "Admin", "Clave2026")
    assert s.hay_usuarios()
    with pytest.raises(ErrorValidacion):
        s.crear_primer_administrador("otro", "Luis", "Perez", "Clave2026")


def test_login_correcto_e_incorrecto(srv):
    assert srv.autenticar("ADMIN", "Clave2026").get_rol().codigo == "ADMIN"   # usuario sin distinguir mayúsculas
    with pytest.raises(CredencialesInvalidas):
        srv.autenticar("admin", "otraClave1")
    with pytest.raises(CredencialesInvalidas):
        srv.autenticar("noexiste", "Clave2026")


def test_la_contrasena_no_se_guarda_en_claro(srv, tmp_path):
    u = srv.listar_usuarios()[0]
    assert "Clave2026" not in str(vars(u))
    assert u.to_dict()["clave_hash"].startswith("pbkdf2_sha256$")
    otro = ServicioClinica(tmp_path / "datos.enc", tmp_path / "clave.key")   # persistencia ida y vuelta
    assert otro.autenticar("admin", "Clave2026").nombre_completo() == "Admin, Ana"


def test_bloqueo_tras_varios_intentos_y_desbloqueo_por_tiempo(srv):
    t0 = datetime(2026, 11, 17, 10, 0)
    for _ in range(MAX_INTENTOS - 1):
        with pytest.raises(CredencialesInvalidas):
            srv.autenticar("admin", "mala1234", t0)
    with pytest.raises(CuentaBloqueada):
        srv.autenticar("admin", "mala1234", t0)
    with pytest.raises(CuentaBloqueada):                       # aun con la clave correcta
        srv.autenticar("admin", "Clave2026", t0 + timedelta(minutes=1))
    assert srv.autenticar("admin", "Clave2026", t0 + timedelta(minutes=usuarios.MINUTOS_BLOQUEO + 1))


def test_usuario_desactivado_no_entra(srv):
    srv.crear_usuario("admision1", "Eva", "Rios", "ADMISION", CLAVE)
    srv.cambiar_estado_usuario("admision1", False)
    with pytest.raises(CredencialesInvalidas):
        srv.autenticar("admision1", CLAVE)


def test_cambio_de_clave_obligatorio_para_usuarios_nuevos(srv):
    u = srv.crear_usuario("admision1", "Eva", "Rios", "ADMISION", "Temporal2026")
    assert u.debe_cambiar_clave()
    with pytest.raises(CredencialesInvalidas):
        srv.cambiar_clave("admision1", "equivocada1", "Nueva2026x")
    srv.cambiar_clave("admision1", "Temporal2026", "Nueva2026x")
    assert not srv.autenticar("admision1", "Nueva2026x").debe_cambiar_clave()


@pytest.mark.parametrize("mala", ["corta1", "sololetras", "12345678", "", "x" * 129])
def test_politica_de_contrasenas(srv, mala):
    with pytest.raises(ErrorValidacion):
        srv.crear_usuario("usuario1", "Eva", "Rios", "ADMISION", mala)


@pytest.mark.parametrize("malo", ["ab", "con espacio", "tilde_ñ", "x" * 21, ""])
def test_nombre_de_usuario_invalido(srv, malo):
    with pytest.raises(ErrorValidacion):
        srv.crear_usuario(malo, "Eva", "Rios", "ADMISION", CLAVE)


def test_no_se_puede_dejar_el_sistema_sin_administrador(srv):
    with pytest.raises(ErrorValidacion):
        srv.cambiar_estado_usuario("admin", False)
    with pytest.raises(ErrorValidacion):
        srv.cambiar_rol_usuario("admin", "MEDICO")


# ---------------------------------------------------------------- roles y permisos
def test_admision_registra_pacientes_pero_no_ve_historias(srv):
    adm = entrar(srv, "admision1", "ADMISION")
    adm.registrar_paciente("12345678", "Ana", "Torres", NAC)
    assert len(adm.listar_pacientes()) == 1
    with pytest.raises(PermisoDenegado):
        adm.obtener_historia("12345678")
    with pytest.raises(PermisoDenegado):
        adm.registrar_medico("40000009", "X", "Y", "CMP-9", "Z")


def test_tecnica_de_enfermeria_solo_consulta_y_actualiza_turnos(srv):
    adm = entrar(srv, "admision1", "ADMISION")
    adm.registrar_paciente("12345678", "Ana", "Torres", NAC)
    tec = entrar(srv, "tecnica1", "TEC_ENFERMERIA")
    assert len(tec.listar_pacientes()) == 1
    for operacion in (lambda: tec.registrar_paciente("87654321", "L", "M", NAC),
                      lambda: tec.obtener_historia("12345678"),
                      lambda: tec.agendar_cita("12345678", "CMP-1001", MAÑANA, "MAÑANA"),
                      lambda: tec.generar_reporte("diario")):
        with pytest.raises(PermisoDenegado):
            operacion()
    cita = adm.agendar_cita("12345678", "CMP-1001", MAÑANA, "MAÑANA")
    t = adm.emitir_ticket(cita.get_id())
    tec.cambiar_estado_ticket(MAÑANA, t.get_numero(), "EN_ATENCION")
    assert t.get_estado() == "EN_ATENCION"


def test_medico_registra_atencion_a_su_nombre(srv):
    adm = entrar(srv, "admision1", "ADMISION")
    adm.registrar_paciente("12345678", "Ana", "Torres", NAC)
    med = entrar(srv, "medico1", "MEDICO", "CMP-1001")
    a = med.registrar_atencion("12345678", "Fiebre", "J00")
    assert a.get_cmp_medico() == "CMP-1001"
    assert len(med.obtener_historia("12345678").get_atenciones()) == 1
    assert med.generar_reporte("diario")["total_atenciones"] == 1


def test_profesional_sin_colegiatura_no_registra_atenciones(srv):
    adm = entrar(srv, "admision1", "ADMISION")
    adm.registrar_paciente("12345678", "Ana", "Torres", NAC)
    enf = entrar(srv, "enfermera1", "ENFERMERA")           # sin colegiatura vinculada
    with pytest.raises(PermisoDenegado):
        enf.registrar_atencion("12345678", "Control", "Z00")


def test_colegiatura_debe_existir_en_la_lista_de_profesionales(srv):
    with pytest.raises(NoEncontrado):
        srv.crear_usuario("medico9", "Eva", "Rios", "MEDICO", CLAVE, "CMP-9999")


def test_administrador_gestiona_usuarios_y_datos_basicos_pero_no_ve_historias(srv):
    admin = ServicioProtegido(srv, srv.autenticar("admin", "Clave2026"))
    admin.crear_usuario("admision1", "Eva", "Rios", "ADMISION", CLAVE)
    assert len(admin.listar_usuarios()) == 2
    # El administrador puede apoyar el registro de pacientes en una posta pequeña.
    admin.registrar_paciente("12345678", "Ana", "Torres", NAC)
    assert len(admin.listar_pacientes()) == 1
    with pytest.raises(PermisoDenegado):
        admin.obtener_historia("12345678")
    with pytest.raises(PermisoDenegado):
        admin.cambiar_estado_usuario("admin", False)       # no puede desactivarse a sí mismo


def test_nadie_mas_gestiona_usuarios(srv):
    med = entrar(srv, "medico1", "MEDICO", "CMP-1001")
    with pytest.raises(PermisoDenegado):
        med.crear_usuario("otro1", "A", "B", "ADMIN", CLAVE)
    with pytest.raises(PermisoDenegado):
        med.cambiar_rol_usuario("medico1", "ADMIN")


def test_operaciones_no_listadas_quedan_denegadas(srv):
    admin = ServicioProtegido(srv, srv.autenticar("admin", "Clave2026"))
    for nombre in ("guardar", "cargar", "autenticar", "cambiar_clave", "crear_primer_administrador"):
        with pytest.raises(PermisoDenegado):
            getattr(admin, nombre)


def test_sesion_de_usuario_desactivado_deja_de_funcionar(srv):
    adm = entrar(srv, "admision1", "ADMISION")
    srv.cambiar_estado_usuario("admision1", False)
    with pytest.raises(PermisoDenegado):
        adm.listar_pacientes()


def test_cambio_de_rol_aplica_de_inmediato(srv):
    adm = entrar(srv, "admision1", "ADMISION")
    srv.cambiar_rol_usuario("admision1", "TEC_LABORATORIO")
    with pytest.raises(PermisoDenegado):
        adm.registrar_paciente("12345678", "Ana", "Torres", NAC)


def test_matriz_de_roles_es_coherente():
    permisos_historia = {Permiso.HISTORIA_VER, Permiso.HISTORIA_EDITAR, Permiso.ATENCION_REGISTRAR}
    for codigo in ("ADMIN", "JEFE", "ADMISION", "ESTADISTICA", "TEC_ENFERMERIA", "TEC_LABORATORIO", "TEC_FARMACIA"):
        assert not (ROLES[codigo].permisos & permisos_historia), codigo   # mínimo privilegio
    assert Permiso.USUARIOS_GESTIONAR in ROLES["ADMIN"].permisos
    assert Permiso.PACIENTES_REGISTRAR in ROLES["ADMIN"].permisos
    assert Permiso.PACIENTES_EDITAR in ROLES["ADMIN"].permisos
    assert all(Permiso.USUARIOS_GESTIONAR not in r.permisos for c, r in ROLES.items() if c != "ADMIN")
    assert {r.grupo for r in ROLES.values()} == {"Administrativo", "Asistencial"}
    assert set(PERMISO_POR_OPERACION.values()) <= set(Permiso)


# ---------------------------------------------------------------- fechas
@pytest.mark.parametrize("texto,esperado", [("17/05/1990", date(1990, 5, 17)), ("1990-05-17", date(1990, 5, 17)),
                                            ("7/5/1990", date(1990, 5, 7)), (" 17-05-1990 ", date(1990, 5, 17))])
def test_formatos_de_fecha_aceptados(texto, esperado):
    assert fechas.parsear_fecha(texto) == esperado


@pytest.mark.parametrize("malo", ["", "17/05/90", "hoy", "1990/05/17", "17.05.1990", "31/02/2024", "00/10/2026", "15/13/2026"])
def test_fechas_invalidas_o_inexistentes(malo):
    with pytest.raises(ErrorValidacion):
        fechas.parsear_fecha(malo, "Nacimiento")


def test_nacimiento_futuro_o_inverosimil(srv):
    with pytest.raises(ErrorValidacion):
        srv.registrar_paciente("12345678", "Ana", "Torres", date.today() + timedelta(days=1))
    with pytest.raises(ErrorValidacion):
        srv.registrar_paciente("12345678", "Ana", "Torres", date(1850, 1, 1))
    srv.registrar_paciente("12345678", "Ana", "Torres", date.today())        # nació hoy: válido


def test_citas_solo_dentro_del_horizonte(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    limite = date.today() + timedelta(days=fechas.MAX_DIAS_CITA)
    if limite.weekday() == 6:                      # el último día permitido no puede ser domingo
        limite -= timedelta(days=1)
    srv.agendar_cita("12345678", "CMP-1001", limite, "TARDE")
    with pytest.raises(ErrorValidacion):
        srv.agendar_cita("12345678", "CMP-1001", date.today() + timedelta(days=fechas.MAX_DIAS_CITA + 1), "TARDE")
    with pytest.raises(ErrorValidacion):
        srv.agendar_cita("12345678", "CMP-1001", date.today() - timedelta(days=1), "TARDE")


def test_fecha_de_atencion_coherente_con_el_paciente(srv):
    srv.registrar_paciente("12345678", "Ana", "Torres", NAC)
    with pytest.raises(ErrorValidacion):
        srv.registrar_atencion("12345678", "CMP-1001", "Control", "Z00", MAÑANA)           # futura
    with pytest.raises(ErrorValidacion):
        srv.registrar_atencion("12345678", "CMP-1001", "Control", "Z00", date(1980, 1, 1))  # antes de nacer
    srv.registrar_atencion("12345678", "CMP-1001", "Control", "Z00", date.today())


def test_reporte_no_acepta_fecha_futura(srv):
    with pytest.raises(ErrorValidacion):
        srv.generar_reporte("diario", MAÑANA)


def test_administrador_puede_agendar_y_emitir_ticket(srv):
    admin = ServicioProtegido(srv, srv.autenticar("admin", "Clave2026"))
    admin.registrar_paciente("12345678", "Ana", "Torres", NAC)
    cita = admin.agendar_cita("12345678", "CMP-1001", MAÑANA, "08:00")
    ticket = admin.emitir_ticket(cita.get_id())
    assert ticket.get_numero() == 1


# ---------------------------------------------------------------- cobertura del Proxy (mejora R-11)
def test_horas_disponibles_se_consulta_con_permiso_de_citas(srv):
    adm = entrar(srv, "admision1", "ADMISION")
    dia = date.today() + timedelta(days=1)
    while dia.weekday() == 6:                      # la posta no atiende domingos
        dia += timedelta(days=1)
    assert len(adm.horas_disponibles("CMP-1001", dia)) > 0


def test_todo_metodo_publico_del_servicio_tiene_permiso_o_exclusion_expresa():
    """Evita que una operacion nueva quede bloqueada (o abierta) por olvidar su permiso."""
    sin_permiso_a_proposito = {"autenticar", "cambiar_clave", "cargar", "guardar", "crear_primer_administrador",
                               "hay_usuarios", "ruta_datos"}        # previas al login o internas
    publicos = {n for n in dir(ServicioClinica) if not n.startswith("_") and callable(getattr(ServicioClinica, n))}
    propios = {n for n in vars(ServicioProtegido) if not n.startswith("_")}   # el Proxy las trata aparte
    olvidados = publicos - set(PERMISO_POR_OPERACION) - propios - sin_permiso_a_proposito
    assert not olvidados, f"Operaciones sin permiso asignado: {sorted(olvidados)}"
