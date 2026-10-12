"""Políticas fuera del modelo. Denegación por defecto y confirmación por acción."""
from __future__ import annotations
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from urllib.parse import urlparse
from victor.errors import VictorError, check_cancel


class Risk(IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2


@dataclass
class Approval:
    title: str
    details: str
    risk: Risk
    done: threading.Event = field(default_factory=threading.Event)
    accepted: bool = False
    origin: dict | None = None


class SecurityManager:
    """El diálogo decide; ni mensajes, ni web, ni respuestas de IA conceden permisos."""
    BLOCKED_COMMANDS = {"cmd", "powershell", "pwsh", "wscript", "cscript", "mshta", "rundll32",
                        "reg", "regedit", "diskpart", "format", "del", "erase", "rd", "rmdir",
                        "shutdown", "bcdedit", "schtasks", "sc", "net", "msiexec", "winget", "certutil"}

    def __init__(self, config, emit):
        self.config, self.emit = config, emit
        self.log = logging.getLogger("victor.security")
        self.context = threading.local()

    def set_origin(self, origin):
        self.context.origin = origin

    def origin(self):
        return getattr(self.context, "origin", None)

    def confirm(self, title, details, risk, cancel):
        check_cancel(cancel)
        self.validate_origin()
        origin = self.origin()
        if origin:
            if self.config.get("remote_block_all"):
                raise VictorError("El control remoto está bloqueado desde el PC.")
            if origin.get("source") == "telegram" and risk == Risk.HIGH and self.config.get("remote_high_policy") == "block":
                raise VictorError("Acción de alto riesgo bloqueada por remoto. Ejecútala en el PC o habilita confirmación presencial en Ajustes.")
        if risk == Risk.LOW and self.config.get("security") != "strict":
            return
        # v6, decisión explícita del propietario: la sesión QR autoriza la
        # escritura LAN ordinaria (MEDIO). Capability creada por el servidor,
        # validada en local_authorizer en cada evento. No aplica a herramientas
        # locales/Telegram, al ratón, ni a ningún atajo clasificado ALTO.
        if (title == 'remote_keyboard_input' and risk == Risk.MEDIUM and origin
                and origin.get('source') == 'local_web' and origin.get('keyboard_channel')):
            self.log.info('confirmation result action=remote_keyboard_input accepted=True authorization=paired_keyboard risk=MEDIUM')
            return
        request = Approval(title, details, risk)
        request.origin = origin
        self.log.info("confirmation requested action=%s risk=%s", title, risk.name)
        self.emit("remote_approval" if origin and origin.get("source") == "telegram" and risk != Risk.HIGH else "approval", request)
        deadline = time.monotonic()+120
        try:
            while not request.done.wait(0.1):
                check_cancel(cancel)
                if time.monotonic() > deadline:
                    request.done.set()
                    raise VictorError("La confirmación caducó. No se ejecutó la acción.")
            check_cancel(cancel)
            self.validate_origin()
            if not request.accepted:
                raise VictorError("Acción cancelada por el usuario.")
        finally:
            self.log.info("confirmation result action=%s accepted=%s cancelled=%s", title, request.accepted, cancel.is_set())

    def validate_origin(self):
        origin = self.origin()
        if origin and not self.origin_authorized(origin):
            raise VictorError("Acceso remoto revocado, pausado o bloqueado desde el PC.")

    def origin_authorized(self, origin):
        if self.config.get("remote_block_all"):
            return False
        if origin.get("source") == "local_web":
            return bool(getattr(self, "local_authorizer", lambda _: False)(origin))
        return (origin.get("source") == "telegram" and origin.get("user_id") in self.config.get("telegram_allowed_ids")
                and not self.config.get("telegram_paused") and self.config.get("telegram_enabled"))

    @staticmethod
    def url(value):
        parsed = urlparse(value)
        if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or any(ord(c) < 32 for c in value):
            raise VictorError("Solo se permiten enlaces HTTP/HTTPS sin credenciales.")
        return value

    def path(self, raw, must_exist=False, allow_root=False):
        if not isinstance(raw, str) or not raw.strip() or "\x00" in raw:
            raise VictorError("Ruta de archivo no válida.")
        # Bloquea UNC, dispositivos y flujos alternativos NTFS.
        expanded = os.path.expandvars(raw)
        if expanded.startswith(("\\\\", "//")) or ":" in expanded[2:]:
            raise VictorError("No se permiten rutas de red, dispositivos ni flujos NTFS.")
        roots = [Path(p).resolve() for p in self.config.get("allowed_folders")]
        path = Path(expanded).expanduser()
        if not path.is_absolute():
            path = roots[0] / path
        # Rechaza enlaces/junctions incluso dentro de las raíces autorizadas.
        for parent in (path, *path.parents):
            if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
                raise VictorError("No se opera sobre enlaces simbólicos ni junctions.")
        path = path.resolve()
        protected = [Path(os.environ.get("WINDIR", "C:/Windows")),
                     Path(os.environ.get("PROGRAMFILES", "C:/Program Files")),
                     Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")),
                     Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")), self.config.data_dir,
                     self.config.root / "victor", self.config.root / ".venv"]
        if path.name.lower() in (".env", ".env.example", "config.json", "main.py", "instalar.bat", "iniciar.bat"):
            raise VictorError("Archivo de configuración o programa protegido.")
        for blocked in protected:
            blocked = blocked.resolve()
            if path == blocked or blocked in path.parents or path in blocked.parents:
                raise VictorError("Ruta protegida. Elige una carpeta de trabajo.")
        if not any(path == root or root in path.parents for root in roots):
            raise VictorError("La ruta está fuera de las carpetas autorizadas. Añádela en Configuración si corresponde.")
        if not allow_root and path in roots:
            raise VictorError("No se puede modificar una carpeta raíz autorizada.")
        if must_exist and not path.exists():
            raise VictorError("El archivo o carpeta no existe.")
        return path

    def executable(self, path):
        p = Path(path)
        if p.stem.lower() in self.BLOCKED_COMMANDS:
            raise VictorError("Esta aplicación es un intérprete o herramienta administrativa bloqueada.")
        if p.suffix.lower() != ".exe" or not p.is_absolute() or not p.is_file():
            raise VictorError("La aplicación debe apuntar a un archivo .exe existente.")
        return str(p)
