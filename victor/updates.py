"""Signed release discovery and bounded downloads; never overwrites a live installation."""
import base64
import hashlib
import json
from pathlib import Path
import re
import shutil
import threading
import time
from urllib.parse import urlparse,urljoin
import requests
from .version import VERSION
from .deployment import deployment

REPO='/NTMatias/VICTOR-IA'
HOSTS={'github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'}
def version(value):
    m=re.fullmatch(r'v?(\d{1,4})\.(\d{1,4})\.(\d{1,4})',value)
    if not m:raise ValueError('Versión de actualización inválida.')
    return tuple(map(int,m.groups()))
def verify_manifest(envelope,public_key):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if len(public_key)!=64:raise ValueError('Falta la clave pública de actualizaciones.')
    payload=base64.b64decode(envelope['payload'],validate=True);signature=base64.b64decode(envelope['signature'],validate=True)
    if len(payload)>32768:raise ValueError('Aviso demasiado grande.')
    Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key)).verify(signature,payload)
    record=json.loads(payload);version(record['version']);url=urlparse(record['asset_url'])
    expected=REPO+'/releases/download/v'+record['version'].lstrip('v')+'/'
    if url.scheme!='https' or url.hostname!='github.com' or not url.path.startswith(expected) or not re.fullmatch(r'[A-Za-z0-9_.-]+\.zip',url.path[len(expected):]) or url.username or url.password or url.query or url.fragment:raise ValueError('Descarga fuera del repositorio o versión autorizados.')
    if not re.fullmatch('[0-9a-f]{64}',record['sha256']) or type(record['size']) is not int or not 0<record['size']<=4*1024**3:raise ValueError('Tamaño o huella inválidos.')
    return record

class Updates:
    def __init__(self,root,emit):
        self.root=Path(root);self.emit=emit;self.settings=deployment(root).get('updates',{});self.stop_event=threading.Event();self.thread=None;self.download_lock=threading.Lock()
    def _open(self,url):
        for _ in range(6):
            parsed=urlparse(url)
            if parsed.scheme!='https' or parsed.hostname not in HOSTS or parsed.username or parsed.password:raise ValueError('Destino de actualización no autorizado.')
            response=requests.get(url,stream=True,timeout=(5,20),allow_redirects=False)
            if response.status_code in (301,302,303,307,308):
                redirect=response.headers.get('Location','');response.close();url=urljoin(url,redirect);continue
            response.raise_for_status();return response
        raise ValueError('Demasiadas redirecciones.')
    def check(self):
        if not self.settings.get('enabled'):return None
        url=self.settings.get('manifest_url','')
        if not url.startswith('https://github.com'+REPO+'/releases/'):raise ValueError('Configura el feed oficial del proyecto.')
        with self._open(url) as response:
            data=b''
            for block in response.iter_content(4096):
                if self.stop_event.is_set():return None
                data+=block
                if len(data)>65536:raise ValueError('Aviso demasiado grande.')
        record=verify_manifest(json.loads(data),self.settings.get('public_key_hex',''))
        return record if version(record['version'])>version(VERSION) else None
    def start(self):
        if not self.settings.get('enabled') or self.thread and self.thread.is_alive():return
        self.stop_event.clear()
        def run():
            while not self.stop_event.is_set():
                try:
                    record=self.check()
                    if record:self.emit('update_available',record)
                except Exception:self.emit('update_status','No se pudo comprobar la actualización. La app sigue disponible.')
                if self.stop_event.wait(6*3600):break
        self.thread=threading.Thread(target=run,name='victor-update-check',daemon=True);self.thread.start()
    def download(self,record):
        # Revalidate the exact signed record at the UI boundary by using a fresh check.
        if not self.download_lock.acquire(False):raise ValueError('Ya hay una descarga en curso.')
        temporary=None
        try:
            fresh=self.check()
            if fresh!=record:raise ValueError('La versión publicada cambió. Comprueba las actualizaciones de nuevo.')
            directory=self.root/'data/updates';directory.mkdir(parents=True,exist_ok=True)
            if shutil.disk_usage(directory).free<record['size']+100*1024**2:raise ValueError('Falta espacio para descargar la versión.')
            target=directory/('VICTOR-'+record['version']+'.zip');temporary=target.with_suffix('.part');checksum=hashlib.sha256();received=0;stamp=0.
            with self._open(record['asset_url']) as response,temporary.open('wb') as stream:
                for block in response.iter_content(65536):
                    if self.stop_event.is_set():raise ValueError('Descarga cancelada.')
                    received+=len(block)
                    if received>record['size']:raise ValueError('La descarga supera el tamaño firmado.')
                    stream.write(block);checksum.update(block)
                    if time.monotonic()-stamp>.3:self.emit('update_progress',int(received/record['size']*100));stamp=time.monotonic()
            if received!=record['size'] or checksum.hexdigest()!=record['sha256']:raise ValueError('La descarga no coincide con la publicación firmada.')
            temporary.replace(target);return target
        finally:
            if temporary:temporary.unlink(missing_ok=True)
            self.download_lock.release()
    def stop(self):self.stop_event.set()
