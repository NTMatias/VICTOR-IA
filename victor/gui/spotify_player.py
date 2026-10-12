"""Mini reproductor: consulta pasiva y controles por el orquestador existente."""
import logging
import threading
import time
from urllib.parse import urlparse
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame,QLabel,QPushButton,QSlider,QVBoxLayout,QHBoxLayout
from victor.security import Risk
from victor.tools.registry import Tool


class SpotifyPoller:
    def __init__(self,core,emit):
        self.core,self.emit=core,emit
        self.stop_event=threading.Event()
        self.thread=threading.Thread(target=self.run,name='victor-spotify-status',daemon=True)
        self.art_url='';self.art=b''

    def cover(self,url):
        if url==self.art_url:return self.art
        self.art_url=url;self.art=b''
        parsed=urlparse(url)
        if parsed.scheme!='https' or parsed.hostname not in ('i.scdn.co','image-cdn-ak.spotifycdn.com'):return b''
        import requests
        try:
            with requests.get(url,timeout=(5,8),stream=True,allow_redirects=False) as response:
                response.raise_for_status()
                for chunk in response.iter_content(32768):
                    if self.stop_event.is_set():return b''
                    self.art+=chunk
                    if len(self.art)>1_000_000:self.art=b'';break
        except Exception:self.art=b''
        return self.art

    def run(self):
        while not self.stop_event.is_set():
            delay=5
            try:
                if self.core.spotify.cache.path.exists():
                    raw=self.core.spotify.client().current_playback()
                    item=(raw or {}).get('item')
                    if item:
                        images=item.get('album',{}).get('images',[])
                        art=self.cover(images[-1]['url'] if images else '')
                        self.emit('spotify_state',{'id':item.get('id') or item.get('uri'), 'name':item.get('name','Sin título'),
                            'artists':', '.join(a['name'] for a in item.get('artists',[])), 'playing':raw.get('is_playing',False),
                            'volume':raw.get('device',{}).get('volume_percent'), 'art':art})
                    else:self.emit('spotify_state',None)
                else:self.emit('spotify_state',None)
            except Exception as exc:
                logging.getLogger('victor.spotify').info('status unavailable type=%s',type(exc).__name__)
                self.emit('spotify_state',None);delay=30
            self.stop_event.wait(delay)


def register_player(core):
    # Única reducción de riesgo autorizada por el usuario; reproduce/pausa no cambian.
    core.registry.tools['spotify_volume'].risk=Risk.LOW
    def resume():
        client=core.spotify.client()
        device=core.spotify.device(client)
        client.start_playback(device_id=device)
        return {'orden_enviada':'Continuar reproducción','estado':core.spotify.playback(client)}
    core.registry.register(Tool('spotify_resume','Continúa la reproducción en Spotify del PC activo.',
        {'type':'object','properties':{},'additionalProperties':False},Risk.MEDIUM,resume))


class SpotifyMiniPlayer(QFrame):
    def __init__(self,app):
        super().__init__(app.root)
        self.app=app;self.state=None;self.dismissed=False;self.paused_since=None
        self.setObjectName('player')
        self.setFixedSize(320,170)
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
            b=QPushButton(label);b.setAccessibleName({'spotify_previous':'Canción anterior','toggle':'Reproducir o pausar','spotify_next':'Siguiente canción'}[name])
            b.clicked.connect(lambda checked=False,n=name:self.action(n));controls.addWidget(b)
            if name=='toggle':self.play=b
        layout.addLayout(controls)
        row=QHBoxLayout();row.addWidget(QLabel('🔊'))
        self.volume=QSlider(Qt.Orientation.Horizontal);self.volume.setRange(0,100);row.addWidget(self.volume)
        self.level=QLabel('—');row.addWidget(self.level);layout.addLayout(row)
        self.debounce=QTimer(self);self.debounce.setSingleShot(True);self.debounce.timeout.connect(self.volume_changed)
        self.volume.valueChanged.connect(lambda value:(self.level.setText(str(value)),self.debounce.start(450)))
        self.hide()

    def dismiss(self):
        self.dismissed=True;self.debounce.stop();self.hide()

    def action(self,name):
        if not self.state:return
        if name=='toggle':name='spotify_pause' if self.state['playing'] else 'spotify_resume'
        from victor.gui.tool_labels import friendly_name
        self.app.send(friendly_name(name),(name,{}))

    def volume_changed(self):
        if self.app.core.busy.is_set():
            self.debounce.start(500);return
        self.app.send('🎵 Spotify: ajustar volumen',('spotify_volume',{'level':self.volume.value()}))

    def update_state(self,state):
        if not state:self.state=None;self.hide();return
        if self.state and state['id']!=self.state['id']:self.dismissed=False;self.paused_since=None
        self.state=state
        if state['playing']:self.paused_since=None
        elif self.paused_since is None:self.paused_since=time.monotonic()
        if self.dismissed or (self.paused_since and time.monotonic()-self.paused_since>300):self.hide();return
        self.title.setText(self.title.fontMetrics().elidedText(state['name'],Qt.TextElideMode.ElideRight,185))
        self.artist.setText(self.artist.fontMetrics().elidedText(state['artists'],Qt.TextElideMode.ElideRight,185))
        self.title.setToolTip(state['name']);self.artist.setToolTip(state['artists'])
        self.play.setText('⏸' if state['playing'] else '▶')
        if state.get('art'):
            pix=QPixmap();pix.loadFromData(state['art']);self.cover.setPixmap(pix.scaled(48,48,Qt.AspectRatioMode.KeepAspectRatio))
        else:self.cover.clear();self.cover.setText('♫')
        if state.get('volume') is not None and not self.volume.isSliderDown() and not self.debounce.isActive():
            self.volume.blockSignals(True);self.volume.setValue(state['volume']);self.volume.blockSignals(False);self.level.setText(str(state['volume']))
        self.show();self.raise_();self.reposition()

    def reposition(self):
        self.move(max(4,self.app.root.width()-self.width()-8),max(8,self.app.entry.parentWidget().mapTo(self.app.root,self.app.entry.pos()).y()-self.height()-14))
