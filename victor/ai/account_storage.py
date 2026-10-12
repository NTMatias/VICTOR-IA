"""Records protected with the existing Windows DPAPI implementation."""
import json
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from victor.credentials import CredentialStore
from victor.errors import VictorError, check_cancel


class AccountStorage:
    def __init__(self, directory):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.path=self.directory/'chatgpt.dpapi'
        self.lock=threading.RLock()

    @contextmanager
    def transaction(self,cancel=None):
        # A rotating refresh token must also be serialized across app instances.
        import msvcrt
        with self.lock, (self.directory/'chatgpt.lock').open('a+b') as handle:
            if handle.tell()==0:handle.write(b'0');handle.flush()
            event=cancel or threading.Event()
            while True:
                check_cancel(event);handle.seek(0)
                try:msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1);break
                except OSError:event.wait(.1)
            try:yield
            finally:handle.seek(0);msvcrt.locking(handle.fileno(),msvcrt.LK_UNLCK,1)

    def read(self):
        if not self.path.exists():return {'active':'','profiles':{}}
        try:
            result=json.loads(CredentialStore.crypt(self.path.read_bytes(),True))
            if not isinstance(result.get('profiles'),dict):raise ValueError()
            return result
        except Exception:
            raise VictorError('No pude leer la sesión cifrada de ChatGPT; el archivo se conserva.') from None

    def write(self,record):
        blob=CredentialStore.crypt(json.dumps(record,ensure_ascii=False).encode('utf-8'))
        temporary=self.path.with_suffix('.tmp')
        try:temporary.write_bytes(blob);os.replace(temporary,self.path)
        finally:temporary.unlink(missing_ok=True)
