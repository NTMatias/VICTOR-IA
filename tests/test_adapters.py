import json
import os
import threading
import unittest
from copy import deepcopy
from types import SimpleNamespace as NS
from unittest.mock import patch
from victor.config import DEFAULTS
from victor.ai.openai_provider import OpenAIProvider
from victor.ai.anthropic_provider import AnthropicProvider, convert
from victor.ai.gemini_provider import GeminiProvider


class ContextList(list):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.cfg = deepcopy(DEFAULTS)
        self.cancel = threading.Event()
        self.tokens = []
        self.specs = [{"name": "get_system_info", "description": "Info", "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False}}]
        self.messages = [{"role": "user", "content": "RAM"}]

    def test_sdk_imports(self):
        import openai
        import anthropic
        from google import genai
        self.assertTrue(openai.OpenAI and anthropic.Anthropic and genai.Client)

    def test_openai_stream_tool_assembly(self):
        chunks = ContextList([
            NS(choices=[NS(delta=NS(content="Voy a consultar.", tool_calls=[]))]),
            NS(choices=[NS(delta=NS(content=None, tool_calls=[NS(index=0, id="call_1", function=NS(name="get_system_info", arguments="{"))]))]),
            NS(choices=[NS(delta=NS(content=None, tool_calls=[NS(index=0, id=None, function=NS(name=None, arguments="}"))]))]),
        ])
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}), patch("openai.OpenAI") as sdk:
            client = sdk.return_value
            client.chat.completions.create.return_value = chunks
            reply = OpenAIProvider().stream(self.messages, "system", self.specs, self.cfg, self.tokens.append, self.cancel)
            kwargs = client.chat.completions.create.call_args.kwargs
        self.assertEqual(reply.calls[0].args, {})
        self.assertEqual(reply.calls[0].id, "call_1")
        self.assertEqual("".join(self.tokens), "Voy a consultar.")
        self.assertFalse(kwargs["parallel_tool_calls"])

    def test_anthropic_tools_and_results_conversion(self):
        messages = self.messages + [
            {"role": "assistant", "content": "", "tool_calls": [{"id": "c", "function": {"name": "get_system_info", "arguments": "{}"}}]},
            {"role": "tool", "name": "get_system_info", "tool_call_id": "c", "content": '{"ok":true}'}]
        result = convert(messages, image="aGVsbG8=")
        self.assertEqual(result[1]["content"][0]["type"], "tool_use")
        self.assertEqual(result[2]["content"][0]["tool_use_id"], "c")
        self.assertEqual(result[2]["content"][1]["type"], "image")

    def test_gemini_native_schema_and_stream(self):
        from google.genai import types
        response = types.GenerateContentResponse(candidates=[types.Candidate(content=types.Content(role="model", parts=[
            types.Part.from_function_call(name="get_system_info", args={})]))])
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test"}), patch("google.genai.Client") as sdk:
            sdk.return_value.models.generate_content_stream.return_value = [response]
            reply = GeminiProvider().stream(self.messages, "system", self.specs, self.cfg, self.tokens.append, self.cancel)
            config = sdk.return_value.models.generate_content_stream.call_args.kwargs["config"]
            sdk.return_value.close.assert_called_once()
        self.assertEqual(reply.calls[0].name, "get_system_info")
        self.assertTrue(config.automatic_function_calling.disable)


if __name__ == "__main__":
    unittest.main()
