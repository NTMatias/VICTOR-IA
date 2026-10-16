"""No real model, accounts, microphone or speaker used by these tests."""
import os
import queue
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from victor.voice.tts_segments import Sentences
from victor.errors import Cancelled

class SegmentationTests(unittest.TestCase):
    def test_incremental_and_final_do_not_duplicate(self):
        parser=Sentences();output=[]
        for token in ['Hola, soy Víctor. ','¿En qué ', 'te ayudo?']:
            output+=parser.feed(token)
        output+=parser.feed('',final=True)
        self.assertEqual(' '.join(output),'Hola, soy Víctor. ¿En qué te ayudo?')
    def test_decimals_and_abbreviations(self):
        parser=Sentences()
        values=parser.feed('El Dr. Pérez confirmó el valor de 3.14 para este ejemplo. Otra oración.',final=True)
        self.assertIn('Dr. Pérez',' '.join(values));self.assertIn('3.14',values[0])
    def test_fenced_code_is_not_spoken(self):
        parser=Sentences()
        values=parser.feed('Una explicación. ```python\nsecret = 3\n``` Y la conclusión.',final=True)
        self.assertNotIn('secret',' '.join(values));self.assertIn('conclusión',' '.join(values))
    def test_long_text_keeps_all_words(self):
        text='palabra '*200
        values=Sentences().feed(text,final=True)
        self.assertEqual(' '.join(values),text.strip());self.assertLessEqual(max(map(len,values)),180)
    def test_long_sentence_is_split_before_worker_limit(self):
        text=('Una frase bastante larga '*35).strip()+'.'
        values=Sentences().feed(text,final=True)
        self.assertEqual(' '.join(values),text);self.assertLessEqual(max(map(len,values)),180)

class FakeClient:
    def __init__(self,root,config=None):self.calls=[];self.stops=0;self.closed=False
    def request(self,text,cancelled,warm=False):
        self.calls.append(text)
        for _ in range(4):
            if cancelled():raise Cancelled('test cancel')
            time.sleep(.005)
        return {'path':'synthetic.wav'}
    def stop(self):self.stops+=1
    def close(self):self.closed=True
    def release_audio(self,path):pass

class PipelineTests(unittest.TestCase):
    def test_final_suffix_does_not_replay_streamed_prefix(self):
        def play(*args):pass
        with patch('victor.voice.output.play_pcm',play):
            output=self.make_output(play);output.begin_stream()
            output.stream_text('Una respuesta clara. ')
            output.finish_stream('Una respuesta clara. Esta es la última frase.')
            self.wait_idle(output)
            self.assertEqual(' '.join(output.client.calls),'Una respuesta clara. Esta es la última frase.')
    def test_old_cancelled_text_does_not_stop_generation_thread(self):
        done=threading.Event()
        def play(*args):pass
        with patch('victor.voice.output.play_pcm',play):
            output=self.make_output(play)
            output.pending.put(('Texto descartado',output.epoch-1,None))
            output.speak('Esta respuesta debe poder reproducirse.',completed=done)
            self.assertTrue(done.wait(1));self.assertTrue(output.thread.is_alive())
    def make_output(self,play):
        from victor.voice.output import VoiceOutput
        config=SimpleNamespace(root=Path(tempfile.gettempdir()),get=lambda key:True)
        self.events=[]
        with patch('victor.voice.output.EdgeTTS',FakeClient),patch('victor.voice.output.play_pcm',play):
            output=VoiceOutput(config,lambda *event:self.events.append(event))
        self.addCleanup(output.close);return output
    def wait_idle(self,output):
        deadline=time.monotonic()+2
        while output.busy and time.monotonic()<deadline:time.sleep(.01)
        self.assertFalse(output.busy)
    def test_stream_completion_and_persistent_idle(self):
        played=[]
        def play(path,cancelled,emit,on_stream):played.append(path);return time.perf_counter()
        with patch('victor.voice.output.play_pcm',play):
            output=self.make_output(play);output.begin_stream()
            text='Hola, soy Víctor y estoy aquí para ayudarte. Una segunda frase clara.'
            output.stream_text(text);output.finish_stream(text);self.wait_idle(output)
            self.assertEqual(' '.join(output.client.calls),text)
            self.assertEqual(len(played),len(output.client.calls))
            output.stop();self.assertEqual(output.client.stops,1);self.assertTrue(output.thread.is_alive())
    def test_stop_discards_pending_audio_and_completes_waiter(self):
        entered=threading.Event();done=threading.Event()
        def play(path,cancelled,emit,on_stream):
            entered.set()
            while not cancelled():time.sleep(.005)
            raise Cancelled('test')
        with patch('victor.voice.output.play_pcm',play):
            output=self.make_output(play);output.speak('Una respuesta que está sonando. Otra frase pendiente.',completed=done)
            self.assertTrue(entered.wait(1));started=time.monotonic();output.stop()
            self.assertLess(time.monotonic()-started,.1);self.assertTrue(done.wait(1));self.wait_idle(output)
            self.assertTrue(output.audio.empty());self.assertTrue(output.pending.empty())
    def test_failure_is_visible_without_fallback(self):
        def play(*args):self.fail('No audio on synthesis failure')
        with patch('victor.voice.output.play_pcm',play):
            output=self.make_output(play)
            output.client.request=lambda *args:(_ for _ in ()).throw(RuntimeError('No model installed'))
            done=threading.Event();output.speak('Hola, soy Víctor.',completed=done)
            self.assertTrue(done.wait(1));self.wait_idle(output)
            self.assertTrue(any(event[0]=='error' for event in self.events));self.assertGreater(output.disabled_until,time.monotonic())
    def test_music_waits_for_fade_and_remains_low_during_reply_window(self):
        from contextlib import contextmanager
        fading=threading.Event();ready=threading.Event();restored=threading.Event();played=threading.Event();done=threading.Event()
        class Ducker:
            @contextmanager
            def hold(self,cancelled):
                fading.set()
                while not ready.wait(.005):
                    if cancelled():raise Cancelled('cancel during fade')
                try:yield True
                finally:restored.set()
        def play(path,cancelled,emit,on_stream):played.set()
        with patch('victor.voice.output.play_pcm',play):
            output=self.make_output(play);output.music_ducker=Ducker();output.begin_interaction()
            output.speak('¿En qué te ayudo?',completed=done)
            self.assertTrue(fading.wait(1));self.assertFalse(played.is_set())
            ready.set();self.assertTrue(done.wait(1));self.wait_idle(output)
            self.assertTrue(played.is_set());self.assertFalse(restored.wait(.15))
            output.end_interaction();self.assertTrue(restored.wait(1))
    def test_successive_turns_do_not_leave_pending_audio(self):
        played=[]
        def play(path,cancelled,emit,on_stream):played.append(path)
        with patch('victor.voice.output.play_pcm',play):
            output=self.make_output(play)
            for i in range(12):
                done=threading.Event();output.speak(f'Esta es la respuesta número {i}.',completed=done)
                self.assertTrue(done.wait(1));self.wait_idle(output)
            self.assertEqual(len(played),12);self.assertEqual(output.client.stops,0)
            self.assertTrue(output.audio.empty());self.assertTrue(output.pending.empty())

if __name__=='__main__':unittest.main()
