"""Capture fake login/navigation/orb states; never opens real user sessions."""
from pathlib import Path
import tempfile
import time
from PySide6.QtWidgets import QApplication
from victor.config import ConfigManager
from victor.gui.app import GUIManager

def main():
    root=Path(__file__).resolve().parents[1];output=root/'docs/desktop_preview';output.mkdir(exist_ok=True)
    qt=QApplication.instance() or QApplication([]);qt.setQuitOnLastWindowClosed(False)
    def pump(seconds):
        end=time.monotonic()+seconds
        while time.monotonic()<end:qt.processEvents();time.sleep(.01)
    with tempfile.TemporaryDirectory() as folder:
        gui=GUIManager(ConfigManager(Path(folder)))
        try:
            gui.resize(1280,900);gui.show();pump(.2);gui.grab().save(str(output/'login.png'))
            gui.auth.setup('preview-only-password',username='Usuario de prueba');gui.on_login_success();pump(.2)
            gui.grab().save(str(output/'home.png'))
            gui.desktop_orb.set_bot_level(.7);gui.desktop_orb.tick();gui.desktop_orb.grab().save(str(output/'orb.png'))
            gui.lock_session();pump(.1)
            assert not gui.auth.authenticated and not gui.desktop_orb.isVisible()
            assert gui.core.submit('No ejecutar esta petición ficticia',gui.conversation_id) is False
        finally:
            gui.close();end=time.monotonic()+10
            while not gui.closed_cleanly and time.monotonic()<end:pump(.1)
    print('Vista previa creada con datos ficticios.')

if __name__=='__main__':main()
