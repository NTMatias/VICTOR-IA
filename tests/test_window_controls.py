"""Tarjetas de acciones y transiciones de ventana, sin escritorio capturado."""
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock
from PySide6.QtCore import QPoint,QRect
from PySide6.QtWidgets import QApplication,QLabel
from victor.config import ConfigManager
from tests.gui_support import authenticated_gui as GUIManager
from victor.gui.widgets import ActionTile


class WindowControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt=QApplication.instance() or QApplication([]);cls.qt.setQuitOnLastWindowClosed(False)
    def pump(self,seconds=.15):
        end=time.monotonic()+seconds
        while time.monotonic()<end:self.qt.processEvents();time.sleep(.005)
    def wait_animation(self,app):
        end=time.monotonic()+2
        while app.window_transitions.running and time.monotonic()<end:self.pump(.02)
        self.pump(.05);self.assertFalse(app.window_transitions.running)

    def test_tiles_survive_resize_theme_and_window_transitions(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));app=GUIManager(cfg)
            try:
                app.show();app.navigate('windows');self.pump()
                self.assertEqual(list(app.window_controls),['minimize','maximize','close'])
                self.assertLess(app.window_controls['minimize'].x(),app.window_controls['maximize'].x())
                self.assertLess(app.window_controls['maximize'].x(),app.window_controls['close'].x())
                image=app.window_controls['minimize'].grab().toImage();point=image.pixelColor(22,15)
                self.assertLess(max(point.red(),point.green(),point.blue())-min(point.red(),point.green(),point.blue()),20)
                self.assertGreater(point.red(),150)
                for theme in ('Dark','Light','Dark'):
                    cfg.save({'theme':theme});app.refresh_config()
                    for width in (1920,420,1600):
                        app.resize(width,1040 if width==1920 else 900);self.pump(.2)
                        for key,count in [('windows',4),('files',8)]:
                            app.navigate(key);self.pump(.1);page=app.page_widgets[key];tiles=page.findChildren(ActionTile)
                            self.assertEqual(len(tiles),count);self.assertEqual(page.horizontalScrollBar().maximum(),0)
                            for tile in tiles:
                                self.assertGreaterEqual(tile.height(),80)
                                for text in tile.findChildren(QLabel):
                                    if text.text():
                                        self.assertGreaterEqual(text.height(),text.fontMetrics().height(),(theme,width,text.text()))
                                        bounds=QRect(text.mapTo(tile,QPoint()),text.size())
                                        self.assertTrue(tile.rect().contains(bounds),(theme,width,text.text(),bounds,tile.rect()))
                app.navigate('windows');app.sections.task=Mock()
                settings=next(t for t in app.page_widgets['windows'].findChildren(ActionTile) if t.accessibleName()=='Configuración')
                settings.click();app.sections.task.assert_called_once_with('open_settings',{},app.sections.windows_output)
                original=QRect(app.geometry());app.window_controls['maximize'].click()
                self.assertTrue(app.window_transitions.running);self.assertTrue(app.window_transitions.overlay.isVisible())
                self.assertFalse(app.window_transitions.start('minimize'))
                self.pump(.1);self.assertNotEqual(app.window_transitions.overlay.geometry(),original)
                self.wait_animation(app);self.assertTrue(app.isMaximized());self.assertIsNone(app.window_transitions.overlay)
                app.window_controls['maximize'].click();self.wait_animation(app);self.assertFalse(app.isMaximized())
                self.assertEqual(app.geometry().size(),original.size())
                app.window_controls['minimize'].click();self.pump(.1)
                self.assertGreater(app.window_transitions.overlay.windowOpacity(),0.)
                self.assertLess(app.window_transitions.overlay.windowOpacity(),1.)
                self.wait_animation(app);self.assertTrue(app.isMinimized())
                app.showNormal();self.pump(.03);self.wait_animation(app);self.assertFalse(app.isMinimized())
                self.assertIn('restore_minimized',app.window_transitions.completed)
                app.window_controls['close'].click();self.assertTrue(app.window_transitions.running)
                end=time.monotonic()+10
                while not app.closed_cleanly and time.monotonic()<end:self.pump(.05)
                self.assertTrue(app.closed_cleanly);self.assertIn('close',app.window_transitions.completed)
                self.assertFalse(app.tool_worker.thread.is_alive());self.assertFalse(app.voice_output.thread.is_alive())
            finally:
                if not app.closed_cleanly:
                    app.close();end=time.monotonic()+10
                    while not app.closed_cleanly and time.monotonic()<end:self.pump(.1)


if __name__=='__main__':unittest.main()
