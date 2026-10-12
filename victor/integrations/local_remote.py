"""Servidor HTTPS opt-in, emparejamiento efímero y ejecución por VictorCore."""
import asyncio
from collections import deque
from datetime import datetime, timedelta, timezone
import io
import ipaddress
import json
import logging
import os
from pathlib import Path
import secrets
import socket
import tempfile
import threading
import time
from victor.errors import VictorError, check_cancel
from victor.integrations.spotify import EncryptedCache
from victor.integrations.remote_page import PAGE
from victor.security import Risk
from victor.tools.registry import Tool


class LocalRemote:
    def __init__(self, config, core, emit):
        self.config,self.core,self.emit=config,core,emit
        self.thread=None
        self.server=None
        self.stop_event=threading.Event()
        self.ready=threading.Event()
        self.lock=threading.RLock()
        self.sessions={}
        self.pair_code=''
        self.pair_deadline=0
        self.address=''
        self.port=8443
        self.frames={}
        self.keyboard_workers=set()
        self.certificate_expiry=None
        from victor.integrations.remote_touch import register_touch
        register_touch(self)
        self.capture_thread=None
        self.log=logging.getLogger('victor.remote')
        core.security.local_authorizer=self.authorized
        event={'type':'object','properties':{'kind':{'enum':['move','left','right','double','up','down']},
             'dx':{'type':'integer','minimum':-500,'maximum':500},'dy':{'type':'integer','minimum':-500,'maximum':500}},
             'required':['kind','dx','dy'],'additionalProperties':False}
        core.registry.register(Tool('remote_pointer_batch','Lote de puntero remoto: desplazamientos relativos, clics y scroll sobre la ventana exacta. Revisa cada evento.',
            {'type':'object','properties':{'window':{'type':'string','minLength':1,'maxLength':300},'events':{'type':'array','items':event,'minItems':1,'maxItems':20}},
             'required':['window','events'],'additionalProperties':False},Risk.MEDIUM,self.pointer_batch))
        core.registry.register(Tool('remote_screen_stream','Compartir el escritorio con el dispositivo local emparejado durante 60 segundos. Puede mostrar información privada.',
             {'type':'object','properties':{},'additionalProperties':False},Risk.MEDIUM,self.start_stream))

    @property
    def running(self):
        return bool(self.thread and self.thread.is_alive())

    def authorized(self, origin):
        with self.lock:
            entry=self.sessions.get(origin.get('session'))
            return bool(entry and entry['expires']>time.monotonic() and self.ready.is_set()
                        and (self.certificate_expiry is None or time.time()<self.certificate_expiry)
                        and (not origin.get('keyboard_channel') or entry.get('keyboard_channel')==origin['keyboard_channel'])
                        and self.config.get('local_remote_enabled') and not self.config.get('remote_block_all'))

    def pair(self, code, peer):
        with self.lock:
            if not self.pair_code or time.monotonic()>self.pair_deadline or not secrets.compare_digest(code,self.pair_code):
                raise VictorError('Código QR inválido o caducado. Genera otro en el PC.')
            self.pair_code=''
            self.sessions={k:v for k,v in self.sessions.items() if v['expires']>time.monotonic()}
            if len(self.sessions)>=4:raise VictorError('Máximo cuatro dispositivos. Detén el servidor para revocar sesiones.')
            token=secrets.token_urlsafe(32)
            self.sessions[token]={'peer':peer,'expires':time.monotonic()+600,'stream_until':0,'out':deque(maxlen=12)}
            return token

    def qr_url(self):
        if not self.ready.is_set():
            raise VictorError('Espera a que el servidor HTTPS esté listo.')
        with self.lock:
            self.pair_code=secrets.token_urlsafe(24)
            self.pair_deadline=time.monotonic()+120
        return f'https://{self.address}:{self.port}/#{self.pair_code}'

    def start(self):
        if self.running:
            return
        self.stop_event.clear()
        self.thread=threading.Thread(target=self.run,name='victor-local-https',daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set(); self.ready.clear()
        with self.lock:
            for worker in self.keyboard_workers:worker.stop()
            self.sessions.clear(); self.pair_code=''; self.frames.clear()
        if getattr(self.core,'active_origin',{}):
            if self.core.active_origin.get('source')=='local_web': self.core.stop()
        if self.server: self.server.should_exit=True

    def reply(self, origin, text, done=False):
        with self.lock:
            entry=self.sessions.get(origin.get('session'))
            if entry: entry['out'].append({'message':str(text)[:12000],'done':done})

    @staticmethod
    def local_ip():
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
            sock.connect(('192.0.2.1',9))  # Selección de ruta; UDP connect no envía paquetes.
            address=sock.getsockname()[0]
        if not ipaddress.ip_address(address).is_private:
            raise VictorError('No encontré una IP local privada. Conecta el PC a tu red Wi-Fi.')
        return address

    def certificate(self, address):
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        folder=self.config.data_dir/'remote_tls'; folder.mkdir(exist_ok=True)
        cert_path,key_path=folder/'certificate.pem',folder/'private.dpapi'
        if cert_path.exists() and key_path.exists():
            cert=x509.load_pem_x509_certificate(cert_path.read_bytes())
            ips=cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value.get_values_for_type(x509.IPAddress)
            if ipaddress.ip_address(address) in ips and cert.not_valid_after_utc>datetime.now(timezone.utc):
                return cert_path.read_bytes(),EncryptedCache.crypt(key_path.read_bytes(),True)
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'VICTOR local')])
        cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(x509.random_serial_number())
              .not_valid_before(datetime.now(timezone.utc)-timedelta(minutes=1)).not_valid_after(datetime.now(timezone.utc)+timedelta(days=30))
              .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address(address)),x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False)
              .sign(key,hashes.SHA256()))
        certificate=cert.public_bytes(serialization.Encoding.PEM)
        private=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
        try:
            key_path.write_bytes(EncryptedCache.crypt(private))
        except VictorError:
            # TLS puede ser efímero; nunca se degrada la protección de tokens OAuth.
            self.emit('notice','DPAPI no disponible: HTTPS usará una clave temporal, eliminada al detener el servidor. El certificado cambiará al reiniciar.')
        cert_path.write_bytes(certificate)
        return certificate,private

    def run(self):
        try:
            import uvicorn
            self.address=self.local_ip()
            self.port=int(os.getenv('REMOTE_PORT','8443'))
            if not 1024<=self.port<=65535: raise VictorError('REMOTE_PORT debe estar entre 1024 y 65535.')
            cert,key=self.certificate(self.address)
            from cryptography import x509
            self.certificate_expiry=x509.load_pem_x509_certificate(cert).not_valid_after_utc.timestamp()
            with tempfile.TemporaryDirectory(prefix='victor-tls-') as folder:
                cp,kp=Path(folder)/'cert.pem',Path(folder)/'key.pem'
                cp.write_bytes(cert); kp.write_bytes(key)
                config=uvicorn.Config(self.create_app(),host=self.address,port=self.port,ssl_certfile=str(cp),ssl_keyfile=str(kp),
                    access_log=False,log_level='warning',ws_max_size=20000,ws_max_queue=4,timeout_graceful_shutdown=3,limit_concurrency=12)
                self.server=uvicorn.Server(config)
                self.server.run()
        except Exception as exc:
            self.log.warning('server failed type=%s',type(exc).__name__)
            self.emit('notice',str(exc) if isinstance(exc,VictorError) else 'Remoto local no disponible. Revisa dependencias, IP privada, puerto libre y permisos de Windows.')
        finally:
            self.stop()

    def create_app(self):
        from fastapi import FastAPI, WebSocket
        from fastapi.responses import HTMLResponse
        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def lifespan(app):
            self.ready.set()
            self.emit('notice','Servidor HTTPS local listo. Genera el QR desde Conectar.')
            try: yield
            finally: self.ready.clear()
        app=FastAPI(lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)
        @app.get('/')
        async def index():
            return HTMLResponse(PAGE,headers={'Cache-Control':'no-store','Referrer-Policy':'no-referrer',
                'X-Frame-Options':'DENY','Content-Security-Policy':"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'"})
        async def authenticate(ws, pairing):
            if ws.headers.get('origin')!=f'https://{self.address}:{self.port}':
                await ws.close(code=1008); return None
            await ws.accept()
            data=json.loads(await asyncio.wait_for(ws.receive_text(),timeout=5))
            token=self.pair(str(data.get('code','')),ws.client.host) if pairing else data.get('session','')
            origin={'source':'local_web','session':token,'user_id':'LAN '+ws.client.host}
            if not self.authorized(origin) or self.sessions[token]['peer']!=ws.client.host:
                await ws.close(code=1008); return None
            await ws.send_json({'session':token} if pairing else {'ready':True})
            return origin
        @app.websocket('/control')
        async def control(ws: WebSocket):
            origin=None
            try:
                origin=await authenticate(ws,True)
                if not origin:return
                stamp=0
                while self.authorized(origin):
                    with self.lock:
                        messages=list(self.sessions[origin['session']]['out']); self.sessions[origin['session']]['out'].clear()
                    for msg in messages: await asyncio.wait_for(ws.send_json(msg),5)
                    try: data=json.loads(await asyncio.wait_for(ws.receive_text(),.15))
                    except asyncio.TimeoutError: continue
                    if isinstance(data,dict) and data=={'type':'ping'}:
                        await ws.send_json({'type':'pong'});continue
                    if time.monotonic()-stamp<.45:
                        await ws.send_json({'error':'Límite de frecuencia.','done':True});continue
                    stamp=time.monotonic()
                    if not isinstance(data,dict) or data.get('tool') not in ('remote_pointer_batch','remote_touch','type_text','press_keys','remote_screen_stream'):
                        await ws.send_json({'error':'Herramienta remota no permitida.','done':True});continue
                    self.emit('remote_command',{'text':'Remoto local: '+data['tool'],'tool':(data['tool'],data.get('args',{})),'origin':origin})
            except Exception:
                try: await ws.close(code=1008)
                except Exception: pass
            finally:
                if origin:
                    with self.lock: self.sessions.pop(origin['session'],None);self.frames.pop(origin['session'],None)
                try:await ws.close(code=1000)
                except Exception:pass
        @app.websocket('/screen')
        async def screen(ws: WebSocket):
            try:
                origin=await authenticate(ws,False)
                if not origin:return
                stamp=0
                while self.authorized(origin):
                    with self.lock: frame=self.frames.get(origin['session'])
                    if frame and frame[0]!=stamp:
                        stamp=frame[0]
                        if isinstance(frame[1],bytes):
                            metadata=frame[2] if len(frame)>2 else {}
                            await asyncio.wait_for(ws.send_json({'frame':metadata}),3)
                            await asyncio.wait_for(ws.send_bytes(frame[1]),3)
                        else:await asyncio.wait_for(ws.send_json({'error':frame[1]}),3)
                    await asyncio.sleep(.03)
            except Exception:
                try:await ws.close(code=1008)
                except Exception:pass
        from victor.integrations.keyboard_socket import install_keyboard_route
        install_keyboard_route(app,self,authenticate)
        return app

    def pointer_batch(self,window,events):
        if not self.authorized(self.core.security.origin() or {}):raise VictorError('Se requiere sesión local autorizada.')
        gui,target=self.core.automation.prepare(window)
        for event in events:
            self.core.security.validate_origin(); check_cancel(self.core.cancel)
            if not target.isActive:raise VictorError('La ventana perdió el foco; lote detenido.')
            gui.failSafeCheck()
            x,y=gui.position()
            kind=event['kind']
            if kind=='move':
                x=max(target.left,min(target.right-1,x+event['dx']));y=max(target.top,min(target.bottom-1,y+event['dy']))
                gui.moveTo(x,y,duration=.05)
            else:
                if not target.left<=x<target.right or not target.top<=y<target.bottom:raise VictorError('Puntero fuera de la ventana autorizada.')
                if kind in ('up','down'):gui.scroll(3 if kind=='up' else -3)
                else:gui.click(button='right' if kind=='right' else 'left',clicks=2 if kind=='double' else 1,interval=.1)
        return {'eventos_ejecutados':len(events),'ventana':window}

    def start_stream(self):
        origin=self.core.security.origin() or {}
        if not self.authorized(origin):raise VictorError('Se requiere sesión local autorizada.')
        try:
            self.stream_fps=max(1,min(20,int(os.getenv('SCREEN_FPS','10'))))
            self.stream_quality=max(20,min(90,int(os.getenv('SCREEN_QUALITY','60'))))
        except ValueError:
            raise VictorError('SCREEN_FPS y SCREEN_QUALITY deben ser enteros en .env.') from None
        with self.lock:self.sessions[origin['session']]['stream_until']=time.monotonic()+60
        if not self.capture_thread or not self.capture_thread.is_alive():
            self.capture_thread=threading.Thread(target=self.capture_loop,name='victor-screen-stream',daemon=True)
            self.capture_thread.start()
        return {'pantalla_autorizada_segundos':60}

    def capture_loop(self):
        fps=self.stream_fps
        quality=self.stream_quality
        while not self.stop_event.is_set():
            start=time.monotonic()
            with self.lock: targets=[k for k,v in self.sessions.items() if v['stream_until']>start and self.authorized({'session':k})]
            if not targets:return
            try:
                from PIL import Image,ImageGrab
                try:
                    import mss
                    with mss.MSS() as display:
                        area=display.monitors[0]
                        shot=display.grab(area);image=Image.frombytes('RGB',shot.size,shot.rgb)
                        left,top=area['left'],area['top']
                except Exception:
                    image=ImageGrab.grab(all_screens=True).convert('RGB')
                    import ctypes
                    left=ctypes.windll.user32.GetSystemMetrics(76) if os.name=='nt' else 0
                    top=ctypes.windll.user32.GetSystemMetrics(77) if os.name=='nt' else 0
                frame_id=secrets.token_hex(12)
                geometry={'left':left,'top':top,'width':image.width,'height':image.height,'time':time.monotonic()}
                image.thumbnail((1920,1080))
                buffer=io.BytesIO();image.save(buffer,format='JPEG',quality=quality);data=buffer.getvalue()
            except Exception:
                data='Windows no permitió capturar la pantalla. Se detuvo la transmisión.'
            with self.lock:
                for token in targets:
                    if token in self.sessions:
                        if isinstance(data,bytes):
                            self.frame_history[frame_id]=geometry
                            self.frame_history={k:v for k,v in self.frame_history.items() if time.monotonic()-v['time']<=30}
                            self.frames[token]=(time.monotonic(),data,{'id':frame_id,'width':image.width,'height':image.height})
                        else:self.frames[token]=(time.monotonic(),data)
                        if not isinstance(data,bytes):self.sessions[token]['stream_until']=0
            self.stop_event.wait(max(.01,1/fps-(time.monotonic()-start)))
