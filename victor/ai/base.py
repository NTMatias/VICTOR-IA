from dataclasses import dataclass, field
import json
import uuid
from victor.errors import VictorError


@dataclass
class ToolCall:
    name: str
    args: dict
    id: str = field(default_factory=lambda: uuid.uuid4().hex)


@dataclass
class Reply:
    text: str = ""
    calls: list[ToolCall] = field(default_factory=list)


def parse_args(value):
    if isinstance(value, dict):
        return value
    try:
        result = json.loads(value)
        if not isinstance(result, dict):
            raise ValueError()
        return result
    except (ValueError, TypeError):
        raise VictorError("El modelo produjo argumentos de herramienta inválidos. No se ejecutó la acción.") from None


def json_fallback(reply):
    if reply.calls or not reply.text.strip().startswith(("{", "```json")):
        return reply
    text = reply.text.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    try:
        payload = json.loads(text)
        if set(payload) == {"tool", "args"} and isinstance(payload["tool"], str) and isinstance(payload["args"], dict):
            return Reply(calls=[ToolCall(payload["tool"], payload["args"])])
    except (ValueError, TypeError):
        pass
    return reply


class BaseProvider:
    """stream() devuelve texto y peticiones; nunca ejecuta herramientas."""
    name = ""

    def stream(self, messages, system, specs, cfg, emit, cancel, image=None):
        raise NotImplementedError("El proveedor debe implementar stream().")


def openai_messages(messages, system, image=None):
    result = [{"role": "system", "content": system}]
    for m in messages:
        item = {k: v for k, v in m.items() if k in ("role", "content", "tool_calls", "tool_call_id")}
        result.append(item)
    if image:
        result.append({"role": "user", "content": [
            {"type": "text", "text": "Analiza esta captura según la pregunta del usuario."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image}}]})
    return result
