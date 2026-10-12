import logging
import queue
import threading
import time
from victor.errors import VictorError
from victor.voice.wakeword import extract_command


class VoiceInput:
    """Captura PCM limitada; la escucha continua requiere activar el micrófono."""
    def __init__(self, config, emit, can_listen):
        self.config, self.emit, self.can_listen = config, emit, can_listen
        self.stop_event = threading.Event()
        self.release_event = threading.Event()
        self.thread = None
        self.model = None
        self.model_name = None

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self):
        if self.running:
            return
        self.stop_event.clear()
        self.release_event.clear()
        self.thread = threading.Thread(target=self._run, name="victor-microphone", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def release(self):
        self.release_event.set()

    def listen(self):
        import sounddevice as sd
        import numpy as np
        import speech_recognition as sr
        frames = queue.Queue(maxsize=150)
        samples = []
        def callback(data, count, timing, status):
            try:
                frames.put_nowait(data.copy())
            except queue.Full:
                pass
        cfg = self.config.snapshot()
        device = int(cfg["microphone"]) if cfg["microphone"].strip() else None
        start = time.monotonic()
        last_voice = start
        speech = False
        with sd.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=1600, device=device, callback=callback):
            while not self.stop_event.is_set() and time.monotonic() - start < 15:
                if cfg["voice_mode"] == "push-to-talk" and self.release_event.is_set():
                    break
                try:
                    block = frames.get(timeout=0.15)
                except queue.Empty:
                    continue
                samples.append(block)
                rms = float(np.sqrt(np.mean(block.astype(np.float32) ** 2)))
                now = time.monotonic()
                if rms > 350:
                    speech, last_voice = True, now
                if cfg["voice_mode"] != "push-to-talk" and ((speech and now-last_voice > 1.1) or (not speech and now-start > 4)):
                    break
        if self.stop_event.is_set() or not samples or not speech:
            return ""
        pcm = np.concatenate(samples).flatten()
        self.emit("voice_status", "Transcribiendo…")
        if cfg["voice_backend"] == "whisper":
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                raise VictorError("faster-whisper es opcional. Instálalo con .venv\\Scripts\\python -m pip install faster-whisper o selecciona Google.") from None
            if self.model_name != cfg["whisper_model"]:
                self.model = WhisperModel(cfg["whisper_model"], device="cpu", compute_type="int8", local_files_only=True)
                self.model_name = cfg["whisper_model"]
            segments, info = self.model.transcribe(pcm.astype(np.float32)/32768.0, language=cfg["language"].split("-")[0], beam_size=1)
            words = []
            for segment in segments:
                if self.stop_event.is_set():
                    return ""
                words.append(segment.text)
            return " ".join(words).strip()
        recognizer = sr.Recognizer()
        recognizer.operation_timeout = 10
        try:
            return recognizer.recognize_google(sr.AudioData(pcm.tobytes(), 16000, 2), language=cfg["language"])
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            raise VictorError("No se pudo transcribir con Google. Revisa Internet o configura Whisper local.") from None

    def _run(self):
        continuous = self.config.get("voice_mode") == "continua"
        try:
            while not self.stop_event.is_set():
                if not self.can_listen():
                    if self.stop_event.wait(0.2):
                        break
                    continue
                self.emit("voice_status", "Escuchando…")
                text = self.listen()
                if self.stop_event.is_set():
                    break
                if text:
                    command = extract_command(text, self.config.get("wake_word"), required=continuous)
                    if command:
                        self.emit("voice_text", command)
                if not continuous:
                    break
                self.stop_event.wait(0.7)
        except ImportError as exc:
            logging.getLogger("victor.voice").warning("missing dependency %s", exc.name)
            self.emit("error", "Voz no disponible: falta sounddevice, numpy o SpeechRecognition. Repite instalar.bat; el chat sigue funcionando.")
        except VictorError as exc:
            self.emit("error", str(exc))
        except Exception:
            logging.getLogger("victor.voice").exception("voice input failed")
            self.emit("error", "No se pudo usar el micrófono/modelo local. Revisa permisos, dispositivo y la guía de voz del README.")
        finally:
            self.emit("voice_status", "Micrófono apagado")
