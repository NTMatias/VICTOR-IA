"""Punto de entrada de VICTOR.IA para Python 3.11+."""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="VICTOR.IA — asistente de escritorio")
    parser.add_argument("--speak-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--smoke-test", metavar="RESULT_JSON", help="Abre la GUI real y la cierra; guarda evidencia de arranque.")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        raise SystemExit("Se necesita Python 3.11 o posterior.")
    if args.speak_worker:
        from victor.voice.output import speak_worker
        speak_worker()
        return
    try:
        from victor.config import ConfigManager
        from victor.logger import setup_logging
        from victor.gui.app import GUIManager
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        config = ConfigManager()
        log = setup_logging(config.data_dir)
        log.info("startup Python=%s", sys.version.split()[0])
        qt = QApplication.instance() or QApplication(sys.argv[:1])
        app = GUIManager(config)
        app.show()
        if args.smoke_test:
            def verify_window():
                result = {"window_open": app.isVisible(), "geometry": [app.width(), app.height()],
                          "title": app.windowTitle(), "tools": len(app.core.registry.tools), "python": sys.version}
                try:
                    if not app.grab().save(str(Path(args.smoke_test).with_suffix(".png"))):
                        raise RuntimeError("Qt no pudo guardar la captura del widget.")
                    result["screenshot"] = str(Path(args.smoke_test).with_suffix(".png"))
                except Exception as exc:
                    result["screenshot_error"] = type(exc).__name__ + ": " + str(exc)
                Path(args.smoke_test).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                app.close()
            QTimer.singleShot(2400, verify_window)
        qt.exec()
        log.info("shutdown")
    except ImportError as exc:
        message = f"Falta una dependencia: {exc.name}. Ejecuta instalar.bat y después iniciar.bat."
        print(message)
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            qt = QApplication.instance() or QApplication([])
            QMessageBox.critical(None, "VICTOR.IA", message)
        except Exception:
            pass
        raise SystemExit(1)


if __name__ == "__main__":
    main()
