"""Pruebas de conexión de solo lectura en un proceso cancelable, sin herramientas IA."""
import asyncio
import json
import os
import sys
import threading
from pathlib import Path
from victor.config import ConfigManager, KEYS
from victor.voice.models import cached_model


def check_services(config, emit):
    def run(name, function):
        try:
            detail = function()
            emit(name, '✅ ' + name + ': ' + detail)
        except Exception as exc:
            # Nunca serializar str(exc): algunas bibliotecas incluyen URLs/tokens.
            emit(name, '❌ ' + name + ': no se pudo verificar (' + type(exc).__name__ + '). Revisa conexión y configuración.')

    cfg = config.snapshot()
    selected = cfg['provider']
    try:
        personal_key = config.api_key(selected)
    except Exception:
        personal_key = ''
    if selected in KEYS and not personal_key:
        emit('IA', '❌ IA: falta ' + KEYS[selected])
    else:
        def ai():
            from victor.ai.manager import AIManager
            cfg.update(network_timeout=8, ollama_timeout=8, max_tokens=128)
            if selected in KEYS:cfg['_api_key'] = personal_key
            provider = AIManager(config, lambda *_: None).providers[selected]
            response = provider.stream([{'role':'user', 'content':'Responde solamente OK.'}],
                                       'Prueba de conexión. No solicites herramientas.', [], cfg,
                                       lambda _: None, threading.Event())
            if not response.text.strip():
                raise RuntimeError('empty response')
            return 'el modelo seleccionado respondió'
        run('IA', ai)
    emit('Whisper', '✅ Whisper: archivos locales disponibles; micrófono sin comprobar' if cached_model(config)
         else '⚠️ Whisper: descarga el modelo local')
    from victor.integrations.spotify import SpotifyManager
    from victor.integrations.google import GoogleManager
    spotify, google = SpotifyManager(config), GoogleManager(config)
    if spotify.cache.path.exists():
        def playback():
            spotify.client().current_playback()
            return 'API accesible (puede no haber reproducción activa)'
        run('Spotify', playback)
    else:
        emit('Spotify', '⚠️ Spotify: conecta la cuenta')
    if google.cache.path.exists():
        def calendar():
            google.events()
            return 'Calendar accesible; Gmail/Drive no comprobados'
        run('Google', calendar)
    else:
        emit('Google', '⚠️ Google: conecta la cuenta')
    if os.getenv('TELEGRAM_BOT_TOKEN', '').strip():
        def telegram():
            from telegram import Bot
            async def probe():
                async with Bot(os.environ['TELEGRAM_BOT_TOKEN']) as bot:
                    await bot.get_me(read_timeout=8, connect_timeout=8, write_timeout=8, pool_timeout=8)
            asyncio.run(asyncio.wait_for(probe(), timeout=20))
            return 'bot accesible; emparejamiento no comprobado'
        run('Telegram', telegram)
    else:
        emit('Telegram', '⚠️ Telegram: falta TELEGRAM_BOT_TOKEN')


if __name__ == '__main__':
    check_services(ConfigManager(Path(sys.argv[1])),
                   lambda name, text: print(json.dumps({'service':name, 'text':text}), flush=True))
