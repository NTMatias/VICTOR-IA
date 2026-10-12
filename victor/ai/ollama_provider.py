import json
import requests
import time
from victor.ai.base import BaseProvider, Reply, ToolCall, openai_messages
from victor.errors import VictorError, check_cancel


class OllamaProvider(BaseProvider):
    name = "Ollama"

    def __init__(self):
        self.tags_cache = ("", 0, [])

    def ensure_model(self, cfg):
        model = "qwen2.5:3b" if cfg["ollama_light"] else cfg["models"][self.name]
        base = cfg["ollama_url"].rstrip("/")
        if self.tags_cache[0] != base or time.monotonic() - self.tags_cache[1] > 30:
            try:
                with requests.get(base + "/api/tags", timeout=(3, 10)) as response:
                    response.raise_for_status()
                    names = [row["name"] for row in response.json().get("models", [])]
                self.tags_cache = (base, time.monotonic(), names)
            except (requests.RequestException, ValueError, KeyError):
                raise VictorError("No pude consultar Ollama. Inicia Ollama y revisa su dirección local.") from None
        if model not in self.tags_cache[2] and model + ":latest" not in self.tags_cache[2]:
            raise VictorError(f"El modelo {model} no está descargado. Ejecuta: ollama pull {model}")
        return model

    def stream(self, messages, system, specs, cfg, emit, cancel, image=None):
        body = {"model": self.ensure_model(cfg), "messages": openai_messages(messages, system), "stream": True,
                "keep_alive": cfg["ollama_keep_alive"],
                "options": {"temperature": cfg["temperature"], "num_predict": cfg["max_tokens"], "num_ctx": cfg["ollama_context"]}}
        if cfg["ollama_gpu"] == "cpu":
            body["options"]["num_gpu"] = 0
        for m in body["messages"]:
            for call in m.get("tool_calls", []):
                # Copia para no mutar la conversación compartida.
                m["tool_calls"] = [{"function": {"name": c["function"]["name"], "arguments": json.loads(c["function"]["arguments"])}} for c in m["tool_calls"]]
                break
        if image:
            body["messages"].append({"role": "user", "content": "Analiza la captura.", "images": [image]})
        # JSON propio permite usar modelos locales sin soporte nativo de tools.
        if specs:
            catalog = [{"tool": s["name"], "args": {k: {a: v for a, v in p.items() if a in ("type", "enum")}
                        for k, p in s["parameters"]["properties"].items()}} for s in specs]
            body["messages"][0]["content"] = body["messages"][0]["content"][:5000]
            body["messages"][0]["content"] += '\nSi necesitas una herramienta, responde SOLO {"tool":"nombre","args":{...}}. Incluye todos sus argumentos. Catálogo: ' + json.dumps(catalog, ensure_ascii=False)
        # Ventana conservadora para CPU: prioriza el mensaje más reciente; SQLite conserva todo.
        allowance = max(2000, cfg["ollama_context"] * 3 - len(body["messages"][0]["content"]) - min(cfg["max_tokens"], 2048) * 2)
        recent = []
        for message in reversed(body["messages"][1:]):
            message = dict(message)
            content = message.get("content") or ""
            if len(content) > allowance:
                if recent:
                    break
                message["content"] = content[-allowance:]
            recent.append(message)
            allowance -= len(message.get("content") or "")
            if allowance <= 0:
                break
        body["messages"] = body["messages"][:1] + list(reversed(recent))
        reply = Reply()
        with requests.post(cfg["ollama_url"].rstrip("/") + "/api/chat", json=body, timeout=(5, cfg["ollama_timeout"]), stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                check_cancel(cancel)
                if not line:
                    continue
                data = json.loads(line)
                if data.get("error"):
                    raise VictorError("Ollama no pudo generar una respuesta. Revisa el modelo instalado.")
                text = data.get("message", {}).get("content", "")
                reply.text += text
                if text:
                    emit(text)
        return reply
