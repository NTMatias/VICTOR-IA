import os
import shutil
import subprocess
import webbrowser
import time
from pathlib import Path
from victor.errors import VictorError


def require_windows():
    if os.name != "nt":
        raise VictorError("Esta función solo está disponible en Windows 10/11.")


class ApplicationManager:
    def __init__(self, config, security):
        self.config, self.security = config, security
        self.launched = {}

    def resolve(self, name):
        require_windows()
        key = name.casefold().strip()
        win = Path(os.environ.get("WINDIR", "C:/Windows"))
        builtins = {"calculadora": win / "System32/calc.exe", "calculator": win / "System32/calc.exe",
                    "bloc de notas": win / "System32/notepad.exe", "notepad": win / "System32/notepad.exe",
                    "explorador": win / "explorer.exe", "paint": win / "System32/mspaint.exe"}
        aliases = {k.casefold(): v for k, v in self.config.get("applications").items()}
        path = aliases.get(key) or builtins.get(key)
        if not path and key == "spotify":
            candidate = Path(os.environ.get("APPDATA", "C:/__missing__")) / "Spotify/Spotify.exe"
            path = candidate if candidate.is_file() else None
        if not path and key in ("chrome", "google chrome", "edge", "microsoft edge", "firefox"):
            relative = {"chrome": "Google/Chrome/Application/chrome.exe", "google chrome": "Google/Chrome/Application/chrome.exe",
                        "edge": "Microsoft/Edge/Application/msedge.exe", "microsoft edge": "Microsoft/Edge/Application/msedge.exe",
                        "firefox": "Mozilla Firefox/firefox.exe"}[key]
            for folder in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
                candidate = Path(os.environ.get(folder, "C:/__missing__")) / relative
                if candidate.is_file():
                    path = candidate
                    break
        if not path:
            raise VictorError("Aplicación no registrada. Añade su alias y ruta .exe en Configuración → aplicaciones.")
        return self.security.executable(str(path))

    def open_application(self, name):
        path = self.resolve(name)
        process = subprocess.Popen([path], shell=False)
        self.launched[process.pid] = path
        result = {"solicitud_apertura": name, "pid": process.pid}
        if Path(path).stem.casefold() == "calc":
            try:
                import pygetwindow
                import psutil
                deadline = time.monotonic() + 3
                windows = []
                while time.monotonic() < deadline:
                    windows = [w for w in pygetwindow.getAllWindows() if w.title.casefold() in ("calculadora", "calculator") and w.visible]
                    if windows:
                        break
                    time.sleep(.2)
                processes = [p.info for p in psutil.process_iter(["pid", "name"]) if (p.info["name"] or "").casefold() in ("calculator.exe", "calculatorapp.exe", "calc.exe")]
                result.update(ventana_visible=bool(windows), procesos=processes)
                if not windows:
                    result["aviso"] = "Windows recibió la solicitud, pero no pude confirmar una ventana visible de Calculadora."
            except Exception:
                result["aviso"] = "Solicitud enviada; no se pudo verificar la ventana de Calculadora."
        return result

    def close_application(self, name):
        import psutil
        target = Path(self.resolve(name)).resolve()
        count = 0
        for p in psutil.process_iter(["pid", "exe"]):
            try:
                if p.info["exe"] and Path(p.info["exe"]).resolve() == target:
                    if p.pid == os.getpid():
                        continue
                    p.terminate()
                    count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if not count:
            raise VictorError("No encontré procesos accesibles de esa aplicación. Algunas aplicaciones de Windows usan otro proceso.")
        return {"procesos_terminados": count, "aplicacion": name}

    def open_url(self, url):
        self.security.url(url)
        if not webbrowser.open(url, new=2):
            raise VictorError("No se pudo solicitar la apertura del navegador.")
        return {"solicitud_apertura": url}
