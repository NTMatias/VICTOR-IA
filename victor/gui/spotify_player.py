"""Mini reproductor: consulta pasiva y controles por el orquestador existente."""
import logging
import threading
import queue
import time
from urllib.parse import urlparse
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame,QLabel,QPushButton,QSlider,QVBoxLayout,QHBoxLayout
from victor.security import Risk
from victor.tools.registry import Tool
from victor.gui.widgets import icon


def best_cover(images):
    """Elegir resolución máxima independientemente del orden de la API."""
    return max((i for i in images if i.get('url')),key=lambda i:(i.get('width') or 0)*(i.get('height') or 0),default={}).get('url','')


class SpotifyPoller:
    def __init__(self,core,emit):
        self.core,self.emit=core,emit
        self.stop_event=threading.Event()
        self.refresh_event=threading.Event()
        self.thread=threading.Thread(target=self.run,name='victor-spotify-status',daemon=True)
        self.art_url='';self.art=b''
        self.art_requests=queue.Queue(maxsize=1)
        self.art_thread=threading.Thread(target=self.art_loop,name='victor-spotify-cover',daemon=True)

    def cover(self,url):
        if url==self.art_url:return self.art
        self.art_url=url;self.art=b''
        try:self.art_requests.get_nowait()
        except queue.Empty:pass
        try:self.art_requests.put_nowait(url)
        except queue.Full:pass
        return b''

    def art_loop(self):
        while not self.stop_event.is_set():
            try:url=self.art_requests.get(timeout=.2)
            except queue.Empty:continue
            data=self.download_cover(url)
            if url==self.art_url and not self.stop_event.is_set():
                self.art=data;self.emit('spotify_art',(url,data))

    def download_cover(self,url):
        parsed=urlparse(url)
        if parsed.scheme!='https' or parsed.hostname not in ('i.scdn.co','image-cdn-ak.spotifycdn.com'):return b''
        import requests
        data=b'';deadline=time.monotonic()+15
        try:
            with requests.get(url,timeout=(5,8),stream=True,allow_redirects=False) as response:
                response.raise_for_status()
                for chunk in response.iter_content(32768):
                    if self.stop_event.is_set() or time.monotonic()>deadline:return b''
                    data+=chunk
                    if len(data)>1_000_000:return b''
        except Exception:return b''
        return data

    def run(self):
        try:self.poll_playback()
        finally:self.core.spotify.close_client()

    def poll_playback(self):
        self.art_thread.start()
        while not self.stop_event.is_set():
            delay=5
            try:
                if self.core.spotify.browser and self.core.spotify.browser.active:
                    # El SDK entrega eventos y progreso local; no duplicar con REST.
                    delay=2
                elif self.core.spotify.cache.path.exists():
                    raw=self.core.spotify.client().current_playback()
                    self.core.spotify.observe_playback(raw)
                    item=(raw or {}).get('item')
                    if item:
                        delay=1.5 if raw.get('is_playing') else 4
                        images=item.get('album',{}).get('images',[])
                        art=self.cover(best_cover(images))
                        self.emit('spotify_state',{'id':item.get('id') or item.get('uri'), 'name':item.get('name','Sin título'),
                            'artists':', '.join(a['name'] for a in item.get('artists',[])), 'playing':raw.get('is_playing',False),
                            'volume':raw.get('device',{}).get('volume_percent'), 'art':art, 'art_url':best_cover(images),
                            'position':raw.get('progress_ms',0),'duration':item.get('duration_ms',0)})
                    else:self.emit('spotify_state',None)
                else:self.emit('spotify_state',None)
            except Exception as exc:
                logging.getLogger('victor.spotify').info('status unavailable type=%s',type(exc).__name__)
                self.emit('spotify_state',None);delay=30
            deadline=time.monotonic()+delay
            while not self.stop_event.is_set() and time.monotonic()<deadline:
                if self.refresh_event.wait(min(.2,max(0,deadline-time.monotonic()))):
                    self.refresh_event.clear();break


def register_player(core):
    # Única reducción de riesgo autorizada por el usuario; reproduce/pausa no cambian.
    core.registry.tools['spotify_volume'].risk=Risk.LOW
    def resume():
        if core.spotify.browser and core.spotify.browser.active:return core.spotify.browser.command('resume')
        client=core.spotify.client()
        device=core.spotify.device(client)
        client.start_playback(device_id=device)
        return {'orden_enviada':'Continuar reproducción','aceptada_por_api':True}
    core.registry.register(Tool('spotify_resume','Continúa la reproducción en Spotify del PC activo.',
        {'type':'object','properties':{},'additionalProperties':False},Risk.MEDIUM,resume))


class SpotifyMiniPlayer(QFrame):
    def __init__(self,app):
        super().__init__(app.root)
        self.app=app;self.state=None;self.dismissed=False;self.paused_since=None
        self.pending=None
        self.confirmed_state=None
        self.observed_pending=None
        self.volume_intent=None
        self.last_volume_sent=None
        self.setObjectName('player')
        self.setFixedSize(292,156)
        layout=QVBoxLayout(self)
        top=QHBoxLayout()
        self.cover=QLabel('♫');self.cover.setObjectName('cover');self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter);self.cover.setFixedSize(48,48)
        top.addWidget(self.cover)
        info=QVBoxLayout();self.title=QLabel();self.artist=QLabel();self.artist.setObjectName('secondary')
        self.title.setTextFormat(Qt.TextFormat.PlainText);self.artist.setTextFormat(Qt.TextFormat.PlainText)
        info.addWidget(self.title);info.addWidget(self.artist);top.addLayout(info,1)
        close=QPushButton('×');close.setObjectName('compact');close.setFixedSize(30,30);close.clicked.connect(self.dismiss);top.addWidget(close)
        layout.addLayout(top)
        controls=QHBoxLayout()
        for label,name in [('⏮','spotify_previous'),('▶','toggle'),('⏭','spotify_next')]:
            b=QPushButton();b.setIcon(icon({'spotify_previous':'previous','toggle':'play','spotify_next':'next'}[name]));b.setAccessibleName({'spotify_previous':'Canción anterior','toggle':'Reproducir','spotify_next':'Siguiente canción'}[name])
            b.clicked.connect(lambda checked=False,n=name:self.action(n));controls.addWidget(b)
            if name=='toggle':self.play=b
        layout.addLayout(controls)
        row=QHBoxLayout();row.addWidget(QLabel('🔊'))
        self.volume=QSlider(Qt.Orientation.Horizontal);self.volume.setRange(0,100);row.addWidget(self.volume)
        self.level=QLabel('—');row.addWidget(self.level);layout.addLayout(row)
        self.debounce=QTimer(self);self.debounce.setSingleShot(True);self.debounce.timeout.connect(self.volume_changed)
        self.volume.valueChanged.connect(self.preview_volume)
        self.volume.sliderReleased.connect(self.flush_volume)
        self.hide()

    def dismiss(self):
        self.dismissed=True;self.debounce.stop();self.hide()

    def action(self,name):
        if not self.state or self.pending:return
        if name=='toggle':name='spotify_pause' if self.state['playing'] else 'spotify_resume'
        self.confirmed_state=dict(self.state)
        self.observed_pending=None
        self.pending=name
        if name in ('spotify_pause','spotify_resume'):
            self.state=dict(self.state,playing=name=='spotify_resume')
            self.play.setIcon(icon('pause' if self.state['playing'] else 'play'));self.play.setAccessibleName('Pausar' if self.state['playing'] else 'Reproducir')
        self.artist.setText('Actualizando Spotify…')
        from victor.gui.tool_labels import friendly_name
        if not self.app.spotify_command(name,{}):
            self.reconcile(name,{'ok':False})
        self.app.sections.spotify_state(self.state)

    def volume_changed(self):
        value=self.volume.value()
        if value==self.last_volume_sent:return
        if not self.app.spotify_command('spotify_volume',{'level':value}):self.volume_intent=None
        else:self.last_volume_sent=value

    def preview_volume(self,value):
        self.level.setText(str(value));self.volume_intent={'level':value,'until':time.monotonic()+130}
        slider=self.app.sections.spotify_volume
        slider.blockSignals(True);slider.setValue(value);slider.blockSignals(False)
        self.debounce.start(120)

    def flush_volume(self):
        self.debounce.stop()
        self.volume_changed()

    def finish_action(self):
        """Retira la predicción al terminar, incluso si se rechazó o falló."""
        if self.pending:
            self.pending=None
            if self.confirmed_state:self.update_state(self.confirmed_state)
            self.confirmed_state=None
            self.observed_pending=None
        self.app.spotify_poller.refresh_event.set()

    def reconcile(self, name, result):
        if not name.startswith('spotify_'):
            return
        if name=='spotify_volume':
            actual=result.get('result',{}) if result.get('ok') else {}
            if not result.get('ok'):self.volume_intent=None;self.last_volume_sent=None
            elif self.volume_intent and actual.get('nivel_solicitado')==self.volume_intent['level']:
                self.volume_intent['until']=time.monotonic()+5
        if self.pending and self.pending != name:
            self.app.spotify_poller.refresh_event.set()
            return
        actual = result.get('result', {}) if result.get('ok') else {}
        actual = actual.get('estado', actual) if isinstance(actual, dict) else {}
        if self.pending==name and result.get('ok') and actual.get('aceptada_por_api'):
            # Mantener la predicción solo hasta recibir el estado de reproducción.
            self.confirmed_state=self.observed_pending or dict(self.state)
        if self.state and 'reproduciendo' in actual:
            state = dict(self.state, playing=bool(actual['reproduciendo']))
            if actual.get('cancion'):
                state.update(name=actual['cancion'], artists=', '.join(actual.get('artistas', [])))
                if state['name'] != self.state['name']:
                    state['art'] = b''
            self.confirmed_state = state
        self.finish_action()

    def update_state(self,state):
        if self.pending:return
        if not state:self.state=None;self.hide();return
        if self.state and state['id']!=self.state['id']:self.dismissed=False;self.paused_since=None
        self.state=state
        if state['playing']:self.paused_since=None
        elif self.paused_since is None:self.paused_since=time.monotonic()
        if self.dismissed or (self.paused_since and time.monotonic()-self.paused_since>300):self.hide();return
        self.title.setText(self.title.fontMetrics().elidedText(state['name'],Qt.TextElideMode.ElideRight,185))
        self.artist.setText(self.artist.fontMetrics().elidedText(state['artists'],Qt.TextElideMode.ElideRight,185))
        self.title.setToolTip(state['name']);self.artist.setToolTip(state['artists'])
        self.play.setIcon(icon('pause' if state['playing'] else 'play'));self.play.setAccessibleName('Pausar' if state['playing'] else 'Reproducir')
        if state.get('art'):
            pix=QPixmap();pix.loadFromData(state['art']);self.cover.setPixmap(pix.scaled(48,48,Qt.AspectRatioMode.KeepAspectRatio))
        else:self.cover.clear();self.cover.setText('♫')
        if self.volume_intent and (state.get('volume')==self.volume_intent['level'] or time.monotonic()>self.volume_intent['until']):self.volume_intent=None
        if not self.volume_intent and state.get('volume')!=self.last_volume_sent:self.last_volume_sent=None
        if state.get('volume') is not None and not self.volume_intent and not self.volume.isSliderDown() and not self.debounce.isActive():
            self.volume.blockSignals(True);self.volume.setValue(state['volume']);self.volume.blockSignals(False);self.level.setText(str(state['volume']))
        self.show();self.raise_();self.reposition()

    def reposition(self):
        if self.parentWidget() is self.app.home_side:return
        self.move(max(4,self.app.root.width()-self.width()-8),max(8,self.app.entry.parentWidget().mapTo(self.app.root,self.app.entry.pos()).y()-self.height()-14))
