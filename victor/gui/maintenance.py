"""Preparación local y auditoría; no consulta ni muestra valores de credenciales."""
import json
import os
import re
import sys
from pathlib import Path
from PySide6.QtCore import QProcess, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar, QListWidget
from victor.gui.widgets import AdaptiveButton
from victor.config import KEYS
from victor.errors import VictorError
from victor.voice.models import model_directory


def audit_rows(path, risks):
    """Lee un sufijo acotado del log y solo extrae campos reconocidos."""
    try:
        with Path(path).open('rb') as stream:
            stream.seek(0, 2)
            stream.seek(max(0, stream.tell() - 262144))
            lines = stream.read().decode('utf-8', errors='replace').splitlines()
    except OSError:
        return []
    rows = [];risks=dict(risks)
    for line in lines:
        requested=re.search(r'confirmation requested action=(\w+) risk=(LOW|MEDIUM|HIGH)',line)
        if requested:risks[requested.group(1)]=requested.group(2)
        confirmation = re.search(r'confirmation result action=(\w+) accepted=(True|False)', line)
        execution = re.search(r'tool=(\w+) result=(success|failed|schema_error)', line)
        if confirmation:
            tool, accepted = confirmation.groups()
            status = ('Directa (sin diálogo)' if 'authorization=owner_direct_mode' in line else 'Confirmada') if accepted == 'True' else 'Rechazada / cancelada'
        elif execution:
            tool, result = execution.groups()
            status = 'Ejecutada' if result == 'success' else 'Falló'
        else:
            continue
        if tool not in risks:
            continue
        recorded=re.search(r'risk=(LOW|MEDIUM|HIGH)',line)
        risk=recorded.group(1) if recorded else risks[tool]
        rows.append(f'{line[:19]} · {tool} · {risk} · {status}')
    return rows[-20:]


class MaintenancePanel(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.ready = False
        self.checked_name = None
        self.buffer = ''
        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(app.config.root))
        # Módulo importable también cuando las pruebas usan una raíz temporal.
        from PySide6.QtCore import QProcessEnvironment
        env = QProcessEnvironment.systemEnvironment()
        env.insert('PYTHONPATH', str(Path(__file__).resolve().parents[2]))
        self.process.setProcessEnvironment(env)
        self.probe = QProcess(self)
        self.probe.setProcessEnvironment(env)
        self.probe_buffer = ''
        self.probe_rows = {}
        self.probe.readyReadStandardOutput.connect(self.read_probe)
        self.probe.readyReadStandardError.connect(lambda: self.probe.readAllStandardError())
        self.probe.finished.connect(self.probe_finished)
        self.probe.errorOccurred.connect(lambda _: self.readiness.setText('No pude iniciar el diagnóstico.'))
        self.probe_deadline = QTimer(self);self.probe_deadline.setSingleShot(True)
        self.probe_deadline.timeout.connect(self.probe_timeout)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(lambda: self.process.readAllStandardError())
        self.process.finished.connect(self.finished)
        self.process.errorOccurred.connect(lambda _: self.label.setText('No pude iniciar la preparación del modelo.'))
        self.deadline = QTimer(self);self.deadline.setSingleShot(True)
        self.deadline.timeout.connect(self.timeout)
        from victor.gui.panels import Columns,card,notice,label
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        left,right=QWidget(),QWidget();ll,rl=QVBoxLayout(left),QVBoxLayout(right)
        for column in (ll,rl):column.setContentsMargins(0,0,0,0);column.setSpacing(12)
        model,ml=card('Whisper local · preparación de voz')
        self.label = QLabel('Comprobando modelo de voz…');self.label.setWordWrap(True)
        ml.addWidget(self.label)
        self.download = AdaptiveButton('Descargar modelo de voz (base: ~150 MB)')
        self.download.clicked.connect(lambda: self.launch('download'));ml.addWidget(self.download)
        self.bar = QProgressBar();self.bar.setRange(0, 0);ml.addWidget(self.bar)
        ll.addWidget(model)
        services,sl=card('Comprobación de servicios')
        refresh = AdaptiveButton('¿Estoy listo? · comprobar conexiones')
        refresh.setToolTip('Hace una consulta breve al modelo de IA y consulta servicios sin ejecutar acciones.')
        refresh.clicked.connect(self.check_connections);sl.addWidget(refresh)
        self.readiness = QLabel();self.readiness.setWordWrap(True);sl.addWidget(self.readiness);ll.addWidget(services);ll.addStretch()
        actions,al=card('Registro de actividad · últimas 20 acciones')
        self.audit = QListWidget();self.audit.setMinimumHeight(280);al.addWidget(self.audit);rl.addWidget(actions)
        notes,nl=card('Verificación real');nl.addWidget(notice('Una cuenta guardada no confirma conectividad. El diagnóstico consulta servicios, pero no ejecuta herramientas ni muestra claves. Micrófono, pantalla y celular requieren pruebas en tu escritorio.'));rl.addWidget(notes);rl.addStretch()
        layout.addWidget(Columns(left,right))
        self.timer = QTimer(self);self.timer.timeout.connect(self.refresh_audit);self.timer.start(3000)
        QTimer.singleShot(0, self.refresh)

    def launch(self, mode):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            return
        self.ready = False
        self.checked_name = self.app.config.get('whisper_model')
        self.download.setEnabled(False);self.bar.show();self.bar.setRange(0, 0)
        self.label.setText('Descargando modelo… el chat sigue disponible.' if mode == 'download' else 'Comprobando caché local…')
        self.buffer = ''
        self.process.start(sys.executable, ['-m', 'victor.voice.models', mode, self.checked_name,
                                           str(model_directory(self.app.config))])
        self.deadline.start(30 * 60 * 1000 if mode == 'download' else 30000)

    def timeout(self):
        self.process.kill()
        self.label.setText('La preparación tardó demasiado. Revisa la conexión o vuelve a intentarlo.')

    def read_output(self):
        self.buffer += bytes(self.process.readAllStandardOutput()).decode('utf-8', errors='replace')
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            try:
                data = json.loads(line)
            except ValueError:
                continue
            if 'ready' in data:
                self.ready = data['ready']
                self.label.setText('Modelo local disponible.' if self.ready else 'Falta el modelo. La voz local está deshabilitada; puedes usar el chat.')
            elif 'error' in data:
                self.label.setText(data['error'])
            elif 'progress' in data:
                self.label.setText(f"Descargando: {data['progress']} / {data.get('total') or '?'} {data.get('unit', '')}")
                if data.get('unit') == 'B' and data.get('total'):
                    self.bar.setRange(0, 100)
                    self.bar.setValue(min(100, int(data['progress'] * 100 / data['total'])))

    def finished(self, code, status):
        self.deadline.stop()
        self.read_output();self.bar.hide();self.download.setEnabled(True)
        self.download.setVisible(not self.ready)
        if code and 'Descargando' in self.label.text():
            self.label.setText('Descarga interrumpida. Puedes reintentar sin bloquear el chat.')
        self.show_readiness()

    def refresh(self):
        self.launch('check');self.refresh_audit();self.show_readiness()

    def check_connections(self):
        if self.probe.state() != QProcess.ProcessState.NotRunning:
            return
        self.probe_buffer = ''
        self.probe_rows = {name: '⚠️ ' + name + ': comprobando…' for name in ('IA', 'Whisper', 'Spotify', 'Google', 'Telegram')}
        self.readiness.setText('\n'.join(self.probe_rows.values()))
        self.probe.start(sys.executable, ['-m', 'victor.diagnostics', str(self.app.config.root)])
        self.probe_deadline.start(90000)

    def read_probe(self):
        self.probe_buffer += bytes(self.probe.readAllStandardOutput()).decode('utf-8', errors='replace')
        while '\n' in self.probe_buffer:
            line, self.probe_buffer = self.probe_buffer.split('\n', 1)
            try:
                row = json.loads(line)
                if row['service'] in self.probe_rows:
                    self.probe_rows[row['service']] = row['text']
            except (ValueError, KeyError, TypeError):
                continue
        self.readiness.setText('\n'.join(self.probe_rows.values()))

    def probe_timeout(self):
        self.probe.kill()

    def probe_finished(self, code, status):
        self.probe_deadline.stop();self.read_probe()
        for name, text in self.probe_rows.items():
            if text.endswith('comprobando…'):
                self.probe_rows[name] = '⚠️ ' + name + ': diagnóstico interrumpido; sin verificar'
        self.readiness.setText('\n'.join(self.probe_rows.values()))

    def show_readiness(self):
        if self.probe_rows:
            self.probe_rows['Whisper'] = '✅ Whisper: archivos locales disponibles; micrófono sin comprobar' if self.ready else '⚠️ Whisper: modelo pendiente / comprobando'
            self.readiness.setText('\n'.join(self.probe_rows.values()))
            return
        cfg = self.app.config
        provider = cfg.get('provider')
        key = KEYS.get(provider)
        try:
            ai = '⚠️ IA: Ollama seleccionado; conexión sin comprobar' if not key else ('⚠️ IA: clave configurada; conexión sin comprobar' if cfg.api_key(provider) else f'❌ IA: falta {key}; añádela en Ajustes → Inteligencia artificial')
        except VictorError:
            ai = '❌ IA: no se pudo leer el almacén cifrado de claves'
        lines = [ai, '✅ Whisper: archivos locales disponibles (micrófono sin comprobar)' if self.ready else '⚠️ Whisper: modelo pendiente / comprobando']
        for label, manager in [('Spotify', self.app.core.spotify), ('Google', self.app.core.google)]:
            lines.append(f'⚠️ {label}: ' + ('autorización guardada; servicio sin comprobar' if manager.cache.path.exists() else 'falta conectar la cuenta'))
        lines.append('⚠️ Telegram: ' + ('token configurado; servicio sin comprobar' if os.getenv('TELEGRAM_BOT_TOKEN') else 'falta TELEGRAM_BOT_TOKEN'))
        self.readiness.setText('\n'.join(lines))

    def refresh_audit(self):
        risks = {name: str(tool.risk.name) for name, tool in self.app.core.registry.tools.items()}
        risks.update(remote_pointer_session='MEDIUM',remote_keyboard_input='MEDIUM')
        rows = audit_rows(self.app.config.data_dir / 'victor.log', risks)
        self.audit.clear();self.audit.addItems(rows or ['Sin acciones registradas.'])

    def stop(self):
        self.timer.stop()
        self.deadline.stop()
        self.probe_deadline.stop()
        if self.probe.state() != QProcess.ProcessState.NotRunning:
            self.probe.kill()
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()

    def running(self):
        return self.process.state() != QProcess.ProcessState.NotRunning or self.probe.state() != QProcess.ProcessState.NotRunning
