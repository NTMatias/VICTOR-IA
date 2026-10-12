"""Reproductor Spotify oficial integrado en VICTOR, sin cliente Spotify desktop.

Loopback + capability aleatoria por ejecución. No expone client_secret, no CORS,
no logs de URL/tokens, comandos solo a través del registro de herramientas.
"""
import json
import secrets
import threading
import time
import logging
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
from victor.errors import VictorError, Cancelled


def decode_state(data):
    """Valida metadatos del SDK antes de cruzar al hilo Qt; no acepta HTML."""
    if not isinstance(data,dict):raise ValueError('Estado inválido')
    result={}
    for key in ('id','name','artists','art_url'):
        value=data.get(key,'')
        if not isinstance(value,str) or len(value)>3000:raise ValueError('Metadato inválido')
        result[key]=value
    for key,maximum in (('volume',100),('position',86400000),('duration',86400000)):
        value=data.get(key,0)
        if isinstance(value,bool) or not isinstance(value,int) or not 0<=value<=maximum:raise ValueError('Número inválido')
        result[key]=value
    if not isinstance(data.get('playing'),bool):raise ValueError('Reproducción inválida')
    result['playing']=data['playing'];result['art']=b''
    return result


class SpotifyWebPlayer:
    def __init__(self, manager, emit, registry=None):
        self.manager, self.emit = manager, emit
        self.registry = registry
        self.secret = secrets.token_urlsafe(32)
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None; self.server = None
        self.device_id = None; self.last_seen = 0
        self.pending = {}; self.serial = 0

    @property
    def active(self):
        with self.lock:
            return bool(self.device_id and time.monotonic()-self.last_seen < 10 and not self.stop_event.is_set())

    def start(self):
        if self.thread and self.thread.is_alive(): return self.url
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                self.request.settimeout(3); super().setup()
            def log_message(self, *args): pass
            def do_GET(self): self.handle_api('GET')
            def do_POST(self): self.handle_api('POST')
            def handle_api(self, method):
                origin = 'http://127.0.0.1:'+str(self.server.server_port)
                path = urlparse(self.path).path
                prefix = '/'+owner.secret+'/'
                if (self.headers.get('Host') != origin[7:] or not path.startswith(prefix)
                        or self.headers.get('Origin', origin) != origin):
                    self.reply(403, {'error':'Acceso denegado'}); return
                try:
                    endpoint = path[len(prefix):]
                    if method=='GET' and not endpoint:
                        html=(Path(__file__).parent/'spotify_web.html').read_bytes()
                        self.reply(200, html, 'text/html; charset=utf-8'); return
                    if method=='GET' and endpoint in ('font','logo'):
                        asset=Path(__file__).parent.parent/'gui'/'assets'/('Inter.ttf' if endpoint=='font' else 'spotify.svg')
                        self.reply(200,asset.read_bytes(),'font/ttf' if endpoint=='font' else 'image/svg+xml');return
                    if method=='GET' and endpoint=='token':
                        self.reply(200, {'token':owner.manager.streaming_token()}); return
                    if method=='GET' and endpoint=='commands':
                        with owner.lock:
                            owner.last_seen=time.monotonic()
                            commands=[{'id':i,'action':p['action'],'args':p['args']} for i,p in owner.pending.items() if not p['sent']]
                            for c in commands: owner.pending[c['id']]['sent']=True
                        self.reply(200, commands); return
                    size=int(self.headers.get('Content-Length','0'))
                    if method!='POST' or size<2 or size>32768:
                        self.reply(400, {'error':'Evento inválido'}); return
                    data=json.loads(self.rfile.read(size))
                    if not isinstance(data,dict): raise ValueError()
                    if endpoint=='browse':
                        if owner.registry is None or data.get('tool') not in {'spotify_search','spotify_collection','spotify_playlists','spotify_item_play'}:
                            self.reply(400, {'error':'Consulta desconocida'});return
                        result=owner.registry.execute(data['tool'],data.get('args',{}))
                        self.reply(200 if result.get('ok') else 400,result.get('result') if result.get('ok') else {'error':result.get('error','La consulta falló.')});return
                    if endpoint=='ready':
                        device=data.get('device','')
                        if not isinstance(device,str) or not 16<=len(device)<=128 or not device.isalnum(): raise ValueError()
                        with owner.lock: owner.device_id=device;owner.last_seen=time.monotonic()
                        if data.get('background') is not True:
                            owner.manager.client().transfer_playback(device,force_play=False)
                        owner.emit('notice','Reproductor VICTOR conectado. Busca una canción o elige una playlist.')
                    elif endpoint=='offline':
                        owner.disconnect()
                    elif endpoint=='state':
                        state=decode_state(data)
                        owner.emit('spotify_browser_state',state)
                    elif endpoint=='result':
                        with owner.lock:
                            p=owner.pending.get(data.get('id'))
                            if p:
                                if p['action']=='duck_begin' and isinstance(data.get('ducked'),bool):p['ducked']=data['ducked']
                                p['ok']=data.get('ok') is True;p['done'].set()
                    else:
                        self.reply(404, {'error':'Ruta desconocida'});return
                    self.reply(200, {'ok':True})
                except (ValueError, TypeError, UnicodeError): self.reply(400, {'error':'Evento inválido'})
                except Exception as exc:
                    if endpoint=='ready':
                        with owner.lock:owner.device_id=None
                    logging.getLogger('victor.spotify').warning('web player request failed type=%s',type(exc).__name__)
                    self.reply(503, {'error':str(exc) if isinstance(exc,VictorError) else 'Spotify no pudo conectar el reproductor. Comprueba Premium y vuelve a conectar tu cuenta.'})
                finally: owner.manager.close_client()
            def reply(self, code, data, content_type='application/json; charset=utf-8'):
                body=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode('utf-8')
                try:
                    self.send_response(code);self.send_header('Content-Type',content_type)
                    self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
                    self.send_header('Referrer-Policy','no-referrer');self.send_header('X-Content-Type-Options','nosniff')
                    self.send_header('Content-Security-Policy',"frame-ancestors 'none'")
                    self.end_headers();self.wfile.write(body)
                except (ConnectionError,TimeoutError):pass
        self.stop_event.clear()
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.server.daemon_threads=True;self.server.timeout=.2
        self.url=f'http://127.0.0.1:{self.server.server_port}/{self.secret}/'
        def serve():
            try:
                while not self.stop_event.is_set():self.server.handle_request()
            finally:self.server.server_close()
        self.thread=threading.Thread(target=serve,name='victor-spotify-web',daemon=True);self.thread.start()
        return self.url

    def command(self, action, args=None, cancel=None):
        allowed={'pause','resume','next','previous','volume','seek','duck_begin','duck_end','duck_keepalive'}
        if action not in allowed:raise VictorError('Control de reproducción desconocido.')
        if not self.active:raise VictorError('El reproductor web se desconectó. Abre Spotify en VICTOR y pulsa Activar audio.')
        with self.lock:
            if len(self.pending)>=12:raise VictorError('Spotify está ocupado. Espera unos segundos.')
            self.serial+=1;identifier=self.serial
            pending={'action':action,'args':args or {},'done':threading.Event(),'ok':False,'sent':False}
            self.pending[identifier]=pending
        try:
            deadline = time.monotonic() + 6
            while not pending['done'].wait(.05):
                if cancel and cancel(): raise Cancelled('Control cancelado.')
                if time.monotonic() > deadline: raise VictorError('El reproductor no respondió. Comprueba que VICTOR siga abierto.')
            if cancel and cancel(): raise Cancelled('Control cancelado.')
            if not pending['ok']:raise VictorError('Spotify rechazó el control. Revisa el aviso en el reproductor integrado.')
            result={'orden_enviada':action,'aceptada_por_api':True, 'destino':'Reproductor VICTOR'}
            if action=='duck_begin' and 'ducked' in pending:result['ducked']=pending['ducked']
            return result
        finally:
            with self.lock:self.pending.pop(identifier,None)

    def disconnect(self):
        with self.lock:
            self.device_id=None;self.last_seen=0
            for p in self.pending.values():p['done'].set()

    def stop(self):
        self.stop_event.set();self.disconnect()
