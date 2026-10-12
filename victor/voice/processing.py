"""Local WebRTC AEC3 + noise suppression; WASAPI reference stays in RAM."""
from collections import deque
import logging
import math
import queue
import threading
import time
import numpy as np


def packet_end(timing, count, rate, now=None):
    now=time.perf_counter() if now is None else now
    try:
        current=timing['current_time'] if isinstance(timing,dict) else timing.currentTime
        adc=timing['input_buffer_adc_time'] if isinstance(timing,dict) else timing.inputBufferAdcTime
        value=now+float(adc)-float(current)+count/rate
        return value if math.isfinite(value) and abs(value-now)<1 else now
    except (TypeError,KeyError,AttributeError,ValueError):return now


class LoopbackReference:
    def __init__(self):
        self.lock=threading.Lock();self.chunks=deque();self.stopped=threading.Event()
        self.ready=False;self.generation=0;self.thread=None;self.error=None

    def start(self):
        if self.thread is None:
            self.thread=threading.Thread(target=self._run,name='victor-echo-reference',daemon=True);self.thread.start()

    def append(self, pcm, end):
        with self.lock:
            self.chunks.append((end-len(pcm)/16000.,end,np.asarray(pcm,dtype=np.int16).copy()))
            while self.chunks and self.chunks[0][1]<end-8:self.chunks.popleft()

    def window(self, end, count):
        start=end-count/16000.;out=np.zeros(count,dtype=np.int16)
        with self.lock:chunks=[p for p in self.chunks if p[1]>=start and p[0]<end]
        for first,last,pcm in chunks:
            offset=round((first-start)*16000);left=max(0,offset);right=min(count,offset+len(pcm))
            if right>left:out[left:right]=pcm[left-offset:right-offset]
        return out

    @staticmethod
    def default_identity():
        try:
            from pycaw.pycaw import AudioUtilities
            return AudioUtilities.GetSpeakers().id
        except Exception:return None

    def _run(self):
        manager=None;stream=None;com_ready=False;failures=0
        try:
            import pyaudiowpatch as pa
            import av
            try:
                import pythoncom
                pythoncom.CoInitialize();com_ready=True
            except ImportError:pass
            while not self.stopped.is_set():
                frames=queue.Queue(maxsize=128)
                try:
                    manager=pa.PyAudio();device=manager.get_default_wasapi_loopback()
                    rate=int(device['defaultSampleRate']);channels=int(device['maxInputChannels'])
                    identity=self.default_identity();last_check=time.perf_counter()
                    resampler=av.AudioResampler(format='s16',layout='mono',rate=16000)
                    source_seconds=out_seconds=0.
                    def callback(data,count,timing,status):
                        value=(data,packet_end(timing,count,rate),bool(status))
                        try:frames.put_nowait(value)
                        except queue.Full:
                            try:frames.get_nowait()
                            except queue.Empty:pass
                            try:frames.put_nowait((data,value[1],True))
                            except queue.Full:pass
                        return (None,pa.paComplete if self.stopped.is_set() else pa.paContinue)
                    stream=manager.open(format=pa.paInt16,channels=channels,rate=rate,input=True,
                                        input_device_index=device['index'],frames_per_buffer=rate//100,
                                        stream_callback=callback,start=False)
                    with self.lock:self.chunks.clear();self.generation+=1
                    stream.start_stream();self.ready=True;self.error=None;failures=0
                    while not self.stopped.is_set():
                        if time.perf_counter()-last_check>=2:
                            last_check=time.perf_counter();new_identity=self.default_identity()
                            if new_identity!=identity or not stream.is_active():break
                        try:data,end,gap=frames.get(timeout=.1)
                        except queue.Empty:continue
                        if gap:
                            resampler=av.AudioResampler(format='s16',layout='mono',rate=16000)
                            source_seconds=out_seconds=0.
                            with self.lock:self.chunks.clear();self.generation+=1
                        pcm=np.frombuffer(data,dtype='<i2').reshape(-1,channels)
                        mono=np.rint(pcm.astype(np.float32).mean(axis=1)).astype(np.int16)
                        frame=av.AudioFrame.from_ndarray(mono.reshape(1,-1),format='s16',layout='mono');frame.sample_rate=rate
                        chunks=[f.to_ndarray().flatten() for f in resampler.resample(frame)]
                        source_seconds+=len(mono)/rate
                        if chunks:
                            samples=np.concatenate(chunks);out_seconds+=len(samples)/16000.
                            self.append(samples,end-max(0.,source_seconds-out_seconds))
                except Exception as exc:
                    kind=type(exc).__name__
                    if kind!=self.error:logging.getLogger('victor.voice').warning('echo_reference unavailable type=%s',kind)
                    self.error=kind;failures+=1
                finally:
                    self.ready=False
                    if stream:
                        try:stream.stop_stream();stream.close()
                        except Exception:pass
                        stream=None
                    if manager:
                        try:manager.terminate()
                        except Exception:pass
                        manager=None
                if self.stopped.wait(min(8.,.5*2**min(failures,4))):break
        except ImportError as exc:self.error=type(exc).__name__
        finally:
            self.ready=False
            if com_ready:pythoncom.CoUninitialize()

    def close(self):
        self.stopped.set()
        if self.thread:self.thread.join(2)
        with self.lock:self.chunks.clear()


class AudioCleaner:
    def __init__(self, config, emit=lambda *args:None, reference=None):
        self.config,self.emit=config,emit
        self.reference=reference
        self.processor=None;self.signature=None;self.partial=np.empty(0,dtype=np.int16)
        self.last_status=None;self.unavailable=False

    def reset(self):
        self.partial=np.empty(0,dtype=np.int16)
        if self.processor:self.processor.reset()

    def process(self, pcm, end):
        noise=self.config.get('voice_noise_reduction');echo=self.config.get('voice_echo_cancellation')
        level={'suave':0,'moderado':1,'intenso':2}[self.config.get('voice_noise_level')]
        if echo and self.reference is None:self.reference=LoopbackReference();self.reference.start()
        if not echo and self.reference:self.reference.close();self.reference=None
        ready=bool(echo and self.reference and self.reference.ready)
        generation=self.reference.generation if self.reference else 0
        signature=(noise,echo,ready,level,generation)
        if signature!=self.signature:
            self.signature=signature;self.partial=np.empty(0,dtype=np.int16)
            try:
                from pywebrtc_audio import AudioProcessor
                self.processor=AudioProcessor(sample_rate=16000,echo_cancellation=ready,
                    noise_suppression=noise,high_pass_filter=noise or ready,
                    auto_gain_control=False,ns_level=level,stream_delay_ms=0) if noise or ready else None
                self.unavailable=False
            except (ImportError,RuntimeError):self.processor=None;self.unavailable=True
        status=('Limpieza no disponible · ejecuta instalar.bat' if self.unavailable else
                ('Ruido reducido' if noise else 'Reducción de ruido desactivada')+
                (' · Eco activo' if ready else ' · Eco sin sonido de referencia disponible' if echo and self.reference.error else ' · Eco preparando sonido de referencia' if echo else ' · Eco desactivado'))
        if status!=self.last_status:self.emit('voice_audio_status',status);self.last_status=status
        if self.processor is None:return pcm,end
        combined=np.concatenate((self.partial,pcm));count=len(combined)//160*160
        self.partial=combined[count:].copy()
        if not count:return np.empty(0,dtype=np.int16),end
        clean_end=end-len(self.partial)/16000.
        far=self.reference.window(clean_end,count) if ready else None
        # Solo bloques completos de 10 ms; el wrapper rellenaría cada fragmento
        # parcial con ceros, rompiendo la continuidad del filtro de eco.
        return self.processor.process(combined[:count],far),clean_end

    def close(self):
        if self.reference:self.reference.close();self.reference=None
        self.processor=None;self.partial=np.empty(0,dtype=np.int16)
        self.signature=None;self.last_status=None
