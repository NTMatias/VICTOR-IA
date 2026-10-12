"""Errores reales del SDK Google, sin red ni credenciales reales."""
import os
import threading
import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

from google.genai.errors import ClientError, ServerError
from victor.ai.base import Reply
from victor.ai.manager import AIManager, http_status
from victor.config import DEFAULTS
from victor.errors import VictorError


class GeminiErrorsTests(unittest.TestCase):
    def setUp(self):
        self.cfg = deepcopy(DEFAULTS)
        self.cfg.update(provider="Gemini", fallback=[])
        self.events = []
        self.manager = AIManager(SimpleNamespace(snapshot=lambda: deepcopy(self.cfg)),
                                 lambda kind, value: self.events.append((kind, value)))

    def failure(self, code):
        error_type = ServerError if code >= 500 else ClientError
        error = error_type(code, {"error": {"code": code, "message": "secret-test-key"}})
        with patch.dict(os.environ, {"GEMINI_API_KEY": "secret-test-key"}), \
             patch.object(self.manager.providers["Gemini"], "stream", side_effect=error), \
             self.assertLogs("victor.ai", level="WARNING") as logs:
            with self.assertRaises(VictorError) as caught:
                self.manager.generate([], "", [], threading.Event())
        message = str(caught.exception)
        self.assertNotIn("secret-test-key", message + "".join(logs.output))
        self.assertIn(f"status={code}", "".join(logs.output))
        return message

    def test_google_404_identifies_model(self):
        self.cfg["models"]["Gemini"] = "gemini-2.5-flash"
        message = self.failure(404)
        self.assertIn("gemini-2.5-flash", message)
        self.assertIn("no está disponible para tu cuenta", message)
        self.assertIn("Ajustes", message)
        self.assertNotIn("revisa la red", message)

    def test_google_auth_quota_and_server_errors(self):
        for code, expected in ((401, "clave inválida"), (403, "sin permisos"),
                               (429, "límite de uso"), (400, "parámetros"),
                               (503, "saturado"), (500, "temporalmente")):
            with self.subTest(code=code):
                self.assertIn(expected, self.failure(code))

    def test_other_sdk_http_status_and_network_failure(self):
        self.assertEqual(http_status(SimpleNamespace(status_code=401, code="invalid_key")), 401)
        self.assertEqual(http_status(SimpleNamespace(response=SimpleNamespace(status_code=502))), 502)
        self.assertIsNone(http_status(ConnectionError()))
        self.assertIsNone(http_status(SimpleNamespace(code=True)))

    def test_google_error_preserves_configured_fallback(self):
        self.cfg["fallback"] = ["Ollama"]
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test"}), \
             patch.object(self.manager.providers["Gemini"], "stream",
                          side_effect=ServerError(503, {"error": {"message": "busy"}})), \
             patch.object(self.manager.providers["Ollama"], "stream", return_value=Reply("Respaldo")), \
             self.assertLogs("victor.ai", level="WARNING"):
            reply = self.manager.generate([], "", [], threading.Event())
        self.assertEqual(reply.text, "Respaldo")
        self.assertTrue(any(kind == "notice" and "saturado" in value for kind, value in self.events))


if __name__ == "__main__":
    unittest.main()
