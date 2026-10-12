"""Temporary SDK volume lease. No REST volume ramps or changes to user settings."""
from contextlib import contextmanager
import secrets
import threading
from victor.errors import VictorError


class MusicDucker:
    def __init__(self, browser, emit):
        self.browser, self.emit = browser, emit

    @contextmanager
    def hold(self, cancelled):
        browser = self.browser()
        if browser is None or not browser.active:
            yield False
            return
        lease = secrets.token_hex(16)
        stopped = threading.Event()
        heartbeat = None
        try:
            self.emit('speech_status','Bajando música…')
            result=browser.command('duck_begin', {'lease': lease}, cancel=cancelled)
            if isinstance(result,dict) and result.get('ducked') is False:
                yield False
                return
            def keep_alive():
                # Una conversación puede conservar el lease al interrumpir un
                # proceso TTS; solo salir del contexto debe detener su latido.
                while not stopped.wait(5):
                    try: browser.command('duck_keepalive', {'lease': lease}, cancel=stopped.is_set)
                    except VictorError: break
            heartbeat = threading.Thread(target=keep_alive, name='victor-duck-lease', daemon=True)
            heartbeat.start()
            yield True
        finally:
            stopped.set()
            if heartbeat: heartbeat.join(timeout=.2)
            try: browser.command('duck_end', {'lease': lease})
            except VictorError:
                self.emit('notice', 'No pude confirmar la restauración del volumen. El reproductor intentará recuperarlo automáticamente.')
