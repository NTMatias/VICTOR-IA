import base64
import ctypes
import io
import os
import uuid
import logging
from pathlib import Path
from victor.errors import VictorError


class ScreenManager:
    def __init__(self, config):
        self.folder = config.data_dir / "captures"
        self.folder.mkdir(exist_ok=True)

    def capture(self, region=None):
        import mss
        from PIL import Image
        try:
            with (mss.MSS() if hasattr(mss, "MSS") else mss.mss()) as screen:
                bounds = screen.monitors[0]
                area = bounds
                if region is not None:
                    if len(region) != 4 or any(not isinstance(v, int) for v in region):
                        raise VictorError("Región: [x, y, ancho, alto], con números enteros.")
                    x, y, w, h = region
                    if w < 1 or h < 1 or x < bounds["left"] or y < bounds["top"] or x+w > bounds["left"]+bounds["width"] or y+h > bounds["top"]+bounds["height"]:
                        raise VictorError("La región está fuera del escritorio.")
                    area = dict(left=x, top=y, width=w, height=h)
                shot = screen.grab(area)
                image = Image.frombytes("RGB", shot.size, shot.rgb)
        except mss.exception.ScreenShotError:
            logging.getLogger("victor.screen").exception("Screen capture unavailable")
            raise VictorError("Windows no permitió capturar la pantalla. Usa una sesión de escritorio interactiva, desbloqueada y sin contenido protegido.") from None
        path = self.folder / (uuid.uuid4().hex + ".png")
        image.save(path)
        # Retención acotada; capturas solo generadas por esta aplicación.
        for old in sorted(self.folder.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)[30:]:
            old.unlink(missing_ok=True)
        return {"captura": str(path), "ancho": image.width, "alto": image.height}

    @staticmethod
    def encode(path):
        from PIL import Image
        with Image.open(path) as image:
            image.thumbnail((1600, 1600))
            data = io.BytesIO()
            image.convert("RGB").save(data, format="PNG")
        return base64.b64encode(data.getvalue()).decode("ascii")

    @staticmethod
    def active_window():
        if os.name != "nt":
            raise VictorError("La ventana activa solo está disponible en Windows.")
        import pygetwindow
        window = pygetwindow.getActiveWindow()
        if window is None:
            return {"titulo": "No hay ventana activa"}
        return {"titulo": window.title, "x": window.left, "y": window.top, "ancho": window.width, "alto": window.height}
