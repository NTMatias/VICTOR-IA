"""Local access and desktop orb checks with disposable, fictitious profiles."""
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock
from PySide6.QtWidgets import QApplication
from victor.auth import AuthManager
from victor.gui.desktop_orb import DesktopVoiceOrb
from victor.config import ConfigManager
from victor.core import VictorCore

class Access(unittest.TestCase):
    def test_plaintext_expiry_is_not_a_saved_session(self):
        with tempfile.TemporaryDirectory() as folder:
            auth=AuthManager(Path(folder));auth.setup('fictitious-password');auth.lock_session()
            auth.session_file.write_text(json.dumps({'expiry':time.time()+86400,'token':'forged'}))
            self.assertFalse(auth.check_saved_session());self.assertFalse(auth.authenticated)
    def test_damaged_profile_does_not_allow_password_replacement(self):
        with tempfile.TemporaryDirectory() as folder:
            auth=AuthManager(Path(folder));auth.auth_file.write_text('{broken')
            self.assertTrue(auth.is_configured());self.assertFalse(auth.verify('fictitious'))
            with self.assertRaises(ValueError):auth.setup('new-fictitious-password')
            self.assertEqual(auth.auth_file.read_text(),'{broken')
    def test_session_is_ciphertext_and_invalidated_by_password_change(self):
        with tempfile.TemporaryDirectory() as folder:
            auth=AuthManager(Path(folder));auth.setup('fictitious-password',username='Ana de prueba')
            token=auth.save_session();self.assertNotIn(token.encode(),auth.session_file.read_bytes())
            self.assertTrue(auth.check_saved_session())
            auth.change_password('fictitious-password','replacement-password')
            self.assertFalse(auth.check_saved_session());self.assertEqual(auth.username(),'Ana de prueba')
    def test_password_not_stored_and_backoff(self):
        with tempfile.TemporaryDirectory() as folder:
            auth=AuthManager(Path(folder));auth.setup('fictitious-password');auth.lock_session()
            self.assertNotIn('fictitious-password',auth.auth_file.read_text())
            for _ in range(5):self.assertFalse(auth.verify('wrong-password'))
            self.assertGreater(auth.retry_after,time.monotonic());self.assertFalse(auth.verify('fictitious-password'))
    def test_locked_core_and_registry_do_not_execute(self):
        with tempfile.TemporaryDirectory() as folder:
            core=VictorCore(ConfigManager(Path(folder)),lambda *args:None)
            try:
                core.access_check=lambda:False;core.registry.access_check=lambda:False
                self.assertFalse(core.submit('Abre calculadora',1));self.assertFalse(core.busy.is_set())
                self.assertFalse(core.registry.execute('get_system_info',{})['ok'])
            finally:core.ai.close()

class Orb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.qt=QApplication.instance() or QApplication([])
    def test_idle_is_static_voice_activates_then_stops(self):
        orb=DesktopVoiceOrb()
        try:
            orb.show();self.qt.processEvents();self.assertFalse(orb.render_timer.isActive())
            orb.set_user_level(.8);self.assertTrue(orb.render_timer.isActive());orb.tick();self.assertGreater(orb.mic_level,0)
            orb.set_user_level(0)
            for _ in range(30):orb.tick()
            self.assertFalse(orb.render_timer.isActive());orb.set_state('Pensando');self.assertFalse(orb.render_timer.isActive())
            orb.set_bot_level(.5);orb.tick();self.assertGreater(orb.tts_level,0);orb.hide();self.assertFalse(orb.render_timer.isActive())
        finally:orb.close()
    def test_corners_stay_in_available_screen_and_no_focus(self):
        from PySide6.QtCore import Qt
        orb=DesktopVoiceOrb()
        try:
            for corner in ('bottom-right','bottom-left','top-right','top-left'):
                orb.reposition(corner);self.assertTrue(self.qt.primaryScreen().availableGeometry().contains(orb.geometry()))
            self.assertTrue(orb.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus)
            orb.set_user_level(float('nan'));self.assertEqual(orb.mic_target,0)
        finally:orb.close()

if __name__=='__main__':unittest.main()
