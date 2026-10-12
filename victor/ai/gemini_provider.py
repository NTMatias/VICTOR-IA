import base64
import json
import os
from victor.ai.base import BaseProvider, Reply, ToolCall
from victor.errors import check_cancel


class GeminiProvider(BaseProvider):
    name = "Gemini"

    def stream(self, messages, system, specs, cfg, emit, cancel, image=None):
        from google import genai
        from google.genai import types
        contents = []
        for m in messages:
            # Contexto interoperable: llamadas históricas se describen como datos.
            # Evita reutilizar firmas de pensamiento de un proveedor/modelo distinto.
            role = "model" if m["role"] == "assistant" else "user"
            text = m.get("content", "") or ""
            if m.get("tool_calls"):
                text += "\nHerramientas solicitadas: " + json.dumps(m["tool_calls"], ensure_ascii=False)
            if m["role"] == "tool":
                text = "Resultado verificado de herramienta " + m.get("name", "") + ":\n" + text
            if text:
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
        if image:
            contents.append(types.Content(role="user", parts=[types.Part.from_bytes(data=base64.b64decode(image), mime_type="image/png")]))
        declarations = [types.FunctionDeclaration(name=s["name"], description=s["description"], parameters_json_schema=s["parameters"]) for s in specs]
        options = types.GenerateContentConfig(system_instruction=system, temperature=cfg["temperature"],
                    max_output_tokens=cfg["max_tokens"], tools=[types.Tool(function_declarations=declarations)] if declarations else None,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))
        reply = Reply()
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"], http_options=types.HttpOptions(timeout=cfg["network_timeout"] * 1000))
        try:
            for chunk in client.models.generate_content_stream(model=cfg["models"][self.name], contents=contents, config=options):
                check_cancel(cancel)
                for candidate in chunk.candidates or []:
                    for part in (candidate.content.parts or []) if candidate.content else []:
                        if part.text and not part.thought:
                            reply.text += part.text
                            emit(part.text)
                        if part.function_call:
                            reply.calls.append(ToolCall(part.function_call.name, dict(part.function_call.args or {})))
        finally:
            client.close()
        return reply
