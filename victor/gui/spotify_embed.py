"""Spotify inside a native Qt child HWND, using the Windows WebView2 runtime."""
import json
import os
import secrets
from pathlib import Path
from PySide6.QtCore import Qt, QProcess, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout


class SpotifyEmbed(QWidget):
    event = Signal(dict)
    def __init__(self, app):
        super().__init__();self.app=app;self.process=None;self.stopping=False;self.loaded=False;self.host_handle=None;self.pipe=None;self.browser_theme=None
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        self.status=QLabel('Tu biblioteca, búsqueda y audio, dentro de VICTOR.');self.status.setWordWrap(True);self.status.setObjectName('secondary')
        row=QHBoxLayout();row.addWidget(self.status,1)
        self.retry=QPushButton('Reconectar');self.retry.clicked.connect(self.restart);row.addWidget(self.retry);layout.addLayout(row)
        self.surface=QWidget();self.surface.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.surface.setMinimumSize(120,240);layout.addWidget(self.surface,1)
        self.apply_theme()
        self.timeout=QTimer(self);self.timeout.setSingleShot(True);self.timeout.setInterval(20000)
        self.timeout.timeout.connect(lambda:self.status.setText('Spotify tarda en cargar. Comprueba la conexión y pulsa Reconectar.'))

    def showEvent(self,event):
        super().showEvent(event)
        if self.process is None and hasattr(self.app,'spotify_web'):QTimer.singleShot(0,self.start)

    def start(self):
        if self.process is not None or self.app.closing:return
        executable=Path(__file__).parent/'webview2'/'SpotifyHost.exe'
        if os.name!='nt' or not executable.is_file():
            self.status.setText('El reproductor integrado necesita Windows y SpotifyHost.exe.');return
        self.stopping=False;self.loaded=False;self.host_handle=None
        from victor.gui.theme import is_light
        self.browser_theme='light' if is_light(self.app.config.get('theme')) else 'dark'
        self.status.setText('Cargando Spotify…');url=self.app.spotify_web.start()+'?theme='+self.browser_theme
        handsfree=self.app.config.get('voice_background_listening') and self.app.config.get('voice_mode')=='continua'
        if handsfree:url+='&handsfree=1'
        profile=self.app.config.data_dir/'spotify_webview2';profile.mkdir(parents=True,exist_ok=True)
        process=QProcess(self);self.process=process
        if handsfree:
            from PySide6.QtCore import QProcessEnvironment
            environment=QProcessEnvironment.systemEnvironment()
            arguments=environment.value('WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS','')
            environment.insert('WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS',arguments+' --autoplay-policy=no-user-gesture-required')
            process.setProcessEnvironment(environment)
        self.pipe_name='victor-spotify-'+secrets.token_hex(16)
        process.setProgram(str(executable));process.setArguments([str(int(self.surface.winId())),url,str(profile),self.pipe_name])
        process.readyReadStandardOutput.connect(self.read_events)
        process.errorOccurred.connect(lambda _:self.status.setText('No pude iniciar Spotify. Comprueba WebView2 y pulsa Reconectar.'))
        process.finished.connect(self.finished);process.start();self.timeout.start()

    def read_events(self):
        process=self.process
        if process is None:return
        while process.canReadLine():
            try:data=json.loads(bytes(process.readLine()).decode('utf-8'))
            except (ValueError,UnicodeError):continue
            kind=data.get('kind')
            if kind=='host':self.host_handle=data.get('hwnd')
            elif kind=='pipe_ready':
                try:self.pipe=open('\\\\.\\pipe\\'+self.pipe_name,'w',encoding='utf-8',buffering=1)
                except OSError:self.status.setText('No se pudo conectar el reproductor interno. Pulsa Reconectar.')
            elif kind=='loaded':
                self.host_handle=data.get('hwnd',self.host_handle)
                self.loaded=True;self.timeout.stop();self.status.setText('Spotify integrado · Pulsa Activar audio una vez para habilitar el sonido.')
                self.apply_theme()
            elif kind=='error':self.timeout.stop();self.status.setText(data.get('message','Spotify se desconectó. Pulsa Reconectar.'))
            elif kind=='link':self.app.run_tool('open_url',{'url':data['url']})
            self.event.emit(data)

    def finished(self,*_):
        self.timeout.stop();self.loaded=False
        self.app.spotify_web.disconnect()
        if self.pipe:
            try:self.pipe.close()
            except OSError:pass
            self.pipe=None
        if self.process:self.process.deleteLater();self.process=None
        if not self.stopping:self.status.setText('El reproductor se cerró. Pulsa Reconectar para recuperarlo.')

    def stop(self):
        self.stopping=True;self.timeout.stop()
        if self.process and self.process.state()!=QProcess.ProcessState.NotRunning:
            process=self.process
            self.command({'command':'close'})
            QTimer.singleShot(2500,lambda:process.kill() if self.process is process and process.state()!=QProcess.ProcessState.NotRunning else None)

    def restart(self):
        if self.process and self.process.state()!=QProcess.ProcessState.NotRunning:
            process=self.process
            process.finished.connect(lambda *_:QTimer.singleShot(0,self.start));self.stop()
        else:self.process=None;self.start()

    def running(self):return bool(self.process and self.process.state()!=QProcess.ProcessState.NotRunning)

    def command(self,data):
        if self.pipe:
            try:self.pipe.write(json.dumps(data)+'\n');self.pipe.flush();return True
            except OSError:return False
        return False

    def apply_theme(self):
        from victor.gui.theme import is_light
        light=is_light(self.app.config.get('theme'))
        self.surface.setStyleSheet('background:'+('#F1ECF9' if light else '#211E32')+';border-radius:20px;')
        theme='light' if light else 'dark'
        if self.loaded and theme!=self.browser_theme:
            if self.command({'command':'probe','script':"document.documentElement.dataset.theme="+json.dumps(theme)}):self.browser_theme=theme


class SpotifyNowPlaying(QFrame):
    """A compact cover/title/artist card; status only from observed playback."""
    def __init__(self,parent=None):
        super().__init__(parent);self.setObjectName('spotifyNowPlaying');self.state={}
        layout=QHBoxLayout(self);layout.setContentsMargins(8,8,8,8)
        self.cover=QLabel('♫');self.cover.setFixedSize(56,56);self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(self.cover)
        texts=QVBoxLayout();texts.setSpacing(4);layout.addLayout(texts,1)
        self.title=QLabel();self.artist=QLabel();self.status=QLabel()
        for widget in (self.title,self.artist,self.status):
            widget.setTextFormat(Qt.TextFormat.PlainText);widget.setWordWrap(True);texts.addWidget(widget)
        self.title.setStyleSheet('font-weight:600;');self.artist.setStyleSheet('color:#A7A7A7;');self.status.setStyleSheet('color:#1DB954;font-size:11px;')

    def update_state(self,state):
        state=state or {};changed=self.state.get('id')!=state.get('id');self.state=dict(state)
        self.title.setText(state.get('name','Spotify'));self.artist.setText(state.get('artists',''))
        self.status.setText(state.get('status') or ('Reproduciendo' if state.get('playing') else 'En pausa'))
        if changed:self.cover.clear();self.cover.setText('♫')
        if state.get('art'):
            pix=QPixmap();pix.loadFromData(state['art'])
            if not pix.isNull():
                pix=pix.scaled(112,112,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation);pix.setDevicePixelRatio(2);self.cover.setPixmap(pix)

    def requested(self,row):
        self.update_state({'id':row.get('id'),'name':row.get('name','Spotify'),'artists':row.get('subtitle',''),'art_url':row.get('image',''),'status':'Conectando la canción…'})
