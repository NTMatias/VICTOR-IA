import sys
import threading
import types
from unittest.mock import patch
from tests.test_victor import Fixture
from victor.voice.input import VoiceInput
from victor.voice.transcription import Transcriber
from victor.errors import VictorError


class VoiceTests(Fixture):
    def test_local_default(self):
        self.assertEqual(self.cfg.get("voice_backend"), "whisper")
        self.assertEqual(self.cfg.get("tts_backend"), "edge")

    def test_no_microphone_guidance(self):
        self.cfg.save({'microphone':'0'})
        voice = VoiceInput(self.cfg, self.emit, lambda: True)
        with patch("sounddevice.query_devices", return_value={'max_input_channels':0,'default_samplerate':16000}):
            with self.assertRaisesRegex(VictorError, "Telegram"):
                voice.listen()

    def test_continuous_accepts_one_request_per_wake(self):
        self.cfg.save({"voice_mode": "continua"})
        captured = []
        def emit(kind, value):
            captured.append((kind, value))
            if kind == 'voice_wake': value.set()
        voice = VoiceInput(self.cfg, emit, lambda: True)
        phrases = iter(["VICTOR abre Chrome", "ahora abre YouTube", "busca música"])
        def listen():
            try:
                return next(phrases)
            except StopIteration:
                voice.stop()
                return ""
        with patch.object(voice, "listen", side_effect=listen):
            voice._run()
        self.assertEqual([v for k, v in captured if k == "voice_text"], ["abre Chrome"])

    def test_transcriber_cpu_local_only(self):
        module = types.ModuleType("faster_whisper")
        from unittest.mock import MagicMock
        model = MagicMock()
        model.transcribe.return_value = ([types.SimpleNamespace(text="hola")], None)
        module.WhisperModel = MagicMock(return_value=model)
        with patch.dict(sys.modules, {"faster_whisper": module}):
            self.assertEqual(Transcriber(self.cfg).transcribe([0.1], threading.Event()), "hola")
        options = module.WhisperModel.call_args.kwargs
        self.assertEqual(options["compute_type"], "int8")
        self.assertEqual(options["device"], "cpu")
        self.assertTrue(options["local_files_only"])
        decoding = model.transcribe.call_args.kwargs
        self.assertEqual(decoding["beam_size"], 5)
        self.assertFalse(decoding["condition_on_previous_text"])
        self.assertIn("Spotify", decoding["initial_prompt"])
