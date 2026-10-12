"""Un modelo CPU compartido para micrófono y notas de voz autorizadas."""
import os
import threading
from pathlib import Path
from victor.errors import VictorError, check_cancel


class Transcriber:
    def __init__(self, config):
        self.config = config
        self.lock = threading.Lock()
        self.model = None
        self.model_name = ""

    def transcribe(self, audio, cancel):
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
            segments, _ = self.model.transcribe(audio, language=self.config.get("language").split("-")[0], beam_size=1, vad_filter=True)
            words = []
            for segment in segments:
                check_cancel(cancel)
                words.append(segment.text)
            return " ".join(words).strip()
        finally:
            self.lock.release()

    def transcribe_file(self, path, cancel):
        if Path(path).stat().st_size > 15_000_000:
            raise VictorError("La nota de voz supera 15 MB.")
        try:
            from faster_whisper.audio import decode_audio
            audio = decode_audio(str(path), sampling_rate=16000)
        except ImportError:
            raise VictorError("Para notas de voz instala faster-whisper con instalar.bat.") from None
        except Exception:
            raise VictorError("No pude leer ese audio. Envía una nota de voz válida.") from None
        if len(audio) > 16000 * 60:
            raise VictorError("La nota de voz debe durar como máximo 60 segundos.")
        return self.transcribe(audio, cancel)
