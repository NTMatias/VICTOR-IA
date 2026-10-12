"""Wake-only rolling capture while TTS runs; never submits ambient speech."""
from collections import deque
import time
from victor.errors import Cancelled, VictorError
from victor.voice.wakeword import wake_match
from victor.voice.capture import MicrophoneError


def listen_for_interrupt(voice):
    import numpy as np
    import sounddevice as sd
    cfg = voice.config.snapshot()
    model = cfg['whisper_model']
    if getattr(voice, 'interrupt_unavailable', None) == model:
        voice.stop_event.wait(.2)
        return ''
    recent = deque()
    from victor.voice.capture import capture_session
    from victor.voice.activity import SpeechDetector
    detector=SpeechDetector()
    total=0;new_samples=0;heard_speech=False
    last_check = 0.
    try:
        with capture_session(voice) as capture:
            while not voice.stop_event.is_set() and voice.can_interrupt():
                packet=capture.read(timeout=.1)
                if packet is None:continue
                if packet.gap:recent.clear();total=0;new_samples=0;detector.reset();heard_speech=False
                block=packet.samples;recent.append(block);total+=len(block);new_samples+=len(block)
                voice.capture_failures=0
                # Duración en muestras: blocksize=0 admite bloques variables.
                while total>51200 and len(recent)>1:total-=len(recent.popleft())
                heard_speech=detector.is_voice(block) or heard_speech
                # El callback continúa capturando durante la inferencia. Ventana
                # solapada: no perder VICTOR en el límite de dos fragmentos.
                if total<12800 or new_samples<6400 or time.monotonic()-last_check<.5:continue
                if not heard_speech:continue
                audio=np.concatenate(list(recent)).flatten().astype(np.float32)
                last_check=time.monotonic()
                new_samples=0;heard_speech=False
                text=voice.transcriber.transcribe(audio/32768.,voice.stop_event,wake_only=True)
                # La voz puede terminar durante la inferencia; una llamada
                # capturada mientras hablaba sigue siendo una activación válida.
                if voice.stop_event.is_set(): return ''
                if wake_match(text,cfg['wake_word']) and not voice.is_speech_echo(text):
                    # El resto puede mezclar al usuario y el altavoz. Esta
                    # escucha solo interrumpe; nunca crea una orden del fragmento.
                    return cfg['wake_word']
    except Cancelled:
        return ''
    except MicrophoneError:
        raise
    except (VictorError, ImportError, sd.PortAudioError):
        voice.interrupt_unavailable=model
        voice.emit('notice','No pude preparar la interrupción por nombre. Revisa el micrófono y Whisper local en Ajustes → Voz. La escucha habitual sigue disponible.')
    return ''
