from __future__ import annotations
import json
import logging
import queue
import time
import tkinter.messagebox as messagebox
import customtkinter as ctk
from victor.config import PROVIDERS
from victor.core import VictorCore
from victor.gui.widgets import ApprovalDialog
from victor.gui.panels import SettingsManager, example_args
from victor.voice.input import VoiceInput
from victor.voice.output import VoiceOutput


class GUIManager(ctk.CTk):
    def __init__(self, config):
        ctk.set_appearance_mode(config.get("theme"))
        ctk.set_default_color_theme("blue")
        super().__init__()
        self.config = config
        self.events = queue.Queue()
        self.core = VictorCore(config, self.emit)
        self.voice_output = VoiceOutput(config, self.emit)
        self.voice_input = VoiceInput(config, self.emit, lambda: not self.core.busy.is_set() and not self.voice_output.speaking.is_set())
        self.approval = None
        self.closing = False
        self.streaming_start = None
        self.partial = ""
        self.settings_window = None
        self.history_map, self.memory_map = [], []
        self.title("VICTOR.IA · Asistente de escritorio")
        self.geometry("1260x830")
        self.minsize(1020, 700)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_chat()
        self._build_inspector()
        rows = self.core.history.list()
        self.conversation_id = rows[0]["id"] if rows else self.core.history.create()
        self.load_conversation(self.conversation_id)
        self.refresh_history()
        self.refresh_memories()
        self.refresh_config()
        if config.warning:
            self.error_label.configure(text=config.warning)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.report_callback_exception = self.callback_error
        self.after(50, self.poll)
        self.pulse = 0
        self.after(700, self.animate)

    def emit(self, kind, payload):
        self.events.put((kind, payload))

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=215, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        ctk.CTkLabel(sidebar, text="V I C T O R . I A", font=("Segoe UI", 23, "bold"), text_color="#19c4b0").pack(padx=16, pady=(27, 3))
        ctk.CTkLabel(sidebar, text="ASISTENTE PERSONAL", font=("Segoe UI", 10)).pack(pady=(0, 25))
        ctk.CTkButton(sidebar, text="＋ Nueva conversación", command=self.new_conversation, fg_color="#0d9488").pack(fill="x", padx=14, pady=5)
        ctk.CTkButton(sidebar, text="Configuración", command=self.open_settings, fg_color="transparent", border_width=1).pack(fill="x", padx=14, pady=7)
        ctk.CTkLabel(sidebar, text="HISTORIAL", anchor="w").pack(fill="x", padx=18, pady=(25, 6))
        self.history_search = ctk.CTkEntry(sidebar, placeholder_text="Buscar conversaciones")
        self.history_search.pack(fill="x", padx=12, pady=5)
        self.history_search.bind("<Return>", lambda e: self.refresh_history())
        ctk.CTkButton(sidebar, text="Buscar", height=27, command=self.refresh_history).pack(fill="x", padx=12)
        self.history_list = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.history_list.pack(fill="both", expand=True, padx=6, pady=8)
        ctk.CTkButton(sidebar, text="Eliminar conversación", fg_color="transparent", text_color=("#9f1239", "#fb7185"), command=self.delete_conversation).pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(sidebar, text="Datos guardados en este equipo\nPermisos antes de actuar", font=("Segoe UI", 10)).pack(pady=16)

    def _build_chat(self):
        panel = ctk.CTkFrame(self, fg_color="transparent")
        panel.grid(row=0, column=1, sticky="nsew", padx=18, pady=18)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)
        ctk.CTkLabel(panel, text="¿En qué trabajamos hoy?", font=("Segoe UI", 25, "bold"), anchor="w").grid(row=0, column=0, sticky="ew", pady=(0, 14))
        selectors = ctk.CTkFrame(panel, fg_color="transparent")
        selectors.grid(row=1, column=0, sticky="ew")
        self.provider = ctk.CTkOptionMenu(selectors, values=list(PROVIDERS), width=135, command=self.select_provider)
        self.provider.pack(side="left", padx=(0, 8))
        self.model = ctk.CTkEntry(selectors, placeholder_text="Modelo editable")
        self.model.pack(side="left", fill="x", expand=True)
        self.model.bind("<Return>", lambda e: self.apply_model())
        ctk.CTkButton(selectors, text="Aplicar", width=65, command=self.apply_model).pack(side="left", padx=(8, 0))
        states = ctk.CTkFrame(panel, fg_color="transparent")
        states.grid(row=2, column=0, sticky="ew", pady=12)
        self.status_label = ctk.CTkLabel(states, text="● Listo", text_color=("#0f766e", "#2dd4bf"), anchor="w")
        self.status_label.pack(side="left")
        self.connection_label = ctk.CTkLabel(states, text="Sin verificar", anchor="e", font=("Segoe UI", 11))
        self.connection_label.pack(side="right")
        self.chat = ctk.CTkTextbox(panel, wrap="word", font=("Segoe UI", 14), corner_radius=12, spacing3=8)
        self.chat.grid(row=3, column=0, sticky="nsew")
        self.chat.tag_config("user", foreground="#3b82f6")
        self.chat.tag_config("assistant", foreground="#0d9488")
        self.chat.tag_config("meta", foreground="#8492a6")
        self.chat.configure(state="disabled")
        self.error_label = ctk.CTkLabel(panel, text="", anchor="w", justify="left", wraplength=540, text_color=("#b91c1c", "#fda4af"), font=("Segoe UI", 11))
        self.error_label.grid(row=4, column=0, sticky="ew", pady=(6, 2))
        self.entry = ctk.CTkTextbox(panel, height=78, wrap="word", font=("Segoe UI", 14))
        self.entry.grid(row=5, column=0, sticky="ew", pady=6)
        self.entry.bind("<Return>", self.on_enter)
        buttons = ctk.CTkFrame(panel, fg_color="transparent")
        buttons.grid(row=6, column=0, sticky="ew", pady=5)
        self.mic = ctk.CTkButton(buttons, text="Micrófono", width=100, command=self.toggle_mic, fg_color="#475569")
        self.mic.pack(side="left", padx=(0, 6))
        self.mic.bind("<ButtonPress-1>", self.mic_press, add="+")
        self.mic.bind("<ButtonRelease-1>", self.mic_release, add="+")
        self.voice_var = ctk.BooleanVar(value=self.config.get("voice_enabled"))
        ctk.CTkSwitch(buttons, text="Voz", variable=self.voice_var, command=self.toggle_voice, width=75).pack(side="left")
        self.send_button = ctk.CTkButton(buttons, text="Enviar ↗", width=100, fg_color="#0d9488", command=self.send)
        self.send_button.pack(side="right")
        ctk.CTkButton(buttons, text="Detener", width=85, fg_color="#475569", command=self.stop).pack(side="right", padx=6)
        self.voice_label = ctk.CTkLabel(panel, text="Micrófono apagado · Enter envía · Mayús+Enter nueva línea", font=("Segoe UI", 10), anchor="w")
        self.voice_label.grid(row=7, column=0, sticky="ew", pady=5)

    def _build_inspector(self):
        tabs = ctk.CTkTabview(self, width=310)
        tabs.grid(row=0, column=2, sticky="nsew", padx=(0, 14), pady=12)
        tools = tabs.add("Herramientas")
        memory = tabs.add("Memoria")
        guide = tabs.add("Guía")
        self.tool_select = ctk.CTkOptionMenu(tools, values=list(self.core.registry.tools), command=self.select_tool, width=270)
        self.tool_select.pack(fill="x", pady=12)
        self.tool_desc = ctk.CTkLabel(tools, text="", wraplength=260, justify="left", anchor="w")
        self.tool_desc.pack(fill="x", pady=8)
        ctk.CTkLabel(tools, text="Argumentos JSON · edítalos antes de ejecutar", font=("Segoe UI", 10)).pack(pady=5)
        self.tool_args = ctk.CTkTextbox(tools, height=250, wrap="word")
        self.tool_args.pack(fill="x", pady=8)
        ctk.CTkButton(tools, text="Ejecutar herramienta", command=self.execute_tool, fg_color="#0d9488").pack(fill="x", pady=8)
        ctk.CTkLabel(tools, text="Toda acción pasa por seguridad.\nPara automatización indica el título exacto\nde la ventana destino.", wraplength=270, font=("Segoe UI", 11)).pack(pady=20)
        self.select_tool(self.tool_select.get())
        self.memory_key = ctk.CTkEntry(memory, placeholder_text="Clave del recuerdo / búsqueda")
        self.memory_key.pack(fill="x", pady=12)
        self.memory_value = ctk.CTkTextbox(memory, height=100, wrap="word")
        self.memory_value.pack(fill="x", pady=5)
        ctk.CTkButton(memory, text="Guardar recuerdo", command=self.save_memory).pack(fill="x", pady=5)
        ctk.CTkButton(memory, text="Buscar / actualizar", command=self.refresh_memories, fg_color="#475569").pack(fill="x", pady=5)
        self.memories = ctk.CTkScrollableFrame(memory, fg_color="transparent")
        self.memories.pack(fill="both", expand=True, pady=8)
        help_box = ctk.CTkTextbox(guide, wrap="word", font=("Segoe UI", 12))
        help_box.pack(fill="both", expand=True, padx=4, pady=8)
        help_box.insert("1.0", "EMPEZAR\n\n1. Copia .env.example a .env y añade una clave; reinicia.\n2. Selecciona proveedor y modelo.\n3. Para uso local, inicia Ollama y descarga un modelo.\n\nSIN API\n\nAbre la calculadora\n¿Cuánta RAM estoy usando?\nRecuerda nombre=Ana\n¿Qué recuerdas?\nCaptura la pantalla\nBorra el archivo ejemplo.txt\n\nARCHIVOS\n\nLas rutas relativas apuntan a workspace/. Puedes autorizar más carpetas en Configuración. No se sobrescriben destinos.\n\nVOZ\n\nManual: un clic escucha una frase.\nPush-to-talk: mantén presionado el botón y suelta para transcribir.\nContinua: activa el micrófono y di VICTOR antes de cada comando.\nGoogle envía audio al servicio; Whisper puede trabajar localmente con modelo descargado.\n\nPRIVACIDAD\n\nEl historial y recuerdos se guardan en data/. Los proveedores online reciben contexto del chat y recuerdos relevantes. Visión pide permiso antes de enviar la captura.\n\nDETENER\n\nCancela futuras acciones y corta la voz. Una petición de red en curso puede tardar hasta su timeout; las acciones terminadas no se deshacen.")
        help_box.configure(state="disabled")

    def refresh_config(self):
        self.provider.set(self.config.get("provider"))
        self.model.delete(0, "end")
        self.model.insert(0, self.config.get("models")[self.config.get("provider")])
        available = [p for p, ok in self.config.credentials_status().items() if ok]
        self.connection_label.configure(text="Claves: " + ", ".join(available) if available else "Sin claves · Ollama opcional")
        if not available and self.config.get("provider") != "Ollama":
            self.error_label.configure(text="Falta configurar una clave: copia .env.example a .env y reinicia. También puedes seleccionar Ollama local.")

    def select_provider(self, provider):
        if self.core.busy.is_set():
            self.provider.set(self.config.get("provider"))
            return
        self.config.save({"provider": provider})
        self.refresh_config()

    def apply_model(self):
        if self.core.busy.is_set():
            return
        models = self.config.get("models")
        models[self.provider.get()] = self.model.get().strip()
        self.config.save({"models": models})
        self.error_label.configure(text="Modelo guardado; su disponibilidad se verifica al enviar.")

    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
        else:
            self.settings_window = SettingsManager(self)

    def append_message(self, role, content):
        self.chat.configure(state="normal")
        name = "TÚ" if role == "user" else self.config.get("name")
        self.chat.insert("end", name + "\n", role)
        self.chat.insert("end", content + "\n\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def begin_response(self):
        self.chat.configure(state="normal")
        self.chat.insert("end", self.config.get("name") + "\n", "assistant")
        self.streaming_start = self.chat.index("end-1c")
        self.chat.configure(state="disabled")
        self.partial = ""

    def replace_response(self, text):
        if self.streaming_start is None:
            self.begin_response()
        self.chat.configure(state="normal")
        self.chat.delete(self.streaming_start, "end-1c")
        self.chat.insert("end", text)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def on_enter(self, event):
        if event.state & 0x1:
            return None
        self.send()
        return "break"

    def send(self, text=None, direct_tool=None):
        if self.closing or self.core.busy.is_set():
            return
        text = text if text is not None else self.entry.get("1.0", "end-1c").strip()
        if not text:
            return
        if len(text) > 12000:
            self.error_label.configure(text="El mensaje supera 12.000 caracteres. Divídelo en mensajes más pequeños.")
            return
        self.voice_output.stop()
        self.error_label.configure(text="")
        self.entry.delete("1.0", "end")
        self.append_message("user", text)
        self.begin_response()
        self.send_button.configure(state="disabled")
        self.core.submit(text, self.conversation_id, direct_tool)

    def stop(self):
        self.core.stop()
        self.voice_input.stop()
        self.voice_output.stop()
        if self.approval and self.approval.winfo_exists():
            self.approval.resolve(False)
        self.status_label.configure(text="Deteniendo…")

    def toggle_voice(self):
        self.config.save({"voice_enabled": self.voice_var.get()})
        if not self.voice_var.get():
            self.voice_output.stop()

    def toggle_mic(self):
        if self.config.get("voice_mode") == "push-to-talk":
            return
        if self.voice_input.running:
            self.voice_input.stop()
        else:
            self.start_mic()

    def start_mic(self):
        if self.core.busy.is_set():
            return
        if self.config.get("voice_backend") == "google" and not getattr(self, "audio_consent", False):
            if not messagebox.askyesno("Reconocimiento online", "El audio se enviará al servicio de reconocimiento de Google. ¿Activar el micrófono?\nPuedes elegir Whisper local en Configuración.", parent=self):
                return
            self.audio_consent = True
        self.voice_output.stop()
        self.voice_input.start()

    def mic_press(self, event):
        if self.config.get("voice_mode") == "push-to-talk":
            self.start_mic()

    def mic_release(self, event):
        if self.config.get("voice_mode") == "push-to-talk":
            self.voice_input.release()

    def select_tool(self, name):
        tool = self.core.registry.tools[name]
        self.tool_desc.configure(text=tool.description + "\nRiesgo: " + tool.risk.name)
        self.tool_args.delete("1.0", "end")
        self.tool_args.insert("1.0", json.dumps(example_args(tool.schema), ensure_ascii=False, indent=2))

    def execute_tool(self):
        try:
            args = json.loads(self.tool_args.get("1.0", "end-1c"))
            name = self.tool_select.get()
            self.send("Ejecutar " + name + ": " + json.dumps(args, ensure_ascii=False), (name, args))
        except ValueError:
            self.error_label.configure(text="Los argumentos no son JSON válido. Revisa comillas y comas.")

    def save_memory(self):
        key, value = self.memory_key.get(), self.memory_value.get("1.0", "end-1c")
        self.send("Guardar recuerdo: " + key, ("remember", {"key": key, "value": value}))

    def forget_memory(self, key):
        self.send("Eliminar recuerdo: " + key, ("forget", {"key": key}))

    def refresh_memories(self):
        for child in self.memories.winfo_children():
            child.destroy()
        for row in self.core.memory.search_memory(self.memory_key.get().strip()):
            frame = ctk.CTkFrame(self.memories)
            frame.pack(fill="x", pady=4)
            ctk.CTkLabel(frame, text=row["key"], font=("Segoe UI", 12, "bold"), wraplength=240, anchor="w").pack(fill="x", padx=8)
            ctk.CTkLabel(frame, text=row["value"], wraplength=240, justify="left", anchor="w").pack(fill="x", padx=8)
            ctk.CTkButton(frame, text="Eliminar", height=24, fg_color="#475569", command=lambda k=row["key"]: self.forget_memory(k)).pack(padx=8, pady=6)

    def refresh_history(self):
        for child in self.history_list.winfo_children():
            child.destroy()
        for row in self.core.history.list(self.history_search.get().strip())[:60]:
            ctk.CTkButton(self.history_list, text=row["title"][:24], anchor="w", fg_color="transparent", height=34,
                          command=lambda cid=row["id"]: self.load_conversation(cid)).pack(fill="x", pady=2)

    def load_conversation(self, conversation_id):
        if self.core.busy.is_set():
            return
        self.conversation_id = conversation_id
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        self.streaming_start = None
        rows = self.core.history.messages(conversation_id)
        if not rows:
            self.append_message("assistant", "Estoy listo. Puedes escribir, usar el micrófono o elegir una herramienta. Escribe «ayuda» para ver los comandos locales.")
        for row in rows:
            self.append_message(row["role"], row["content"])

    def new_conversation(self):
        if not self.core.busy.is_set():
            self.load_conversation(self.core.history.create())
            self.refresh_history()

    def delete_conversation(self):
        if self.core.busy.is_set():
            return
        if messagebox.askyesno("Eliminar historial", "¿Eliminar permanentemente esta conversación local? Los recuerdos se conservan.", parent=self):
            self.core.history.delete(self.conversation_id)
            rows = self.core.history.list()
            self.load_conversation(rows[0]["id"] if rows else self.core.history.create())
            self.refresh_history()

    def poll(self):
        try:
            for _ in range(200):
                try:
                    kind, payload = self.events.get_nowait()
                except queue.Empty:
                    break
                if kind == "token":
                    self.partial += payload
                    self.replace_response(self.partial)
                elif kind == "stream_reset":
                    self.partial = ""
                    self.replace_response("")
                elif kind == "answer":
                    self.replace_response(payload + "\n\n")
                    self.streaming_start = None
                    if not self.closing and not self.core.cancel.is_set():
                        self.voice_output.speak(payload)
                elif kind == "approval":
                    if self.closing or self.core.cancel.is_set():
                        payload.done.set()
                    else:
                        self.approval = ApprovalDialog(self, payload)
                elif kind == "status":
                    self.status_label.configure(text="● " + payload)
                elif kind == "connection":
                    self.connection_label.configure(text=payload)
                elif kind in ("error", "notice"):
                    self.error_label.configure(text=payload[:800])
                elif kind in ("voice_status", "speech_status"):
                    self.voice_label.configure(text=payload)
                    self.mic.configure(fg_color="#0d9488" if self.voice_input.running else "#475569")
                elif kind == "voice_text":
                    self.send(payload)
                elif kind == "done":
                    self.send_button.configure(state="normal")
                    self.status_label.configure(text="● Listo")
                    self.refresh_history()
                    self.refresh_memories()
                elif kind == "tool_result":
                    name, result = payload
                    self.status_label.configure(text="● " + name + (" completada" if result["ok"] else " falló"))
        except Exception:
            logging.getLogger("victor.gui").exception("event dispatch failed")
            self.error_label.configure(text="Error al actualizar la interfaz. Revisa data/victor.log.")
        if self.winfo_exists():
            self.after(60, self.poll)

    def animate(self):
        if self.closing:
            return
        self.pulse = (self.pulse + 1) % 3
        if self.core.busy.is_set():
            self.status_label.configure(text_color=["#14b8a6", "#2dd4bf", "#5eead4"][self.pulse])
        self.after(700, self.animate)

    def callback_error(self, exc, value, tb):
        logging.getLogger("victor.gui").error("GUI callback failed", exc_info=(exc, value, tb))
        self.error_label.configure(text="No se pudo completar esa operación: " + str(value)[:300])

    def close(self):
        if self.closing:
            return
        self.closing = True
        self.close_started = time.monotonic()
        self.stop()
        self.voice_output.close()
        self.entry.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self.status_label.configure(text="Cerrando trabajadores…")
        self.after(100, self._finish_close)

    def _finish_close(self):
        threads = [self.core.thread, self.voice_input.thread, self.voice_output.thread]
        active = [t for t in threads if t and t.is_alive()]
        if active and time.monotonic()-self.close_started < self.config.get("network_timeout") + 15:
            self.after(100, self._finish_close)
            return
        if active:
            logging.getLogger("victor.gui").warning("shutdown deadline reached for %s", [t.name for t in active])
        # Cancela también temporizadores internos de CustomTkinter antes de destruir Tcl.
        for callback_id in self.tk.call("after", "info"):
            self.tk.call("after", "cancel", callback_id)
        self.destroy()
