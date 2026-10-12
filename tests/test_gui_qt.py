import tempfile
import time
import unittest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from victor.config import ConfigManager
from victor.gui.app import GUIManager
from victor.gui.widgets import ApprovalCard
from victor.security import Approval, Risk


class QtGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])
        cls.qt.setQuitOnLastWindowClosed(False)

    def pump(self, seconds=.1):
        until = time.monotonic()+seconds
        while time.monotonic() < until:
            self.qt.processEvents()
            time.sleep(.01)

    def test_gui_lifecycle_and_confirmations(self):
        with tempfile.TemporaryDirectory() as folder:
            app = GUIManager(ConfigManager(Path(folder)))
            try:
                app.show()
                app.resize(420, 760)
                self.pump(.3)
                self.assertTrue(app.isVisible())
                self.assertLessEqual(app.width(), 440)
                request = Approval("delete_file", "archivo de prueba", Risk.HIGH)
                card = ApprovalCard(request)
                self.assertFalse(card.approve.isEnabled())
                card.resolve(True)
                self.assertFalse(request.done.is_set())
                card.phrase.setText("EJECUTAR")
                self.assertTrue(card.approve.isEnabled())
                card.resolve(True)
                self.assertTrue(request.accepted)
                app.send("¿Cuánta RAM estoy usando?")
                deadline = time.monotonic()+8
                while app.core.busy.is_set() and time.monotonic() < deadline:
                    self.pump(.1)
                self.pump(.2)
                self.assertIn("RAM:", app.current_bubble.label.text())
                self.assertTrue(app.send_button.isEnabled())
                app.toggle_drawer(2)
                self.pump(.3)
                self.assertTrue(app.drawer.isVisible())
                self.assertIs(app.pages.currentWidget(), app.page_widgets['ia'])
                self.assertFalse(app.shell.geometry().intersects(app.sidebar.geometry()))
                self.assertLessEqual(app.current_bubble.width(), app.current_bubble.parentWidget().width() * .71)
                self.assertEqual(app.entry.height(), app.mic.height())
                self.assertEqual(app.entry.height(), app.send_button.height())
                app.resize(1120, 880)
                self.pump(.3)
                self.assertFalse(app.shell.geometry().intersects(app.sidebar.geometry()))
                widths = [b.width() for b in app.quick_buttons]
                self.assertLessEqual(max(widths)-min(widths), 2)
                app.settings.fields["name"].setText("VICTOR QT")
                app.settings.save()
                self.assertEqual(app.config.get("name"), "VICTOR QT")
            finally:
                app.close()
                deadline = time.monotonic()+10
                while not app.closed_cleanly and time.monotonic() < deadline:
                    self.pump(.1)
            self.assertTrue(app.closed_cleanly)
            self.assertFalse(app.metrics.thread.is_alive())
            self.assertFalse(app.voice_output.thread.is_alive())
