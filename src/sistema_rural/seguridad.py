"""Protección de datos personales (RD-02, Ley N.° 29733).

- Los datos sensibles se cifran con Fernet (AES-128-CBC + HMAC-SHA256).
- El DNI además se guarda como hash HMAC-SHA256, para detectar duplicados
  y buscar sin descifrar ni exponer el número (DM-05).
- El DNI se muestra siempre enmascarado (DM-01).
"""
import hashlib
import hmac
import os
import re
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from .errores import ErrorValidacion

_PATRON_DNI = re.compile(r"^\d{8}$")
_PATRON_CE = re.compile(r"^[A-Za-z0-9]{9,12}$")


def validar_dni(dni: str) -> str:
    """Devuelve el DNI limpio o lanza ErrorValidacion (8 dígitos exactos)."""
    dni = str(dni).strip()
    if not _PATRON_DNI.fullmatch(dni):
        raise ErrorValidacion("El DNI debe tener exactamente 8 dígitos numéricos.")
    return dni


def validar_documento(tipo: str, numero: str) -> tuple[str, str]:
    """Valida DNI peruano o Carné de Extranjería (9 a 12 caracteres alfanuméricos)."""
    tipo = str(tipo).strip().upper()
    numero = str(numero).strip().upper()
    if tipo == "DNI":
        return tipo, validar_dni(numero)
    if tipo in ("CE", "CARNÉ DE EXTRANJERÍA", "CARNE DE EXTRANJERIA"):
        if not _PATRON_CE.fullmatch(numero):
            raise ErrorValidacion("El Carné de Extranjería debe tener entre 9 y 12 caracteres alfanuméricos.")
        return "CE", numero
    raise ErrorValidacion("Seleccione DNI o Carné de Extranjería.")


def enmascarar_dni(dni: str) -> str:
    """12345678 -> ****5678"""
    return "*" * 4 + dni[-4:]


class Cifrador:
    """Cifra/descifra texto y calcula el hash del DNI con una clave local."""

    def __init__(self, ruta_clave="clave.key"):
        ruta = Path(ruta_clave)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if ruta.exists():
            clave = ruta.read_bytes().strip()
        else:
            clave = Fernet.generate_key()
            ruta.write_bytes(clave)
            try:
                os.chmod(ruta, 0o600)  # solo el dueño puede leerla
            except OSError:
                pass
        self._fernet = Fernet(clave)
        self._sal = hashlib.sha256(b"hash-dni|" + clave).digest()

    def cifrar(self, texto: str) -> str:
        return self._fernet.encrypt(texto.encode("utf-8")).decode("ascii")

    def descifrar(self, token: str) -> str:
        try:
            return self._fernet.decrypt(token.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise ErrorValidacion("No se pudo descifrar: clave incorrecta o dato alterado.") from exc

    def cifrar_bytes(self, datos: bytes) -> bytes:
        return self._fernet.encrypt(datos)

    def descifrar_bytes(self, datos: bytes) -> bytes:
        try:
            return self._fernet.decrypt(datos)
        except InvalidToken as exc:
            raise ErrorValidacion("No se pudo abrir el archivo de datos: clave incorrecta.") from exc

    def hash_dni(self, dni: str) -> str:
        return hmac.new(self._sal, dni.encode("utf-8"), hashlib.sha256).hexdigest()

    def hash_documento(self, tipo: str, numero: str) -> str:
        """Hash separado por tipo para evitar colisiones entre DNI y CE."""
        if tipo == "DNI":
            return self.hash_dni(numero)  # conserva las claves de los pacientes antiguos
        return hmac.new(self._sal, f"{tipo}|{numero}".encode("utf-8"), hashlib.sha256).hexdigest()


_cifrador = None


def configurar(ruta_clave="clave.key") -> Cifrador:
    """Inicializa el cifrador global (lo llama ServicioClinica)."""
    global _cifrador
    _cifrador = Cifrador(ruta_clave)
    return _cifrador


def cifrador() -> Cifrador:
    if _cifrador is None:
        configurar()
    return _cifrador
