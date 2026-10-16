"""Tests unitarios para el Orbe de Escritorio, Autenticación y Mejoras de Interfaz."""
import unittest
import tempfile
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication
from victor.auth import AuthManager
from victor.config import ConfigManager
from victor.gui.desktop_orb import DesktopVoiceOrb
from victor.gui.login import LoginOverlay
from victor.gui.app import GUIManager


class TestV8Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def test_auth_manager_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            auth = AuthManager(Path(tmp))
            self.assertFalse(auth.is_configured())
            self.assertFalse(auth.verify("cualquiera"))

            # Configuración inicial
            with self.assertRaises(ValueError):
                auth.setup("123")  # Muy corta

            self.assertTrue(auth.setup("claveSegura123", hint="mi pista"))
            self.assertTrue(auth.is_configured())
            self.assertEqual(auth.get_hint(), "mi pista")

            # Verificación
            self.assertTrue(auth.verify("claveSegura123"))
            self.assertFalse(auth.verify("claveErronea"))

            # Sesión recordada
            self.assertFalse(auth.check_saved_session())
            token = auth.save_session(remember_days=7)
            self.assertTrue(bool(token))
            self.assertTrue(auth.check_saved_session())

            auth.logout()
            self.assertFalse(auth.check_saved_session())

            # Cambio de contraseña
            self.assertFalse(auth.change_password("claveViejaErronea", "nuevaClave456"))
            self.assertTrue(auth.change_password("claveSegura123", "nuevaClave456"))
            self.assertTrue(auth.verify("nuevaClave456"))

    def test_desktop_voice_orb(self):
        orb = DesktopVoiceOrb()
        self.assertIsNotNone(orb)
        self.assertEqual(orb.width(), 110)
        self.assertEqual(orb.height(), 110)

        # Verificación de flags no táctiles
        from PySide6.QtCore import Qt
        self.assertTrue(bool(orb.windowFlags() & Qt.WindowType.FramelessWindowHint))
        self.assertTrue(bool(orb.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
        self.assertFalse(bool(orb.windowFlags() & Qt.WindowType.WindowTransparentForInput))
        self.assertTrue(bool(orb.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus))

        # Reactividad de audio
        orb.set_user_level(0.85)
        self.assertAlmostEqual(orb.mic_target, 0.85)
        orb.tick()
        self.assertGreater(orb.mic_level, 0.0)

        orb.set_bot_level(0.65)
        self.assertAlmostEqual(orb.tts_target, 0.65)
        orb.tick()
        self.assertGreater(orb.tts_level, 0.0)

        # Estados
        for state in ("Listo", "Escuchando", "Pensando", "Respondiendo"):
            orb.set_state(state)
            self.assertEqual(orb.state, state)
            orb.tick()

        orb.close()

    def test_login_overlay_and_gui_integration(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            cfg = ConfigManager(folder)
            app = GUIManager(cfg)
            try:
                # Al no estar configurado, debe mostrar loginOverlay
                self.assertFalse(app.auth.is_configured())
                self.assertIs(app.window_stack.currentWidget(), app.login_overlay)

                # Configurar clave a través del overlay
                app.login_overlay.pass_input.setText("miClave2026")
                app.login_overlay.user_input.setText('Usuario de prueba')
                app.login_overlay.confirm_input.setText("miClave2026")
                app.login_overlay.hint_input.setText("año actual")
                app.login_overlay.submit()
                deadline=time.monotonic()+3
                while app.login_overlay.busy and time.monotonic()<deadline:self.qt.processEvents();time.sleep(.01)

                # Debe desbloquear y mostrar la app principal
                self.assertTrue(app.auth.is_configured())
                self.assertIs(app.window_stack.currentWidget(), app.main_app_widget)

                # Probar bloqueo manual
                app.lock_session()
                self.assertIs(app.window_stack.currentWidget(), app.login_overlay)

                # Probar login con clave correcta
                app.login_overlay.pass_input.setText("miClave2026")
                app.login_overlay.submit()
                deadline=time.monotonic()+3
                while app.login_overlay.busy and time.monotonic()<deadline:self.qt.processEvents();time.sleep(.01)
                self.assertIs(app.window_stack.currentWidget(), app.main_app_widget)

                # Probar orbe y toggle
                self.assertTrue(hasattr(app, 'desktop_orb'))
                self.assertTrue(hasattr(app, 'orb_btn'))
                self.assertTrue(app.desktop_orb.isVisible())
                app.toggle_desktop_orb()
                self.assertFalse(app.desktop_orb.isVisible())
                app.toggle_desktop_orb()
                self.assertTrue(app.desktop_orb.isVisible())

            finally:
                app.close()
                deadline=time.monotonic()+10
                while not app.closed_cleanly and time.monotonic()<deadline:self.qt.processEvents();time.sleep(.01)


if __name__ == "__main__":
    unittest.main()
