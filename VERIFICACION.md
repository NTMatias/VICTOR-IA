# Verificación v6 — 26/09/2026 — solo remoto

## Ejecutado en este entorno

- VICTOR_IA_v6.zip generado e inspeccionado: 88 archivos, 76 módulos Python, CRC correcto; exclusión de .venv, data, .env y cachés. Las imágenes CAPTURAS_V5 son históricas, no pruebas nuevas del remoto.
- **97 pruebas aprobadas en 31,385 s:** las 83 existentes y 14 nuevas del remoto. `python -m compileall -q main.py victor tests`: salida 0. No se instalaron ni reinstalaron dependencias.
- Node 24.18 ejecutó el codec real de JavaScript: diferencias de texto, Unicode, salto de línea/Tab, borrado, orden/ACK WebSocket, rechazo y descarte de cola. El JavaScript completo extraído de la página pasó `node --check`. Node es solo una dependencia de esa prueba de desarrollo, no de la app.
- Pruebas Python: todas las permutaciones de los atajos peligrosos; alias y teclas ordinarias; rechazo de campos extras/caracteres de control/secuencias inválidas; UTF-16 y tamaño de INPUT; identidad HWND/PID con título mutable; riesgo y ámbito de autorización; revocación tras confirmar; parada antes de consumir cola; worker de teclado libre del estado busy de VictorCore; lock de sesión libre mientras espera aprobación.
- FastAPI TestClient ejecutó autenticación del WebSocket `/keyboard`, vinculación a la IP del dispositivo, JSON real, ACK y ping/pong. Backend de entrada y sonda de foco simulados: NO se enviaron teclas ni se accedió al escritorio. Se comprobó cierre de trabajadores. No equivale a una prueba TLS/Wi-Fi con teléfono.
- La caducidad del certificado se comprobó asignando una fecha vencida a la política, no esperando un certificado real ni probando avisos nativos del navegador.
- Las pruebas existentes de mapeo táctil, límites de ventana y captura siguieron pasando con sus mocks originales. Las trazas MSS/ImageGrab de esos tests son fallos inducidos: no hubo intentos nuevos de captura real ni diagnóstico de CodexSandboxDesktop.
- Se corrigieron dos fallos encontrados por los tests nuevos: codificación cp1252 del proceso Node (ahora UTF-8 explícito) y limpieza al cancelar el scope del WebSocket. Se repitieron primero esos tests afectados y después la suite completa.

## Alcance y arquitectura

Comparación exacta contra ZIP v5: solo cambiaron cuatro módulos existentes: `integrations/local_remote.py`, `integrations/remote_view.py`, `system/input_automation.py` y el bloque puntual de `security.py`. **core.py, theme.py, Spotify, GUI, voz y todos los demás módulos existentes son idénticos**. Las pruebas anteriores no se editaron. Se añadieron módulos dedicados al teclado, foco y tests.

- `/control` mantiene el ratón/confirmaciones del orquestador existente; `/screen` mantiene su worker de captura. `/keyboard` usa una cola ordenada acotada y worker propios, sin pasar por busy de VictorCore. Cada socket tiene su tráfico independiente. Los locks de sesiones solo protegen acceso breve a diccionarios; no abarcan SendInput, aprobaciones ni la captura.
- Se evita el retardo de 0,5 s de activación y la pausa global PyAutoGUI por cada letra. Los paquetes normales exigen que la ventana autorizada siga activa; una aprobación alta puede devolver el foco únicamente a la ventana autorizada. Se usa la identidad HWND/PID para soportar cambios de título sin escribir en otra ventana.
- El único bypass de diálogo es `remote_keyboard_input`, MEDIO, origen local_web, con capability de teclado creada por el servidor y validada contra la sesión QR. No se aplica a ratón, local, Telegram o riesgo ALTO. La autorización/rechazo y ejecución quedan registradas sin el contenido de las teclas normales.
- Código: `keyboard_protocol.py` (schema/riesgos), `keyboard_worker.py` (cola/autorización), `keyboard_socket.py` (WS/ACK/vida), `keyboard_client.py` (codec/cliente JS), `remote_input.py` (SendInput), `remote_focus.py` (UI Automation/Win32), y adaptación de `remote_view.py`. La entrada Unicode sigue el mismo mecanismo nativo que type_text, sin portapapeles.
- Foco en subproceso oculto: hasta 8 s para inicio y 2 s por respuesta; si se bloquea se termina y queda Teclado manual. Se detecta el elemento editable, no solo la ventana. No se lee su texto. WebSocket con latido, timeout de apertura y mensajes de reconexión/HTTPS; la cola no se reenvía tras perder ACK. Certificado vencido revoca autorización y se regenera al reiniciar el servidor.

## Solo verificable por el propietario en su PC/celular

Se conserva como válida la prueba previa del propietario: streaming y ratón ya funcionaban en su PC real. Aquí NO se ejecutaron MSS/ImageGrab, SendInput real, movimientos/clics, UI Automation sobre aplicaciones reales, teclado móvil, IME/autocorrección del dispositivo, TLS real, desconexión Wi-Fi física ni medidas de latencia. No se reintentó resolver el aislamiento conocido.

La apertura automática depende de que la aplicación exponga un campo editable y de la política de foco del navegador móvil; iOS y otros navegadores pueden requerir tocar Teclado. Los atajos Ctrl+Alt+Supr/Power no son sintetizables mediante SendInput: se informa sin fingir ejecución. La gestión de otras aplicaciones elevadas depende de las restricciones de Windows; no se eleva el asistente.

## Pasos exactos de aceptación manual

1. Cierra VICTOR y la pestaña remota antigua del celular. Actualiza el código desde v6 conservando tu `.env`, `data/` y `.venv`. Ejecuta `iniciar.bat` en tu escritorio normal de Windows; no necesitas reinstalar dependencias ya disponibles.
2. Conecta PC y celular a la misma Wi-Fi. Abre Bloc de notas con un documento vacío. Anota el título exacto de su ventana (no solo el nombre de la aplicación).
3. En VICTOR: ☰ → **Conectar → Activar / detener remoto HTTPS**. Espera el aviso de servidor listo y pulsa **Mostrar QR local**. Escanea el QR nuevo antes de 120 s.
4. La dirección debe coincidir con la IP del PC mostrada por VICTOR: `https://<IP-del-PC>:8443/#<código>`, o el puerto configurado en REMOTE_PORT. En el aviso de certificado autofirmado, usa Avanzado → Continuar a esa IP (en Safari, Mostrar detalles → Visitar sitio web, si está disponible). Acepta solo la IP mostrada en tu PC. Si el certificado caducó, detén/inicia HTTPS en el PC para regenerarlo y escanea otro QR. No desactives la validación global del navegador. Si Windows pregunta por firewall, permite Python solo en tu red privada de confianza.
5. Autoriza en el PC compartir pantalla. En el campo superior del móvil introduce el título exacto de Bloc de notas. Debes ver la imagen del PC y el mensaje **Teclado conectado · QR autorizado**. Usa Renovar pantalla · 60 s cuando venza la autorización de streaming.
6. Toca el área de texto de Bloc de notas sobre la imagen remota y confirma ese clic en el PC (su riesgo MEDIO no cambió). Una vez aplicado, se detectará el campo mediante UI Automation/Win32 cuando la aplicación lo exponga. Si el teclado nativo no se abre automáticamente, pulsa **Teclado**: algunos navegadores móviles exigen ese gesto directo. También puedes enfocar inicialmente el documento desde el PC y pulsar Teclado en el móvil.
7. Escribe lentamente `Hola áéñ 123 !` y después una frase a tu ritmo habitual. Debe aparecer en Bloc de notas sin escribir EJECUTAR por palabra. Prueba un emoji y el método de composición de tu teclado. La composición IME se envía al confirmar el carácter, no durante sus candidatos provisionales. El cambio de título de Bloc de notas al editar no debe cortar la escritura.
8. Prueba los botones Intro, Retroceso, Escape y flechas. Marca Ctrl y pulsa A: debe seleccionar todo en Bloc de notas; desmarca Ctrl después. Puedes marcar Alt/Shift y usar los demás botones. Los modificadores solo existen durante cada atajo completo, no quedan mantenidos en el PC. Los botones A/C/V permiten selección/copia/pegado con Ctrl. Pegar contenido se ejecuta en el PC con su portapapeles.
9. Para probar la separación de riesgos, con el documento de prueba marca Ctrl+Shift y pulsa Escape: VICTOR debe pedir **EJECUTAR** en el PC. Primero recházalo: no debe abrirse el Administrador de tareas y el teclado se detendrá sin repetir entradas. Vuelve a emparejar para continuar. Si decides aprobar después, revisa la ventana y escribe EJECUTAR; la combinación se enviará. Alt+F4 también exige confirmación y puede cerrar la ventana: no lo pruebes sobre trabajo sin guardar. Ctrl+Alt+Supr exige confirmación pero Windows bloquea su síntesis: se mostrará una explicación, no se fingirá que se ejecutó.
10. Desactiva Wi-Fi del móvil unos segundos. Debe aparecer un aviso de desconexión en vez de quedarse esperando indefinidamente (detección por latido: hasta unos 15 s, más la planificación del navegador). No se reenviarán teclas pendientes al reconectar. Restaura Wi-Fi, genera otro QR desde el PC y abre una sesión nueva. La sesión vence a los diez minutos. **Detener** en la página remota o desactivar HTTPS en el PC revoca el teclado y el resto del remoto.

## Historial de verificación v5 (sus limitaciones de teclado quedan sustituidas por v6)

# Verificación v5 — 25/09/2026

## Resultado ejecutado, sin atribuir pruebas ajenas

- Suite completa: **83 pruebas aprobadas en 23,887 s**. Siete pruebas nuevas cubren variantes del wake word, aviso tras fallos, caché incompleta/local, auditoría acotada, predicción/rechazo Spotify, debounce, presentación y diagnóstico sin credenciales ni ejecución de herramientas. La salida de pruebas contiene excepciones inducidas por mocks; no son fallos de la suite.
- `verificar.bat --sin-pausa`: salida 0. Ejecutó `python -m compileall -q main.py victor tests` y los imports esenciales. La suite también importa todos los módulos. No se reinstalaron dependencias.
- Ventana Qt real abierta y cerrada limpiamente; capturas propias `CAPTURAS_V5/principal.png`, `estrecha.png` y `preparacion.png`. Métricas visibles proceden de psutil; el panel de preparación se capturó con un perfil temporal sin cuentas ni modelo, no con datos de usuario.
- El script de humo no comprueba cuentas ni dispositivos: lo dice en su salida.
- ZIP v5 generado con 81 archivos; CRC e integridad aprobados. Empaquetado por lista de inclusión, sin .venv, data, modelos, .env ni cachés. Se incluyen verificar.bat y tres capturas propias.
- Comparación byte a byte con ZIP v4: core.py, security.py, local_remote.py, remote_view.py, remote_touch.py, remote_page.py, google.py, spotify.py e input_automation.py **idénticos**. Se conserva la arquitectura, OAuth, seguridad y remoto que el usuario ya probó en su PC real.

## P1 — referencia recibida y medida directamente

Se abrió la imagen real Nextendo (1568×724), se inspeccionaron sus píxeles y se midieron las máscaras de título y punto con Pillow/NumPy. Límites con tolerancia ±1–2 px por suavizado:

| Elemento | Medición en Nextendo |
|---|---|
| Hero | x321..1239, y92..223; aproximadamente 918×131 px |
| Tinta del título | x349..978, y122..156; 35 px de alto visible |
| Resumen | x346..1214, y267..343; 868×76 px |
| Punto verde | x365..379, y298..312; 15×15 px |
| Primera tarjeta | x346..776, y394..453; 430×59 px |
| Separación columnas/filas | 8 px / 8 px |
| Radios aproximados | Hero 26, resumen 20, tarjetas 14 px |

El raster NO contiene metadatos de familia tipográfica ni font-weight: no es posible medir un valor CSS 700/800 exacto a partir de él. Se observa un título muy grueso, de trazo ancho y redondeado. VICTOR usa peso 800 declarado y QFont ExtraBold, tamaño 44 px en ancho y 28 px en angosto; conserva la fuente disponible de Windows. La altura de tinta no equivale al tamaño CSS.

Comparación de la captura propia final: mismo orden hero/descripción → resumen/punto → encabezado → dos columnas; mismos radios 26/20/14, punto 15 y hueco 8 entre tarjetas. Las métricas ponen icono/detalle a la izquierda y valor a la derecha. Diferencias: VICTOR conserva su paleta azul (sin degradado púrpura), símbolos en vez de carátulas de juegos, cuatro tarjetas y un área de chat. Su fuente de Windows no es idéntica a la referencia, los títulos de métricas son más pequeños y las tarjetas se adaptan al ancho disponible. No se promete una réplica píxel por píxel.

## P2 — remoto conservado; diagnóstico concreto del escritorio del agente

**Evidencia del usuario:** pantalla del PC en el celular y ratón táctil ya funcionan en su PC real. Se reconoce como verificación aportada por él; no se trata como función rota.

Prueba nueva en este proceso:
- MSS: `ScreenShotError: Windows graphics function failed (no error provided): BitBlt`.
- Pillow ImageGrab: `OSError: screen grab failed`.
- GetProcessWindowStation: `WinSta0`.
- GetThreadDesktop: `CodexSandboxDesktop-163b71cc6e630ea8b43f7939ca782a83`.
- OpenInputDesktop: `Default`.
- Sesión del proceso = sesión de consola activa = 1; no es una sesión de Escritorio Remoto.

La diferencia comprobada es el **escritorio aislado de Codex frente al escritorio interactivo Default**, no un PC sin monitor ni una falta hipotética de mss. Las dos APIs no pudieron capturar desde ese contexto. Windows no proporcionó un código adicional para BitBlt; no se inventa una causa interna del controlador. `QWidget.grab()` sí capturó las ventanas propias: no es una captura de todo el escritorio. No se intentó saltar ese aislamiento.

No se generó un QR nuevo persistente para la entrega: dura 120 s y no daría una prueba real de pantalla/celular en este contexto. Las pruebas de rutas, seguridad y geometría existentes pasaron dentro de la suite. No se atribuye una prueba nueva con celular, teclado nativo ni Wi-Fi al agente.

Piezas para diagnóstico en el PC normal (líneas de esta entrega):
- `victor/integrations/local_remote.py:72`: QR; `:157`: HTTPS/WSS; `:247`: permiso/vida del stream; `:261`: worker de captura independiente.
- `victor/integrations/remote_view.py:23`: coordenadas y bandas por aspect ratio; `:24`: toque; `:25–27`: gestos; `:28`: foco del input/teclado nativo; `:29–33`: texto/IME/Retroceso/Intro.
- `victor/integrations/remote_touch.py:10`: geometría real, origen virtual, antigüedad y validación.
- `victor/system/input_automation.py:45`: escritura Unicode; `:72`: teclas.
- `victor/tools/builtins.py:44`: type_text conserva riesgo ALTO. Mouse/tacto mantienen MEDIO.

**Límite explícito:** el texto móvil se agrupa tras 450 ms y requiere EJECUTAR en el PC; no es escritura instantánea sin confirmación. Se conserva el botón Teclado, no se detecta automáticamente que un clic haya enfocado un campo. Relajar esa política rompería el requisito de conservar los niveles y security.py. El flujo supervisado existente se conserva, pero esos dos aspectos de la experiencia solicitada no se declaran completados.

## P3 — Spotify

Predicción visual de reproducir/pausar inmediata y mensaje de orden pendiente; no se inventa la próxima pista. Los controles continúan pasando por el mismo registro/confirmación. Rechazo o fallo restaura el estado confirmado; tool_result reconcilia datos reales. Polling en worker: 2 s reproduciendo, 5 s pausado, 30 s tras error, con refresco al terminar una orden. Volumen: 300 ms de debounce, no envía mientras se mantiene el arrastre y conserva solo el último valor. Ningún OAuth ni operación de SpotifyManager cambió.

Mediciones reales **solo de UI con API simulada**: callback de predicción 0,47 ms en prueba focal, 0,11 ms en la primera suite y **0,20 ms en la suite final**. Un arrastre de 40 valores produjo una sola orden con el último valor. No hay token Spotify autorizado disponible en este perfil del agente, por lo que NO se midieron latencia HTTP, cambio real de canción ni tiempo acústico. Esto no invalida la cuenta que el usuario ya conectó en su instalación.

## P4 — qué se ejecutó y qué falta

- **A:** worker de descarga real de Whisper base completó 147.882.941 bytes (~148 MB) desde Hugging Face tras conceder red; primera tentativa sin red falló de forma clara. Se descargaron cuatro archivos, se cargó WhisperModel CPU int8 y se ejecutó inferencia sobre 1 s de silencio: 0 segmentos, 1,45 s incluyendo carga. No equivale a medir precisión de voz. La descarga queda en data/models (excluida del ZIP); el usuario pulsa el botón una vez en una instalación limpia. QProcess mantiene la GUI libre y se termina al cerrar, con límite de tiempo. Progreso basado en bytes cuando el SDK los informa; caché incompleta no habilita la voz. No se hizo una nueva grabación ni una frase real de extremo a extremo. La descarga fría real se invocó por el mismo worker desde consola. Después se pulsó el botón real de la GUI con el destino de prueba apuntando al modelo ya descargado: QProcess completó, activó el estado disponible y cerró limpiamente. La GUI siguió procesando eventos. Esto prueba reanudación/caché desde el botón; no se duplicó una descarga fría de 148 MB ni se simuló que se hubiese hecho.
- **B:** case/acentos y variantes delimitadas Bictor/Viktor/Vitor/Vicktor; tras tres fallos sugiere proximidad/dispositivo. Pruebas con transcripciones controladas, no ensayo acústico en vivo. No confunde victorioso/victoria ni confirmaciones con wake word.
- **C:** botón ⛶ / F11, reversible; prueba GUI aprobada.
- **D:** panel lee un sufijo acotado del log y muestra hasta 20 eventos de ejecución o confirmación/rechazo. No muestra líneas arbitrarias que puedan contener secretos. Prueba con registros controlados aprobada; perfil de captura sin acciones muestra lista vacía, no inventada.
- **E:** prechequeo automático local y botón de conexiones reales en otro QProcess: respuesta breve del proveedor seleccionado sin herramientas, API Spotify, Google Calendar y getMe de Telegram. Límite global 90 s y terminación al cerrar. Se ejecutó el botón GUI real sin credenciales y se obtuvieron cinco resultados explícitos; además pruebas simuladas verifican que no se ejecuten herramientas devueltas por el modelo ni se impriman claves. Falta ejecutar esas consultas con cuentas autenticadas aquí. Gmail/Drive, audio y emparejamiento se distinguen de los servicios comprobados y no se dan por verificados.
- **F:** verificar.bat ejecutado correctamente; compilación e imports, sin instalar nada.

## Evidencia histórica v4 (no constituye nueva prueba v5)

# Verificación v4 — 25/09/2026

## Comprobado en este turno

- `python -m compileall -q main.py victor tests`: aprobado.
- Suite completa: **76 pruebas aprobadas**, 18,929 segundos. Incluye las 36 originales, todas las de v2/v3 y ocho nuevas de v4. Se corrigió un nombre de clase equivocado en el nuevo test (Reply); no fue un fallo de la aplicación.
- GUI real abierta/cerrada, revisión visual de cinco capturas propias incluidas, panel sin Tools, estilos, nombres legibles y tarjeta sin JSON, mini reproductor con ejemplo rotulado y vista de voz. Trabajadores cerrados correctamente.
- Cobertura comprobada de nombres amigables para todas las herramientas registradas; detalles de correo conservan destinatario y cuerpo completo. Spotify volumen es bajo; play/pausa/anterior/siguiente mantienen riesgo. Las pruebas no reprodujeron música de una cuenta real.
- Confirmación de voz probada con transcripciones simuladas y solicitud local activada: una frase sin esa vinculación no autoriza una acción. No se grabó de nuevo micrófono ni se descargaron modelos: no se repitió el trabajo anterior.
- Telegram probado con IA simulada: una frase libre llega al mismo generador; sin clave se emite error comprensible. Se probó la extracción del primer video con HTML de prueba. No se contactó un bot real ni se abrió/reprodujo un video real.
- Mapeo remoto probado con coordenadas negativas y rechazo de frames caducados; protocolo HTTPS/WebSocket conserva las pruebas anteriores. JavaScript pasó `node --check`; una prueba JS adicional verificó proporción de pantalla y bandas vacías. No se enviaron pulsaciones ni clics a aplicaciones personales.
- Comparación exacta con el ZIP v3: **google.py, spotify.py, core.py y security.py idénticos byte a byte**. Los flujos de autorización no se tocaron. El usuario informa que Google y Spotify ya funcionan con su cuenta real; se conserva esa verificación aportada por el usuario, sin atribuirla a una prueba nueva del agente.
- No se instalaron, reinstalaron ni cambiaron dependencias en este turno.

## Qué sigue sin comprobarse de extremo a extremo

En la carpeta y entorno accesibles al agente no hay token Google/Spotify, ID de cliente Spotify, token Telegram ni claves de IA. Esto no contradice que el usuario tenga otra instalación ya autorizada. Por ello el mini reproductor se capturó con datos de ejemplo visibles y no se volvió a abrir OAuth ni a reautorizar cuentas.

Pendientes: estado/carátula/controles Spotify reales, reconocimiento hablado de confirmaciones (incluida alta), frases libres con IA real y Telegram, reproducción del primer video y móvil real con tacto/teclado nativo/streaming. Las restricciones de captura del escritorio y micrófono/modelo documentadas en v3 no se declaran resueltas ni se repitieron sin necesidad.

La voz afirmativa solo autoriza después de activar su escucha explícitamente en el PC. El teclado móvil está sujeto a EJECUTAR: no promete escritura instantánea sin confirmación. No se midió latencia real del remoto en Wi-Fi.

## Alcance de cambios

Se retiró únicamente la UI manual de herramientas. Se añadieron módulos de presentación, mini reproductor, vista de voz y adaptadores de YouTube/tacto. El receptor de voz incorpora contexto de confirmación y el streaming añade metadatos de geometría; la autorización, orquestación y OAuth existentes se mantienen. Ningún dato de ejemplo se inyecta en la aplicación de producción.

## Evidencia anterior (histórica)

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
