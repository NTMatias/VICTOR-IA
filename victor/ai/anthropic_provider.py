import json
import os
from victor.ai.base import BaseProvider, Reply, ToolCall
from victor.errors import check_cancel


def convert(messages, image=None):
    result = []
    for m in messages:
        if m["role"] == "tool":
            role = "user"
            parts = [{"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}]
        else:
            role = m["role"]
            parts = [{"type": "text", "text": m["content"]}] if m.get("content") else []
            for c in m.get("tool_calls", []):
                parts.append({"type": "tool_use", "id": c["id"], "name": c["function"]["name"], "input": json.loads(c["function"]["arguments"])})
        if not parts:
            continue
        if result and result[-1]["role"] == role:
            result[-1]["content"].extend(parts)
        else:
            result.append({"role": role, "content": parts})
    if image:
        content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image}}]
        if result and result[-1]["role"] == "user":
            result[-1]["content"].extend(content)
        else:
            result.append({"role": "user", "content": content})
    return result


class AnthropicProvider(BaseProvider):
    name = "Anthropic"

    def stream(self, messages, system, specs, cfg, emit, cancel, image=None):
        from anthropic import Anthropic
        reply = Reply()
        options = dict(model=cfg["models"][self.name], system=system, messages=convert(messages, image),
                       max_tokens=cfg["max_tokens"], temperature=min(cfg["temperature"], 1))
        if specs:
            options["tools"] = [{"name": s["name"], "description": s["description"], "input_schema": s["parameters"]} for s in specs]
        with Anthropic(api_key=cfg.get("_api_key") or os.environ["ANTHROPIC_API_KEY"], timeout=cfg["network_timeout"], max_retries=0) as client:
            with client.messages.stream(**options) as stream:
                for text in stream.text_stream:
                    check_cancel(cancel)
                    reply.text += text
                    emit(text)
                result = stream.get_final_message()
        reply.calls = [ToolCall(b.name, b.input, b.id) for b in result.content if b.type == "tool_use"]
        return reply
