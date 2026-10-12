"""Configuración atómica; ninguna clave se escribe en config.json."""
from __future__ import annotations
import copy
import json
import os
import threading
from pathlib import Path
from dotenv import load_dotenv
from victor.errors import VictorError

ROOT = Path(__file__).resolve().parent.parent
PROVIDERS = ("OpenAI", "Anthropic", "Gemini", "Ollama")
KEYS = {"OpenAI": "OPENAI_API_KEY", "Anthropic": "ANTHROPIC_API_KEY", "Gemini": "GEMINI_API_KEY"}
DEFAULTS = {
    "provider": "OpenAI",
    "models": {"OpenAI": "gpt-4.1-mini", "Anthropic": "claude-sonnet-4-20250514",
               "Gemini": "gemini-2.5-flash", "Ollama": "qwen2.5:7b"},
    "fallback": [], "temperature": 0.5, "max_tokens": 2048,
    "name": "VICTOR.IA", "personality": "Atento, preciso, práctico y con humor discreto.",
    "formality": "Profesional y cercano", "language": "es-EC",
    "system_prompt": "Responde con concisión salvo que el usuario pida detalle.",
    "theme": "Dark", "security": "normal", "voice_enabled": False,
    "voice_id": "", "voice_rate": 175, "voice_mode": "manual",
    "voice_backend": "whisper", "whisper_model": "base", "wake_word": "VICTOR",
    "microphone": "", "vision_provider": "OpenAI", "vision_model": "gpt-4.1-mini",
    "ollama_url": "http://127.0.0.1:11434", "context_chars": 24000,
    "allowed_folders": [str(ROOT / "workspace")], "applications": {},
    "auto_search": True, "network_timeout": 30,
    "ollama_light": False, "ollama_keep_alive": "5m", "ollama_timeout": 180,
    "ollama_gpu": "auto", "ollama_context": 4096,
    "tts_backend": "edge", "edge_voice": "es-EC-LuisNeural", "conversation_window": 45,
    "telegram_enabled": False, "telegram_allowed_ids": [], "telegram_paused": False,
    "remote_block_all": False, "remote_high_policy": "block", "remote_rate_limit": 6,
    "local_remote_enabled": False,
}


class ConfigManager:
    def __init__(self, root: Path = ROOT):
        self.root = root
        self.data_dir = root / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (root / "workspace").mkdir(exist_ok=True)
        load_dotenv(root / ".env", override=False)
        self.path = self.data_dir / "config.json"
        self.lock = threading.RLock()
        self.data = copy.deepcopy(DEFAULTS)
        self.data["allowed_folders"] = [str(root / "workspace")]
        self.warning = ""
        if self.path.exists():
            try:
                saved = json.loads(self.path.read_text(encoding="utf-8"))
                candidate = copy.deepcopy(self.data)
                candidate.update({k: v for k, v in saved.items() if k in DEFAULTS})
                self.validate(candidate)
                self.data = candidate
            except (ValueError, OSError, TypeError, VictorError):
                self.warning = "La configuración no es válida. Se cargaron valores seguros; el archivo original se conserva."

    def snapshot(self):
        with self.lock:
            return copy.deepcopy(self.data)

    def get(self, key):
        with self.lock:
            return copy.deepcopy(self.data[key])

    @staticmethod
    def validate(d):
        if d["provider"] not in PROVIDERS or d["vision_provider"] not in PROVIDERS:
            raise VictorError("Proveedor no válido.")
        if not isinstance(d["fallback"], list) or any(p not in PROVIDERS for p in d["fallback"]):
            raise VictorError("Fallback: usa nombres OpenAI, Anthropic, Gemini, Ollama separados por comas.")
        if not isinstance(d["models"], dict) or any(not isinstance(d["models"].get(p), str) or not d["models"][p].strip() for p in PROVIDERS):
            raise VictorError("Especifica un modelo para cada proveedor.")
        for k, low, high in (("temperature", 0, 2), ("max_tokens", 128, 16384),
                             ("voice_rate", 80, 350), ("context_chars", 8000, 80000), ("network_timeout", 5, 120)):
            if isinstance(d[k], bool) or not isinstance(d[k], (int, float)) or not low <= d[k] <= high:
                raise VictorError(f"{k} debe estar entre {low} y {high}.")
        for k in ("max_tokens", "voice_rate", "context_chars", "network_timeout"):
            if not isinstance(d[k], int):
                raise VictorError(f"{k} debe ser un entero.")
        for k in ("name", "personality", "formality", "language", "system_prompt", "wake_word", "vision_model", "voice_id", "microphone", "whisper_model"):
            if not isinstance(d[k], str) or len(d[k]) > 12000:
                raise VictorError(f"Valor inválido: {k}.")
        if not d["wake_word"].strip():
            raise VictorError("La palabra de activación no puede estar vacía.")
        choices = {"theme": ("Dark", "Light", "System"), "security": ("normal", "strict"),
                   "voice_mode": ("manual", "push-to-talk", "continua"), "voice_backend": ("google", "whisper")}
        for k, allowed in choices.items():
            if d[k] not in allowed:
                raise VictorError(f"Valor inválido: {k}.")
        for k in ("auto_search", "voice_enabled"):
            if not isinstance(d[k], bool):
                raise VictorError(f"{k} debe ser verdadero o falso.")
        if not isinstance(d["ollama_light"], bool) or d["ollama_gpu"] not in ("auto", "cpu"):
            raise VictorError("Perfil Ollama inválido.")
        if d["tts_backend"] not in ("edge", "sapi") or not isinstance(d["edge_voice"], str):
            raise VictorError("Configuración de salida de voz inválida.")
        for key in ("telegram_enabled", "telegram_paused", "remote_block_all", "local_remote_enabled"):
            if not isinstance(d[key], bool):
                raise VictorError("Configuración remota inválida.")
        if not isinstance(d["telegram_allowed_ids"], list) or any(type(i) is not int or i <= 0 for i in d["telegram_allowed_ids"]):
            raise VictorError("Los IDs de Telegram deben ser enteros positivos en una lista JSON.")
        if d["remote_high_policy"] not in ("block", "pc") or type(d["remote_rate_limit"]) is not int or not 1 <= d["remote_rate_limit"] <= 20:
            raise VictorError("Política o límite remoto inválidos.")
        if not isinstance(d["conversation_window"], int) or not 0 <= d["conversation_window"] <= 180:
            raise VictorError("La ventana de conversación debe estar entre 0 y 180 segundos.")
        if not isinstance(d["ollama_timeout"], int) or not 30 <= d["ollama_timeout"] <= 600:
            raise VictorError("Timeout Ollama: entre 30 y 600 segundos.")
        if not isinstance(d["ollama_context"], int) or not 2048 <= d["ollama_context"] <= 16384:
            raise VictorError("Contexto Ollama: entre 2048 y 16384 tokens.")
        import re
        if not isinstance(d["ollama_keep_alive"], str) or not re.fullmatch(r"\d{1,3}[smh]", d["ollama_keep_alive"]):
            raise VictorError("keep_alive debe ser una duración, por ejemplo 5m.")
        from urllib.parse import urlparse
        url = urlparse(d["ollama_url"])
        if url.scheme != "http" or url.hostname not in ("127.0.0.1", "localhost", "::1") or url.username or url.query:
            raise VictorError("Ollama debe usar una URL HTTP local (localhost o 127.0.0.1).")
        if not isinstance(d["allowed_folders"], list) or not d["allowed_folders"]:
            raise VictorError("Configura al menos una carpeta autorizada.")
        for folder in d["allowed_folders"]:
            if not isinstance(folder, str) or not Path(folder).is_absolute():
                raise VictorError("Las carpetas autorizadas deben tener rutas absolutas.")
        if not isinstance(d["applications"], dict):
            raise VictorError("Aplicaciones debe ser un objeto JSON de alias: ruta.exe.")
        for name, path in d["applications"].items():
            if not name or not isinstance(path, str) or not Path(path).is_absolute() or Path(path).suffix.lower() != ".exe":
                raise VictorError("Cada aplicación necesita un alias y una ruta absoluta a un .exe.")

    def save(self, values):
        with self.lock:
            candidate = copy.deepcopy(self.data)
            candidate.update({k: v for k, v in values.items() if k in DEFAULTS})
            self.validate(candidate)
            temp = self.path.with_suffix(".tmp")
            temp.write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, self.path)
            self.data = candidate

    def credentials_status(self):
        return {p: bool(os.environ.get(k, "").strip()) for p, k in KEYS.items()}
