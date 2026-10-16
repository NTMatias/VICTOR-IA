"""Secciones Grafito; todos los controles usan los servicios y permisos existentes."""
import json
import webbrowser
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QBoxLayout, QGridLayout, QFormLayout,
    QScrollArea, QFrame, QLabel, QPushButton, QLineEdit, QPlainTextEdit, QComboBox, QCheckBox,
    QMessageBox, QListWidget, QSlider, QFileDialog, QTabWidget, QStackedWidget, QSpinBox, QProgressBar)
from victor.gui.service_cards import ServiceList, StatusText, CoverArt, friendly_date, sender, file_type
from victor.config import PROVIDERS, KEYS
from victor.errors import VictorError
from victor.gui.widgets import icon, display_text, ResponsiveButtons, brand_icon, AdaptiveButton, ActionTile


def label(text, kind='secondary'):
    w=QLabel(text); w.setObjectName(kind); w.setWordWrap(True); w.setTextFormat(Qt.TextFormat.PlainText)
    return w

def button(text, callback, glyph=None, primary=False, danger=False):
    w=AdaptiveButton(text); w.setObjectName('danger' if danger else 'primary' if primary else 'normal')
    if glyph: w.setIcon(icon(glyph, '#F28F95' if danger else '#E9EAF1' if primary else '#A9C8FF'))
    w.clicked.connect(callback); return w

def card(title):
    w=QFrame(); w.setObjectName('card'); l=QVBoxLayout(w); l.setContentsMargins(20,20,20,20); l.setSpacing(16)
    if title: l.addWidget(label(title, 'cardTitle'))
    return w,l

def notice(text):
    w=label(text); w.setStyleSheet('background: #252A34; border: 1px solid #455876; border-radius: 8px; padding: 12px; color: #C3CCDB;')
    return w

class Columns(QWidget):
    def __init__(self, *widgets, weights=None, breakpoint=720):
        super().__init__(); self.box=QBoxLayout(QBoxLayout.Direction.LeftToRight,self)
        self.breakpoint=breakpoint
        self.box.setContentsMargins(0,0,0,0); self.box.setSpacing(16)
        for i,w in enumerate(widgets): self.box.addWidget(w, (weights or [1]*len(widgets))[i])
    def resizeEvent(self,event):
        super().resizeEvent(event)
        available=getattr(self,'available_width',self.width())
        self.box.setDirection(QBoxLayout.Direction.TopToBottom if available<self.breakpoint else QBoxLayout.Direction.LeftToRight)

class Page(QScrollArea):
    def __init__(self, title, subtitle, eyebrow, actions=()):
        super().__init__(); self.setWidgetResizable(True)
        self.body=QWidget(); self.body.setObjectName('pageBody'); self.setWidget(self.body)
        self.content=QVBoxLayout(self.body); self.content.setContentsMargins(28,24,28,28); self.content.setSpacing(16)
        self.content.addWidget(label(eyebrow.upper(),'caption'))
        row=QBoxLayout(QBoxLayout.Direction.LeftToRight);self.heading_row=row; titles=QVBoxLayout(); titles.setSpacing(8)
        self.title=label(title,'sectionTitle'); titles.addWidget(self.title); titles.addWidget(label(subtitle))
        row.addLayout(titles,1)
        for action in actions: row.addWidget(action,alignment=Qt.AlignmentFlag.AlignBottom)
        self.content.addLayout(row)
    def showEvent(self,event):
        super().showEvent(event)
        # Una página oculta puede conservar el ancho calculado antes de apilar
        # sus columnas. Recalcular cuando sus layouts vuelven a estar visibles.
        QTimer.singleShot(0,self.settle_width)
    def settle_width(self):
        self.content.activate()
        if self.horizontalScrollBar().maximum() and self.body.minimumSizeHint().width()<=self.viewport().width():
            self.setWidgetResizable(False);self.setWidgetResizable(True)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.heading_row.setDirection(QBoxLayout.Direction.TopToBottom if self.viewport().width()<650 else QBoxLayout.Direction.LeftToRight)
        # El viewport evita que un hijo ancho mantenga columnas que deberían apilarse.
        narrow=self.viewport().width()<650
        for columns in self.body.findChildren(Columns):
            narrow_columns=columns.width()<columns.breakpoint if columns.breakpoint!=720 else self.viewport().width()<776
            columns.box.setDirection(QBoxLayout.Direction.TopToBottom if narrow_columns else QBoxLayout.Direction.LeftToRight)
        for row in self.body.findChildren(QHBoxLayout):row.setDirection(QBoxLayout.Direction.TopToBottom if narrow else QBoxLayout.Direction.LeftToRight)
        for grid in self.body.findChildren(ResponsiveButtons):
            grid.available_width=max(100,self.viewport().width()-96);grid.arrange()
        from PySide6.QtWidgets import QSizePolicy
        for text in self.body.findChildren(QLabel):
            if text.wordWrap() and text.objectName()!='badge':
                policy=text.sizePolicy();policy.setHorizontalPolicy(QSizePolicy.Policy.Ignored);policy.setHeightForWidth(True);text.setSizePolicy(policy)
        for combo in self.body.findChildren(QComboBox):
            combo.setMinimumContentsLength(5);combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        for action in self.body.findChildren(AdaptiveButton):action.updateGeometry()
        for tile in self.body.findChildren(ActionTile):tile.sync_height()
    def finish(self): self.content.addStretch(1)


class SpotifyPage(QScrollArea):
    """The original Qt playback card beside the single embedded music browser."""
    def __init__(self):
        super().__init__();self.setWidgetResizable(True)
        self.body=QWidget();self.body.setObjectName('pageBody');self.setWidget(self.body)
        self.content=QVBoxLayout(self.body);self.content.setContentsMargins(16,16,16,16);self.content.setSpacing(12)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        for action in self.body.findChildren(AdaptiveButton):action.updateGeometry()
        for columns in self.body.findChildren(Columns):
            if columns.breakpoint:
                columns.available_width=self.viewport().width()
                columns.box.setDirection(QBoxLayout.Direction.TopToBottom if self.viewport().width()<columns.breakpoint else QBoxLayout.Direction.LeftToRight)
        for grid in self.body.findChildren(ResponsiveButtons):
            reserve=32 if grid.parentWidget() is self.body else 160
            grid.available_width=max(100,self.viewport().width()-reserve);grid.arrange()


class SettingsManager(QWidget):
    """Editor único de configuración, dividido en las páginas del diseño."""
    GROUPS={
        'ia': ('provider','models','fallback','temperature','max_tokens','context_chars','ai_reasoning_effort'),
        'voice_settings': ('voice_mode','voice_background_listening','wake_word','language','microphone','voice_backend','whisper_model','openai_transcription_model','voice_vocabulary','voice_corrections','voice_enabled','tts_backend','voice_id','edge_voice','voice_rate','voice_pitch','speech_dictionary','conversation_window','voice_noise_reduction','voice_echo_cancellation','voice_noise_level'),
        'general': ('theme','auto_search','network_timeout','telegram_enabled','local_remote_enabled','telegram_paused','desktop_orb_enabled','desktop_orb_corner'),
        'personality': ('name','personality','formality','system_prompt'),
        'ollama': ('ollama_url','ollama_light','ollama_gpu','ollama_timeout','ollama_context','ollama_keep_alive'),
        'vision_settings': ('vision_provider','vision_model'),
        'security': ('security','action_confirmations','remote_block_all','remote_high_policy','remote_rate_limit','telegram_allowed_ids','allowed_folders','applications'),
    }
    TITLES={
        'ia': ('Modelos e inteligencia artificial','Administra los modelos, parámetros y mecanismos de respaldo.'),
        'voice_settings': ('Configuración de voz','Escucha, activación y respuestas habladas en un solo lugar.'),
        'general': ('Preferencias generales','Personaliza la apariencia y el comportamiento de VICTOR.'),
        'personality': ('Identidad y personalidad','Define cómo habla VICTOR y cómo responde a tus preguntas.'),
        'ollama': ('Ollama local','Configura el servidor y los recursos del modelo en tu equipo.'),
        'vision_settings': ('Modelos para visión','Configura el análisis visual de capturas de pantalla.'),
        'security': ('Seguridad y permisos','Decide qué puede hacer el asistente y qué necesita confirmación.'),
    }
    LABELS={'desktop_orb_enabled':'Mostrar orbe en el escritorio','desktop_orb_corner':'Esquina del orbe','provider':'Proveedor principal','fallback':'Orden de respaldo','temperature':'Temperatura','max_tokens':'Límite de tokens',
        'context_chars':'Contexto conversacional (caracteres)','voice_mode':'Modo de escucha','wake_word':'Palabra de activación',
        'language':'Idioma','microphone':'Micrófono (índice; vacío = predeterminado)','voice_backend':'Motor de reconocimiento',
        'whisper_model':'Modelo Whisper','voice_enabled':'Leer respuestas en voz alta','tts_backend':'Motor de síntesis',
        'openai_transcription_model':'Modelo de reconocimiento OpenAI',
        'voice_background_listening':'Iniciar escucha continua al abrir VICTOR',
        'voice_noise_reduction':'Reducir ruido del micrófono','voice_echo_cancellation':'Cancelar eco de altavoces','voice_noise_level':'Intensidad de reducción de ruido',
        'voice_id':'Identificador de voz SAPI','edge_voice':'Voz de Edge','voice_rate':'Velocidad de voz',
        'voice_vocabulary':'Nombres propios (separados por comas)', 'voice_corrections':'Correcciones musicales (una por línea: oído => correcto)',
        'conversation_window':'Conversación tras activación (segundos)','theme':'Tema de la aplicación','auto_search':'Buscar información actual automáticamente',
        'network_timeout':'Tiempo de espera de red (segundos)','telegram_enabled':'Activar Telegram al iniciar',
        'local_remote_enabled':'Permitir servidor HTTPS local','telegram_paused':'Pausar órdenes Telegram',
        'name':'Nombre del asistente','personality':'Personalidad','formality':'Formalidad','system_prompt':'Instrucciones del asistente',
        'ollama_url':'URL del servidor','ollama_light':'Modo ligero (modelo 3B)','ollama_gpu':'CPU / GPU',
        'ollama_timeout':'Tiempo de espera (segundos)','ollama_context':'Contexto del modelo (tokens)','ollama_keep_alive':'Mantener cargado (ej. 5m)',
        'vision_provider':'Proveedor de visión','vision_model':'Modelo de visión','security':'Nivel de seguridad',
        'action_confirmations':'Pedir confirmación antes de acciones', 'remote_block_all':'Bloquear todo acceso remoto','remote_high_policy':'Acciones altas desde Telegram (block / pc)',
        'remote_rate_limit':'Límite de órdenes Telegram por minuto','telegram_allowed_ids':'Usuarios Telegram autorizados (JSON)',
        'allowed_folders':'Carpetas autorizadas (JSON)','applications':'Aplicaciones por alias (JSON)'}
    def __init__(self, app):
        super().__init__(); self.app,self.fields,self.pages=app,{},{}
        self.error=label(''); self.messages={}; self.api_key_fields={}; self.api_key_status={}
        for group,keys in self.GROUPS.items(): self.pages[group]=self.build_group(group,keys)

    def field(self,key,value):
        choices={'provider':PROVIDERS,'vision_provider':PROVIDERS,'theme':('Dark','Light','System'),'security':('normal','strict'),
            'voice_mode':('manual','push-to-talk','continua'),'voice_backend':('whisper','google','openai'),'ollama_gpu':('auto','cpu'),
            'openai_transcription_model':('gpt-transcribe','gpt-4o-transcribe','gpt-4o-mini-transcribe'),
            'tts_backend':('edge','sapi'),'remote_high_policy':('block','pc'),
            'voice_noise_level':('suave','moderado','intenso'),
            'desktop_orb_corner':('bottom-right','bottom-left','top-right','top-left'),
            'edge_voice':('es-MX-JorgeNeural','es-EC-LuisNeural','es-CO-GonzaloNeural','es-PE-AlexNeural','es-MX-DaliaNeural')}
        if isinstance(value,bool): w=QCheckBox(); w.setChecked(value)
        elif key=='desktop_orb_corner':
            w=QComboBox()
            for title,corner in [('Abajo a la derecha','bottom-right'),('Abajo a la izquierda','bottom-left'),('Arriba a la derecha','top-right'),('Arriba a la izquierda','top-left')]:w.addItem(title,corner)
            w.setCurrentIndex(w.findData(value))
        elif key in choices:
            w=QComboBox(); w.addItems(choices[key])
            if key=='edge_voice': w.setEditable(True)
            w.setCurrentText(str(value))
        elif key in ('temperature','max_tokens','context_chars','voice_rate','ollama_context'):
            bounds={'temperature':(0,200,100),'max_tokens':(128,16384,1),'context_chars':(8000,80000,1),'voice_rate':(80,350,1),'ollama_context':(2048,16384,1)}
            lo,hi,factor=bounds[key]; w=QSlider(Qt.Orientation.Horizontal); w.setRange(lo,hi); w.setValue(round(value*factor)); w.setProperty('factor',factor)
        elif isinstance(value,(list,dict)) or key in ('personality','system_prompt','voice_vocabulary','voice_corrections'):
            w=QPlainTextEdit(json.dumps(value,ensure_ascii=False,indent=2) if isinstance(value,(list,dict)) else value); w.setMinimumHeight(90); w.setMaximumHeight(150)
            if isinstance(value,(list,dict)):w.setStyleSheet("font-family:'IBM Plex Mono'; font-size:12px;")
        else: w=QLineEdit(str(value))
        self.fields[key]=w; return w

    def add_field(self,layout,key,value):
        if key=='models':
            for p in PROVIDERS:
                w=QLineEdit(value[p]); self.fields['model:'+p]=w
                layout.addWidget(label('Modelo '+p)); layout.addWidget(w)
            return
        w=self.field(key,value)
        row=QHBoxLayout(); row.addWidget(label(self.LABELS.get(key,key)),1)
        if isinstance(w,QSlider):
            reading=label(str(value));reading.setWordWrap(False);reading.setProperty('slider_readout',True);row.addWidget(reading)
            w.valueChanged.connect(lambda v,r=reading,f=w.property('factor'):r.setText(f'{v/f:g}'))
        layout.addLayout(row); layout.addWidget(w)


    def build_group(self,group,keys):
        title,desc=self.TITLES[group]
        save_keys=tuple(keys)+(('models',) if group=='ollama' else ('context_chars',) if group=='personality' else ())
        save=button('Guardar política' if group=='security' else 'Guardar cambios',lambda:self.save(save_keys),'check',True)
        page=Page(title,desc,'Seguridad / políticas' if group=='security' else 'Ajustes / '+title,(save,))
        left,right=QWidget(),QWidget(); ll,rl=QVBoxLayout(left),QVBoxLayout(right)
        for l in (ll,rl): l.setContentsMargins(0,0,0,0);l.setSpacing(12)
        cfg=self.app.config.snapshot()
        def panel(side,title,fields=()):
            c,l=card(title); (ll if side=='left' else rl).addWidget(c)
            for key in fields:self.add_field(l,key,cfg[key])
            return c,l
        def linked(key,layout):
            original=self.fields[key]
            if isinstance(original,QLineEdit):
                w=QLineEdit(original.text());w.textEdited.connect(original.setText);original.textChanged.connect(w.setText)
            elif isinstance(original,QSlider):
                w=QSlider(Qt.Orientation.Horizontal);w.setRange(original.minimum(),original.maximum());w.setValue(original.value());w.valueChanged.connect(original.setValue);original.valueChanged.connect(w.setValue)
            else:return
            layout.addWidget(label('Modelo local' if key=='model:Ollama' else self.LABELS.get(key,key)));layout.addWidget(w)
        if group=='ia':
            c,l=panel('left','Proveedor principal'); self.provider_buttons={}
            from PySide6.QtWidgets import QButtonGroup
            self.provider_group=QButtonGroup(self);self.provider_group.setExclusive(True)
            self.field('provider',cfg['provider']).hide()
            self.model_stack=QStackedWidget()
            for index,provider in enumerate(PROVIDERS):
                w=button(provider+'\n'+('Local' if provider=='Ollama' else 'API'),lambda checked=False,p=provider:self.select_provider(p))
                w.setIcon(brand_icon(provider));w.setIconSize(__import__('PySide6.QtCore',fromlist=['QSize']).QSize(26,26))
                w.setCheckable(True);w.setStyleSheet('min-height:42px;');self.provider_buttons[provider]=w;self.provider_group.addButton(w)
                model=QLineEdit(cfg['models'][provider]);self.fields['model:'+provider]=model;self.model_stack.addWidget(model)
            l.addWidget(ResponsiveButtons(self.provider_buttons.values(),columns=4,cell_width=112));l.addWidget(label('Modelo activo'));l.addWidget(self.model_stack)
            l.addWidget(label('Proveedor principal'));l.addWidget(self.fields['provider']);self.fields['provider'].show()
            self.fields['provider'].currentTextChanged.connect(self.select_provider);self.select_provider(cfg['provider'])
            _,order=panel('left','Orden de respaldo')
            self.fallback_list=QListWidget();self.fallback_list.setFixedHeight(135)
            self.fallback_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
            self.fallback_list.addItems(cfg['fallback']);order.addWidget(self.fallback_list)
            self.field('fallback',cfg['fallback']).hide()
            self.fallback_list.model().rowsMoved.connect(self.sync_fallback)
            row=QHBoxLayout();self.fallback_provider=QComboBox();self.fallback_provider.addItems(PROVIDERS);row.addWidget(self.fallback_provider,1)
            row.addWidget(button('Añadir',self.add_fallback,'plus'));row.addWidget(button('Quitar',self.remove_fallback,'close'));order.addLayout(row)
            order.addWidget(label('Arrastra para cambiar el orden. Cada proveedor usa su modelo editable.'))
            panel('right','Parámetros de generación',('temperature','max_tokens','context_chars','ai_reasoning_effort'))
            from victor.gui.ai_accounts import AccountPanel
            self.account_panels={};self.account_cards={}
            for provider in ('OpenAI',):
                account_card,accounts_layout=panel('left','');self.account_cards[provider]=account_card;ll.insertWidget(1,account_card)
                account_panel=AccountPanel(self.app,provider);self.account_panels[provider]=account_panel;accounts_layout.addWidget(account_panel)
            gemini_card,gemini_layout=panel('left','Gemini · API key')
            self.account_cards['Gemini']=gemini_card;ll.insertWidget(1,gemini_card)
            gemini_layout.addWidget(label('Gemini se conecta mediante tu clave personal. Obtén la clave en Google AI Studio y guárdala en Claves API personales.'))
            self.gemini_key_link=button('Obtener API key de Gemini',lambda:webbrowser.open('https://aistudio.google.com/apikey'),'link')
            gemini_layout.addWidget(self.gemini_key_link)
            self.select_provider(cfg['provider'])
            _,l=panel('right','Claves API personales')
            l.addWidget(label('Introduce tu propia clave para cada proveedor. Se guarda cifrada para tu usuario de Windows y se usa en la siguiente petición.'))
            for provider in KEYS:
                l.addWidget(label(provider,'bodyTitle'))
                if provider=='Gemini':
                    l.addWidget(button('Crear o consultar clave en Google AI Studio',lambda:webbrowser.open('https://aistudio.google.com/apikey'),'link'))
                entry=QLineEdit();entry.setEchoMode(QLineEdit.EchoMode.Password);entry.setMaxLength(4096)
                entry.setPlaceholderText('Pega una clave nueva para guardar o reemplazar')
                entry.setAccessibleName('Clave API personal de '+provider);self.api_key_fields[provider]=entry;l.addWidget(entry)
                state=label('');self.api_key_status[provider]=state;l.addWidget(state)
                row=QHBoxLayout()
                show=QCheckBox('Mostrar clave');show.toggled.connect(lambda visible,w=entry:w.setEchoMode(QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password));l.addWidget(show)
                row.addWidget(button('Guardar clave',lambda checked=False,p=provider:self.save_api_keys(p),'check'))
                row.addWidget(button('Quitar clave personal',lambda checked=False,p=provider:self.remove_api_key(p),'close'))
                l.addLayout(row)
                l.addWidget(button('Probar conexión '+provider,lambda checked=False,p=provider:self.test_api(p),'link'))
            l.addWidget(notice('Ollama es local y no requiere clave. La clave personal tiene prioridad sobre .env. Al quitarla, vuelve a usarse la de .env si existe. Guardar no comprueba saldo ni permisos.'))
            self.refresh_api_keys()
        elif group=='voice_settings':
            _,l=panel('left','Reconocimiento de voz',('voice_backend','openai_transcription_model'))
            self.recognition_state=label('');l.addWidget(self.recognition_state)
            l.addWidget(label('OpenAI transcribe tu audio con su API. Puedes conversar con Gemini, Anthropic u Ollama y usar OpenAI solo para reconocer tu voz.'))
            l.addWidget(notice('OpenAI requiere Internet y una clave con saldo o facturación de API; el audio se envía a OpenAI al activar la escucha. Whisper es local. Google conserva su reconocimiento por Internet.'))
            l.addWidget(button('Configurar clave OpenAI',lambda:self.app.navigate('ia'),'link'))
            self.fields['voice_backend'].currentTextChanged.connect(self.refresh_recognition)
            self.fields['openai_transcription_model'].currentTextChanged.connect(self.refresh_recognition)
            _,l=panel('left','Entrada y escucha',('voice_mode','voice_background_listening','wake_word','microphone','language','conversation_window'))
            _,clean=panel('left','Ruido y eco',('voice_noise_reduction','voice_echo_cancellation','voice_noise_level'))
            clean.addWidget(label('Procesamiento WebRTC gratuito y local. La cancelación de eco compara el micrófono con el sonido de salida de Windows, sin guardar ni enviar esa referencia. Usa moderado para empezar; intenso puede alterar más la voz. No elimina todas las voces ajenas ni la reverberación de la habitación.'))
            clean.addWidget(button('Probar micrófono sin ejecutar órdenes',self.app.test_microphone,'mic'))
            l.addWidget(label('En modo continua, di «VICTOR», espera «¿En qué te ayudo?» y haz una petición. Puedes interrumpir su voz diciendo VICTOR; la activación durante la voz usa Whisper local. La música permanece baja mientras espera tu petición: si no empiezas a hablar en unos 8 segundos, recupera el volumen. Después de una petición vuelve a esperar VICTOR. También acepta nombre y orden en una frase, con otra app activa o minimizada. Manual escucha al pulsar el micrófono. Cerrar la app o silenciar el micrófono detiene la escucha.'))
            l.addWidget(label('Al activar el inicio automático autorizas la captura del micrófono al abrir la app; los motores Google/OpenAI envían las intervenciones al servicio seleccionado.'))
            _,l=panel('left','Modelo para Whisper local',('whisper_model',))
            self.whisper_state=label('Comprobando modelo…');l.addWidget(self.whisper_state)
            self.whisper_progress=QProgressBar();l.addWidget(self.whisper_progress)
            row=QHBoxLayout();row.addWidget(button('Descargar modelo',lambda:self.app.maintenance.launch('download'),'mic'))
            row.addWidget(button('Cancelar descarga',lambda:self.app.maintenance.process.kill(),'close'));l.addLayout(row)
            _,l=panel('left','Vocabulario y correcciones',('voice_vocabulary','voice_corrections'))
            l.addWidget(label('OpenAI y Whisper utilizan estos nombres como pistas. Las correcciones sustituyen el título/artista completo únicamente en órdenes de música con cualquiera de los tres motores.'))
            l.addWidget(notice('Añade canciones, artistas o aplicaciones que uses. Para mayor precisión puedes elegir Whisper small y descargarlo; necesita más memoria y tiempo que base.'))
            _,l=panel('right','Salida de voz',('voice_enabled','tts_backend','edge_voice','voice_id','voice_rate','voice_pitch','speech_dictionary'))
            l.addWidget(label('Jorge: voz masculina de México. Luis: voz masculina de Ecuador. Los signos de formato se convierten en pausas; el texto del chat se conserva.'))
            l.addWidget(button('Probar voz seleccionada',self.preview_voice,'volume'))
            _,l=panel('right','Verificación y acciones');l.addWidget(button('Activar escucha',lambda:self.app.navigate('voice'),'mic'))
            l.addWidget(button('Confirmar por voz',self.app.listen_approval,'shield'));l.addWidget(notice('La confirmación por voz solo se habilita para una acción pendiente en este PC.'))
            self.refresh_recognition()
        elif group=='general':
            _,orb=panel('left','Orbe del escritorio',('desktop_orb_enabled','desktop_orb_corner'))
            orb.addWidget(notice('Azul: tu voz. Violeta: voz de VICTOR. Mantén pulsado el centro y arrastra para moverlo. Permanece quieto en silencio.'))
            _,access=panel('right','Acceso a la aplicación')
            access.addWidget(button('Cambiar contraseña local',self.change_local_password,'lock'))
            access.addWidget(button('Administración de cuentas',self.open_cloud_admin,'shield'))
            access.addWidget(button('Comprobar actualizaciones',self.check_updates,'download'))
            _,l=panel('left','Apariencia',('theme',));row=QHBoxLayout()
            for text,value in [('Oscuro','Dark'),('Claro','Light'),('Seguir sistema','System')]:row.addWidget(button(text,lambda checked=False,v=value:self.fields['theme'].setCurrentText(v)))
            l.addLayout(row)
            _,l=panel('left','Experiencia del chat',('auto_search',));l.addWidget(button('Modo presentación · F11',self.app.toggle_presentation,'fullscreen'))
            _,l=panel('right','Red y rendimiento',('network_timeout',));l.addWidget(button('Comprobar conexiones',lambda:self.app.maintenance.check_connections(),'wifi'))
            _,l=panel('right','Integraciones y permisos',('telegram_enabled','local_remote_enabled','telegram_paused'))
            l.addWidget(button('Ir a conexiones',lambda:self.app.navigate('spotify'),'link'));l.addWidget(button('Ver seguridad',lambda:self.app.navigate('security'),'shield'));l.addWidget(button('Herramientas avanzadas',lambda:self.app.navigate('windows'),'apps'))
        elif group=='ollama':
            _,l=panel('left','Servidor y modelo',('ollama_url',));linked('model:Ollama',l)
            panel('left','Modo de ejecución',('ollama_gpu','ollama_light','ollama_timeout'))
            panel('right','Memoria y contexto',('ollama_context','ollama_keep_alive'))
            _,l=panel('right','Consejos de rendimiento');l.addWidget(notice('Usa un modelo pequeño y reduce el contexto si falta memoria. Auto permite que Ollama detecte la GPU. CPU fuerza ejecución sin GPU.'))
        elif group=='personality':
            _,l=panel('left','Identidad',('name','personality','formality'));linked('language',l)
            _,l=panel('left','Preferencias');linked('context_chars',l);l.addWidget(label('Se conservan mensajes recientes y un resumen de los antiguos.'))
            _,l=panel('right','Instrucciones del asistente',('system_prompt',));l.addWidget(label('Estas instrucciones no cambian los permisos del PC.'))
            _,l=panel('right','Vista previa del tono');l.addWidget(notice('El modelo usará tu nombre, personalidad, formalidad e idioma en el siguiente mensaje. La respuesta real depende del proveedor.'))
        elif group=='vision_settings':
            panel('left','Proveedor de visión',('vision_provider','vision_model'))
            _,l=panel('left','Capacidades admitidas')
            for question,glyph in [('¿Qué error aparece?','screen'),('Lee el texto que aparece','file'),('¿Qué hay en mi pantalla?','screen')]:
                l.addWidget(button(question,lambda checked=False,q=question:self.analyze_from_settings(q),glyph))
            _,l=panel('right','Análisis de pantalla');l.addWidget(button('Abrir pantalla y visión',lambda:self.app.navigate('vision'),'screen'))
            l.addWidget(label('El análisis real se muestra en Herramientas / Pantalla y visión. Necesita un modelo compatible y autorización para enviar la imagen.'))
            _,l=panel('right','Privacidad');l.addWidget(notice('Las capturas solo se transmiten cuando solicitas un análisis y aceptas el permiso. Las claves nunca aparecen en esta pantalla.'))
        elif group=='security':
            _,l=panel('left','Nivel de seguridad',('security','action_confirmations','remote_block_all','remote_high_policy','remote_rate_limit'))
            l.addWidget(notice('Desactiva «Pedir confirmación» para ejecutar las acciones directamente. El bloqueo remoto, las rutas permitidas y la validación de argumentos permanecen activos.'))
            panel('left','Recursos autorizados',('allowed_folders','applications','telegram_allowed_ids'))
            _,l=panel('right','Confirmaciones opcionales');l.addWidget(label('Si activas las confirmaciones, las solicitudes aparecen en un diálogo con el detalle de la acción.'))
            l.addWidget(button('Ver confirmación pendiente',self.app.show_pending_approval,'shield'));l.addWidget(button('Confirmar por voz',self.app.listen_approval,'mic'))
            _,l=panel('right','Protecciones activas');l.addWidget(notice('Validación de rutas · Sin sobrescritura · Papelera · Comandos bloqueados · Revocación de sesiones'))
            l.addWidget(button('Detener todas las sesiones remotas',self.app.local_remote.stop,'stop',danger=True));l.addWidget(button('Ver auditoría',lambda:self.app.navigate('diagnostics'),'list'))
            _,l=panel('right','Acceso y clave personal')
            l.addWidget(label('Protección de inicio de sesión con clave maestra o PIN para este equipo.'))
            l.addWidget(button('Cambiar clave de acceso',self.open_change_password,'lock'))
            l.addWidget(button('Bloquear aplicación ahora',self.app.lock_session,'lock'))
        ll.addStretch();rl.addStretch();page.content.addWidget(Columns(left,right))
        message=label('');self.messages[group]=message;page.content.addWidget(message);page.finish();return page

    def open_change_password(self):
        from victor.gui.login import ChangePasswordDialog
        dialog=ChangePasswordDialog(self.app.auth,self)
        if dialog.exec():
            self.show_message('Contraseña actualizada correctamente.')

    def analyze_from_settings(self, question):
        self.app.navigate('vision')
        self.app.sections.task('analyze_screen',{'question':question,'region':None},self.app.sections.vision_output)

    def sync_fallback(self,*args):
        self.fields['fallback'].setPlainText(json.dumps([self.fallback_list.item(i).text() for i in range(self.fallback_list.count())]))
    def add_fallback(self):
        p=self.fallback_provider.currentText()
        if p not in [self.fallback_list.item(i).text() for i in range(self.fallback_list.count())]:self.fallback_list.addItem(p)
        self.sync_fallback()
    def remove_fallback(self):
        row=self.fallback_list.currentRow()
        if row>=0:self.fallback_list.takeItem(row);self.sync_fallback()

    def select_provider(self,provider):
        if self.fields['provider'].currentText()!=provider: self.fields['provider'].setCurrentText(provider)
        for p,w in self.provider_buttons.items():
            w.setChecked(p==provider)
            w.setText(p+'\n'+('Cuenta' if self.app.config.get('auth_methods').get(p)=='account' else 'Local' if p=='Ollama' else 'API'))
        for p,w in getattr(self,'account_cards',{}).items():w.setVisible(p==provider)
        self.model_stack.setCurrentIndex(PROVIDERS.index(provider))
        self.model_stack.setVisible(self.app.config.get('auth_methods').get(provider)!='account')
        for key in ('temperature','max_tokens'):
            if key in self.fields:self.fields[key].setEnabled(self.app.config.get('auth_methods').get(provider)!='account')

    def refresh_api_keys(self):
        for provider, label_widget in self.api_key_status.items():
            try: label_widget.setText(self.app.config.credential_source(provider))
            except VictorError as exc: label_widget.setText(str(exc))
        self.refresh_recognition()

    def refresh_recognition(self,*args):
        if not hasattr(self,'recognition_state'):return
        backend=self.fields['voice_backend'].currentText()
        self.fields['openai_transcription_model'].setEnabled(backend=='openai')
        if backend=='openai':
            try:
                ready=bool(self.app.config.api_key('OpenAI'))
                status='Clave configurada; conexión y saldo aún no comprobados.' if ready else 'Falta tu clave OpenAI. Guárdala en Ajustes → IA → Claves API personales.'
            except VictorError as exc:status=str(exc)
            self.recognition_state.setText('OpenAI · '+self.fields['openai_transcription_model'].currentText()+'\n'+status)
        else:
            self.recognition_state.setText('Whisper · reconocimiento local.' if backend=='whisper' else 'Google · reconocimiento por Internet.')

    def save_api_keys(self,provider=None):
        if self.app.core.busy.is_set():
            self.show_message('Espera a que termine el turno.');return False
        values={p:w.text().strip() for p,w in self.api_key_fields.items() if (provider is None or p==provider) and w.text().strip()}
        if not values:
            if provider is not None:self.show_message('Pega primero una clave nueva.')
            return provider is None
        try:
            if QMessageBox.question(self,'Guardar clave API','Estas claves usan la API y su facturación independiente de las suscripciones. ¿Guardar y autorizar su uso cuando selecciones el método API?')!=QMessageBox.StandardButton.Yes:return False
            self.app.config.credentials.update(values)
            for p in values:self.api_key_fields[p].clear()
            self.refresh_api_keys();self.app.refresh_config()
            self.show_message('Claves guardadas con cifrado de Windows. Se usarán en la siguiente petición.');return True
        except VictorError as exc:self.show_message(str(exc));return False

    def test_api(self,provider):
        if self.app.core.busy.is_set() or (self.app.auth_thread and self.app.auth_thread.is_alive()):self.show_message('Espera a que termine la operación actual.');return
        if QMessageBox.question(self,'Probar API','Se enviará una consulta breve a '+provider+' con la clave guardada. Puede generar un cargo de API. ¿Continuar?')!=QMessageBox.StandardButton.Yes:return
        import threading
        def check():
            try:
                from victor.ai.manager import AIManager
                from types import SimpleNamespace
                cfg=self.app.config.snapshot();cfg['provider']=provider;cfg['fallback']=[];cfg['auth_methods']={**cfg['auth_methods'],provider:'api'}
                manager=AIManager(SimpleNamespace(snapshot=lambda:cfg,api_key=self.app.config.api_key),lambda *args:None)
                manager.generate([{'role':'user','content':'Responde únicamente OK.'}],'Responde únicamente OK.',[],self.app.integration_cancel)
                self.app.emit('notice',provider+' API: conexión y respuesta comprobadas.')
            except Exception as exc:self.app.emit('notice',str(exc) if isinstance(exc,VictorError) else 'No pude probar '+provider+' API.')
        self.app.auth_thread=threading.Thread(target=check,name='victor-api-probe',daemon=True);self.app.auth_thread.start()

    def remove_api_key(self,provider):
        if self.app.core.busy.is_set():self.show_message('Espera a que termine el turno.');return
        try:
            self.app.config.credentials.update({provider:None});self.api_key_fields[provider].clear()
            self.refresh_api_keys();self.app.refresh_config();self.show_message('Clave personal eliminada. '+self.app.config.credential_source(provider)+'.')
        except VictorError as exc:self.show_message(str(exc))

    def preview_voice(self):
        values={key:self.fields[key].currentText() if isinstance(self.fields[key],QComboBox) else self.fields[key].text()
                for key in ('tts_backend','edge_voice','voice_id')}
        values['voice_rate']=self.fields['voice_rate'].value()
        self.app.voice_output.speak('Hola, soy Víctor. ¿Escuchamos música? Puedo reproducir tu canción favorita (sin interrupciones). ¡Vamos!',settings=values,force=True)

    def change_local_password(self):
        if not self.app.auth.authenticated:return
        from .login import ChangePasswordDialog
        dialog=ChangePasswordDialog(self.app.auth,self);dialog.exec()

    def open_cloud_admin(self):
        if not getattr(self.app.auth,'cloud',False):
            self.show_message('La nube aún no está conectada. Configura deployment.json para habilitar cuentas y administración.');return
        from .cloud_admin import CloudAdmin
        self.admin_dialog=CloudAdmin(self.app.auth,self);self.admin_dialog.show()

    def check_updates(self):
        if not self.app.updates.settings.get('enabled'):
            self.show_message('Las actualizaciones aún no están configuradas para esta distribución.');return
        import threading
        def run():
            try:
                record=self.app.updates.check()
                self.app.emit('update_available',record) if record else self.app.emit('update_status','Esta versión está al día.')
            except Exception:self.app.emit('update_status','No se pudo verificar la publicación de actualizaciones.')
        threading.Thread(target=run,name='victor-check-update',daemon=True).start()

    def save(self,keys=None):
        if self.app.core.busy.is_set(): self.show_message('Espera a que termine el turno.'); return
        try:
            old=self.app.config.snapshot(); values={}; models=dict(old['models'])
            for key,w in self.fields.items():
                original='models' if key.startswith('model:') else key
                if keys is not None and original not in keys: continue
                if key.startswith('model:'): models[key[6:]]=w.text().strip(); continue
                if isinstance(w,QCheckBox): value=w.isChecked()
                elif isinstance(w,QComboBox): value=w.currentData() if key=='desktop_orb_corner' else w.currentText()
                elif isinstance(w,QSlider): value=w.value()/w.property('factor'); value=int(value) if isinstance(old[key],int) else value
                else:
                    raw=w.toPlainText() if isinstance(w,QPlainTextEdit) else w.text()
                    value=json.loads(raw) if isinstance(old[key],(dict,list)) else int(raw) if isinstance(old[key],int) else float(raw) if isinstance(old[key],float) else raw.strip()
                values[key]=value
            if values.get('desktop_orb_corner',old['desktop_orb_corner'])!=old['desktop_orb_corner']:values['desktop_orb_position']=None
            if keys is None or 'models' in keys: values['models']=models
            self.app.config.validate({**old,**values})
            if (keys is None or 'models' in keys) and not self.save_api_keys():return
            guarded=('security','applications','allowed_folders','telegram_allowed_ids','remote_high_policy','remote_block_all','local_remote_enabled')
            if values.get('action_confirmations', old['action_confirmations']) and any(k in values and values[k]!=old[k] for k in guarded):
                if QMessageBox.question(self,'Cambiar permisos','¿Guardar estos cambios de permisos? Las acciones de alto riesgo mantienen la confirmación explícita.')!=QMessageBox.StandardButton.Yes: return
            listening=self.app.voice_input.running
            self.app.voice_input.stop(); self.app.config.save(values); self.app.refresh_config()
            if self.app.config.get('voice_mode')=='continua' and (listening or self.app.config.get('voice_background_listening')):
                self.app.queue_continuous_listening()
            if 'remote_block_all' in values and values['remote_block_all']: self.app.local_remote.stop()
            self.show_message('Configuración guardada. Los modelos y la voz usarán estos valores en la siguiente operación.')
        except VictorError as exc: self.show_message(str(exc))
        except (ValueError,TypeError): self.show_message('Revisa los números y las listas JSON.')
        except Exception:
            import logging; logging.getLogger('victor.gui').exception('settings save failed'); self.show_message('No pude guardar la configuración. Revisa el registro local.')
    def show_message(self,text):
        self.error.setText(text)
        for w in self.messages.values(): w.setText(text)


class Sections:
    def __init__(self,app):
        self.app,self.pages,self.outputs=app,{},{}
        self.build_history(); self.build_memory(); self.build_windows(); self.build_files(); self.build_vision(); self.build_internet()
        self.build_spotify(); self.build_google(); self.build_mail(); self.build_whatsapp(); self.build_telegram(); self.build_remote()
        self.settings=SettingsManager(app); self.pages.update(self.settings.pages); app.settings=self.settings
        from victor.gui.maintenance import MaintenancePanel
        app.maintenance=MaintenancePanel(app)
        page=Page('Diagnóstico y auditoría','Comprueba tus conexiones y revisa las acciones ejecutadas.','Seguridad / diagnóstico')
        page.content.addWidget(app.maintenance); self.pages['diagnostics']=page
        self.timer=QTimer(app); self.timer.timeout.connect(self.refresh_connections); self.timer.start(1000)

    def task(self,name,args,output=None):
        if output: self.outputs[name]=output; output.setPlainText('Procesando…')
        self.app.run_tool(name,args)

    def output(self,layout):
        w=QPlainTextEdit(); w.setReadOnly(True); w.setPlaceholderText('Los resultados reales aparecerán aquí.'); w.setMinimumHeight(130); layout.addWidget(w); return w

    def build_history(self):
        a=self.app; page=Page('Historial de conversaciones','Encuentra y retoma tus conversaciones guardadas localmente.','Biblioteca / chats')
        left,ll=card(''); row=QHBoxLayout(); a.history_search=QLineEdit(); a.history_search.setPlaceholderText('Buscar conversaciones…')
        a.history_search.returnPressed.connect(a.refresh_history); a.history_search.textChanged.connect(a.refresh_history)
        row.addWidget(a.history_search,1); row.addWidget(button('Nueva',self.new_chat,'plus',True)); ll.addLayout(row)
        a.history_list=QListWidget(); a.history_list.itemClicked.connect(self.preview_history); ll.addWidget(a.history_list)
        right,rl=card('Vista previa de conversación'); self.history_heading=label('Selecciona una conversación','cardTitle'); rl.addWidget(self.history_heading)
        self.history_preview=self.output(rl); row=QHBoxLayout(); row.addStretch(); row.addWidget(button('Eliminar',self.delete_chat,'trash',danger=True)); row.addWidget(button('Continuar conversación',self.continue_chat,'file',True)); rl.addLayout(row)
        page.content.addWidget(Columns(left,right,weights=[4,5])); self.pages['history']=page

    def preview_history(self,item):
        rows=self.app.core.history.messages(item.data(Qt.ItemDataRole.UserRole)); self.history_heading.setText(item.text())
        self.history_preview.setPlainText('\n\n'.join(('TÚ' if r['role']=='user' else self.app.config.get('name'))+'\n'+r['content'] for r in rows))
    def continue_chat(self):
        item=self.app.history_list.currentItem()
        if item: self.app.load_conversation(item.data(Qt.ItemDataRole.UserRole)); self.app.navigate('home')
    def new_chat(self): self.app.new_conversation(); self.app.navigate('home')
    def delete_chat(self):
        item=self.app.history_list.currentItem()
        if not item or self.app.core.busy.is_set(): return
        if self.app.config.get('action_confirmations') and QMessageBox.question(self.app,'Eliminar conversación','¿Eliminar esta conversación local?')!=QMessageBox.StandardButton.Yes: return
        cid=item.data(Qt.ItemDataRole.UserRole); self.app.core.history.delete(cid)
        if cid==self.app.conversation_id: self.app.new_conversation()
        else: self.app.refresh_history()
        self.history_preview.clear()

    def build_memory(self):
        a=self.app; page=Page('Memoria','Información personal que VICTOR puede consultar cuando la necesitas.','Conocimiento / local')
        left,ll=card('Añadir un recuerdo'); ll.addWidget(label('Clave del recuerdo')); a.memory_key=QLineEdit(); a.memory_key.setPlaceholderText('ej. nombre_proyecto'); ll.addWidget(a.memory_key)
        ll.addWidget(label('Contenido')); a.memory_value=QPlainTextEdit(); a.memory_value.setPlaceholderText('Describe el dato que VICTOR debe recordar.'); a.memory_value.setFixedHeight(100); ll.addWidget(a.memory_value)
        ll.addWidget(button('Guardar recuerdo',lambda:self.task('remember',{'key':a.memory_key.text(),'value':a.memory_value.toPlainText()}),'plus',True),alignment=Qt.AlignmentFlag.AlignLeft)
        ll.addWidget(notice('Los recuerdos se almacenan en este PC y se conservan entre sesiones.')); ll.addStretch()
        right,rl=card('Recuerdos guardados'); a.memory_search=QLineEdit(); a.memory_search.setPlaceholderText('Buscar recuerdos por clave o contenido'); a.memory_search.textChanged.connect(a.refresh_memories); rl.addWidget(a.memory_search)
        a.memory_list=QListWidget(); rl.addWidget(a.memory_list); rl.addWidget(button('Eliminar seleccionado',a.forget_memory,'trash',danger=True),alignment=Qt.AlignmentFlag.AlignRight)
        page.content.addWidget(Columns(left,right,weights=[4,5])); self.pages['memory']=page

    def tile(self,title,detail,glyph,callback):
        w=ActionTile();w.setObjectName('normal');w.clicked.connect(callback);w.setAccessibleName(title);w.setToolTip(title+' · '+detail)
        row=QHBoxLayout(w);row.setContentsMargins(12,12,12,12)
        mark=QLabel();mark.setPixmap(icon(glyph).pixmap(18,18));row.addWidget(mark)
        texts=QVBoxLayout();texts.addWidget(label(title,'cardTitle'));texts.addWidget(label(detail));row.addLayout(texts,1)
        for child in w.findChildren(QLabel):child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        return w

    def build_windows(self):
        page=Page('Aplicaciones y Windows','Controla aplicaciones y consulta el estado de tu equipo.','Herramientas / sistema')
        top,tl=card('Acciones rápidas'); self.app_query=QLineEdit(); self.app_query.setPlaceholderText('Nombre de aplicación registrada o URL…')
        tiles=[('Abrir aplicación','Busca una aplicación instalada.','grid',lambda:self.app_operation('open_application')),
            ('Cerrar aplicación','Solicita autorización.','close',lambda:self.app_operation('close_application')),
            ('Abrir navegador','Sitio web o URL.','globe',lambda:self.app_operation('open_url')),
            ('Configuración','Abre ajustes de Windows.','settings',lambda:self.task('open_settings',{},self.windows_output))]
        tl.addWidget(ResponsiveButtons([self.tile(*t) for t in tiles],columns=4,cell_width=170)); row=QHBoxLayout(); row.addWidget(self.app_query,1); row.addWidget(button('Abrir',lambda:self.app_operation('open_application'),'grid',True)); tl.addLayout(row); page.content.addWidget(top)
        left,ll=card('Rendimiento actual'); self.cpu=label('CPU: —'); self.ram=label('RAM: —'); ll.addWidget(self.cpu); ll.addWidget(self.ram)
        ll.addWidget(ResponsiveButtons([button(text,lambda:self.task('get_system_info',{},self.windows_output),'cpu') for text in ('Consultar equipo','Almacenamiento','Ver procesos')],columns=3,cell_width=150)); self.windows_output=self.output(ll)
        right,rl=card('Sonido y comandos permitidos'); rl.addWidget(label('Volumen del sistema')); self.system_volume=QSlider(Qt.Orientation.Horizontal); self.system_volume.setRange(0,100); self.system_volume.setValue(50); rl.addWidget(self.system_volume)
        self.system_volume.sliderReleased.connect(lambda:self.task('control_volume',{'level':self.system_volume.value()},self.windows_output))
        row=QHBoxLayout()
        for text,act in [('Bajar','down'),('Subir','up'),('Silenciar','mute')]: row.addWidget(button(text,lambda checked=False,act=act:self.task('adjust_volume',{'action':act},self.windows_output),'volume'))
        rl.addLayout(row); rl.addWidget(label('Diagnóstico permitido')); self.diagnostic=QComboBox(); self.diagnostic.addItems(['systeminfo','ipconfig','whoami','hostname']); rl.addWidget(self.diagnostic)
        rl.addWidget(button('Ejecutar diagnóstico',lambda:self.task('run_terminal',{'command':self.diagnostic.currentText()},self.windows_output),'terminal',True))
        rl.addWidget(notice('Solo la lista permitida, sin argumentos. Las confirmaciones dependen de tu política en Seguridad.')); rl.addStretch()
        page.content.addWidget(Columns(left,right)); page.finish(); self.pages['windows']=page
    def app_operation(self,name):
        value=self.app_query.text().strip()
        if name=='open_url': value=value or 'https://www.google.com'; args={'url':value}
        elif value.startswith(('http://','https://')) and name=='open_application': name='open_url'; args={'url':value}
        else: args={'name':value}
        self.task(name,args,self.windows_output)

    def build_files(self):
        page=Page('Archivos y carpetas','Operaciones locales dentro de las ubicaciones autorizadas.','Herramientas / archivos')
        top,tl=card('Acciones disponibles'); tiles=[]
        self.file_operation=QComboBox()
        operations=[('Abrir','Archivo o carpeta','folder','open_file'),('Listar','Contenido de carpeta','list','list_files'),('Crear carpeta','Nueva carpeta','plus','create_folder'),('Crear texto','Archivo .txt','file','create_file'),
                    ('Copiar','Duplicar archivo','copy','copy_file'),('Mover','Cambiar ubicación','arrow','move_file'),('Renombrar','Cambiar nombre','edit','rename_file'),('Papelera','Enviar archivo','trash','delete_file')]
        for i,(title,detail,glyph,name) in enumerate(operations):
            self.file_operation.addItem(title,name);tiles.append(self.tile(title,detail,glyph,lambda checked=False,n=name:self.select_file(n)))
        tl.addWidget(ResponsiveButtons(tiles,columns=4,cell_width=150));page.content.addWidget(top)
        left,ll=card('Preparar operación'); ll.addWidget(self.file_operation); self.file_source=QLineEdit(); self.file_destination=QLineEdit(); self.file_text=QPlainTextEdit(); self.file_text.setFixedHeight(80)
        for text,w in [('Ruta del archivo / carpeta',self.file_source),('Destino completo o nombre nuevo',self.file_destination),('Contenido (crear texto)',self.file_text)]: ll.addWidget(label(text)); ll.addWidget(w)
        row=QHBoxLayout(); row.addWidget(button('Seleccionar ruta',self.choose_file,'folder')); row.addStretch(); row.addWidget(button('Continuar',self.execute_file,'arrow',True)); ll.addLayout(row)
        right,rl=card('Protección de archivos'); self.folder_notice=notice('\n'.join(self.app.config.get('allowed_folders'))); rl.addWidget(self.folder_notice)
        rl.addWidget(label('Sin sobrescritura · Eliminación reversible · Confirmación de acciones sensibles'))
        self.files_output=self.output(rl); page.content.addWidget(Columns(left,right)); page.finish(); self.pages['files']=page
    def select_file(self,name): self.file_operation.setCurrentIndex(self.file_operation.findData(name)); self.file_source.setFocus()
    def choose_file(self):
        if self.file_operation.currentData() in ('open_file','list_files','create_folder'):
            path=QFileDialog.getExistingDirectory(self.app,'Selecciona una carpeta')
        else: path,_=QFileDialog.getOpenFileName(self.app,'Selecciona un archivo')
        if path: self.file_source.setText(path)
    def execute_file(self):
        name=self.file_operation.currentData(); src=self.file_source.text(); dst=self.file_destination.text()
        args={'source':src,'destination':dst} if name in ('copy_file','move_file') else {'source':src,'name':dst} if name=='rename_file' else {'path':src}
        if name=='create_file': args['text']=self.file_text.toPlainText()
        self.task(name,args,self.files_output)

    def build_vision(self):
        page=Page('Pantalla y visión','Captura la pantalla e interpreta lo que aparece en tu equipo.','Herramientas / pantalla')
        left,ll=card('Vista previa de captura'); self.capture_preview=label('Todavía no hay una captura.'); self.capture_preview.setAlignment(Qt.AlignmentFlag.AlignCenter); self.capture_preview.setMinimumHeight(160); ll.addWidget(self.capture_preview)
        row=QHBoxLayout(); row.addWidget(button('Pantalla completa',lambda:self.task('take_screenshot',{'region':None},self.vision_output),'screen',True)); row.addWidget(button('Capturar región',self.capture_region,'fullscreen')); row.addWidget(button('Ventana activa',lambda:self.task('active_window',{},self.vision_output),'screen')); ll.addLayout(row)
        self.vision_output=self.output(ll)
        right,rl=card('Acciones rápidas'); self.vision_question=QLineEdit(); self.vision_question.setPlaceholderText('¿Qué hay en mi pantalla?'); rl.addWidget(self.vision_question)
        for text in ('¿Qué hay en mi pantalla?','Lee el texto que aparece','¿Qué error aparece?'):
            rl.addWidget(button(text,lambda checked=False,text=text:self.analyze(text),'search'))
        rl.addWidget(label('Región manual · x / y / ancho / alto')); row=QHBoxLayout(); self.region=[]
        for default in (0,0,640,480):
            w=QSpinBox(); w.setRange(-32000,32000); w.setValue(default); self.region.append(w); row.addWidget(w)
        rl.addLayout(row); rl.addWidget(button('Analizar captura',lambda:self.analyze(self.vision_question.text() or '¿Qué hay en mi pantalla?'),'screen',True))
        rl.addWidget(notice('El análisis transmite la captura al proveedor configurado tras tu aprobación.')); rl.addStretch()
        page.content.addWidget(Columns(left,right)); page.finish(); self.pages['vision']=page
    def capture_region(self): self.task('take_screenshot',{'region':[w.value() for w in self.region]},self.vision_output)
    def analyze(self,text): self.task('analyze_screen',{'question':text,'region':None},self.vision_output)

    def build_internet(self):
        page=Page('Internet y navegación','Busca información actual, consulta fuentes y abre páginas.','Herramientas / internet')
        left,ll=card('Buscar en Internet'); self.web_query=QLineEdit(); self.web_query.setPlaceholderText('Noticias, información o consulta…'); ll.addWidget(self.web_query)
        self.web_query.returnPressed.connect(lambda:self.task('search_web',{'query':self.web_query.text()},self.web_output))
        ll.addWidget(button('Buscar en la web',lambda:self.task('search_web',{'query':self.web_query.text()},self.web_output),'search',True),alignment=Qt.AlignmentFlag.AlignLeft)
        self.web_results=QListWidget(); self.web_results.itemDoubleClicked.connect(lambda item:self.task('open_url',{'url':item.data(Qt.ItemDataRole.UserRole)},self.web_output)); ll.addWidget(self.web_results)
        self.web_output=self.output(ll)
        right,rl=card('Abrir en el navegador'); self.url=QLineEdit(); self.url.setPlaceholderText('https://…'); rl.addWidget(self.url); rl.addWidget(button('Abrir enlace',lambda:self.task('open_url',{'url':self.url.text()},self.web_output),'globe',True))
        rl.addWidget(label('YouTube')); self.youtube=QLineEdit(); self.youtube.setPlaceholderText('Busca un vídeo'); rl.addWidget(self.youtube)
        rl.addWidget(button('Reproducir primer resultado',lambda:self.task('youtube_play_first',{'query':self.youtube.text()},self.web_output),'play'))
        rl.addWidget(notice('Haz doble clic en una fuente para abrirla. Los errores de lectura se muestran con el resultado.')); rl.addStretch()
        page.content.addWidget(Columns(left,right)); page.finish(); self.pages['internet']=page

    def build_spotify(self):
        from victor.gui.spotify_embed import SpotifyEmbed
        page=SpotifyPage()
        page.content.addWidget(label('CONEXIONES / SPOTIFY','caption'))
        header=QHBoxLayout();page.title=label('Spotify','sectionTitle');header.addWidget(page.title,1)
        header.addWidget(button('Conectar Spotify',self.app.connect_spotify,'link'));page.content.addLayout(header)
        self.spotify_now_card,ll=card(None);ll.setContentsMargins(16,16,16,16);ll.setSpacing(12)
        heading=QHBoxLayout();heading.addWidget(label('Reproduciendo ahora','cardTitle'),1)
        self.spotify_status=label('Sin reproducción');heading.addWidget(self.spotify_status);ll.addLayout(heading)
        artwork=QWidget();artwork.setMaximumWidth(240);art=QVBoxLayout(artwork);art.setContentsMargins(0,0,0,0)
        self.spotify_cover=CoverArt();art.addWidget(self.spotify_cover,alignment=Qt.AlignmentFlag.AlignTop)
        controls=QWidget();cl=QVBoxLayout(controls);cl.setContentsMargins(0,0,0,0);cl.setSpacing(8)
        self.spotify_title=label('Elige una canción en tu biblioteca.','cardTitle');cl.addWidget(self.spotify_title)
        self.spotify_artist=label('');cl.addWidget(self.spotify_artist)
        self.spotify_play=button('Reproducir / Pausar',lambda:self.app.player.action('toggle'),'play')
        cl.addWidget(ResponsiveButtons([
            button('Anterior',lambda:self.app.player.action('spotify_previous'),'previous'),self.spotify_play,
            button('Siguiente',lambda:self.app.player.action('spotify_next'),'next')],columns=3,cell_width=104))
        cl.addWidget(label('Volumen Spotify'));self.spotify_volume=QSlider(Qt.Orientation.Horizontal)
        self.spotify_volume.setRange(0,100);self.spotify_volume.setAccessibleName('Volumen Spotify')
        self.spotify_volume.valueChanged.connect(lambda value:self.app.player.volume.setValue(value))
        self.spotify_volume.sliderReleased.connect(lambda:self.app.player.flush_volume());cl.addWidget(self.spotify_volume)
        cl.addWidget(label('Posición de reproducción'));self.spotify_position=QSlider(Qt.Orientation.Horizontal)
        self.spotify_position.setRange(0,0);self.spotify_position.setAccessibleName('Posición de reproducción')
        self.spotify_position.sliderReleased.connect(lambda:self.app.spotify_command('spotify_seek',{'position':self.spotify_position.value()}));cl.addWidget(self.spotify_position)
        cl.addWidget(button('Mostrar / ocultar mini reproductor',self.toggle_player,'screen'))
        self.spotify_now=Columns(artwork,controls,weights=[2,3],breakpoint=0);ll.addWidget(self.spotify_now)
        from PySide6.QtWidgets import QSizePolicy
        for text in (self.spotify_title,self.spotify_artist):
            text.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
        self.spotify_status.setWordWrap(False);self.spotify_status.setMinimumWidth(80);self.spotify_status.setMaximumWidth(200)
        left=QWidget();left_layout=QVBoxLayout(left);left_layout.setContentsMargins(0,0,0,0)
        left_layout.addWidget(self.spotify_now_card);left_layout.addStretch(1)
        self.spotify_embed=SpotifyEmbed(self.app);self.spotify_embed.setMinimumHeight(500)
        self.spotify_columns=Columns(left,self.spotify_embed,breakpoint=1100)
        page.content.addWidget(self.spotify_columns,1)
        self.pages['spotify']=page

    def toggle_player(self):
        player=self.app.player;player.dismissed=not player.dismissed
        if player.dismissed:player.hide()
        else:player.update_state(player.state)

    def build_google(self):
        a=self.app; page=Page('Tu espacio Google','Agenda, correo y archivos, sin información técnica duplicada.','Conexiones / google',(button('Conectar Google',a.connect_google,'link'),))
        self.google_tabs=QTabWidget();page.content.addWidget(self.google_tabs)
        self.google_output=StatusText('Consulta tu agenda o tus mensajes.');page.content.addWidget(self.google_output)
        calendar,ll=card('Próximos eventos');self.events=ServiceList('googlecalendar');ll.addWidget(self.events)
        self.events.itemDoubleClicked.connect(lambda item:self.open_service_item(item))
        ll.addWidget(button('Actualizar agenda',lambda:self.task('google_events',{},self.google_output),'refresh',True))
        gmail,gl=card('Bandeja de entrada · Sin leer');self.mail_results=ServiceList('gmail');gl.addWidget(self.mail_results)
        self.mail_results.itemDoubleClicked.connect(lambda item:self.open_service_item(item))
        row=QHBoxLayout();row.addWidget(button('Actualizar correos',lambda:self.task('google_unread',{},self.google_output),'refresh'))
        row.addWidget(button('Redactar correo',lambda:a.navigate('mail'),'send',True));gl.addLayout(row)
        drive,dl=card('Tus archivos');self.drive_query=QLineEdit();self.drive_query.setPlaceholderText('Busca por nombre de archivo…');dl.addWidget(self.drive_query)
        search=lambda:self.task('google_drive_search',{'query':self.drive_query.text()},self.drive_output)
        self.drive_query.returnPressed.connect(search);dl.addWidget(button('Buscar en Drive',search,'search',True))
        self.drive_results=ServiceList('googledrive');dl.addWidget(self.drive_results)
        self.drive_results.itemDoubleClicked.connect(lambda item:self.open_service_item(item))
        self.drive_output=StatusText('Doble clic en un archivo para abrirlo.');dl.addWidget(self.drive_output)
        for name,logo,widget in [('Calendario','googlecalendar',calendar),('Gmail','gmail',gmail),('Drive','googledrive',drive)]:
            self.google_tabs.addTab(widget,brand_icon(logo),name)
        page.finish();self.pages['google']=page

    def open_service_item(self,item):
        url=item.data(Qt.ItemDataRole.UserRole)
        if url:self.task('open_url',{'url':url})

    def build_mail(self):
        page=Page('Enviar un correo','Escribe el destinatario, el asunto y el mensaje.','Conexiones / gmail',(button('Volver a Google',lambda:self.app.navigate('google'),'mail'),))
        c,l=card('Destinatario y contenido'); self.mail_to=QLineEdit(); self.mail_subject=QLineEdit(); self.mail_body=QPlainTextEdit(); self.mail_body.setMinimumHeight(160)
        for text,w in [('Destinatario',self.mail_to),('Asunto',self.mail_subject),('Mensaje',self.mail_body)]: l.addWidget(label(text)); l.addWidget(w)
        l.addWidget(notice('El botón Enviar manda un correo real a la cuenta indicada. Las confirmaciones se controlan en Seguridad.'))
        l.addWidget(button('Enviar correo',lambda:self.task('google_send_email',{'to':self.mail_to.text(),'subject':self.mail_subject.text(),'body':self.mail_body.toPlainText()},self.mail_output),'send',True),alignment=Qt.AlignmentFlag.AlignRight)
        self.mail_output=self.output(l); page.content.addWidget(c); page.finish(); self.pages['mail']=page

    def build_whatsapp(self):
        from victor.gui.whatsapp_embed import WhatsAppEmbed
        page=SpotifyPage()
        page.content.addWidget(label('CONEXIONES / WHATSAPP','caption'))
        header=QHBoxLayout();page.title=label('WhatsApp','sectionTitle');header.addWidget(page.title,1)
        header.addWidget(button('Conectar WhatsApp',lambda:self.whatsapp_embed.start(),'link'));page.content.addLayout(header)
        self.whatsapp_embed=WhatsAppEmbed(self.app);self.whatsapp_embed.setMinimumHeight(500)
        self.whatsapp_embed.snapshot_changed.connect(self.app.whatsapp_recent.update_snapshot)
        page.content.addWidget(self.whatsapp_embed,1)
        help_text=label('WhatsApp Web integrado · Tus chats, contactos y archivos se manejan aquí. La sesión se conserva al cerrar VICTOR.')
        page.content.addWidget(help_text);self.pages['whatsapp']=page

    def build_telegram(self):
        a=self.app; page=Page('Telegram','Habla con VICTOR desde tu bot privado y autoriza dispositivos.','Conexiones / telegram')
        left,ll=card('Control del bot'); self.telegram_status=label('Detenido'); ll.addWidget(self.telegram_status)
        row=QHBoxLayout(); row.addWidget(button('Iniciar / detener',a.toggle_telegram,'stop')); row.addWidget(button('Pausar / reanudar',lambda:a.telegram.pause(not a.config.get('telegram_paused')),'pause')); ll.addLayout(row)
        ll.addWidget(label('Emparejar un nuevo usuario','cardTitle')); ll.addWidget(button('Generar código',a.pair_telegram,'link',True)); self.telegram_pair=label('Código de un uso; caduca en 120 segundos.'); ll.addWidget(self.telegram_pair); ll.addStretch()
        right,rl=card('Usuarios autorizados'); self.telegram_users=QListWidget(); self.telegram_users.setMinimumHeight(150);rl.addWidget(self.telegram_users)
        rl.addWidget(button('Quitar usuario seleccionado',self.remove_telegram_user,'trash',danger=True))
        rl.addWidget(button('Administrar usuarios y permisos',lambda:a.navigate('security'),'shield'))
        rl.addWidget(notice('Configura TELEGRAM_BOT_TOKEN en .env. Usa un chat privado con tu bot. Las órdenes pasan por los mismos permisos que en el PC.')); rl.addStretch()
        page.content.addWidget(Columns(left,right)); page.finish(); self.pages['telegram']=page

    def remove_telegram_user(self):
        item=self.telegram_users.currentItem()
        if not item:return
        user_id=item.data(Qt.ItemDataRole.UserRole)
        accepted=not self.app.config.get('action_confirmations') or QMessageBox.question(self.app,'Revocar acceso',f'¿Quitar la autorización Telegram del usuario {user_id}?')==QMessageBox.StandardButton.Yes
        import logging
        logging.getLogger('victor.security').info('GUI revocar usuario Telegram confirmed=%s',accepted)
        if accepted:
            ids=[value for value in self.app.config.get('telegram_allowed_ids') if value!=user_id]
            self.app.config.save({'telegram_allowed_ids':ids})
            self.settings.fields['telegram_allowed_ids'].setPlainText(json.dumps(ids))
            self.refresh_connections()

    def build_remote(self):
        a=self.app; page=Page('Control PC desde el celular','Acceso remoto HTTPS, emparejamiento QR y permisos por sesión.','Conexiones / acceso remoto')
        left,ll=card('Servidor remoto'); self.remote_status=label('Servidor detenido'); ll.addWidget(self.remote_status)
        ll.addWidget(label('Dirección de conexión')); self.remote_address=QLineEdit(); self.remote_address.setReadOnly(True); ll.addWidget(self.remote_address)
        row=QHBoxLayout(); row.addWidget(button('Iniciar / detener servidor',a.toggle_local_remote,'stop')); row.addWidget(button('Mostrar QR',a.show_local_qr,'screen')); ll.addLayout(row)
        ll.addWidget(label('Permisos de sesión','cardTitle')); ll.addWidget(notice('El QR autoriza el dispositivo. El streaming continúa mientras la sesión esté conectada; la política de acciones se administra en Seguridad.'))
        ll.addWidget(button('Detener todas las sesiones',a.local_remote.stop,'stop',danger=True)); ll.addStretch()
        right,rl=card('Emparejar celular'); a.qr_image=QLabel(); a.qr_image.setMinimumHeight(190); a.qr_image.setAlignment(Qt.AlignmentFlag.AlignCenter); rl.addWidget(a.qr_image)
        a.qr_timer=QTimer(a);a.qr_timer.setSingleShot(True);a.qr_timer.timeout.connect(a.qr_image.clear)
        a.integration_info=label('Misma Wi-Fi. Inicia el servidor y genera el QR.'); rl.addWidget(a.integration_info)
        for text in ('1 · Abre el enlace HTTPS de tu PC y acepta su certificado local.','2 · El QR de un uso empareja el dispositivo.','3 · Autoriza compartir pantalla y selecciona la ventana de destino.','4 · Desliza un dedo sobre la imagen; toca para hacer clic; dos dedos para scroll.','5 · Toca un campo y pulsa Teclado si el navegador necesita ese gesto.'):
            rl.addWidget(label(text))
        self.remote_sessions=label('Sesiones activas: 0'); rl.addWidget(self.remote_sessions)
        self.remote_devices=QListWidget();self.remote_devices.setMaximumHeight(100);rl.addWidget(self.remote_devices)
        rl.addWidget(button('Revocar dispositivo seleccionado',self.revoke_device,'stop',danger=True))
        page.content.addWidget(Columns(left,right)); page.finish(); self.pages['remote']=page

    def revoke_device(self):
        item=self.remote_devices.currentItem()
        if item:
            token=item.data(Qt.ItemDataRole.UserRole)
            with self.app.local_remote.lock:
                self.app.local_remote.sessions.pop(token,None);self.app.local_remote.frames.pop(token,None)
            self.refresh_connections()

    def refresh_connections(self):
        a=self.app
        self.remote_status.setText('Servidor activo' if a.local_remote.ready.is_set() else 'Iniciando…' if a.local_remote.running else 'Servidor detenido')
        self.remote_address.setText(f'https://{a.local_remote.address}:{a.local_remote.port}/' if a.local_remote.ready.is_set() else '')
        selected=self.remote_devices.currentItem();selected=selected.data(Qt.ItemDataRole.UserRole) if selected else None
        with a.local_remote.lock:devices=[(token,entry['peer']) for token,entry in a.local_remote.sessions.items()]
        self.remote_sessions.setText('Sesiones activas: '+str(len(devices)));self.remote_devices.clear()
        from PySide6.QtWidgets import QListWidgetItem
        for token,peer in devices:
            item=QListWidgetItem('Celular / LAN · '+peer);item.setData(Qt.ItemDataRole.UserRole,token);self.remote_devices.addItem(item)
            if token==selected:self.remote_devices.setCurrentItem(item)
        self.telegram_status.setText('Bot activo · '+('pausado' if a.config.get('telegram_paused') else 'órdenes habilitadas') if a.telegram.running else 'Bot detenido')
        ids=a.config.get('telegram_allowed_ids')
        shown=[self.telegram_users.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.telegram_users.count())]
        if shown!=ids:
            self.telegram_users.clear()
            for user_id in ids:
                item=QListWidgetItem('Usuario autorizado · '+str(user_id));item.setData(Qt.ItemDataRole.UserRole,user_id);self.telegram_users.addItem(item)
        self.settings.whisper_state.setText(a.maintenance.label.text())
        self.settings.whisper_progress.setVisible(not a.maintenance.bar.isHidden())
        self.settings.whisper_progress.setRange(a.maintenance.bar.minimum(),a.maintenance.bar.maximum());self.settings.whisper_progress.setValue(a.maintenance.bar.value())

    def tool_result(self,name,result):
        out=self.outputs.get(name)
        if out and (not result.get('ok') or name not in ('spotify_search','spotify_collection','spotify_playlists')): out.setPlainText(display_text(result.get('result',{}) if result.get('ok') else result.get('error','La operación falló.')))
        if name.startswith('spotify_'):
            if not result.get('ok'):self.spotify_embed.status.setText(result.get('error','Falló Spotify.'))
            return
        if not result.get('ok'):return
        data=result.get('result')
        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtGui import QPixmap
        if name=='take_screenshot' and isinstance(data,dict):
            pix=QPixmap(data.get('captura','')); self.capture_preview.setPixmap(pix.scaled(640,320,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        if name=='google_events':
            self.events.clear(); rows=data.get('eventos',[])
            for r in rows:self.events.add_card(r['titulo'],friendly_date(r.get('inicio'),r.get('todo_el_dia',False)),r.get('lugar',''),r.get('url'))
            self.google_tabs.setCurrentIndex(0);self.google_output.setPlainText(f'{len(rows)} eventos próximos.' if rows else 'No hay eventos próximos.')
        elif name=='google_unread':
            self.mail_results.clear();rows=data.get('correos_no_leidos',[])
            for r in rows:
                person,address=sender(r.get('remitente',''))
                self.mail_results.add_card(r.get('asunto','Sin asunto'),person+' · '+friendly_date(r.get('fecha')),r.get('resumen',''), 'https://mail.google.com/mail/u/0/#inbox/'+r['thread_id'] if r.get('thread_id') else None)
            self.google_tabs.setCurrentIndex(1);self.google_output.setPlainText(f'{len(rows)} mensajes sin leer · Doble clic para abrir en Gmail.' if rows else 'No tienes mensajes sin leer.')
        elif name=='google_drive_search':
            self.drive_results.clear();rows=data.get('archivos',[])
            for r in rows:self.drive_results.add_card(r.get('name','Sin título'),file_type(r.get('mimeType','')), 'Modificado: '+friendly_date(r['modifiedTime']) if r.get('modifiedTime') else 'Doble clic para abrir',r.get('webViewLink'))
            self.google_tabs.setCurrentIndex(2);self.drive_output.setPlainText(f'{len(rows)} archivos encontrados.' if rows else 'No se encontraron archivos con ese nombre.')
            self.google_output.setPlainText('Drive · Resultados de búsqueda')
        elif name=='search_web':
            self.web_results.clear()
            for r in data.get('fuentes',[]):
                item=QListWidgetItem(r.get('titulo','Sin título')+'\n'+r.get('url',''));item.setData(Qt.ItemDataRole.UserRole,r.get('url'));self.web_results.addItem(item)
        if name in ('remember','forget'): self.app.refresh_memories()

    def spotify_state(self,state):
        state=state or {}
        self.spotify_status.setText('Actualizando Spotify…' if self.app.player.pending else
                                    'Reproduciendo' if state.get('playing') else 'En pausa' if state else 'Sin reproducción')
        self.spotify_title.setText(state.get('name') or 'Elige una canción en tu biblioteca.')
        self.spotify_artist.setText(state.get('artists',''))
        self.spotify_play.setIcon(icon('pause' if state.get('playing') else 'play'))
        self.spotify_play.setAccessibleName('Pausar' if state.get('playing') else 'Reproducir')
        if not self.spotify_position.isSliderDown():
            self.spotify_position.setRange(0,state.get('duration',0));self.spotify_position.setValue(state.get('position',0))
        if not self.spotify_volume.isSliderDown():
            intent=self.app.player.volume_intent
            self.spotify_volume.blockSignals(True)
            self.spotify_volume.setValue(intent['level'] if intent else (state.get('volume') or 0))
            self.spotify_volume.blockSignals(False)
        if getattr(self,'spotify_art_id',None)!=state.get('id'):
            self.spotify_cover.clear();self.spotify_art_id=state.get('id')
        if state.get('art'):
            from PySide6.QtGui import QPixmap
            pix=QPixmap()
            if pix.loadFromData(state['art']):self.spotify_cover.setPixmap(pix)
        if not state:self.spotify_cover.clear()
        self.app.present_spotify(state)


def example_args(schema):
    return {k: p['enum'][0] if 'enum' in p else None if p.get('type')==['array','null'] else
            p.get('minimum',0) if p.get('type')=='integer' else ['ctrl','a'] if p.get('type')=='array' else ''
            for k,p in schema['properties'].items()}
