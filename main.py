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
        config = ConfigManager()
        log = setup_logging(config.data_dir)
        log.info("startup Python=%s", sys.version.split()[0])
        app = GUIManager(config)
        if args.smoke_test:
            def verify_window():
                result = {"window_open": bool(app.winfo_viewable()), "geometry": app.geometry(),
                          "title": app.title(), "tools": len(app.core.registry.tools), "python": sys.version}
                try:
                    import mss
                    import mss.tools
                    with mss.mss() as sct:
                        region = {"left": app.winfo_rootx(), "top": app.winfo_rooty(), "width": app.winfo_width(), "height": app.winfo_height()}
                        shot = sct.grab(region)
                        mss.tools.to_png(shot.rgb, shot.size, output=str(Path(args.smoke_test).with_suffix(".png")))
                    result["screenshot"] = str(Path(args.smoke_test).with_suffix(".png"))
                except Exception as exc:
                    result["screenshot_error"] = type(exc).__name__ + ": " + str(exc)
                    try:
                        from PIL import ImageGrab
                        box = (app.winfo_rootx(), app.winfo_rooty(), app.winfo_rootx()+app.winfo_width(), app.winfo_rooty()+app.winfo_height())
                        ImageGrab.grab(bbox=box).save(Path(args.smoke_test).with_suffix(".png"))
                        result["screenshot_fallback"] = "Pillow ImageGrab"
                    except Exception as fallback_error:
                        result["screenshot_fallback_error"] = str(fallback_error)
                Path(args.smoke_test).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
                app.close()
            app.after(1800, verify_window)
        app.mainloop()
        log.info("shutdown")
    except ImportError as exc:
        message = f"Falta una dependencia: {exc.name}. Ejecuta instalar.bat y después iniciar.bat."
        print(message)
        try:
            import tkinter.messagebox
            tkinter.messagebox.showerror("VICTOR.IA", message)
        except Exception:
            pass
        raise SystemExit(1)


if __name__ == "__main__":
    main()
