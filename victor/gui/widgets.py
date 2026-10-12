import math
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QPlainTextEdit, QDialog
from victor.security import Risk


class Composer(QPlainTextEdit):
    submitted = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.submitted.emit()
        else:
            super().keyPressEvent(event)


class Bubble(QFrame):
    def __init__(self, role, text):
        super().__init__()
        self.setStyleSheet("QFrame {border-radius: 16px; background: " + ("#2865cf" if role == "user" else "#222b3b") + ";}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 11, 15, 11)
        self.label = QLabel(text)
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.TextFormat.PlainText)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.label)

    def set_text(self, text):
        self.label.setText(text)


class ApprovalCard(QFrame):
    """Confirmación dentro del chat; la aprobación no puede producirla el modelo."""
    def __init__(self, request, parent=None):
        super().__init__(parent)
        self.request = request
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        title = QLabel("Autorizar: " + request.title)
        if request.origin:
            title.setText(title.text() + " · Telegram " + str(request.origin["user_id"]))
        title.setWordWrap(True)
        layout.addWidget(title)
        details = QPlainTextEdit(request.details)
        details.setReadOnly(True)
        details.setMaximumHeight(160)
        layout.addWidget(details)
        self.phrase = None
        if request.risk == Risk.HIGH:
            layout.addWidget(QLabel("Escribe EJECUTAR para autorizar en este PC"))
            self.phrase = QLineEdit()
            layout.addWidget(self.phrase)
        row = QHBoxLayout()
        self.approve = QPushButton("Confirmar")
        self.decline = QPushButton("Cancelar")
        self.approve.clicked.connect(lambda: self.resolve(True))
        self.decline.clicked.connect(lambda: self.resolve(False))
        row.addWidget(self.approve)
        row.addWidget(self.decline)
        layout.addLayout(row)
        if self.phrase:
            self.approve.setEnabled(False)
            self.phrase.textChanged.connect(lambda text: self.approve.setEnabled(text == "EJECUTAR"))

    def resolve(self, accepted):
        if self.request.done.is_set() or (accepted and self.phrase and self.phrase.text() != "EJECUTAR"):
            return
        self.request.accepted = accepted
        self.request.done.set()
        self.approve.setEnabled(False)
        self.decline.setEnabled(False)
        if self.phrase:
            self.phrase.setEnabled(False)
        self.layout().addWidget(QLabel("Autorizado una vez" if accepted else "Cancelado"))


class ApprovalDialog(QDialog):
    def __init__(self, parent, request):
        super().__init__(parent)
        self.setWindowTitle("VICTOR.IA · Confirmación explícita")
        self.setModal(True)
        self.resize(500, 420)
        self.card = ApprovalCard(request)
        layout = QVBoxLayout(self)
        layout.addWidget(self.card)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_done)
        self.timer.start(100)

    def check_done(self):
        if self.card.request.done.is_set():
            self.accept()

    def reject(self):
        self.card.resolve(False)
        super().reject()


class ListeningWave(QFrame):
    """Onda indicadora de actividad, no pretende representar muestras de audio."""
    def __init__(self):
        super().__init__()
        self.phase = 0
        self.active = False
        self.setFixedHeight(38)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)

    def set_active(self, active):
        self.active = active
        self.timer.start(80) if active else self.timer.stop()
        self.update()

    def tick(self):
        if not self.window().isActiveWindow() or self.window().isMinimized():
            return
        self.phase += 0.25
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#79a9ff"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for i in range(32):
            height = 3 + (abs(math.sin(i * .5 + self.phase)) * 23 if self.active else 1)
            x = self.width() / 2 + (i-16) * 6
            painter.drawLine(int(x), int(19-height/2), int(x), int(19+height/2))
