"""Barge-in, reply silence and music lifetime without the owner's audio."""
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import subprocess
import sys
import tempfile
import threading
import time
import unittest

from victor.config import ConfigManager
from victor.errors import VictorError
from victor.voice.input import VoiceInput
from victor.voice.output import VoiceOutput


class InterruptInput(unittest.TestCase):
    def test_busy_voice_accepts_only_wake_then_one_request(self):
        for activation in ('VICTOR', 'VICTOR pausa la canción'):
            with self.subTest(activation=activation), tempfile.TemporaryDirectory() as folder:
                cfg=ConfigManager(Path(folder));cfg.save({'voice_mode':'continua'})
                busy=[True];events=[]
                def emit(k,v):
                    events.append((k,v))
                    if k=='voice_interrupt':busy[0]=False;v.set()
                voice=VoiceInput(cfg,emit,lambda:not busy[0]);voice.can_interrupt=lambda:busy[0]
                phrases=iter(['pausa la canción','charla posterior'] if activation=='VICTOR' else ['charla posterior'])
                def listen():
                    try:return next(phrases)
                    except StopIteration:voice.stop();return ''
                with patch.object(voice,'listen_interrupt',return_value=activation),patch.object(voice,'listen',side_effect=listen):voice._run()
                self.assertEqual([v for k,v in events if k=='voice_text'],['pausa la canción'])
                self.assertEqual(sum(k=='voice_interrupt' for k,v in events),1)
                self.assertEqual(voice.reply_deadline,0)

    def test_interrupt_replaces_inline_request_waiting_for_greeting(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'voice_mode':'continua'})
            events=[];speaking=[False];old=[]
            def emit(k,v):
                events.append((k,v))
                if k=='voice_wake':speaking[0]=True;old.append(v)
                if k=='voice_interrupt':old[0].set();speaking[0]=False;v.set()
            voice=VoiceInput(cfg,emit,lambda:not speaking[0]);voice.can_interrupt=lambda:speaking[0]
            phrases=iter(['VICTOR manda un correo','pausa la canción'])
            def listen():
                try:return next(phrases)
                except StopIteration:voice.stop();return ''
            with patch.object(voice,'listen_interrupt',return_value='VICTOR'),patch.object(voice,'listen',side_effect=listen):voice._run()
            self.assertEqual([v for k,v in events if k=='voice_text'],['pausa la canción'])
            self.assertEqual(sum(k=='voice_interrupt' for k,v in events),1)

    def test_silence_expires_once_and_returns_to_wake(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'voice_mode':'continua'})
            clock=[100.];events=[]
            def emit(k,v):
                events.append((k,v))
                if k=='voice_wake':v.set()
            voice=VoiceInput(cfg,emit,lambda:True)
            phrases=iter([('VICTOR',100.),('',104.),('',109.),('pausa la canción',110.)])
            def listen():
                try:text,clock[0]=next(phrases);return text
                except StopIteration:voice.stop();return ''
            with patch('victor.voice.input.time.monotonic',side_effect=lambda:clock[0]),patch.object(voice,'listen',side_effect=listen):voice._run()
            self.assertEqual(sum(k=='voice_reply_timeout' for k,v in events),1)
            self.assertFalse(any(k=='voice_text' for k,v in events))

    def test_speaking_before_timeout_extends_reply_deadline(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'voice_backend':'whisper'})
            voice=VoiceInput(cfg,Mock(),lambda:True);voice.reply_deadline=108.
            voice.transcriber=Mock();voice.transcriber.transcribe.return_value='una petición larga'
            clock=[100.]
            from victor.voice.capture import AudioPacket
            packets=iter([3000]*15+[0]*12)
            def read():clock[0]+=.4;return AudioPacket(np.full(1600,next(packets),dtype=np.int16),clock[0])
            @contextmanager
            def capture_session(voice):yield SimpleNamespace(read=read)
            with patch('victor.voice.capture.capture_session',capture_session),patch('victor.voice.activity.SpeechDetector.is_voice',side_effect=lambda b:bool(b[0])),patch('victor.voice.input.time.monotonic',side_effect=lambda:clock[0]):
                self.assertEqual(voice.listen(),'una petición larga')
            self.assertGreater(voice.reply_deadline,112.)

    def test_wake_recognition_is_local_even_when_request_backend_is_openai(self):
        import numpy as np
        from victor.voice.transcription import Transcriber
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'voice_backend':'openai'})
            model=Mock();model.transcribe.return_value=([SimpleNamespace(text='VICTOR')],None)
            with patch('faster_whisper.WhisperModel',return_value=model),patch('victor.voice.models.cached_model',return_value='local-fixture'),patch('victor.voice.openai_transcription.transcribe',side_effect=AssertionError('No cloud audio for barge-in')):
                text=Transcriber(cfg).transcribe(np.ones(16000,dtype=np.float32)*.1,threading.Event(),wake_only=True)
            self.assertEqual(text,'VICTOR')
            kw=model.transcribe.call_args.kwargs
            self.assertEqual(kw['beam_size'],3);self.assertIsNone(kw['initial_prompt'])

    def test_rolling_capture_filters_echo_and_keeps_recording_during_inference(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'microphone':'0','voice_noise_reduction':False,'voice_echo_cancellation':False})
            voice=VoiceInput(cfg,Mock(),lambda:False)
            voice.can_interrupt=lambda:True
            voice.is_speech_echo=lambda text:text.startswith('Aquí en VICTOR')
            calls=[];producer_stopped=threading.Event();produced=[0]
            def transcribe(audio,cancel,**kwargs):
                calls.append((len(audio),kwargs))
                # ASR tarda mientras el callback continúa llenando el buffer.
                before=produced[0];time.sleep(.12);self.assertGreater(produced[0],before)
                return ['mi amigo VICTOR llegó','Aquí en VICTOR IA','VICTOR no mandes la voz del altavoz a la IA'][len(calls)-1]
            voice.transcriber.transcribe=transcribe
            def stream(**kwargs):
                class Capture:
                    def __enter__(self):
                        def produce():
                            while not producer_stopped.wait(.01):
                                produced[0]+=1
                                kwargs['callback'](np.full((1600,1),3000,dtype=np.int16),1600,None,None)
                        self.thread=threading.Thread(target=produce);self.thread.start()
                    def __exit__(self,*args):producer_stopped.set();self.thread.join(2)
                return Capture()
            with patch('sounddevice.query_devices',return_value={'max_input_channels':1,'default_samplerate':16000}),patch('sounddevice.check_input_settings'),patch('victor.voice.activity.SpeechDetector.is_voice',return_value=True),patch('sounddevice.InputStream',side_effect=stream):self.assertEqual(voice.listen_interrupt(),'VICTOR')
            self.assertEqual(len(calls),3)
            self.assertTrue(all(kw=={'wake_only':True} for n,kw in calls))
            self.assertTrue(all(12800<=n<=51200 for n,kw in calls))
            self.assertFalse(any(c.args[0]=='voice_text' for c in voice.emit.call_args_list))

    def test_missing_local_wake_model_does_not_end_regular_listener(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'microphone':'0','voice_noise_reduction':False,'voice_echo_cancellation':False})
            events=[];voice=VoiceInput(cfg,lambda *e:events.append(e),lambda:False)
            voice.can_interrupt=lambda:True
            voice.transcriber=Mock();voice.transcriber.transcribe.side_effect=VictorError('missing local model')
            def stream(**kw):
                capture=Mock()
                def enter():
                    for _ in range(12):kw['callback'](np.full((1600,1),3000,dtype=np.int16),1600,None,None)
                capture.__enter__=Mock(side_effect=enter);capture.__exit__=Mock(return_value=False);return capture
            with patch('sounddevice.query_devices',return_value={'max_input_channels':1,'default_samplerate':16000}),patch('sounddevice.check_input_settings'),patch('victor.voice.activity.SpeechDetector.is_voice',return_value=True),patch('sounddevice.InputStream',side_effect=stream):
                self.assertEqual(voice.listen_interrupt(),'');self.assertEqual(voice.listen_interrupt(),'')
            self.assertFalse(voice.stop_event.is_set());self.assertEqual(sum(k=='notice' for k,v in events),1)
            voice.transcriber.transcribe.assert_called_once()


class InterruptOutput(unittest.TestCase):
    def test_own_phrase_is_echo_but_short_user_wake_is_not(self):
        voice=SimpleNamespace(current_text='Lo escuchas aquí en VICTOR.IA. Puedes pedirme otra canción.')
        self.assertTrue(VoiceOutput.is_speech_echo(voice,'aquí en VICTOR IA'))
        self.assertTrue(VoiceOutput.is_speech_echo(voice,'VICTOR IA'))
        self.assertFalse(VoiceOutput.is_speech_echo(voice,'VICTOR'))
        self.assertFalse(VoiceOutput.is_speech_echo(voice,'VICTOR pausa la canción'))

    def test_real_child_and_music_lease_survive_interruption_and_reply_wait(self):
        script='''from victor.voice import output
from victor.voice.levels import report_meter
import time
def synth(payload,path=None):
    if path is not None:path.write_bytes(b'x'*45)
def play(path):
    report_meter('tts_level',.5)
    time.sleep(.4)
output.speak_sapi=synth
output.play_audio=play
output.speak_worker()
'''
        real_popen=subprocess.Popen
        def child(args,**kw):return real_popen([sys.executable,'-c',script],**kw)
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'voice_enabled':True,'tts_backend':'sapi'})
            pcm=threading.Event();restored=threading.Event();begins=[]
            class Ducker:
                @contextmanager
                def hold(self,cancelled):
                    begins.append(1)
                    try:yield True
                    finally:restored.set()
            with patch('victor.voice.output.subprocess.Popen',side_effect=child):
                voice=VoiceOutput(cfg,lambda k,v:pcm.set() if k=='tts_level' and v==.5 else None);voice.music_ducker=Ducker()
                first=threading.Event();second=threading.Event()
                try:
                    voice.begin_interaction();voice.speak('Respuesta larga',completed=first)
                    self.assertTrue(pcm.wait(5));voice.stop(preserve_music=True);pcm.clear()
                    voice.speak('¿En qué te ayudo?',force=True,completed=second)
                    self.assertTrue(first.wait(5));self.assertTrue(second.wait(5))
                    self.assertEqual(begins,[1]);self.assertFalse(restored.wait(.35))
                    voice.end_interaction();self.assertTrue(restored.wait(2))
                    # Cerrar con una espera nueva también libera el volumen.
                    restored.clear();third=threading.Event()
                    voice.begin_interaction();voice.speak('¿En qué te ayudo?',completed=third)
                    self.assertTrue(third.wait(5));self.assertFalse(restored.is_set())
                finally:voice.close();voice.thread.join(5)
                self.assertFalse(voice.thread.is_alive())
                self.assertTrue(restored.is_set())

    def test_gui_interrupt_cancels_old_reply_and_holds_until_timeout(self):
        from victor.gui.app import GUIManager
        app=SimpleNamespace(closing=False,voice_waiting_reply=False,
                            voice_input=SimpleNamespace(stop_event=threading.Event()),
                            voice_panel=Mock(),voice_output=Mock(),core=Mock())
        done=threading.Event();GUIManager.handle_event(app,'voice_interrupt',done)
        app.core.stop.assert_called_once();app.voice_output.stop.assert_called_once_with(preserve_music=True)
        app.voice_output.begin_interaction.assert_called_once();self.assertTrue(app.voice_waiting_reply)
        app.voice_output.speak.assert_called_once_with('¿En qué te ayudo?',force=True,completed=done)
        GUIManager.handle_event(app,'voice_reply_timeout',None)
        app.voice_output.end_interaction.assert_called_once();self.assertFalse(app.voice_waiting_reply)


if __name__=='__main__':unittest.main()
