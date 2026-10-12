import importlib
import json
import os
import pkgutil
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from victor.config import ConfigManager
from victor.database import Database
from victor.memory import MemoryManager
from victor.history import ConversationManager
from victor.context import ContextManager
from victor.security import SecurityManager, Risk
from victor.errors import VictorError, Cancelled
from victor.system.files import FileManager
from victor.tools.registry import Tool, ToolRegistry
from victor.ai.base import Reply, ToolCall, json_fallback
from victor.ai.manager import AIManager
from victor.core import VictorCore
from victor.voice.wakeword import extract_command


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="victor-test-")
        self.root = Path(self.temp.name)
        self.cfg = ConfigManager(self.root)
        self.events = []
        self.approve = True
        self.cancel = threading.Event()
        self.security = SecurityManager(self.cfg, self.emit)
        self.files = FileManager(self.security)

    def tearDown(self):
        self.temp.cleanup()

    def emit(self, kind, payload):
        self.events.append((kind, payload))
        if kind == "approval":
            payload.accepted = self.approve
            payload.done.set()


class SecurityTests(Fixture):
    def test_path_in_workspace(self):
        self.assertEqual(self.security.path("note.txt"), self.root / "workspace/note.txt")

    def test_traversal_rejected(self):
        with self.assertRaises(VictorError):
            self.security.path("../../outside.txt")

    def test_protected_paths(self):
        for value in ("C:/Windows/System32/test.txt", str(self.root / "data/config.json"), ".env", "\\\\server\\share\\x.txt", "note.txt:evil"):
            with self.subTest(value=value), self.assertRaises(VictorError):
                self.security.path(value)

    def test_root_cannot_be_modified(self):
        with self.assertRaises(VictorError):
            self.security.path(str(self.root / "workspace"))

    def test_url_schemes(self):
        for url in ("file:///C:/Windows", "javascript:alert(1)", "https://a:b@example.com", "ms-settings:"):
            with self.assertRaises(VictorError):
                self.security.url(url)
        self.assertEqual(self.security.url("https://example.com"), "https://example.com")

    def test_low_no_confirmation(self):
        self.security.confirm("ram", "", Risk.LOW, self.cancel)
        self.assertEqual(self.events, [])

    def test_medium_and_high_confirmed_each_time(self):
        for risk in (Risk.MEDIUM, Risk.HIGH, Risk.HIGH):
            self.security.confirm("action", "exact args", risk, self.cancel)
        self.assertEqual(len(self.events), 3)

    def test_decline(self):
        self.approve = False
        with self.assertRaises(VictorError):
            self.security.confirm("delete", "file", Risk.HIGH, self.cancel)

    def test_cancel(self):
        self.cancel.set()
        with self.assertRaises(Cancelled):
            self.security.confirm("delete", "file", Risk.HIGH, self.cancel)

    def test_strict_confirms_low(self):
        self.cfg.save({"security": "strict"})
        self.security.confirm("ram", "", Risk.LOW, self.cancel)
        self.assertEqual(len(self.events), 1)

    def test_registry_unknown_and_extra_args(self):
        registry = ToolRegistry(self.security, self.cancel, self.emit)
        calls = []
        registry.register(Tool("safe", "test", {"type": "object", "properties": {}, "additionalProperties": False}, Risk.LOW, lambda: calls.append(1)))
        self.assertFalse(registry.execute("unknown", {})["ok"])
        self.assertFalse(registry.execute("safe", {"execute": "evil"})["ok"])
        self.assertEqual(calls, [])

    def test_registry_decline_prevents_execution(self):
        self.approve = False
        registry = ToolRegistry(self.security, self.cancel, self.emit)
        calls = []
        registry.register(Tool("danger", "test", {"type": "object"}, Risk.HIGH, lambda: calls.append(1)))
        self.assertFalse(registry.execute("danger", {})["ok"])
        self.assertEqual(calls, [])

    def test_shell_not_allowed(self):
        from victor.system.windows_controller import WindowsController
        if os.name == "nt":
            with self.assertRaises(VictorError):
                WindowsController().run_diagnostic("whoami & del *")


class StorageTests(Fixture):
    def test_config_roundtrip(self):
        self.cfg.save({"name": "Victor", "fallback": ["Gemini", "Ollama"]})
        other = ConfigManager(self.root)
        self.assertEqual(other.get("name"), "Victor")
        self.assertEqual(other.get("fallback"), ["Gemini", "Ollama"])

    def test_no_secrets_saved(self):
        self.cfg.save({"OPENAI_API_KEY": "secret", "name": "V"})
        self.assertNotIn("secret", self.cfg.path.read_text())

    def test_invalid_config_keeps_previous(self):
        with self.assertRaises(VictorError):
            self.cfg.save({"max_tokens": -5})
        self.assertEqual(self.cfg.get("max_tokens"), 2048)

    def test_corrupt_config_recovers(self):
        self.cfg.path.write_text("broken")
        recovered = ConfigManager(self.root)
        self.assertTrue(recovered.warning)

    def test_memory_persistence_and_forget(self):
        path = self.root / "data/test.db"
        memory = MemoryManager(Database(path))
        memory.remember("nombre", "Ana")
        memory = MemoryManager(Database(path))
        self.assertEqual(memory.recall("nombre")[0]["value"], "Ana")
        memory.remember("nombre", "Luis")
        self.assertEqual(len(memory.recall("nombre")), 1)
        memory.forget("nombre")
        self.assertEqual(memory.recall("nombre"), [])

    def test_history_search_delete_cascade(self):
        db = Database(self.root / "data/test.db")
        history = ConversationManager(db)
        cid = history.create()
        history.add(cid, "user", "pregunta especial")
        self.assertEqual(history.list("especial")[0]["id"], cid)
        history = ConversationManager(Database(self.root / "data/test.db"))
        self.assertEqual(history.messages(cid)[0]["content"], "pregunta especial")
        history.delete(cid)
        self.assertEqual(history.messages(cid), [])

    def test_create_copy_rename_move_no_overwrite(self):
        self.files.create_file("a.txt", "Hola")
        self.files.copy_file("a.txt", "b.txt")
        self.files.rename_file("b.txt", "c.txt")
        self.files.move_file("c.txt", "d.txt")
        self.assertEqual((self.root / "workspace/d.txt").read_text(), "Hola")
        with self.assertRaises(FileExistsError):
            self.files.copy_file("a.txt", "d.txt")
        self.assertTrue((self.root / "workspace/a.txt").exists())

    def test_executable_creation_rejected(self):
        with self.assertRaises(VictorError):
            self.files.create_file("evil.bat", "echo x")

    def test_delete_uses_recycle_bin(self):
        self.files.create_file("a.txt", "x")
        with patch("send2trash.send2trash") as trash:
            self.files.delete_file("a.txt")
            trash.assert_called_once_with(str(self.root / "workspace/a.txt"))

    def test_context_bounded_and_summary_persists(self):
        db = Database(self.root / "data/test.db")
        history, memory = ConversationManager(db), MemoryManager(db)
        cid = history.create()
        for n in range(40):
            history.add(cid, "user" if n % 2 == 0 else "assistant", f"Decisión {n}. " + "detalle " * 300)
        messages, system = ContextManager(self.cfg, history, memory).build(cid)
        self.assertLessEqual(sum(len(m["content"]) for m in messages), self.cfg.get("context_chars"))
        self.assertTrue(history.get(cid)["summary"])
        self.assertIn("39", messages[-1]["content"])


class AITests(Fixture):
    def test_json_tool_alternative(self):
        reply = json_fallback(Reply('{"tool":"get_system_info","args":{}}'))
        self.assertEqual(reply.calls[0].name, "get_system_info")

    def test_not_arbitrary_json(self):
        self.assertEqual(json_fallback(Reply('{"answer": 42}')).calls, [])

    def test_missing_key_message(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(VictorError, "OPENAI_API_KEY"):
                AIManager(self.cfg, self.emit).generate([], "", [], self.cancel)

    def test_fallback_on_error(self):
        self.cfg.save({"fallback": ["Ollama"]})
        manager = AIManager(self.cfg, self.emit)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}), \
             patch.object(manager.providers["OpenAI"], "stream", side_effect=ConnectionError()), \
             patch.object(manager.providers["Ollama"], "stream", return_value=Reply("Respaldo")):
            reply = manager.generate([], "", [], self.cancel)
        self.assertEqual(reply.text, "Respaldo")
        self.assertTrue(any(k == "notice" and "respaldo" in v for k, v in self.events))

    def test_cancel_no_fallback(self):
        self.cfg.save({"fallback": ["Ollama"]})
        manager = AIManager(self.cfg, self.emit)
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}), \
             patch.object(manager.providers["OpenAI"], "stream", side_effect=Cancelled()), \
             patch.object(manager.providers["Ollama"], "stream") as fallback:
            with self.assertRaises(Cancelled):
                manager.generate([], "", [], self.cancel)
        fallback.assert_not_called()

    def test_wakeword_boundary(self):
        self.assertEqual(extract_command("VICTOR, abre Chrome", "VICTOR"), "abre Chrome")
        self.assertEqual(extract_command("Víctor, abre Chrome", "VICTOR"), "abre Chrome")
        self.assertEqual(extract_command("victorioso abre Chrome", "VICTOR"), "")
        self.assertEqual(extract_command("Hola", "VICTOR", False), "Hola")

    def test_local_commands(self):
        core = VictorCore(self.cfg, self.emit)
        self.assertEqual(core.local_command("Abre la calculadora"), ("open_application", {"name": "calculadora"}))
        self.assertEqual(core.local_command("¿Cuánta RAM estoy usando?")[0], "get_system_info")
        self.assertEqual(core.local_command('Borra el archivo "nota.txt"'), ("delete_file", {"path": "nota.txt"}))

    def test_core_ram_and_persistent_turn(self):
        core = VictorCore(self.cfg, self.emit)
        cid = core.history.create()
        core.submit("¿Cuánta RAM estoy usando?", cid)
        core.thread.join(10)
        self.assertFalse(core.busy.is_set())
        self.assertTrue(any(k == "answer" and "RAM:" in v for k, v in self.events))
        reopened = VictorCore(self.cfg, self.emit)
        self.assertTrue(reopened.history.messages(cid))

    def test_import_every_module(self):
        import victor
        for module in pkgutil.walk_packages(victor.__path__, "victor."):
            importlib.import_module(module.name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
