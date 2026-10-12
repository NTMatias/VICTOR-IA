import customtkinter as ctk
from victor.security import Risk


class ApprovalDialog(ctk.CTkToplevel):
    """Sin aprobaciones automáticas ni botón aceptar activado por defecto."""
    def __init__(self, parent, request):
        super().__init__(parent)
        self.request = request
        self.title("VICTOR.IA · Autorizar acción")
        self.geometry("660x530")
        self.transient(parent)
        self.grab_set()
        ctk.CTkLabel(self, text="Revisa esta acción", font=("Segoe UI", 23, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(self, text=f"{request.title} · Riesgo {request.risk.name}").pack(pady=5)
        box = ctk.CTkTextbox(self, wrap="word", height=270)
        box.pack(fill="both", expand=True, padx=20, pady=10)
        box.insert("1.0", request.details)
        box.configure(state="disabled")
        self.phrase = None
        if request.risk == Risk.HIGH:
            ctk.CTkLabel(self, text="Para autorizar, escribe EJECUTAR:").pack()
            self.phrase = ctk.CTkEntry(self, width=240)
            self.phrase.pack(pady=5)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(pady=15)
        ctk.CTkButton(row, text="Cancelar", fg_color="#475569", command=lambda: self.resolve(False)).pack(side="left", padx=8)
        self.approve = ctk.CTkButton(row, text="Autorizar una vez", fg_color="#b45309", command=lambda: self.resolve(True))
        self.approve.pack(side="left", padx=8)
        if self.phrase:
            self.approve.configure(state="disabled")
            self.phrase.bind("<KeyRelease>", lambda e: self.approve.configure(state="normal" if self.phrase.get() == "EJECUTAR" else "disabled"))
        self.protocol("WM_DELETE_WINDOW", lambda: self.resolve(False))
        self.bind("<Escape>", lambda e: self.resolve(False))
        self.after(100, self.lift)

    def resolve(self, accepted):
        if accepted and self.phrase and self.phrase.get() != "EJECUTAR":
            return
        self.request.accepted = accepted
        self.request.done.set()
        self.grab_release()
        self.destroy()
