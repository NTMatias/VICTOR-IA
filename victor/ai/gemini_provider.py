import base64
import json
import os
import random
import time
from victor.ai.base import BaseProvider, Reply, ToolCall
from victor.errors import check_cancel, VictorError


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
        deadline = time.monotonic() + cfg['network_timeout']
        for attempt in range(3):
            check_cancel(cancel)
            reply = Reply()
            started = False
            remaining = max(.1, deadline - time.monotonic())
            # Un solo intento SDK; los reintentos de VICTOR tienen presupuesto
            # total y se pueden cancelar durante la espera.
            client = genai.Client(api_key=cfg.get("_api_key") or os.environ["GEMINI_API_KEY"],
                http_options=types.HttpOptions(timeout=int(remaining * 1000), retry_options=types.HttpRetryOptions(attempts=1)))
            retry_error = None
            try:
                for chunk in client.models.generate_content_stream(model=cfg["models"][self.name], contents=contents, config=options):
                    check_cancel(cancel)
                    if time.monotonic() > deadline:
                        raise VictorError('La respuesta de Gemini superó el tiempo de espera. Inténtalo de nuevo o usa tu proveedor de respaldo.')
                    started = True
                    for candidate in chunk.candidates or []:
                        for part in (candidate.content.parts or []) if candidate.content else []:
                            if part.text and not part.thought:
                                reply.text += part.text
                                emit(part.text)
                            if part.function_call:
                                reply.calls.append(ToolCall(part.function_call.name, dict(part.function_call.args or {})))
                return reply
            except Exception as exc:
                status = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
                # Nunca repetir un stream que ya empezó: podría duplicar texto
                # o herramientas. Claves/cuota/parámetros tampoco se reintentan.
                if started or status not in (500, 502, 503, 504) or attempt == 2:
                    raise
                retry_error = exc
            finally:
                client.close()
            delay = 2 ** attempt + random.uniform(0, .25)
            if deadline - time.monotonic() <= delay + .5:
                raise retry_error
            notice = cfg.get('_retry_notice')
            if notice:
                notice(f'Gemini no está disponible temporalmente. Reintentando ({attempt + 1}/2)…')
            cancel.wait(delay)
            check_cancel(cancel)
