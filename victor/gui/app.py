"""Ventana Qt. El núcleo existente conserva toda la ejecución y los permisos."""
import json
import logging
import queue
import threading
from datetime import datetime
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QBoxLayout, QGridLayout, QScrollArea, QTabWidget, QListWidget, QListWidgetItem, QLineEdit, QPlainTextEdit, QComboBox, QMessageBox)
from victor.core import VictorCore
from victor.gui.theme import STYLE, LABEL_STYLES, state_style
from victor.gui.widgets import Bubble, MessageRow, Composer, ListeningWave, ApprovalCard, ApprovalDialog
from victor.gui.panels import SettingsManager, example_args
from victor.gui.metrics import MetricsWorker
from victor.voice.input import VoiceInput
from victor.voice.output import VoiceOutput
from victor.security import Risk
from victor.integrations.telegram_bot import TelegramService
from victor.integrations.local_remote import LocalRemote


class GUIManager(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.events = queue.Queue()
        self.core = VictorCore(config, self.emit)
        self.voice_output = VoiceOutput(config, self.emit)
        self.voice_input = VoiceInput(config, self.emit, lambda: not self.core.busy.is_set() and not self.voice_output.speaking.is_set())
        self.telegram = TelegramService(config, self.core, self.voice_input.transcriber, self.emit)
        self.local_remote = LocalRemote(config, self.core, self.emit)
        self.active_remote = None
        self.integration_cancel = threading.Event()
        self.auth_thread = None
        self.metrics = MetricsWorker(self.emit)
        self.closing = False
        self.closed_cleanly = False
        self.approvals = []
        self.current_bubble = None
        self.partial = ""
        self.drawer_open = False
        self.setWindowTitle("VICTOR.IA · Asistente personal")
        self.resize(940, 880)
        self.setMinimumSize(420, 640)
        self.setFont(QFont("Segoe UI Variable", 10))
        self.setStyleSheet(STYLE)
        self.build()
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
        if config.get("telegram_enabled"):
            self.telegram.start()

    def emit(self, kind, payload):
        self.events.put((kind, payload))

    def button(self, text, callback):
        button = QPushButton(text)
        button.clicked.connect(callback)
        return button

    def build(self):
        self.root = QWidget()
        self.root.setObjectName("root")
        self.outer = QWidget()
        self.outer.setObjectName("root")
        self.outer_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight, self.outer)
        self.outer_layout.setContentsMargins(20, 20, 20, 20)
        self.outer_layout.setSpacing(16)
        self.outer_layout.addWidget(self.root, 1)
        self.setCentralWidget(self.outer)
        layout = QVBoxLayout(self.root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        header = QHBoxLayout()
        greetings = QVBoxLayout()
        hour = datetime.now().hour
        greeting = "Buenos días" if hour < 12 else "Buenas tardes" if hour < 19 else "Buenas noches"
        small = QLabel(greeting + "  ·  VICTOR.IA")
        small.setStyleSheet(LABEL_STYLES["muted"])
        title = QLabel("¿En qué te ayudo?")
        title.setStyleSheet(LABEL_STYLES["heading"])
        greetings.addWidget(small)
        greetings.addWidget(title)
        header.addLayout(greetings, 1)
        self.menu = self.button("☰", lambda: self.toggle_drawer())
        header.addWidget(self.menu)
        self.mic = self.button("●", self.toggle_mic)
        self.mic.setObjectName("mic")
        self.mic.setToolTip("Activar / desactivar micrófono")
        self.mic.setFixedSize(52, 52)
        self.mic.pressed.connect(self.mic_press)
        self.mic.released.connect(self.mic_release)
        # El micrófono forma parte del compositor inferior.
        layout.addLayout(header)
        self.metric_grid = QGridLayout()
        self.metric_cards, self.metric_values = [], {}
        for key, label in (("cpu", "CPU"), ("ram", "RAM"), ("network", "RED · uso actual"), ("state", "ESTADO")):
            card = QFrame()
            card.setObjectName("card")
            inner = QVBoxLayout(card)
            caption = QLabel(label)
            caption.setStyleSheet(LABEL_STYLES["caption"])
            value = QLabel("Listo" if key == "state" else "—")
            value.setStyleSheet(LABEL_STYLES["metric"])
            inner.addWidget(caption)
            inner.addWidget(value)
            self.metric_values[key] = value
            self.metric_cards.append(card)
        layout.addLayout(self.metric_grid)
        self.quick = QGridLayout()
        self.quick_buttons = []
        for i, (label, command) in enumerate((("Ver pantalla", lambda: self.send("¿Qué hay en mi pantalla?")),
            ("Navegar", lambda: self.send("Abre Google")), ("Abrir app", self.quick_open), ("Memoria", lambda: self.toggle_drawer(1)))):
            button = self.button(label, command)
            self.quick_buttons.append(button)
            self.quick.addWidget(button, 0, i)
        layout.addLayout(self.quick)
        self.proactive = QLabel()
        self.proactive.setObjectName("proactive")
        self.proactive.setWordWrap(True)
        self.proactive.setTextFormat(Qt.TextFormat.PlainText)
        self.proactive.hide()
        layout.addWidget(self.proactive)
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_body = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_body)
        self.chat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.chat_layout.setContentsMargins(4, 8, 4, 8)
        self.chat_layout.setSpacing(12)
        self.chat_scroll.setWidget(self.chat_body)
        layout.addWidget(self.chat_scroll, 1)
        self.listen_text = QLabel("Micrófono apagado")
        self.listen_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.listen_text.setStyleSheet(LABEL_STYLES["muted"])
        self.wave = ListeningWave()
        self.wave.hide()
        layout.addWidget(self.wave)
        layout.addWidget(self.listen_text)
        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet(LABEL_STYLES["error"])
        layout.addWidget(self.error_label)
        self.entry = Composer()
        self.entry.setPlaceholderText("Escribe una orden o una pregunta…")
        self.entry.setFixedHeight(52)
        self.entry.submitted.connect(self.send)
        composer_row = QHBoxLayout()
        composer_row.setSpacing(10)
        composer_row.addWidget(self.entry, 1)
        composer_row.addWidget(self.mic)
        layout.addLayout(composer_row)
        actions = QHBoxLayout()
        self.connection_label = QLabel("Sin verificar")
        self.connection_label.setStyleSheet(LABEL_STYLES["caption"])
        actions.addWidget(self.connection_label, 1)
        actions.addWidget(self.button("Detener", self.stop))
        self.send_button = self.button("Enviar  ↑", self.send)
        self.send_button.setObjectName("primary")
        self.send_button.setFixedSize(76, 52)
        composer_row.addWidget(self.send_button)
        layout.addLayout(actions)
        self.build_drawer()
        self.arrange_metrics()

    def build_drawer(self):
        self.drawer = QFrame()
        self.outer_layout.addWidget(self.drawer)
        self.drawer.setObjectName("drawer")
        drawer_layout = QVBoxLayout(self.drawer)
        top = QHBoxLayout()
        top.addWidget(QLabel("Tu espacio"), 1)
        top.addWidget(self.button("Cerrar", lambda: self.toggle_drawer()))
        drawer_layout.addLayout(top)
        self.tabs = QTabWidget()
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabBar().setUsesScrollButtons(True)
        drawer_layout.addWidget(self.tabs)
        history = QWidget()
        hl = QVBoxLayout(history)
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Buscar conversaciones")
        self.history_search.returnPressed.connect(self.refresh_history)
        hl.addWidget(self.history_search)
        hl.addWidget(self.button("Nueva conversación", self.new_conversation))
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(lambda item: self.load_conversation(item.data(Qt.ItemDataRole.UserRole)))
        hl.addWidget(self.history_list)
        hl.addWidget(self.button("Eliminar conversación", self.delete_conversation))
        self.tabs.addTab(history, "Historial")
        memory = QWidget()
        ml = QVBoxLayout(memory)
        self.memory_key = QLineEdit()
        self.memory_key.setPlaceholderText("Clave / buscar recuerdo")
        self.memory_value = QPlainTextEdit()
        self.memory_value.setMaximumHeight(90)
        ml.addWidget(self.memory_key)
        ml.addWidget(self.memory_value)
        ml.addWidget(self.button("Guardar", lambda: self.send("Guardar recuerdo", ("remember", {"key": self.memory_key.text(), "value": self.memory_value.toPlainText()}))))
        ml.addWidget(self.button("Buscar", self.refresh_memories))
        self.memory_list = QListWidget()
        ml.addWidget(self.memory_list)
        ml.addWidget(self.button("Eliminar seleccionado", self.forget_memory))
        self.tabs.addTab(memory, "Memoria")
        self.settings = SettingsManager(self)
        self.tabs.addTab(self.settings, "Ajustes")
        tools = QWidget()
        tl = QVBoxLayout(tools)
        self.tool_select = QComboBox()
        self.tool_select.addItems(self.core.registry.tools)
        self.tool_select.currentTextChanged.connect(self.select_tool)
        self.tool_desc = QLabel()
        self.tool_desc.setWordWrap(True)
        self.tool_args = QPlainTextEdit()
        tl.addWidget(self.tool_select)
        tl.addWidget(self.tool_desc)
        tl.addWidget(self.tool_args)
        tl.addWidget(self.button("Ejecutar herramienta", self.execute_tool))
        self.tabs.addTab(tools, "Tools")
        integrations = QWidget()
        il = QVBoxLayout(integrations)
        self.integration_info = QLabel("Telegram: configura TELEGRAM_BOT_TOKEN en .env y activa el bot. Spotify: configura las credenciales y conecta tu cuenta.")
        self.integration_info.setWordWrap(True)
        il.addWidget(self.integration_info)
        il.addWidget(self.button("Activar / detener Telegram", self.toggle_telegram))
        il.addWidget(self.button("Generar código de emparejamiento", self.pair_telegram))
        il.addWidget(self.button("Pausar / reanudar remoto", lambda: self.telegram.pause(not self.config.get("telegram_paused"))))
        il.addWidget(self.button("Conectar Spotify", self.connect_spotify))
        il.addWidget(self.button("Conectar Google", self.connect_google))
        il.addWidget(self.button("Próximos eventos Google", lambda: self.send("Consultar calendario", ("google_events", {}))))
        il.addWidget(self.button("Activar / detener remoto HTTPS", self.toggle_local_remote))
        il.addWidget(self.button("Mostrar QR local", self.show_local_qr))
        self.qr_image = QLabel()
        self.qr_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        il.addWidget(self.qr_image)
        il.addStretch()
        integration_scroll = QScrollArea()
        integration_scroll.setWidgetResizable(True)
        integration_scroll.setWidget(integrations)
        self.tabs.addTab(integration_scroll, "Conectar")
        self.select_tool(self.tool_select.currentText())
        self.drawer.hide()
        self.drawer_animation = QPropertyAnimation(self.drawer, b"maximumWidth", self)
        self.drawer_animation.setDuration(180)
        self.drawer_animation.valueChanged.connect(lambda _: self.arrange_metrics())
        self.drawer_animation.finished.connect(lambda: self.drawer.setVisible(self.drawer_open))

    def arrange_metrics(self):
        columns = 2 if self.root.width() < 650 else 4
        for i in range(4):
            self.metric_grid.setColumnStretch(i, 1 if i < columns else 0)
            self.quick.setColumnStretch(i, 1 if i < columns else 0)
        for i, card in enumerate(self.metric_cards):
            self.metric_grid.addWidget(card, i // columns, i % columns)
        for i, button in enumerate(self.quick_buttons):
            self.quick.addWidget(button, i // columns, i % columns)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "drawer"):
            self.layout_drawer()
        if hasattr(self, "metric_cards"):
            self.arrange_metrics()

    def layout_drawer(self):
        narrow = self.width() < 800
        self.outer_layout.setDirection(QBoxLayout.Direction.TopToBottom if narrow else QBoxLayout.Direction.LeftToRight)
        self.drawer.setMaximumHeight(250 if narrow else 16777215)
        self.drawer.setMaximumWidth(16777215 if narrow else 360)
        self.drawer.setMinimumWidth(0)

    def toggle_drawer(self, tab=None):
        self.drawer_open = True if tab is not None else not self.drawer_open
        if tab is not None:
            self.tabs.setCurrentIndex(tab)
        self.drawer_animation.stop()
        self.layout_drawer()
        if self.width() >= 800:
            self.drawer.show()
            self.drawer_animation.setStartValue(0 if self.drawer_open else 360)
            self.drawer_animation.setEndValue(360 if self.drawer_open else 0)
            self.drawer_animation.start()
        else:
            self.drawer.setVisible(self.drawer_open)
        QTimer.singleShot(200, self.arrange_metrics)

    def quick_open(self):
        self.toggle_drawer(3)
        self.tool_select.setCurrentText("open_application")

    def refresh_config(self):
        configured = [p for p, enabled in self.config.credentials_status().items() if enabled]
        self.connection_label.setText(self.config.get("provider") + " · " + ("sin verificar" if configured else "Sin conexión a IA"))
        if not configured and self.config.get("provider") != "Ollama":
            self.error_label.setText("Configura .env para IA online o selecciona Ollama en Ajustes. Los comandos locales funcionan sin claves.")
        self.setStyleSheet(__import__("victor.gui.theme", fromlist=["theme_style"]).theme_style(self.config.get("theme")))

    def append_message(self, role, text):
        container = MessageRow(role, text)
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
            self.integration_info.setText("En tu chat privado con el bot escribe /vincular " + self.telegram.pairing_code() + " · caduca en 120 segundos.")
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
            QTimer.singleShot(120000, self.qr_image.clear)
        except Exception:
            self.error_label.setText("No pude generar el QR. Espera al servidor y revisa que qrcode esté instalado.")

    def connect_google(self):
        if self.auth_thread and self.auth_thread.is_alive():
            return
        def authorize():
            try:
                self.core.google.authorize(self.integration_cancel)
                self.emit("notice", "Google conectado. Consulta correos, calendario o Drive desde Tools.")
            except Exception as exc:
                from victor.errors import VictorError
                self.emit("notice", str(exc) if isinstance(exc, VictorError) else "Google no pudo autorizarse. Revisa credenciales y usuario de prueba en Cloud Console.")
        self.auth_thread = threading.Thread(target=authorize, name="victor-google-auth", daemon=True)
        self.auth_thread.start()

    def connect_spotify(self):
        if self.auth_thread and self.auth_thread.is_alive():
            return
        self.integration_info.setText("Autoriza Spotify en el navegador. Tiempo máximo: 120 segundos.")
        def authorize():
            try:
                self.core.spotify.authorize(self.integration_cancel)
                self.emit("notice", "Spotify conectado. Abre Spotify en el PC y activa la reproducción.")
            except Exception as exc:
                logging.getLogger("victor.spotify").warning("OAuth failed type=%s", type(exc).__name__)
                self.emit("notice", "No se pudo conectar Spotify. Revisa credenciales, URI de retorno y autorización.")
        self.auth_thread = threading.Thread(target=authorize, name="victor-spotify-auth", daemon=True)
        self.auth_thread.start()

    def send(self, text=None, direct_tool=None, origin=None):
        if self.closing or self.core.busy.is_set():
            return
        if isinstance(text, bool) or text is None:
            text = self.entry.toPlainText().strip()
        if not text or len(text) > 12000:
            if text:
                self.error_label.setText("El mensaje excede 12.000 caracteres.")
            return
        self.voice_output.stop()
        self.entry.clear()
        self.error_label.clear()
        self.append_message("user", (f"Remoto {origin['user_id']}: " if origin else "") + text)
        self.current_bubble = self.append_message("assistant", "…")
        self.partial = ""
        self.send_button.setEnabled(False)
        self.active_remote = origin
        if not self.core.submit(text, self.conversation_id, direct_tool, origin=origin):
            self.active_remote = None
            self.send_button.setEnabled(True)

    def stop(self):
        self.core.stop()
        self.voice_input.stop()
        self.voice_output.stop()
        for card in self.approvals:
            card.resolve(False)

    def toggle_mic(self):
        if self.config.get("voice_mode") != "push-to-talk":
            self.voice_input.stop() if self.voice_input.running else self.start_mic()

    def start_mic(self):
        if self.core.busy.is_set():
            return
        if self.config.get("voice_backend") == "google" and not getattr(self, "audio_consent", False):
            if QMessageBox.question(self, "Audio online", "Google recibirá el audio para transcribirlo. ¿Continuar?") != QMessageBox.StandardButton.Yes:
                return
            self.audio_consent = True
        self.voice_output.stop()
        self.voice_input.start()

    def mic_press(self):
        if self.config.get("voice_mode") == "push-to-talk":
            self.start_mic()

    def mic_release(self):
        if self.config.get("voice_mode") == "push-to-talk":
            self.voice_input.release()

    def select_tool(self, name):
        tool = self.core.registry.tools[name]
        self.tool_desc.setText(tool.description + " · " + tool.risk.name)
        self.tool_args.setPlainText(json.dumps(example_args(tool.schema), ensure_ascii=False, indent=2))

    def execute_tool(self):
        try:
            name = self.tool_select.currentText()
            args = json.loads(self.tool_args.toPlainText())
            self.send("Ejecutar " + name, (name, args))
        except ValueError:
            self.error_label.setText("Revisa el formato JSON de los argumentos.")

    def refresh_history(self):
        self.history_list.clear()
        for row in self.core.history.list(self.history_search.text()):
            item = QListWidgetItem(row["title"])
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.history_list.addItem(item)

    def refresh_memories(self):
        self.memory_list.clear()
        for row in self.core.memory.search_memory(self.memory_key.text()):
            item = QListWidgetItem(row["key"] + "\n" + row["value"])
            item.setData(Qt.ItemDataRole.UserRole, row["key"])
            self.memory_list.addItem(item)

    def forget_memory(self):
        item = self.memory_list.currentItem()
        if item:
            self.send("Eliminar recuerdo", ("forget", {"key": item.data(Qt.ItemDataRole.UserRole)}))

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
        for row in rows:
            self.append_message(row["role"], row["content"])
        if not rows:
            self.append_message("assistant", "Estoy listo. Puedes pedirme abrir una aplicación, consultar el equipo o recordar algo.")

    def new_conversation(self):
        if not self.core.busy.is_set():
            self.load_conversation(self.core.history.create())
            self.refresh_history()

    def delete_conversation(self):
        if not self.core.busy.is_set() and QMessageBox.question(self, "Eliminar", "¿Eliminar esta conversación local?") == QMessageBox.StandardButton.Yes:
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
            threads = [self.core.thread, self.voice_input.thread, self.voice_output.thread, self.metrics.thread, self.telegram.thread, self.auth_thread, self.local_remote.thread, self.local_remote.capture_thread]
            if not any(t and t.is_alive() for t in threads):
                self.closed_cleanly = True
                self.close()

    def set_state(self, state):
        self.metric_values["state"].setText("● " + state)
        self.metric_values["state"].setStyleSheet(state_style(state))

    def handle_event(self, kind, payload):
        if kind == "google_summary":
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
            self.telegram.request_approval(payload)
            return
        if kind in ("token", "stream_reset", "answer"):
            self.partial = self.partial + payload if kind == "token" else "" if kind == "stream_reset" else payload
            if self.current_bubble:
                self.current_bubble.set_text(self.partial or "…")
                self.scroll_bottom()
            if kind == "answer" and not self.closing and not self.core.cancel.is_set():
                if self.active_remote:
                    self.remote_service(self.active_remote).reply(self.active_remote, payload)
                else:
                    self.voice_output.speak(payload)
        elif kind == "approval":
            if self.closing or self.core.cancel.is_set():
                payload.done.set()
            elif payload.risk == Risk.HIGH:
                card = ApprovalCard(payload)
                self.approvals.append(card)
                self.chat_layout.addWidget(card)
                self.scroll_bottom()
            else:
                card = ApprovalCard(payload)
                self.approvals.append(card)
                self.chat_layout.addWidget(card)
                self.scroll_bottom()
        elif kind == "metrics":
            self.metric_values["cpu"].setText(f"{payload['cpu']:.0f}%")
            self.metric_values["ram"].setText(f"{payload['ram']:.0f}%")
            self.metric_values["network"].setText(f"{payload['network']/1024:.0f} KB/s")
        elif kind == "hardware":
            self.metric_values["cpu"].setToolTip(payload["description"])
        elif kind == "status":
            self.set_state("Pensando" if self.core.busy.is_set() else "Listo")
        elif kind == "connection":
            self.connection_label.setText(payload)
        elif kind in ("notice", "error"):
            self.error_label.setText(payload[:800])
            if kind == "error" and self.active_remote:
                self.remote_service(self.active_remote).reply(self.active_remote, payload)
        elif kind == "voice_status":
            listening = payload.startswith("Escuchando")
            self.listen_text.setText("Escuchando · di '" + self.config.get("wake_word") + "' para hablar" if listening else payload)
            self.wave.setVisible(listening)
            self.wave.set_active(listening and self.isActiveWindow())
            self.set_state("Escuchando" if listening else "Listo")
        elif kind == "speech_status":
            self.listen_text.setText(payload)
        elif kind == "voice_text":
            self.send(payload)
        elif kind == "done":
            if self.active_remote and self.active_remote.get("source") == "local_web":
                self.local_remote.reply(self.active_remote, "Turno finalizado.", done=True)
            self.active_remote = None
            self.send_button.setEnabled(not self.closing)
            self.set_state("Listo")
            self.refresh_history()
            self.refresh_memories()

    def changeEvent(self, event):
        super().changeEvent(event)
        if hasattr(self, "wave"):
            self.wave.set_active(self.voice_input.running and self.isActiveWindow() and not self.isMinimized())

    def closeEvent(self, event):
        if self.closed_cleanly:
            self.poll_timer.stop()
            self.wave.set_active(False)
            event.accept()
            return
        event.ignore()
        if not self.closing:
            self.closing = True
            self.stop()
            self.integration_cancel.set()
            self.telegram.stop()
            self.local_remote.stop()
            self.voice_output.close()
            self.metrics.stop_event.set()
            self.entry.setEnabled(False)
            self.send_button.setEnabled(False)
            self.error_label.setText("Cerrando tareas… Una llamada pendiente finalizará al alcanzar su timeout.")
