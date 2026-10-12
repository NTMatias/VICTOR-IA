"""Account settings use the app's existing background auth lifecycle and Qt palette."""
import queue
import threading
import webbrowser
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QMessageBox
from victor.gui.widgets import AdaptiveButton as QPushButton
from victor.errors import VictorError, Cancelled


class AccountPanel(QWidget):
    def __init__(self,app,provider):
        if provider != 'OpenAI':
            raise ValueError('Solo ChatGPT admite conexión mediante cuenta.')
        super().__init__();self.app=app;self.provider=provider;self.account=app.core.ai.accounts[provider]
        self.events=queue.Queue();self.cancel=threading.Event();self.active=False;self.models=[]
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(12)
        title=QLabel('CHATGPT / OPENAI');title.setObjectName('cardTitle');layout.addWidget(title)
        layout.addWidget(QLabel('Método de conexión'))
        self.method=QComboBox();self.method.addItem('Usar API key','api')
        self.method.setMinimumContentsLength(5);self.method.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.method.addItem('Iniciar sesión con ChatGPT','account')
        self.method.setCurrentIndex(1 if app.config.get('auth_methods')[provider]=='account' else 0)
        layout.addWidget(self.method)
        self.body=QWidget();body=QVBoxLayout(self.body);body.setContentsMargins(0,0,0,0);layout.addWidget(self.body)
        self.state=QLabel();self.state.setWordWrap(True);self.state.setObjectName('secondary');body.addWidget(self.state)
        if provider=='OpenAI':
            self.profiles=QComboBox();body.addWidget(self.profiles);self.profiles.currentIndexChanged.connect(self.select_profile)
            self.profiles.setMinimumContentsLength(5);self.profiles.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.connect_button=QPushButton('Continuar con ChatGPT')
        self.connect_button.setObjectName('primary');self.connect_button.clicked.connect(lambda:self.start('connect'))
        body.addWidget(self.connect_button)
        row=QHBoxLayout();body.addLayout(row)
        self.test_button=QPushButton('Actualizar modelos / probar')
        self.test_button.clicked.connect(lambda:self.start('probe'));row.addWidget(self.test_button)
        self.logout=QPushButton('Cerrar sesión')
        self.logout.clicked.connect(lambda:self.start('disconnect'));row.addWidget(self.logout)
        if provider=='OpenAI':
            row=QHBoxLayout();body.addLayout(row)
            add=QPushButton('Añadir otra cuenta');add.clicked.connect(lambda:self.start('new'));row.addWidget(add)
            usage=QPushButton('Gestionar uso');usage.clicked.connect(lambda:webbrowser.open('https://chatgpt.com/#settings/Usage'));row.addWidget(usage)
        body.addWidget(QLabel('Modelo de la cuenta'))
        self.model=QComboBox();self.model.currentIndexChanged.connect(self.select_model);body.addWidget(self.model)
        self.model.setMinimumContentsLength(5);self.model.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        hint=QLabel('Tu plan debe ser elegible y autorizar su uso. Voz: Whisper local; la API de transcripción es independiente.')
        hint.setWordWrap(True);hint.setObjectName('secondary');body.addWidget(hint)
        settings_hint=QLabel('Temperatura y límite de tokens se aplican a la API. El plan utiliza los parámetros compatibles de su servicio.')
        settings_hint.setWordWrap(True);settings_hint.setObjectName('secondary');body.addWidget(settings_hint)
        self.cancel_button=QPushButton('Cancelar conexión');self.cancel_button.clicked.connect(self.cancel.set);self.cancel_button.hide();body.addWidget(self.cancel_button)
        self.method.currentIndexChanged.connect(self.change_method)
        self.timer=QTimer(self);self.timer.timeout.connect(self.poll);self.timer.start(150)
        self.refresh()

    def idle(self):
        return not self.app.core.busy.is_set() and not (self.app.auth_thread and self.app.auth_thread.is_alive())

    def change_method(self):
        if not self.idle():
            self.app.settings.show_message('Espera a que termine la operación actual.');self.refresh();return
        method=self.method.currentData();old=self.app.config.get('auth_methods')
        if method=='api' and old[self.provider]!='api':
            if QMessageBox.question(self,'Usar API','La API tiene facturación y límites separados de tu suscripción. ¿Autorizar este método para '+self.provider+'?')!=QMessageBox.StandardButton.Yes:
                self.refresh();return
        old[self.provider]=method;self.app.config.save({'auth_methods':old});self.app.refresh_config();self.refresh()

    def select_model(self,index):
        value=self.model.itemData(index)
        if not value:return
        if self.app.core.busy.is_set():self.refresh_models();return
        models=self.app.config.get('account_models');models[self.provider]=value;self.app.config.save({'account_models':models});self.app.refresh_config()

    def select_profile(self,index):
        key=self.profiles.itemData(index)
        if not key or not self.idle():return
        self.account.select(key);self.models=[];self.refresh();self.start('probe')

    def refresh_models(self):
        self.model.blockSignals(True);self.model.clear()
        for model in self.models:self.model.addItem(model['label'],model['id'])
        selected=self.model.findData(self.app.config.get('account_models')[self.provider])
        self.model.setCurrentIndex(selected if selected>=0 else 0);self.model.setEnabled(bool(self.models));self.model.blockSignals(False)

    def refresh(self):
        method=self.app.config.get('auth_methods')[self.provider]
        self.method.blockSignals(True);self.method.setCurrentIndex(1 if method=='account' else 0);self.method.blockSignals(False)
        self.body.setVisible(method=='account')
        if not self.active:
            try:self.state.setText(self.account.status())
            except VictorError as exc:self.state.setText(str(exc))
        if self.provider=='OpenAI':
            self.profiles.blockSignals(True);self.profiles.clear()
            try:
                for profile in self.account.profiles():
                    self.profiles.addItem(profile['label']+' · '+profile['id'][:6],profile['id'])
                    if profile['active']:self.profiles.setCurrentIndex(self.profiles.count()-1)
            except VictorError:pass
            self.profiles.blockSignals(False)
        self.refresh_models()
        for action in (self.connect_button,self.test_button,self.logout,self.method):action.setEnabled(not self.active)
        self.cancel_button.setVisible(self.active)

    def start(self,operation):
        if not self.idle():self.app.settings.show_message('Espera a que termine la operación actual.');return
        self.active=True;self.cancel.clear();self.refresh()
        self.state.setText('Autoriza ChatGPT en el navegador…'
                           if operation in ('connect','new') else 'Comprobando conexión…')
        def work():
            try:
                if operation in ('connect','new'):
                    result=self.account.connect(self.cancel,new_account=operation=='new')
                elif operation=='disconnect':result=self.account.disconnect(self.cancel)
                else:result=self.account.list_models(self.cancel)
                self.events.put((True,operation,result))
            except Cancelled:self.events.put((False,operation,'Operación cancelada.'))
            except Exception as exc:self.events.put((False,operation,str(exc) if isinstance(exc,VictorError) else 'No se pudo completar la operación de cuenta.'))
        self.app.auth_thread=threading.Thread(target=work,name='victor-ai-account',daemon=True);self.app.auth_thread.start()

    def poll(self):
        if self.app.closing:self.cancel.set();return
        try:ok,operation,result=self.events.get_nowait()
        except queue.Empty:return
        self.active=False
        if ok and isinstance(result,list):
            self.models=result
            saved=self.app.config.get('account_models')
            if result and saved[self.provider] not in [model['id'] for model in result]:
                saved[self.provider]=result[0]['id'];self.app.config.save({'account_models':saved})
        if operation=='disconnect':self.models=[]
        self.refresh();self.app.refresh_config()
        if not ok:self.state.setText(result)
        elif isinstance(result,str):self.state.setText(result)
