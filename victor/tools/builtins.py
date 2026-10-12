from victor.tools.registry import Tool
from victor.security import Risk


def string(description="", max_length=4000):
    return {"type": "string", "minLength": 1, "maxLength": max_length, "description": description}


def install_tools(core):
    r = core.registry
    def add(tool_name, desc, function, risk=Risk.LOW, **properties):
        schema = {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}
        r.register(Tool(tool_name, desc, schema, risk, function))
    path = string("Ruta dentro de una carpeta autorizada; puede ser relativa a la primera raíz.")
    window = string("Título EXACTO de la ventana destino, nunca VICTOR.IA.", 500)
    region = {"type": ["array", "null"], "items": {"type": "integer"}, "minItems": 4, "maxItems": 4,
              "description": "null para pantalla completa; [x,y,ancho,alto] para región."}
    add("open_application", "Abre una aplicación registrada por alias, sin argumentos de terminal.", core.apps.open_application, name=string())
    add("close_application", "Termina procesos de una aplicación registrada; puede perder cambios sin guardar.", core.apps.close_application, Risk.MEDIUM, name=string())
    add("open_url", "Abre una URL HTTP/HTTPS en el navegador.", core.apps.open_url, url=string())
    add("open_file", "Abre carpeta o archivo de tipo seguro en una raíz autorizada.", core.files.open_file, path=path)
    add("create_folder", "Crea una carpeta; no sobrescribe.", core.files.create_folder, Risk.MEDIUM, path=path)
    add("list_files", "Lista archivos de una carpeta autorizada.", core.files.list_files, path=path)
    add("create_file", "Crea archivo de texto nuevo; nunca sobrescribe.", core.files.create_file, Risk.MEDIUM, path=path, text={"type": "string", "maxLength": 200000})
    add("move_file", "Mueve un archivo individual a una ruta nueva sin sobrescribir.", core.files.move_file, Risk.MEDIUM, source=path, destination=path)
    add("copy_file", "Copia un archivo individual sin sobrescribir.", core.files.copy_file, Risk.MEDIUM, source=path, destination=path)
    add("rename_file", "Renombra un archivo individual sin sobrescribir.", core.files.rename_file, Risk.MEDIUM, source=path, name=string())
    add("delete_file", "Envía un archivo individual a la papelera; requiere confirmación explícita.", core.files.delete_file, Risk.HIGH, path=path)
    add("get_system_info", "CPU, RAM, disco, procesos y batería reales.", core.windows.get_system_info)
    add("control_volume", "Ajusta volumen entre 0 y 100.", core.windows.control_volume, Risk.MEDIUM, level={"type": "integer", "minimum": 0, "maximum": 100})
    add("adjust_volume", "Sube o baja diez puntos el volumen, o silencia.", core.windows.adjust_volume, Risk.MEDIUM,
        action={"type": "string", "enum": ["up", "down", "mute"]})
    add("open_settings", "Abre Configuración de Windows.", core.windows.open_settings)
    add("run_terminal", "Solo diagnósticos de lista blanca SIN argumentos. No permite shell ni scripts.", core.windows.run_diagnostic, Risk.HIGH,
        command={"type": "string", "enum": ["ipconfig", "whoami", "hostname", "systeminfo"]})
    add("take_screenshot", "Captura local; no envía la imagen a Internet.", core.screen.capture, region=region)
    add("active_window", "Obtiene título y geometría de la ventana actualmente activa.", core.screen.active_window)
    add("analyze_screen", "Captura y analiza con visión; pide permiso antes de transmitir la imagen.",
        lambda question, region: core.vision.analyze(question, core.cancel, region), question=string(), region=region)
    add("search_web", "Busca información actual, con enlaces, extractos y errores por fuente.", lambda query: core.web.search(query, core.cancel), query=string(max_length=600))
    add("mouse_click", "Un clic en la ventana exacta indicada; revisa posibles consecuencias.", core.automation.mouse_click, Risk.MEDIUM,
        window=window, x={"type": "integer"}, y={"type": "integer"}, button={"type": "string", "enum": ["left", "right"]})
    add("move_mouse", "Mueve el puntero dentro de la ventana autorizada.", core.automation.move_mouse, Risk.MEDIUM, window=window, x={"type": "integer"}, y={"type": "integer"})
    add("type_text", "Escribe texto Unicode sin Enter; confirmación explícita.", core.automation.type_text, Risk.HIGH, window=window, text=string(max_length=2000))
    add("press_keys", "Envía una tecla o un atajo a una ventana; Enter/Delete requieren confirmación explícita.", core.automation.press_keys, Risk.MEDIUM,
        window=window, keys={"type": "array", "items": string(max_length=20), "minItems": 1, "maxItems": 4})
    add("remember", "Guarda un recuerdo pedido explícitamente por el usuario.", core.memory.remember, Risk.MEDIUM, key=string(max_length=150), value=string())
    add("recall", "Busca recuerdos por clave/texto; cadena vacía devuelve recientes.", core.memory.recall, key={"type": "string", "maxLength": 150})
    add("forget", "Elimina un recuerdo por su clave exacta.", core.memory.forget, Risk.MEDIUM, key=string(max_length=150))
