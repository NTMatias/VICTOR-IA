"""Pantalla de inicio de sesión y bloqueo para VICTOR.IA."""
from __future__ import annotations
import threading
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QPoint
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QSizePolicy,
    QDialog,
)
from victor.auth import AuthManager
from victor.gui.theme import COLORS, title_font
from victor.gui.widgets import icon, brand_icon


class LoginOverlay(QWidget):
    """Pantalla de autenticación moderna con estética Grafito."""

    authenticated = Signal()
    checked=Signal(bool,str)

    def __init__(self, auth: AuthManager, parent=None):
        super().__init__(parent)
        self.auth = auth
        self.busy=False;self.registering=False;self.checked.connect(self._checked)
        self.setObjectName("loginOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            """
            QWidget#loginOverlay {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(17, 19, 24, 250),
                    stop:0.5 rgba(22, 28, 40, 252),
                    stop:1 rgba(29, 32, 42, 250));
            }
            QFrame#loginCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(29, 32, 39, 230),
                    stop:1 rgba(22, 25, 33, 240));
                border: 1px solid rgba(131, 175, 255, 45);
                border-radius: 20px;
            }
            QLineEdit {
                background: #16181E;
                border: 1px solid #30333E;
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 14px;
                color: #E9EAF1;
            }
            QLineEdit:focus {
                border: 1px solid #83AFFF;
                background: #1B1E26;
            }
            QPushButton#primaryAction {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #588AD8, stop:1 #7B68EE);
                border: 1px solid #83AFFF;
                border-radius: 10px;
                padding: 12px 20px;
                color: white;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton#primaryAction:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6A9BF0, stop:1 #8F7DF5);
                border-color: #A9C8FF;
            }
            QPushButton#ghostButton {
                background: transparent;
                border: 0;
                color: #9196A5;
                font-size: 12px;
                text-decoration: underline;
                padding: 4px;
            }
            QPushButton#ghostButton:hover {
                color: #83AFFF;
            }
            QLabel#loginError {
                color: #F28F95;
                font-size: 13px;
                font-weight: 500;
            }
            """
        )

        self.setup_ui()
        if getattr(self.auth,'cloud',False):QTimer.singleShot(0,self.restore_cloud_session)

    def setup_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 20, 20, 20)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Tarjeta central flotante
        self.card = QFrame()
        self.card.setObjectName("loginCard")
        self.card.setMaximumWidth(420);self.card.setMinimumWidth(300)
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(36, 40, 36, 36)
        card_layout.setSpacing(16)

        # Cabecera con logo
        brand_row = QHBoxLayout()
        brand_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_icon_lbl = QLabel()
        brand_icon_lbl.setPixmap(icon("brand", size=40).pixmap(40, 40))
        brand_row.addWidget(brand_icon_lbl)
        card_layout.addLayout(brand_row)

        self.title_label = QLabel("<b>VICTOR.<span style='color:#83AFFF'>IA</span></b>")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24px; color: #E9EAF1; margin-top: 4px;")
        card_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("Asistente personal de escritorio")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setStyleSheet("color: #9196A5; font-size: 13px; margin-bottom: 8px;")
        card_layout.addWidget(self.subtitle_label)

        # Mensaje de error
        self.error_label = QLabel("")
        self.error_label.setObjectName("loginError")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        card_layout.addWidget(self.error_label)

        self.user_label=QLabel('Usuario');card_layout.addWidget(self.user_label)
        self.user_input=QLineEdit();self.user_input.setPlaceholderText('Tu nombre');card_layout.addWidget(self.user_input)

        # Campo contraseña principal
        self.pass_label = QLabel("Contraseña o PIN")
        self.pass_label.setStyleSheet("color: #C3CCDB; font-size: 12px; font-weight: 600;")
        card_layout.addWidget(self.pass_label)

        pass_row = QHBoxLayout()
        pass_row.setSpacing(6)
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_input.setPlaceholderText("Ingresa tu clave...")
        self.pass_input.returnPressed.connect(self.submit)
        pass_row.addWidget(self.pass_input, 1)

        self.toggle_eye_btn = QPushButton()
        self.toggle_eye_btn.setIcon(icon("screen", size=16))
        self.toggle_eye_btn.setToolTip("Mostrar/Ocultar contraseña")
        self.toggle_eye_btn.setFixedSize(38, 38)
        self.toggle_eye_btn.clicked.connect(self.toggle_show_password)
        pass_row.addWidget(self.toggle_eye_btn)
        card_layout.addLayout(pass_row)

        # Campo confirmación (solo para configuración inicial)
        self.confirm_label = QLabel("Confirmar contraseña")
        self.confirm_label.setStyleSheet("color: #C3CCDB; font-size: 12px; font-weight: 600;")
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Repite tu clave...")
        self.confirm_input.returnPressed.connect(self.submit)
        card_layout.addWidget(self.confirm_label)
        card_layout.addWidget(self.confirm_input)

        # Campo pista (solo para configuración inicial)
        self.hint_label = QLabel("Pista para recordar la contraseña (opcional)")
        self.hint_label.setStyleSheet("color: #9196A5; font-size: 12px;")
        self.hint_input = QLineEdit()
        self.hint_input.setPlaceholderText("Ej: Año de mi primera guitarra...")
        self.hint_input.returnPressed.connect(self.submit)
        card_layout.addWidget(self.hint_label)
        card_layout.addWidget(self.hint_input)

        # Opción recordar sesión (solo en login normal)
        self.remember_cb = QCheckBox("Recordar sesión en este equipo (14 días)")
        self.remember_cb.setChecked(False)
        self.remember_cb.setStyleSheet("color: #9196A5; font-size: 12px; margin-top: 4px;")
        card_layout.addWidget(self.remember_cb)

        # Botón de acción principal
        self.submit_btn = QPushButton("Iniciar sesión")
        self.submit_btn.setObjectName("primaryAction")
        self.submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.submit_btn.clicked.connect(self.submit)
        card_layout.addWidget(self.submit_btn)

        # Pista visible al fallar o solicitar
        self.hint_display = QLabel("")
        self.hint_display.setStyleSheet("color: #83AFFF; font-size: 12px; font-style: italic;")
        self.hint_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_display.setWordWrap(True)
        self.hint_display.hide()
        card_layout.addWidget(self.hint_display)

        self.show_hint_btn = QPushButton("¿Olvidaste tu contraseña? Ver pista")
        self.show_hint_btn.setObjectName("ghostButton")
        self.show_hint_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.show_hint_btn.clicked.connect(self.reveal_hint)
        self.show_hint_btn.hide()
        card_layout.addWidget(self.show_hint_btn)
        self.cloud_toggle=QPushButton('Crear una cuenta');self.cloud_toggle.clicked.connect(self.toggle_registration);card_layout.addWidget(self.cloud_toggle)
        self.cloud_notice=QLabel('El administrador podrá ver tu correo, fecha de registro, último acceso y versión. Tus conversaciones y claves de IA no se envían.');self.cloud_notice.setWordWrap(True);card_layout.addWidget(self.cloud_notice)
        self.cloud_consent=QCheckBox('Acepto registrar esos datos de mi cuenta.');card_layout.addWidget(self.cloud_consent)

        root_layout.addWidget(self.card)
        self.refresh_mode()

    def refresh_mode(self):
        """Alterna entre modo primer registro o modo inicio de sesión."""
        is_configured = self.auth.is_configured()
        cloud=getattr(self.auth,'cloud',False)
        self.cloud_toggle.setVisible(cloud);self.cloud_notice.setVisible(cloud);self.cloud_consent.setVisible(cloud and self.registering)
        self.user_input.setText(self.auth.username() if is_configured else '')
        self.user_input.setReadOnly(is_configured)
        if not is_configured:
            self.subtitle_label.setText("Crea tu acceso local a VICTOR")
            self.pass_label.setText("Nueva contraseña o PIN (mín. 8 caracteres)")
            self.confirm_label.show()
            self.confirm_input.show()
            self.hint_label.show()
            self.hint_input.show()
            self.remember_cb.hide()
            self.show_hint_btn.hide()
            self.submit_btn.setText("Crear clave e ingresar")
        else:
            self.subtitle_label.setText("Introduce tu contraseña para desbloquear")
            self.pass_label.setText("Contraseña o PIN")
            self.confirm_label.hide()
            self.confirm_input.hide()
            self.hint_label.hide()
            self.hint_input.hide()
            self.remember_cb.show()
            hint = self.auth.get_hint()
            self.show_hint_btn.setVisible(bool(hint))
            self.submit_btn.setText("Iniciar sesión")

        self.pass_input.clear()
        self.confirm_input.clear()
        self.error_label.hide()
        self.hint_display.hide()
        QTimer.singleShot(100, self.pass_input.setFocus)
        if cloud:
            self.user_label.setText('Correo electrónico');self.user_input.setReadOnly(False);self.user_input.setPlaceholderText('tu@correo.com')
            self.subtitle_label.setText('Crea tu cuenta de VICTOR' if self.registering else 'Entra con tu cuenta de VICTOR')
            self.submit_btn.setText('Crear cuenta' if self.registering else 'Iniciar sesión')
            self.confirm_label.setVisible(self.registering);self.confirm_input.setVisible(self.registering)
            self.cloud_toggle.setText('Ya tengo una cuenta' if self.registering else 'Crear una cuenta')

    def toggle_registration(self):
        if self.busy:return
        email=self.user_input.text();self.registering=not self.registering;self.refresh_mode();self.user_input.setText(email)
    def restore_cloud_session(self):
        if self.busy or not self.auth.session_file.exists():return
        self.busy=True;self.submit_btn.setEnabled(False)
        def restore():
            valid=self.auth.check_saved_session()
            try:self.checked.emit(valid,'' if valid else 'Inicia sesión de nuevo para continuar.')
            except RuntimeError:pass
        threading.Thread(target=restore,name='victor-cloud-restore',daemon=True).start()

    def toggle_show_password(self):
        current = self.pass_input.echoMode()
        new_mode = QLineEdit.EchoMode.Normal if current == QLineEdit.EchoMode.Password else QLineEdit.EchoMode.Password
        self.pass_input.setEchoMode(new_mode)
        if self.confirm_input.isVisible():
            self.confirm_input.setEchoMode(new_mode)

    def reveal_hint(self):
        hint = self.auth.get_hint()
        if hint:
            self.hint_display.setText(f"Pista guardada: {hint}")
            self.hint_display.show()

    def submit(self):
        if self.busy:return
        pwd = self.pass_input.text()
        confirm=self.confirm_input.text();hint=self.hint_input.text().strip();username=self.user_input.text().strip()
        configured=self.auth.is_configured();remember=self.remember_cb.isChecked()
        cloud=getattr(self.auth,'cloud',False)
        if cloud and self.registering and (pwd!=confirm or not self.cloud_consent.isChecked()):
            self.show_error('Confirma tu contraseña y acepta registrar los datos de cuenta.');return
        if not configured and (len(pwd)<8 or pwd!=confirm or not username):
            self.show_error('Escribe tu nombre y una contraseña de al menos 8 caracteres; confirma la misma contraseña.');return
        self.busy=True;self.submit_btn.setEnabled(False);self.error_label.hide()
        def verify():
            try:
                if cloud:
                    if self.registering:self.auth.signup(username,pwd)
                    else:self.auth.login(username,pwd)
                elif configured:
                    if not self.auth.verify(pwd):raise ValueError('No se pudo entrar. Revisa la contraseña o espera 30 segundos tras varios intentos.')
                else:self.auth.setup(pwd,hint,username)
                if remember:self.auth.save_session(14)
                else:self.auth.clear_saved_session()
                result=(True,'')
            except Exception as exc:result=(False,str(exc) if isinstance(exc,ValueError) else 'No se pudo abrir el acceso local.')
            try:self.checked.emit(*result)
            except RuntimeError:pass
        threading.Thread(target=verify,name='victor-login',daemon=True).start()

    def _checked(self,success,message):
        self.busy=False;self.submit_btn.setEnabled(True)
        if success:
            self.pass_input.clear();self.confirm_input.clear();self.authenticated.emit()
        else:
            if message.startswith('Cuenta creada:'):self.registering=False;self.refresh_mode()
            self.show_error(message)

    def show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.show()


class ChangePasswordDialog(QDialog):
    """Diálogo modal para cambiar la contraseña de acceso."""
    checked=Signal(bool,str)

    def __init__(self, auth: AuthManager, parent=None):
        super().__init__(parent)
        self.auth = auth
        self.busy=False;self.checked.connect(self._saved)
        self.setWindowTitle("Cambiar contraseña · VICTOR.IA")
        self.setFixedSize(380, 390)
        self.setStyleSheet("""
            QDialog { background: #1D2027; color: #E9EAF1; }
            QLabel { color: #C3CCDB; font-size: 12px; }
            QLineEdit { background: #16181E; border: 1px solid #30333E; border-radius: 8px; padding: 8px 12px; color: #E9EAF1; }
            QLineEdit:focus { border-color: #83AFFF; }
            QPushButton#primaryAction { background: #588AD8; border: 1px solid #749DE1; border-radius: 8px; padding: 9px 16px; color: white; font-weight: 600; }
            QPushButton#primaryAction:hover { background: #6A9BF0; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        title = QLabel("Cambiar clave de acceso")
        title.setStyleSheet("font-size: 17px; font-weight: 650; color: #E9EAF1;")
        layout.addWidget(title)

        self.error = QLabel("")
        self.error.setStyleSheet("color: #F28F95; font-size: 12px;")
        self.error.hide()
        layout.addWidget(self.error)

        layout.addWidget(QLabel("Contraseña actual:"))
        self.current_pwd = QLineEdit()
        self.current_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.current_pwd)

        layout.addWidget(QLabel("Nueva contraseña (mín. 8 caracteres):"))
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.new_pwd)

        layout.addWidget(QLabel("Confirmar nueva contraseña:"))
        self.confirm_pwd = QLineEdit()
        self.confirm_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.confirm_pwd)

        layout.addWidget(QLabel("Nueva pista (opcional):"))
        self.hint_input = QLineEdit()
        self.hint_input.setText(self.auth.get_hint())
        layout.addWidget(self.hint_input)

        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Guardar nueva clave")
        self.save_btn=save_btn
        save_btn.setObjectName("primaryAction")
        save_btn.clicked.connect(self.save)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def save(self):
        if self.busy:return
        cur = self.current_pwd.text()
        new = self.new_pwd.text()
        conf = self.confirm_pwd.text()
        hint = self.hint_input.text().strip()

        if not 8<=len(new)<=256:
            self.error.setText("La nueva clave debe tener entre 8 y 256 caracteres.")
            self.error.show()
            return
        if new != conf:
            self.error.setText("Las nuevas claves no coinciden.")
            self.error.show()
            return

        self.busy=True;self.save_btn.setEnabled(False)
        def update():
            try:result=(self.auth.change_password(cur,new,hint),'La contraseña actual no es correcta o debes esperar tras varios intentos.')
            except Exception:result=(False,'No se pudo actualizar la contraseña.')
            try:self.checked.emit(*result)
            except RuntimeError:pass
        threading.Thread(target=update,name='victor-password-change',daemon=True).start()
    def _saved(self,success,message):
        self.busy=False;self.save_btn.setEnabled(True)
        if success:self.accept()
        else:self.error.setText(message);self.error.show()
