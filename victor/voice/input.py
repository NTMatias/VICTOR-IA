import logging
import queue
import threading
import time
from victor.errors import VictorError
from victor.voice.wakeword import extract_command
from victor.voice.transcription import Transcriber


class VoiceInput:
    """Captura PCM limitada; la escucha continua requiere activar el micrófono."""
    def __init__(self, config, emit, can_listen):
        self.config, self.emit, self.can_listen = config, emit, can_listen
        self.stop_event = threading.Event()
        self.release_event = threading.Event()
        self.thread = None
        self.model = None
        self.model_name = None
        self.transcriber = Transcriber(config)
        self.conversation_until = 0

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self):
        if self.running:
            return
        self.stop_event.clear()
        self.release_event.clear()
        self.conversation_until = 0
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
        devices = sd.query_devices()
        if not any(device["max_input_channels"] > 0 for device in devices):
            raise VictorError("No hay micrófono disponible. Puedes usar el celular enviando notas de voz por Telegram tras emparejarlo en el PC.")
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
            return self.transcriber.transcribe(pcm.astype(np.float32)/32768.0, self.stop_event)
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
        misses = 0
        try:
            while not self.stop_event.is_set():
                if not self.can_listen():
                    if self.conversation_until:
                        self.conversation_until = time.monotonic() + self.config.get("conversation_window")
                    if self.stop_event.wait(0.2):
                        break
                    continue
                self.emit("voice_status", "Escuchando…")
                confirmation_context = getattr(self, "confirmation_context", lambda: None)()
                text = self.listen()
                if self.stop_event.is_set():
                    break
                if text:
                    confirming = getattr(self, "confirmation_pending", lambda: False)()
                    command = extract_command(text, self.config.get("wake_word"), required=continuous and not confirming and time.monotonic() > self.conversation_until)
                    if command:
                        misses = 0
                        self.conversation_until = time.monotonic() + self.config.get("conversation_window")
                        if confirmation_context is not None:
                            self.emit("voice_confirmation", (confirmation_context, command))
                        else:
                            self.emit("voice_text", command)
                    else:
                        misses += 1
                elif continuous:
                    misses += 1
                if continuous and misses >= 3:
                    self.emit("notice", "No he reconocido la palabra de activación varias veces. Habla más cerca del micrófono o revisa el dispositivo en Ajustes.")
                    misses = 0
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
