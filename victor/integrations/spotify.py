"""Spotify opcional: OAuth explícito, caché DPAPI y llamadas acotadas."""
import ctypes
from ctypes import wintypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import re
import os
import secrets
import threading
import time
import unicodedata
from urllib.parse import urlparse, parse_qs
import webbrowser
from victor.errors import VictorError, check_cancel
from victor.security import Risk
from victor.tools.registry import Tool


class SpotifyUnavailable(VictorError):
    fallback = "spotify"


class EncryptedCache:
    def __init__(self, path):
        self.path = path

    @staticmethod
    def crypt(data, decrypt=False):
        if os.name != "nt":
            raise VictorError("La caché OAuth segura requiere Windows.")
        class Blob(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]
        buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
        incoming, outgoing = Blob(len(data), buffer), Blob()
        function = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
        if not function(ctypes.byref(incoming), None, None, None, None, 1, ctypes.byref(outgoing)):
            raise VictorError("Windows no permitió proteger/leer el token OAuth. No se guarda en texto plano.")
        try:
            return ctypes.string_at(outgoing.pbData, outgoing.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
            ctypes.windll.kernel32.LocalFree(ctypes.cast(outgoing.pbData, ctypes.c_void_p))

    def get_cached_token(self):
        if not self.path.exists():
            return None
        try:
            return json.loads(self.crypt(self.path.read_bytes(), True))
        except (ValueError, OSError, VictorError):
            raise VictorError("No pude leer el token protegido. Vuelve a conectar Spotify desde el PC.") from None

    def save_token_to_cache(self, token_info):
        data = self.crypt(json.dumps(token_info).encode("utf-8"))
        temporary = self.path.with_suffix(".tmp")
        temporary.write_bytes(data)
        os.replace(temporary, self.path)


class SpotifyManager:
    def __init__(self, config):
        self.config = config
        self.lock = threading.Lock()
        self.cache = EncryptedCache(config.data_dir / "spotify.oauth")
        self._auth = None
        self._token = None
        self._clients = threading.local()
        self._premium_until = 0
        self._device_id = None
        self._device_until = 0
        self.browser = None

    def oauth(self):
        if not os.environ.get("SPOTIPY_CLIENT_ID") or not os.environ.get("SPOTIPY_CLIENT_SECRET"):
            raise VictorError("Spotify no configurado: añade SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET y SPOTIPY_REDIRECT_URI a .env y conecta desde el PC.")
        if self._auth is not None:
            return self._auth
        try:
            from spotipy.oauth2 import SpotifyOAuth
            from spotipy.cache_handler import CacheHandler
        except ImportError:
            raise VictorError("Spotify desactivado: instala spotipy con instalar.bat.") from None
        owner = self.cache
        class Cache(CacheHandler):
            def get_cached_token(self):
                return owner.get_cached_token()
            def save_token_to_cache(self, token_info):
                owner.save_token_to_cache(token_info)
        uri = os.environ.get("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
        parsed = urlparse(uri)
        if parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or not parsed.port or parsed.path != "/callback":
            raise VictorError("SPOTIPY_REDIRECT_URI debe ser http://127.0.0.1:PUERTO/callback y coincidir con Spotify Dashboard.")
        self._auth = SpotifyOAuth(client_id=os.environ["SPOTIPY_CLIENT_ID"], client_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
            redirect_uri=uri, scope="user-read-private user-read-playback-state user-modify-playback-state playlist-read-private streaming user-read-email",
            cache_handler=Cache(), open_browser=False, requests_timeout=10)
        return self._auth

    def authorize(self, cancel):
        auth, state, outcome = self.oauth(), secrets.token_urlsafe(24), {}
        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                self.request.settimeout(2)
                super().setup()
            def do_GET(self):
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)
                valid = parsed.path == "/callback" and secrets.compare_digest(query.get("state", [""])[0], state)
                if valid:
                    outcome["code"] = query.get("code", [""])[0]
                self.send_response(200 if valid else 400)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Vuelve a VICTOR.IA." if valid else b"Solicitud no valida.")
            def log_message(self, *args):
                return
        with self.lock:
            with HTTPServer(("127.0.0.1", urlparse(auth.redirect_uri).port), Handler) as server:
                server.timeout = .3
                if not webbrowser.open(auth.get_authorize_url(state=state)):
                    raise VictorError("No se pudo abrir el navegador para conectar Spotify.")
                deadline = time.monotonic()+120
                while not outcome and time.monotonic() < deadline:
                    check_cancel(cancel)
                    server.handle_request()
            if not outcome.get("code"):
                raise VictorError("La autorización Spotify se canceló o caducó.")
            auth.get_access_token(code=outcome["code"], as_dict=True, check_cache=False)
            self._token = None
            self._premium_until = self._device_until = 0
        return "Spotify conectado. Activa el reproductor VICTOR o tu dispositivo Spotify."

    def client(self):
        try:
            import spotipy
        except ImportError:
            raise VictorError("Spotify desactivado: falta spotipy. Ejecuta instalar.bat.") from None
        with self.lock:
            token = self._token
            if not token or token.get("expires_at", 0) <= time.time()+60:
                auth = self.oauth()
                token = auth.validate_token(self.cache.get_cached_token())
                self._token = token
        if not token:
            raise VictorError("Conecta Spotify desde Integraciones en el PC antes de enviar órdenes.")
        # Una sesión HTTP por trabajador: conexiones reutilizadas sin compartir
        # requests.Session entre el polling y los controles.
        entry = getattr(self._clients, 'entry', None)
        if entry and entry[0] == token['access_token']:
            return entry[1]
        if entry:
            session = getattr(entry[1], '_session', None)
            if session: session.close()
        client = spotipy.Spotify(auth=token["access_token"], requests_timeout=(3, 5), retries=0, status_retries=0)
        self._clients.entry = (token['access_token'], client)
        return client

    def streaming_token(self):
        self.client()  # Renueva el token con el mismo flujo OAuth y caché cifrada.
        with self.lock:
            token=dict(self._token or {})
        if 'streaming' not in token.get('scope','').split():
            raise VictorError('Vuelve a pulsar Conectar Spotify para conceder el permiso streaming al reproductor VICTOR.')
        return token['access_token']

    def close_client(self):
        """Cierra la conexión HTTP del trabajador actual al terminar su cola."""
        entry=getattr(self._clients,'entry',None)
        if entry:
            try:
                session=getattr(entry[1],'_session',None)
                if session:session.close()
            finally:del self._clients.entry

    def device(self, client):
        now = time.monotonic()
        with self.lock:
            premium = self._premium_until > now
            cached = self._device_id if self._device_until > now else None
        if not premium:
            if client.current_user().get("product") != "premium":
                raise SpotifyUnavailable("El control requiere Spotify Premium. Intentaré abrir la aplicación como alternativa.")
            with self.lock: self._premium_until = now + 300
        if self.browser and self.browser.active:
            return self.browser.device_id
        if cached:
            return cached
        configured = os.environ.get("SPOTIPY_DEVICE_ID", "")
        devices = [d for d in client.devices().get("devices", []) if d.get("type") == "Computer" and d.get("is_active") and (not configured or d.get("id") == configured)]
        if not devices:
            raise SpotifyUnavailable("No hay un dispositivo Spotify activo del PC. Abre Spotify y reproduce algo; intentaré abrir la aplicación.")
        with self.lock:
            self._device_id, self._device_until = devices[0]['id'], now+5
        return devices[0]["id"]

    def observe_playback(self, state):
        """El polling ya consulta el dispositivo; evita repetir esa consulta al pulsar."""
        device = (state or {}).get('device', {})
        configured = os.getenv('SPOTIPY_DEVICE_ID', '')
        with self.lock:
            if (device.get('id') and device.get('type') == 'Computer' and device.get('is_active', True)
                    and (not configured or device['id'] == configured)):
                self._device_id, self._device_until = device['id'], time.monotonic()+5
            else:
                self._device_until = 0

    @staticmethod
    def playback(client):
        state = client.current_playback()
        if not state or not state.get("item"):
            return {"reproduciendo": False, "aviso": "No hay canción activa."}
        item = state["item"]
        return {"reproduciendo": bool(state.get("is_playing")), "cancion": item.get("name"),
                "artistas": [a["name"] for a in item.get("artists", [])], "uri": item.get("uri"),
                "dispositivo": state.get("device", {}).get("name")}

    def play(self, query):
        from victor.integrations.music_intent import artist_request
        artist = artist_request(query)
        if artist:
            return self.play_artist(artist)
        if re.fullmatch(r"(?:cualquier|alguna|una)\s+canci[oó]n(?:\s+de)?",query.strip(),re.I):
            raise VictorError('Dime de qué artista quieres escuchar una canción.')
        client = self.client()
        from victor.integrations.music_match import exact_match, nearest_match, split_query
        def matches(row):
            if not row or not catalog_item(row,'track')['available']:return False
            return exact_match(query,row)
        title,requested_artist=split_query(query)
        search_query=('track:"'+title.replace('"',' ')+'" artist:"'+requested_artist.replace('"',' ')+'"') if requested_artist else query
        tracks=catalog_request(lambda:client.search(q=query,type='track',limit=10)).get('tracks',{}).get('items',[])
        pool=list(tracks)
        candidates=[row for row in tracks if matches(row)]
        if not candidates:
            # Spotify can rank a related hit first; ask for the title explicitly.
            scoped=search_query if requested_artist else 'track:"'+query.replace('"',' ').strip()+'"'
            tracks=catalog_request(lambda:client.search(q=scoped,type='track',limit=10)).get('tracks',{}).get('items',[])
            pool.extend(tracks)
            candidates=[row for row in tracks if matches(row)]
        approximate=None
        if not candidates:
            available=lambda:[row for row in pool if row and catalog_item(row,'track')['available']]
            approximate=nearest_match(query,available())
            if approximate is None and requested_artist:
                # Un artista mal transcrito puede ocultar el título correcto.
                pool.extend(catalog_request(lambda:client.search(q=title,type='track',limit=10)).get('tracks',{}).get('items',[]))
                candidates=[row for row in pool if matches(row)]
                if not candidates:approximate=nearest_match(query,available())
            if not candidates and approximate is None and requested_artist:
                # La búsqueda literal del título/artista puede ser demasiado estricta
                # para un dictado. Conservar el artista como guía de recuperación;
                # la elección sigue validando ambos campos del catálogo.
                terms=' '.join(re.findall(r'[^\W_]+',title+' '+requested_artist))
                pool.extend(catalog_request(lambda:client.search(q=terms,type='track',limit=10)).get('tracks',{}).get('items',[]))
                candidates=[row for row in pool if matches(row)]
                if not candidates:approximate=nearest_match(query,available())
            if not candidates and approximate is None:
                raise VictorError('No encontré una coincidencia suficientemente cercana para «'+query+'». Prueba con otro dato de la canción o elige un resultado en Spotify de VICTOR.')
        selected=max(candidates,key=lambda row:row.get('popularity',0) or 0) if candidates else approximate[0]
        result=self.play_selected(client, selected)
        if not candidates:result['coincidencia']={'consulta':query,'tipo':'aproximada','similitud':approximate[1]}
        return result

    def play_artist(self, artist):
        client = self.client()
        def normalized(value):
            return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in unicodedata.normalize('NFKD',value).casefold() if not unicodedata.combining(c))))
        requested = normalized(artist)
        tracks = catalog_request(lambda:client.search(q='artist:"'+artist.replace('"',' ')+'"',type='track',limit=10)).get('tracks',{}).get('items',[])
        candidates = [row for row in tracks if row and catalog_item(row,'track')['available']
                      and any(normalized(a.get('name',''))==requested for a in row.get('artists',[]))]
        if not candidates:
            raise VictorError('No encontré canciones disponibles del artista «'+artist+'». Revisa su nombre.')
        last = getattr(self, '_last_artist_track', {})
        options = [row for row in candidates if row.get('id') != last.get(requested)] or candidates
        selected = secrets.choice(options)
        result = self.play_selected(client, selected)
        if len(last) >= 32:last.clear()
        last[requested] = selected.get('id');self._last_artist_track=last
        result['artista_solicitado'] = artist
        return result

    def play_selected(self, client, selected):
        uri=selected['uri'];device=self.device(client)
        client.start_playback(device_id=device, uris=[uri])
        if self.browser and self.browser.active:
            # La confirmación audible/actual llega por player_state_changed del SDK.
            return {'orden_enviada':'Reproducir canción','solicitada':selected['name'],'seleccion':catalog_item(selected,'track'),
                    'aceptada_por_api':True,'aviso':'El estado real se actualiza desde el reproductor VICTOR.'}
        actual = self.playback(client)
        actual["solicitada"] = selected['name']
        actual['seleccion']=catalog_item(selected,'track')
        actual["confirmada"] = actual.get("uri") == uri and actual.get("reproduciendo", False)
        if not actual["confirmada"]:
            actual["aviso"] = "Orden enviada; la pista solicitada aún no está confirmada como reproducción actual."
        return actual

    def action(self, action, level=None):
        if self.browser and self.browser.active:
            result=self.browser.command(action, {'level':level} if action=='volume' else {})
            if action=='volume':result['nivel_solicitado']=level
            return result
        client = self.client()
        device = self.device(client)
        if action == "pause":
            client.pause_playback(device_id=device)
        elif action == "next":
            client.next_track(device_id=device)
        elif action == "previous":
            client.previous_track(device_id=device)
        elif action == "volume":
            client.volume(level, device_id=device)
        # La respuesta HTTP confirma recepción, no el estado final del dispositivo.
        # El worker de estado reconcilia inmediatamente sin añadir otro GET aquí.
        result={"orden_enviada": action, "aceptada_por_api": True}
        if action=='volume':result['nivel_solicitado']=level
        return result

    def current_track(self):
        return self.playback(self.client())

    def playlists(self):
        return [{"nombre": row["name"], "id": row["id"], "url": row.get("external_urls", {}).get("spotify"), "propietario":row.get("owner",{}).get("display_name", "Playlist de Spotify"), "descripcion":row.get("description", ""),
                 **catalog_item(row, 'playlist')}
                for row in self.client().current_user_playlists(limit=50).get("items", []) if row]

    def search_catalog(self, query, category, offset):
        """Busca sin reproducir; diez resultados por tipo, paginación explícita."""
        kinds = 'track,playlist,show,episode,album' if category == 'all' else category
        client = self.client()
        data = catalog_request(lambda: client.search(q=query, type=kinds, limit=10, offset=offset))
        rows = []
        more = False
        for kind in kinds.split(','):
            page = data.get(kind+'s', {}) or {}
            rows.extend(catalog_item(row, kind) for row in page.get('items', []) if row)
            more = more or bool(page.get('next'))
        return {'items':rows, 'query':query, 'category':category, 'offset':offset,
                'next_offset':offset+10 if more and offset < 1000 else None}

    def collection_items(self, kind, identifier, offset):
        """Una página por llamada: mantiene orden/duplicados y posición real de la playlist."""
        client = self.client()
        if kind == 'playlist':
            page = catalog_request(lambda: client.playlist_items(identifier, limit=50, offset=offset), playlist=True)
        elif kind == 'show':
            page = catalog_request(lambda: client.show_episodes(identifier, limit=50, offset=offset))
        else:
            page = catalog_request(lambda: client.album_tracks(identifier, limit=50, offset=offset))
            entries=page.get('items',[])
            if any(row and not (row.get('album') or {}).get('images') for row in entries):
                album=catalog_request(lambda: client.album(identifier))
                for row in entries:
                    if row:row.setdefault('album',{})['images']=album.get('images',[])
        rows = []
        for index, entry in enumerate(page.get('items', [])):
            if not entry: continue
            item = (entry.get('item') or entry.get('track')) if kind == 'playlist' else entry
            if not item: continue
            row = catalog_item(item, 'episode' if kind == 'show' else 'track')
            row.update(context='spotify:'+kind+':'+identifier if kind != 'show' else '', position=offset+index)
            rows.append(row)
        return {'items':rows, 'kind':kind, 'identifier':identifier, 'offset':offset,
                'total':page.get('total',len(rows)), 'next_offset':offset+len(page.get('items', [])) if page.get('next') and page.get('items') else None}

    def play_item(self, uri, context, position):
        """Reproduce la elección exacta, sin otra búsqueda que pueda cambiar de canción."""
        if not re.fullmatch(r'spotify:(track|episode):[A-Za-z0-9]{22}', uri):
            raise VictorError('Esta canción no se puede reproducir desde Spotify.')
        if context and not re.fullmatch(r'spotify:(playlist|album):[A-Za-z0-9]{22}', context):
            raise VictorError('Colección de Spotify inválida.')
        client = self.client()
        options = {'context_uri':context,'offset':{'position':position}} if context else {'uris':[uri]}
        catalog_request(lambda: client.start_playback(device_id=self.device(client), **options))
        return {'orden_enviada':'Reproducir selección', 'aceptada_por_api':True, 'uri':uri}

    def seek(self, position):
        if self.browser and self.browser.active:return self.browser.command('seek',{'position':position})
        client=self.client();client.seek_track(position,device_id=self.device(client))
        return {'orden_enviada':'Posición de reproducción','milisegundos_solicitados':position,'aceptada_por_api':True}

    def play_playlist(self, playlist_id):
        client=self.client();client.start_playback(device_id=self.device(client),context_uri='spotify:playlist:'+playlist_id)
        return {'orden_enviada':'Reproducir playlist','aceptada_por_api':True}


def register_spotify(core):
    manager = SpotifyManager(core.config)
    def add(name, description, function, risk=Risk.MEDIUM, **args):
        core.registry.register(Tool(name, description, {"type": "object", "properties": args, "required": list(args), "additionalProperties": False}, risk, function))
    add("spotify_play", "Reproduce un título concreto o elige una canción del artista si piden 'cualquier canción de ARTISTA', 'una canción de ARTISTA' o 'música de ARTISTA'.", manager.play, query={"type": "string", "minLength": 1, "maxLength": 300})
    add("spotify_pause", "Pausa Spotify.", lambda: manager.action("pause"))
    add("spotify_next", "Siguiente pista Spotify.", lambda: manager.action("next"))
    add("spotify_previous", "Pista anterior Spotify.", lambda: manager.action("previous"))
    add("spotify_volume", "Ajusta volumen Spotify.", lambda level: manager.action("volume", level), level={"type": "integer", "minimum": 0, "maximum": 100})
    add("spotify_current_track", "Consulta la canción actual real.", manager.current_track, Risk.LOW)
    add("spotify_playlists", "Lista hasta 50 playlists del usuario conectado.", manager.playlists, Risk.LOW)
    add('spotify_seek','Cambiar posición de la pista actual.',manager.seek,position={'type':'integer','minimum':0,'maximum':86400000})
    add('spotify_playlist_play','Reproduce una playlist del usuario en el PC activo.',manager.play_playlist,
        playlist_id={'type':'string','pattern':'^[A-Za-z0-9]{22}$'})
    add('spotify_search','Busca canciones, playlists, álbumes, podcasts y episodios sin reproducir.',manager.search_catalog,Risk.LOW,
        query={'type':'string','minLength':1,'maxLength':300},category={'type':'string','enum':['all','track','playlist','show','episode','album']},offset={'type':'integer','minimum':0,'maximum':1000})
    add('spotify_collection','Consulta canciones de una playlist/álbum o episodios de un podcast sin reproducir.',manager.collection_items,Risk.LOW,
        kind={'type':'string','enum':['playlist','album','show']},identifier={'type':'string','pattern':'^[A-Za-z0-9]{22}$'},offset={'type':'integer','minimum':0,'maximum':100000})
    add('spotify_item_play','Reproduce la canción o episodio seleccionado y conserva el orden de la playlist.',manager.play_item,
        uri={'type':'string','pattern':'^spotify:(track|episode):[A-Za-z0-9]{22}$'},context={'type':'string','pattern':'^(spotify:(playlist|album):[A-Za-z0-9]{22})?$'},position={'type':'integer','minimum':0,'maximum':100000})
    return manager


def catalog_item(row, kind):
    """Metadatos comunes para Qt y web; nunca HTML ni URLs de audio."""
    kind = row.get('type') or kind
    images = row.get('images') or (row.get('album') or {}).get('images') or []
    image = max((i for i in images if i.get('url')),key=lambda i:(i.get('width') or 0)*(i.get('height') or 0),default={}).get('url','')
    artists = ', '.join(a.get('name','') for a in row.get('artists',[]))
    subtitle = artists or row.get('publisher') or (row.get('owner') or {}).get('display_name') or (row.get('show') or {}).get('name') or ''
    uri = row.get('uri') or 'spotify:'+kind+':'+str(row.get('id') or '')
    return {'id':row.get('id') or '', 'kind':kind, 'name':row.get('name') or 'Sin título',
            'subtitle':subtitle, 'image':image, 'uri':uri, 'url':(row.get('external_urls') or {}).get('spotify') or '',
            'duration':row.get('duration_ms',0), 'available':not row.get('is_local',False) and row.get('is_playable') is not False and not row.get('restrictions') and bool(re.fullmatch(r'spotify:(track|episode|playlist|album|show):[A-Za-z0-9]{22}',uri))}


def catalog_request(request, playlist=False):
    """Errores comprensibles; los cuerpos OAuth/HTTP nunca se presentan al usuario."""
    try: return request()
    except VictorError: raise
    except Exception as exc:
        status = getattr(exc,'http_status',None)
        if status == 403 and playlist:
            raise VictorError('Spotify solo permite consultar esta playlist si eres su propietario o colaborador. Puedes abrirla en Spotify.') from None
        if status in (401,403): raise VictorError('Spotify rechazó el acceso. Reconecta tu cuenta y revisa los permisos y Premium.') from None
        if status == 429: raise VictorError('Spotify limitó las consultas. Espera antes de buscar de nuevo.') from None
        if status == 404: raise VictorError('Spotify no encontró este contenido o no está disponible para tu cuenta.') from None
        raise VictorError('No pude completar la consulta a Spotify. Comprueba tu conexión e inténtalo otra vez.') from None
