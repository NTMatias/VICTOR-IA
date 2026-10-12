"""Transcripción de OpenAI con audio en memoria, sin cambiar la IA del chat."""
import asyncio
import io
import wave
from victor.errors import VictorError, check_cancel
from victor.voice.text import recognition_vocabulary


def wav_audio(audio):
    import numpy as np
    samples = np.asarray(audio, dtype=np.float32)
    if samples.ndim != 1 or not np.isfinite(samples).all():
        raise VictorError("El audio de voz no es válido.")
    if samples.size > 16000 * 60:
        raise VictorError("El audio de voz debe durar como máximo 60 segundos.")
    if not samples.size:
        return b""
    pcm = (np.clip(samples, -1, 1) * 32767).astype('<i2')
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as stream:
        stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(16000)
        stream.writeframes(pcm.tobytes())
    return buffer.getvalue()


def require_key(config):
    key = config.api_key('OpenAI')
    if not key:
        raise VictorError("La voz OpenAI necesita tu clave: Ajustes → IA → Claves API personales → OpenAI. Puedes seguir usando Whisper local o Google en Ajustes → Voz.")
    return key


def transcribe(audio, config, cancel):
    check_cancel(cancel)
    key = require_key(config)
    wav = wav_audio(audio)
    if not wav:
        return ""
    cfg = config.snapshot()
    try:
        return asyncio.run(_request(wav, key, cfg, cancel))
    except VictorError:
        raise
    except Exception as exc:
        # Nunca mostrar cuerpos HTTP: pueden contener claves, audio o prompts.
        status = getattr(exc, 'status_code', None)
        if status in (401, 403):
            message = "OpenAI no aceptó la clave o sus permisos. Revisa la clave personal de OpenAI en Ajustes → IA."
        elif status == 429:
            message = "OpenAI alcanzó el límite de uso o saldo. Revisa la facturación de tu API y vuelve a intentar."
        elif status == 404:
            message = "Tu cuenta no tiene acceso al modelo de voz seleccionado. Elige otro modelo OpenAI en Ajustes → Voz."
        elif isinstance(exc, (TimeoutError, asyncio.TimeoutError)) or 'Timeout' in type(exc).__name__:
            message = "La transcripción OpenAI tardó demasiado. Revisa Internet y vuelve a intentar."
        else:
            message = "No se pudo transcribir con OpenAI. Revisa Internet y el servicio; no se ejecutó ninguna orden."
        raise VictorError(message) from None


async def _request(wav, key, cfg, cancel):
    from openai import AsyncOpenAI
    model = cfg['openai_transcription_model']
    language = cfg['language'].split('-')[0].split('_')[0].lower()
    vocabulary = recognition_vocabulary(cfg)
    options = {'model': model, 'file': ('voice.wav', wav, 'audio/wav'), 'response_format': 'json'}
    if vocabulary:
        options['prompt'] = ('Nombres propios que pueden aparecer: ' if language == 'es' else 'Proper names that may occur: ') + vocabulary
    if model == 'gpt-transcribe':
        options['extra_body'] = {'languages': [language], 'keywords': vocabulary.split(', ') if vocabulary else []}
    else:
        options['language'] = language
    timeout = min(30, cfg['network_timeout'])
    check_cancel(cancel)
    async with AsyncOpenAI(api_key=key, base_url='https://api.openai.com/v1', timeout=timeout, max_retries=0) as client:
        # Plazo total además del timeout HTTP, cancelable sin dejar un hilo de red vivo.
        task = asyncio.create_task(asyncio.wait_for(client.audio.transcriptions.create(**options), timeout))
        try:
            while not task.done():
                check_cancel(cancel)
                await asyncio.wait({task}, timeout=.1)
            check_cancel(cancel)
            result = task.result()
            if not isinstance(getattr(result, 'text', None), str):
                raise VictorError("OpenAI no devolvió una transcripción válida; no se ejecutó ninguna orden.")
            return result.text.strip()
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
