import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QScrollArea, QLabel, QPushButton, QLineEdit, QPlainTextEdit, QComboBox, QCheckBox, QMessageBox
from victor.config import PROVIDERS
from victor.errors import VictorError


class SettingsManager(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app, self.fields = app, {}
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        form = QFormLayout(body)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        cfg = app.config.snapshot()
        choices = {"provider": PROVIDERS, "vision_provider": PROVIDERS, "theme": ("Dark", "Light", "System"),
                   "security": ("normal", "strict"), "voice_mode": ("manual", "push-to-talk", "continua"),
                   "voice_backend": ("whisper", "google"), "ollama_gpu": ("auto", "cpu"), "tts_backend": ("edge", "sapi"), "remote_high_policy": ("block", "pc")}
        labels = {"provider": "Proveedor", "models": "Modelos por proveedor", "fallback": "Orden de respaldo (JSON)",
                  "ollama_light": "Modo ligero: qwen2.5:3b", "ollama_gpu": "Ollama: auto GPU / CPU", "ollama_timeout": "Timeout Ollama (segundos)",
                  "ollama_context": "Contexto Ollama (tokens)", "ollama_keep_alive": "Mantener modelo cargado", "applications": "Alias de aplicaciones (JSON)",
                  "allowed_folders": "Carpetas autorizadas (JSON)", "system_prompt": "Instrucciones personales", "voice_backend": "Reconocimiento de voz",
                  "voice_mode": "Modo de escucha", "wake_word": "Palabra de activación", "voice_enabled": "Leer respuestas en voz alta"}
        for key, value in cfg.items():
            if key == "models":
                for provider in PROVIDERS:
                    widget = QLineEdit(value[provider])
                    self.fields["model:"+provider] = widget
                    form.addRow("Modelo " + provider, widget)
                continue
            if isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(value)
            elif key in choices:
                widget = QComboBox()
                widget.addItems(choices[key])
                widget.setCurrentText(str(value))
            elif isinstance(value, (list, dict)) or key in ("system_prompt", "personality"):
                widget = QPlainTextEdit(json.dumps(value, ensure_ascii=False, indent=2) if isinstance(value, (list, dict)) else value)
                widget.setFixedHeight(90)
            else:
                widget = QLineEdit(str(value))
            self.fields[key] = widget
            form.addRow(labels.get(key, key.replace("_", " ")), widget)
        scroll.setWidget(body)
        layout.addWidget(scroll)
        self.error = QLabel("Claves únicamente en .env o variables de entorno.")
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        save = QPushButton("Guardar configuración")
        save.clicked.connect(self.save)
        layout.addWidget(save)

    def save(self):
        if self.app.core.busy.is_set():
            self.error.setText("Espera a que termine el turno.")
            return
        try:
            old = self.app.config.snapshot()
            values, models = {}, {}
            for key, widget in self.fields.items():
                if key.startswith("model:"):
                    models[key[6:]] = widget.text().strip()
                    continue
                if isinstance(widget, QCheckBox):
                    value = widget.isChecked()
                elif isinstance(widget, QComboBox):
                    value = widget.currentText()
                else:
                    raw = widget.toPlainText() if isinstance(widget, QPlainTextEdit) else widget.text()
                    value = json.loads(raw) if isinstance(old[key], (dict, list)) else int(raw) if isinstance(old[key], int) else float(raw) if isinstance(old[key], float) else raw.strip()
                values[key] = value
            values["models"] = models
            self.app.config.validate({**old, **values})
            if any(values[k] != old[k] for k in ("security", "applications", "allowed_folders", "telegram_allowed_ids", "remote_high_policy", "remote_block_all")):
                if QMessageBox.question(self, "Cambiar permisos", "¿Guardar estos cambios en permisos y aplicaciones autorizadas?") != QMessageBox.StandardButton.Yes:
                    return
            self.app.voice_input.stop()
            self.app.config.save(values)
            self.app.refresh_config()
            self.error.setText("Configuración guardada. Reinicia para cambios de integraciones.")
        except VictorError as exc:
            self.error.setText(str(exc))
        except (ValueError, TypeError):
            self.error.setText("Revisa los números y el formato JSON de listas y aplicaciones.")
        except Exception:
            self.error.setText("No se pudo guardar la configuración. Revisa el registro local.")


def example_args(schema):
    return {k: p["enum"][0] if "enum" in p else None if p["type"] == ["array", "null"] else
            p.get("minimum", 0) if p["type"] == "integer" else ["ctrl", "a"] if p["type"] == "array" else ""
            for k, p in schema["properties"].items()}
