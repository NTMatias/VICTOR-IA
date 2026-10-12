"""Explicit provider chooser and verified local image cards in the chat."""
import queue
import shutil
import threading
import webbrowser
from pathlib import Path
from PySide6.QtCore import Qt,QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QComboBox,QPlainTextEdit,QFileDialog,QScrollArea,QWidget,QSizePolicy
from victor.ai.images import MODELS,ImageArchive,ImageService
from victor.gui.panels import label,button
from victor.errors import VictorError,Cancelled


class ImageChooser(QDialog):
    def __init__(self,app,prompt):
        super().__init__(app);self.app=app;self.setWindowTitle('Generar imagen');self.setModal(True);self.resize(540,520)
        layout=QVBoxLayout(self);layout.setSpacing(14);layout.setContentsMargins(24,24,24,24)
        layout.addWidget(label('¿Quién genera tu imagen?','sectionTitle'))
        self.provider=QComboBox();self.provider.addItem('ChatGPT / OpenAI','OpenAI');self.provider.addItem('Gemini','Gemini');layout.addWidget(self.provider)
        self.prompt=QPlainTextEdit(prompt);self.prompt.setPlaceholderText('Describe la imagen que quieres crear…');self.prompt.setMinimumHeight(120);layout.addWidget(self.prompt)
        layout.addWidget(label('Modelo de imágenes'))
        self.model=QComboBox();self.model.setEditable(True);self.model.setMinimumContentsLength(5)
        self.model.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon);layout.addWidget(self.model)
        self.state=label('');layout.addWidget(self.state)
        self.billing=label('');layout.addWidget(self.billing)
        self.provider_help=button('Ver requisitos del proveedor',self.open_provider_help,'link');layout.addWidget(self.provider_help)
        layout.addWidget(label('La imagen se genera con tu clave API del proveedor elegido y puede tener un coste. El acceso por cuenta para conversar es independiente.'))
        layout.addWidget(button('Configurar clave API',self.configure,'settings'))
        row=QHBoxLayout();self.generate=button('Generar imagen',self.accept,'play',True);row.addWidget(self.generate);row.addWidget(button('Cancelar',self.reject,'close'));layout.addLayout(row)
        preferred=app.config.get('provider')
        try:
            if preferred not in MODELS or not app.config.api_key(preferred):
                preferred=next((provider for provider in MODELS if app.config.api_key(provider)),'OpenAI')
        except VictorError:preferred='OpenAI'
        self.provider.setCurrentIndex(self.provider.findData(preferred))
        self.provider.currentIndexChanged.connect(self.refresh);self.prompt.textChanged.connect(self.refresh_enabled);self.refresh()
    def configure(self):self.reject();self.app.navigate('ia')
    def open_provider_help(self):
        webbrowser.open('https://ai.google.dev/gemini-api/docs/billing' if self.provider.currentData()=='Gemini' else 'https://platform.openai.com/settings/organization/billing/overview')
    def refresh(self):
        provider=self.provider.currentData();self.model.clear()
        self.model.addItems([MODELS[provider]]+(['gpt-image-2.5-flare','gpt-image-1.5'] if provider=='OpenAI' else ['gemini-3.1-flash-image','gemini-3.1-flash-lite-image','gemini-3-pro-image']))
        try:self.key_ready=bool(self.app.config.api_key(provider))
        except VictorError:self.key_ready=False
        self.state.setText('Clave API configurada; su acceso y cuota se comprobarán al generar.' if self.key_ready else 'Falta tu clave API personal de '+provider+'. No se usará la sesión de otra aplicación.')
        self.billing.setText('Gemini: la API de imágenes requiere facturación habilitada y cuota; la cuota gratuita del chat no incluye imágenes.' if provider=='Gemini' else 'OpenAI: necesitas saldo o facturación de API y acceso al modelo de imágenes; la suscripción ChatGPT del chat es independiente.')
        self.refresh_enabled()
    def refresh_enabled(self):self.generate.setEnabled(getattr(self,'key_ready',False) and bool(self.prompt.toPlainText().strip()))


class ImageCard(QWidget):
    def __init__(self,record,parent=None):
        super().__init__(parent);self.record=record;self.pixmap=QPixmap(record['path']);layout=QVBoxLayout(self);layout.setContentsMargins(0,4,0,0)
        self.preview=QLabel();self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter);self.preview.setMinimumSize(40,40);layout.addWidget(self.preview)
        self.preview.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
        if self.pixmap.isNull():self.preview.setText('La imagen ya no está disponible en esta PC.')
        title=('ChatGPT / OpenAI' if record['provider']=='OpenAI' else 'Gemini')+' · '+str(record.get('width',''))+' × '+str(record.get('height',''))
        layout.addWidget(label(title))
        row=QHBoxLayout();row.addWidget(button('Ver imagen',self.view,'screen'));row.addWidget(button('Guardar como…',self.save,'file'));layout.addLayout(row)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if not self.pixmap.isNull():self.preview.setPixmap(self.pixmap.scaled(max(40,self.width()),600,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
    def view(self):
        if self.pixmap.isNull():return
        dialog=QDialog(self);dialog.setWindowTitle('Imagen generada');dialog.resize(900,780);layout=QVBoxLayout(dialog)
        scroll=QScrollArea();picture=QLabel();picture.setPixmap(self.pixmap);scroll.setWidget(picture);layout.addWidget(scroll)
        dialog.show();self.full_view=dialog
    def save(self):
        if self.pixmap.isNull():return
        path,_=QFileDialog.getSaveFileName(self,'Guardar imagen','imagen-victor.png','PNG (*.png)')
        if path:
            if Path(path).suffix.lower()!='.png':path+='.png'
            try:shutil.copyfile(self.record['path'],path)
            except OSError: self.preview.setToolTip('No se pudo guardar en la carpeta elegida.')


class ImageController:
    def __init__(self,app):
        self.app=app;self.archive=ImageArchive(app.config,app.core.db);self.service=ImageService(app.config,self.archive)
        self.busy=False;self.pending=None;self.thread=None;self.cancel=threading.Event();self.events=queue.Queue()
        self.timer=QTimer(app);self.timer.timeout.connect(self.poll);self.timer.start(100)
    def explain(self,text,voice=False):
        answer='Sí, puedo generar imágenes aquí en VICTOR. Pulsa **Generar imagen** debajo del chat o dime qué imagen quieres crear. Podrás elegir **ChatGPT / OpenAI** o **Gemini**, y ver, ampliar y guardar el resultado en esta conversación. La generación necesita la clave API del proveedor elegido con permisos y cuota; la cuenta ChatGPT del chat es independiente.'
        self.app.voice_output.stop(preserve_music=bool(voice));self.app.entry.clear()
        self.app.voice_turn=bool(voice);self.app.active_remote=None;self.app.spotify_turn=None;self.app.spotify_ack=False
        self.app.core.history.add(self.app.conversation_id,'user',text);self.app.append_message('user',text)
        self.app.core.history.add(self.app.conversation_id,'assistant',answer);self.app.append_message('assistant',answer)
        self.app.voice_panel.transcript.setText('Dijiste: '+text);self.app.voice_panel.show_response();self.app.voice_panel.response.setText(answer)
        self.app.refresh_history();self.app.scroll_bottom()
        if voice:self.app.voice_output.speak('Sí, puedo generar imágenes. Dime qué quieres crear y elige ChatGPT o Gemini en el selector.')
    def request(self,text,voice=False,origin=None):
        if origin:
            self.app.error_label.setText('Para generar imágenes, elige el proveedor desde el chat de VICTOR en este PC.');return
        if self.busy or self.pending or self.app.core.busy.is_set() or self.app.closing:return
        self.app.voice_output.stop();self.app.entry.setPlainText(text)
        chooser=ImageChooser(self.app,text);self.pending=chooser
        chooser.finished.connect(lambda code:self.chosen(chooser,code,voice));chooser.show()
    def chosen(self,chooser,code,voice):
        self.pending=None
        if code!=QDialog.DialogCode.Accepted:chooser.deleteLater();return
        if self.app.core.busy.is_set() or self.app.closing:chooser.deleteLater();return
        prompt=chooser.prompt.toPlainText().strip()[:12000];provider=chooser.provider.currentData();model=chooser.model.currentText().strip()
        conversation=self.app.conversation_id;chooser.deleteLater();self.busy=True;self.cancel.clear()
        self.app.entry.clear();self.app.voice_turn=voice;self.app.active_remote=None
        self.app.core.history.add(conversation,'user',prompt);self.app.append_message('user',prompt)
        bubble=self.app.append_message('assistant','Generando imagen con '+('ChatGPT / OpenAI' if provider=='OpenAI' else provider)+'…')
        self.app.send_button.setEnabled(False);self.app.set_state('Pensando')
        def work():
            try:
                path,dimensions=self.service.generate(prompt,provider,model,self.cancel)
                self.events.put((bubble,conversation,voice,True,(path,provider,model,dimensions)))
            except Exception as exc:self.events.put((bubble,conversation,voice,False,str(exc) if isinstance(exc,VictorError) else 'No se pudo completar la imagen.'))
        self.thread=threading.Thread(target=work,name='victor-image',daemon=True);self.thread.start()
    def poll(self):
        try:bubble,conversation,voice,ok,result=self.events.get_nowait()
        except queue.Empty:return
        self.busy=False
        if self.app.closing:return
        from shiboken6 import isValid
        visible=self.app.conversation_id==conversation and isValid(bubble)
        if ok and not self.cancel.is_set():
            path,provider,model,dimensions=result
            try:
                record=self.archive.store(conversation,path,provider,model,dimensions)
                if visible:bubble.set_text('Aquí tienes tu imagen.');bubble.show_image(record)
                if voice:self.app.voice_output.speak('Aquí tienes tu imagen. La puedes ver en la conversación.')
            except Exception:
                if visible:bubble.set_text('La imagen se generó, pero no pude guardarla en el historial.')
        else:
            text='Generación cancelada.' if self.cancel.is_set() else result
            self.app.core.history.add(conversation,'assistant',text)
            if visible:bubble.set_text(text)
        if self.app.conversation_id==conversation and not visible:self.app.load_conversation(conversation)
        self.app.send_button.setEnabled(True);self.app.refresh_history();self.app.set_state(self.app.activity_state());self.app.scroll_bottom()
    def stop(self):
        self.cancel.set()
        if self.pending:self.pending.reject()
    def shutdown(self):self.stop();self.timer.stop()
