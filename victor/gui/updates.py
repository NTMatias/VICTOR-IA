"""Non-blocking release notification and download progress."""
import threading
from PySide6.QtCore import Signal,QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QPushButton,QProgressBar

class UpdateDialog(QDialog):
    completed=Signal(object,str)
    def __init__(self,manager,record,parent=None):
        super().__init__(parent);self.manager=manager;self.record=record;self.setWindowTitle('Nueva versión de VICTOR');self.resize(460,230)
        layout=QVBoxLayout(self);self.status=QLabel(f"Está disponible VICTOR {record['version']}. Puedes seguir usando esta versión mientras se descarga.");self.status.setWordWrap(True);layout.addWidget(self.status)
        self.progress=QProgressBar();self.progress.setRange(0,100);layout.addWidget(self.progress)
        self.button=QPushButton('Descargar versión verificada');self.button.clicked.connect(self.download);layout.addWidget(self.button)
        self.completed.connect(self.done_download)
    def download(self):
        self.button.setEnabled(False)
        def run():
            try:path=self.manager.download(self.record);error=''
            except Exception as exc:path=None;error=str(exc) if isinstance(exc,ValueError) else 'No se pudo descargar. Comprueba Internet e inténtalo de nuevo.'
            try:self.completed.emit(path,error)
            except RuntimeError:pass
        threading.Thread(target=run,name='victor-update-download',daemon=True).start()
    def done_download(self,path,error):
        self.button.setEnabled(True)
        if error:self.status.setText(error);return
        self.progress.setValue(100);self.status.setText('Descarga verificada. Abre la carpeta para instalar la nueva versión. No se sobrescribieron tus cuentas ni conversaciones.')
        self.button.setText('Abrir carpeta de descarga');self.button.clicked.disconnect();self.button.clicked.connect(lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent))))
