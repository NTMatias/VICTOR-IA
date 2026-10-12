"""Vista de voz que comparte el mismo micrófono y orquestador del chat."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton,QScrollArea,QFrame
from victor.gui.theme import state_style,title_font,LABEL_STYLES


class VoicePanel(QWidget):
    def __init__(self,app):
        super().__init__();self.app=app
        layout=QVBoxLayout(self);layout.setContentsMargins(16,16,16,16);layout.setSpacing(16)
        title=QLabel('Asistente de voz');title.setFont(title_font());title.setStyleSheet(LABEL_STYLES['heading']);title.setWordWrap(True);layout.addWidget(title)
        self.state=QLabel('● Listo');self.state.setAlignment(Qt.AlignmentFlag.AlignCenter);layout.addWidget(self.state)
        self.mic=QPushButton('🎙');self.mic.setObjectName('voiceMic');self.mic.setFixedSize(110,110)
        self.mic.clicked.connect(app.toggle_mic);self.mic.pressed.connect(app.mic_press);self.mic.released.connect(app.mic_release)
        layout.addWidget(self.mic,alignment=Qt.AlignmentFlag.AlignCenter)
        self.transcript=QLabel('Pulsa el micrófono y habla.');self.transcript.setWordWrap(True);self.transcript.setTextFormat(Qt.TextFormat.PlainText)
        self.response=QLabel('Tu respuesta aparecerá aquí.');self.response.setWordWrap(True);self.response.setTextFormat(Qt.TextFormat.PlainText)
        self.transcript.setObjectName('secondary')
        body=QWidget();self.content=QVBoxLayout(body);self.content.addWidget(self.transcript);self.content.addWidget(self.response);self.content.addStretch()
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(body);layout.addWidget(scroll,1)
        self.confirm_button=QPushButton('🎙 Responder a la confirmación')
        self.confirm_button.clicked.connect(app.listen_approval);self.confirm_button.hide();layout.addWidget(self.confirm_button)
        back=QPushButton('Volver al chat');back.clicked.connect(lambda:app.show_voice(False));layout.addWidget(back)

    def set_state(self,state):
        self.state.setText('● '+state);self.state.setStyleSheet(state_style(state))
