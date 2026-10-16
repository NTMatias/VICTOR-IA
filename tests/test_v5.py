import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from victor.config import ConfigManager
from tests.gui_support import authenticated_gui as GUIManager
from victor.gui.maintenance import audit_rows
from victor.voice.models import cached_model, model_directory, complete
from victor.voice.wakeword import extract_command
from victor.voice.input import VoiceInput


class V5(unittest.TestCase):
    def test_diagnostics_no_credentials_no_secrets(self):
        import os
        from victor.diagnostics import check_services
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {}, clear=True):
            cfg=ConfigManager(Path(folder));rows={}
            with patch('victor.diagnostics.cached_model', return_value=None):
                check_services(cfg, lambda name, text: rows.update({name:text}))
            self.assertEqual(set(rows), {'IA','Whisper','Spotify','Google','Telegram'})
            self.assertIn('OPENAI_API_KEY', rows['IA'])

    def test_diagnostics_ai_probe_never_executes_tools(self):
        import os
        from victor.diagnostics import check_services
        from victor.ai.base import Reply, ToolCall
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'OPENAI_API_KEY':'secret-not-in-output'}):
            cfg=ConfigManager(Path(folder));rows={}
            provider=Mock();provider.stream.return_value=Reply('OK', [ToolCall('delete_file', {'path':'x'})])
            with patch('victor.ai.manager.AIManager') as manager, patch('victor.diagnostics.cached_model', return_value=None):
                manager.return_value.providers={'OpenAI':provider}
                check_services(cfg, lambda name,text:rows.update({name:text}))
            self.assertIn('respondió', rows['IA'])
            self.assertEqual(provider.stream.call_args.args[2], [])
            self.assertNotIn('secret-not-in-output', str(rows))

    def test_wake_variants_and_boundaries(self):
        for word in ('Víctor', 'VICTOR', 'Bictor', 'Viktor', 'Vitor', 'Vicktor'):
            self.assertEqual(extract_command(word + ', abre Chrome', 'VICTOR'), 'abre Chrome')
        for word in ('victorioso', 'victoria', 'dictor', 'sí', 'confirmar'):
            self.assertEqual(extract_command(word + ' abre Chrome', 'VICTOR'), '')

    def test_missing_wake_guidance(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg = ConfigManager(Path(folder));cfg.save({'voice_mode': 'continua'})
            emit = Mock();voice = VoiceInput(cfg, emit, lambda: True)
            def heard():
                if heard.calls == 3:voice.stop()
                heard.calls += 1
                return 'frase sin activación'
            heard.calls = 0
            with patch.object(voice, 'listen', side_effect=heard):voice._run()
            self.assertFalse(any(args[0][0] in ('notice','voice_text','voice_wake') for args in emit.call_args_list))

    def test_cache_detects_incomplete_and_local(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg = ConfigManager(Path(folder));directory = model_directory(cfg);directory.mkdir(parents=True)
            (directory/'model.bin').write_bytes(b'fixture')
            self.assertFalse(complete(directory))
            for name in ('config.json', 'tokenizer.json'):(directory/name).write_text('{}')
            self.assertEqual(cached_model(cfg), str(directory.resolve()))

    def test_audit_bounds_and_no_arbitrary_log_text(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'audit.log'
            path.write_text('secret unrelated log\n' + '\n'.join('2026-09-25 10:20:30 INFO victor tool=open_url result=success seconds=.1' for _ in range(25)) +
                            '\n2026-09-25 10:21:00 INFO confirmation result action=delete_file accepted=False cancelled=False')
            rows = audit_rows(path, {'open_url':'LOW', 'delete_file':'HIGH'})
            self.assertEqual(len(rows), 20);self.assertIn('Rechazada', rows[-1])
            self.assertNotIn('secret', ''.join(rows))

    def test_gui_prediction_rejection_debounce_and_presentation(self):
        qt = QApplication.instance() or QApplication([]);qt.setQuitOnLastWindowClosed(False)
        def pump(seconds):
            end=time.monotonic()+seconds
            while time.monotonic()<end:qt.processEvents();time.sleep(.005)
        with tempfile.TemporaryDirectory() as folder:
            app=GUIManager(ConfigManager(Path(folder)))
            try:
                app.show();pump(.1)
                app.toggle_presentation();self.assertTrue(app.menu.isHidden())
                app.toggle_presentation();self.assertFalse(app.menu.isHidden())
                # Aislar el estado de prueba del polling sin cuenta de este perfil.
                app.spotify_poller.stop_event.set();app.spotify_poller.thread.join(1);pump(.1)
                app.spotify_command=Mock(return_value=True)
                player=app.player
                player.update_state(dict(id='test', name='Pista de prueba', artists='Fixture', playing=True,volume=20, art=b''))
                start=time.perf_counter();player.action('toggle');latency=(time.perf_counter()-start)*1000
                self.assertEqual(player.play.accessibleName(),'Reproducir');self.assertTrue(player.pending)
                self.assertEqual(app.sections.spotify_play.accessibleName(),'Reproducir')
                self.assertEqual(player.pending,'spotify_pause')
                player.update_state(dict(player.state,playing=True));self.assertFalse(player.state['playing'])
                player.reconcile('spotify_pause', {'ok':False});self.assertTrue(player.state['playing'])
                app.spotify_command.reset_mock()
                for n in range(30,70):player.volume.setValue(n)
                self.assertFalse(app.spotify_command.called);pump(.2)
                app.spotify_command.assert_called_once_with('spotify_volume', {'level':69})
                # Un snapshot anterior no debe hacer retroceder el volumen local.
                old=dict(player.state,volume=20)
                player.update_state(old);app.sections.spotify_state(old)
                self.assertEqual(player.volume.value(),69)
                self.assertEqual(app.sections.spotify_volume.value(),69)
                player.reconcile('spotify_volume',{'ok':True,'result':{'nivel_solicitado':69,'aceptada_por_api':True}})
                player.update_state(old);self.assertEqual(player.volume.value(),69)
                player.update_state(dict(old,volume=69));self.assertIsNone(player.volume_intent)
                print(f'V5 visual optimistic callback: {latency:.2f} ms (API simulada)')
                app.maintenance.ready=False
                app.start_mic();self.assertFalse(app.voice_input.running)
            finally:
                app.close();pump(6)
            self.assertTrue(app.closed_cleanly)


if __name__=='__main__':unittest.main()
