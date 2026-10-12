# Verificación v3 — resultados de este turno

## Parte A: interfaz real

GUI abierta antes/después de modificarla, capturas propias a 1120 y 420 px y panel cerrado. Se revisaron visualmente. La prueba GUI comprueba ausencia de intersección panel/chat, botones de igual ancho, burbujas ≤70%, compositor alineado, permisos y cierre limpio. `INTERFAZ_V3.png` es una captura del widget Qt, no una captura del escritorio externo.

## Parte B: pruebas reales autorizadas

- Entorno observado: Windows, CPython 3.12.14, procesador Intel64 Family 6 Model 158 y **7,94 GB de RAM disponibles como total**. No se certifica un benchmark del i5-8400/16 GB descrito sin un modelo local.
- MSS: volvió a fallar `BitBlt` (Windows no proporcionó código adicional). ImageGrab: `screen grab failed`. El flujo `analyze_screen` también se intentó con esquema correcto y devolvió el error contenido. No hubo imagen ni respuesta real de visión.
- Calculadora: el lanzador devolvió PID, pero la comprobación no encontró ventana visible ni proceso persistente. Se mantiene como no verificado.
- Micrófono: se enumeraron dispositivos, incluido Realtek, y se completó la grabación de cinco segundos a 16 kHz. La transcripción falló porque no existe el modelo Whisper local. No se midió inferencia ni se afirmó reconocer una frase. Audio capturado solo en memoria, no incluido en ZIP.
- Voz: Edge generó un MP3 real; Qt llegó a `EndOfMedia`. Se detectó un bug: al terminar, el reproductor retenía el archivo y la limpieza producía WinError 32, activando erróneamente SAPI. Se corrigió liberando el backend Qt antes de borrar el temporal. La prueba completa posterior terminó con código 0. Audibilidad física no comprobable por el agente. SAPI por separado devolvió acceso denegado (-2147024891).
- Búsqueda ddgs real: fuentes HTML obtenidas y leídas, incluida docs.python.org. Aviso del almacén de certificados de Windows, sin impedir el resultado. El primer harness omitió `cancel`; se corrigió el harness, no la aplicación.
- IA: no hay claves OpenAI/Anthropic/Gemini presentes; Ollama local no respondió. No se pudo completar «hola» contra un modelo. Tampoco hay configuración Google, Telegram ni Spotify en este contexto; no se probaron cuentas reales.
- Volumen: lectura inicial 100; se bajó realmente a 98 y se restauró a 100. El primer intento de subir no podía aumentar porque ya estaba al máximo; no se cuenta como cambio.

## Parte C: Google y remoto

- Google implementado con OAuth independiente, tokens DPAPI, REST con timeouts y herramientas de Gmail/Calendar/Drive. Tests con mocks para lectura, consultas escapadas, MIME y bloqueo de envío sin confirmación. **No se enviaron correos ni se completó OAuth real**: faltan credenciales y DPAPI no está disponible en este contexto.
- Prueba nativa de DPAPI para la clave TLS denegada por Windows. El token OAuth sigue sin poder degradarse a texto plano. TLS admite clave efímera borrada al detener el servidor, con aviso visible.
- **HTTPS real aprobado**: certificado generado, respuesta 200 sobre IP privada LAN, contenido de página con trackpad, emparejamiento WebSocket y rechazo de `run_terminal` por la lista de herramientas del canal. El servidor terminó. Uvicorn registró un timeout de apagado elegante con cero tareas pendientes; la comprobación confirmó que el hilo dejó de ejecutarse.
- Protocolo y seguridad probados con TestClient: Origin ajeno rechazado, QR de un uso, revocación, caducidad, riesgos altos confirmados únicamente en PC, límites de puntero y trabajador JPEG independiente. No se movió el puntero ni se escribió en aplicaciones personales durante estos tests; la captura JPEG fue simulada.
- Pendiente real: acceso desde celular, aceptación de certificado en su navegador, acciones del trackpad/teclado y streaming de escritorio (captura bloqueada). No se declara rendimiento de 10 fps comprobado.

## Compilación y dependencias

Se mantiene la base de pruebas anterior. Suite v3: **68 pruebas aprobadas**, incluidas las 36 originales, las de v2 y nueve de servicios v3. Compilación e imports comprobados; `pip check` sin conflictos. Las trazas de tests de fallos de captura son esperadas.

No se ejecutó de nuevo el instalador completo. Se instalaron dependencias nuevas desde wheels oficiales. **Incidencia respecto a la instrucción de conservar paquetes:** las restricciones iniciales hicieron que pip cambiara websockets 16.1.1→15.0.1 y cryptography 50.0.1→49.0.0. No se ocultó ni se volvió a reinstalar para deshacerlo; la suite y pip check pasaron. El instalador v3 amplía rangos para admitir también las versiones anteriores y evitar esa sustitución innecesaria en el PC del usuario.

El ZIP excluye .venv, data, .env, certificados, tokens, grabaciones, modelos y cachés. Incluye una captura propia de la interfaz con una consulta de RAM de prueba.

---
## Registro histórico v2/v1 (no describe nuevas pruebas v3)

# Verificación de VICTOR.IA v2 — 24/09/2026

Entorno: Windows, Python 3.12.14 de 64 bits. Se trabajó sobre el proyecto existente; se conservaron las 36 pruebas originales. No se reinstalaron dependencias existentes: solo se incorporaron las nuevas mediante wheels oficiales.

## Resultado final v2

- `python -m compileall -q main.py victor tests`: aprobado.
- `python -m unittest discover -s tests -v`: **59 pruebas aprobadas**, 11,807 segundos. Incluye las 36 originales. Los errores impresos por tests de captura son fallos simulados esperados y contenidos.
- `pip check`: sin dependencias rotas. Imports reales de todos los módulos y de faster-whisper, edge-tts, python-telegram-bot y spotipy: aprobados.
- Ventana real PySide6 abierta/cerrada; ancho de 420 px, RAM real desde chat, panel lateral, guardado y confirmación EJECUTAR comprobados. Los trabajadores terminaron. Smoke de main.py y captura del widget revisada durante bloque 2; no se repitió sin necesidad.
- Bloque 6: diez pruebas con servicios simulados aprobadas. Rutas Google, Spotify DTMF, volumen 30 y visión; emparejamiento de un uso, expiración, rate limit, pausa, allowlist, texto/nota de voz al mismo flujo, confirmación ligada al remitente, rechazo de alto riesgo remoto, autorización en PC y revocación durante espera. Spotify contrasta pista solicitada con estado devuelto. Ningún bot/cuenta real fue contactado en estos tests.
- Búsqueda ddgs real: cuatro fuentes HTML leídas. Lectura real de volumen mediante pycaw/comtypes: correcta; no se cambió el volumen del usuario.

## No verificado con servicio real / limitaciones

- **Telegram y Spotify: no verificado con servicio real.** Configura tus credenciales y prueba emparejamiento, audio, OAuth, reproducción y entrega de captura. OAuth DPAPI está implementado pero no se ha completado con una cuenta real.
- Sin llamadas reales a OpenAI, Anthropic, Gemini ni inferencia Ollama. Adaptadores y fallback se probaron con respuestas simuladas.
- Whisper, micrófono, wake word hablada y salida audible edge/SAPI no verificados de extremo a extremo. No se descargaron modelos ni se grabó audio personal.
- MSS e ImageGrab no pudieron capturar el escritorio de este entorno. El respaldo y errores se probaron con mocks; la captura del widget Qt sí funcionó. No se analizó una pantalla real con IA.
- Calculadora aceptó el lanzamiento, pero no se pudo confirmar una ventana/proceso persistente. El resultado ahora lo advierte. No se declara resuelto el bloqueo del entorno.
- No se enviaron clics/teclas a aplicaciones personales ni se modificó su volumen.
- No se volvió a ejecutar instalar.bat ni reinstalar dependencias ya comprobadas. El script incorpora nuevas dependencias opcionales; la instalación limpia online completa con pip sigue pendiente de verificación. Se comprobaron los imports y coherencia del entorno resultante.
- Google OAuth y remoto web/QR/HTTPS móvil quedaron diferidos por ser opcionales. No hay implementaciones vacías ni controles que aparenten esas funciones.

## Evidencia anterior por bloques y v1 (histórica)

El registro siguiente conserva lo realizado antes. Las referencias a CustomTkinter, Tcl y 36 pruebas describen v1, no la interfaz entregada en v2. Las limitaciones de búsqueda de v1 se superaron con ddgs; las capturas de escritorio siguen bloqueadas.

# Verificación de la entrega

## Evolución v2 (24 de septiembre de 2026)

Bloque 1 cerrado: 42 pruebas aprobadas (las 36 originales más seis nuevas). Se verificaron normalización de argumentos, devolución del esquema sin error técnico en GUI, límite de un reintento, alias locales, órdenes de volumen/web y preflight Ollama con HTTP simulado. ddgs 9.16 se instaló y realizó una búsqueda real: cuatro fuentes HTML obtenidas y leídas correctamente. Persistió un aviso del almacén de certificados del entorno, pero la operación finalizó. No se probó inferencia Ollama real ni GPU física; sus comprobaciones automáticas tienen timeout y error comprensible.

La evidencia siguiente pertenece a **v1** y no certifica por sí misma la nueva GUI ni las integraciones v2.

Bloque 2 cerrado: instalada únicamente la dependencia nueva PySide6 6.11.2 y sus componentes. Prueba Qt aprobada: ventana a 420 px, respuesta RAM real, panel lateral, guardado, confirmación alta y trabajadores cerrados. Smoke test real de main.py aprobado sin ajuste Tcl/Tk. Captura del widget Qt generada y revisada visualmente (940 × 880); esto no equivale a capturar el escritorio externo. Las métricas CPU/RAM/red mostradas son medidas reales. No se muestra tarjeta proactiva porque no hay una integración conectada que suministre datos.

Bloque 3 cerrado: cuatro pruebas aprobadas para valores predeterminados locales, ausencia de micrófono, seguimiento de órdenes sin nueva wake word y parámetros Whisper CPU/int8/local_files_only. Whisper se simuló en tests; no se descargaron modelos ni se grabó audio del usuario. edge-tts y su reproducción/respaldos necesitan verificación real; son opcionales y no intervienen en el arranque.

Bloque 4 cerrado: dos pruebas aprobadas para respaldo ImageGrab y error comprensible cuando fallan ambos capturadores. En comprobación real MSS e ImageGrab continuaron bloqueados por el entorno. pycaw/comtypes leyeron correctamente el volumen (sin modificarlo). La calculadora aceptó el lanzamiento, pero no apareció ventana ni proceso persistente verificable; ahora el resultado de la herramienta lo informa explícitamente. No se repitieron intentos sin cambios.

Bloque 5 opcional diferido: Google OAuth y control remoto web/QR no están implementados ni se anuncian como disponibles. La vía móvil de esta entrega será Telegram. Spotify se cubre en el bloque 6 obligatorio.

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
