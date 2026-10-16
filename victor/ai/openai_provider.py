import os
from victor.ai.base import BaseProvider, Reply, ToolCall, parse_args, openai_messages
from victor.errors import check_cancel


class OpenAIProvider(BaseProvider):
    name = "OpenAI"
    def __init__(self):
        from .transport import Transport
        self.transport=Transport()
    def close(self):self.transport.close()

    def stream(self, messages, system, specs, cfg, emit, cancel, image=None):
        from openai import OpenAI
        reply, pending = Reply(), {}
        options = dict(model=cfg["models"][self.name], messages=openai_messages(messages, system, image),
                       max_completion_tokens=cfg["max_tokens"], stream=True)
        # Familias de razonamiento no aceptan temperatura configurable.
        if not options["model"].startswith(("o1", "o3", "o4", "gpt-5", "gpt-6")):
            options["temperature"] = cfg["temperature"]
        if specs:
            options["tools"] = [{"type": "function", "function": s} for s in specs]
            options["parallel_tool_calls"] = False
        with self.transport.use(OpenAI,cancel,api_key=cfg.get("_api_key") or os.environ["OPENAI_API_KEY"], timeout=cfg["network_timeout"], max_retries=0) as client:
            with client.chat.completions.create(**options) as stream:
                for chunk in stream:
                    check_cancel(cancel)
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    if delta.content:
                        reply.text += delta.content
                        emit(delta.content)
                    for part in delta.tool_calls or []:
                        current = pending.setdefault(part.index, {"id": "", "name": "", "args": ""})
                        if part.id:
                            current["id"] = part.id
                        if part.function:
                            current["name"] += part.function.name or ""
                            current["args"] += part.function.arguments or ""
        reply.calls = [ToolCall(c["name"], parse_args(c["args"]), c["id"]) for c in pending.values()]
        return reply
