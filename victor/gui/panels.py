import json
import tkinter.messagebox as messagebox
import customtkinter as ctk
from victor.config import PROVIDERS
from victor.errors import VictorError


class SettingsManager(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("VICTOR.IA · Configuración")
        self.geometry("790x760")
        self.transient(app)
        self.fields = {}
        ctk.CTkLabel(self, text="Tu asistente, tus preferencias", font=("Segoe UI", 22, "bold")).pack(pady=15)
        self.body = ctk.CTkScrollableFrame(self)
        self.body.pack(fill="both", expand=True, padx=20)
        cfg = app.config.snapshot()
        self.body.grid_columnconfigure(1, weight=1)
        rows = [
            ("provider", "Proveedor principal", PROVIDERS),
            *[("model:"+p, "Modelo "+p, None) for p in PROVIDERS],
            ("fallback", "Fallback (orden, separado por comas)", None),
            ("temperature", "Temperatura (0–2)", None), ("max_tokens", "Máximo de tokens de salida", None),
            ("name", "Nombre del asistente", None), ("personality", "Personalidad", "text"),
            ("formality", "Formalidad", None), ("language", "Idioma / reconocimiento (es-EC)", None),
            ("system_prompt", "Instrucciones personales", "text"),
            ("theme", "Tema", ("Dark", "Light", "System")), ("security", "Seguridad (strict confirma todo)", ("normal", "strict")),
            ("voice_mode", "Modo de micrófono", ("manual", "push-to-talk", "continua")),
            ("voice_backend", "Reconocimiento", ("google", "whisper")),
            ("wake_word", "Palabra de activación", None), ("voice_rate", "Velocidad de voz", None),
            ("voice_id", "ID de voz SAPI (vacío = automático)", None), ("microphone", "ID micrófono (vacío = predeterminado)", None),
            ("whisper_model", "Modelo Whisper local / ruta", None),
            ("vision_provider", "Proveedor de visión", PROVIDERS), ("vision_model", "Modelo compatible con visión", None),
            ("ollama_url", "Servidor Ollama local", None), ("context_chars", "Presupuesto de contexto (caracteres)", None),
            ("network_timeout", "Timeout de red (segundos)", None),
            ("allowed_folders", "Carpetas autorizadas (una ruta absoluta por línea)", "text"),
            ("applications", 'Apps: JSON {"alias": "C:/ruta/app.exe"}', "text"),
        ]
        for index, (key, label, choices) in enumerate(rows):
            ctk.CTkLabel(self.body, text=label, anchor="w", wraplength=280).grid(row=index, column=0, sticky="w", padx=8, pady=8)
            value = cfg["models"][key[6:]] if key.startswith("model:") else cfg[key]
            if key == "fallback":
                value = ", ".join(value)
            elif key == "allowed_folders":
                value = "\n".join(value)
            elif key == "applications":
                value = json.dumps(value, ensure_ascii=False, indent=2)
            if choices == "text":
                widget = ctk.CTkTextbox(self.body, height=95, wrap="word")
                widget.insert("1.0", str(value))
            elif choices:
                widget = ctk.CTkOptionMenu(self.body, values=list(choices))
                widget.set(value)
            else:
                widget = ctk.CTkEntry(self.body)
                widget.insert(0, str(value))
            widget.grid(row=index, column=1, sticky="ew", padx=8, pady=6)
            self.fields[key] = widget
        self.search_var = ctk.BooleanVar(value=cfg["auto_search"])
        ctk.CTkCheckBox(self.body, text="Buscar automáticamente información actual", variable=self.search_var).grid(row=len(rows), columnspan=2, pady=15)
        self.error = ctk.CTkLabel(self, text="Las claves se leen únicamente desde .env o variables de entorno.", wraplength=730)
        self.error.pack(pady=8)
        ctk.CTkButton(self, text="Guardar configuración", command=self.save).pack(pady=(0, 18))

    def save(self):
        if self.app.core.busy.is_set():
            self.error.configure(text="Espera a que finalice el turno antes de cambiar la configuración.")
            return
        try:
            values = {}
            models = {}
            for key, widget in self.fields.items():
                raw = widget.get("1.0", "end-1c") if isinstance(widget, ctk.CTkTextbox) else widget.get()
                if key.startswith("model:"):
                    models[key[6:]] = raw.strip()
                elif key in ("max_tokens", "voice_rate", "context_chars", "network_timeout"):
                    values[key] = int(raw)
                elif key == "temperature":
                    values[key] = float(raw)
                elif key == "fallback":
                    values[key] = [p.strip() for p in raw.split(",") if p.strip()]
                elif key == "allowed_folders":
                    values[key] = [p.strip().strip('"') for p in raw.splitlines() if p.strip()]
                elif key == "applications":
                    values[key] = json.loads(raw)
                else:
                    values[key] = raw.strip()
            values["models"] = models
            values["auto_search"] = self.search_var.get()
            self.app.config.validate({**self.app.config.snapshot(), **values})
            sensitive = any(values[k] != self.app.config.get(k) for k in ("allowed_folders", "applications", "security"))
            if sensitive and not messagebox.askyesno("Cambiar permisos", "Vas a cambiar carpetas, aplicaciones autorizadas o política de seguridad.\n\n¿Guardar estos permisos?", parent=self):
                return
            self.app.voice_input.stop()
            self.app.config.save(values)
            ctk.set_appearance_mode(values["theme"])
            self.app.refresh_config()
            self.destroy()
        except (ValueError, TypeError, VictorError) as exc:
            self.error.configure(text=str(exc), text_color="#ef6b6b")
        except OSError:
            self.error.configure(text="No se pudo guardar la configuración. Comprueba el acceso a data/.")


def example_args(schema):
    result = {}
    for key, prop in schema["properties"].items():
        if "enum" in prop:
            value = prop["enum"][0]
        elif prop["type"] == ["array", "null"]:
            value = None
        elif prop["type"] == "integer":
            value = prop.get("minimum", 0)
        elif prop["type"] == "array":
            value = ["ctrl", "a"]
        else:
            value = ""
        result[key] = value
    return result
