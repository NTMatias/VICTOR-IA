"""Regresiones GUI/audio sin micrófono, altavoces ni escritorio físico."""
from array import array
import io
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

from victor.config import ConfigManager
from victor.voice.levels import pcm_rms, decode_meter
from victor.voice.output import VoiceOutput, speak_sapi


class AudioLevels(unittest.TestCase):
    def test_pcm_formats_and_silence(self):
        for kind,values,fmt in [('h',[16384,-16384],'Int16'),('i',[1073741824,-1073741824],'Int32'),('f',[.5,-.5],'Float'),('B',[192,64],'UInt8')]:
            with self.subTest(fmt=fmt):self.assertAlmostEqual(pcm_rms(array(kind,values).tobytes(),fmt),.5)
        self.assertEqual(pcm_rms(bytes(16),'Int16'),0.)
        self.assertEqual(pcm_rms(bytes([128]*16),'UInt8'),0.)
        self.assertEqual(pcm_rms(array('f',[2.,-2.]).tobytes(),'Float'),1.)

    def test_invalid_pcm_and_real_qt_buffer_fixture(self):
        from PySide6.QtCore import QByteArray
        from PySide6.QtMultimedia import QAudioBuffer,QAudioFormat
        for data,fmt in [(b'x','Int16'),(b'','Float'),(b'abc','Unknown'),(array('f',[float('nan')]).tobytes(),'Float')]:
            self.assertEqual(pcm_rms(data,fmt),0.)
        fmt=QAudioFormat();fmt.setSampleRate(16000);fmt.setChannelCount(1);fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        buffer=QAudioBuffer(QByteArray(array('h',[16384,-16384]).tobytes()),fmt)
        self.assertAlmostEqual(pcm_rms(bytes(buffer.data())[:buffer.byteCount()],buffer.format().sampleFormat().name),.5)

    def test_meter_protocol_rejects_noise_and_nonfinite(self):
        self.assertEqual(decode_meter('{"type":"tts_level","value":2}'),('tts_level',1.))
        self.assertEqual(decode_meter('{"type":"tts_level","value":-2}'),('tts_level',0.))
        for text in ['Qt log','[]','{}','{"type":"tts_level","value":true}','{"type":"tts_level","value":NaN}','{"type":"tts_meter","value":1}','{"type":"speech_status","value":"fake"}']:
            with self.subTest(text=text):self.assertIsNone(decode_meter(text))
        self.assertEqual(decode_meter('{"type":"tts_meter","value":false}'),('tts_meter',False))

    def test_reader_discards_cancelled_epoch_and_closed_pipe(self):
        voice=VoiceOutput.__new__(VoiceOutput);voice.epoch=2;voice.closing=threading.Event();voice.emit=Mock()
        process=Mock();process.stdout=io.StringIO('{"type":"tts_level","value":0.5}\n')
        voice.read_meter(process,1);voice.emit.assert_not_called()
        process.stdout.seek(0);voice.read_meter(process,2);voice.emit.assert_called_once_with('tts_level',.5)
        process.stdout.close();voice.read_meter(process,2)

    def test_parent_receives_levels_before_process_finishes_and_cleans_up(self):
        received=threading.Event();finished=threading.Event();events=[]
        def emit(kind,value):
            events.append((kind,value))
            if kind=='tts_level' and value==.5:received.set()
        class Input(io.StringIO):
            def close(self):self.payload=self.getvalue();super().close()
        class Process:
            def __init__(self):
                self.stdin=Input();self.stdout=io.StringIO('unrelated log\n{"type":"tts_level","value":0.5}\n');self.returncode=None
            def wait(self,timeout=None):
                if not received.wait(2):raise RuntimeError('No streaming meter')
                self.returncode=0;finished.set();return 0
            def poll(self):return self.returncode
            def terminate(self):self.returncode=0
            def kill(self):self.returncode=1
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'voice_enabled':True});process=Process()
            with patch('victor.voice.output.subprocess.Popen',return_value=process):
                voice=VoiceOutput(cfg,emit)
                try:
                    completed=threading.Event()
                    voice.speak('¿En qué te ayudo? Canción, español.', completed=completed);self.assertTrue(finished.wait(3))
                    self.assertTrue(completed.wait(3))
                    deadline=time.monotonic()+2
                    while voice.speaking.is_set() and time.monotonic()<deadline:time.sleep(.01)
                    self.assertIn(('tts_level',0.),events);self.assertFalse(voice.speaking.is_set())
                    self.assertEqual(json.loads(process.stdin.payload)['text'],'¿En qué te ayudo? Canción, español.')
                    self.assertTrue(process.stdin.payload.isascii())
                finally:voice.close();voice.thread.join(2)
                self.assertFalse(voice.thread.is_alive());self.assertTrue(process.stdout.closed)

    def test_sapi_render_and_direct_fallback_use_existing_engine(self):
        payload={'text':'Hola','rate':160,'voice_id':'chosen','language':'es'}
        engine=Mock()
        with patch('pyttsx3.init',return_value=engine):
            speak_sapi(payload,Path('fixture.wav'));engine.save_to_file.assert_called_once_with('Hola','fixture.wav');engine.say.assert_not_called()
            engine.stop.assert_called_once();engine.reset_mock()
            speak_sapi(payload);engine.say.assert_called_once_with('Hola');engine.save_to_file.assert_not_called()
            engine.runAndWait.side_effect=RuntimeError('induced')
            with self.assertRaises(RuntimeError):speak_sapi(payload)
            self.assertEqual(engine.stop.call_count,2)

    def test_microphone_levels_come_from_pcm_fixture_and_reset(self):
        import numpy as np
        from victor.voice.input import VoiceInput
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'voice_mode':'push-to-talk','voice_backend':'whisper'});events=[]
            voice=VoiceInput(cfg,lambda *args:events.append(args),lambda:True)
            voice.transcriber.transcribe=Mock(return_value='transcripción fixture')
            original_emit=voice.emit
            def emit(kind,value):
                original_emit(kind,value)
                if kind=='mic_level' and value:voice.release_event.set()
            voice.emit=emit
            def stream(**kwargs):
                context=Mock();context.__enter__=Mock(side_effect=lambda:kwargs['callback'](np.full((1600,1),3000,dtype=np.int16),1600,None,None));context.__exit__=Mock(return_value=False);return context
            cfg.save({'microphone':'0','voice_noise_reduction':False,'voice_echo_cancellation':False})
            with patch('sounddevice.query_devices',return_value={'max_input_channels':1,'default_samplerate':16000}),patch('sounddevice.check_input_settings'),patch('victor.voice.activity.SpeechDetector.is_voice',return_value=True),patch('sounddevice.InputStream',side_effect=stream):
                self.assertEqual(voice.listen(),'transcripción fixture')
            self.assertEqual([v for k,v in events if k=='mic_level'],[.5,0.])


class UIRepairs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.qt=QApplication.instance() or QApplication([]);cls.qt.setQuitOnLastWindowClosed(False)
    def pump(self,seconds=.1):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:self.qt.processEvents();time.sleep(.005)

    def test_navigation_notices_audio_controls_and_all_responsive_pages(self):
        from victor.gui.app import GUIManager
        from victor.gui.widgets import display_text
        # This test covers Qt navigation/layout. Dedicated fixture tests cover actual browser hosts.
        with tempfile.TemporaryDirectory() as folder,patch('victor.gui.spotify_embed.SpotifyEmbed.start'),patch('victor.gui.whatsapp_embed.WhatsAppEmbed.start'):
            cfg=ConfigManager(Path(folder));app=GUIManager(cfg)
            try:
                app.show();self.pump(.2)
                app.navigate('spotify')
                self.assertEqual(set(app.section_tabs['spotify']),{'spotify','google','telegram','whatsapp','remote'})
                app.section_tabs['spotify']['telegram'].click();self.assertEqual(app.current_page,'telegram')
                app.section_tabs['telegram']['remote'].click();self.assertEqual(app.current_page,'remote')
                for dest in ('remote','google','spotify','ia','personality','windows','files','diagnostics'):
                    app.navigate(dest);self.pump(.02)
                    row=app.section_tabs[dest]
                    self.assertEqual([key for key,b in row.items() if b.isChecked()],[dest])
                    self.assertEqual(sum(b.isChecked() for b in app.nav_buttons.values()),1)
                for provider in app.settings.provider_buttons:
                    app.settings.provider_buttons[provider].click()
                    self.assertEqual([p for p,b in app.settings.provider_buttons.items() if b.isChecked()],[provider])
                    self.assertFalse(app.settings.provider_buttons[provider].icon().isNull())
                cfg.save({'voice_mode':'continua','voice_enabled':False});app.navigate('voice')
                self.assertTrue(app.voice_panel.modes['continua'].isChecked());self.assertFalse(cfg.get('voice_enabled'))
                app.handle_event('voice_status','Escuchando…');app.handle_event('mic_level',.6);app.handle_event('tts_level',.8)
                self.assertEqual(app.voice_panel.input_wave.target,.6);self.assertEqual(app.voice_panel.mic.target,.8)
                app.voice_output.speaking.set();app.handle_event('status','finished')
                self.assertIn('Respondiendo',app.summary_title.text());app.handle_event('done',None)
                self.assertIn('Respondiendo',app.summary_title.text());app.voice_output.speaking.clear()
                app.handle_event('voice_status','Micrófono apagado');app.handle_event('speech_status','Voz en espera')
                self.assertFalse(any(app.voice_panel.input_wave.history));self.assertEqual(app.voice_panel.mic.target,0.)
                app.handle_event('tts_meter',False);self.assertIn('no disponible',app.voice_panel.output_meter.text())
                app.error_label.setText('Primer aviso');app.error_label.start_fade();self.pump(.08)
                app.error_label.setText('Segundo aviso');self.pump(.3)
                self.assertEqual(app.error_label.text(),'Segundo aviso');self.assertEqual(app.error_label.effect.opacity(),1.)
                app.error_label.expiry.start(40);self.pump(.4)
                self.assertTrue(app.error_label.isHidden());self.assertFalse(app.error_label.text())
                self.assertTrue(any('Segundo aviso' in row for row in app.error_label.history))
                self.assertEqual(set(app.window_controls),{'close','minimize','maximize'})
                app.window_controls['maximize'].click();self.pump(.35);self.assertTrue(app.isMaximized())
                app.window_controls['maximize'].click();self.pump(.35);self.assertFalse(app.isMaximized())
                app.window_controls['minimize'].click();self.pump(.35);self.assertTrue(app.isMinimized());app.showNormal()
                app.resize(420,760);self.pump(.3)
                for key,page in app.page_widgets.items():
                    app.navigate(key);self.pump(.04)
                    if hasattr(page,'horizontalScrollBar'):
                        # Lazy web views and queued Qt layout recalculations need an event-loop turn.
                        deadline=time.monotonic()+1
                        while page.horizontalScrollBar().maximum() and time.monotonic()<deadline:self.pump(.02)
                        with self.subTest(page=key):self.assertEqual(page.horizontalScrollBar().maximum(),0)
                self.assertLessEqual(app.width(),440)
                app.resize(1600,900);app.navigate('ia');self.pump(.2)
                self.assertEqual(app.settings.pages['ia'].horizontalScrollBar().maximum(),0)
                from PySide6.QtWidgets import QLabel
                for reading in app.settings.pages['ia'].findChildren(QLabel):
                    if reading.property('slider_readout'):self.assertGreater(reading.width(),0)
                for provider in app.settings.provider_buttons.values():
                    self.assertGreaterEqual(provider.height(),52);self.assertIn('\n',provider.text())
                self.assertIn('cpu: 25',display_text({'cpu':25}).lower())
            finally:
                app.voice_output.speaking.clear();app.close();deadline=time.monotonic()+10
                while not app.closed_cleanly and time.monotonic()<deadline:self.pump(.1)
            self.assertTrue(app.closed_cleanly)


if __name__=='__main__':unittest.main()
