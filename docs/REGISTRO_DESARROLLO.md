# Registro histórico de desarrollo

Las verificaciones descritas aquí corresponden a cada revisión y pueden usar fixtures. Esta información no promete acceso actual a todos los servicios. Se han omitido instrucciones operativas del PC y anonimizado rutas locales.

# VICTOR.IA — progreso y reanudación

## 12/10/2026 — Corrección real de Codex, recientes, imágenes y limpieza

- CLI local Codex actualizado de 0.142.5 a 0.162.1. Modelo global guardado `gpt-5.4` retirado: no se modifica configuración global; se consulta catálogo por app-server `initialize/initialized/model/list`, se selecciona recomendado/elección explícita y se pasa `--model` al TUI. Catálogo real incluye Sol/Astra/Luna y prueba real con `gpt-6.1-sol` respondió `OK`, sin herramientas/cambios. Cola/cancelación/timeout del probe, paginación y filtros de modelos probados con RPC real de fixture.
- WhatsApp: extracción de recientes ignora SVG/data-icon y mantiene emoji/texto humano. Fixture real WebView2 con títulos SVG `ic-image`, `wds-ic-read` demuestra previews limpias. Fixtures de host ahora se compilan en carpeta temporal; fuera de la app. Se eliminó WhatsAppPanel/ContactRow nativo retirado, su test obsoleto, bridge antiguo y cuatro ejecutables viejos/de prueba. Widget reciente y WebHost activos conservados.
- Imágenes: botón visible en Inicio; pregunta de capacidad atendida localmente sin gastar IA, contexto del chat actualizado. Selector prioriza clave disponible, admite elegir proveedor, muestra requisitos y enlace de facturación. Prueba REAL del modelo Gemini Nano Banana 2.1 devuelve 429 por cuota; no se consiguió generar imagen con la cuota actual. No se cambió facturación ni de proveedor automáticamente. El error explica requisitos; OpenAI necesita su clave/saldo propios. No afirmar éxito de imagen real basándose en fixtures.
- 53 pruebas dirigidas aprobadas (Codex modelos, imágenes, WhatsApp Web, diseño, GUI, cuentas y credenciales); 23 afectadas repetidas después de la carga diferida de terminales, aprobadas. pip check/compileall correctos. QA visual oscuro/claro/560px y TUI Codex REAL integrado, catálogo visible y cierre limpio comprobados en app aislada. Los terminales no crean sus renderizadores Chromium hasta entrar en su sección. Auditoría de clases confirmó SpotifyList sin ninguna referencia; retirado, vistas activas de Spotify conservadas.

## 12/10/2026 — Revisión actual: fuentes, imágenes, agentes y Gemini solo por API

- Gemini: eliminado el módulo de cuenta/CLI, sin login Google en ajustes ni registro en AIManager. Los ajustes antiguos pasan a `api` conservando las demás preferencias. No se borran sesiones personales previas. Botones oficiales de Google AI Studio junto a instrucciones y al campo de clave. Se mantiene Gemini para chat, visión e imágenes mediante API key. Gmail/Calendar/Drive independientes.
- Fuente Segoe UI con antialiasing/hinting nativo; diseño y paleta Grafito conservados. Conversación 15 px, texto de controles 14 px.
- Imágenes OpenAI/Gemini: selector de proveedor/modelo/descripción, clave obligatoria, confirmación mediante Generar, proceso cancelable, validación de PNG/JPEG/WebP, historial con adjuntos locales, ampliar y guardar PNG. REST Gemini usa los pasos `model_output` documentados. Se resuelve recargar una conversación durante una generación sin acceder a un widget eliminado.
- Agentes de programación: Codex y Claude Code oficiales completos dentro de xterm.js/ConPTY; carpeta de proyecto, herramientas/autenticación/permisos propios del CLI, adjuntar rutas, entrada Unicode, copiar, interrumpir y cerrar. Dependencias instaladas en el proyecto. Claude Code requiere Git Bash, ya presente en esta PC; documentado para otras PCs.
- Revisión de interfaz aislada, capturas e inicio/cierre limpio; ambos CLIs verificaron `--version` dentro de ConPTY. No se ejecutaron tareas de IA ni solicitudes de imágenes facturadas. Las pruebas de API y OAuth son fixtures, no verificación de acceso real a una cuenta.
- 55 pruebas distintas dirigidas aprobadas; cancelación de un proceso real de fixture y recarga de conversación durante generación comprobadas. Compilación y `pip check` correctos.

## 12/10/2026 — Cuentas de IA y preparación USB


- Cuenta ChatGPT: SIWC oficial dinámico, loopback 127.0.0.1, PKCE S256/state/nonce, validación JWT RS256 con JWKS/issuer/audiencia/expiración, scopes concedidos, modelos con visibility=list y slug. Registro/host estables, perfiles separados, DPAPI, renovación atómica y bloqueo entre procesos, revocación al cerrar sesión. Responses público con store=false/stream=true, historial explícito y herramientas adicionales del rol developer; completar únicamente tras response.completed. Cancelación y errores/quota sin usar endpoints privados, cookies ni claves de otros programas.
- Google: Gemini CLI 0.63.0 instalado localmente, perfil propio con almacenamiento cifrado oficial. Login mediante terminal oficial y verificación de respuesta posterior; inferencia oculta por -p/stream-json y contexto de VICTOR. Sin herramientas, comandos, MCP, extensiones, hooks ni skills; allowlist efectiva vacía + deny-all. Modelo Automático; cuenta desconectable sin borrar sesiones ajenas. API keys y modelos API independientes; conservar Ollama/Claude y funciones locales/voz/visión. No se editó core.py, security.py ni theme.py.
- UI adaptada a Grafito con controles de cuenta, estado real, modelos, cambio de cuenta, gestión de uso, cierre, claves ocultables y prueba de API con confirmación de posible cargo. Cambio de método API pide confirmación. No hay fallback de cuenta a pago. Se corrigió desbordamiento de combos en anchura 560px y estados de sesión corrupta sin cerrar la app.
- 101 pruebas dirigidas (28 cuentas/credenciales/GUI/Gemini + 73 voz/Spotify/WhatsApp) aprobadas, con repeticiones de grupos afectados; pip check y compileall correctos. OAuth firmado y loopback real con credenciales sintéticas, CLI mediante fixtures. Autorización y elegibilidad de una suscripción real no comprobadas; las realiza el usuario desde ajustes.
- Portátil: Python 3.12 x64 completo y aislado mediante _pth, dependencias instaladas, Whisper base, Node 24.18.0/Gemini CLI y WebView2 Fixed Runtime 155.0.4283.45 oficial. Configuración limpia sin claves/sesiones/historial; manifest SHA256 y ZIP. Lanzador prepara los permisos de lectura AppContainer del runtime en Windows 10 y requiere una carpeta local NTFS (extraer en Escritorio). El intérprete incluido verificó imports, CLI, Silero, transcripción offline de fixture y QR real de WhatsApp con el runtime fijo. La USB solicitada es <USB> copiar solo el paquete limpio y guía después de verificación.

## 11/10/2026 — Regreso a WhatsApp Web y rediseño de recientes

- WhatsAppEmbed vuelve a un WebView2 visible y flexible, sin la espera/editor nativos que fallaban al abrir un chat. Mantiene `data/whatsapp_webview2`. Nuevo host `WhatsAppWebHost.exe`; perfil y archivos de los hosts antiguos no se borraron.
- `whatsapp_theme.js` modifica solo colores: paleta Grafito oscuro/claro, variables legacy y actuales WDS con variantes RGB, fondos, compositor, burbujas y acentos. Adaptación de contraste para vinculación; QR, iconos y contenido gráfico se conservan. No cambia el DOM de interacción de las conversaciones.
- `whatsapp_recent.js` observa únicamente vistas previas, nombres, horas y contadores. Elimina del preview el nodo del badge y preserva números legítimos/emoji. No lee todo el historial ni envía contenido a IA. Apertura de la fila mediante eventos de ratón del navegador, con coordenadas de un elemento actual y origen oficial validado. IDs por elemento evitan mezclar dos contactos con el mismo nombre.
- Recientes: avatar, nombre/hora, preview elidido y badge azul independiente; filas planas con separador, sin tarjetas dentro de tarjetas. Estados de sincronización y vacío, tema claro/oscuro y actualización sin reconstruir filas si no hay cambios.
- Pruebas: cuatro de WhatsApp aprobadas en 14,757 s; trece de regresión en 14,209 s. Fixture en navegador real confirma clic confiable (`isTrusted`), chat con emoji, recepción mientras Inicio está abierto, contadores y paletas. Vista pública/QR reales sin vincular; capturas inspeccionadas. No se mandaron mensajes reales ni se alteraron datos personales.

## 11/10/2026 — WhatsApp nativo y mensajes recientes en Inicio

- Se reemplazó la página visible por `whatsapp_panel.py`: chats/contactos y buscador, historial de mensajes con burbujas de la paleta de VICTOR, editor, botón Enviar, carga anterior y borradores por conversación. Mismo estilo en oscuro/claro; no se editó `theme.py`.
- Tarjeta Inicio bajo Actividad reciente: dos conversaciones recientes, última vista previa, contadores sin leer y clic para abrir el chat. Columna derecha desplazable en pantallas de poca altura; no corta las tarjetas. Se conserva el mini reproductor.
- `WhatsAppNativeHost.exe` usa el perfil anterior y un viewport fuera de la interfaz, con `whatsapp_bridge.js`. La comunicación WebView2 valida el origen oficial. El puente observa datos renderizados, comparte QR/chats/contactos/mensajes y ejecuta acciones concretas; no emplea Store/API privada ni expone ejecución libre de scripts a la UI. Contactos y mensajes se conservan temporalmente en memoria, sin copiar al chat/historial ni enviar a IA.
- Apertura y envío verifican nombre/contexto, id de conversación y nueva burbuja saliente; los ids de solicitud evitan duplicar envíos. Un fallo conserva el borrador, sin reintento automático. La confirmación no borra texto nuevo ni el borrador de otra conversación. HTML recibido se dibuja como texto literal. Las búsquedas filtradas no reemplazan la tarjeta de recientes.
- Pruebas: pase de 17 casos aprobado en 28,597 s, incluyendo QR real, cliente nativo con navegador y datos ficticios, mensajes mientras está en Inicio, contactos y cambio de tema, borradores, contenido no ejecutable y regresiones de Spotify/GUI/niveles. Se añadieron después comprobaciones de búsqueda sin tildes y rechazo del destinatario equivocado, verificadas en el caso de integración.
- Vistas inspeccionadas a 1640×950 y 1366×768; se corrigieron widgets obsoletos aún visibles, anchura de burbujas y recorte de recientes en la columna derecha. La sesión real del propietario no se usó para enviar mensajes. Requiere reinicio para usar el nuevo host y panel; QR solo si la sesión conservada no sigue vinculada.

Limitaciones concretas: adaptación del DOM de WhatsApp sujeta a cambios del sitio; sincronización de contactos/historial real pendiente de la cuenta del propietario; envío de texto y marcadores de multimedia, sin reproducción de audio ni descarga de adjuntos en esta vista.

## 11/10/2026 — Título/artista y pestaña WhatsApp

- `music_match.py` reconoce títulos con créditos de colaboración sin confundir esos créditos con el título solicitado; comprueba todos los artistas del catálogo, conserva las etiquetas de versiones (remix/live/acoustic) y separa por el último «de» para admitir títulos que contengan esa palabra. Se conserva el criterio de similitud para errores breves y la prioridad de títulos exactos sobre hits relacionados.
- `SpotifyManager.play` añade un cuarto intento acotado con título y artista como términos, cuando fallan consultas literales y el título solo. No elige una canción distinta únicamente por ser del artista solicitado. Prueba con catálogo real: «Bastardo de Pablo Chil-E» → «Bastardo (feat. Ñengo Flow & Jere Klein)», Pablo Chill-E/Ñengo Flow/Jere Klein, similitud 0,987. Selección final verificada sin llamar reproducción.
- WhatsApp en Conexiones, navegación, buscador de secciones y cierre general. Vista nativa con `WhatsAppEmbed` y nuevo `WhatsAppHost.exe` compilado del fuente C#, usando el WebView2 oficial ya distribuido. No se modificó el host de Spotify.
- La página oficial `https://web.whatsapp.com/` permite QR, chats, nuevo chat por nombre y envío/recepción con los controles de WhatsApp. Perfil propio persistente, activo al cambiar de pestaña y recuperado al arrancar si existe. Reconectar mantiene cookies/datos; cierre espera al proceso y lo termina si no responde. Tema mediante preferencia nativa del perfil; no se extraen chats/contactos mediante librerías no oficiales ni se envían a IA.
- Pruebas: 33 de búsqueda/voz/chat aprobadas; 20 adicionales de catálogo/selección/GUI/niveles aprobadas (un nombre de clase mal escrito en la invocación se corrigió); una prueba adicional de GUI Spotify aprobada; tres de WhatsApp aprobadas. QR oficial cargado e inspeccionado visualmente. Mensajes/contactos reales pendientes de vinculación por el propietario.

No se modificaron preferencias personales ni políticas de confirmación. Reiniciar `iniciar.bat` para cargar la pestaña nueva.

## 11/10/2026 — Auditoría de reconocimiento y procesamiento acústico

- Se añadieron `voice/capture.py`, `activity.py` y `processing.py`: captura persistente, VAD Silero y WebRTC AEC3 con reducción de ruido. Procesamiento local en bloques completos de 10 ms; sin ganancia automática que amplifique el ruido. Referencia WASAPI del dispositivo de salida predeterminado, temporal en RAM. Dependencias instaladas y fijadas en `requirements.txt`: pywebrtc-audio 0.2.0 y PyAudioWPatch 0.2.12.7.
- Captura admite tasas nativas y estéreo, convierte a mono 16 kHz, sigue el micrófono predeterminado y detecta desconexiones, desbordamientos y audio obsoleto. Una petición incompleta por un corte no se ejecuta. Reconexión acotada y cierre de recursos; límite de petición 55 s.
- Se corrigió un fallo de reloj de Windows que mezclaba fragmentos anteriores con la respuesta al saludo: toda la captura usa `perf_counter`. El proceso TTS informa el final real del audio antes de limpiar recursos, para conservar el inicio de tu respuesta.
- Activación local por nombre al inicio o después de un saludo corto; no activa por mencionar a Víctor dentro de otra frase. Se preservan interrupción, espera de respuesta, fundidos musicales y controles directos. Silero reemplaza el umbral de volumen como detector de voz.
- Whisper usa vocabulario mediante `hotwords`, sin instrucciones en `initial_prompt` que podían aparecer como transcripción. Se filtran segmentos de silencio/repetición, se valida idioma/modelo y se descartan resultados cancelados.
- Ajustes y sección Voz muestran estado del procesamiento y ofrecen **Probar micrófono sin ejecutar órdenes**. El diagnóstico no llama herramientas, no cambia preferencias persistidas y restaura la escucha anterior.
- Verificación final: 117 pruebas dirigidas aprobadas en 57,091 s; prueba GUI adicional aprobada en 2,157 s; 19 archivos compilados y `pip check` correcto. Ensayos sintéticos con DSP y Whisper reales; queda por comprobar el comportamiento con la voz, habitación y juego del propietario.
- No se modificaron claves, OAuth, datos del propietario ni políticas de confirmación. Para usar: reiniciar `iniciar.bat`, revisar **Ajustes → Voz → Ruido y eco** y probar micrófono con ambos tipos de salida.

Fuentes técnicas: [WebRTC/Python](https://github.com/strands-labs/pywebrtc-audio), [PyAudioWPatch](https://github.com/s0d3s/PyAudioWPatch), [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [sounddevice](https://python-sounddevice.readthedocs.io/en/latest/api/streams.html) y [reloj Python](https://docs.python.org/3.12/library/time.html#time.perf_counter).

Las entradas siguientes son históricas; sus limitaciones sobre VAD por RMS y ausencia de cancelación acústica quedan reemplazadas por esta revisión.

## 11/10/2026 — Interrupción por VICTOR y música baja durante la espera

- Continua abre una captura local mientras TTS está ocupado, con ventanas solapadas de hasta 3,2 s, buffer acotado y Whisper sin pistas de nombres que fuercen una activación. El callback sigue capturando durante la inferencia. Solo devuelve la palabra de activación; no transmite como orden el resto del audio de altavoz/usuario. El modelo local es necesario aunque la transcripción habitual use OpenAI/Google; falta de modelo/dispositivo no cancela la escucha habitual ni repite avisos continuamente.
- La activación corta el proceso y la cola de voz y cancela la generación anterior. Conserva el lease musical entre respuestas interrumpidas, saluda otra vez y admite una petición. Interrumpir un saludo reemplaza la orden inline que todavía esperaba enviarse. El filtro de similitud de texto rechaza fragmentos de la propia voz, pero no es cancelación acústica de eco completa.
- El saludo empieza tras la bajada y mantiene el volumen bajo mientras espera la petición. Silencio de unos 8 s libera la música y vuelve a esperar VICTOR; RMS de voz durante la captura prolonga ese plazo y el límite de conversación sigue acotando la espera. La petición y su respuesta conservan la bajada; done libera el lease después de la última locución. Pausa del micrófono/cierre/fallo de entrada liberan la espera.
- El latido del lease sigue activo al cambiar de proceso TTS. Un ACK de duck_begin distingue canción pausada/no activa: no se conserva un lease vacío que impediría bajar una canción iniciada después del saludo. Se preservan volumen manual, fundidos, controles directos, métodos normales de transcripción, claves y preferencias del propietario.
- Pruebas dirigidas, pipes reales y muestra local sintética documentados en VERIFICACION.md. Pendiente comprobar micrófono/altavoz real, eco de la habitación y latencia durante un juego. Reiniciar iniciar.bat.

## 11/10/2026 — Fundido de música, activación por petición y pausa directa

- Volumen temporal con lease en el SDK integrado: 2,5 s para bajar hasta 10 % (sin elevar niveles inferiores), voz bloqueada hasta completar la bajada y 2,5 s para recuperar el volumen previo. Cambios manuales durante la locución actualizan el nivel a restaurar. Frases consecutivas comparten el volumen bajo. Cancelación, errores y latido de recuperación evitan dejar una bajada huérfana; el SDK reintenta la restauración ante un fallo temporal.
- Proceso de voz prepara el audio y avisa por pipe; el padre solicita el fundido y solo entonces permite reproducirlo. Se conserva UTF-8/JSON ASCII. Cancelar el saludo no reproduce voz tardía. El polling SDK sigue admitiendo pausa/siguiente/volumen mientras se ejecuta el fundido.
- Continua permite una petición por activación, tanto con foco como minimizada; después vuelve a esperar VICTOR. Se conserva saludo + petición y nombre con orden en la misma frase, así como escucha manual/PTT y confirmaciones cuando la política configurada las exige. Las conversaciones sin activación se descartan sin avisos repetidos.
- «Ponle pausa a la canción» y variantes usan la herramienta Spotify directamente, antes del matcher genérico «pon…»; no consultan Gemini. Identidad del contexto reforzada: el usuario habla con VICTOR, no con su proveedor. VICTOR solo nunca se envía como pregunta al modelo.
- No se modificaron claves, OAuth, proveedor, voz, controles de seguridad ni preferencias del propietario. Reiniciar con iniciar.bat. Verificación dirigida y límites documentados en VERIFICACION.md; micrófono, volumen audible y juego del propietario requieren su sesión física.

Las entradas siguientes conservan el historial de entregas. La ventana que admitía varias peticiones sin repetir VICTOR queda reemplazada por una petición por activación.

## 11/10/2026 — VICTOR solo activa, saluda y escucha la petición

- Se distinguió la palabra de activación de una orden vacía: «VICTOR» solo genera «¿En qué te ayudo?», incluso con la app minimizada. La captura espera una señal del proceso de voz al terminar el saludo. Después se aceptan peticiones sin repetir VICTOR durante la ventana de conversación, sin depender del foco. También se conserva nombre + orden en una frase. Caducidad, pausa y cierre vuelven a reposo; una orden cancelada durante el saludo no se envía.
- La instalación estaba en manual con inicio automático marcado. Se guardó copia `config.before-wake-greeting-20261011-160456.json` y se habilitaron continua/inicio automático/voz. Se preservaron proveedor Gemini, modelo gemini-3.1-flash-lite, Whisper base y voz es-EC-LuisNeural, así como claves y OAuth.
- UTF-8 explícito en la lectura del worker y JSON ASCII en el pipe corrigen el texto que Windows podía convertir en «Ã©»/copyright. La limpieza normaliza Unicode NFC y conserva tildes y ñ. El micrófono descarta audio si empieza un turno o una respuesta mientras capturaba, para evitar autoescucha.
- Controles breves de canción y volumen usan Spotify directamente cuando existe una pista observada. Las preguntas y correo conservan el mismo núcleo/IA/permisos. Las acciones locales de voz arman la confirmación automáticamente tras leer sus detalles; no activan el foco del diálogo en segundo plano. Riesgo alto exige «ejecutar», nunca un sí ambiguo. Tras confirmar/cancelar continúa la escucha. Remoto y revisiones de más de 6.000 caracteres hablados no se arman así. No se implementó envío de correo sin confirmación.
- Gemini tiene hasta dos reintentos de errores 500/502/503/504 con espera 1/2 segundos más jitter, cancelación y presupuesto de red. Nunca repite streams iniciados ni errores de clave/cuota. Registros anteriores mostraron ServerError 503 reales; una consulta breve real con la clave/modelo configurados respondió ahora. La disponibilidad de Google sigue siendo externa.
- Pruebas dirigidas de activación, pipes Unicode, controles, Gemini, Whisper, credenciales y arranque/minimización aprobadas. Audio sintético Luis → Whisper base reconoce «VICTOR» solo y conserva «¿En qué te ayudo? Canción, café y español.»; no se probó el micrófono/altavoz físico del propietario ni un juego real.
- Reiniciar con iniciar.bat para cargar los cambios. Prueba pendiente del propietario: otra app activa → decir VICTOR → esperar saludo → petición. Se conserva la antigua escucha manual/push-to-talk si se elige expresamente.

## 11/10/2026 — Canción cercana, coletillas de radio y escucha continua

- Spotify prioriza título/artista exactos (también nombres con espacios decorativos) y después clasifica similitud del título y créditos. Tolera Chris/Kris y errores como tuki tuk, Sex Playlist 1, interludio/Omar Cobbord. Si el artista mal escrito elimina resultados, consulta el título sin artista. Máximo tres búsquedas de diez pistas; conserva disponibilidad, URI exacta de selección manual y protección contra hits ajenos. Metadatos de coincidencia aproximada guardados en el resultado real.
- Voz musical: «Solicitud enviada: título». Coletillas 20 % cada frase / 60 % ninguna. Solo después de observar la pista esperada sonando en el reproductor VICTOR, una vez por solicitud; sin atribuir sonido a un ACK. Conservado título aunque el estado llegue antes de answer.
- Escucha automática opcional persistente; configuración del propietario aplicada: continua + iniciar al abrir + voz activada, conservando Whisper/base y sus claves. Copia anterior `data/config.before-handsfree-20261011-154041.json`. El modelo local ya está disponible. Necesita reiniciar iniciar.bat.
- Micrófono funciona sin foco/minimizado. Fuera de la ventana exige VICTOR en cada orden; respeta pausa/TTS/core ocupado/cierre. Timer espera a que termine el worker anterior antes de reiniciar; silencio no produce avisos repetidos. Menor intervalo entre capturas.
- Spotify arranca oculto si hay cuenta guardada y escucha automática. Conexión del SDK/activación sin clic en ese modo; no transferir ni iniciar música ajena al arrancar. Autoplay restringido al proceso WebView2 de esta app, no al navegador del usuario. Verificar la compatibilidad del flag al preparar distribución, según documentación Microsoft; recuperación manual disponible si el runtime falla.
- Pruebas: 41 dirigidas aprobadas; 25 adicionales de catálogo/SDK/servicios/OpenAI aprobadas; tras ajustes finales, 16 afectadas aprobadas, incluida ventana WebView2 real minimizada con WAV silencioso que admite play() sin interacción. No se reprodujeron canciones reales ni se capturó el micrófono del propietario. Detalles en VERIFICACION.md.

## 11/10/2026 — Reconocimiento de OpenAI integrado

- Añadido motor `openai` en Ajustes → Voz, con `gpt-transcribe` recomendado por documentación oficial actual y dos alternativas GPT-4o. Reutiliza la clave personal DPAPI de OpenAI, independientemente del proveedor del chat. No se afirma que sea el motor interno exacto de ChatGPT.
- Micrófono: PCM a WAV mono de 16 kHz en memoria, idioma/nombres propios en la petición, plazo total máximo de 30 s, sin reintentos ni fallback silencioso; cancelación HTTP cooperativa y ningún comando después de cancelar/fallar. Mensajes útiles para clave, permisos, cuota, modelo y red sin mostrar cuerpos HTTP.
- Ajustes de reconocimiento primero en la página de Voz; estado de clave y acceso a su configuración. Sesión de voz muestra el motor guardado. Whisper local/Google siguen disponibles y las notas Telegram usan OpenAI solo cuando ese motor está seleccionado. Decodificador PyAV compatible con la versión instalada, límite de duración y cancelación.
- Diagnóstico real de configuración: estaba seleccionado Google, sin vocabulario ni correcciones personales; no estaban activas las preferencias de la entrega anterior. Restaurados GAMINA/Kris R y alias explícitos sin cambiar otros ajustes. Copia previa `data/config.before-openai-voice-20261011-151735.json`. No hay clave OpenAI configurada, por lo que se conserva Google hasta que el propietario guarde su clave y seleccione OpenAI. Reiniciar mediante iniciar.bat para cargar el código nuevo.
- 33 pruebas dirigidas aprobadas en 15,337 s; pase visual de ajustes aprobado en 6,247 s. SDK real con HTTP simulado verifica multipart, WAV, keywords/languages y endpoint; no gasto de API, micrófono físico ni órdenes Spotify reales. Detalles en VERIFICACION.md.

## 11/10/2026 — Voz, claves personales, Markdown y música por artista

- Proyecto activo: Desktop/VICTOR_IA. No se editó core.py, security.py ni theme.py. Sin reinstalar dependencias, ZIP ni reproducción nueva sobre la cuenta del propietario.
- IA: campos ocultos por OpenAI/Anthropic/Gemini en Ajustes, guardado y borrado DPAPI; claves personales tienen prioridad sobre .env. AIManager, proveedores, diagnóstico y estados GUI usan el mismo origen. Configuración e historial no almacenan claves.
- Whisper: beam_size=5, pistas editables de nombres, sin condicionar con texto anterior; correcciones explícitas limitadas al título/artista de órdenes musicales. La configuración de esta instalación contiene GAMINA/Kris R y las variantes confirmadas por el propietario. Copia previa de config.json en data/config.before-voice-2026-10-11.json.
- Voz: Jorge masculina es-MX verificada en catálogo Edge y síntesis real a MP3. Luis sigue seleccionable. Formato y signos se limpian/convierten en pausas, manteniendo cifras y contenido; tablas se convierten en filas habladas. SAPI ya selecciona por idioma y no por la aparición de «es» dentro de «Desktop». Velocidad Edge aplicada y botón de prueba sin guardar.
- Chat/Voz: render Markdown nativo Qt, tablas, listas, enlaces, espaciado, temas y fuentes sin duplicados. Se conserva el texto original. No se cargan imágenes/HTML del modelo ni enlaces con protocolos no web.
- Spotify: expresiones como «cualquier canción de Fuerza Regida», «música de Kris R», «pon algo de Bad Bunny» se interpretan como artista; búsqueda acotada, coincidencia de créditos, disponibilidad y variación de selección. La misma herramienta/estado real y el panel de carátula se mantienen. Los títulos concretos conservan coincidencia exacta.
- Verificación detallada en VERIFICACION.md. Audio sintético confirma mejora de GAMINA; micrófono/audio del propietario siguen pendientes. Para cargar el código actualizado, cerrar y abrir con iniciar.bat.

## 11/10/2026 — Spotify por voz: ejecutar la orden y retirar respuestas ficticias

- [x] Identificado el origen de «Preparando resultado…»: la frase «reproducir la mena en Spotify.» no entraba en el comando local y Gemini redactaba un supuesto resultado de herramienta seguido de texto, sin ejecutar spotify_play. No era una confirmación real del SDK.
- [x] Enrutado directo desde GUI para reproducción/controles Spotify, infinitivo, puntuación, cortesía y palabra de activación; título y artista conservados. Las solicitudes de playlists/álbumes/podcasts conservan su flujo. La IA no puede presentar un comprobante JSON sin una herramienta de reproducción ejecutada en ese turno. Los resultados históricos malformados muestran falta de verificación, sin carga permanente.
- [x] Consulta por artista separada en el segundo intento; conservada coincidencia exacta y protección contra reproducir resultados relacionados. Títulos con «de» siguen probándose primero completos.
- [x] El propietario corrigió el título a **GAMINA de Kris R**. Orden real dirigida únicamente a su dispositivo VICTOR activo. Spotify confirmó ID esperado, nombre GAMINA, artistas Kris R./Los Money Makers, is_playing=true y dispositivo VICTOR. No se abrieron reproductores ni se cambiaron dispositivos externos. No se afirma haber escuchado audio físico ni validado el micrófono.
- [x] 27 pruebas dirigidas aprobadas en 23,476 s; tras el ajuste final del guard de confirmaciones y el caso de fallo local, 11 pruebas afectadas aprobadas en 10,048 s. Compilación final de los seis archivos Python afectados con salida 0.

Archivos: nuevo victor/gui/spotify_commands.py, app.py, widgets.py, integrations/spotify.py; nuevo tests/test_spotify_voice_commands.py y test_spotify_embed.py. Core, security, theme, credenciales y configuración del propietario intactos.

## 11/10/2026 — Restauración del panel de carátula y coherencia visual de Spotify

- [x] Restaurado el panel Qt «Reproduciendo ahora» arriba a la izquierda: carátula original HiDPI, título/artistas, anterior/pausa/siguiente a su derecha, volumen, posición y mini reproductor. Se conserva la biblioteca/búsqueda integrada y el único host de audio.
- [x] Catálogo a la derecha en pantalla amplia; distribución vertical desplazable en ventana estrecha. Se recalculan columnas y tamaños mínimos de botones al redimensionar para evitar anchos obsoletos.
- [x] Vista integrada con los colores grafito/azul, Inter 13 px, bordes y tamaños de VICTOR; sin fondo negro ni degradado/títulos enormes. Sincronización Dark/Light/System y Reconectar. El pie conserva estado/enlace; sus transportes duplicados quedan ocultos sin desmontar el SDK.
- [x] Inspección de widgets Qt y CapturePreview real de WebView2 en oscuro/claro a 1600 y estrecho a 420; biblioteca y búsqueda de la cuenta consultadas sin activar audio. Estado de la carátula inyectado en pausa únicamente para revisar el diseño.
- [x] Pase final: 22 pruebas dirigidas aprobadas en 22,488 s y compilación de los siete archivos Python afectados con salida 0. Incluye controles restaurados, paleta real del DOM, redimensionado sin desbordamiento, SDK, catálogo y Google. No se repitió la suite completa.

Archivos: victor/gui/panels.py, spotify_embed.py, spotify_player.py, app.py; victor/integrations/spotify_web.html; tres pruebas afectadas y documentación. No se modificaron core.py, security.py, theme.py, credenciales ni configuración del propietario.

## 11/10/2026 — Spotify integrado: sustituye las dos listas Qt y la ventana externa

- [x] Un único reproductor completo dentro de Conexiones → Spotify: WebView2 nativo alojado en un HWND hijo de Qt. Biblioteca, búsqueda/filtros, playlists/álbumes/podcasts, carátulas, selección por URI/posición, anterior/pausa/siguiente, volumen y progreso conservados. Abrir una colección no reproduce su primera pista. Cambiar de sección conserva el mismo proceso y audio; Reconectar lo reinicia. Sin lanzamiento del navegador para el reproductor. OAuth y los enlaces expresamente pulsados conservan sus flujos habituales.
- [x] Eliminadas las listas duplicadas de biblioteca/búsqueda y sus controles Qt. Vista web ajustada a ventanas estrechas: buscador y Activar audio accesibles, filtros desplazables, sin desbordamiento horizontal. Fuente Inter y recursos locales existentes.
- [x] Voz: búsqueda de diez candidatos, título normalizado (acentos/caso/puntuación), artista opcional y segundo intento por título. No reproduce un resultado relacionado si no coincide. API real de la cuenta seleccionó GAMINA — Kris R., Los Money Makers; start_playback fue interceptado, sin cambiar la música del usuario.
- [x] Chat/voz: tarjeta compacta con carátula/título/artistas. Se ocultan resultados técnicos y duplicados de herramientas Spotify en el historial visual, conservando la auditoría. Solo el estado observado confirma Reproduciendo; espera y falta de confirmación se muestran claramente. Respuestas normales de IA y errores siguen disponibles.
- [x] WebView2 Runtime local 154.0.4258.62: carga real, HWND padre verificado, búsqueda de cuenta real (48 resultados), EME/Widevine con audio MP4 soportado. Capturas reales de la vista embebida y tarjetas revisadas. No se activó audio ni se verificó micrófono físico. No se diagnosticó captura del escritorio aislado.
- [x] 22 pruebas dirigidas aprobadas (22,082 s); prueba GUI adicional aprobada tras el ajuste móvil (9,004 s). Compilación del host C# y compileall aprobados. Sin reinstalar dependencias existentes; SDK oficial Microsoft.Web.WebView2 1.0.4258.31 incluido con licencia/procedencia y build.ps1 reproducible. Perfil del navegador en data/spotify_webview2.
- [ ] Confirmar audio audible, comandos de voz y continuidad al cambiar de sección/minimizar en la sesión real del propietario. Compatibilidad de episodios y restricciones de contenido/cuenta dependen de Spotify.

Verificación final tras todos los ajustes: **27 pruebas dirigidas aprobadas en 23,015 s** y compileall con salida 0. Incluye cinco regresiones adicionales de estado real, dispositivo, control rápido, esquemas/confirmaciones y riesgo. La prueba de integración antigua se actualizó a una URI Spotify válida de 22 caracteres.

Archivos modificados: victor/integrations/spotify.py, spotify_web.py/.html; victor/gui/app.py, panels.py, widgets.py, voice_panel.py, spotify_player.py; tests/test_spotify_catalog.py, test_service_update.py, test_v5.py y test_integrations.py; README, PROGRESO y VERIFICACION. Añadidos spotify_embed.py, webview2/ (host y SDK oficial) y tests/test_spotify_embed.py. core.py, security.py, theme.py, claves, configuración y remoto intactos. Las secciones históricas inferiores describen versiones anteriores.


## 11/10/2026 — Spotify: biblioteca navegable y búsqueda visual

- [x] Seleccionar una playlist abre sus canciones en «Tu biblioteca», sin reproducir la primera. Paginación progresiva de 50, carátulas, duración, volver a playlists y selección por URI/posición exactas. Se conservan duplicados/índices reales y se omiten entradas eliminadas; pistas locales/no disponibles se señalan.
- [x] Búsqueda visual con filtros, Enter/botón, debounce de 400 ms, más resultados y descarte de respuestas obsoletas. Explorar playlists/álbumes/podcasts no inicia audio. Transportes, volumen y posición al lado de la carátula; vistas adaptativas y miniaturas asíncronas independientes de audio/controles.
- [x] Ventana web rediseñada con biblioteca lateral, buscador superior, filtros, listado central y barra inferior. Fuente Inter local, logo Spotify existente, enlaces, búsqueda y navegación reales; se conserva el SDK de audio, renovación OAuth, comandos/ACK, desconexión y origen loopback. Nuevas operaciones pasan por el registro/seguridad. Sin controles decorativos que simulen funcionalidades.
- [x] Cuenta real: búsqueda «GAMINA» devolvió 48 resultados de cinco tipos; biblioteca con cinco playlists. Navegación real en navegador cargó las 59 canciones de la primera playlist, con carátulas, sin activar audio. Capturas propias de web y widgets Qt revisadas. Estado del reproductor Qt en la captura es inyectado para inspección, no audio confirmado.
- [x] 17 pruebas dirigidas aprobadas en 18,962 s; compileall aprobado. Detectado y corregido desbordamiento de 4 px en ventana de 420 px. No se reinstalaron dependencias ni se repitió la suite completa ajena a estos cambios.
- [ ] Probar reproducción audible al elegir una canción/episodio en la app y en Edge/Chrome; verificar podcasts disponibles según cuenta/región/SDK. Las pruebas de envío exacto/posición utilizan API simulada; no se declara reproducción nueva de punta a punta ni se mide latencia audible.

Archivos: `victor/integrations/spotify.py`, `spotify_web.py/.html`, `victor/gui/app.py`, `panels.py`, `service_cards.py`, nuevo `tests/test_spotify_catalog.py`, README, PROGRESO y VERIFICACION. No se modificaron core.py, security.py, theme.py, Gemini, configuración ni control remoto.

## 11/10/2026 — diagnóstico y corrección de Gemini

- [x] Reproducción real con la clave local, sin mostrarla: Google rechazó `gemini-2.5-flash` con 404 NOT_FOUND, indicando que ya no está disponible para usuarios nuevos y recomendando `gemini-3.8-flash`.
- [x] Modelo Gemini predeterminado y de esta instalación actualizado a `gemini-3.8-flash`, guardado/recargado; comprobado que los demás modelos y preferencias no cambiaron. No se modificaron claves.
- [x] AIManager reconoce `.code` de google-genai además de `.status_code` de otros SDK. Mensajes separados para modelo no disponible (404), credenciales/permisos, cuota y saturación (503); logs sin cuerpos de respuesta ni claves. Respaldo y cancelación conservados.
- [x] 17 pruebas dirigidas aprobadas en 2,600 s y compileall aprobado. El proveedor real devolvió `OK` usando el modelo nuevo y los esquemas completos de herramientas, sin ejecutar acciones.
- [ ] Disponibilidad estable del servicio externo: hubo respuestas 503 antes y después del éxito. La comprobación final por AIManager con la configuración guardada produjo 503 a los 26,09 s, ahora descrito correctamente como saturación; no se declara una conversación completa en GUI como probada.

Archivos: `victor/ai/manager.py`, `victor/config.py`, nuevo `tests/test_gemini_errors.py`, PROGRESO y VERIFICACION; solo modelo Gemini en `data/config.json`. Sin reinstalación, cambios de interfaz ni suite completa repetida.

## 11/10/2026 — servicios ordenados y Spotify sin diálogos

- [x] Herramientas ocultas del menú principal, accesibles en Ajustes → Generales → Herramientas avanzadas y por voz. Se conservan las 21 vistas y las funciones existentes.
- [x] Google separado en pestañas con logos SVG CC0, fechas legibles, filas con jerarquía y enlaces por doble clic. Metadatos añadidos: fecha/hilo Gmail, lugar/enlace/evento de todo el día Calendar y modificación/tamaño Drive. Eliminada salida técnica duplicada. Corregido el doble pintado de texto descubierto en la captura propia.
- [x] Carátulas Spotify de resolución máxima, render HiDPI responsivo hasta 240 px; biblioteca con tarjetas. Se conservan workers independientes, predicción y debounce; añadida deduplicación del mismo volumen y recepción de resultados de herramientas por voz en las vistas correspondientes.
- [x] Preferencia persistente del propietario `action_confirmations=false`, aplicada a la instalación real sin cambiar claves ni core.py. SecurityManager omite diálogos, conserva validación/bloqueos/origen; auditoría muestra «Directa (sin diálogo)». Perfil reversible en Seguridad. OAuth y QR siguen vigentes.
- [x] Reproductor real mediante SDK oficial Spotify, servido solo en loopback y abierto en ventana web Edge/Chrome. Transporta comandos/ACK, token renovado solo con scope streaming, selección de dispositivo, eventos de estado y reconexión. Cierre cancela solicitudes/servidor; desconexión del PC desconecta SDK. No se necesita Spotify desktop cuando el SDK está conectado. No se integró el audio dentro de Qt: esa petición literal permanece como limitación explícita, no fingida.
- [x] Compilación y 126 pruebas completas aprobadas, 64,172 s. Capturas de widgets Qt con fixtures en `work/services_11`, fuera del proyecto; ventana abierta y cierre limpio. Corregido un ancho obsoleto de Diagnóstico al volver a mostrar la página, detectado por la suite. Últimos ajustes verificados mediante pruebas dirigidas; véase VERIFICACION.
- [ ] Probar OAuth con scopes nuevos, Premium/DRM y audio real del SDK, controles por voz y tiempo audible de volumen/cambio de pista en PC real. No se midió esa latencia ni se promete instantaneidad. No se volvió a intentar MSS/ImageGrab ni entrada física en CodexSandboxDesktop. El streaming del celular no fue modificado.

Archivos: `victor/config.py`, `security.py`, `integrations/google.py`, `spotify.py`, nuevos `spotify_web.py/.html`, `gui/app.py`, `panels.py`, `spotify_player.py`, `maintenance.py`, nuevo `service_cards.py`, cuatro logos/licencia, `tests/test_service_update.py`, README, PROGRESO y VERIFICACION; solo la preferencia indicada en `data/config.json`. Sin reinstalación ni otro proyecto/ZIP.


## 11/10/2026 — referencia final de controles Windows

- [x] Aclarado directamente con el propietario: de izquierda a derecha **− □ ×**, según la última referencia. Sustituidos círculos de colores por símbolos claros, áreas 44×30 px y hover de cierre rojo; en tema claro los trazos son oscuros para mantener contraste. El cuadrado cambia a restaurar cuando está maximizada. Animaciones conservadas.
- [x] 2 pruebas afectadas (WindowControls y QtGUI) aprobadas en 13,412 s; incluye orden físico y color del símbolo, tamaños/temas y transiciones. Compilación de los archivos afectados: salida 0. Captura propia del encabezado revisada: `work/controls_windows.png`, fuera del producto; apertura/cierre limpio confirmados.
- No se eliminaron funciones ni se cambiaron permisos: la simplificación para uso por voz se recomienda, no se aplica sin una decisión sobre el alcance. Abrir aplicaciones/URL ya son LOW y directas en seguridad normal; Strict solicita confirmación también para LOW.

Modificados `victor/gui/app.py`, `widgets.py`, `tests/test_window_controls.py`, README y VERIFICACION. Sin cambios en core/security ni reinstalaciones. El orden/estilo de la sección anterior queda como registro histórico, sustituido por esta referencia confirmada.

## 11/10/2026 — tarjetas recortadas, orden y transiciones de ventana

- [x] Corregidas las tarjetas de Windows/Archivos: botón con contenido y altura real del layout (80 px en ancho, creciente con texto apilado). El estilo ya no se propaga a las etiquetas; su política conserva height-for-width para no recortar líneas al reducir la ventana o cambiar tema.
- [x] Orden solicitado, izquierda a derecha: × rojo, □ verde, − amarillo.
- [x] Transiciones no bloqueantes: maximizar/restaurar y minimizar 260 ms, cierre 220 ms, curva InOutCubic, escala/fade sobre una captura Qt de la ventana propia. Restaurar desde la barra de tareas también anima. La captura temporal se libera al terminar; clics repetidos no superponen animaciones. El cierre conserva la parada de workers original.
- [x] Nueva prueba `tests/test_window_controls.py`: tarjetas completas y clic funcional, 1920/420/1600 px, Dark/Light/Dark, orden físico de botones, movimiento/opacidad intermedios de animación, estados finales, restauración y cierre limpio. Pase final: 1 prueba en 8,470 s. Cuatro pruebas GUI existentes afectadas aprobadas en 19,788 s; no se repitió la suite completa ni se reinstalaron dependencias.
- [x] Compilación de GUI y tests afectados: salida 0. Capturas propias en `work/tiles_fixed_1920.png`, `tiles_fixed_420.png` y `tiles_fixed_1600.png`, fuera del producto; imagen ancha revisada directamente.

Modificados `victor/gui/widgets.py`, `panels.py`, `app.py`, `tests/test_ui_repairs.py` (espera acorde con la duración de animación), README y VERIFICACION; añadido `tests/test_window_controls.py`. No se modificaron voz, Spotify, remoto, core, security ni theme. Las transiciones son una aproximación visual en Qt/Windows, no el efecto Genie nativo de macOS.

## 11/10/2026 — correcciones gráficas y niveles de voz

- [x] Selección exclusiva: una pestaña activa en cada sección y un proveedor activo; las acciones rápidas de Windows/Google ya no quedan marcadas como pestañas.
- [x] Navegación secundaria visible: Conexiones muestra Spotify, Google, Telegram y Control remoto. Herramientas, Seguridad y Ajustes también tienen pestañas visibles.
- [x] Avisos temporales: duran 5,5 segundos, desaparecen con fade de 240 ms y se conservan los últimos 20 en el botón del encabezado «Ver avisos recientes». Un mensaje nuevo cancela la desaparición del anterior.
- [x] Logos SVG de OpenAI, Anthropic, Gemini y Ollama, fuente Simple Icons 13.21.0, licencia CC0 incluida; contraste adaptado para tema claro. Controles cerrar/minimizar/maximizar circulares de 14 px con zonas de clic de 24 px, rojos/amarillos/verdes.
- [x] Diseño responsivo: 21 vistas sin scroll horizontal a 420×760; tarjetas/acciones se apilan y los textos de botones demasiado largos conservan el nombre completo en tooltip. Corregidos valores numéricos de sliders y altura de proveedores tras cambiar tamaño/tema. Capturas propias revisadas en oscuro/claro, ancho reducido y restaurado.
- [x] Voz: historial visual del RMS real del micrófono y orbe separado para PCM del audio de VICTOR; pipe de niveles desde el proceso de síntesis y Qt QAudioBufferOutput. Fin de escucha borra los niveles antiguos; resultados secundarios no cambian a «Listo» mientras VICTOR está respondiendo. Visitar Voz ya no activa salida hablada sin autorización: botón explícito «Voz de VICTOR · activada/desactivada».
- [x] Pruebas: 8 nuevas; suite completa de 117 aprobada en 48,476 s. Después del último ajuste visual, 4 pruebas GUI afectadas aprobadas en 17,833 s. Detalles y límites físicos en VERIFICACION.md.
- [x] Compilación final de main.py/victor/tests: salida 0; revisión visual final oscuro/claro y ventana restaurada completada.
- [ ] Verificación por el propietario: reacción con micrófono/altavoces reales y reproducción de sus voces Edge/SAPI. Los niveles de las capturas son fixtures; no son audio físico. Streaming/input del celular conservados, sin nuevos intentos de captura del escritorio aislado.

Archivos de producto modificados: `victor/gui/{app,panels,widgets,voice_panel,maintenance}.py`, `victor/voice/{input,output}.py`; añadido `victor/voice/levels.py` y cuatro SVG con licencia en `victor/gui/assets/`. Añadida `tests/test_ui_repairs.py`; README y VERIFICACION actualizados. No se modificaron `core.py`, `security.py`, `theme.py`, los servicios remotos ni el backend/reproductor Spotify. No se reinstalaron dependencias ni se borraron datos/configuración.

## Corrección de arranque — aviso bs4

- Causa confirmada: activate.bat conservaba la ruta del entorno original en outputs/VICTOR_IA_v6; `where python` tras activarlo mostraba Python global, no el de Desktop/VICTOR_IA.
- Modificado únicamente iniciar.bat para invocar por ruta absoluta el Python de esta .venv y main.py. BeautifulSoup 4.15.0 ya estaba instalado; no se reinstaló ninguna dependencia.
- Imports bs4/GUI correctos. Ejecutado iniciar.bat --smoke-test con resultado fuera del proyecto: salida 0, ventana real abierta y cerrada. No se repitió la suite ni se modificaron funciones del asistente.

## 10/10/2026 — diseño Grafito, Spotify y remoto en Desktop/VICTOR_IA

- [x] Editado el proyecto real. Respaldo de fuentes sin secretos: `<CARPETA_LOCAL>`. No se reinstalaron dependencias ni se generó un segundo proyecto.
- [x] 21 vistas Qt + diálogo de autorización + página móvil basadas en los PNG del ZIP. Inter/IBM Plex Mono y sus licencias incluidas, iconos vectoriales, navegación/controles enlazados a servicios, formularios de todos los DEFAULTS, respuesta clara sin cuentas ni voz local preparada. Historial/memoria y protecciones conservados. Contraste claro y ventana 420×760 comprobados.
- [x] Spotify: cola independiente de la IA, HTTP por trabajador con cierre limpio, cache cuenta/dispositivo, polling 1,5/4 s, carátulas separadas, debounce 120 ms y protección de slider frente a estado atrasado. Seek y playlists usan API real pasando por el registro y confirmación MEDIO.
- [x] Remoto: streaming sin corte de 60 s dentro de sesión activa, latidos renovadores, canal puntero propio con ACK/coalescencia, gesto directo sobre imagen/scroll, teclado Unicode/IME/special keys, detección de foco y botón nativo. Coordenadas corresponden al fotograma decodificado mostrado; se descartan frames decodificados obsoletos y no se repiten eventos al desconectar. Ratón MEDIO por conexión/destino, atajos peligrosos ALTO; núcleo/seguridad intactos.
- [x] Ejecutado: 109 pruebas en 45,748 s, compileall código 0; tras ajuste de contraste, tres pruebas GUI en 14,687 s y compileall nuevamente 0. Ventana Qt visible en 21 vistas y cierre limpio; revisión de capturas propias, desktop1600×900 y narrow420×760. Primeros fallos de regresión corregidos y verificados (expectativa de navegación antigua, anchos, fixture de Spotify aislada del polling).
- [x] Último ajuste del reproductor: play/pausa y volumen se reflejan inmediatamente tanto en el panel grande como en el mini. Tres pruebas afectadas aprobadas en 20,163 s; callback visual con API simulada 0,87 ms. Compileall final: código 0. Cachés retiradas de nuevo tras verificar.
- [x] Limpieza: 77 .pyc de 11 cachés, 860655 bytes eliminados. 3 capturas antiguas (154239 bytes) movidas a `<CARPETA_LOCAL>`. `.env`, `.venv`, `data/`, `workspace/`, tests y scripts conservados.
- [x] Documentación vigente arriba en README y VERIFICACION; las secciones inferiores son historial, no pruebas nuevas. Comparación binaria de core.py y security.py contra respaldo: idénticos.
- [ ] Aceptación del propietario pendiente: cuenta Spotify real y tiempos de audio; teléfono iOS/Android, TLS/Wi-Fi, captura/puntero/teclado físicos, UI Automation en sus apps, servidor activo >10 min y reconexión. No comprobables en CodexSandboxDesktop; no se reintentó diagnóstico/captura ni se declaran resueltos por pruebas simuladas.
- [ ] La reproducción visual no es una identidad pixel por pixel: PNG sin fuente SVG original, renderizado Qt, texto dinámico, iconos recreados y adaptación responsive difieren. Próximo evento se muestra cuando se consulta Calendar, no se simula una sincronización ni un evento de ejemplo.

## V6 — solo control remoto
- [x] A: teclado incremental/Unicode, IME al confirmar composición, teclas especiales, serialización y ACK; detección de elemento editable y botón de foco HTML. Implementación terminada; entrada real/apertura del teclado móvil pendientes de prueba del propietario.
- [x] B: MEDIO sin diálogo para teclado ordinario con capability de sesión QR; set explícito de atajos ALTO, confirmación PC y revalidación. No se alteran mouse/clic ni type_text local/Telegram. Security solo contiene la excepción puntual; core intacto.
- [x] C: teclado/captura/ratón separados; sonda de foco en subproceso terminable; colas y timeouts acotados, revocación, latidos, errores visibles y ninguna repetición automática tras desconexión.
- [x] Pruebas: 97 aprobadas (83 anteriores + 14 nuevas), JavaScript Node y compileall. Solo backend/sonda simulados; no se intentó captura, mouse/teclado reales ni diagnóstico del escritorio aislado.
- [x] Alcance auditado contra v5: core, tema, Spotify y demás módulos existentes sin cambios, salvo los cuatro módulos remotos/seguridad autorizados.
- [x] README y VERIFICACION incluyen pasos exactos numerados, riesgos y límites (foco por navegador, Ctrl+Alt+Supr no sintetizable, Windows elevado).
- [ ] Validación manual: streaming con v6, tacto, texto/IME/atajos, confirmaciones altas, pérdida de Wi-Fi y certificado en PC/celular real. No declarada resuelta por el agente.
- [x] ZIP v6 generado: 88 archivos, 76 módulos Python, CRC/integridad aprobados. Sin .venv, data, modelos, .env ni claves. Las capturas incluidas son las históricas de interfaz v5; no se tomaron capturas nuevas.

## V5 — entrega y pendientes explícitos
- [x] P1: referencia Nextendo recibida, abierta y medida directamente (tabla en VERIFICACION). Hero, resumen, radios, punto 15 px y dos columnas adaptados conservando paleta. GUI real y capturas propias revisadas. No se afirma recuperar la fuente/CSS exactos del raster.
- [x] P2 preservación: fuentes remotas, core y security idénticos a v4. Se reconoce que el usuario ya comprobó pantalla/ratón en su PC. Diagnóstico nuevo: CodexSandboxDesktop distinto de Default; MSS/ImageGrab fallan allí. Instrucciones del teléfono en README.
- [ ] P2 experiencia completa solicitada: teclado instantáneo sin interrupciones y apertura automática al enfocar un campo NO implementados; el botón Teclado y la escritura supervisada se conservan. type_text es ALTO y requiere EJECUTAR en PC. Nueva prueba con celular no realizada por el agente.
- [x] P3 arquitectura y pruebas: predicción/reconciliación, polling adaptativo y debounce. 0,20 ms de callback visual con API simulada en la suite final. Latencia Spotify real pendiente de cuenta en este entorno.
- [x] P4 A: caché y descarga aislada implementadas; descarga real ~148 MB y carga/inferencia CPU sobre silencio ejecutadas. También se ejecutó el botón GUI real contra la caché ya descargada y cerró limpiamente. Descarga fría desde GUI y ensayo hablado completo pendientes de validación, no declarados probados.
- [x] P4 B/C/D/F: wake word tolerante y aviso, presentación F11, auditoría visible, script de humo. Pruebas nuevas aprobadas; voz acústica en vivo pendiente.
- [x] P4 E: prechequeo local y diagnóstico de conexiones en proceso aislado implementados. Botón GUI ejecutado sin credenciales, pruebas de IA simulada sin herramientas aprobadas. Consultas con cuentas autenticadas pendientes de verificación en este perfil; Gmail/Drive, micrófono y emparejamiento no se confunden con conectividad.
- [x] Validación: 83 pruebas, compileall, imports y ventana. Sin reinstalar dependencias.
- [x] Empaquetado v5: ZIP generado e integridad comprobada; 81 archivos, 69 módulos Python. Se excluyen data, modelos, claves y .venv. Las limitaciones pendientes anteriores permanecen explícitas.

## V4
- [x] A/B: pestaña Tools retirada; estilos más redondeados y nombres/detalles centralizados en español. Prueba GUI anterior aprobada. Referencia visual: el adjunto disponible contiene texto; se siguió la descripción escrita de estilo.
- [x] C: mini reproductor con consulta real y controles por registro; volumen bajo, OAuth intacto.
- [x] D: vista de voz y confirmación local explícitamente activada; mismo micrófono y orquestador.
- [x] E: Telegram en lenguaje libre por IA, errores visibles y acción YouTube supervisada.
- [x] F: página remota unificada y mapeo táctil; teclado sujeto a confirmación en PC.
- [x] Entrega: pruebas completas, documentación, capturas propias y ZIP v4.

## V3
- [x] Parte A: GUI únicamente. Panel comparte diseño (lateral en ancho, debajo en angosto), márgenes 20 px, botones iguales y 2×2, burbujas máximo 70%, resultados JSON presentados como texto, rutas con tooltip, tarjetas de confirmación destacadas, estados con color y compositor 52 px. Prueba GUI ampliada aprobada y capturas propias wide/narrow/closed revisadas. No se modificó núcleo en esta parte.
- [x] Parte B: ddgs real, grabación 5 s, volumen 100→98→100 y Edge/Qt reproducido. Corregido bloqueo de MP3 al limpiar el reproductor; salida 0 tras corrección. Sin modelo Whisper, claves ni Ollama disponible. MSS/ImageGrab bloqueados, calculadora sin ventana persistente y SAPI acceso denegado; no se declaran resueltos. Datos completos en VERIFICACION.md al cierre.
- [x] Parte C: Google OAuth y remoto HTTPS local implementados. Nueve tests nuevos aprobados y HTTPS/WSS real verificado; cuentas Google y celular pendientes, DPAPI bloqueado para tokens.
- [x] V3: documentación actualizada, 68 pruebas, compilación e integridad ZIP. Sin datos privados ni credenciales. Consultar VERIFICACION.md para límites e incidencia de versiones pip.

Base existente: `work/VICTOR_IA`. No reescribir núcleo ni eliminar las 36 pruebas originales.

- [x] Bloque 1: alias de argumentos, reintento de esquema, router local, Ollama CPU/GPU, ddgs, errores. Cerrado: 42 pruebas aprobadas y búsqueda real con cuatro páginas leídas.
- [x] Bloque 2: reemplazo de GUI por PySide6, métricas reales, diseño responsivo, confirmaciones y pruebas GUI. Prueba Qt aprobada a 420 px, arranque real y captura del widget revisada.
- [x] Bloque 3: Whisper local, edge-tts con respaldo, conversación continua y detección de micrófono. Cuatro pruebas aprobadas; servicios/audio reales pendientes, dependencias nuevas aisladas en el instalador.
- [x] Bloque 4: respaldo de captura y pruebas aprobadas; lectura real de volumen correcta. Calculadora sin ventana verificable y escritorio bloqueado: documentados, sin reintentos repetidos.
- [x] Bloque 5 (opcional): cerrado como diferido. Google OAuth y remoto web/QR no se implementan en v2; se prioriza el bloque obligatorio 6. No se añaden módulos vacíos ni botones que finjan estas funciones. Spotify se implementa en bloque 6.
- [x] Bloque 6: Telegram autorizado y emparejado, notas de voz locales, seguridad remota, Spotify y pruebas. Diez pruebas de integración con mocks aprobadas; servicios reales pendientes.
- [x] Entrega: documentación, .env.example, compileall, suite completa y VICTOR_IA_v2.zip limpio.

## Reglas operativas

Una sola ruta: entrada → VictorCore → ToolRegistry → SecurityManager. Sin claves dentro del ZIP.
Cerrar cada bloque con pruebas antes del siguiente. No reintentar pip ni una prueba después de más de dos fallos; registrar el bloqueo y continuar con lo independiente.

## Estado inicial

README.md y VERIFICACION.md leídos. Se conserva la evidencia de v1. Entorno `.venv` existente; no reinstalar paquetes ya presentes. Bloque 1 cerrado. ddgs 9.16 instalado desde wheel oficial. Un intento de descarga fue bloqueado por permisos de red; permiso concedido y descarga completada. Búsqueda real respondió con cuatro fuentes HTML, incluida docs.python.org. No se ha probado inferencia Ollama real.

Cierre v2: compileall, 59 pruebas, imports nuevos y pip check aprobados. Empaquetado limpio mediante work/package_project.py; revisión CRC y lista explícita de archivos. Google/remoto QR diferidos; consultar VERIFICACION.md antes de atribuir pruebas reales a APIs, audio o escritorio.

Cierre v4: 76 pruebas aprobadas, compilación y JavaScript correctos, cinco capturas revisadas. OAuth/core/security idénticos a v3. Sin instalación de dependencias. Validaciones de servicio real pendientes detalladas en VERIFICACION.md; miniplayer de ejemplo solo en evidencia.