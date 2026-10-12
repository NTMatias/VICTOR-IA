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
        from PIL import Image
        try:
            import mss
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
        except VictorError:
            raise
        except Exception:
            logging.getLogger("victor.screen").warning("MSS unavailable, trying ImageGrab", exc_info=True)
            try:
                from PIL import ImageGrab
                image = ImageGrab.grab(all_screens=True)
                if region is not None:
                    if len(region) != 4 or any(type(v) is not int for v in region):
                        raise VictorError("Región: [x, y, ancho, alto], con números enteros.")
                    x, y, w, h = region
                    left = ctypes.windll.user32.GetSystemMetrics(76) if os.name == "nt" else 0
                    top = ctypes.windll.user32.GetSystemMetrics(77) if os.name == "nt" else 0
                    x, y = x-left, y-top
                    if min(x, y) < 0 or min(w, h) < 1 or x+w > image.width or y+h > image.height:
                        raise VictorError("La región está fuera del escritorio.")
                    image = image.crop((x, y, x+w, y+h))
            except VictorError:
                raise
            except Exception:
                logging.getLogger("victor.screen").exception("ImageGrab also unavailable")
                raise VictorError("No pude capturar el escritorio con MSS ni ImageGrab. Comprueba que Windows esté desbloqueado, en sesión interactiva y sin contenido protegido.") from None
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
