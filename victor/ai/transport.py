"""Reuse a provider's HTTP pool between turns; cancel only its current transport."""
import threading
from contextlib import contextmanager

class Transport:
    def __init__(self):self.client=None;self.identity=None;self.lock=threading.RLock()
    def close(self):
        with self.lock:
            if self.client:self.client.close()
            self.client=None;self.identity=None
    @contextmanager
    def use(self,factory,cancel,**options):
        identity=(options.get('api_key'),options.get('base_url'),options.get('timeout'))
        with self.lock:
            if self.client is None or self.identity!=identity:
                self.close();self.client=factory(**options);self.identity=identity
            client=self.client
        done=threading.Event()
        def watch():
            while not done.wait(.05):
                if cancel.is_set():self.close();return
        watcher=threading.Thread(target=watch,name='victor-ai-cancel',daemon=True);watcher.start()
        try:yield client
        finally:done.set();watcher.join(.15)
