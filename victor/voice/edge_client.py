"""Bounded MP3→PCM streaming; one small persistent network thread, no TTS model."""
import asyncio
import concurrent.futures
from collections import OrderedDict
import queue
import threading
import time
import hashlib
import json
from pathlib import Path
from .normalizer import SpanishSpeechNormalizer
from victor.errors import Cancelled

class Audio:
    def __init__(self,cancelled):
        self.blocks=queue.Queue(maxsize=12);self.cancelled=cancelled;self.future=None
        self.started=time.perf_counter();self.first_pcm=None;self.first_play=None;self.end=None
        self.error=None;self.finished=threading.Event();self.bytes=0

class EdgeTTS:
    def __init__(self,root,config=None):
        self.config=config;self.closed=False;self.lock=threading.RLock();self.active=set()
        self.cache_directory=Path(root)/'data/voice_cache'
        self.cache=OrderedDict();self.cache_bytes=0;self.loop=asyncio.new_event_loop()
        self.ready=threading.Event();self.thread=threading.Thread(target=self._run,name='victor-edge-network',daemon=True);self.thread.start();self.ready.wait(2)
    def _run(self):
        # At most the current phrase plus one prefetched phrase. Playback stays ordered.
        asyncio.set_event_loop(self.loop);self.semaphore=asyncio.Semaphore(2);self.ready.set();self.loop.run_forever()
        tasks=asyncio.all_tasks(self.loop)
        for task in tasks:task.cancel()
        self.loop.run_until_complete(asyncio.gather(*tasks,return_exceptions=True))
        self.loop.run_until_complete(asyncio.sleep(.25));self.loop.close()
    def settings(self):
        def get(key,default):
            try:return self.config.get(key) if self.config else default
            except (KeyError,AttributeError):return default
        return (get('edge_voice','es-EC-LuisNeural') or 'es-EC-LuisNeural',
                f"{max(-50,min(80,round((get('voice_rate',180)/175-1)*100))):+d}%",get('voice_pitch','+0Hz'))
    def request(self,text,cancelled=lambda:False,warm=False):
        if self.closed or cancelled():raise Cancelled()
        if warm:text='¿En qué te ayudo?'
        try:dictionary=self.config.get('speech_dictionary') if self.config else {}
        except (KeyError,AttributeError):dictionary={}
        normalized=SpanishSpeechNormalizer(dictionary).normalize(text)
        voice,rate,pitch=self.settings();key=(normalized,voice,rate,pitch)
        audio=Audio(cancelled)
        with self.lock:self.active.add(audio)
        audio.future=asyncio.run_coroutine_threadsafe(self._synthesize(audio,key,warm),self.loop)
        if warm:
            while not audio.finished.wait(.02):
                if cancelled():audio.future.cancel();raise Cancelled()
            self.release_audio(audio)
            if audio.error:raise audio.error
        return {'path':audio}
    async def _put(self,audio,block,warm):
        if not block:return
        if audio.cancelled() or self.closed:raise asyncio.CancelledError()
        if audio.first_pcm is None:audio.first_pcm=time.perf_counter()
        audio.bytes+=len(block)
        if warm:return
        while True:
            if audio.cancelled() or self.closed:raise asyncio.CancelledError()
            try:audio.blocks.put_nowait(block);return
            except queue.Full:await asyncio.sleep(.01)
    async def _synthesize(self,audio,key,warm):
        try:
            import av
            import edge_tts
            async with self.semaphore:
                with self.lock:cached=self.cache.get(key)
                cache_file=self.cache_directory/(hashlib.sha256(json.dumps(key,ensure_ascii=False).encode()).hexdigest()+'.pcm')
                if cached is None and key[0]=='¿En qué te ayudo?' and cache_file.is_file():
                    # This is generated public greeting audio, never chat or microphone data.
                    if 0<cache_file.stat().st_size<=256*1024:
                        data=cache_file.read_bytes()
                        if len(data)%2==0:cached=tuple(data[i:i+9600] for i in range(0,len(data),9600))
                if cached is not None:
                    for block in cached:await self._put(audio,block,warm)
                    return
                # Retry only before any PCM is exposed; never duplicate an audible prefix.
                for attempt in range(2):
                    decoder=av.CodecContext.create('mp3','r');resampler=av.AudioResampler(format='s16',layout='mono',rate=24000)
                    bank=[];size=0
                    async def frames(packet):
                        nonlocal size
                        for frame in decoder.decode(packet):
                            for pcm in resampler.resample(frame):
                                data=pcm.to_ndarray().tobytes();await self._put(audio,data,warm)
                                if size<=1024**2:bank.append(data);size+=len(data)
                    try:
                        async with asyncio.timeout(35):
                            async for event in edge_tts.Communicate(key[0],key[1],rate=key[2],pitch=key[3],connect_timeout=5,receive_timeout=12).stream():
                                if audio.cancelled():raise asyncio.CancelledError()
                                if event['type']=='audio':
                                    for packet in decoder.parse(event['data']):await frames(packet)
                            for packet in decoder.parse(b''):await frames(packet)
                            await frames(None)
                            for pcm in resampler.resample(None):
                                data=pcm.to_ndarray().tobytes();await self._put(audio,data,warm)
                                if size<=1024**2:bank.append(data);size+=len(data)
                        if not audio.bytes:raise RuntimeError('Edge no devolvió audio decodificable.')
                        if size<=1024**2:
                            with self.lock:
                                self.cache[key]=tuple(bank);self.cache_bytes+=size
                                while len(self.cache)>8 or self.cache_bytes>2*1024**2:
                                    _,old=self.cache.popitem(last=False);self.cache_bytes-=sum(map(len,old))
                            if key[0]=='¿En qué te ayudo?' and size<=256*1024:
                                try:
                                    self.cache_directory.mkdir(parents=True,exist_ok=True)
                                    temporary=cache_file.with_suffix('.tmp');temporary.write_bytes(b''.join(bank));temporary.replace(cache_file)
                                    for old in sorted(self.cache_directory.glob('*.pcm'),key=lambda p:p.stat().st_mtime,reverse=True)[8:]:old.unlink()
                                except OSError:pass  # Disk cache failure must not prevent speech.
                        break
                    except asyncio.CancelledError:raise
                    except Exception:
                        if attempt or audio.bytes:raise
                        await asyncio.sleep(.1)
        except asyncio.CancelledError:audio.error=Cancelled()
        except Exception as exc:audio.error=RuntimeError('Edge TTS no disponible. Comprueba Internet. '+type(exc).__name__)
        finally:audio.end=time.perf_counter();audio.finished.set()
    def release_audio(self,audio):
        if not isinstance(audio,Audio):return
        if audio.future and not audio.finished.is_set():audio.future.cancel()
        with self.lock:self.active.discard(audio)
    def stop(self):
        with self.lock:active=list(self.active)
        for audio in active:
            if audio.future:audio.future.cancel()
    def close(self):
        self.closed=True;self.stop()
        with self.lock:self.cache.clear();self.cache_bytes=0
        if self.loop.is_running():self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(2)

def play_pcm(audio,cancelled,emit,on_stream=lambda stream:None):
    import sounddevice as sd
    import numpy as np
    first=None;last_meter=0.
    with sd.RawOutputStream(samplerate=24000,channels=1,dtype='int16',blocksize=960,latency='low') as stream:
        on_stream(stream);emit('tts_meter',True)
        try:
            while True:
                if cancelled():stream.abort();raise Cancelled()
                try:block=audio.blocks.get(timeout=.02)
                except queue.Empty:
                    if audio.finished.is_set():
                        if audio.error:raise audio.error
                        break
                    continue
                stream.write(block)
                now=time.perf_counter()
                if first is None:
                    first=now;audio.first_play=now;emit('speech_status','Hablando…')
                    import logging
                    logging.getLogger('victor.voice').info('edge first_audio_seconds=%.3f',now-audio.started)
                if now-last_meter>=.05:
                    values=np.frombuffer(block,dtype='<i2').astype(np.float32)/32768
                    emit('tts_level',min(1.,float(np.sqrt(np.mean(values*values)))*4));last_meter=now
        finally:on_stream(None);emit('tts_level',0.)
    return first
