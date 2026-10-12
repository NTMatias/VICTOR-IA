import os
from unittest.mock import patch, MagicMock
from tests.test_victor import Fixture
from victor.core import VictorCore
from victor.tools.registry import ToolRegistry, Tool
from victor.security import Risk
from victor.ai.ollama_provider import OllamaProvider
from victor.errors import VictorError
from victor.ai.base import Reply, ToolCall


class BlockOne(Fixture):
    def test_argument_aliases(self):
        registry = ToolRegistry(self.security, self.cancel, self.emit)
        registry.register(Tool("open_application", "open", {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"], "additionalProperties": False}, Risk.LOW, lambda name: name))
        for alias in ("app", "app_name", "application", "nombre", "program", "name"):
            self.assertEqual(registry.execute("open_application", {alias: "spotify"})["result"], "spotify")

    def test_schema_error_for_model_not_gui(self):
        core = VictorCore(self.cfg, self.emit)
        result = core.registry.execute("open_application", {"wrong": 4}, notify_validation=False)
        self.assertEqual(result["error_code"], "schema_validation")
        self.assertIn("required", result["schema_error"])
        self.assertFalse(any(k == "notice" for k, v in self.events))

    def test_one_schema_retry(self):
        core = VictorCore(self.cfg, self.emit)
        cid = core.history.create()
        invalid = Reply(calls=[ToolCall("open_application", {"wrong": "app"})])
        with patch.object(core.ai, "generate", return_value=invalid) as generate:
            core.submit("Haz una tarea interpretada por IA", cid)
            core.thread.join(5)
        self.assertEqual(generate.call_count, 2)
        self.assertTrue(any(k == "answer" and "un reintento" in v for k, v in self.events))

    def test_registered_alias_and_web_volume(self):
        self.cfg.save({"applications": {"spotify": str(self.root / "Spotify.exe"), "word": str(self.root / "Word.exe")}})
        core = VictorCore(self.cfg, self.emit)
        self.assertEqual(core.local_command("abre spotify"), ("open_application", {"name": "spotify"}))
        self.assertEqual(core.local_command("Abre Google"), ("open_url", {"url": "https://www.google.com"}))
        self.assertEqual(core.local_command("Baja el volumen al 30"), ("control_volume", {"level": 30}))
        self.assertEqual(core.local_command("silencia")[1], {"action": "mute"})
        self.assertIn("youtube.com/results", core.local_command("busca gatos en YouTube")[1]["url"])

    def test_ollama_model_missing(self):
        provider = OllamaProvider()
        with patch("victor.ai.ollama_provider.requests.get") as get:
            get.return_value.__enter__.return_value.json.return_value = {"models": []}
            with self.assertRaisesRegex(VictorError, "ollama pull qwen2.5:7b"):
                provider.ensure_model(self.cfg.snapshot())

    def test_ollama_light(self):
        self.cfg.save({"ollama_light": True})
        with patch("victor.ai.ollama_provider.requests.get") as get:
            get.return_value.__enter__.return_value.json.return_value = {"models": [{"name": "qwen2.5:3b"}]}
            self.assertEqual(OllamaProvider().ensure_model(self.cfg.snapshot()), "qwen2.5:3b")
