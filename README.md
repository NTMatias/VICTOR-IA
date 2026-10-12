# VICTOR.IA v3

Asistente de escritorio modular para **Windows 10/11 y Python 3.11+ de 64 bits**. Interfaz PySide6 (Qt), chat con streaming, cuatro proveedores de IA, herramientas supervisadas de Windows, memoria e historial SQLite y voz opcional.

## Instalar y abrir

1. Descomprime **toda** la carpeta `VICTOR_IA` en una ubicación donde tengas permisos de escritura (por ejemplo, Documentos). No lo ejecutes dentro del ZIP ni como administrador.
2. Ejecuta **instalar.bat**. Crea `.venv`, instala las dependencias y comprueba los imports principales. Requiere Internet para descargar paquetes. Si no encuentra Python, muestra cómo instalarlo; recomendamos Python 3.12 de 64 bits desde python.org.
3. Ejecuta **iniciar.bat**. Se abre la ventana incluso sin claves API. Los comandos locales y los paneles de memoria e historial funcionan sin servicio de IA.

El instalador copia `.env.example` a `.env` si este no existe. Nunca sobrescribe tus claves, configuración ni historial. Puedes repetir la instalación para reparar dependencias. No incluye modelos ni un runtime Python dentro del ZIP.

## Configurar IA

Edita `.env` con un editor de texto y completa solo las claves que necesites:

```dotenv
OPENAI_API_KEY=tu_clave
ANTHROPIC_API_KEY=tu_clave
GEMINI_API_KEY=tu_clave
```

También se admiten variables de entorno con esos nombres; tienen prioridad sobre `.env`. **Reinicia la aplicación** tras cambiar claves. No se guardan en `config.json`, ni se muestran en la GUI ni se registran en logs. `.env` es texto local: protégelo y no lo compartas. Una suscripción de chat no implica saldo/API disponible.

En **Configuración** selecciona proveedor, modelo, temperatura y tokens. Los nombres iniciales son ejemplos editables, no promesas de disponibilidad para tu cuenta. Cambia un modelo si el proveedor lo retira o tu cuenta no tiene acceso.

| Proveedor | Preparación | Integración |
|---|---|---|
| OpenAI | Crea una clave con acceso y saldo en la plataforma | SDK oficial, Chat Completions, streaming y function calling. Usa modelos compatibles con Chat Completions; modelos exclusivos de Responses no están soportados en este adaptador. |
| Anthropic | Crea una clave y configura facturación/acceso | SDK oficial Messages, streaming y tool use. |
| Gemini | Crea una clave de Gemini API en Google AI Studio | SDK oficial `google-genai`, streaming y llamadas nativas. El historial de herramientas se convierte en texto de evidencia entre rondas para no reutilizar firmas de pensamiento. |
| Ollama | Instala Ollama, inicia su servicio y descarga un modelo | HTTP local `/api/chat`, streaming y protocolo JSON de herramientas. La calidad de uso de herramientas depende del modelo. |

Ejemplo de preparación de Ollama, **fuera del asistente**:

```powershell
ollama pull qwen2.5:7b
ollama serve
```

Si Ollama ya está ejecutándose no necesitas `ollama serve`. Selecciona **Ollama** y el nombre exacto del modelo descargado. Solo se aceptan servidores de loopback locales. Un modelo con visión se configura por separado; un modelo de texto no puede analizar imágenes.

**Fallback**: escribe una lista JSON, por ejemplo `["Gemini", "Ollama"]`. El principal se intenta primero; si falta su clave o falla, se prueba el siguiente y se informa del cambio. Está vacío inicialmente para no enviar conversaciones a proveedores adicionales sin configurarlos. En visión se utiliza solo el proveedor de visión seleccionado, sin fallback silencioso de imágenes. Una respuesta parcial fallida se borra antes de mostrar la del respaldo.

## Uso

- **Enter** envía; **Mayús+Enter** agrega una línea. Hay streaming de texto de todos los adaptadores.
- **Detener** corta la voz, cancela confirmaciones y evita las siguientes acciones. Una petición de red ya iniciada puede tardar hasta el timeout en devolver el control; las acciones completadas no se deshacen.
- **Nueva conversación**, búsqueda y eliminación están en el panel lateral ☰ → Historial. El historial vuelve a aparecer al abrir la aplicación.
- En **Herramientas** selecciona una operación, edita los argumentos JSON y pulsa Ejecutar. No necesitas IA para usarlas.
- En **Memoria** escribe una clave y su valor, guárdalo, búscalo o elimínalo. Los cambios piden confirmación.
- En **Configuración** puedes editar nombre, personalidad, formalidad, idioma, instrucciones, tema, voz, modelos, seguridad, carpetas y aliases de aplicaciones.

Comandos locales sin clave:

```text
Abre la calculadora
Abre Google Chrome
¿Cuánta RAM estoy usando?
Recuerda nombre=Ana
¿Qué recuerdas?
Captura la pantalla
Borra el archivo ejemplo.txt
Abre https://www.python.org
Ayuda
```

La conversación libre y la interpretación de órdenes no incluidas en la gramática local requieren un modelo. `Borra el archivo ejemplo.txt` apunta a `workspace/ejemplo.txt` y pide escribir **EJECUTAR** antes de enviarlo a la papelera.

## Archivos, aplicaciones y permisos

La carpeta `workspace/`, creada automáticamente, es la única raíz autorizada por defecto. Añade otras **rutas absolutas** como lista JSON, por ejemplo `["C:/Users/TuUsuario/Documents/Trabajo"]`, en Ajustes. No autorices todo tu disco. Las rutas relativas se resuelven dentro de la primera raíz.

- Se bloquean carpetas del sistema, datos internos del asistente, `.env`, enlaces simbólicos/junctions, rutas UNC/dispositivos, flujos NTFS y rutas fuera de las raíces autorizadas.
- Crear archivos admite texto (`txt`, `md`, `csv`, `json`, `log`, `yaml`, `yml`). No crea ejecutables ni scripts. Nunca sobrescribe destinos existentes.
- Mover/copiar/renombrar/eliminar admite **archivos individuales**, no árboles de carpetas. La eliminación usa `send2trash`; nunca hay borrado permanente como fallback.
- Abrir archivos admite un conjunto de extensiones de documentos, texto y medios. No abre scripts, accesos directos, ejecutables ni documentos con macros.
- Las aplicaciones iniciales incluyen calculadora, bloc de notas, Paint, explorador y navegadores conocidos. Puedes registrar aliases con un JSON como `{"editor": "C:/Apps/Editor/editor.exe"}`. Solo acepta `.exe` existentes y bloquea intérpretes y herramientas administrativas conocidas. Registra exclusivamente programas que conozcas.
- Cerrar aplicaciones usa terminación de proceso y **puede perder cambios sin guardar**. Por ello requiere autorización y muestra una advertencia. Algunas aplicaciones de Windows usan un proceso distinto del lanzador; en ese caso no se cierran y se informa.

**Riesgos:** bajo = ejecución directa; medio = tarjeta de confirmación dentro del chat con parámetros exactos; alto = tarjeta y escribir `EJECUTAR`. `strict` también confirma operaciones de bajo riesgo. No existe modo que elimine las confirmaciones de alto riesgo. Cada solicitud y su resultado se registran, sin guardar cuerpos con claves.

La terminal está limitada a `ipconfig`, `whoami`, `hostname` y `systeminfo`, **sin argumentos**, siempre con confirmación explícita y `shell=False`. Los comandos arbitrarios, instalación de software, edición del registro y elevación administrativa están **deliberadamente deshabilitados**. La IA no puede modificar las listas de permisos.

## Ratón y teclado

Cada acción pasa por seguridad y necesita el **título exacto de la ventana**. La ventana se activa y se verifica antes de enviar la entrada. Los clics y movimientos deben estar dentro de sus límites. Un cambio de foco interrumpe la escritura. `type_text` admite Unicode y no añade Enter; Enter/Delete requieren autorización explícita aparte. No automatiza la propia ventana de VICTOR.IA ni aplicaciones elevadas.

PyAutoGUI mantiene `FAILSAFE=True`: mueve el puntero a una esquina para abortar. Se ejecutan acciones individuales, no macros ilimitadas. Un clic o atajo puede tener consecuencias en la aplicación destino: revisa los parámetros del diálogo.

## Voz local

El instalador intenta instalar las dependencias opcionales por separado. El chat arranca aunque fallen. La entrada predeterminada es **faster-whisper, base, CPU int8**; no requiere GPU. Para descargar el modelo una sola vez (Internet y espacio libre):

```powershell
.venv\Scripts\python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"
```

El ZIP no incluye modelos. La aplicación exige la copia local y muestra instrucciones si falta; no inicia descargas ocultas. Puedes elegir `small` o una ruta de modelo en Ajustes. Usa hasta cuatro hilos CPU y comparte una instancia entre micrófono y Telegram.

- **Manual:** pulsa el círculo de micrófono para una frase; termina por silencio o a los 15 segundos.
- **Push-to-talk:** mantén presionado el botón y suelta para transcribir.
- **Continua:** activa el micrófono y di VICTOR antes de la primera orden. Durante `conversation_window` (45 segundos por defecto) acepta órdenes siguientes sin repetir el nombre; luego vuelve a exigirlo. Se suspende durante IA y reproducción de voz.
- `wake_word` permite VICTOR o Victoria. Se reconoce después de transcribir, no con un detector especializado de baja potencia. La onda es un indicador animado de escucha, no amplitud del audio.
- Activa **Leer respuestas en voz alta** para TTS: `edge` envía el texto a Microsoft y necesita Internet; si falla intenta SAPI/pyttsx3. `sapi` usa directamente Windows sin red. La salida corre en un proceso cancelable. `edge_voice` predeterminada: `es-EC-LuisNeural`; velocidad/ID SAPI se configuran por separado.
- Google sigue como STT alternativo; la GUI pide consentimiento porque envía audio a Internet.

Si no hay micrófono, la aplicación lo informa y propone notas de voz por Telegram. Revisa permisos de micrófono de Windows o enumera dispositivos con `.venv\Scripts\python -c "import sounddevice; print(sounddevice.query_devices())"` y configura su índice en `microphone`. El umbral de voz es fijo; ruido o un micrófono débil pueden perjudicarlo.

## Telegram y celular como micrófono

1. Crea un bot en **@BotFather** dentro de Telegram (`/newbot`). No publiques su token.
2. Añade `TELEGRAM_BOT_TOKEN` a `.env` y reinicia VICTOR.IA.
3. Abre ☰ → **Conectar** → **Activar / detener Telegram**. Espera el aviso de conexión.
4. Pulsa **Generar código de emparejamiento**. En tu chat privado con el bot escribe `/vincular CODIGO`. Caduca en 120 segundos, se usa una vez y admite cinco intentos. El ID queda en `telegram_allowed_ids` en Ajustes; puedes revocarlo allí.
5. Envía texto o una nota de voz (máximo 60 segundos/15 MB). El audio se descarga temporalmente, se transcribe localmente con Whisper y muestra la transcripción. Requiere haber descargado el modelo. Texto, voz y PC usan el mismo VictorCore y registro de herramientas.

No acepta grupos ni usuarios desconocidos. Usa polling, sin abrir puertos. La GUI muestra la orden e ID remitente; logs registran usuario, hora, herramienta y resultado. Telegram transporta texto/audio/capturas mediante sus servidores; este canal no es un chat secreto de extremo a extremo.

Comandos: `/estado`, `/captura`, `/pausa`, `/reanudar`, `/ayuda`. El botón del PC detiene el servicio; pausa conserva la conexión pero impide órdenes. Límite predeterminado: seis órdenes por usuario cada 30 segundos. `remote_block_all` bloquea control remoto desde el PC y no puede desactivarse desde el bot.

Riesgo medio: botones inline Confirmar/Cancelar ligados al usuario, chat y acción; caducan en 120 segundos. Riesgo alto (borrar, terminal, escribir texto, Enter/Delete): **bloqueado por defecto** (`remote_high_policy=block`). Con `pc` exige escribir **EJECUTAR en la ventana del PC**, nunca en Telegram. Se vuelven a comprobar permisos después de la confirmación. `/captura` siempre confirma y advierte de la transferencia a Telegram. Confirmaciones demasiado extensas se muestran completas en el PC.

## Spotify

1. Crea una aplicación en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), habilita Web API y registra exactamente `http://127.0.0.1:8888/callback` como redirect URI.
2. Configura `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET` y `SPOTIPY_REDIRECT_URI` en `.env`; reinicia.
3. ☰ → **Conectar** → **Conectar Spotify** abre OAuth en tu navegador (máximo 120 segundos). El receptor temporal escucha solo en 127.0.0.1. El token se guarda cifrado con DPAPI de Windows en `data/spotify.oauth`; no se guarda en texto plano.
4. Necesitas una cuenta Premium con acceso permitido a tu aplicación y Spotify activo en el PC. Empieza una reproducción allí. Opcionalmente fija su ID con `SPOTIPY_DEVICE_ID`.

Prueba «Reproduce DTMF en Spotify», «Pausa Spotify», «Siguiente en Spotify», «Anterior en Spotify», «Qué suena en Spotify» y «Mis playlists de Spotify». Las herramientas incluyen volumen (0–100), búsqueda y reproducción, estado actual y hasta 50 playlists. Modificar reproducción requiere confirmación. Se consulta la pista real después de reproducir; si todavía no coincide se informa como no confirmada. Sin Premium o dispositivo activo se explica el problema y se intenta abrir la app. Si no se encuentra, registra su ejecutable en `applications` como alias `spotify`.

## Google: Gmail, Calendar y Drive

En Google Cloud Console crea un proyecto, habilita **Gmail API, Google Calendar API y Google Drive API**, configura la pantalla de consentimiento y añade tu cuenta como usuario de prueba si la aplicación está en Testing. Crea un **cliente OAuth de aplicación de escritorio**; no un cliente web. Copia su ID y secreto a `GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET` en `.env`. Gemini y Google OAuth son independientes.

Reinicia VICTOR y pulsa ☰ → Conectar → **Conectar Google**. Se abre el navegador y un receptor temporal en 127.0.0.1. Hay 90 segundos para autorizar. El token se cifra con **DPAPI del usuario Windows** en `data/google.oauth`. Si Windows deniega DPAPI, la conexión persistente falla y nunca se guarda el token en texto plano. Debe ejecutarse en una sesión de escritorio normal del mismo usuario. No compartas `.env`, tokens ni copias de `data/`.

Herramientas disponibles en Tools o mediante IA:

- `google_unread`: hasta cinco correos no leídos, remitente, asunto y extracto proporcionado por Gmail.
- `google_events`: próximos diez eventos del calendario principal. **Próximos eventos Google** en Conectar usa la misma herramienta. Solo tras obtener un evento real aparece su tarjeta en la cabecera; vacía o desconectada no inventa sugerencias.
- `google_drive_search(query)`: hasta 20 archivos por coincidencia de nombre; solo metadatos y enlaces, no descarga documentos.
- `google_send_email(to, subject, body)`: envía realmente el mensaje. **Alto riesgo: muestra el contenido completo y exige EJECUTAR en el PC**. No se envió ningún correo real durante las pruebas de entrega.

El modo Testing, la verificación de scopes sensibles y las políticas de tu organización pueden limitar el acceso. Reautoriza si cambias scopes o caduca el token. Los datos obtenidos pueden incorporarse al contexto de IA si solicitas su análisis; configura el proveedor correspondiente.

## Remoto local HTTPS, QR, trackpad y teclado

1. PC y celular deben estar en la misma red privada. En Conectar pulsa **Activar / detener remoto HTTPS**, espera el aviso y pulsa **Mostrar QR local**. No se inicia automáticamente al abrir VICTOR.
2. Abre el QR en el celular. La URL usa la IP LAN detectada, puerto 8443 (editable como `REMOTE_PORT`) y HTTPS. Es un certificado **autofirmado**: el navegador mostrará un aviso. Comprueba que la dirección corresponde al PC y acepta la excepción local. En algunos navegadores/políticas administradas esta excepción puede no permitirse. No se publica un túnel ni se abre el router.
3. Si Windows pregunta por firewall, permite Python únicamente en tu red privada. El programa no cambia reglas de firewall ni necesita administrador. Las redes Wi-Fi con aislamiento entre dispositivos impedirán la conexión.
4. El QR caduca en 120 segundos y se usa una sola vez. El secreto viaja en el fragmento, se retira del navegador y no se registra en URLs del servidor. La sesión dura diez minutos; máximo cuatro dispositivos. Detener el servidor revoca todas las sesiones.
5. Escribe el **título exacto de la ventana destino**. El trackpad acumula desplazamientos y envía lotes como máximo cada 500 ms o al terminar el gesto. Hay clic izquierdo/derecho/doble y scroll. Cada lote pasa por VictorCore, validación y SecurityManager y pide confirmación en el PC. Los movimientos quedan dentro de la ventana aprobada; pérdida de foco y failsafe detienen la acción. Los lotes recibidos mientras el PC está ocupado se rechazan, no se reproducen después a ciegas.
6. Texto y Enter/Delete exigen EJECUTAR. Escape, Tab, Backspace y combinaciones Ctrl/Alt/Shift mantienen como mínimo confirmación media. Esto es automatización supervisada por lotes, no un ratón con autorización permanente.
7. **Ver pantalla · 60 s** solicita permiso separado. Después transmite JPEG en otro trabajador y otro WebSocket. `SCREEN_FPS=10` y `SCREEN_QUALITY=60`; límites efectivos 1–20 fps y 20–90. La resolución se reduce hasta 1920×1080. El ritmo real depende de CPU, captura y Wi-Fi. Al fallar la captura se detiene y se informa. No se guardan los frames en disco.

`local_remote_enabled` permite desactivar el canal y `remote_block_all` bloquea ambos canales remotos. Telegram y HTTPS coexisten y comparten una sola cola de ejecución y las mismas políticas. El botón de apagado funciona aunque una orden espere confirmación.

El certificado dura 30 días y contiene la IP actual. Su clave persistente se protege con DPAPI. Si DPAPI no está disponible, **solo TLS** puede usar una clave efímera en una carpeta temporal que se elimina al parar: el siguiente inicio cambia el certificado y el navegador pedirá aceptarlo otra vez. No existe ese respaldo para tokens Google/Spotify. El ZIP no contiene certificados ni claves TLS. La prueba real de HTTPS se hizo desde este PC a su IP LAN; conexión desde un celular y rendimiento de streaming real siguen pendientes.

## Pantalla, visión y búsqueda

`take_screenshot` acepta `region: null` para todos los monitores o `[x, y, ancho, alto]` para una región dentro del escritorio. Conserva las últimas 30 capturas en `data/captures`. `active_window` devuelve el título y geometría. Las capturas de visión se reducen a 1600 píxeles por lado como máximo; no es OCR determinista.

Para «¿Qué hay en mi pantalla?» configura un proveedor y modelo de **visión**. Antes de transmitir una captura aparece el proveedor, archivo y pregunta en una confirmación. Sin clave o con un modelo no compatible se muestra un error; no se inventa un análisis. El permiso es por captura, no permanente.

La búsqueda usa `ddgs` (sustituye `duckduckgo-search`), con timeout y caché de cinco minutos. Se detectan expresiones como noticias, hoy, precio, busca e investiga; también puede solicitarla el modelo. Se leen hasta cuatro páginas HTML, con tamaño limitado, sin redirects automáticos y rechazando direcciones privadas/locales. Páginas bloqueadas, de contenido dinámico o no HTML pueden dejar solo el extracto del buscador. Las respuestas incorporan las fuentes y las limitaciones de lectura. Los resultados son datos no confiables, nunca autorización para actuar.

## Arquitectura y datos

`main.py` inicia la aplicación. `victor/core.py` coordina un turno por vez, los adaptadores de `ai/` generan peticiones, y `tools/registry.py` valida esquemas y consulta `SecurityManager` antes de ejecutar. Los plugins son registros internos explícitos; no se carga código arbitrario descargado.

La GUI usa una cola de eventos y solo el hilo principal toca Qt. Red, herramientas y reconocimiento corren fuera del hilo de interfaz. La síntesis vive en un proceso separado. Cerrar cancela tareas y espera a los trabajadores de forma no bloqueante; existe un límite de cierre (timeout de red + 15 segundos) para servicios/controladores que no responden. Los trabajadores pendientes son daemon como último recurso; no se promete interrumpir de inmediato código nativo de terceros.

`data/` contiene SQLite, configuración, logs rotativos (2 MB × 5 archivos) y capturas. Son datos **locales sin cifrar**. No se registran claves API ni cuerpos HTTP. Los proveedores online reciben mensajes, contexto y recuerdos seleccionados para responder. Copia `data/` con la aplicación cerrada para respaldar la información. No compartas esa carpeta si contiene información privada.

El contexto usa un presupuesto de caracteres, mensajes recientes y recuerdos relevantes. Cuando crece, genera un **resumen extractivo local** (sin coste API) que conserva principio y desenlace de mensajes; no es una síntesis semántica y puede omitir detalles. El historial íntegro permanece en SQLite. La ventana carga los últimos 200 mensajes y lista hasta 60 conversaciones; las búsquedas consultan la base completa.

## Solución de problemas

- **No hay Python:** instala Python 3.12 x64 con soporte `venv`; marca Add to PATH. Python de 32 bits puede impedir instalar dependencias.
- **No abre la GUI:** ejecuta `iniciar.bat` desde una terminal para ver el error. Repite `instalar.bat`. Se necesita una sesión de escritorio interactiva.
- **Clave ausente:** revisa el nombre exacto en `.env`, que Windows no lo haya guardado como `.env.txt`, y reinicia.
- **401/403:** clave inválida o permisos insuficientes. **429:** cuota, saldo o límite temporal. **400/404:** modelo/parámetros no compatibles. Edita el modelo.
- **Ollama no conecta:** comprueba que su servicio corre en `http://127.0.0.1:11434` y que `ollama list` muestra el modelo exacto.
- **Voz/volumen/captura no disponible:** son dependencias opcionales. Repite la instalación o instala la biblioteca indicada en el mensaje dentro de `.venv`.
- **Búsqueda falla:** DuckDuckGo puede limitar o bloquear peticiones; espera y vuelve a intentar. No hay resultados ficticios.
- **Archivo fuera de permisos:** muévelo a `workspace/` o autoriza su carpeta de forma explícita en Configuración. No se amplían permisos automáticamente.
- **Paquetes no descargan:** revisa proxy, firewall y conectividad con PyPI. No desactives TLS ni antivirus. El instalador requiere Internet; un fallo de dependencias principales debe corregirse antes de iniciar.
- **Configuración dañada:** se cargan valores seguros y se avisa; el archivo original no se borra automáticamente. Ciérralo antes de restaurar una copia.

## Verificación reproducible

```powershell
.venv\Scripts\python -m compileall -q main.py victor tests
.venv\Scripts\python -m unittest discover -s tests -v
.venv\Scripts\python main.py --smoke-test data\smoke.json
```

La última prueba abre una ventana real, guarda título/visibilidad/geometría y una captura del propio widget Qt (no del escritorio externo); después cierra. Las pruebas unitarias no usan claves, no gastan saldo, no controlan aplicaciones personales ni borran archivos reales. La prueba de papelera usa un mock; consulta `VERIFICACION.md` para saber qué se ejecutó de verdad antes de esta entrega.

## Documentación oficial de las integraciones

- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [Anthropic Messages](https://platform.claude.com/docs/en/api/http/messages)
- [Google GenAI SDK](https://googleapis.github.io/python-genai/)
- [Ollama Chat API](https://docs.ollama.com/api/chat)

Los servicios externos, modelos, cuotas y hardware no se incluyen en el proyecto. Las funciones deshabilitadas deliberadamente se explican arriba; no hay acciones simuladas que se presenten como realizadas.

## Ajustes de v2 y solución de problemas

- La ventana se adapta hasta 420 px. CPU/RAM/red son medidas reales cada dos segundos; red significa tráfico total local de interfaces, no velocidad contratada. La onda se detiene con la ventana inactiva.
- Ollama usa `qwen2.5:7b`; en un i5-8400 sin GPU puede ser lento. Activa `ollama_light` y descarga `ollama pull qwen2.5:3b`. `/api/tags` comprueba disponibilidad antes de pedir inferencia. Configura `ollama_timeout` (180 s), `ollama_keep_alive` (`5m`) y contexto (4096 tokens). `ollama_gpu=cpu` fuerza CPU; `auto` deja la selección a Ollama. Se detectan GPU NVIDIA mediante nvidia-smi; una ausencia no descarta otros dispositivos compatibles con Ollama.
- Configuraciones existentes se conservan: al actualizar desde v1, selecciona explícitamente Whisper, el nuevo modelo Ollama y edge si quieres cambiar tus preferencias anteriores.
- «Abre word» funciona cuando `word` está registrado en `applications`; alias de argumentos app/app_name/application/nombre/program se normalizan a name. Un esquema inválido permite al modelo una sola corrección automática.
- Capturas: primero MSS, después ImageGrab. Una sesión bloqueada, remota o protegida puede impedir ambas. Se informa sin afirmar que se capturó. El resultado de Calculadora distingue solicitud de lanzamiento de ventana visible verificada.
- Telegram no conecta: revisa token, conectividad y otra instancia que esté haciendo polling. Si falta la biblioteca, reejecuta instalar.bat o instala solo python-telegram-bot en .venv. Los cambios en .env requieren reinicio.
- Spotify no conecta: revisa URI exacta, puerto 8888 libre, permisos de tu cuenta en Dashboard y token DPAPI asociado al mismo usuario Windows. No se puede migrar el token cifrado a otro usuario: vuelve a conectar.
- Si una función opcional no se instaló, el instalador lo avisa; el chat sigue funcionando. Python 3.12 de 64 bits es la versión comprobada. No se comprobó una instalación nueva en todas las versiones posteriores de Python.

Documentación: [ddgs](https://github.com/deedy5/ddgs), [Ollama tags](https://docs.ollama.com/api/tags), [python-telegram-bot](https://docs.python-telegram-bot.org/en/stable/), [Spotipy](https://spotipy.readthedocs.io/en/2.26.0/), [Spotify redirect URI](https://developer.spotify.com/documentation/web-api/concepts/redirect_uri).

## Revisión visual v3, punto por punto

Captura propia incluida: **INTERFAZ_V3.png**. Se abrió la aplicación real y se revisaron también las variantes a 420 px y panel cerrado.

1. Panel: ocupa su propia parte del layout, nunca tapa el chat. A menos de 800 px se coloca debajo para evitar comprimir ambos hasta hacerlos ilegibles; al ocultarlo el chat recupera el espacio. Bordes de 20 px y botones rápidos iguales; 2×2 al estrecharse.
2. Burbujas: usuario azul a la derecha, asistente gris a la izquierda, máximo 70%, 12 px entre mensajes. El formato JSON de herramientas/historial se presenta como etiquetas y texto, manteniendo avisos de incertidumbre. Rutas largas abreviadas con texto completo en tooltip.
3. Permisos: tarjeta con alerta y contexto, Confirmar en acento y Cancelar secundario. Las acciones altas conservan la palabra EJECUTAR; el cambio es de presentación, no de autoridad.
4. Métricas: reflow 2×2 y estados con punto verde/azul/ámbar. No se inventan lecturas antes de obtener muestras.
5. Compositor: entrada, micrófono y enviar a 52 px de alto, con etiquetas de escucha/conexión discretas. Detener permanece visible.
6. Tema: paleta y estilos centralizados en `victor/gui/theme.py`, incluidos burbujas, estados y confirmación.

La Parte A solo modificó GUI y sus pruebas. La Parte B corrigió la liberación del MP3 de Qt; la Parte C añadió registros Google y autorización de origen local mediante extensiones acotadas del núcleo existente, sin reemplazarlo.

Fuentes de integración: [Google OAuth](https://googleapis.dev/python/google-auth-oauthlib/latest/reference/google_auth_oauthlib.flow.html), [Gmail send](https://developers.google.com/workspace/gmail/api/guides/sending), [Calendar events](https://developers.google.com/calendar/api/v3/reference/events/list), [Drive files](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list), [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/), [Uvicorn TLS](https://www.uvicorn.org/settings/).
