"""Spotify opcional: OAuth explícito, caché DPAPI y llamadas acotadas."""
import ctypes
from ctypes import wintypes
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import secrets
import threading
import time
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

    def oauth(self):
        if not os.environ.get("SPOTIPY_CLIENT_ID") or not os.environ.get("SPOTIPY_CLIENT_SECRET"):
            raise VictorError("Spotify no configurado: añade SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET y SPOTIPY_REDIRECT_URI a .env y conecta desde el PC.")
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
        return SpotifyOAuth(client_id=os.environ["SPOTIPY_CLIENT_ID"], client_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
            redirect_uri=uri, scope="user-read-private user-read-playback-state user-modify-playback-state playlist-read-private",
            cache_handler=Cache(), open_browser=False, requests_timeout=10)

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
        return "Spotify conectado. Activa su aplicación en el PC."

    def client(self):
        try:
            import spotipy
        except ImportError:
            raise VictorError("Spotify desactivado: falta spotipy. Ejecuta instalar.bat.") from None
        with self.lock:
            auth = self.oauth()
            token = auth.validate_token(self.cache.get_cached_token())
        if not token:
            raise VictorError("Conecta Spotify desde Integraciones en el PC antes de enviar órdenes.")
        return spotipy.Spotify(auth=token["access_token"], requests_timeout=10, retries=0, status_retries=0)

    def device(self, client):
        if client.current_user().get("product") != "premium":
            raise SpotifyUnavailable("El control requiere Spotify Premium. Intentaré abrir la aplicación como alternativa.")
        configured = os.environ.get("SPOTIPY_DEVICE_ID", "")
        devices = [d for d in client.devices().get("devices", []) if d.get("type") == "Computer" and d.get("is_active") and (not configured or d.get("id") == configured)]
        if not devices:
            raise SpotifyUnavailable("No hay un dispositivo Spotify activo del PC. Abre Spotify y reproduce algo; intentaré abrir la aplicación.")
        return devices[0]["id"]

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
        client = self.client()
        device = self.device(client)
        tracks = client.search(q=query, type="track", limit=1).get("tracks", {}).get("items", [])
        if not tracks:
            raise VictorError("Spotify no encontró una pista para esa búsqueda.")
        uri = tracks[0]["uri"]
        client.start_playback(device_id=device, uris=[uri])
        time.sleep(.5)
        actual = self.playback(client)
        actual["solicitada"] = tracks[0]["name"]
        actual["confirmada"] = actual.get("uri") == uri and actual.get("reproduciendo", False)
        if not actual["confirmada"]:
            actual["aviso"] = "Orden enviada; la pista solicitada aún no está confirmada como reproducción actual."
        return actual

    def action(self, action, level=None):
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
        return {"orden_enviada": action, "estado": self.playback(client)}

    def current_track(self):
        return self.playback(self.client())

    def playlists(self):
        return [{"nombre": row["name"], "id": row["id"], "url": row.get("external_urls", {}).get("spotify")}
                for row in self.client().current_user_playlists(limit=50).get("items", []) if row]


def register_spotify(core):
    manager = SpotifyManager(core.config)
    def add(name, description, function, risk=Risk.MEDIUM, **args):
        core.registry.register(Tool(name, description, {"type": "object", "properties": args, "required": list(args), "additionalProperties": False}, risk, function))
    add("spotify_play", "Busca y reproduce una pista en el PC activo; comprueba qué suena.", manager.play, query={"type": "string", "minLength": 1, "maxLength": 300})
    add("spotify_pause", "Pausa Spotify.", lambda: manager.action("pause"))
    add("spotify_next", "Siguiente pista Spotify.", lambda: manager.action("next"))
    add("spotify_previous", "Pista anterior Spotify.", lambda: manager.action("previous"))
    add("spotify_volume", "Ajusta volumen Spotify.", lambda level: manager.action("volume", level), level={"type": "integer", "minimum": 0, "maximum": 100})
    add("spotify_current_track", "Consulta la canción actual real.", manager.current_track, Risk.LOW)
    add("spotify_playlists", "Lista hasta 50 playlists del usuario conectado.", manager.playlists, Risk.LOW)
    return manager
