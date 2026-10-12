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


def http_status(exc):
    """Normaliza el código HTTP: google-genai usa .code, otros SDK .status_code."""
    for value in (getattr(exc, "status_code", None), getattr(exc, "code", None),
                  getattr(getattr(exc, "response", None), "status_code", None)):
        if isinstance(value, int) and not isinstance(value, bool) and 100 <= value <= 599:
            return value
    return None


class AIManager:
    def __init__(self, config, emit):
        self.config, self.emit = config, emit
        self.providers = {p.name: p for p in (OpenAIProvider(), AnthropicProvider(), GeminiProvider(), OllamaProvider())}
        self.log = logging.getLogger("victor.ai")
        self.accounts = {}
        self.account_providers = {}
        if hasattr(config,'data_dir'):
            from victor.ai.chatgpt_account import ChatGPTAccount, ChatGPTProvider
            self.accounts={'OpenAI':ChatGPTAccount(config)}
            self.account_providers={'OpenAI':ChatGPTProvider(self.accounts['OpenAI'])}

    def generate(self, messages, system, specs, cancel, image=None, vision=False, on_token=None):
        cfg = self.config.snapshot()
        primary = cfg["vision_provider"] if vision else cfg["provider"]
        order = [primary] if vision else list(dict.fromkeys([primary] + cfg["fallback"]))
        methods=cfg.get('auth_methods',{})
        # A plan/account request never silently switches to billable API inference.
        if primary=='OpenAI' and methods.get(primary)=='account':order=[primary]
        errors = []
        if vision:
            if not cfg["vision_model"].strip():
                raise VictorError("Configura un modelo compatible con visión en Configuración.")
            cfg["models"][primary] = cfg["vision_model"]
        for name in order:
            check_cancel(cancel)
            start = time.monotonic()
            try:
                request_cfg = dict(cfg)
                request_cfg['_retry_notice'] = lambda message: self.emit('connection', message)
                account_mode=name=='OpenAI' and methods.get(name)=='account'
                if name in KEYS and not account_mode:
                    key = self.config.api_key(name) if hasattr(self.config, "api_key") else os.environ.get(KEYS[name], "").strip()
                    if not key:
                        errors.append(f"{name}: falta {KEYS[name]}. Añade tu clave en Ajustes → Inteligencia artificial → Claves API personales.")
                        continue
                    request_cfg["_api_key"] = key
                mode_label='ChatGPT · cuenta' if account_mode else name
                self.emit("connection", f"Conectando con {mode_label}…")
                provider=self.account_providers[name] if account_mode else self.providers[name]
                reply = provider.stream(messages, system, specs, request_cfg,
                              on_token or (lambda t: self.emit("token", t)), cancel, image)
                check_cancel(cancel)
                self.log.info("provider=%s success seconds=%.2f", name, time.monotonic()-start)
                self.emit("connection", f"Conectado · {mode_label}")
                if name != primary:
                    self.emit("notice", f"Se usó {name} como respaldo. " + " | ".join(errors))
                return json_fallback(reply)
            except Cancelled:
                raise
            except Exception as exc:
                # No registrar cuerpos HTTP ni claves. Tipo/código son suficientes para diagnosticar.
                status = http_status(exc)
                self.log.warning("provider=%s error=%s status=%s seconds=%.2f", name, type(exc).__name__, status, time.monotonic()-start)
                if account_mode and isinstance(exc,VictorError):
                    message=str(exc)
                elif isinstance(exc, ImportError):
                    message = "SDK no instalado; vuelve a ejecutar instalar.bat."
                elif status in (401, 403):
                    message = "clave inválida o sin permisos; revisa tu clave en Ajustes → Inteligencia artificial."
                elif status == 429:
                    message = "límite de uso o saldo agotado."
                elif status == 404:
                    message = (f"el modelo {cfg['models'][name]!r} no existe o no está disponible para tu cuenta. "
                               f"Cambia el modelo en Ajustes → Inteligencia artificial → {name} y guarda los cambios.")
                elif status == 400:
                    message = "modelo o parámetros no compatibles; revisa el nombre del modelo."
                elif status == 503:
                    message = "servicio temporalmente saturado; inténtalo de nuevo más tarde o configura otro proveedor de respaldo."
                elif status in (500, 502, 504):
                    message = "el servicio está fallando temporalmente; inténtalo de nuevo más tarde."
                elif isinstance(exc, VictorError):
                    message = str(exc)
                else:
                    message = "no se pudo conectar o completar la respuesta; revisa la red y el servicio."
                errors.append(f"{name}: {message}")
                self.emit("stream_reset", None)
        self.emit("connection", "Sin conexión a IA")
        raise VictorError("\n".join(errors))
