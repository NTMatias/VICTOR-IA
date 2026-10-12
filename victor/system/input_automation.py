import time
from victor.errors import VictorError, check_cancel
from victor.system.apps import require_windows


class InputAutomation:
    """Una acción por aprobación, ventana exacta, límites y failsafe de PyAutoGUI."""
    def __init__(self, cancel):
        self.cancel = cancel

    def prepare(self, window):
        require_windows()
        import pyautogui
        import pygetwindow
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.15
        matches = [w for w in pygetwindow.getAllWindows() if w.title == window]
        if len(matches) != 1 or "VICTOR.IA" in window:
            raise VictorError("Indica el título exacto de una única ventana destino, distinta de VICTOR.IA.")
        target = matches[0]
        if target.isMinimized:
            target.restore()
        target.activate()
        if self.cancel.wait(0.5):
            check_cancel(self.cancel)
        if not target.isActive:
            raise VictorError("No se pudo activar la ventana destino. No se envió ninguna entrada.")
        return pyautogui, target

    def mouse_click(self, window, x, y, button="left"):
        gui, target = self.prepare(window)
        if not (target.left <= x < target.right and target.top <= y < target.bottom):
            raise VictorError("Las coordenadas deben estar dentro de la ventana autorizada.")
        check_cancel(self.cancel)
        gui.click(x, y, button=button)
        return {"clic": [x, y], "ventana": window}

    def move_mouse(self, window, x, y):
        gui, target = self.prepare(window)
        if not (target.left <= x < target.right and target.top <= y < target.bottom):
            raise VictorError("Las coordenadas deben estar dentro de la ventana autorizada.")
        gui.moveTo(x, y, duration=0.2)
        return {"posicion": [x, y]}

    def type_text(self, window, text):
        if len(text) > 2000 or any(ord(c) < 32 for c in text):
            raise VictorError("Escritura limitada a 2000 caracteres sin Enter ni caracteres de control.")
        gui, target = self.prepare(window)
        # Entrada Unicode nativa evita alterar el portapapeles y permite acentos.
        import ctypes
        from ctypes import wintypes
        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]
        class MOUSEINPUT(ctypes.Structure):
            _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]
        class UNION(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]
        class INPUT(ctypes.Structure):
            _fields_ = [("type", wintypes.DWORD), ("u", UNION)]
        raw = text.encode("utf-16-le")
        for i in range(0, len(raw), 2):
            check_cancel(self.cancel)
            gui.failSafeCheck()
            if not target.isActive:
                raise VictorError("La ventana perdió el foco; escritura interrumpida.")
            unit = int.from_bytes(raw[i:i+2], "little")
            events = (INPUT * 2)(INPUT(1, UNION(ki=KEYBDINPUT(0, unit, 4, 0, 0))), INPUT(1, UNION(ki=KEYBDINPUT(0, unit, 6, 0, 0))))
            if ctypes.windll.user32.SendInput(2, events, ctypes.sizeof(INPUT)) != 2:
                raise VictorError("Windows bloqueó la entrada. No automatices aplicaciones elevadas.")
        return {"caracteres_enviados": len(text), "ventana": window}

    def press_keys(self, window, keys):
        allowed = {"ctrl", "alt", "shift", "enter", "tab", "esc", "up", "down", "left", "right", "space", "backspace", "delete", "home", "end", "pageup", "pagedown"} | set("abcdefghijklmnopqrstuvwxyz0123456789")
        if not 1 <= len(keys) <= 4 or any(k not in allowed for k in keys):
            raise VictorError("Atajo inválido; no se permite la tecla Windows ni teclas de función.")
        gui, target = self.prepare(window)
        gui.hotkey(*keys)
        return {"teclas_enviadas": keys, "ventana": window}
