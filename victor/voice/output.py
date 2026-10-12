import json
import logging
import os
import queue
import subprocess
import sys
import threading
import time
from victor.config import ROOT
from victor.errors import Cancelled


class VoiceOutput:
    """Síntesis aislada con niveles PCM por pipe; detener nunca bloquea la GUI."""
    def __init__(self, config, emit):
        self.config, self.emit = config, emit
        self.pending = queue.Queue(maxsize=2)
        self.closing = threading.Event()
        self.lock = threading.Lock()
        self.process = None
        self.epoch = 0
        self.speaking = threading.Event()
        self.music_ducker = None
        self.duck_context = None
        self.interaction = threading.Event()
        self.current_text = ''
        self.last_audio_end = 0.
        self.audio_end_received = False
        self.thread = threading.Thread(target=self._run, name="victor-speaker", daemon=True)
        self.thread.start()

    @property
    def busy(self):
        return self.speaking.is_set() or not self.pending.empty()

    def speak(self, text, settings=None, force=False, completed=None):
        from victor.voice.text import speech_text
        text = speech_text(text)
        if not self.closing.is_set() and (force or self.config.get("voice_enabled")) and text:
            try:
                with self.lock:
                    self.pending.put_nowait((text[:7000], self.epoch, settings, completed))
                return True
            except queue.Full:
                self.emit("notice", "La cola de voz está llena; la respuesta está disponible en el chat.")
        if completed is not None:
            completed.set()
        return False

    def begin_interaction(self):
        self.interaction.set()

    def end_interaction(self):
        self.interaction.clear()

    def is_speech_echo(self, text):
        # Evitar que una frase de VICTOR que contiene su nombre lo active.
        # Una llamada corta del usuario sigue siendo admisible.
        from difflib import SequenceMatcher
        import re, unicodedata
        def words(s):
            return re.findall(r'\w+', ''.join(c for c in unicodedata.normalize('NFD',s.casefold()) if not unicodedata.combining(c)))
        heard, spoken=words(text),words(self.current_text)
        if len(heard)<2 or not spoken:return False
        h=' '.join(heard)
        for i in range(len(spoken)):
            candidate=' '.join(spoken[i:i+len(heard)])
            if SequenceMatcher(None,h,candidate).ratio()>=.85:return True
        return False

    def stop(self, preserve_music=False):
        if not preserve_music:self.end_interaction()
        while True:
            try:
                item = self.pending.get_nowait()
                if item[3] is not None:
                    item[3].set()
            except queue.Empty:
                break
        with self.lock:
            self.epoch += 1
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()

    def close(self):
        self.closing.set()
        self.stop()

    def read_meter(self,process,epoch,on_ready=None):
        from victor.voice.levels import decode_meter
        try:
            for line in iter(lambda:process.stdout.readline(2048),''):
                packet=decode_meter(line)
                if packet and epoch==self.epoch and not self.closing.is_set():
                    if packet[0]=='speech_ready':
                        if on_ready: on_ready()
                    elif packet[0]=='speech_ended':
                        if not self.audio_end_received and packet[1]<=time.perf_counter()+1:
                            self.last_audio_end=packet[1];self.audio_end_received=True
                    else: self.emit(*packet)
        except (OSError,ValueError):
            # El cierre/cancelación puede cerrar el pipe mientras el lector sale.
            if not self.closing.is_set() and epoch==self.epoch:
                logging.getLogger('victor.voice').debug('Audio meter pipe closed')

    def _run(self):
        while not self.closing.is_set():
            try:
                text, epoch, settings, completed = self.pending.get(timeout=0.2)
            except queue.Empty:
                if not self.interaction.is_set():self._release_music()
                continue
            if self.closing.is_set():
                if completed is not None: completed.set()
                break
            if epoch != self.epoch:
                if completed is not None: completed.set()
                continue
            self.speaking.set()
            self.audio_end_received=False
            self.current_text=text
            self.emit("speech_status", "Preparando voz…")
            reader=None
            try:
                if self.interaction.is_set():self._hold_music(epoch)
                cfg = self.config.snapshot()
                if settings:
                    cfg.update({k:v for k,v in settings.items() if k in ('tts_backend','edge_voice','voice_id','voice_rate')})
                with self.lock:
                    if self.closing.is_set() or epoch != self.epoch:
                        continue
                    self.process = subprocess.Popen([sys.executable, str(ROOT / "main.py"), "--speak-worker"],
                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                        text=True, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
                    process = self.process
                payload = {"text": text, "rate": cfg["voice_rate"], "voice_id": cfg["voice_id"], "language": cfg["language"],
                           "backend": cfg["tts_backend"], "edge_voice": cfg["edge_voice"], 'audio_gate':self.music_ducker is not None}
                def ready(process=process,epoch=epoch):
                    allowed=False
                    try:
                        self._hold_music(epoch)
                        allowed=not self.closing.is_set() and epoch==self.epoch
                    except Exception:
                        if epoch==self.epoch and not self.closing.is_set():
                            self.emit('error','No pude bajar la música antes de hablar. La respuesta sigue disponible en el chat.')
                    try:
                        process.stdin.write(json.dumps({'play':allowed})+'\n');process.stdin.flush()
                    except (OSError,ValueError): pass
                reader=threading.Thread(target=self.read_meter,args=(process,epoch,ready),name='victor-audio-levels',daemon=True);reader.start()
                # ASCII JSON es independiente de la página de códigos del hijo.
                process.stdin.write(json.dumps(payload,ensure_ascii=True)+'\n');process.stdin.flush()
                if not payload['audio_gate']:process.stdin.close()
                process.wait(timeout=180)
                if process.returncode and not self.closing.is_set() and epoch == self.epoch:
                    self.emit("error", "La síntesis de voz no pudo completarse. Revisa pyttsx3 y las voces de Windows.")
            except Exception:
                failed = not self.closing.is_set() and epoch == self.epoch
                if failed: logging.getLogger("victor.voice").exception("speech failed")
                with self.lock:
                    if self.process and self.process.poll() is None:
                        self.process.kill()
                        self.process.wait(timeout=5)
                if failed: self.emit("error", "La salida de voz no está disponible. El texto sigue en el chat.")
            finally:
                if reader:reader.join(timeout=15)
                if self.process and self.process.stdout:self.process.stdout.close()
                if self.process and self.process.stdin and not self.process.stdin.closed:
                    try:self.process.stdin.close()
                    except OSError:pass  # El hijo puede haber sido terminado durante el saludo.
                with self.lock:
                    self.process = None
                self.speaking.clear()
                if not self.audio_end_received:self.last_audio_end=time.perf_counter()
                self.emit('tts_level',0.)
                self.emit("speech_status", "Voz en espera")
                if completed is not None: completed.set()
                if self.closing.is_set() or (not self.interaction.is_set() and (self.pending.empty() or epoch!=self.epoch)):
                    self._release_music()
        self._release_music()

    def _hold_music(self, epoch):
        if self.music_ducker and self.duck_context is None:
            context=self.music_ducker.hold(lambda:self.closing.is_set() or epoch!=self.epoch)
            if context.__enter__():self.duck_context=context
            else:context.__exit__(None,None,None)

    def _release_music(self):
        if self.duck_context:
            context,self.duck_context=self.duck_context,None
            try:context.__exit__(None,None,None)
            except Exception:self.emit('notice','No se pudo completar la restauración de música.')


def speak_sapi(payload,path=None):
    import pyttsx3
    engine = pyttsx3.init("sapi5" if os.name == "nt" else None)
    engine.setProperty("rate", payload["rate"])
    if payload.get("voice_id"):
        engine.setProperty("voice", payload["voice_id"])
    else:
        language = payload.get("language", "es").split("-")[0]
        selected = False
        for voice in engine.getProperty("voices"):
            import re
            locales = [v.decode('utf-8', errors='ignore') if isinstance(v, bytes) else str(v) for v in voice.languages]
            matches = any(re.match(r"^[\x00-\x1f]*" + re.escape(language) + r"(?:[-_]|$)", v, re.I) for v in locales)
            if matches or (language == "es" and re.search(r"\b(?:spanish|español|castellano)\b", voice.name, re.I)):
                engine.setProperty("voice", voice.id)
                selected = True
                break
        if not selected:
            engine.stop()
            from victor.errors import VictorError
            raise VictorError("No hay una voz SAPI del idioma elegido. Usa Edge o instala una voz en español en Windows.")
    try:
        if path is None:engine.say(payload['text'])
        else:engine.save_to_file(payload['text'],str(path))
        engine.runAndWait()
    finally:engine.stop()


def play_audio(path):
    """Reproduce el archivo real; Qt entrega el PCM a la visualización al reproducirlo."""
    import time
    from PySide6.QtCore import QUrl,QTimer
    from PySide6.QtWidgets import QApplication
    from PySide6.QtMultimedia import QMediaPlayer,QAudioOutput
    from victor.voice.levels import pcm_rms,report_meter
    app=QApplication.instance() or QApplication([])
    player,output=QMediaPlayer(),QAudioOutput();player.setAudioOutput(output)
    failed=[];meter=None;last=[0.];meter_seen=[False];deadline=QTimer();deadline.setSingleShot(True)
    meter_check=QTimer();meter_check.setSingleShot(True)
    try:
        try:
            from PySide6.QtMultimedia import QAudioBufferOutput
            meter=QAudioBufferOutput();player.setAudioBufferOutput(meter)
            def measured(buffer):
                if time.monotonic()-last[0]<.04 and buffer.byteCount():return
                last[0]=time.monotonic()
                try:
                    level=pcm_rms(bytes(buffer.data())[:buffer.byteCount()],buffer.format().sampleFormat().name)*output.volume() if buffer.byteCount() else 0.
                    if buffer.byteCount() and not meter_seen[0]:meter_seen[0]=True;report_meter('tts_meter',True)
                    report_meter('tts_level',min(1.,level*4.))
                except (ValueError,TypeError,RuntimeError):
                    report_meter('tts_meter',False);report_meter('tts_level',0.)
            meter.audioBufferReceived.connect(measured)
            # Algunos backends de Qt no entregan PCM aunque exista la clase.
            meter_check.timeout.connect(lambda:report_meter('tts_meter',False) if not meter_seen[0] else None)
            meter_check.start(2000)
        except (ImportError,AttributeError):report_meter('tts_meter',False)
        def on_error(*args):failed.append(True);app.quit()
        player.errorOccurred.connect(on_error)
        player.mediaStatusChanged.connect(lambda status:app.quit() if status==QMediaPlayer.MediaStatus.EndOfMedia else None)
        player.playbackStateChanged.connect(lambda state:report_meter('speech_status','Hablando…' if state==QMediaPlayer.PlaybackState.PlayingState else 'Voz en espera'))
        player.setSource(QUrl.fromLocalFile(str(path)));deadline.timeout.connect(on_error);deadline.start(150000)
        player.play();app.exec()
    finally:
        deadline.stop();meter_check.stop()
        player.stop();player.setSource(QUrl());report_meter('tts_level',0.)
        report_meter('speech_ended',time.perf_counter())
        from shiboken6 import delete
        delete(player);delete(output)
        if meter:delete(meter)
        app.processEvents()
    if failed:raise RuntimeError('No audio output')


def speak_worker():
    # Windows puede abrir sys.stdin con cp1252 aunque el padre escriba UTF-8.
    payload = json.loads(sys.stdin.buffer.readline().decode('utf-8'))
    gated=False
    def ended():
        if payload.get('audio_gate'):
            from victor.voice.levels import report_meter
            report_meter('speech_ended',time.perf_counter())
    def await_audio():
        nonlocal gated
        if gated or not payload.get('audio_gate'): return
        from victor.voice.levels import report_meter
        from victor.errors import Cancelled
        report_meter('speech_ready',True)
        response=sys.stdin.buffer.readline()
        if not response or json.loads(response.decode('utf-8')).get('play') is not True:
            raise Cancelled('Audio cancelado antes de reproducir.')
        gated=True
    if payload.get("backend") == "edge":
        try:
            import asyncio
            import tempfile
            from pathlib import Path
            import edge_tts
            async def synthesize(path):
                rate = max(-50, min(80, round((payload.get("rate", 175) / 175 - 1) * 100)))
                await asyncio.wait_for(edge_tts.Communicate(payload["text"], payload["edge_voice"], rate=f"{rate:+d}%", connect_timeout=8, receive_timeout=20).save(str(path)), timeout=40)
            with tempfile.TemporaryDirectory(prefix="victor-tts-") as folder:
                path = Path(folder) / "speech.mp3"
                asyncio.run(synthesize(path))
                await_audio()
                play_audio(path)
                ended()
            return
        except Cancelled:
            raise
        except Exception:
            # Respaldo real SAPI; errores de ambos se contienen en el proceso padre.
            logging.getLogger("victor.voice").exception("Edge TTS failed; trying SAPI")
    try:
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory(prefix='victor-sapi-') as folder:
            path=Path(folder)/'speech.wav';speak_sapi(payload,path)
            if not path.is_file() or path.stat().st_size<=44:raise RuntimeError('No SAPI audio file')
            await_audio()
            play_audio(path)
            ended()
    except Cancelled:
        raise
    except Exception:
        # Una instalación sin render PCM/Qt mantiene SAPI directo, sin simular niveles.
        from victor.voice.levels import report_meter
        logging.getLogger('victor.voice').exception('SAPI PCM unavailable; direct SAPI fallback')
        report_meter('tts_meter',False);report_meter('speech_status','Hablando…')
        await_audio()
        speak_sapi(payload)
        ended()
