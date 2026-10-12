"""Claves personales protegidas para el usuario de Windows; nunca en config.json."""
import json
import os
import threading
from victor.errors import VictorError


class CredentialStore:
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()

    @staticmethod
    def crypt(data, decrypt=False):
        from victor.integrations.spotify import EncryptedCache
        try:
            return EncryptedCache.crypt(data, decrypt)
        except Exception:
            raise VictorError("No se pudo acceder al almacén cifrado de claves de Windows.") from None

    def _read(self):
        if not self.path.exists():
            return {}
        try:
            values = json.loads(self.crypt(self.path.read_bytes(), True))
            if not isinstance(values, dict) or any(not isinstance(v, str) for v in values.values()):
                raise ValueError()
            return values
        except (OSError, ValueError, VictorError):
            raise VictorError("No pude leer las claves personales cifradas. No se ha modificado el archivo.") from None

    def get(self, provider):
        with self.lock:
            return self._read().get(provider, "")

    def update(self, values):
        from victor.config import KEYS
        if any(p not in KEYS or (v is not None and (not isinstance(v, str) or not v.strip()
                or len(v) > 4096 or any(c.isspace() for c in v.strip()))) for p, v in values.items()):
            raise VictorError("Introduce una clave sin espacios ni saltos de línea.")
        with self.lock:
            stored = self._read()
            for provider, value in values.items():
                if value is None:
                    stored.pop(provider, None)
                else:
                    stored[provider] = value.strip()
            encrypted = self.crypt(json.dumps(stored).encode("utf-8"))
            temporary = self.path.with_suffix(".tmp")
            try:
                temporary.write_bytes(encrypted)
                os.replace(temporary, self.path)
            except OSError:
                raise VictorError("No pude guardar las claves cifradas.") from None
            finally:
                temporary.unlink(missing_ok=True)
