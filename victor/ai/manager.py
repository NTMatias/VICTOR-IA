import logging
import os
import time
from victor.ai.openai_provider import OpenAIProvider
from victor.ai.anthropic_provider import AnthropicProvider
from victor.ai.gemini_provider import GeminiProvider
from victor.ai.ollama_provider import OllamaProvider
from victor.ai.base import json_fallback
from victor.config import KEYS
from victor.errors import VictorError, Cancelled, check_cancel


class AIManager:
    def __init__(self, config, emit):
        self.config, self.emit = config, emit
        self.providers = {p.name: p for p in (OpenAIProvider(), AnthropicProvider(), GeminiProvider(), OllamaProvider())}
        self.log = logging.getLogger("victor.ai")

    def generate(self, messages, system, specs, cancel, image=None, vision=False, on_token=None):
        cfg = self.config.snapshot()
        primary = cfg["vision_provider"] if vision else cfg["provider"]
        order = [primary] if vision else list(dict.fromkeys([primary] + cfg["fallback"]))
        errors = []
        if vision:
            if not cfg["vision_model"].strip():
                raise VictorError("Configura un modelo compatible con visión en Configuración.")
            cfg["models"][primary] = cfg["vision_model"]
        for name in order:
            check_cancel(cancel)
            if name in KEYS and not os.environ.get(KEYS[name], "").strip():
                errors.append(f"{name}: falta {KEYS[name]}. Copia .env.example a .env, añade tu clave y reinicia.")
                continue
            start = time.monotonic()
            try:
                self.emit("connection", f"Conectando con {name}…")
                reply = self.providers[name].stream(messages, system, specs, cfg,
                              on_token or (lambda t: self.emit("token", t)), cancel, image)
                check_cancel(cancel)
                self.log.info("provider=%s success seconds=%.2f", name, time.monotonic()-start)
                self.emit("connection", f"Conectado · {name}")
                if name != primary:
                    self.emit("notice", f"Se usó {name} como respaldo. " + " | ".join(errors))
                return json_fallback(reply)
            except Cancelled:
                raise
            except Exception as exc:
                # No registrar cuerpos HTTP ni claves. Tipo/código son suficientes para diagnosticar.
                status = getattr(exc, "status_code", None)
                self.log.warning("provider=%s error=%s status=%s seconds=%.2f", name, type(exc).__name__, status, time.monotonic()-start)
                if isinstance(exc, ImportError):
                    message = "SDK no instalado; vuelve a ejecutar instalar.bat."
                elif status in (401, 403):
                    message = "clave inválida o sin permisos; revisa .env."
                elif status == 429:
                    message = "límite de uso o saldo agotado."
                elif status in (400, 404):
                    message = "modelo o parámetros no compatibles; revisa el nombre del modelo."
                elif isinstance(exc, VictorError):
                    message = str(exc)
                else:
                    message = "no se pudo conectar o completar la respuesta; revisa la red y el servicio."
                errors.append(f"{name}: {message}")
                self.emit("stream_reset", None)
        self.emit("connection", "Sin conexión a IA")
        raise VictorError("\n".join(errors))
