"""Servicios externos simulados; no equivale a verificar cuentas reales."""
import asyncio
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, AsyncMock, patch
from victor.config import ConfigManager
from victor.core import VictorCore
from victor.errors import VictorError
from victor.security import Approval, Risk
from victor.integrations.telegram_bot import TelegramService
from victor.integrations.spotify import SpotifyUnavailable


class Integrations(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = ConfigManager(Path(self.temp.name))
        self.events = []
        self.core = VictorCore(self.config, lambda *x: self.events.append(x))
        self.bot = TelegramService(self.config, self.core, Mock(), lambda *x: self.events.append(x))
        self.origin = {"source": "telegram", "user_id": 123, "chat_id": 123}
        self.config.save({"telegram_enabled": True, "telegram_allowed_ids": [123]})
        self.bot.ready.set()

    def test_local_routes(self):
        self.assertEqual(self.core.local_command("Abre Google"), ("open_url", {"url": "https://www.google.com"}))
        self.assertEqual(self.core.local_command("Reproduce DTMF en Spotify"), ("spotify_play", {"query": "DTMF"}))
        self.assertEqual(self.core.local_command("Baja el volumen al 30"), ("control_volume", {"level": 30}))
        self.assertEqual(self.core.local_command("Qué estoy viendo en la pantalla")[0], "analyze_screen")

    def test_pairing_single_use_and_expiry(self):
        code = self.bot.pairing_code()
        self.assertFalse(self.bot.pair(999, "wrong"))
        self.assertTrue(self.bot.pair(999, code))
        self.assertTrue(self.bot.authorized(999))
        self.assertFalse(self.bot.pair(888, code))
        code = self.bot.pairing_code()
        self.bot.pair_expiry = 0
        self.assertFalse(self.bot.pair(888, code))

    def test_rate_pause_and_allowlist(self):
        self.assertFalse(self.bot.authorized(999))
        self.assertTrue(all(self.bot.within_rate(123) for _ in range(6)))
        self.assertFalse(self.bot.within_rate(123))
        self.bot.pause()
        self.assertFalse(self.bot.can_execute(self.origin))
        self.bot.pause(False)
        self.config.save({"remote_block_all": True})
        self.assertFalse(self.bot.can_execute(self.origin))

    def test_inline_approval_bound_to_user_and_once(self):
        request = Approval("control_volume", "30", Risk.MEDIUM, origin=self.origin)
        self.bot.pending["abc"] = (request, self.origin)
        self.assertFalse(self.bot.resolve_callback(999, 123, "v:abc:y"))
        self.assertTrue(self.bot.resolve_callback(123, 123, "v:abc:y"))
        self.assertTrue(request.accepted)
        self.assertFalse(self.bot.resolve_callback(123, 123, "v:abc:y"))

    def test_high_risk_cannot_be_approved_in_telegram(self):
        request = Approval("delete_file", "x", Risk.HIGH, origin=self.origin)
        self.bot.pending["abc"] = (request, self.origin)
        self.assertFalse(self.bot.resolve_callback(123, 123, "v:abc:y"))
        self.core.security.set_origin(self.origin)
        with self.assertRaises(VictorError):
            self.core.security.confirm("delete_file", "x", Risk.HIGH, threading.Event())
        self.config.save({"remote_high_policy": "pc"})
        def confirm(kind, item):
            self.assertEqual(kind, "approval")
            item.accepted = True
            item.done.set()
        self.core.security.emit = confirm
        self.core.security.confirm("delete_file", "x", Risk.HIGH, threading.Event())

    def test_permission_revoked_during_confirmation(self):
        self.core.security.set_origin(self.origin)
        def revoke(kind, item):
            self.config.save({"telegram_allowed_ids": []})
            item.accepted = True
            item.done.set()
        self.core.security.emit = revoke
        with self.assertRaises(VictorError):
            self.core.security.confirm("move_file", "x", Risk.MEDIUM, threading.Event())

    def test_text_and_voice_reach_same_gui_dispatch(self):
        message = Mock(text="Abre Google", voice=None, reply_text=AsyncMock())
        update = Mock(effective_user=Mock(id=123), effective_chat=Mock(type="private", id=123), effective_message=message)
        asyncio.run(self.bot._message(update, None))
        self.assertEqual(self.events[-1][0], "remote_command")
        self.assertEqual(self.events[-1][1]["origin"], self.origin)
        voice = Mock(duration=2, file_size=200, get_file=AsyncMock(return_value=Mock(download_to_drive=AsyncMock())))
        message.text, message.voice = None, voice
        self.bot.transcriber.transcribe_file.return_value = "Baja el volumen al 30"
        asyncio.run(self.bot._message(update, None))
        self.assertEqual(self.events[-1][1]["text"], "Baja el volumen al 30")
        self.bot.transcriber.transcribe_file.assert_called_once()

    def test_spotify_play_real_state_contract(self):
        client = Mock()
        client.current_user.return_value = {"product": "premium"}
        client.devices.return_value = {"devices": [{"type": "Computer", "is_active": True, "id": "pc"}]}
        client.search.return_value = {"tracks": {"items": [{"uri": "spotify:track:AAAAAAAAAAAAAAAAAAAAAA", "name": "DTMF"}]}}
        client.current_playback.return_value = {"is_playing": True, "item": {"name": "DTMF", "uri": "spotify:track:AAAAAAAAAAAAAAAAAAAAAA", "artists": []}}
        with patch.object(self.core.spotify, "client", return_value=client), patch("victor.integrations.spotify.time.sleep"):
            result = self.core.spotify.play("DTMF")
        self.assertTrue(result["confirmada"])
        client.start_playback.assert_called_once_with(device_id="pc", uris=["spotify:track:AAAAAAAAAAAAAAAAAAAAAA"])
        client.current_user.return_value = {"product": "free"}
        self.core.spotify._premium_until = 0  # Fuerza la revisión tras vencer la caché breve.
        with self.assertRaises(SpotifyUnavailable):
            self.core.spotify.device(client)

    def test_vision_requires_disclosure_confirmation(self):
        self.core.screen.capture = Mock(return_value={"captura": "test.png"})
        self.core.security.confirm = Mock(side_effect=VictorError("cancelado"))
        with self.assertRaises(VictorError):
            self.core.vision.analyze("Qué estoy viendo", threading.Event())
        self.assertEqual(self.core.security.confirm.call_args.args[2], Risk.MEDIUM)

    def test_remote_typing_is_high_risk(self):
        self.core.security.set_origin(self.origin)
        result = self.core.registry.execute("type_text", {"text": "echo hola", "window": "Notepad"})
        self.assertFalse(result["ok"])
        # La prueba de esquema no debe confundirse con una denegación de seguridad.
        self.assertNotEqual(result.get("error_code"), "schema_validation")
