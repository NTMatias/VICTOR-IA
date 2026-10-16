"""Gestión de autenticación y seguridad de acceso local para VICTOR.IA."""
from __future__ import annotations
import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
import time
from pathlib import Path

def create_auth(data_dir):
    from .deployment import deployment
    settings=deployment(Path(data_dir).parent).get('cloud',{})
    if settings.get('enabled'):
        from .cloud_auth import CloudAuth
        return CloudAuth(data_dir,settings)
    return AuthManager(data_dir)


class AuthManager:
    """Administrador de credenciales de acceso local con hashing PBKDF2-HMAC-SHA256."""

    ITERATIONS = 600_000

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.auth_file = self.data_dir / "auth.json"
        self.session_file = self.data_dir / "auth_session.json"
        self.lock = threading.RLock()
        self.authenticated = False
        self.failed_attempts=0;self.retry_after=0.
        self.log = logging.getLogger("victor.auth")

    def is_configured(self) -> bool:
        """Determina si ya existe una contraseña/PIN configurado."""
        with self.lock:
            if not self.auth_file.exists():
                return False
            # A damaged profile must require recovery, never allow a new password over it.
            return True

    def setup(self, password: str, hint: str = "", username: str = "Usuario") -> bool:
        """Configura la contraseña inicial de acceso."""
        if not password or not 8<=len(password)<=256:
            raise ValueError("La contraseña debe tener entre 8 y 256 caracteres.")
        if not username.strip() or len(username.strip())>64:raise ValueError('Escribe un nombre de usuario de hasta 64 caracteres.')
        with self.lock:
            if self.auth_file.exists() and not self.authenticated:raise ValueError('Verifica la contraseña actual antes de cambiar el acceso.')
            salt = secrets.token_bytes(32)
            pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self.ITERATIONS)
            payload = {
                "hash": pwd_hash.hex(),
                "username": username.strip(),"iterations":self.ITERATIONS,
                "salt": salt.hex(),
                "hint": hint.strip(),
                "created_at": time.time(),
                "updated_at": time.time(),
            }
            temp_file = self.auth_file.with_suffix(".tmp")
            try:
                temp_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                os.replace(temp_file, self.auth_file)
                self.authenticated = True
                self.clear_saved_session()
                self.log.info("Acceso local configurado correctamente.")
                return True
            finally:
                if temp_file.exists():
                    temp_file.unlink(missing_ok=True)

    def verify(self, password: str) -> bool:
        """Verifica la contraseña ingresada."""
        with self.lock:
            if time.monotonic()<self.retry_after:return False
            if not self.is_configured():
                return False
            try:
                data = json.loads(self.auth_file.read_text(encoding="utf-8"))
                stored_hash = bytes.fromhex(data["hash"])
                salt = bytes.fromhex(data["salt"])
                iterations=data.get('iterations',200_000)
                if type(iterations) is not int or not 200_000<=iterations<=1_000_000 or len(salt)!=32 or len(stored_hash)!=32 or len(password)>256:raise ValueError()
                computed_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
                if hmac.compare_digest(stored_hash, computed_hash):
                    self.authenticated = True
                    self.failed_attempts=0;self.retry_after=0.
                    return True
                self.failed_attempts+=1
                if self.failed_attempts>=5:self.retry_after=time.monotonic()+30
                return False
            except Exception as exc:
                self.log.error("No se pudo verificar el perfil local: %s",type(exc).__name__)
                return False

    def change_password(self, current_password: str, new_password: str, new_hint: str | None = None) -> bool:
        """Cambia la contraseña validando previamente la actual."""
        if not self.verify(current_password):
            return False
        hint = self.get_hint() if new_hint is None else new_hint
        return self.setup(new_password, hint=hint,username=self.username())

    def username(self):
        try:return str(json.loads(self.auth_file.read_text(encoding='utf-8')).get('username','Usuario'))
        except (OSError,ValueError):return 'Usuario'

    def get_hint(self) -> str:
        """Devuelve la pista de recuperación de contraseña si existe."""
        with self.lock:
            if not self.auth_file.exists():
                return ""
            try:
                data = json.loads(self.auth_file.read_text(encoding="utf-8"))
                return str(data.get("hint", ""))
            except Exception:
                return ""

    def save_session(self, remember_days: int = 14) -> str:
        """Genera un token de sesión recordada en este equipo."""
        if not self.authenticated:raise ValueError('Inicia sesión antes de recordarla.')
        token = secrets.token_hex(32)
        expiry = time.time() + (remember_days * 86400)
        from victor.credentials import CredentialStore
        data = {"token": token, "expiry": expiry,"profile_sha256":hashlib.sha256(self.auth_file.read_bytes()).hexdigest()}
        try:
            temporary=self.session_file.with_suffix('.tmp');temporary.write_bytes(CredentialStore.crypt(json.dumps(data).encode('utf-8')));os.replace(temporary,self.session_file)
            return token
        except Exception:
            return ""

    def check_saved_session(self) -> bool:
        """Comprueba si existe una sesión recordada válida."""
        with self.lock:
            if not self.is_configured():
                return False
            if not self.session_file.exists():
                return False
            try:
                from victor.credentials import CredentialStore
                data = json.loads(CredentialStore.crypt(self.session_file.read_bytes(),True))
                fingerprint=hashlib.sha256(self.auth_file.read_bytes()).hexdigest()
                if len(data.get('token',''))==64 and hmac.compare_digest(data.get('profile_sha256',''),fingerprint) and time.time() < data.get("expiry", 0):
                    self.authenticated = True
                    return True
                self.session_file.unlink(missing_ok=True)
                return False
            except Exception:
                return False

    def clear_saved_session(self):
        """Elimina el token de sesión guardado."""
        with self.lock:
            try:
                self.session_file.unlink(missing_ok=True)
            except Exception:
                pass

    def logout(self):
        """Cierra la sesión activa."""
        with self.lock:
            self.authenticated = False
            self.clear_saved_session()

    def lock_session(self):
        """Bloquea la sesión sin borrar la sesión guardada."""
        with self.lock:
            self.authenticated = False
            self.clear_saved_session()
