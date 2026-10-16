"""Ventana Qt. El núcleo existente conserva toda la ejecución y los permisos."""
import json
import logging
import queue
import threading
import time
from datetime import datetime
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QFont, QShortcut, QKeySequence
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QBoxLayout, QGridLayout, QScrollArea, QTabWidget, QListWidget, QListWidgetItem, QLineEdit, QPlainTextEdit, QComboBox, QMessageBox, QStackedWidget, QSizeGrip, QSizePolicy)
from victor.core import VictorCore
from victor.errors import VictorError
from victor.gui.theme import STYLE, LABEL_STYLES, state_style, title_font
from victor.gui.widgets import Bubble, MessageRow, Composer, ListeningWave, ApprovalCard, ApprovalDialog
from victor.gui.panels import SettingsManager
from victor.gui.metrics import MetricsWorker
from victor.voice.input import VoiceInput
from victor.voice.output import VoiceOutput
from victor.security import Risk
from victor.gui.tool_labels import readable_names, friendly_name, confirmation_details
from victor.integrations.telegram_bot import TelegramService
from victor.integrations.local_remote import LocalRemote
from victor.gui.spotify_player import SpotifyMiniPlayer, SpotifyPoller, register_player
from victor.gui.voice_panel import VoicePanel
from victor.gui.widgets import display_text, icon, DashboardDial, ToolWorker, ResponsiveButtons, WindowControl, TransientNotice, WindowTransitions
from victor.auth import create_auth
from victor.gui.desktop_orb import DesktopVoiceOrb
from victor.gui.login import LoginOverlay


class GUIManager(QMainWindow):
    def __init__(self, config, auth=None):
        super().__init__()
        self.config = config
        self.auth = auth or create_auth(config.data_dir)
        self.desktop_orb = DesktopVoiceOrb()
        self.desktop_orb.reposition(config.get('desktop_orb_corner'))
        self.desktop_orb.restore_position(config.get('desktop_orb_position'))
        self.desktop_orb.positionSaved.connect(lambda x,y:self.config.save({'desktop_orb_position':[x,y]}))
        self.events = queue.Queue()
        self.core = VictorCore(config, self.emit)
        self.core.access_check=lambda:self.auth.authenticated
        self.core.registry.access_check=lambda:self.auth.authenticated
        from victor.updates import Updates
        self.updates=Updates(config.root,self.emit);self.update_dialog=None;self.notified_versions=set()
        register_player(self.core)
        from victor.plugins.video import register_video
        register_video(self.core)
        self.confirmation_target = None
        self.voice_view = False
        self.voice_output = VoiceOutput(config, self.emit)
        self.voice_input = VoiceInput(config, self.emit, lambda: (not self.core.busy.is_set() or self.voice_confirmation_active()) and not self.voice_output.busy)
        self.voice_input.can_interrupt = lambda:self.voice_output.busy and not self.closing
        self.voice_input.is_speech_echo = self.voice_output.is_speech_echo
        self.voice_input.capture_handoff = lambda:self.voice_output.last_audio_end
        self.voice_waiting_reply = False
        self.voice_diagnostic_active=False
        self.voice_diagnostic_resume=False
        self.voice_input.confirmation_pending = self.voice_confirmation_active
        self.voice_input.confirmation_context = lambda: self.confirmation_target if self.voice_confirmation_active() else None
        self.voice_background = True
        self.voice_input.background_context = lambda: self.voice_background
        self.telegram = TelegramService(config, self.core, self.voice_input.transcriber, self.emit)
        self.local_remote = LocalRemote(config, self.core, self.emit)
        self.active_remote = None
        self.voice_turn = False
        self.integration_cancel = threading.Event()
        self.auth_thread = None
        self.metrics = MetricsWorker(self.emit)
        self.closing = False
        self.closed_cleanly = False
        from victor.gui.images import ImageController
        self.images=ImageController(self)
        self.approvals = []
        self.approval_dialogs=[]
        self.current_bubble = None
        self.partial = ""
        self.spotify_turn = None
        self.spotify_ack = False
        self.drawer_open = False
        self.presentation = False
        self.setWindowTitle("VICTOR.IA · Asistente personal")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint,True)
        self.resize(1600, 900)
        self.setMinimumSize(420, 640)
        from victor.gui.theme import load_fonts
        load_fonts()
        from victor.gui.typography import install,ui_font
        install();self.setFont(ui_font())
        self.setStyleSheet(STYLE)
        self.window_transitions=WindowTransitions(self)
        self.build()
        self.player = SpotifyMiniPlayer(self)
        self.player.setParent(self.home_side)
        self.home_side_layout.addWidget(self.player)
        self.tool_worker = ToolWorker(self.core, self.emit)
        self.spotify_controls = ToolWorker(self.core, self.emit, "spotify_control_result")
        from victor.integrations.spotify_web import SpotifyWebPlayer
        self.spotify_web = SpotifyWebPlayer(self.core.spotify, self.emit, self.core.registry)
        self.core.spotify.browser = self.spotify_web
        from victor.voice.music_ducking import MusicDucker
        self.voice_output.music_ducker = MusicDucker(lambda:self.spotify_web, self.emit)
        self.spotify_poller = SpotifyPoller(self.core, self.emit)
        self.spotify_poller.access_check=lambda:self.auth.authenticated
        self.set_state("Listo")
        rows = self.core.history.list()
        self.conversation_id = rows[0]["id"] if rows else self.core.history.create()
        self.load_conversation(self.conversation_id)
        self.refresh_history()
        self.refresh_memories()
        self.refresh_config()
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll)
        self.poll_timer.start(50)
        self.metrics.start()
        self.voice_restart_timer=QTimer(self);self.voice_restart_timer.setSingleShot(True)
        self.voice_restart_timer.timeout.connect(self.resume_continuous_listening)
        if self.auth.authenticated:self._start_authenticated()

    def _start_authenticated(self):
        if not self.auth.authenticated or self.closing:return
        config=self.config
        self.updates.start()
        if self.spotify_poller.thread.ident is None:self.spotify_poller.thread.start()
        self.desktop_orb.reposition(config.get('desktop_orb_corner'))
        self.desktop_orb.setVisible(config.get('desktop_orb_enabled'))
        self.orb_btn.setChecked(config.get('desktop_orb_enabled'))
        self.voice_output.preload()
        if config.get('voice_mode')=='continua' and config.get('voice_background_listening'):
            if self.core.spotify.cache.path.exists():QTimer.singleShot(0,self.sections.spotify_embed.start)
            self.voice_restart_timer.start(500)
        self._resume_service(self.telegram,'telegram_enabled')
        self._resume_service(self.local_remote,'local_remote_enabled')
        if self.sections.whatsapp_embed.profile.is_dir():QTimer.singleShot(0,self.sections.whatsapp_embed.start)

    def _resume_service(self,service,key):
        if self.closing or not self.auth.authenticated or not self.config.get(key):return
        if service.running and service.stop_event.is_set():
            QTimer.singleShot(200,lambda:self._resume_service(service,key));return
        if not service.running:service.start()

    def emit(self, kind, payload):
        self.events.put((kind, payload))

    def button(self, text, callback):
        button = QPushButton(text)
        button.clicked.connect(callback)
        return button


    def build(self):
        from victor.gui.panels import card, label, button
        self.outer=QWidget(); self.outer.setObjectName('outer'); self.setCentralWidget(self.outer)
        self.window_stack=QStackedWidget(self.outer)
        outer_box=QVBoxLayout(self.outer); outer_box.setContentsMargins(0,0,0,0); outer_box.addWidget(self.window_stack)
        self.main_app_widget=QWidget(); self.main_app_widget.setObjectName('mainApp')
        self.outer_layout=QHBoxLayout(self.main_app_widget); self.outer_layout.setContentsMargins(24,22,24,22); self.outer_layout.setSpacing(0)
        self.login_overlay=LoginOverlay(self.auth,self)
        self.login_overlay.authenticated.connect(self.on_login_success)
        self.window_stack.addWidget(self.main_app_widget)
        self.window_stack.addWidget(self.login_overlay)
        if not self.auth.authenticated and not self.auth.check_saved_session():
            self.window_stack.setCurrentWidget(self.login_overlay)
        else:
            self.window_stack.setCurrentWidget(self.main_app_widget)
        self.sidebar=QFrame(); self.sidebar.setObjectName('sidebar'); self.sidebar.setFixedWidth(220)
        sl=QVBoxLayout(self.sidebar); sl.setContentsMargins(13,22,13,18); sl.setSpacing(5)
        brand_row=QHBoxLayout(); brand_mark=QLabel(); brand_mark.setPixmap(icon('brand',size=34).pixmap(34,34));brand_row.addWidget(brand_mark)
        brand=QLabel('<b>VICTOR.<span style="color:#83AFFF">IA</span></b>')
        self.brand_text=brand
        brand.setStyleSheet('font-size:18px;'); brand.setMinimumHeight(38); brand_row.addWidget(brand,1); sl.addLayout(brand_row)
        self.brand_caption=label('ASISTENTE\nPERSONAL','caption'); self.brand_caption.setStyleSheet('font-size:9px; color:#9196A5; letter-spacing:2px;');self.brand_caption.setContentsMargins(42,0,0,12); sl.addWidget(self.brand_caption)
        self.nav_buttons={}; self.nav_labels={};self.nav_headers=[]
        headings={'home':'ASISTENTE','history':'TU ESPACIO','windows':'TRABAJO','security':'CONFIGURACIÓN'}
        for key,name,glyph in [('home','Inicio','home'),('voice','Voz','mic'),('history','Historial','clock'),('memory','Memoria','memory'),
            ('windows','Herramientas','grid'),('spotify','Conexiones','link'),('codex','Agentes de programación','terminal'),('security','Seguridad','shield'),('ia','Ajustes','settings')]:
            if key in headings:
                heading=label(headings[key],'caption');heading.setStyleSheet('font-size:9px; color:#9196A5; padding:5px 12px 0px;');sl.addWidget(heading);self.nav_headers.append(heading)
            w=button(name,lambda checked=False,k=key:self.navigate(k),glyph); w.setObjectName('nav'); w.setCheckable(True); w.setMinimumHeight(38)
            self.nav_buttons[key]=w; self.nav_labels[key]=name; sl.addWidget(w)
        sl.addStretch()
        self.lock_nav=button('Bloquear app',self.lock_session,'lock')
        self.lock_nav.setObjectName('lockBtn'); self.lock_nav.setFixedHeight(34); sl.addWidget(self.lock_nav)
        self.sidebar_connection=label('● IA sin verificar','caption'); sl.addWidget(self.sidebar_connection)
        self.outer_layout.addWidget(self.sidebar)
        self.shell=QWidget(); self.shell.setObjectName('shell'); shell=QVBoxLayout(self.shell); shell.setContentsMargins(0,0,0,0); shell.setSpacing(0)
        self.outer_layout.addWidget(self.shell,1)
        self.header=QFrame(); self.header.setObjectName('header'); self.header.setFixedHeight(68)
        header=QHBoxLayout(self.header); header.setContentsMargins(27,12,22,12)
        self.menu=button('',self.toggle_drawer,'list'); self.menu.setObjectName('compact'); self.menu.setFixedWidth(32); header.addWidget(self.menu)
        self.breadcrumb=button('Inicio  │  Inicio',self.section_menu);self.breadcrumb.setStyleSheet('border:0; background:transparent; text-align:left; padding:0;');self.breadcrumb.setToolTip('Elegir una vista de esta sección'); header.addWidget(self.breadcrumb,1)
        self.breadcrumb.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Preferred)
        self.orb_btn=button('Orbe voz',self.toggle_desktop_orb,'wave')
        self.orb_btn.setObjectName('orbBtn'); self.orb_btn.setCheckable(True); self.orb_btn.setChecked(True)
        self.orb_btn.setToolTip('Activar o desactivar orbe flotante en el escritorio')
        header.addWidget(self.orb_btn)
        self.present_button=button('Modo presentación · F11',self.toggle_presentation,'screen'); header.addWidget(self.present_button)
        self.command_input=QLineEdit(); self.command_input.setPlaceholderText('Buscar comando  Ctrl + K'); self.command_input.setFixedWidth(190)
        self.command_input.returnPressed.connect(self.command_from_header); header.addWidget(self.command_input)
        self.lock_header_btn=button('',self.lock_session,'lock'); self.lock_header_btn.setObjectName('lockBtn'); self.lock_header_btn.setFixedWidth(30); self.lock_header_btn.setToolTip('Bloquear sesión'); header.addWidget(self.lock_header_btn)
        self.notice_button=button('',self.show_notices,'list');self.notice_button.setObjectName('compact');self.notice_button.setFixedWidth(30);self.notice_button.setToolTip('Ver avisos recientes');header.addWidget(self.notice_button)
        self.window_controls={}
        for action,callback in [('minimize',self.animate_minimize),('maximize',self.toggle_maximize),('close',self.close)]:
            w=WindowControl(action,callback);self.window_controls[action]=w;header.addWidget(w)
        shell.addWidget(self.header)
        self.header.installEventFilter(self)
        self.presentation_shortcut=QShortcut(QKeySequence('F11'),self); self.presentation_shortcut.activated.connect(self.toggle_presentation)
        self.command_shortcut=QShortcut(QKeySequence('Ctrl+K'),self); self.command_shortcut.activated.connect(self.command_input.setFocus)
        self.pages=QStackedWidget(); shell.addWidget(self.pages,1); self.page_widgets={}
        self.root=QWidget(); self.root.setObjectName('root'); home=QHBoxLayout(self.root); home.setContentsMargins(50,46,50,44); home.setSpacing(18)
        self.home_chat=QWidget(); left=QVBoxLayout(self.home_chat); left.setContentsMargins(0,0,0,0); left.setSpacing(12); home.addWidget(self.home_chat,1)
        conversation=QHBoxLayout(); caption=label('CONVERSACIÓN ACTIVA','caption');caption.setWordWrap(False);caption.setStyleSheet('font-size:9px; color:#9196A5; letter-spacing:1px;');conversation.addWidget(caption)
        self.model_badge=button('',lambda:self.navigate('ia')); self.model_badge.setObjectName('compact');self.model_badge.setFixedHeight(26); conversation.addWidget(self.model_badge); conversation.addStretch()
        self.conversation_caption=caption
        self.summary_title=label('● Listo','badge');self.summary_title.setWordWrap(False); conversation.addWidget(self.summary_title); left.addLayout(conversation)
        self.hero_title=self.summary_title; self.summary_description=label(''); self.summary_description.hide()
        self.status_dot=QLabel(); self.status_dot.hide()
        frame=QFrame(); frame.setObjectName('chatFrame'); fl=QVBoxLayout(frame); fl.setContentsMargins(16,18,16,18)
        self.chat_scroll=QScrollArea(); self.chat_scroll.setWidgetResizable(True); self.chat_body=QWidget(); self.chat_layout=QVBoxLayout(self.chat_body)
        self.chat_layout.setContentsMargins(4,0,4,0); self.chat_layout.setSpacing(18); self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_scroll.setWidget(self.chat_body); fl.addWidget(self.chat_scroll); left.addWidget(frame,1)
        self.quick=QGridLayout(); self.quick.setSpacing(9); self.quick_buttons=[]
        for i,(title,glyph,callback) in enumerate([('Ver pantalla','screen',lambda:self.send('¿Qué hay en mi pantalla?')),('Navegar','globe',lambda:self.run_tool('open_url',{'url':'https://www.google.com'})),
            ('Abrir aplicación','grid',lambda:self.navigate('windows')),('Generar imagen','image',lambda:self.images.request(''))]):
            w=button(title,callback,glyph); w.setMinimumHeight(30);w.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed); self.quick_buttons.append(w); self.quick.addWidget(w,0,i); self.quick.setColumnStretch(i,1)
        left.addLayout(self.quick)
        self.composer_frame=QFrame(); self.composer_frame.setObjectName('composer'); composer=QHBoxLayout(self.composer_frame); composer.setContentsMargins(9,9,9,9); composer.setSpacing(9)
        self.entry=Composer(); self.entry.setPlaceholderText('Escribe un mensaje a VICTOR…'); self.entry.setFixedHeight(36); self.entry.submitted.connect(self.send)
        composer.addWidget(self.entry,1); self.mic=button('',self.toggle_mic,'mic'); self.mic.setObjectName('mic'); self.mic.setFixedSize(46,36)
        self.mic.pressed.connect(self.mic_press); self.mic.released.connect(self.mic_release); self.mic.setToolTip('Micrófono'); composer.addWidget(self.mic)
        self.send_button=button('Enviar',self.send,'send',True); self.send_button.setFixedSize(90,36); composer.addWidget(self.send_button)
        self.stop_button=button('Detener',self.stop,'stop',danger=True); self.stop_button.setFixedHeight(36); composer.addWidget(self.stop_button); left.addWidget(self.composer_frame)
        self.wave=ListeningWave(); self.wave.hide(); left.addWidget(self.wave)
        self.listen_text=label('Micrófono apagado'); self.listen_text.hide(); left.addWidget(self.listen_text)
        self.home_side=QWidget();self.home_side_layout=QVBoxLayout(self.home_side);self.home_side_layout.setContentsMargins(0,0,0,0);self.home_side_layout.setSpacing(12)
        from PySide6.QtWidgets import QLayout
        self.home_side_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.home_side_scroll=QScrollArea();self.home_side_scroll.setWidgetResizable(True);self.home_side_scroll.setFixedWidth(292)
        self.home_side_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff);self.home_side_scroll.setWidget(self.home_side);home.addWidget(self.home_side_scroll)
        metric,ml=card('Rendimiento');ml.setContentsMargins(14,14,14,14);ml.setSpacing(8); row=QHBoxLayout(); row.setSpacing(4)
        self.dials={}; self.metric_values={}; self.metric_cards=[]
        for key,name,color in [('cpu','CPU','#83AFFF'),('ram','RAM','#B3A0E9'),('network','Red','#68CCA4')]:
            dial=DashboardDial(name,color); self.dials[key]=dial; row.addWidget(dial); self.metric_values[key]=QLabel('—')
        self.metric_values['state']=QLabel('Listo'); ml.addLayout(row); self.home_side_layout.addWidget(metric)
        event,el=card('Próximo evento');el.setContentsMargins(14,14,14,14);el.setSpacing(10);event.setMinimumHeight(136)
        event_title=el.takeAt(0).widget();event_row=QHBoxLayout();event_row.addWidget(event_title,1)
        agenda=button('Ver agenda →',lambda:self.navigate('google'));agenda.setObjectName('compact');event_row.addWidget(agenda);el.addLayout(event_row)
        self.proactive=label('Consulta tu calendario para ver el próximo evento.'); self.proactive.setObjectName('proactive'); el.addWidget(self.proactive);self.home_side_layout.addWidget(event)
        activity,al=card('Actividad reciente'); self.activity=label('Memoria local disponible.\nHistorial guardado automáticamente.'); al.addWidget(self.activity); self.home_side_layout.addWidget(activity)
        from victor.gui.whatsapp_panel import WhatsAppRecent
        self.whatsapp_recent=WhatsAppRecent(self);self.home_side_layout.addWidget(self.whatsapp_recent);self.home_side_layout.addStretch()
        self.page_widgets['home']=self.root; self.pages.addWidget(self.root)
        self.voice_panel=VoicePanel(self); self.page_widgets['voice']=self.voice_panel; self.pages.addWidget(self.voice_panel)
        self.build_drawer()
        self.error_label=TransientNotice(); self.error_label.setStyleSheet('color:#F28F95; padding:6px 28px;'); shell.addWidget(self.error_label)
        self.connection_label=label('Sin verificar'); self.connection_label.hide()
        self.grip=QSizeGrip(self);self.grip.resize(14,14)
        self.navigate('home'); self.arrange_metrics()
        from PySide6.QtWidgets import QCompleter
        self.command_map={w.title.text().lower():key for key,w in self.page_widgets.items() if hasattr(w,'title')}
        self.command_map.update({'inicio':'home','voz':'voice','historial':'history','memoria':'memory'})
        completer=QCompleter(list(self.command_map),self);completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive);completer.setFilterMode(Qt.MatchFlag.MatchContains);self.command_input.setCompleter(completer)

    def build_drawer(self):
        from victor.gui.panels import Sections, button
        self.sections=Sections(self)
        for key,w in self.sections.pages.items(): self.page_widgets[key]=w; self.pages.addWidget(w)
        from victor.gui.agents import AgentPage
        self.agent_pages={key:AgentPage(self,key) for key in ('codex','claude')}
        for key,page in self.agent_pages.items():self.page_widgets[key]=page;self.pages.addWidget(page)
        self.drawer=self.sidebar; self.tabs=self.pages
        self.groups={
            'Herramientas':[('windows','Windows'),('files','Archivos'),('vision','Pantalla y visión'),('internet','Internet')],
            'Agentes de programación':[('codex','Codex'),('claude','Claude Code')],
            'Conexiones':[('spotify','Spotify'),('google','Google'),('whatsapp','WhatsApp'),('telegram','Telegram'),('remote','Control remoto')],
            'Seguridad':[('security','Permisos'),('diagnostics','Diagnóstico y auditoría')],
            'Ajustes':[('ia','Proveedores'),('voice_settings','Voz'),('general','Generales'),('personality','Personalidad'),('ollama','Ollama'),('vision_settings','Visión')],
        }
        from PySide6.QtWidgets import QButtonGroup
        self.section_tabs={}
        for group,items in self.groups.items():
            destinations=list(items)+([('mail','Correo')] if group=='Conexiones' else [])
            for key,_ in destinations:
                buttons={};exclusive=QButtonGroup(self.page_widgets[key]);exclusive.setExclusive(True)
                for dest,text in items:
                    b=button(text,lambda checked=False,d=dest:self.navigate(d));b.setObjectName('compact');b.setCheckable(True)
                    exclusive.addButton(b);buttons[dest]=b
                self.section_tabs[key]=buttons
                self.page_widgets[key].content.insertWidget(2,ResponsiveButtons(buttons.values(),columns=len(items),cell_width=145))
        # Estos controles ejecutan consultas: no son pestañas con un estado persistente.
        for key,actions in [('windows',[('Información del equipo',lambda:self.sections.task('get_system_info',{},self.sections.windows_output)),('Diagnóstico',self.sections.diagnostic.setFocus)])]:
            self.page_widgets[key].content.insertWidget(3,ResponsiveButtons([button(text,callback) for text,callback in actions],columns=len(actions),cell_width=150))

    def navigate(self,key):
        if key not in self.page_widgets: return
        self.current_page=key
        self.pages.setCurrentWidget(self.page_widgets[key]); self.voice_view=key=='voice'
        owners={'claude':'codex','files':'windows','vision':'windows','internet':'windows','google':'spotify','whatsapp':'spotify','telegram':'spotify','remote':'spotify','mail':'spotify',
                'diagnostics':'security','voice_settings':'ia','general':'ia','personality':'ia','ollama':'ia','vision_settings':'ia'}
        owner=owners.get(key,key)
        for k,b in self.nav_buttons.items(): b.setChecked(k==owner)
        selected='google' if key=='mail' else key
        for buttons in self.section_tabs.values():
            for destination,widget in buttons.items():widget.setChecked(destination==selected)
        if hasattr(self,'voice_panel'):self.voice_panel.sync_settings()
        names={'codex':'Codex','claude':'Claude Code','home':'Inicio','voice':'Voz','windows':'Windows','files':'Archivos y carpetas','vision':'Pantalla y visión','internet':'Internet',
               'memory':'Memoria','history':'Historial','spotify':'Spotify','google':'Google','whatsapp':'WhatsApp','telegram':'Telegram','remote':'Control remoto · PC',
               'security':'Seguridad','diagnostics':'Diagnóstico','ia':'Inteligencia artificial','voice_settings':'Voz','general':'Preferencias',
               'personality':'Personalidad','ollama':'Ollama','vision_settings':'Visión','mail':'Enviar correo'}
        self.breadcrumb.setText(self.nav_labels.get(owner,'Inicio')+'  │  '+names[key])
        if key=='history': self.refresh_history()
        if key=='memory': self.refresh_memories()

    def arrange_metrics(self):
        if not hasattr(self,'home_side'): return
        narrow=self.width()<1000
        self.home_side.setVisible(not narrow and not self.presentation)
        self.home_side_scroll.setVisible(not narrow and not self.presentation)
        self.sidebar.setFixedWidth(64 if narrow else 220)
        self.brand_caption.setVisible(not narrow)
        self.brand_text.setVisible(not narrow)
        self.sidebar_connection.setVisible(not narrow)
        for key,w in self.nav_buttons.items(): w.setText('' if narrow else 'Agentes de\nprogramación' if key=='codex' else self.nav_labels[key]); w.setToolTip(self.nav_labels[key])
        for heading in self.nav_headers:heading.setVisible(not narrow)
        if hasattr(self,'lock_nav'):self.lock_nav.setText('' if narrow else 'Bloquear app')
        self.root.layout().setContentsMargins(16 if narrow else 50,24 if narrow else 46,16 if narrow else 50,20 if narrow else 44)
        for column in range(4): self.quick.setColumnStretch(column,1 if not narrow or column<2 else 0)
        for i,w in enumerate(self.quick_buttons): self.quick.addWidget(w,i//(2 if narrow else 4),i%(2 if narrow else 4))
        compact=self.width()<700
        self.conversation_caption.setVisible(not compact)
        self.send_button.setText('' if compact else 'Enviar');self.send_button.setFixedWidth(40 if compact else 90);self.send_button.setToolTip('Enviar')
        self.mic.setFixedWidth(36 if compact else 46)
        self.command_input.setVisible(self.width()>=800); self.present_button.setVisible(self.width()>=650)
        if hasattr(self,'orb_btn'):self.orb_btn.setVisible(self.width()>=750)
        if hasattr(self,'lock_header_btn'):self.lock_header_btn.setVisible(self.width()>=600)
        self.stop_button.setText('' if compact else 'Detener');self.stop_button.setToolTip('Detener')

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self.arrange_metrics()
        if hasattr(self,'grip'):self.grip.move(self.width()-18,self.height()-18)

    def eventFilter(self,watched,event):
        from PySide6.QtCore import QEvent
        if watched is getattr(self,'header',None):
            if event.type()==QEvent.Type.MouseButtonDblClick and event.button()==Qt.MouseButton.LeftButton:self.toggle_maximize();return True
            if event.type()==QEvent.Type.MouseButtonPress and event.button()==Qt.MouseButton.LeftButton:
                if self.windowHandle():self.windowHandle().startSystemMove();return True
        return super().eventFilter(watched,event)

    def layout_drawer(self): self.arrange_metrics()

    def toggle_drawer(self,tab=None):
        if tab is not None:
            self.navigate({0:'history',1:'memory',2:'ia',3:'spotify',4:'voice',5:'diagnostics'}.get(tab,'home'))
        else:
            self.drawer_open=not self.sidebar.isVisible(); self.sidebar.setVisible(self.drawer_open)

    def quick_open(self): self.navigate('windows')

    def show_voice(self,enabled): self.navigate('voice' if enabled else 'home')

    def on_login_success(self):
        if not self.auth.authenticated:return
        self.window_stack.setCurrentWidget(self.main_app_widget)
        self.arrange_metrics()
        self._start_authenticated()

    def lock_session(self):
        self.auth.lock_session()
        admin=getattr(self.settings,'admin_dialog',None)
        if admin:admin.table.setRowCount(0);admin.close()
        if self.update_dialog:self.update_dialog.close()
        self.voice_restart_timer.stop();self.stop()
        self.telegram.stop();self.local_remote.stop()
        self.sections.whatsapp_embed.stop();self.sections.spotify_embed.stop()
        self.desktop_orb.reset();self.desktop_orb.hide()
        self.login_overlay.refresh_mode()
        self.window_stack.setCurrentWidget(self.login_overlay)

    def toggle_desktop_orb(self):
        if not self.auth.authenticated:return
        if not hasattr(self, 'desktop_orb'):
            return
        if self.desktop_orb.isVisible():
            self.desktop_orb.hide()
            if hasattr(self, 'orb_btn'):
                self.orb_btn.setChecked(False)
        else:
            self.desktop_orb.reposition()
            self.desktop_orb.show()
            if hasattr(self, 'orb_btn'):
                self.orb_btn.setChecked(True)
        self.config.save({'desktop_orb_enabled':self.desktop_orb.isVisible()})
        if 'desktop_orb_enabled' in self.settings.fields:self.settings.fields['desktop_orb_enabled'].setChecked(self.desktop_orb.isVisible())

    def toggle_maximize(self):self.window_transitions.start('restore' if self.isMaximized() else 'maximize')

    def animate_minimize(self):self.window_transitions.start('minimize')

    def animate_restore(self):
        if not self.closing and not self.isMinimized() and not self.window_transitions.running:self.window_transitions.start('restore_minimized')

    def command_from_header(self):
        text=self.command_input.text().strip()
        if text.lower() in self.command_map:self.navigate(self.command_map[text.lower()]);self.command_input.clear()
        elif text: self.navigate('home'); self.send(text); self.command_input.clear()

    def show_notices(self):
        from PySide6.QtWidgets import QDialog
        dialog=QDialog(self);dialog.setWindowTitle('Avisos recientes');dialog.resize(620,360)
        layout=QVBoxLayout(dialog);text=QPlainTextEdit();text.setReadOnly(True)
        text.setPlainText('\n\n'.join(reversed(self.error_label.history)) or 'No hay avisos recientes.');layout.addWidget(text)
        dialog.exec()

    def section_menu(self):
        from PySide6.QtWidgets import QMenu
        menu=QMenu(self)
        for group,items in self.groups.items():
            sub=menu.addMenu(group)
            for key,text in items:sub.addAction(text,lambda k=key:self.navigate(k))
        menu.exec(self.breadcrumb.mapToGlobal(self.breadcrumb.rect().bottomLeft()))

    def run_tool(self,name,args):
        if self.closing or not self.auth.authenticated: return
        if not self.tool_worker.submit(name,args): self.error_label.setText('Hay demasiadas tareas pendientes. Espera o detén la operación.')

    def spotify_command(self,name,args):
        if self.closing or not self.auth.authenticated: return False
        accepted=self.spotify_controls.submit(name,args,coalesce=name=='spotify_volume')
        if not accepted: self.error_label.setText('La cola de Spotify está llena. Espera antes de volver a pulsar.')
        return accepted

    def voice_confirmation_active(self):
        return bool(self.confirmation_target and not self.confirmation_target.done.is_set())

    def listen_approval(self):
        if not self.auth.authenticated:return
        pending = next((card for card in reversed(self.approvals) if not card.request.done.is_set()), None)
        if not pending:
            return
        self.voice_output.stop()
        self.voice_input.stop()
        self.confirmation_target = pending.request
        def begin():
            if self.closing or pending.request.done.is_set() or self.confirmation_target is not pending.request:
                return
            if self.voice_input.running:
                QTimer.singleShot(50, begin)
            else:
                self.voice_input.start()
                self.voice_input.conversation_until = time.monotonic()+30
        begin()
        self.voice_panel.response.setText("Revisa la acción y sus parámetros. Di sí o confirmar para autorizar; no o cancelar para rechazar.")

    def show_pending_approval(self):
        dialog=next((d for d in reversed(self.approval_dialogs) if not d.card.request.done.is_set()),None)
        if dialog: dialog.show();dialog.raise_();dialog.activateWindow()
        else: self.error_label.setText('No hay una acción pendiente de autorización.')

    def arm_spoken_approval(self, request):
        """Leer la acción local completa antes de aceptar una autorización humana."""
        from victor.voice.text import speech_text
        details = speech_text(request.details)
        # No truncar una revisión de correo/acción extensa ni admitir remoto.
        if request.origin or len(details) > 6000:
            return False
        self.confirmation_target = request
        instruction = ('Di ejecutar para autorizar, o cancelar para rechazar.' if request.risk == Risk.HIGH
                       else 'Di confirmar para autorizar, o cancelar para rechazar.')
        self.voice_panel.show_response()
        self.voice_panel.response.setText(instruction)
        self.voice_output.speak('Necesito tu confirmación. ' + request.title + '. ' + details + '. ' + instruction, force=True)
        return True

    def handle_voice_text(self, text, confirmation=None):
        if confirmation is not None and confirmation is not self.confirmation_target:
            return
        if confirmation is None and not self.voice_confirmation_active():
            from victor.voice.wakeword import wake_match, extract_command
            if wake_match(text,self.config.get('wake_word')) and not extract_command(text,self.config.get('wake_word')):
                # Una activación aislada nunca es una pregunta al proveedor.
                self.voice_input.conversation_until=time.monotonic()+self.config.get('conversation_window')
                self.handle_event('voice_wake',threading.Event())
                return
        if self.voice_confirmation_active() and confirmation is self.confirmation_target:
            from victor.core import folded
            word = folded(text)
            if word not in ("si", "confirmar", "confirmo", "ejecutar", "no", "cancelar"):
                self.voice_panel.response.setText("No reconocí una confirmación exacta. Di sí, confirmar, no o cancelar.")
                return
            card = next((c for c in self.approvals if c.request is self.confirmation_target), None)
            if card:
                accept = word in ("si", "confirmar", "confirmo", "ejecutar")
                if accept and card.request.risk == Risk.HIGH and word != 'ejecutar':
                    self.voice_panel.response.setText('Para autorizar esta acción di ejecutar. Para rechazar di cancelar.')
                    self.voice_output.speak('Para autorizar esta acción di ejecutar. Para rechazar di cancelar.', force=True)
                    return
                if accept and card.phrase:
                    card.phrase.setText("EJECUTAR")
                card.resolve(accept)
            self.confirmation_target = None
            if self.config.get('voice_mode') != 'continua': self.voice_input.stop()
            return
        self.voice_panel.transcript.setText("Dijiste: " + text)
        self.send(text, voice=True)

    def refresh_config(self):
        self.desktop_orb.reposition(self.config.get('desktop_orb_corner'))
        self.desktop_orb.setVisible(self.auth.authenticated and self.config.get('desktop_orb_enabled'))
        if hasattr(self,'orb_btn'):self.orb_btn.setChecked(self.config.get('desktop_orb_enabled'))
        provider = self.config.get("provider")
        credential_error = ""
        account_status='Error de sesión'
        try:
            account_mode=provider=='OpenAI' and self.config.get('auth_methods').get(provider)=='account'
            ready = account_mode or provider == "Ollama" or bool(self.config.api_key(provider))
            if account_mode:account_status=self.core.ai.accounts[provider].status().split('\n')[-1]
        except VictorError as exc:
            ready=False;credential_error=str(exc)
        self.connection_label.setText(provider + " · " + (account_status if account_mode else "sin verificar" if ready else "Sin conexión a IA"))
        if credential_error:
            self.error_label.setText(credential_error)
        elif not ready:
            self.error_label.setText("Añade tu clave en Ajustes → Inteligencia artificial o selecciona Ollama. Los comandos locales funcionan sin claves.")
        elif self.error_label.text().startswith("Añade tu clave en Ajustes"):
            self.error_label.clear()
        self.setStyleSheet(__import__("victor.gui.theme", fromlist=["theme_style"]).theme_style(self.config.get("theme")))
        from victor.gui.theme import is_light
        light=is_light(self.config.get('theme'))
        self.sections.spotify_embed.apply_theme()
        self.sections.whatsapp_embed.apply_theme()
        self.whatsapp_recent.apply_theme()
        for page in self.agent_pages.values():page.apply_theme()
        for bubble in self.chat_body.findChildren(Bubble):bubble.apply_theme(light)
        for dial in self.dials.values():dial.setProperty('light',light);dial.update()
        self.model_badge.setText((self.config.get('account_models').get(provider) or 'Conecta tu cuenta' if account_mode else self.config.get('models')[provider])+' · '+provider)
        if hasattr(self.settings,'account_panels'):
            for panel in self.settings.account_panels.values():panel.refresh()
            self.settings.model_stack.setVisible(not account_mode)
            for key in ('temperature','max_tokens'):self.settings.fields[key].setEnabled(not account_mode)
        self.sidebar_connection.setText('● '+self.connection_label.text())
        self.sections.folder_notice.setText('\n'.join(self.config.get('allowed_folders')))
        from victor.gui.widgets import brand_icon
        for provider,widget in self.settings.provider_buttons.items():widget.setIcon(brand_icon(provider,light))
        self.settings.refresh_api_keys()
        self.voice_panel.sync_settings()

    def append_message(self, role, text):
        container = MessageRow(role, text)
        from victor.gui.theme import is_light
        container.bubble.apply_theme(is_light(self.config.get('theme')))
        self.chat_layout.addWidget(container)
        self.scroll_bottom()
        return container.bubble

    def scroll_bottom(self):
        QTimer.singleShot(0, lambda: self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum()))

    def toggle_telegram(self):
        enabled = not self.telegram.running
        self.config.save({"telegram_enabled": enabled})
        self.telegram.start() if enabled else self.telegram.stop()
        self.integration_info.setText("Telegram iniciándose…" if enabled else "Telegram detenido.")

    def pair_telegram(self):
        try:
            self.sections.telegram_pair.setText("En tu chat privado con el bot escribe /vincular " + self.telegram.pairing_code() + " · caduca en 120 segundos.")
        except Exception as exc:
            self.error_label.setText(str(exc))

    def remote_service(self, origin):
        return self.local_remote if origin.get("source") == "local_web" else self.telegram

    def toggle_local_remote(self):
        enabled = not self.local_remote.running
        self.config.save({"local_remote_enabled": enabled})
        self.local_remote.start() if enabled else self.local_remote.stop()
        if not enabled:
            self.qr_image.clear()
            self.integration_info.setText("Remoto local detenido.")

    def show_local_qr(self):
        try:
            import io, qrcode
            from PySide6.QtGui import QPixmap
            url = self.local_remote.qr_url()
            data = io.BytesIO()
            qrcode.make(url).save(data, format="PNG")
            pixmap = QPixmap()
            pixmap.loadFromData(data.getvalue())
            self.qr_image.setPixmap(pixmap.scaled(190,190,Qt.AspectRatioMode.KeepAspectRatio))
            self.integration_info.setText("Misma Wi-Fi. Acepta el certificado local. QR de un uso, 120 segundos. " + url.split('#')[0])
            self.qr_timer.start(120000)
        except Exception:
            self.error_label.setText("No pude generar el QR. Espera al servidor y revisa que qrcode esté instalado.")

    def connect_google(self):
        if self.auth_thread and self.auth_thread.is_alive():
            return
        def authorize():
            try:
                self.core.google.authorize(self.integration_cancel)
                self.emit("notice", "Google conectado. Pide consultar correos, calendario o Drive por texto o voz.")
            except Exception as exc:
                from victor.errors import VictorError
                self.emit("notice", str(exc) if isinstance(exc, VictorError) else "Google no pudo autorizarse. Revisa credenciales y usuario de prueba en Cloud Console.")
        self.auth_thread = threading.Thread(target=authorize, name="victor-google-auth", daemon=True)
        self.auth_thread.start()

    def open_spotify_player(self):
        try:
            self.navigate('spotify')
            self.sections.spotify_embed.start()
            self.error_label.setText('Pulsa Activar audio en Spotify de VICTOR para habilitar el sonido.')
        except Exception:
            logging.getLogger('victor.spotify').exception('embedded player failed')
            self.error_label.setText('No pude iniciar Spotify integrado. Comprueba Microsoft Edge WebView2 Runtime.')

    def connect_spotify(self):
        if self.auth_thread and self.auth_thread.is_alive():
            return
        self.integration_info.setText("Autoriza Spotify en el navegador. Tiempo máximo: 120 segundos.")
        def authorize():
            try:
                self.core.spotify.authorize(self.integration_cancel)
                self.emit("notice", "Spotify conectado. Pulsa Activar reproductor VICTOR; no necesitas abrir Spotify desktop.")
            except Exception as exc:
                logging.getLogger("victor.spotify").warning("OAuth failed type=%s", type(exc).__name__)
                self.emit("notice", "No se pudo conectar Spotify. Revisa credenciales, URI de retorno y autorización.")
        self.auth_thread = threading.Thread(target=authorize, name="victor-spotify-auth", daemon=True)
        self.auth_thread.start()

    def send(self, text=None, direct_tool=None, origin=None, voice=False):
        if not self.auth.authenticated:return False
        if self.closing or self.core.busy.is_set() or self.images.busy or self.images.pending:
            return
        if isinstance(text, bool) or text is None:
            text = self.entry.toPlainText().strip()
        if not text or len(text) > 12000:
            if text:
                self.error_label.setText("El mensaje excede 12.000 caracteres.")
            return
        from victor.ai.images import wants_image,image_capability_question
        if direct_tool is None and not origin and image_capability_question(text):
            self.images.explain(text,voice);return
        if direct_tool is None and wants_image(text):
            self.images.request(text,voice=voice,origin=origin);return
        self.voice_output.stop(preserve_music=bool(voice and not origin))
        self.spotify_turn=None;self.spotify_ack=False;self.voice_panel.show_response()
        self.entry.clear()
        self.error_label.clear()
        self.append_message("user", (f"Remoto {origin['user_id']}: " + readable_names(text) if origin else text))
        self.current_bubble = self.append_message("assistant", "…")
        self.partial = ""
        self.send_button.setEnabled(False)
        self.active_remote = origin
        self.voice_turn = bool(voice and not origin)
        from victor.gui.spotify_commands import spotify_command
        direct_tool=direct_tool or spotify_command(text,self.config.get('wake_word'), self.player.state)
        if not self.core.submit(text, self.conversation_id, direct_tool, origin=origin):
            self.active_remote = None
            self.voice_turn = False
            self.send_button.setEnabled(True)

    def stop(self):
        if hasattr(self,'voice_restart_timer'):self.voice_restart_timer.stop()
        self.core.stop()
        self.images.stop()
        self.tool_worker.interrupt()
        self.spotify_controls.interrupt()
        self.voice_input.stop()
        self.voice_output.stop()
        for card in list(self.approvals):
            card.resolve(False)

    def toggle_mic(self):
        if not self.auth.authenticated:return
        if self.config.get("voice_mode") != "push-to-talk":
            self.voice_restart_timer.stop()
            self.voice_input.stop() if self.voice_input.running else self.start_mic()

    def pause_mic(self):
        self.voice_restart_timer.stop()
        self.voice_input.stop()
        self.voice_output.end_interaction()

    def test_microphone(self):
        if not self.auth.authenticated:return
        if self.closing or self.voice_diagnostic_active:return
        if self.core.busy.is_set():
            self.error_label.setText('Espera a que termine la petición actual antes de probar el micrófono.');return
        self.voice_diagnostic_active=True
        self.voice_diagnostic_resume=self.config.get('voice_mode')=='continua' and (
            (self.voice_input.running and not self.voice_input.stop_event.is_set()) or self.voice_restart_timer.isActive())
        self.pause_mic();self.voice_output.stop()
        self.navigate('voice');self.voice_panel.show_response()
        self.voice_panel.response.setText('Di una frase para comprobar el texto reconocido. Esta prueba no ejecuta órdenes.')
        deadline=time.monotonic()+12
        def begin():
            if self.closing:return
            if self.voice_input.running or self.voice_output.busy:
                if time.monotonic()<deadline:QTimer.singleShot(50,begin)
                else:
                    self.voice_diagnostic_active=False;self.error_label.setText('El micrófono anterior aún está cerrándose. Vuelve a probar al terminar.')
                    if self.voice_diagnostic_resume:self.queue_continuous_listening()
                    self.voice_diagnostic_resume=False
                return
            self.voice_input.start(diagnostic=True)
        begin()

    def queue_continuous_listening(self):
        if not self.auth.authenticated:return
        if self.config.get('voice_mode')=='continua' and not self.closing:
            if self.config.get('voice_background_listening') and self.core.spotify.cache.path.exists() and self.sections.spotify_embed.process is None:
                self.sections.spotify_embed.start()
            self.voice_restart_timer.start(100)

    def resume_continuous_listening(self):
        if self.closing or self.config.get('voice_mode')!='continua':return
        if self.voice_input.running:
            if self.voice_input.stop_event.is_set():self.voice_restart_timer.start(100)
            return
        if self.core.busy.is_set():
            self.voice_restart_timer.start(200);return
        if self.config.get('voice_backend')=='whisper' and not self.maintenance.ready:
            from PySide6.QtCore import QProcess
            if self.maintenance.process.state()!=QProcess.ProcessState.NotRunning:
                self.voice_restart_timer.start(200);return
            self.error_label.setText('La escucha continua necesita el modelo Whisper descargado. Prepáralo en Ajustes → Voz.');return
        self.start_mic()

    def start_mic(self):
        if self.core.busy.is_set():
            return
        if self.config.get('voice_backend') == 'whisper' and (not self.maintenance.ready or self.maintenance.checked_name != self.config.get('whisper_model')):
            self.error_label.setText('Prepara el modelo en el panel ¿Estoy listo?; el chat sigue disponible.')
            self.navigate('diagnostics')
            self.maintenance.refresh()
            return
        if self.config.get("voice_backend") == "google" and not getattr(self, "audio_consent", False):
            if self.config.get('action_confirmations') and not self.config.get('voice_background_listening') and QMessageBox.question(self, "Audio online", "Google recibirá el audio para transcribirlo. ¿Continuar?") != QMessageBox.StandardButton.Yes:
                return
            self.audio_consent = True
        self.voice_output.stop()
        self.voice_input.start()

    def mic_press(self):
        if not self.auth.authenticated:return
        if self.config.get("voice_mode") == "push-to-talk":
            self.start_mic()

    def mic_release(self):
        if self.config.get("voice_mode") == "push-to-talk":
            self.voice_input.release()

    def refresh_history(self):
        self.history_list.clear()
        for row in self.core.history.list(self.history_search.text()):
            item = QListWidgetItem(row["title"])
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.history_list.addItem(item)

    def refresh_memories(self):
        self.memory_list.clear()
        for row in self.core.memory.search_memory(self.memory_search.text()):
            item = QListWidgetItem(row["key"] + "\n" + row["value"])
            item.setData(Qt.ItemDataRole.UserRole, row["key"])
            self.memory_list.addItem(item)

    def forget_memory(self):
        item = self.memory_list.currentItem()
        if item:
            self.run_tool("forget", {"key": item.data(Qt.ItemDataRole.UserRole)})

    def load_conversation(self, conversation_id):
        if self.core.busy.is_set():
            return
        self.conversation_id = conversation_id
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.current_bubble = None
        rows = self.core.history.messages(conversation_id)
        spotify_result=None
        for row in rows:
            text=row['content']
            if row['role']=='assistant' and text.startswith('[Resultado de herramienta spotify_'):
                try:spotify_result=json.loads(text.split('\n',1)[1])
                except (ValueError,IndexError):spotify_result=None
                if spotify_result and spotify_result.get('ok'):continue
            bubble=self.append_message(row['role'],text)
            attachment=self.images.archive.attachment(row['id'])
            if attachment:bubble.show_image(attachment)
            if spotify_result and spotify_result.get('ok') and row['role']=='assistant':
                try:data=json.loads(text)
                except (ValueError,TypeError):data=None
                if data==spotify_result.get('result') and isinstance(data,dict):
                    selected=data.get('seleccion')
                    if selected:bubble.show_music({'id':selected.get('id'),'name':selected.get('name'),'artists':selected.get('subtitle',''),'status':'Solicitud de Spotify'})
                    else:bubble.set_text('Spotify · '+str(data.get('solicitada') or data.get('cancion') or 'Control enviado al reproductor'))
                spotify_result=None
        if not rows:
            self.append_message("assistant", "Estoy listo. Puedes pedirme abrir una aplicación, consultar el equipo o recordar algo.")

    def new_conversation(self):
        if not self.core.busy.is_set():
            self.load_conversation(self.core.history.create())
            self.refresh_history()

    def delete_conversation(self):
        if not self.core.busy.is_set() and (not self.config.get("action_confirmations") or QMessageBox.question(self, "Eliminar", "¿Eliminar esta conversación local?") == QMessageBox.StandardButton.Yes):
            self.core.history.delete(self.conversation_id)
            self.new_conversation()

    def poll(self):
        try:
            for _ in range(250):
                try:
                    kind, payload = self.events.get_nowait()
                except queue.Empty:
                    break
                self.handle_event(kind, payload)
        except Exception:
            logging.getLogger("victor.gui").exception("Qt event failed")
            self.error_label.setText("No se pudo actualizar la interfaz. Consulta el registro local.")
        if self.closing:
            threads = [self.core.thread, self.voice_input.thread, self.voice_output.thread, self.metrics.thread, self.telegram.thread, self.auth_thread, self.local_remote.thread, self.local_remote.capture_thread, self.spotify_poller.thread, self.spotify_poller.art_thread, self.tool_worker.thread, self.spotify_controls.thread, self.spotify_web.thread]
            if not any(t and t.is_alive() for t in threads) and not (self.images.thread and self.images.thread.is_alive()) and not any(page.backend.running() for page in self.agent_pages.values()) and not self.maintenance.running() and not self.sections.spotify_embed.running() and not self.sections.whatsapp_embed.running():
                self.closed_cleanly = True
                self.close()

    def toggle_presentation(self):
        self.presentation=not self.presentation
        self.sidebar.setVisible(not self.presentation)
        self.menu.setVisible(not self.presentation)
        self.navigate('home')
        self.present_button.setText('Salir de presentación · F11' if self.presentation else 'Modo presentación · F11')
        self.arrange_metrics()

    def set_state(self,state):
        self.summary_title.setText('● '+state)
        self.summary_title.setStyleSheet(state_style(state))
        self.metric_values['state'].setText(state)
        self.voice_panel.set_state(state)
        if hasattr(self,'desktop_orb'):
            self.desktop_orb.set_state(state)

    def activity_state(self):
        """Un resultado secundario no oculta una respuesta de voz en curso."""
        if self.voice_output.speaking.is_set():return 'Respondiendo'
        if self.images.busy:return 'Pensando'
        if self.core.busy.is_set() or self.tool_worker.active.is_set() or self.spotify_controls.active.is_set():return 'Pensando'
        return 'Escuchando' if self.voice_input.running else 'Listo'

    def spotify_result_card(self,name,result):
        actions={'spotify_play','spotify_item_play','spotify_next','spotify_previous','spotify_pause','spotify_resume','spotify_volume','spotify_seek'}
        if name not in actions or not result.get('ok'):
            self.spotify_turn=None;self.voice_panel.show_response()
            return
        data=result.get('result',{});row=data.get('seleccion') if isinstance(data,dict) else None
        state=dict(self.player.state or {})
        expected=row.get('id') if row else None
        if row:
            state={'id':row.get('id'),'name':row.get('name','Spotify'),'artists':row.get('subtitle',''),'art_url':row.get('image',''),'status':'Conectando la canción…'}
            state['art']=self.spotify_poller.cover(state['art_url'])
        elif not state:state={'name':'Spotify','artists':'','status':'Orden enviada al reproductor'}
        self.spotify_turn={'name':name,'state':state,'expected':expected,'track_id':expected,'requested':bool(row),'deadline':time.monotonic()+8,'radio':''}
        self.voice_panel.show_music(state)
        if self.current_bubble:self.current_bubble.show_music(state)

    def present_spotify(self,state):
        turn=self.spotify_turn
        if not turn or not state:return
        expected=turn.get('expected')
        if expected and state.get('id')!=expected:
            if state.get('art_url')==turn['state'].get('art_url') and state.get('art'):
                turn['state']['art']=state['art']
            elif time.monotonic()>turn['deadline']:
                turn['state']['status']='Spotify todavía no confirmó la canción solicitada.'
            else:return
        else:
            turn['state']=dict(state)
            if expected:turn['expected']=None
        self.voice_panel.show_music(turn['state'])
        if self.current_bubble:self.current_bubble.show_music(turn['state'])
        self.speak_spotify_radio(turn)

    def speak_spotify_radio(self,turn):
        phrase=turn.get('radio','');state=turn['state']
        if (phrase and state.get('playing') and state.get('id')==turn.get('track_id')
                and self.core.spotify.browser and self.core.spotify.browser.active and not self.active_remote
                and not self.closing and not self.core.cancel.is_set()):
            turn['radio']=''
            self.voice_output.speak(phrase)

    def handle_event(self, kind, payload):
        if kind=='update_available':
            if not self.auth.authenticated or payload['version'] in self.notified_versions:return
            from .updates import UpdateDialog
            self.notified_versions.add(payload['version']);self.update_dialog=UpdateDialog(self.updates,payload,self);self.update_dialog.show();return
        if kind=='update_progress':
            if self.update_dialog:self.update_dialog.progress.setValue(payload)
            return
        if kind=='update_status':
            if self.auth.authenticated:self.error_label.setText(payload)
            return
        if kind in ('voice_wake','voice_interrupt'):
            if self.closing or self.voice_input.stop_event.is_set():
                payload.set()
                return
            self.voice_waiting_reply=True
            self.voice_output.begin_interaction()
            if kind=='voice_interrupt':
                self.core.stop()
                self.spotify_turn=None;self.spotify_ack=False
                self.voice_output.stop(preserve_music=True)
            self.voice_panel.show_response()
            self.voice_panel.response.setText('¿En qué te ayudo?')
            self.voice_output.speak('¿En qué te ayudo?', force=True, completed=payload)
            return
        if kind=='voice_reply_received':
            self.voice_waiting_reply=False
            return
        if kind in ('voice_reply_timeout','voice_input_stopped'):
            self.voice_waiting_reply=False
            self.voice_output.end_interaction()
            return
        if kind=='spotify_art':
            url,data=payload
            if self.spotify_turn and self.spotify_turn['state'].get('art_url')==url:
                self.spotify_turn['state']['art']=data;self.present_spotify(self.spotify_turn['state'])
            if self.player.state and self.player.state.get('art_url')==url:
                state=dict(self.player.state,art=data);self.player.update_state(state);self.sections.spotify_state(state)
            return
        if kind in ('panel_result','spotify_control_result'):
            name,result,seconds=payload
            self.sections.tool_result(name,result)
            if kind=='spotify_control_result':
                self.player.reconcile(name,result)
                self.sections.spotify_state(self.player.state)
                if not result.get('ok'):self.sections.spotify_embed.status.setText(result.get('error','Falló Spotify.'))
                self.spotify_poller.refresh_event.set()
            self.activity.setText(friendly_name(name)+' · '+('Ejecutada' if result.get('ok') else 'Falló'))
            self.refresh_history(); self.refresh_memories()
            self.set_state(self.activity_state())
            return
        if kind == 'tool_result':
            if payload[0] in {'spotify_play','spotify_item_play','spotify_playlist_play','spotify_next','spotify_previous','spotify_pause','spotify_resume','spotify_volume','spotify_seek'}:
                self.spotify_ack=bool(payload[1].get('ok'))
            self.player.reconcile(*payload)
            self.sections.tool_result(*payload)
            self.spotify_result_card(*payload)
            return
        if kind == 'spotify_browser_state':
            payload=dict(payload,art=self.spotify_poller.cover(payload.get('art_url','')))
            if self.player.pending:
                self.player.observed_pending=payload
                return
            self.player.update_state(payload);self.sections.spotify_state(payload)
            return
        if kind == "spotify_state":
            self.player.update_state(payload)
            self.sections.spotify_state(self.player.state)
            if any(not c.request.done.is_set() for c in self.approvals):
                self.player.hide()
            return
        if kind == "voice_confirmation":
            request, text = payload
            self.handle_voice_text(text, request)
            return
        if kind == "google_summary":
            if payload and ' · ' in payload:
                from victor.gui.service_cards import friendly_date
                title, date=payload.rsplit(' · ',1);payload=title+' · '+friendly_date(date)
            self.proactive.setText(payload)
            self.proactive.setVisible(bool(payload))
            return
        if kind == "remote_command":
            origin = payload["origin"]
            service = self.remote_service(origin)
            permitted = service.authorized(origin) if origin.get("source") == "local_web" else service.can_execute(origin)
            if self.closing or not permitted:
                return
            if self.core.busy.is_set():
                if origin.get("source") == "local_web":
                    service.reply(origin, "PC ocupado. Espera y vuelve a enviar.", done=True)
                else:
                    service.reply(origin, "El PC está ocupado. Intenta de nuevo al terminar la orden actual.")
            else:
                self.send(payload["text"], payload.get("tool"), origin)
            return
        if kind == "remote_approval":
            payload.details = confirmation_details(payload.title, payload.details)
            payload.title = friendly_name(payload.title)
            self.telegram.request_approval(payload)
            return
        if kind in ("token", "stream_reset", "answer"):
            if kind=='answer' and self.spotify_turn is None and not self.spotify_ack:
                from victor.gui.spotify_commands import unverified_spotify_answer
                if unverified_spotify_answer(payload):
                    payload='No se confirmó ninguna reproducción en Spotify. Pide la canción y el artista para ejecutar la orden.'
            self.partial = self.partial + payload if kind == "token" else "" if kind == "stream_reset" else payload
            musical=self.spotify_turn is not None
            if self.current_bubble and not musical:
                self.current_bubble.set_text(self.partial or "…")
                self.scroll_bottom()
            if not musical and not self.voice_waiting_reply:self.voice_panel.response.setText(display_text(self.partial or "Pensando…"))
            if kind == "answer" and not self.closing and not self.core.cancel.is_set():
                if musical:
                    state=self.spotify_turn['state']
                    payload=('Solicitud enviada: '+state.get('name','Spotify')+'.') if self.spotify_turn.get('requested') else 'Listo.'
                    if self.spotify_turn.get('requested'):
                        from victor.voice.music_radio import radio_phrase
                        self.spotify_turn['radio']=radio_phrase()
                if self.active_remote:
                    self.remote_service(self.active_remote).reply(self.active_remote, display_text(payload))
                else:
                    self.voice_output.speak(payload)
                    if musical:self.speak_spotify_radio(self.spotify_turn)
        elif kind == "approval":
            if self.closing:
                payload.done.set()
                return
            # Modal no bloqueante: accesible desde cualquier sección sin congelar workers.
            dialog=ApprovalDialog(self,payload)
            card=dialog.card; self.approvals.append(card)
            voice=QPushButton('Confirmar o cancelar por voz en este PC')
            voice.setIcon(icon('mic')); voice.clicked.connect(self.listen_approval); card.layout().addWidget(voice)
            self.voice_panel.confirm_button.show()
            self.approval_dialogs.append(dialog)
            dialog.finished.connect(lambda _code,d=dialog:self.release_dialog(d))
            if self.voice_turn and self.config.get('voice_mode') == 'continua' and self.voice_input.running and not self.voice_input.stop_event.is_set():
                if self.arm_spoken_approval(payload) and self.voice_background:
                    dialog.setModal(False)
                    dialog.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
                    dialog.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, True)
            dialog.show()
        elif kind == "metrics":
            self.metric_values["cpu"].setText(f"{payload['cpu']:.0f}%")
            self.metric_values["ram"].setText(f"{payload['ram']:.0f}%")
            self.metric_values["network"].setText(f"{payload['network']/1024:.0f} KB/s")
            self.dials['cpu'].set_value(payload['cpu']); self.dials['ram'].set_value(payload['ram'])
            self.dials['network'].set_value(payload['network']/1024)
            self.dials['network'].setToolTip(f"Red: {payload['network']/1024:.1f} KB/s · no es un porcentaje de capacidad")
            self.sections.cpu.setText(f"CPU en uso: {payload['cpu']:.0f}%")
            self.sections.ram.setText(f"Memoria RAM: {payload['ram']:.0f}%")
        elif kind == "hardware":
            self.metric_values["cpu"].setToolTip(payload["description"])
            self.dials['cpu'].setToolTip(payload['description'])
        elif kind == "status":
            self.set_state(self.activity_state())
        elif kind == "connection":
            self.connection_label.setText(payload)
            self.sidebar_connection.setText("● "+payload)
        elif kind in ("notice", "error"):
            self.error_label.setText(readable_names(payload[:800]))
            if kind == "error" and self.active_remote:
                self.remote_service(self.active_remote).reply(self.active_remote, payload)
        elif kind == "voice_status":
            listening = payload.startswith("Escuchando")
            self.listen_text.setText(payload)
            self.wave.setVisible(listening)
            self.listen_text.setVisible(listening)
            self.wave.set_active(listening)
            self.voice_panel.input_wave.set_active(listening)
            self.set_state("Escuchando" if listening else "Pensando" if payload.startswith('Transcribiendo') or self.core.busy.is_set() else "Respondiendo" if self.voice_output.speaking.is_set() else "Listo")
            if listening: self.voice_panel.prompt.setText(payload)
        elif kind == 'mic_level':
            self.wave.set_level(payload);self.voice_panel.set_input_level(payload)
            if hasattr(self,'desktop_orb'):self.desktop_orb.set_user_level(payload)
        elif kind == 'voice_audio_status':
            self.voice_panel.audio_processing.setText(payload)
        elif kind == 'voice_diagnostic_text':
            self.voice_panel.transcript.setText('Prueba de micrófono: '+payload)
            self.voice_panel.response.setText('Texto reconocido. No se ejecutó ninguna orden.')
        elif kind == 'voice_diagnostic_done':
            self.voice_diagnostic_active=False
            if not payload:self.voice_panel.response.setText('No reconocí una frase. Revisa el micrófono y el área de avisos, y vuelve a probar.')
            if self.voice_diagnostic_resume and not self.closing:self.queue_continuous_listening()
            self.voice_diagnostic_resume=False
        elif kind == 'tts_level':
            self.voice_panel.set_output_level(payload)
            if hasattr(self,'desktop_orb'):self.desktop_orb.set_bot_level(payload)
        elif kind == 'tts_meter':
            self.voice_panel.output_meter.setText('Nivel de voz no disponible en este motor/versión; el audio sigue funcionando.' if not payload else 'Voz de VICTOR · nivel real de audio')
        elif kind == "speech_status":
            self.listen_text.setText(payload)
            self.voice_panel.mic.set_active(payload.startswith('Hablando'))
            if not payload.startswith('Hablando'):self.voice_panel.set_output_level(0.)
            self.set_state("Respondiendo" if payload.startswith(("Hablando","Preparando","Bajando")) else "Pensando" if self.core.busy.is_set() else "Escuchando" if self.voice_input.running else "Listo")
            if payload.startswith('Bajando'):self.voice_panel.prompt.setText(payload)
        elif kind == "voice_text":
            self.handle_voice_text(payload)
        elif kind == "done":
            if not self.voice_waiting_reply:self.voice_output.end_interaction()
            self.confirmation_target = None
            self.voice_turn = False
            self.voice_panel.confirm_button.hide()
            if self.active_remote and self.active_remote.get("source") == "local_web":
                self.local_remote.reply(self.active_remote, "Turno finalizado.", done=True)
            self.active_remote = None
            self.send_button.setEnabled(not self.closing)
            self.set_state(self.activity_state())
            self.refresh_history()
            self.refresh_memories()

    def release_dialog(self,dialog):
        if dialog in self.approval_dialogs: self.approval_dialogs.remove(dialog)
        if dialog.card in self.approvals: self.approvals.remove(dialog.card)
        dialog.deleteLater()

    def changeEvent(self, event):
        super().changeEvent(event)
        from PySide6.QtCore import QEvent
        if hasattr(self,'voice_input') and event.type() in (QEvent.Type.ActivationChange,QEvent.Type.WindowStateChange):
            self.voice_background=not self.isActiveWindow() or self.isMinimized()
        if hasattr(self,'window_transitions') and event.type()==QEvent.Type.WindowStateChange:
            if event.oldState() & Qt.WindowState.WindowMinimized and not self.isMinimized():QTimer.singleShot(0,self.animate_restore)
        if hasattr(self, "wave"):
            self.wave.set_active(self.voice_input.running and self.isActiveWindow() and not self.isMinimized())

    def closeEvent(self, event):
        if not self.closing and not self.closed_cleanly and hasattr(self,'window_transitions') and not self.window_transitions.close_visual_done and (self.isVisible() or self.window_transitions.running):
            event.ignore();self.window_transitions.start('close');return
        if self.closed_cleanly:
            if hasattr(self,'desktop_orb'):self.desktop_orb.close()
            self.poll_timer.stop()
            self.wave.set_active(False)
            self.voice_panel.input_wave.set_active(False);self.voice_panel.mic.set_active(False)
            self.error_label.expiry.stop();self.error_label.fade.stop()
            event.accept()
            return
        event.ignore()
        if not self.closing:
            if hasattr(self,'desktop_orb'):self.desktop_orb.close()
            self.maintenance.stop()
            self.images.shutdown()
            for page in self.agent_pages.values():page.shutdown()
            self.qr_timer.stop()
            self.player.debounce.stop()
            self.sections.timer.stop()
            self.tool_worker.stop()
            self.spotify_controls.stop()
            self.spotify_web.stop()
            self.sections.spotify_embed.stop()
            self.sections.whatsapp_embed.stop()
            self.closing = True
            self.stop()
            self.integration_cancel.set()
            for panel in self.settings.account_panels.values():panel.cancel.set()
            self.telegram.stop()
            self.local_remote.stop()
            self.spotify_poller.stop_event.set()
            self.voice_output.close()
            self.updates.stop()
            threading.Thread(target=self.core.ai.close,name='victor-ai-close',daemon=True).start()
            self.metrics.stop_event.set()
            self.entry.setEnabled(False)
            self.send_button.setEnabled(False)
            self.error_label.setText("Cerrando tareas… Una llamada pendiente finalizará al alcanzar su timeout.")
