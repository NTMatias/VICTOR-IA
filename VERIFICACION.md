# Verificación de la entrega

Entorno: Windows, CPython 3.12.14 de 64 bits. Verificación realizada durante la preparación del proyecto, 23–24 de septiembre de 2026.

## Comprobaciones realizadas y aprobadas

- `python -m compileall -q`: compilación de los archivos Python del proyecto.
- **36 pruebas automatizadas aprobadas**, sin claves ni llamadas de pago. Incluyen imports de todos los módulos, imports de los SDK oficiales, ensamblado de streaming/tool calls con respuestas simuladas, argumentos inválidos, denegación de permisos, cancelación, rutas protegidas, límites de archivos, ausencia de claves, fallback simulado, wake word, configuración, memoria, historial y resumen de contexto.
- `pip check`: no se encontraron dependencias rotas.
- **Ventana real CustomTkinter abierta y cerrada en Windows**, sin claves API. Visibilidad confirmada por Tk, título correcto, tamaño 1260 × 830 y 26 herramientas registradas.
- Integración GUI: consulta real de RAM desde el chat, reactivación del botón Enviar, apertura y guardado del panel de configuración, y cierre con trabajadores detenidos.
- Diálogo real de alto riesgo: botón de autorización inicialmente deshabilitado; una confirmación vacía no acepta; escribir `EJECUTAR` permite aceptar.
- `instalar.bat` e `iniciar.bat` terminaron con código **0**. El segundo abrió la ventana y ejecutó el modo de comprobación de arranque.
- Herramientas Windows: consulta de RAM/sistema y ejecución del diagnóstico `hostname` con resultado satisfactorio.
- Creación, copia, renombrado y movimiento de archivos desechables de prueba. No se tocaron documentos personales.
- **Papelera real**: un archivo creado exclusivamente para la prueba fue enviado mediante `send2trash`; desapareció de la carpeta de origen. Para esta prueba de integración se autorizó programáticamente esa única operación; el diálogo se comprobó por separado.
- Imports de las dependencias opcionales de ratón/teclado, ventanas, voz y volumen. `sounddevice` también pudo enumerar los dispositivos disponibles.

## Condiciones particulares de estas pruebas

El índice `/simple/` de PyPI se bloqueó en este entorno, aunque la descarga directa de archivos oficiales funcionó. Para verificar los scripts se usaron paquetes oficiales previamente descargados y `PIP_NO_INDEX`/`PIP_FIND_LINKS` en el proceso de prueba. **No se verificó una instalación online completa contra el índice estándar**. El instalador entregado usa pip normal y necesita Internet.

El runtime Python suministrado por el entorno tenía problemas resolviendo rutas absolutas de Tcl/Tk. La prueba utilizó una copia local de sus bibliotecas Tcl/Tk con rutas relativas mediante variables de entorno. No se modificó el código de la aplicación para simular la ventana, ni se incluyen esas bibliotecas de prueba en el ZIP. Una instalación estándar de Python con Tkinter es el requisito documentado.

Se corrigió un problema de limpieza de temporizadores encontrado al cerrar la GUI, y la prueba de integración posterior confirmó el cierre de los trabajadores.

## No verificado de extremo a extremo / bloqueado

- **OpenAI, Anthropic y Gemini con claves reales**: no se proporcionaron claves para realizar solicitudes. «Hola» con una cuenta válida y el fallback entre servicios reales siguen pendientes de verificación en la cuenta del usuario. Las pruebas de proveedores utilizaron respuestas simuladas, no un servicio real.
- **Ollama con un modelo descargado**: no se probó inferencia real ni visión local.
- **Capturas y visión**: Windows denegó la captura gráfica (`BitBlt`); el método alternativo de captura de evidencia también falló. Se verificó que el fallo de herramienta se contiene. No se pudo revisar una captura visual de la interfaz ni analizar una pantalla real.
- **Salida de voz SAPI**: el motor devolvió acceso denegado al consultar su voz en este entorno. No se verificó reproducción audible.
- **Micrófono, reconocimiento online/local y wake word hablada**: se comprobaron imports, enumeración de dispositivos y procesamiento de texto de activación; no se grabó ni transcribió voz real. Whisper no se descargó ni ejecutó.
- **Búsqueda web real**: se intentó una búsqueda, pero el motor encontró restricciones del almacén de certificados de Windows y no devolvió resultados. La aplicación informó del fallo. No se verificó una respuesta de IA basada en fuentes obtenidas en vivo.
- **Calculadora**: el lanzador `calc.exe` aceptó la solicitud y devolvió un PID. No se pudo confirmar una nueva ventana/proceso persistente; no se declara comprobada su apertura visual.
- **Control de volumen y automatización de aplicaciones personales**: imports comprobados; no se modificó el volumen ni se enviaron clics o teclas a aplicaciones del usuario.

## Límites intencionales

No se implementa ejecución arbitraria de shell, modificación del registro, instalación de software desde la IA ni elevación administrativa. La terminal admite únicamente cuatro diagnósticos de lista blanca. Las operaciones de mover/copiar/renombrar/eliminar trabajan con archivos individuales; no con árboles completos. Estos límites también se explican en el README.

El ZIP contiene el código, instaladores, documentación y pruebas. No incluye claves, historial de pruebas, capturas privadas, entornos virtuales, paquetes descargados ni modelos.
