import json
import requests
from victor.ai.base import BaseProvider, Reply, ToolCall, openai_messages
from victor.errors import VictorError, check_cancel


class OllamaProvider(BaseProvider):
    name = "Ollama"

    def stream(self, messages, system, specs, cfg, emit, cancel, image=None):
        body = {"model": cfg["models"][self.name], "messages": openai_messages(messages, system), "stream": True,
                "options": {"temperature": cfg["temperature"], "num_predict": cfg["max_tokens"], "num_ctx": 16384}}
        for m in body["messages"]:
            for call in m.get("tool_calls", []):
                # Copia para no mutar la conversación compartida.
                m["tool_calls"] = [{"function": {"name": c["function"]["name"], "arguments": json.loads(c["function"]["arguments"])}} for c in m["tool_calls"]]
                break
        if image:
            body["messages"].append({"role": "user", "content": "Analiza la captura.", "images": [image]})
        # JSON propio permite usar modelos locales sin soporte nativo de tools.
        if specs:
            body["messages"][0]["content"] += '\nSi necesitas una herramienta, responde SOLO {"tool":"nombre","args":{...}}. Catálogo: ' + json.dumps(specs, ensure_ascii=False)
        reply = Reply()
        with requests.post(cfg["ollama_url"].rstrip("/") + "/api/chat", json=body, timeout=(5, cfg["network_timeout"]), stream=True) as response:
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
