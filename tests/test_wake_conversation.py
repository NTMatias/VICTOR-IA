"""Activation, speech encoding and provider failures without owner's microphone."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from google.genai.errors import ServerError, ClientError
from victor.config import ConfigManager, DEFAULTS, ROOT
from victor.errors import Cancelled
from victor.voice.input import VoiceInput
from victor.voice.text import speech_text
from victor.voice.wakeword import wake_match
from victor.ai.gemini_provider import GeminiProvider
from victor.gui.spotify_commands import spotify_command


class WakeConversation(unittest.TestCase):
    def run_phrases(self, phrases, modify=None):
        with tempfile.TemporaryDirectory() as folder:
            cfg = ConfigManager(Path(folder)); cfg.save({'voice_mode': 'continua'})
            events = []
            def emit(kind, value):
                events.append((kind, value))
                if kind == 'voice_wake': value.set()
            voice = VoiceInput(cfg, emit, lambda: True)
            voice.background_context = lambda: True
            phrases = iter(phrases)
            def listen():
                try:
                    text = next(phrases)
                    if modify: modify(voice, text)
                    return text
                except StopIteration:
                    voice.stop(); return ''
            with patch.object(voice, 'listen', side_effect=listen): voice._run()
            return events

    def test_wake_alone_then_any_request_without_focus(self):
        events = self.run_phrases(['charla de fondo', 'Víctor.', 'reproduce GAMINA de Kris R',
                                  'ignora esta conversación', 'VICTOR', 'baja el volumen', 'VICTOR',
                                  '¿qué hora es?', 'VICTOR', 'manda un correo a Ana'])
        self.assertEqual(sum(k == 'voice_wake' for k, v in events), 4)
        self.assertEqual([v for k,v in events if k == 'voice_text'],
                         ['reproduce GAMINA de Kris R', 'baja el volumen', '¿qué hora es?', 'manda un correo a Ana'])
        self.assertTrue(any(k == 'voice_status' and v == 'Escuchando tu petición…' for k,v in events))

    def test_expiry_returns_to_wake_wait_and_reactivates(self):
        def expire(voice, text):
            if text == 'chatter': voice.conversation_until = 0
        events = self.run_phrases(['VICTOR', 'chatter', 'baja volumen', 'viktor', 'cambia la canción'], expire)
        self.assertEqual(sum(k == 'voice_wake' for k,v in events), 2)
        self.assertEqual([v for k,v in events if k == 'voice_text'], ['cambia la canción'])
        self.assertIsNone(wake_match('victorioso', 'VICTOR'))

    def test_greeting_must_finish_before_inline_command_or_next_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg = ConfigManager(Path(folder)); cfg.save({'voice_mode': 'continua'})
            greeting = threading.Event(); events = []; completed = []
            def emit(kind, value):
                events.append((kind,value))
                if kind == 'voice_wake': completed.append(value); greeting.set()
            voice = VoiceInput(cfg, emit, lambda: True)
            def listen():
                if listen.calls == 0:
                    listen.calls += 1; return 'VICTOR reproduce GAMINA'
                voice.stop(); return ''
            listen.calls = 0
            with patch.object(voice, 'listen', side_effect=listen) as capture:
                thread = threading.Thread(target=voice._run); thread.start()
                try:
                    self.assertTrue(greeting.wait(2)); time.sleep(.15)
                    self.assertEqual(capture.call_count, 1)
                    self.assertFalse(any(k == 'voice_text' for k,v in events))
                    completed[0].set(); thread.join(2)
                    self.assertFalse(thread.is_alive())
                    self.assertEqual([v for k,v in events if k == 'voice_text'], ['reproduce GAMINA'])
                finally: voice.stop(); thread.join(2)

    def test_pause_during_greeting_never_dispatches_command(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg = ConfigManager(Path(folder)); cfg.save({'voice_mode': 'continua'})
            greeting = threading.Event(); events = []
            def emit(kind, value):
                events.append((kind,value))
                if kind == 'voice_wake': greeting.set()
            voice = VoiceInput(cfg, emit, lambda: True)
            with patch.object(voice, 'listen', return_value='VICTOR manda el correo'):
                thread = threading.Thread(target=voice._run); thread.start()
                self.assertTrue(greeting.wait(2)); voice.stop(); thread.join(2)
            self.assertFalse(thread.is_alive())
        self.assertFalse(any(k == 'voice_text' for k,v in events))

    def test_gui_greeting_is_forced_and_completion_is_forwarded_without_focus(self):
        from victor.gui.app import GUIManager
        app = SimpleNamespace(closing=False, voice_input=SimpleNamespace(stop_event=threading.Event()),
                              voice_panel=Mock(), voice_output=Mock())
        finished = threading.Event()
        GUIManager.handle_event(app, 'voice_wake', finished)
        app.voice_output.speak.assert_called_once_with('¿En qué te ayudo?', force=True, completed=finished)
        self.assertFalse(finished.is_set())
        app.closing=True; app.voice_output.reset_mock()
        GUIManager.handle_event(app, 'voice_wake', finished)
        self.assertTrue(finished.is_set()); app.voice_output.speak.assert_not_called()

    def test_followup_controls_use_actual_music_state(self):
        state = {'id': 'track', 'volume': 35}
        for text, expected in [('cambia la canción', ('spotify_next', {})),
                               ('pausa', ('spotify_pause', {})),
                               ('sube el volumen', ('spotify_volume', {'level': 45})),
                               ('baja volumen', ('spotify_volume', {'level': 25})),
                               ('pon el volumen al 20 por ciento', ('spotify_volume', {'level': 20}))]:
            self.assertEqual(spotify_command(text, state=state), expected)
        self.assertEqual(spotify_command('ajusta el volumen a 50 en Spotify'), ('spotify_volume', {'level': 50}))
        self.assertIsNone(spotify_command('sube el volumen'))
        self.assertIsNone(spotify_command('volumen 200 en Spotify'))
        self.assertIsNone(spotify_command('manda un correo', state=state))


class SpeechEncoding(unittest.TestCase):
    def test_capture_discards_audio_if_speech_starts_while_stream_opens(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'microphone':'0'});available=[True]; events=[]
            voice=VoiceInput(cfg,lambda *event:events.append(event),lambda:available[0])
            voice.transcriber=Mock()
            def stream(**kwargs):
                context=Mock()
                def enter():
                    kwargs['callback'](np.full((1600,1),3000,dtype=np.int16),1600,None,None)
                    available[0]=False
                context.__enter__=Mock(side_effect=enter);context.__exit__=Mock(return_value=False)
                return context
            with patch('sounddevice.query_devices',return_value={'max_input_channels':1,'default_samplerate':16000}),patch('sounddevice.check_input_settings'),patch('sounddevice.InputStream',side_effect=stream):
                self.assertEqual(voice.listen(),'')
            voice.transcriber.transcribe.assert_not_called()
            self.assertIn(('mic_level',0.),events)

    def test_real_worker_reads_utf8_even_with_windows_cp1252_stdin(self):
        phrase = '¿En qué te ayudo? Canción, acción, café, niño y pingüino.'
        script = '''import json
from victor.voice import output
def fake_sapi(payload, path=None):
    print(json.dumps(payload['text'], ensure_ascii=True))
    if path is not None: path.write_bytes(b'x' * 45)
output.speak_sapi = fake_sapi
output.play_audio = lambda path: None
output.speak_worker()
'''
        env = dict(os.environ, PYTHONIOENCODING='cp1252')
        result = subprocess.run([sys.executable, '-c', script], cwd=ROOT, env=env,
                                input=json.dumps({'text':phrase, 'backend':'sapi'}, ensure_ascii=False).encode('utf-8'),
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr.decode('ascii', errors='replace'))
        self.assertEqual(json.loads(result.stdout), phrase)
        self.assertEqual(speech_text('**Cancio\u0301n** (español) ©'), 'Canción, español')


class HandsfreeApproval(unittest.TestCase):
    def test_real_gui_core_mail_review_and_spoken_authorization_no_mail_sent(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from unittest.mock import PropertyMock
        from victor.gui.app import GUIManager
        q=QApplication.instance() or QApplication([]); q.setQuitOnLastWindowClosed(False)
        def until(check, seconds=5):
            deadline=time.monotonic()+seconds
            while not check() and time.monotonic()<deadline: q.processEvents(); time.sleep(.01)
            return check()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'voice_mode':'continua','voice_backend':'google'})
            app=GUIManager(cfg);send_mail=Mock(return_value={'sent':True})
            app.core.registry.tools['google_send_email'].function=send_mail
            app.voice_output.speak=Mock()
            try:
                app.showMinimized();app.voice_background=True
                with patch.object(VoiceInput,'running',new_callable=PropertyMock,return_value=True):
                    args={'to':'demo@example.com','subject':'Asunto de prueba','body':'Cuerpo completo de la prueba.'}
                    app.send('envía el correo',('google_send_email',args),voice=True)
                    self.assertTrue(until(lambda:app.confirmation_target is not None))
                    request=app.confirmation_target;send_mail.assert_not_called()
                    review=app.voice_output.speak.call_args.args[0]
                    for value in args.values():self.assertIn(value,review)
                    dialog=app.approval_dialogs[-1]
                    self.assertFalse(dialog.isModal())
                    self.assertTrue(dialog.testAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating))
                    app.handle_voice_text('confirmar',request);send_mail.assert_not_called()
                    app.handle_voice_text('ejecutar',request)
                    self.assertTrue(until(lambda:not app.core.busy.is_set()))
                    send_mail.assert_called_once_with(**args)
                    self.assertTrue(request.accepted)
                    self.assertFalse(app.voice_input.stop_event.is_set())
            finally:
                app.close();self.assertTrue(until(lambda:app.closed_cleanly))

    def test_remote_or_truncated_review_cannot_arm_local_voice(self):
        from victor.gui.app import GUIManager
        from victor.security import Approval, Risk
        app=SimpleNamespace(confirmation_target=None,voice_panel=Mock(),voice_output=Mock())
        for request in (Approval('email','review',Risk.HIGH,origin={'source':'telegram'}),
                        Approval('email','X'*6001,Risk.HIGH)):
            self.assertFalse(GUIManager.arm_spoken_approval(app,request))
        self.assertIsNone(app.confirmation_target);app.voice_output.speak.assert_not_called()


class GeminiRetries(unittest.TestCase):
    def setUp(self):
        self.cfg = dict(DEFAULTS, _api_key='fixture', _retry_notice=Mock())
        self.cancel = threading.Event(); self.cancel.wait = Mock(return_value=False)
        part = SimpleNamespace(text='Respuesta', thought=False, function_call=None)
        self.chunk = SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=[part]))])
        self.tokens = []
        self.client = Mock()

    def run_provider(self):
        with patch('google.genai.Client', return_value=self.client), patch('victor.ai.gemini_provider.random.uniform', return_value=0):
            return GeminiProvider().stream([], '', [], self.cfg, self.tokens.append, self.cancel)

    def test_transient_503_recovers_and_emits_text_once(self):
        self.client.models.generate_content_stream.side_effect = [ServerError(503, {}), ServerError(503, {}), iter([self.chunk])]
        reply = self.run_provider()
        self.assertEqual(reply.text, 'Respuesta'); self.assertEqual(self.tokens, ['Respuesta'])
        self.assertEqual(self.client.close.call_count, 3)
        self.assertEqual([call.args[0] for call in self.cancel.wait.call_args_list], [1, 2])
        self.assertEqual(self.cfg['_retry_notice'].call_count, 2)

    def test_invalid_key_and_quota_not_retried(self):
        for code in (400, 401, 403, 404, 429):
            self.client.reset_mock(); self.client.models.generate_content_stream.side_effect = ClientError(code, {})
            with self.assertRaises(ClientError): self.run_provider()
            self.assertEqual(self.client.models.generate_content_stream.call_count, 1)

    def test_cancel_during_backoff_and_partial_stream_not_replayed(self):
        self.client.models.generate_content_stream.side_effect = ServerError(503, {})
        self.cancel.wait.side_effect = lambda delay: self.cancel.set()
        with self.assertRaises(Cancelled): self.run_provider()
        self.assertEqual(self.client.close.call_count, 1)
        self.cancel.clear(); self.client.reset_mock()
        def partial():
            yield self.chunk
            raise ServerError(503, {})
        self.client.models.generate_content_stream.side_effect = None
        self.client.models.generate_content_stream.return_value = partial()
        with self.assertRaises(ServerError): self.run_provider()
        self.assertEqual(self.client.models.generate_content_stream.call_count, 1)
        self.assertEqual(self.tokens, ['Respuesta'])

    def test_deadline_and_attempt_cap(self):
        self.client.models.generate_content_stream.side_effect = ServerError(503, {})
        with patch('victor.ai.gemini_provider.time.monotonic', side_effect=[0, 0, 29.8]):
            with self.assertRaises(ServerError): self.run_provider()
        self.assertEqual(self.client.models.generate_content_stream.call_count, 1)
        self.client.reset_mock()
        with self.assertRaises(ServerError): self.run_provider()
        self.assertEqual(self.client.models.generate_content_stream.call_count, 3)


if __name__ == '__main__': unittest.main()
