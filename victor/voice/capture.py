"""One microphone stream, bounded buffers and native-rate fallback."""
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass
import queue
import time
import os
import numpy as np
from victor.errors import VictorError
from victor.voice.processing import AudioCleaner, packet_end


class MicrophoneError(VictorError):
    pass


@dataclass
class AudioPacket:
    samples: np.ndarray
    end: float
    gap: bool = False


class MicrophoneCapture:
    def __init__(self, config, emit=lambda *args:None):
        self.config=config
        self.cleaner=AudioCleaner(config,emit)
        self.frames=queue.Queue(maxsize=512)
        self.history=deque()
        self.replay=deque()
        self.history_samples=0
        self.stream=None
        self.rate=16000
        self.resampler=None
        self.source_seconds=0.;self.output_seconds=0.
        self.cutoff=0.
        self.last_callback=time.perf_counter()
        self.dropped=False
        self.default_key=None;self.last_default_check=0.;self.com_ready=False

    @staticmethod
    def default_microphone():
        try:
            from pycaw.pycaw import AudioUtilities
            current=AudioUtilities.CreateDevice(AudioUtilities.GetMicrophone())
            return current.id,current.FriendlyName
        except Exception:return None,None

    def choose_default(self, sd):
        if os.name!='nt':return None
        try:
            import pythoncom
            pythoncom.CoInitialize();self.com_ready=True
        except ImportError:return None
        key,name=self.default_microphone();self.default_key=key
        if not key:return None
        devices=sd.query_devices();hosts=sd.query_hostapis()
        matches=[i for i,d in enumerate(devices) if d['max_input_channels'] and d['name']==name]
        wasapi=[i for i in matches if 'WASAPI' in hosts[devices[i]['hostapi']]['name']]
        if wasapi:return wasapi[0]
        if matches:return matches[0]
        raise MicrophoneError('El micrófono predeterminado de Windows no aparece en el controlador de audio. Reinicia VICTOR después de conectar el nuevo dispositivo.')

    def open(self):
        if self.stream is not None:return self
        import sounddevice as sd
        value=self.config.get('microphone').strip()
        try:device=int(value) if value else None
        except ValueError:raise MicrophoneError('El micrófono seleccionado no es válido. Elige un dispositivo en Ajustes → Voz.') from None
        try:
            if not value:device=self.choose_default(sd)
            info=sd.query_devices(device, 'input')
            if info['max_input_channels']<1:raise MicrophoneError('No hay micrófono de entrada disponible en el dispositivo seleccionado. Revisa Ajustes → Voz o usa notas de voz por Telegram.')
            channels=1
            rates=list(dict.fromkeys([16000,int(info['default_samplerate'])]))
            selected=None
            for rate in rates:
                for count in dict.fromkeys((1,min(2,info['max_input_channels']))):
                    try:sd.check_input_settings(device=device,channels=count,dtype='int16',samplerate=rate)
                    except sd.PortAudioError:continue
                    selected=(rate,count);break
                if selected:break
            if selected is None:raise MicrophoneError('El micrófono no admite los formatos de captura. Revisa el dispositivo y su controlador en Ajustes → Voz.')
            self.rate,channels=selected
            self.last_callback=time.perf_counter()
            self.last_default_check=time.perf_counter()
            self.stream=sd.InputStream(samplerate=self.rate,channels=channels,dtype='int16',blocksize=0,
                                       latency='low',device=device,callback=self.callback)
            self.stream.__enter__()
            return self
        except MicrophoneError:
            self.close();raise
        except (sd.PortAudioError,ValueError,KeyError,IndexError):
            self.close()
            raise MicrophoneError('No pude abrir el micrófono seleccionado. Revisa permisos, dispositivo y uso exclusivo por otra aplicación.') from None

    def callback(self,data,count,timing,status):
        # Solo copiar/enqueue: no inferencia, GUI ni acceso al dispositivo aquí.
        now=time.perf_counter();self.last_callback=now
        stamp=packet_end(timing,count,self.rate,now)
        gap=self.dropped or bool(status and getattr(status,'input_overflow',False))
        try:self.frames.put_nowait((data.copy(),stamp,gap));self.dropped=False
        except queue.Full:
            try:self.frames.get_nowait()
            except queue.Empty:pass
            self.dropped=True
            try:self.frames.put_nowait((data.copy(),stamp,True))
            except queue.Full:pass

    def _convert(self, data):
        if data.ndim==2:
            data=data[:,0] if data.shape[1]==1 else np.rint(data.astype(np.float32).mean(axis=1)).astype(np.int16)
        data=np.ascontiguousarray(data,dtype=np.int16)
        if self.rate==16000:return data
        import av
        if self.resampler is None:self.resampler=av.AudioResampler(format='s16',layout='mono',rate=16000)
        frame=av.AudioFrame.from_ndarray(data.reshape(1,-1),format='s16',layout='mono');frame.sample_rate=self.rate
        chunks=[f.to_ndarray().flatten() for f in self.resampler.resample(frame)]
        self.source_seconds+=len(data)/self.rate
        result=np.concatenate(chunks) if chunks else np.empty(0,dtype=np.int16)
        self.output_seconds+=len(result)/16000.
        return result

    def begin_phase(self, after=None, replay=False):
        self.cutoff=time.perf_counter() if after is None else after
        self.replay=deque(p for p in self.history if p.end>=self.cutoff) if replay else deque()

    def read(self, timeout=.15):
        if self.default_key and time.perf_counter()-self.last_default_check>1:
            self.last_default_check=time.perf_counter()
            key,_=self.default_microphone()
            if key!=self.default_key:raise MicrophoneError('Cambió el micrófono predeterminado. Reconectando sin ejecutar una captura incompleta.')
        if self.replay:return self.replay.popleft()
        deadline=time.perf_counter()+timeout;stale=False
        while time.perf_counter()<deadline:
            try:data,stamp,gap=self.frames.get(timeout=max(.001,deadline-time.perf_counter()))
            except queue.Empty:
                if time.perf_counter()-self.last_callback>2:
                    raise MicrophoneError('El micrófono dejó de entregar audio. Revisa conexión y dispositivo en Ajustes → Voz.')
                return None
            if stamp<self.cutoff:continue
            if time.perf_counter()-stamp>6:stale=True;continue
            gap=gap or stale
            if gap:self.resampler=None;self.source_seconds=self.output_seconds=0.;self.cleaner.reset()
            samples=self._convert(data)
            if not samples.size:continue
            if self.rate!=16000:stamp-=max(0.,self.source_seconds-self.output_seconds)
            samples,stamp=self.cleaner.process(samples,stamp)
            if not samples.size:continue
            packet=AudioPacket(samples,stamp,gap)
            self.history.append(packet);self.history_samples+=len(samples)
            while self.history_samples>16000*8 and len(self.history)>1:
                self.history_samples-=len(self.history.popleft().samples)
            return packet
        return None

    def close(self):
        stream,self.stream=self.stream,None
        if stream is not None:
            try:stream.__exit__(None,None,None)
            except Exception:pass
        self.resampler=None;self.history.clear();self.replay.clear();self.history_samples=0
        self.source_seconds=self.output_seconds=0.
        self.cleaner.close()
        self.default_key=None
        if self.com_ready:
            import pythoncom
            pythoncom.CoUninitialize();self.com_ready=False
        while not self.frames.empty():
            try:self.frames.get_nowait()
            except queue.Empty:break


@contextmanager
def capture_session(voice):
    if voice.capture is None:voice.capture=MicrophoneCapture(voice.config,voice.emit)
    capture=voice.capture.open()
    try:yield capture
    finally:
        if not voice.keep_capture:
            capture.close();voice.capture=None
