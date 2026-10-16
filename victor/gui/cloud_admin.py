"""Read-only admin view; server RLS, not the presence of this widget, grants access."""
import threading
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QPushButton,QTableWidget,QTableWidgetItem,QAbstractItemView,QComboBox,QHBoxLayout

class CloudAdmin(QDialog):
    loaded=Signal(object,str)
    def __init__(self,auth,parent=None):
        super().__init__(parent);self.auth=auth;self.setWindowTitle('Administración · VICTOR');self.resize(820,500)
        layout=QVBoxLayout(self);self.status=QLabel('Cuentas y últimos accesos. No se muestran contraseñas ni claves de IA.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.offset=0;self.mode=QComboBox();self.mode.addItems(['Cuentas registradas','Historial de accesos']);self.mode.currentIndexChanged.connect(self.reset_page);layout.addWidget(self.mode)
        self.table=QTableWidget(0,4);self.table.setHorizontalHeaderLabels(['Correo','Registro','Último acceso','Versión']);self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);layout.addWidget(self.table)
        self.refresh=QPushButton('Actualizar lista');self.refresh.clicked.connect(self.load);layout.addWidget(self.refresh);self.loaded.connect(self.present);self.load()
        pages=QHBoxLayout();self.previous=QPushButton('Anterior');self.next=QPushButton('Siguiente');self.previous.clicked.connect(lambda:self.page(-200));self.next.clicked.connect(lambda:self.page(200));pages.addWidget(self.previous);pages.addWidget(self.next);layout.addLayout(pages);self.previous.setEnabled(False);self.next.setEnabled(False)
    def reset_page(self):self.offset=0;self.load()
    def page(self,delta):self.offset=max(0,self.offset+delta);self.load()
    def load(self):
        if not self.auth.authenticated:return
        self.refresh.setEnabled(False)
        self.mode.setEnabled(False)
        if hasattr(self,'next'):self.next.setEnabled(False);self.previous.setEnabled(False)
        history=self.mode.currentIndex()==1;offset=self.offset
        def run():
            try:
                if not self.auth.is_admin():raise ValueError('Esta cuenta no es administradora.')
                rows=self.auth.admin_events(offset) if history else self.auth.admin_profiles(offset);error=''
                if not isinstance(rows,list) or len(rows)>200:raise ValueError('Respuesta inválida.')
            except Exception:rows=[];error='No se pudo acceder al panel. Verifica tu cuenta administradora y la conexión.'
            try:self.loaded.emit(rows,error)
            except RuntimeError:pass
        threading.Thread(target=run,name='victor-admin-read',daemon=True).start()
    def present(self,rows,error):
        self.refresh.setEnabled(True);self.mode.setEnabled(True);self.table.setRowCount(0);history=self.mode.currentIndex()==1
        if not self.auth.authenticated:self.close();return
        self.status.setText(error or f'Registros {self.offset+1}–{self.offset+len(rows)}.');self.previous.setEnabled(self.offset>0);self.next.setEnabled(len(rows)==200)
        self.table.setHorizontalHeaderLabels(['Correo','Acceso','Versión',''] if history else ['Correo','Registro','Último acceso','Versión'])
        for row,data in enumerate(rows):
            self.table.insertRow(row)
            values=[(data.get('profiles') or {}).get('email'),data.get('occurred_at'),data.get('app_version'),''] if history else [data.get(key) for key in ('email','created_at','last_login_at','app_version')]
            for column,value in enumerate(values):self.table.setItem(row,column,QTableWidgetItem(str(value or '—')))
        self.table.resizeColumnsToContents()
