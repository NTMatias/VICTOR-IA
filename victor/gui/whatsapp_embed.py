"""WhatsApp Web visible e integrado; paleta VICTOR y resúmenes para Inicio."""
import json
import os
import secrets
from pathlib import Path
from PySide6.QtCore import Qt,QProcess,QTimer,Signal
from PySide6.QtWidgets import QWidget,QLabel,QPushButton,QVBoxLayout,QHBoxLayout


class WhatsAppEmbed(QWidget):
    event=Signal(dict)
    snapshot_changed=Signal(dict)
    def __init__(self,app):
        super().__init__();self.app=app;self.process=None;self.pipe=None;self.loaded=False
        self.stopping=False;self.host_handle=None;self.browser_theme=None;self.state='disconnected';self.chats=[];self.pending={}
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(10)
        row=QHBoxLayout();self.status=QLabel('Tus conversaciones y mensajes, dentro de VICTOR.');self.status.setWordWrap(True);self.status.setObjectName('secondary');row.addWidget(self.status,1)
        self.retry=QPushButton('Reconectar');self.retry.clicked.connect(self.restart);row.addWidget(self.retry);layout.addLayout(row)
        self.surface=QWidget();self.surface.setAttribute(Qt.WidgetAttribute.WA_NativeWindow);self.surface.setMinimumSize(120,360);layout.addWidget(self.surface,1)
        self.timeout=QTimer(self);self.timeout.setSingleShot(True);self.timeout.setInterval(45000)
        self.timeout.timeout.connect(lambda:self.status.setText('WhatsApp tarda en cargar. Revisa la conexión y pulsa Reconectar.'))
        self.apply_theme()

    @property
    def profile(self):return self.app.config.data_dir/'whatsapp_webview2'
    @property
    def executable(self):return Path(__file__).parent/'webview2'/'WhatsAppWebHost.exe'

    def showEvent(self,event):
        super().showEvent(event)
        if self.process is None:QTimer.singleShot(0,self.start)

    def start(self):
        if self.process is not None or self.app.closing:return
        if os.name!='nt' or not self.executable.is_file():self.status.setText('WhatsApp integrado requiere Windows y WhatsAppWebHost.exe.');return
        try:self.profile.mkdir(parents=True,exist_ok=True)
        except OSError:self.status.setText('No pude abrir el perfil local de WhatsApp. Revisa el acceso a la carpeta de datos.');return
        self.stopping=False;self.loaded=False;self.host_handle=None;self.browser_theme=None
        self.state='loading';self.status.setText('Cargando WhatsApp…');self.snapshot_changed.emit({'state':'loading','chats':self.chats})
        self.pipe_name='victor-whatsapp-'+secrets.token_hex(16)
        process=QProcess(self);self.process=process
        process.setProgram(str(self.executable));process.setArguments([str(int(self.surface.winId())),'https://web.whatsapp.com/',str(self.profile),self.pipe_name])
        process.readyReadStandardOutput.connect(self.read_events)
        process.errorOccurred.connect(lambda error,p=process:self.process_error(p,error))
        process.finished.connect(lambda *_,p=process:self.finished(p));process.start();self.timeout.start()

    def process_error(self,process,error):
        if self.process is not process:return
        self.timeout.stop();self.status.setText('No pude iniciar WhatsApp. Revisa WebView2 y pulsa Reconectar.')
        if error==QProcess.ProcessError.FailedToStart:self.finished(process,failed=True)

    def receive_snapshot(self,payload):
        if not isinstance(payload,dict) or payload.get('state') not in ('loading','connected','qr','disconnected'):return
        from victor.gui.whatsapp_panel import valid_rows
        self.state=payload['state']
        if self.state=='connected':
            self.chats=valid_rows(payload.get('recent',payload.get('chats',[])))
            self.status.setText('WhatsApp conectado · Chats, contactos y mensajes en esta pestaña.')
        elif self.state in ('qr','disconnected'):
            self.chats=[];self.status.setText('Vincula tu teléfono con el QR de WhatsApp.' if self.state=='qr' else 'WhatsApp se desconectó. Pulsa Reconectar.')
        self.snapshot_changed.emit({'state':self.state,'chats':self.chats,'contact_mode':False})

    def read_events(self):
        process=self.process
        if process is None:return
        while process.canReadLine():
            try:data=json.loads(bytes(process.readLine()).decode('utf-8'))
            except (ValueError,UnicodeError):continue
            if not isinstance(data,dict):continue
            kind=data.get('kind')
            if kind=='host':self.host_handle=data.get('hwnd')
            elif kind=='pipe_ready':
                try:self.pipe=open('\\\\.\\pipe\\'+self.pipe_name,'w',encoding='utf-8',buffering=1)
                except OSError:self.status.setText('No pude conectar la vista de WhatsApp. Pulsa Reconectar.')
            elif kind=='loaded':
                self.loaded=True;self.timeout.stop();self.host_handle=data.get('hwnd',self.host_handle)
                if self.state=='loading':self.status.setText('WhatsApp integrado · Vincula tu teléfono si aparece el QR.')
                self.apply_theme()
            elif kind=='whatsapp':
                if data.get('type')=='snapshot':self.receive_snapshot(data.get('payload'))
                elif data.get('type')=='result' and data.get('request') in self.pending:
                    name=self.pending.pop(data['request'])
                    self.status.setText('Conversación abierta · '+name if data.get('ok') else str(data.get('error','Selecciona la conversación en WhatsApp.')))
            elif kind=='error':self.timeout.stop();self.status.setText(data.get('message','WhatsApp se desconectó. Pulsa Reconectar.'))
            elif kind=='link':
                from urllib.parse import urlsplit
                url=data.get('url','')
                if urlsplit(url).scheme in ('https','http'):self.app.run_tool('open_url',{'url':url})
            self.event.emit(data)

    def open_chat(self,identifier):
        name=next((row['name'] for row in self.chats if row['id']==identifier),None)
        if not name or self.state!='connected':return
        request=secrets.token_hex(12)
        if self.command({'command':'whatsapp','payload':{'kind':'victor_whatsapp','request':request,'action':'open','id':identifier}}):self.pending[request]=name

    def finished(self,process,failed=False):
        if self.process is not process:return
        self.timeout.stop();self.loaded=False;self.host_handle=None;self.pending.clear()
        if self.pipe:
            try:self.pipe.close()
            except OSError:pass
            self.pipe=None
        process.deleteLater();self.process=None
        if not self.stopping:
            self.receive_snapshot({'state':'disconnected'})
            if not failed:self.status.setText('WhatsApp se cerró. Pulsa Reconectar; tu sesión permanece guardada.')

    def running(self):return bool(self.process and self.process.state()!=QProcess.ProcessState.NotRunning)
    def command(self,data):
        if self.pipe:
            try:self.pipe.write(json.dumps(data)+'\n');self.pipe.flush();return True
            except OSError:return False
        return False
    def stop(self):
        self.stopping=True;self.timeout.stop()
        if self.running():
            process=self.process;self.command({'command':'close'})
            QTimer.singleShot(2500,lambda:process.kill() if self.process is process and self.running() else None)
    def restart(self):
        if self.app.closing:return
        if self.running():
            process=self.process;process.finished.connect(lambda *_:QTimer.singleShot(0,self.start));self.stop()
        else:
            if self.process:self.finished(self.process)
            self.start()
    def apply_theme(self):
        from victor.gui.theme import is_light
        theme='light' if is_light(self.app.config.get('theme')) else 'dark'
        self.surface.setStyleSheet('background:'+('#F6F7FA' if theme=='light' else '#15171C')+';')
        if self.loaded and theme!=self.browser_theme and self.command({'command':'theme','theme':theme}):self.browser_theme=theme
