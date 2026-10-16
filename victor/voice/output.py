"""Lightweight Edge voice with ordered progressive PCM and immediate cancellation."""
import queue
import threading
import time
from victor.config import ROOT
from victor.errors import Cancelled
from victor.voice.edge_client import EdgeTTS,play_pcm
from victor.voice.tts_segments import Sentences

class VoiceOutput:
    def __init__(self,config,emit):
        self.config,self.emit=config,emit
        self.pending=queue.Queue(maxsize=48);self.audio=queue.Queue(maxsize=2)
        self.closing=threading.Event();self.lock=threading.RLock();self.epoch=0
        self.speaking=threading.Event();self.generating=threading.Event();self.playing=threading.Event()
        self.music_ducker=None;self.duck_context=None;self.interaction=threading.Event()
        self.current_text='';self.last_audio_end=0.;self.audio_end_received=False
        self.sentence_chars=240
        self.client=EdgeTTS(getattr(config,'root',ROOT),config);self.stream=Sentences(self.sentence_chars)
        self.stream_open=False;self.stream_enabled=False;self.disabled_until=0.;self.audio_stream=None
        self.thread=threading.Thread(target=self._generate,name='victor-tts-generate',daemon=True)
        self.play_thread=threading.Thread(target=self._play,name='victor-tts-play',daemon=True)
        self.thread.start();self.play_thread.start()
    @property
    def busy(self):return self.speaking.is_set() or self.generating.is_set() or not self.pending.empty() or not self.audio.empty()
    def speak(self,text,settings=None,force=False,completed=None):
        text=text[:7000]
        if not self.closing.is_set() and time.monotonic()>=self.disabled_until and (force or self.config.get('voice_enabled')) and text:
            phrases=Sentences(self.sentence_chars).feed(text,final=True)
            with self.lock:
                if self.pending.qsize()+len(phrases)<=48:
                    for i,phrase in enumerate(phrases):self.pending.put_nowait((phrase,self.epoch,completed if i==len(phrases)-1 else None))
                    self.speaking.set();return True
            self.emit('notice','La cola de voz alcanzó su límite; conserva la respuesta completa en el chat.')
        if completed is not None:completed.set()
        return False
    def begin_stream(self):
        with self.lock:
            self.stream.reset();self.stream_open=True;self.stream_enabled=bool(self.config.get('voice_enabled'))
    def stream_text(self,text):
        with self.lock:
            if not self.stream_open or not self.stream_enabled:return
            if len(self.stream.received)+len(text)>7000:self.stream_enabled=False;return
            for phrase in self.stream.feed(text):self.speak(phrase)
    def finish_stream(self,text):
        with self.lock:
            if not self.stream_open:return self.speak(text)
            self.stream_open=False
            if text.startswith(self.stream.received):
                if self.stream_enabled:
                    suffix=text[len(self.stream.received):]
                    for phrase in self.stream.feed(suffix,final=True):self.speak(phrase)
                return
            self.stop(preserve_music=True);self.speak(text)
    def retry(self):self.disabled_until=0.
    def preload(self):
        if self.config.get('voice_enabled') or self.config.get('voice_mode')=='continua':
            with self.lock:
                if self.pending.empty():self.pending.put_nowait((None,self.epoch,None))
    def begin_interaction(self):self.interaction.set()
    def end_interaction(self):self.interaction.clear()
    def is_speech_echo(self,text):
        import re,unicodedata
        from difflib import SequenceMatcher
        def words(value):return re.findall(r'\w+',''.join(c for c in unicodedata.normalize('NFD',value.casefold()) if not unicodedata.combining(c)))
        heard,spoken=words(text),words(self.current_text)
        if len(heard)<2 or not spoken:return False
        return any(SequenceMatcher(None,' '.join(heard),' '.join(spoken[i:i+len(heard)])).ratio()>=.85 for i in range(len(spoken)))
    def stop(self,preserve_music=False):
        with self.lock:
            self.epoch+=1;self.stream_open=False
            if not preserve_music:self.end_interaction()
            for channel in (self.pending,self.audio):
                while True:
                    try:
                        item=channel.get_nowait()
                        if channel is self.audio:self.client.release_audio(item[0])
                        if item[-1] is not None:item[-1].set()
                    except queue.Empty:break
            self.client.stop()
            if self.audio_stream is not None:
                try:self.audio_stream.abort()
                except Exception:pass
            self._idle()
    def close(self):
        self.closing.set();self.stop()
        def cleanup():
            self.thread.join(5);self.play_thread.join(5);self.client.close()
        threading.Thread(target=cleanup,name='victor-tts-close',daemon=True).start()
    def _put_audio(self,item,epoch):
        while not self.closing.is_set() and epoch==self.epoch:
            try:self.audio.put(item,timeout=.05);return True
            except queue.Full:continue
        if item[-1] is not None:item[-1].set()
        self.client.release_audio(item[0])
        return False
    def _generate(self):
        while not self.closing.is_set():
            try:text,epoch,completed=self.pending.get(timeout=.1)
            except queue.Empty:continue
            if epoch!=self.epoch:
                if completed is not None:completed.set()
                continue
            self.generating.set();self.emit('speech_status','Preparando voz…')
            try:
                packet=self.client.request(text or '',lambda:self.closing.is_set() or epoch!=self.epoch,warm=text is None)
                if text is not None:self._put_audio((packet['path'],text,epoch,completed),epoch)
            except Cancelled:
                if completed is not None:completed.set()
            except Exception as exc:
                if epoch==self.epoch and not self.closing.is_set():
                    self.disabled_until=time.monotonic()+5;self.emit('error','Voz no disponible: '+str(exc)[:500]);self.stop(preserve_music=True)
                if completed is not None:completed.set()
            finally:self.generating.clear();self._idle()
    def _idle(self):
        if self.pending.empty() and self.audio.empty() and not self.generating.is_set() and not self.playing.is_set():
            self.speaking.clear();self.emit('speech_status','Voz en espera')
    def _play(self):
        while not self.closing.is_set():
            try:path,text,epoch,completed=self.audio.get(timeout=.1)
            except queue.Empty:
                if not self.interaction.is_set() and not self.busy:self._release_music()
                continue
            if epoch!=self.epoch:
                if completed is not None:completed.set()
                self.client.release_audio(path)
                continue
            self.playing.set();self.current_text=text;self.speaking.set()
            try:
                self._hold_music(epoch)
                if epoch!=self.epoch:raise Cancelled()
                def stream(value):self.audio_stream=value
                play_pcm(path,lambda:self.closing.is_set() or epoch!=self.epoch,self.emit,stream)
            except Cancelled:pass
            except Exception as exc:
                if epoch==self.epoch and not self.closing.is_set():self.emit('error','No pude reproducir la voz: '+str(exc)[:200]);self.stop(preserve_music=True)
            finally:
                self.last_audio_end=time.perf_counter();self.audio_end_received=True;self.playing.clear();self.emit('tts_level',0.)
                if completed is not None:completed.set()
                self.client.release_audio(path)
                self._idle()
        self._release_music()
    def _hold_music(self,epoch):
        if self.music_ducker and self.duck_context is None:
            context=self.music_ducker.hold(lambda:self.closing.is_set() or epoch!=self.epoch)
            if context.__enter__():self.duck_context=context
            else:context.__exit__(None,None,None)
    def _release_music(self):
        if self.duck_context:
            context,self.duck_context=self.duck_context,None
            try:context.__exit__(None,None,None)
            except Exception:self.emit('notice','No se pudo restaurar el volumen de música.')

def speak_worker():
    """Compatibility entry uses Edge; normal playback needs no child process."""
    import json,sys
    payload=json.loads(sys.stdin.buffer.readline().decode('utf-8'))
    class Config:
        root=ROOT
        def get(self,key):
            from victor.config import DEFAULTS
            return True if key=='voice_enabled' else DEFAULTS[key]
    done=threading.Event();output=VoiceOutput(Config(),lambda kind,value:None)
    try:output.speak(payload.get('text',''),force=True,completed=done);done.wait(180)
    finally:output.close()
