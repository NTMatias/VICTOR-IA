import os
import shutil
from victor.errors import VictorError


class FileManager:
    TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".log", ".yaml", ".yml"}
    OPEN_EXTENSIONS = TEXT_EXTENSIONS | {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".mp3", ".wav", ".mp4"}

    def __init__(self, security):
        self.security = security

    def create_file(self, path, text):
        p = self.security.path(path)
        if p.suffix.lower() not in self.TEXT_EXTENSIONS:
            raise VictorError("Solo se pueden crear archivos de texto: txt, md, csv, json, log, yaml, yml.")
        if len(text) > 200000:
            raise VictorError("El texto supera el límite de 200.000 caracteres.")
        with p.open("x", encoding="utf-8") as handle:
            handle.write(text)
        return {"creado": str(p)}

    def create_folder(self, path):
        p = self.security.path(path)
        p.mkdir(parents=False, exist_ok=False)
        return {"creada": str(p)}

    def transfer(self, source, destination, copy=False):
        src = self.security.path(source, True)
        dst = self.security.path(destination)
        if not src.is_file():
            raise VictorError("Mover/copiar/renombrar admite archivos individuales, no árboles de carpetas.")
        if not dst.parent.is_dir():
            raise VictorError("La carpeta de destino no existe.")
        # Creación exclusiva: no sobrescribir datos aunque aparezcan después de la confirmación.
        with src.open("rb") as incoming, dst.open("xb") as outgoing:
            try:
                shutil.copyfileobj(incoming, outgoing, 1024 * 1024)
            except BaseException:
                outgoing.close()
                dst.unlink(missing_ok=True)
                raise
        if not copy:
            src.unlink()
        return {"origen": str(src), "destino": str(dst), "operacion": "copiado" if copy else "movido"}

    def move_file(self, source, destination):
        return self.transfer(source, destination)

    def copy_file(self, source, destination):
        return self.transfer(source, destination, copy=True)

    def rename_file(self, source, name):
        from pathlib import Path
        if Path(name).name != name or any(c in name for c in '\\/:*?"<>|') or name in (".", ".."):
            raise VictorError("Indica solo el nuevo nombre, sin ruta.")
        src = self.security.path(source, True)
        return self.transfer(str(src), str(src.with_name(name)))

    def delete_file(self, path):
        from send2trash import send2trash
        p = self.security.path(path, True)
        if p.is_dir():
            raise VictorError("Por seguridad solo se envían archivos individuales a la papelera.")
        send2trash(str(p))
        return {"enviado_a_papelera": str(p)}

    def open_file(self, path):
        p = self.security.path(path, True, allow_root=True)
        if p.is_file() and p.suffix.lower() not in self.OPEN_EXTENSIONS:
            raise VictorError("Ese tipo de archivo no puede abrirse con esta herramienta por seguridad.")
        if os.name != "nt":
            raise VictorError("Abrir archivos con su aplicación asociada requiere Windows.")
        os.startfile(str(p))
        return {"solicitud_apertura": str(p)}

    def list_files(self, path="."):
        p = self.security.path(path, True, allow_root=True)
        if not p.is_dir():
            raise VictorError("Selecciona una carpeta.")
        return [{"nombre": item.name, "carpeta": item.is_dir()} for item in list(p.iterdir())[:200]]
