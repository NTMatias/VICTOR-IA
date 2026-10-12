"""Agent sections host the original full interactive applications via xterm/ConPTY."""
import json
import subprocess
from pathlib import Path
from PySide6.QtCore import QObject,Slot,QTimer,QUrl
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLineEdit,QFileDialog,QApplication,QComboBox,QSizePolicy
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage,QWebEngineProfile,QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel
from victor.agents.terminal import AgentTerminal,executable
from victor.gui.panels import Page,label,button,notice
from victor.errors import VictorError


class LocalTerminalPage(QWebEnginePage):
    def __init__(self,profile,parent,path):super().__init__(profile,parent);self.path=path.resolve()
    def acceptNavigationRequest(self,url,kind,main):
        return (url.isLocalFile() and Path(url.toLocalFile()).resolve()==self.path) or url.toString()=='about:blank'
    def createWindow(self,kind):return None


class TerminalBridge(QObject):
    def __init__(self,view):super().__init__(view);self.view=view
    @Slot(str)
    def input(self,value):self.view.backend.write(value)
    @Slot(int,int)
    def resize(self,cols,rows):self.view.backend.resize(cols,rows)
    @Slot()
    def ready(self):self.view.web_ready=True;self.view.apply_theme()


class AgentPage(Page):
    def __init__(self,app,agent):
        name='Codex' if agent=='codex' else 'Claude Code'
        super().__init__(name,'Tu agente de programación completo, dentro de VICTOR.','Agentes de programación / '+name)
        self.app=app;self.agent=agent;self.backend=AgentTerminal(app.config,agent);self.web_ready=False
        row=QHBoxLayout();self.folder=QLineEdit(str(app.config.root/'workspace'));self.folder.setReadOnly(True)
        row.addWidget(self.folder,1);self.choose=button('Elegir proyecto',self.pick,'folder');row.addWidget(self.choose);self.content.addLayout(row)
        self.model=None
        if agent=='codex':
            self.model=QComboBox();self.model.addItem('Automático · recomendado por Codex','');self.model.setAccessibleName('Modelo de Codex')
            # Long model labels must fit the viewport without widening the entire page.
            self.model.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
            self.model.setMinimumContentsLength(5)
            self.model.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            self.content.addWidget(self.model)
        controls=QHBoxLayout();self.open_button=button('Abrir '+name,self.start,'terminal',True);controls.addWidget(self.open_button)
        controls.addWidget(button('Interrumpir',self.backend.interrupt,'stop'))
        controls.addWidget(button('Cerrar sesión de terminal',self.backend.stop,'close'))
        controls.addWidget(button('Copiar selección',self.copy_selection,'copy'));self.content.addLayout(controls)
        controls.addWidget(button('Adjuntar archivos',self.attach,'file'))
        self.state=label(('CLI oficial disponible.' if executable(app.config,agent) else 'CLI no instalado. Consulta las instrucciones de instalación.')+' Elige el proyecto y abre el agente.');self.content.addWidget(self.state)
        self.content.addWidget(notice('El agente usa su propia cuenta, permisos y herramientas. Las peticiones y aprobaciones se hacen en su terminal. Cerrar esta terminal conserva el historial del CLI y no cierra tu cuenta.'))
        self.surface=None;self.web_profile=None
        self.timer=QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(40)
        QApplication.instance().focusChanged.connect(self.focus_changed)
    def showEvent(self,event):
        super().showEvent(event);self.ensure_surface()
    def ensure_surface(self):
        # Keep Chromium renderers out of startup when the user only needs the chat.
        if self.surface is not None:return
        self.surface=QWebEngineView();self.surface.setMinimumHeight(480)
        profile=QWebEngineProfile(self.surface);self.web_profile=profile
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        page=LocalTerminalPage(profile,self.surface,Path(__file__).parent/'terminal'/'terminal.html')
        self.surface.setPage(page);self.content.addWidget(self.surface,1)
        settings=page.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows,False)
        self.channel=QWebChannel(page);self.bridge=TerminalBridge(self);self.channel.registerObject('terminalBridge',self.bridge);page.setWebChannel(self.channel)
        self.surface.setUrl(QUrl.fromLocalFile(str(page.path)))
    def pick(self):
        if self.backend.running():self.state.setText('Cierra la terminal antes de cambiar de proyecto.');return
        path=QFileDialog.getExistingDirectory(self,'Proyecto para '+self.agent,self.folder.text())
        if path:self.folder.setText(path)
    def start(self):
        if not self.web_ready:self.state.setText('Preparando la terminal…');return
        try:
            self.surface.page().runJavaScript('window.victorTerminal.reset();window.victorTerminal.focus();')
            self.backend.start(self.folder.text(),model=self.model.currentData() if self.model else '');self.choose.setEnabled(False);self.open_button.setEnabled(False)
            self.state.setText('Abriendo el CLI oficial…');self.surface.setFocus()
        except VictorError as exc:self.state.setText(str(exc))
    def poll(self):
        import queue
        chunks=[]
        for _ in range(64):
            try:kind,value=self.backend.events.get_nowait()
            except queue.Empty:break
            if kind=='output':chunks.append(value)
            elif kind=='status':self.state.setText(value)
            elif kind=='models' and self.model:
                previous=self.model.currentData();self.model.clear();self.model.addItem('Automático · recomendado por Codex','')
                for item in value['items']:self.model.addItem(item['label'],item['id'])
                index=self.model.findData(previous);self.model.setCurrentIndex(max(0,index))
                self.state.setText('Modelo de esta sesión: '+value['selected'])
            elif kind=='started':self.state.setText('Sesión abierta · '+value)
            elif kind=='error':self.state.setText(value)
            elif kind=='exit':self.state.setText('Terminal finalizada. Puedes abrirla de nuevo o retomar una sesión con los comandos del agente.')
        if chunks and self.surface:self.surface.page().runJavaScript('window.victorTerminal.write('+json.dumps(''.join(chunks))+');')
        if not self.backend.running():self.choose.setEnabled(True);self.open_button.setEnabled(True)
        if self.model:self.model.setEnabled(not self.backend.running())
        if self.app.closing:self.backend.stop()
    def copy_selection(self):
        if self.surface is None:return
        self.surface.page().runJavaScript('window.victorTerminal.selection()',lambda text:QApplication.clipboard().setText(text or ''))
    def attach(self):
        paths,_=QFileDialog.getOpenFileNames(self,'Archivos para el agente',self.folder.text())
        if paths and self.backend.running():
            text=' '+subprocess.list2cmdline(paths)+' '
            self.backend.write('\x1b[200~'+text+'\x1b[201~');self.surface.setFocus()
    def apply_theme(self):
        from victor.gui.theme import is_light
        if self.web_ready:self.surface.page().runJavaScript('window.victorTerminal.theme('+json.dumps(is_light(self.app.config.get('theme')))+');')
    def focus_changed(self,old,new):
        active=any(page.surface is not None and (new is page.surface or (new is not None and page.surface.isAncestorOf(new))) for page in getattr(self.app,'agent_pages',{}).values())
        self.app.command_shortcut.setEnabled(not active);self.app.presentation_shortcut.setEnabled(not active)
    def shutdown(self):self.timer.stop();self.backend.stop()
