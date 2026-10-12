import logging
import threading
import time
from victor.errors import VictorError, Cancelled
from victor.voice.wakeword import extract_command, wake_match
from victor.voice.transcription import Transcriber


class VoiceInput:
    """Espera la activación, saluda y escucha peticiones en cualquier ventana."""
    def __init__(self, config, emit, can_listen):
        self.config, self.emit, self.can_listen = config, emit, can_listen
        self.stop_event = threading.Event()
        self.release_event = threading.Event()
        self.thread = None
        self.model = None
        self.model_name = None
        self.transcriber = Transcriber(config)
        self.conversation_until = 0
        self.reply_deadline = 0
        self.reply_silence_seconds = 8
        self.can_interrupt = lambda: False
        self.is_speech_echo = lambda text: False
        self.capture = None
        self.keep_capture = False
        self.capture_handoff = lambda: 0.
        self.last_handoff = 0.
        self.detector = None
        self.capture_failures = 0
        self.diagnostic = False
        self.diagnostic_result = False

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, diagnostic=False):
        if self.running:
            return
        self.stop_event.clear()
        self.diagnostic=diagnostic;self.diagnostic_result=False;self.capture_failures=0
        self.release_event.clear()
        self.conversation_until = 0
        self.reply_deadline = 0
        self.interrupt_unavailable = None
        self.thread = threading.Thread(target=self._run, name="victor-microphone", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def release(self):
        self.release_event.set()

    def listen(self):
        cfg=self.config.snapshot()
        if self.diagnostic:cfg['voice_mode']='manual'
        wake_only=(cfg['voice_mode']=='continua' and time.monotonic()>=self.conversation_until
                   and not getattr(self,'confirmation_pending',lambda:False)())
        if cfg['voice_backend'] == 'openai' and not wake_only:
            from victor.voice.openai_transcription import require_key
            require_key(self.config)
        import numpy as np
        from collections import deque
        from victor.voice.capture import capture_session
        from victor.voice.activity import SpeechDetector
        if self.detector is None:self.detector=SpeechDetector()
        self.detector.reset()
        samples=[];pre=deque();pre_samples=0;voiced=0.;silence=0.;captured=0.
        start=time.monotonic()
        with capture_session(self) as capture:
            handoff=self.capture_handoff()
            if handoff>self.last_handoff:
                capture.begin_phase(handoff,replay=True);self.last_handoff=handoff
            while not self.stop_event.is_set():
                if not self.can_listen():
                    if self.diagnostic:
                        self.emit('notice','La sesión está ocupada. Vuelve a probar el micrófono cuando termine la respuesta.')
                    self.emit('mic_level', 0.)
                    return ''
                if cfg['voice_mode']=='push-to-talk' and self.release_event.is_set():break
                packet=capture.read()
                if packet is None:
                    if not samples and time.monotonic()-start>=4:break
                    continue
                block=packet.samples
                self.capture_failures=0
                if packet.gap:
                    self.detector.reset();pre.clear();pre_samples=0
                    if samples:
                        self.emit('notice','Hubo una interrupción en el audio del micrófono. Repite la petición; no se ejecutó audio incompleto.')
                        return ''
                rms=float(np.sqrt(np.mean(block.astype(np.float32)**2)))
                self.emit('mic_level',min(1.,rms/6000.))
                duration=len(block)/16000.
                speech=self.detector.is_voice(block)
                if speech:
                    if not samples:samples.extend(pre);pre.clear()
                    samples.append(block);voiced+=duration;silence=0.
                    if self.reply_deadline:self.reply_deadline=time.monotonic()+self.reply_silence_seconds
                elif samples:samples.append(block);silence+=duration
                else:
                    pre.append(block);pre_samples+=len(block)
                    while pre_samples>5600 and len(pre)>1:pre_samples-=len(pre.popleft())
                if samples:captured+=duration
                if captured>=55:
                    self.emit('notice','La petición de voz superó 55 segundos. No ejecuté una frase cortada; divídela en peticiones más cortas.')
                    return ''
                if cfg['voice_mode']!='push-to-talk' and ((samples and silence>=.7) or (not samples and time.monotonic()-start>=4)):break
        self.emit('mic_level',0.)
        if self.stop_event.is_set() or not samples or voiced<.06:return ''
        pcm=np.concatenate(samples).flatten()
        self.emit("voice_status", "Transcribiendo…")
        # Rechazar una captura cuyo turno se invalidó durante su decodificación.
        if wake_only:
            text=self.transcriber.transcribe(pcm.astype(np.float32)/32768.,self.stop_event,wake_only=True)
        elif cfg['voice_backend'] in ('whisper','openai'):
            text=self.transcriber.transcribe(pcm.astype(np.float32)/32768.,self.stop_event)
        else:
            text=self.transcribe_google(pcm,cfg)
        if self.stop_event.is_set() or not self.can_listen():return ''
        import unicodedata
        return unicodedata.normalize('NFC',text).strip()

    def transcribe_google(self, pcm, cfg):
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        recognizer.operation_timeout = 10
        try:
            return recognizer.recognize_google(sr.AudioData(pcm.tobytes(), 16000, 2), language=cfg["language"])
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            raise VictorError("No se pudo transcribir con Google. Revisa Internet o configura Whisper local.") from None

    def listen_interrupt(self):
        from victor.voice.interruption import listen_for_interrupt
        return listen_for_interrupt(self)

    def capture_retry(self, listen):
        from victor.voice.capture import MicrophoneError
        try:return listen()
        except MicrophoneError:
            self.capture_failures+=1
            if self.capture:self.capture.close();self.capture=None
            if self.config.get('voice_mode')!='continua' or self.capture_failures>=3:raise
            logging.getLogger('victor.voice').warning('microphone reconnect attempt=%d',self.capture_failures)
            self.emit('voice_status','Reconectando micrófono…')
            self.stop_event.wait(.3*self.capture_failures)
            return ''

    def activate(self, text, interrupt=False):
        if self.capture:self.capture.begin_phase()
        finished=threading.Event()
        self.emit('voice_interrupt' if interrupt else 'voice_wake',finished)
        deadline=time.monotonic()+180
        while not finished.is_set() and not self.stop_event.is_set() and time.monotonic()<deadline:
            if self.can_interrupt():
                replacement=self.capture_retry(self.listen_interrupt)
                if replacement:
                    text=replacement
                    # Reemplazar también una orden inline que aún esperaba el
                    # saludo. La señal anterior ya no arma la nueva petición.
                    finished=threading.Event()
                    self.emit('voice_interrupt',finished)
                    deadline=time.monotonic()+180
            else:self.stop_event.wait(.1)
        if self.stop_event.is_set():return ''
        if not finished.is_set():
            self.emit('error','El saludo de voz no terminó. Revisa la salida de audio en Ajustes → Voz.')
            self.emit('voice_reply_timeout',None)
            return ''
        self.conversation_until=time.monotonic()+self.config.get('conversation_window')
        self.reply_deadline=time.monotonic()+min(self.reply_silence_seconds,self.config.get('conversation_window'))
        self.emit('voice_status','Escuchando tu petición…')
        if self.capture:
            handoff=self.capture_handoff()
            self.capture.begin_phase(handoff if handoff else time.perf_counter(),replay=True)
            self.last_handoff=handoff
        return text

    def expire_reply(self):
        if self.reply_deadline and (time.monotonic()>=self.reply_deadline or time.monotonic()>=self.conversation_until):
            self.conversation_until=self.reply_deadline=0
            self.emit('voice_reply_timeout',None)

    def _run(self):
        continuous = self.config.get("voice_mode") == "continua" and not self.diagnostic
        self.keep_capture=continuous
        pending_text = None
        try:
            while not self.stop_event.is_set():
                self.expire_reply()
                if not self.can_listen():
                    if self.diagnostic:
                        self.emit('notice','La sesión está ocupada. Vuelve a probar el micrófono cuando termine la respuesta.');break
                    if continuous and self.can_interrupt():
                        text=self.capture_retry(self.listen_interrupt)
                        if text:
                            text=self.activate(text,interrupt=True)
                            command=extract_command(text,self.config.get('wake_word'))
                            if command:
                                pending_text=command
                        continue
                    if self.conversation_until:
                        self.conversation_until = time.monotonic() + self.config.get("conversation_window")
                        if self.reply_deadline:self.reply_deadline=time.monotonic()+self.reply_silence_seconds
                    if self.capture:self.capture.begin_phase()
                    if self.stop_event.wait(0.2):
                        break
                    continue
                armed = time.monotonic() < self.conversation_until
                self.emit("voice_status", "Escuchando tu petición…" if armed or not continuous else "Escuchando · di " + self.config.get('wake_word'))
                confirmation_context = getattr(self, "confirmation_context", lambda: None)()
                text = pending_text if pending_text is not None else self.capture_retry(self.listen)
                pending_text = None
                if self.stop_event.is_set():
                    break
                if text:
                    if self.diagnostic:
                        self.diagnostic_result=True;self.emit('voice_diagnostic_text',text);break
                    confirming = getattr(self, "confirmation_pending", lambda: False)()
                    woke = wake_match(text, self.config.get('wake_word')) is not None
                    if continuous and woke and not confirming and confirmation_context is None:
                        # La GUI confirma cuando TERMINA el saludo, incluso si falla
                        # el motor. No capturar ni enviar la orden antes de esa señal.
                        text=self.activate(text)
                        if self.stop_event.is_set():break
                        if not text:continue
                    command = extract_command(text, self.config.get("wake_word"), required=continuous and not confirming and time.monotonic() > self.conversation_until)
                    if command:
                        if not confirming and confirmation_context is None:
                            from victor.voice.text import correct_music_command
                            original = command
                            command = correct_music_command(command, self.config.get("voice_corrections"))
                            if original != command:
                                self.emit("notice", "Corrección de voz: «" + original + "» → «" + command + "»")
                        # Una activación permite una petición; el resto de la
                        # conversación ambiental no se entrega al asistente.
                        self.conversation_until = 0
                        self.reply_deadline = 0
                        self.emit('voice_reply_received',None)
                        if confirmation_context is not None:
                            self.emit("voice_confirmation", (confirmation_context, command))
                        else:
                            self.emit("voice_text", command)
                if not continuous:
                    break
                self.expire_reply()
                self.stop_event.wait(0.05)
        except ImportError as exc:
            logging.getLogger("victor.voice").warning("missing dependency %s", exc.name)
            self.emit("error", "Voz no disponible: falta sounddevice, numpy o SpeechRecognition. Repite instalar.bat; el chat sigue funcionando.")
        except Cancelled:
            pass
        except VictorError as exc:
            self.emit("error", str(exc))
        except Exception:
            logging.getLogger("victor.voice").exception("voice input failed")
            self.emit("error", "No se pudo usar el micrófono/modelo local. Revisa permisos, dispositivo y la guía de voz del README.")
        finally:
            self.keep_capture=False
            if self.capture:self.capture.close();self.capture=None
            self.emit('voice_input_stopped',None)
            self.emit('mic_level',0.)
            self.emit("voice_status", "Micrófono apagado")
            if self.diagnostic:
                self.emit('voice_diagnostic_done',self.diagnostic_result);self.diagnostic=False
