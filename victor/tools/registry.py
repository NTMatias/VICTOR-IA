from dataclasses import dataclass
import json
import logging
import time
from typing import Callable
import jsonschema
from victor.security import Risk
from victor.errors import VictorError, Cancelled, check_cancel


@dataclass
class Tool:
    name: str
    description: str
    schema: dict
    risk: Risk
    function: Callable


class ToolRegistry:
    """Único punto de ejecución, también para comandos locales y panel de herramientas."""
    def __init__(self, security, cancel, emit):
        self.security, self.cancel, self.emit = security, cancel, emit
        self.tools = {}
        self.log = logging.getLogger("victor.tools")

    def register(self, tool):
        if tool.name in self.tools:
            raise ValueError("Nombre de herramienta duplicado")
        jsonschema.Draft202012Validator.check_schema(tool.schema)
        self.tools[tool.name] = tool

    def specs(self):
        return [{"name": t.name, "description": t.description, "parameters": t.schema} for t in self.tools.values()]

    def execute(self, name, args):
        start = time.monotonic()
        try:
            check_cancel(self.cancel)
            tool = self.tools.get(name)
            if tool is None:
                raise VictorError("Herramienta desconocida; no se ejecutó nada.")
            jsonschema.validate(args, tool.schema)
            args = json.loads(json.dumps(args))
            for key in ("path", "source", "destination"):
                if key in args:
                    args[key] = str(self.security.path(args[key], allow_root=name in ("open_file", "list_files")))
            if name in ("open_application", "close_application"):
                # resolve valida alias antes del diálogo; ejecutar vuelve a validar.
                owner = getattr(tool.function, "__self__", None)
                if owner:
                    owner.resolve(args["name"])
            risk = tool.risk
            if name == "press_keys" and any(k in ("enter", "delete") for k in args.get("keys", [])):
                risk = Risk.HIGH
            if name == "type_text":
                risk = Risk.HIGH  # el texto podría terminar en una consola
            details = json.dumps(args, ensure_ascii=False, indent=2)
            if name == "close_application":
                details += "\nCerrar termina el proceso y puede perder cambios sin guardar."
            if name in ("mouse_click", "type_text", "press_keys", "move_mouse"):
                details += "\nSe activará la ventana indicada. Revisa el destino. Mueve el ratón a una esquina para abortar."
            self.security.confirm(name, details, risk, self.cancel)
            check_cancel(self.cancel)
            self.emit("status", "Ejecutando " + name)
            result = tool.function(**args)
            self.log.info("tool=%s result=success seconds=%.2f", name, time.monotonic()-start)
            return {"ok": True, "result": result}
        except Cancelled:
            raise
        except jsonschema.ValidationError:
            result = "Argumentos inválidos para la herramienta. No se ejecutó la acción."
        except ImportError as exc:
            self.log.warning("tool=%s missing_dependency=%s", name, exc.name)
            result = f"Función no disponible: falta {exc.name}. Repite instalar.bat o consulta el README."
        except VictorError as exc:
            result = str(exc)
        except FileExistsError:
            result = "El destino ya existe. No se sobrescribió. Elige otro nombre."
        except FileNotFoundError:
            result = "No existe el archivo o la carpeta indicada."
        except PermissionError:
            result = "Windows denegó el acceso. No ejecutes el asistente como administrador."
        except Exception:
            self.log.exception("tool=%s failed", name)
            result = "La herramienta no pudo completar la acción. Revisa los parámetros y el registro local."
        self.log.info("tool=%s result=failed seconds=%.2f", name, time.monotonic()-start)
        self.emit("notice", f"{name}: {result}")
        return {"ok": False, "error": result}
