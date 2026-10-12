"""Whisper local u OpenAI para micrófono y notas de voz autorizadas."""
import os
import threading
import time
import logging
from pathlib import Path
from victor.errors import VictorError, check_cancel


class Transcriber:
    def __init__(self, config):
        self.config = config
        self.lock = threading.Lock()
        self.model = None
        self.model_name = ""

    def transcribe(self, audio, cancel, wake_only=False):
        check_cancel(cancel)
        if not wake_only and self.config.get('voice_backend') == 'openai':
            from victor.voice.openai_transcription import transcribe
            return transcribe(audio, self.config, cancel)
        import numpy as np
        audio=np.asarray(audio,dtype=np.float32)
        if audio.ndim!=1 or not np.isfinite(audio).all() or len(audio)>16000*60:
            raise VictorError('El audio de voz no es válido o supera 60 segundos.')
        if not audio.size or np.max(np.abs(audio))<1e-5:return ''
        started=time.monotonic()
        while not self.lock.acquire(timeout=.2):
            check_cancel(cancel)
        try:
            check_cancel(cancel)
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                raise VictorError("Voz local desactivada: instala faster-whisper con instalar.bat. También puedes elegir Google en Ajustes.") from None
            name = self.config.get("whisper_model")
            from victor.voice.models import cached_model
            name = cached_model(self.config) or name
            if self.model is None or name != self.model_name:
                try:
                    self.model = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=max(1, min(4, (os.cpu_count() or 2)-1)),
                                             num_workers=1, local_files_only=True)
                    self.model_name = name
                except Exception:
                    raise VictorError("No encuentro el modelo Whisper local. Descarga base o small con el comando indicado en README → Voz local.") from None
            from victor.voice.text import recognition_vocabulary
            language=self.config.get('language').replace('_','-').split('-')[0].lower()
            supported=getattr(self.model,'supported_languages',None)
            if isinstance(supported,(list,tuple)) and language not in supported:
                raise VictorError('El modelo Whisper no admite el idioma elegido. Usa un modelo multilingüe como base o small y un idioma como es-EC.')
            vocabulary = '' if wake_only else recognition_vocabulary(self.config.snapshot())
            options = dict(language=language, beam_size=3 if wake_only else 5,
                           vad_filter=True, condition_on_previous_text=False,
                           temperature=0.0, vad_parameters={'min_silence_duration_ms':350,'speech_pad_ms':200},
                           initial_prompt=None)
            # Compatibilidad con instalaciones anteriores que aún no incluyen hotwords.
            import inspect
            if "hotwords" in inspect.signature(self.model.transcribe).parameters:
                options["hotwords"] = vocabulary or None
            elif vocabulary:
                # Compatibilidad antigua: solo nombres, sin instrucciones que
                # Whisper pueda confundir con palabras realmente pronunciadas.
                options['initial_prompt']=vocabulary
            segments, _ = self.model.transcribe(audio, **options)
            words = []
            rejected=0
            for segment in segments:
                check_cancel(cancel)
                prob=getattr(segment,'no_speech_prob',0.)
                logprob=getattr(segment,'avg_logprob',0.)
                ratio=getattr(segment,'compression_ratio',0.)
                # Rechazar silencio/repeticiones sin convertir nombres propios
                # poco probables por sí solos en una denegación automática.
                if ((isinstance(prob,(int,float)) and isinstance(logprob,(int,float)) and prob>=.6 and logprob<=-1.)
                    or (isinstance(ratio,(int,float)) and ratio>2.4)):
                    rejected+=1;continue
                words.append(segment.text)
            check_cancel(cancel)
            logging.getLogger('victor.voice').info('asr phase=%s audio_seconds=%.2f latency=%.2f segments=%d rejected=%d',
                'wake' if wake_only else 'request',len(audio)/16000.,time.monotonic()-started,len(words),rejected)
            return " ".join(words).strip()
        finally:
            self.lock.release()

    def transcribe_file(self, path, cancel):
        check_cancel(cancel)
        if Path(path).stat().st_size > 15_000_000:
            raise VictorError("La nota de voz supera 15 MB.")
        try:
            audio = decode_audio(path, cancel)
        except VictorError:
            raise
        except ImportError:
            raise VictorError("Para notas de voz instala av y numpy con instalar.bat.") from None
        except Exception:
            raise VictorError("No pude leer ese audio. Envía una nota de voz válida.") from None
        if len(audio) > 16000 * 60:
            raise VictorError("La nota de voz debe durar como máximo 60 segundos.")
        return self.transcribe(audio, cancel)


def decode_audio(path, cancel=None):
    """Decodifica con PyAV sin depender de parámetros retirados en av.open."""
    import av
    import numpy as np
    chunks = []
    count = 0
    with av.open(str(path)) as container:
        resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
        for frame in container.decode(audio=0):
            if cancel is not None:
                check_cancel(cancel)
            for block in resampler.resample(frame):
                samples = block.to_ndarray().flatten()
                count += samples.size
                if count > 16000 * 60:
                    raise VictorError("La nota de voz debe durar como máximo 60 segundos.")
                chunks.append(samples)
        for block in resampler.resample(None):
            chunks.append(block.to_ndarray().flatten())
            count += chunks[-1].size
        if count > 16000 * 60:
            raise VictorError("La nota de voz debe durar como máximo 60 segundos.")
    return np.concatenate(chunks).astype(np.float32) / 32768 if chunks else np.array([], dtype=np.float32)
