import json
import logging
import os
import queue
import subprocess
import sys
import threading
from victor.config import ROOT


class VoiceOutput:
    """SAPI en proceso aislado: detener la voz nunca bloquea el hilo de Tk."""
    def __init__(self, config, emit):
        self.config, self.emit = config, emit
        self.pending = queue.Queue(maxsize=2)
        self.closing = threading.Event()
        self.lock = threading.Lock()
        self.process = None
        self.epoch = 0
        self.speaking = threading.Event()
        self.thread = threading.Thread(target=self._run, name="victor-speaker", daemon=True)
        self.thread.start()

    def speak(self, text):
        if self.config.get("voice_enabled") and text:
            try:
                with self.lock:
                    self.pending.put_nowait((text[:7000], self.epoch))
            except queue.Full:
                self.emit("notice", "La cola de voz está llena; la respuesta está disponible en el chat.")

    def stop(self):
        while True:
            try:
                self.pending.get_nowait()
            except queue.Empty:
                break
        with self.lock:
            self.epoch += 1
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()

    def close(self):
        self.closing.set()
        self.stop()

    def _run(self):
        while not self.closing.is_set():
            try:
                text, epoch = self.pending.get(timeout=0.2)
            except queue.Empty:
                continue
            if self.closing.is_set():
                break
            if epoch != self.epoch:
                continue
            self.speaking.set()
            self.emit("speech_status", "Hablando…")
            try:
                cfg = self.config.snapshot()
                with self.lock:
                    if self.closing.is_set() or epoch != self.epoch:
                        continue
                    self.process = subprocess.Popen([sys.executable, str(ROOT / "main.py"), "--speak-worker"],
                        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                    process = self.process
                payload = {"text": text, "rate": cfg["voice_rate"], "voice_id": cfg["voice_id"], "language": cfg["language"],
                           "backend": cfg["tts_backend"], "edge_voice": cfg["edge_voice"]}
                process.communicate(json.dumps(payload, ensure_ascii=False), timeout=180)
                if process.returncode and not self.closing.is_set() and epoch == self.epoch:
                    self.emit("error", "La síntesis de voz no pudo completarse. Revisa pyttsx3 y las voces de Windows.")
            except Exception:
                logging.getLogger("victor.voice").exception("speech failed")
                with self.lock:
                    if self.process and self.process.poll() is None:
                        self.process.kill()
                        self.process.wait(timeout=5)
                self.emit("error", "La salida de voz no está disponible. El texto sigue en el chat.")
            finally:
                with self.lock:
                    self.process = None
                self.speaking.clear()
                self.emit("speech_status", "Voz en espera")


def speak_sapi(payload):
    import pyttsx3
    engine = pyttsx3.init("sapi5" if os.name == "nt" else None)
    engine.setProperty("rate", payload["rate"])
    if payload.get("voice_id"):
        engine.setProperty("voice", payload["voice_id"])
    else:
        language = payload.get("language", "es").split("-")[0]
        for voice in engine.getProperty("voices"):
            description = (voice.name + " " + str(voice.languages)).lower()
            if language in description or (language == "es" and "spanish" in description):
                engine.setProperty("voice", voice.id)
                break
    engine.say(payload["text"])
    engine.runAndWait()
    engine.stop()


def speak_worker():
    payload = json.loads(sys.stdin.read())
    if payload.get("backend") == "edge":
        try:
            import asyncio
            import tempfile
            from pathlib import Path
            import edge_tts
            from PySide6.QtCore import QUrl, QTimer
            from PySide6.QtWidgets import QApplication
            from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
            async def synthesize(path):
                await asyncio.wait_for(edge_tts.Communicate(payload["text"], payload["edge_voice"], connect_timeout=8, receive_timeout=20).save(str(path)), timeout=40)
            with tempfile.TemporaryDirectory(prefix="victor-tts-") as folder:
                path = Path(folder) / "speech.mp3"
                asyncio.run(synthesize(path))
                app = QApplication([])
                player, output = QMediaPlayer(), QAudioOutput()
                player.setAudioOutput(output)
                failed = []
                def on_error(*args):
                    failed.append(True)
                    app.quit()
                player.errorOccurred.connect(on_error)
                player.mediaStatusChanged.connect(lambda status: app.quit() if status == QMediaPlayer.MediaStatus.EndOfMedia else None)
                player.setSource(QUrl.fromLocalFile(str(path)))
                QTimer.singleShot(150000, on_error)
                player.play()
                app.exec()
                player.stop()
                # Windows mantiene abierto el MP3 hasta liberar el backend de Qt.
                player.setSource(QUrl())
                from shiboken6 import delete
                delete(player)
                delete(output)
                app.processEvents()
                if failed:
                    raise RuntimeError("No audio output")
            return
        except Exception:
            # Respaldo real SAPI; errores de ambos se contienen en el proceso padre.
            logging.getLogger("victor.voice").exception("Edge TTS failed; trying SAPI")
    speak_sapi(payload)
