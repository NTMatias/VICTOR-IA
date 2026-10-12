# Notas históricas de desarrollo

Registro conservado para documentar decisiones, intentos y limitaciones. Las entradas antiguas describen estados anteriores: para capacidades actuales consultar README y RELEASE.

# VICTOR.IA — diseño Grafito integrado · 12/10/2026

## Correcciones de Codex, imágenes y recientes; limpieza del proyecto

Codex se actualizó a **0.162.1**. VICTOR consulta `model/list` del app-server oficial y abre el CLI con un modelo del catálogo actual, sin heredar modelos retirados de la configuración general. El selector muestra esos modelos; Automático usa el recomendado. La configuración global de Codex permanece intacta. Se verificó una respuesta real `OK` con `gpt-6.1-sol`, sin herramientas ni cambios de archivos.

Inicio incluye **Generar imagen** debajo del chat. La pregunta «¿puedes generar imágenes?» recibe una explicación local correcta y el contexto de los proveedores también conoce esta capacidad. El selector permite OpenAI o Gemini y prioriza un proveedor con clave configurada. **La prueba real de Gemini devolvió HTTP 429 por cuota**. La API de los modelos de imagen Gemini no ofrece nivel gratuito; hace falta facturación de API y cuota. Esto es independiente del chat gratuito y de una suscripción ChatGPT. El selector incluye requisitos y enlace de facturación; las denegaciones no se presentan como una imagen generada ni cambian de proveedor silenciosamente. [Requisitos oficiales Gemini](https://ai.google.dev/gemini-api/docs/billing).

Los recientes de WhatsApp excluyen SVG, etiquetas de iconos y badges del texto del mensaje, conservando nombres, emoji y texto real. Se comprueban casos `ic-image` y `wds-ic-read` junto al texto legítimo de foto y mensaje. Se retiraron el editor nativo antiguo, sus clases, el bridge y ejecutables obsoletos; WhatsApp Web y su perfil siguen siendo la integración activa.

La limpieza eliminó aproximadamente **1,25 GB**: caché de instaladores, Gemini CLI retirado, paquete de instalación xterm duplicado (los archivos necesarios están dentro de `victor/gui/terminal`), ejecutable Codex antiguo, cachés de navegadores y backups de configuración antiguos. Se conservan claves, OAuth, historial, perfiles y sus almacenes persistentes, Whisper, entorno Python, dependencias, agentes actuales, código, herramientas de construcción y pruebas activas. Un respaldo del código retirado y el registro de limpieza están fuera de la app en el workspace de Codex.

También se retiró la clase SpotifyList sin referencias activas. Las vistas terminal de Codex/Claude se crean al entrar en cada sección para evitar dos renderizadores Chromium al abrir únicamente el chat.

## ChatGPT por cuenta, Gemini por API y versión portátil · 12/10/2026

En **Ajustes → Inteligencia artificial**, ChatGPT permite elegir cuenta o API key. Gemini usa **únicamente API key**; se retiraron el inicio de sesión Google y el conector Gemini CLI. El botón **Obtener API key de Gemini** abre [Google AI Studio](https://aistudio.google.com/apikey). Pega y guarda la clave en **Claves API personales → Gemini**. Los ajustes antiguos de cuenta Gemini pasan a API al cargar, sin restablecer preferencias ni borrar perfiles personales. No se utilizan credenciales de Antigravity. Gmail, Calendar y Drive conservan su conexión Google independiente.

Se conserva el diseño Grafito con fuente nativa Segoe UI, antialiasing y texto de conversación de 15 px. **Agentes de programación** reúne dos terminales integradas: **Codex** y **Claude Code**, ejecutando sus CLIs oficiales mediante ConPTY y xterm.js. Elige una carpeta de proyecto y abre el agente; sus comandos, sesiones, autenticación, herramientas y permisos se gestionan en su propio terminal. Puedes pegar texto, adjuntar rutas, interrumpir y cerrar la sesión. Claude Code en Windows necesita Git Bash instalado. No se transfieren sesiones privadas al portable.

Pide «genera una imagen de…» y elige **ChatGPT / OpenAI** o **Gemini**, modelo y descripción. La imagen aparece en la conversación, se conserva en el historial y permite ampliarla o guardarla en PNG. **La generación de imágenes requiere API key del proveedor seleccionado**: la conexión de cuenta ChatGPT para texto no cubre esta API. No hay cambio automático a otro proveedor. Detener cancela la espera y termina el proceso local; una petición ya recibida por el proveedor podría haber consumido cuota.

La edición portátil incluye el runtime, las dependencias y el modelo Whisper para abrir VICTOR sin Python ni VS Code en Windows 10/11 de 64 bits. Extrae todo el ZIP en el Escritorio y ejecuta **ABRIR VICTOR.bat**. No contiene sesiones ni claves personales. Para instrucciones y capacidades por modalidad, lee [PORTABLE_CUENTAS.md](PORTABLE_CUENTAS.md).

Esta instalación se modificó directamente en `<CARPETA_LOCAL>`, sin crear otro proyecto. Conserva `.env`, `data/`, `workspace/` y `.venv/`. Para usarla, cierra VICTOR y ejecuta `iniciar.bat`. No necesitas reinstalar dependencias ya instaladas.

## WhatsApp Web con paleta VICTOR y nuevos recientes · última revisión del 11/10/2026

Se restauró **WhatsApp Web visible dentro de Conexiones**, conservando el perfil vinculado. WhatsApp maneja directamente apertura de chats, contactos, mensajes, archivos y borradores; se retiró del flujo activo el editor nativo que podía quedarse en «Abriendo conversación…». La adaptación cambia colores, no sustituye sus controles. Aplica la paleta Grafito en oscuro/claro, incluyendo las variables actuales WDS, compositor y burbujas. La pantalla de vinculación conserva el QR y sus gráficos.

La tarjeta de Inicio ahora tiene filas planas: avatar con iniciales, nombre, hora, vista previa y contador separado sin leer. Se eliminaron los números pegados al nombre/preview provenientes de los badges de WhatsApp; números que sean parte del mensaje se conservan. Las filas abren el chat en la vista web con entrada de ratón del navegador. Datos de recientes solo en memoria y fuera de los proveedores IA.

Verificación: cuatro pruebas WhatsApp aprobadas en 14,757 s y trece de regresión en 14,209 s; vista oficial y QR reales con perfil temporal, temas oscuro/claro, apertura desde recientes con un nombre que contiene emoji, actualización al recibir y cierre. Pruebas de conversaciones con datos ficticios, sin mensajes a personas reales. Capturas de la tarjeta y vinculación inspeccionadas visualmente. Al siguiente inicio, `iniciar.bat` carga la versión nueva.

## WhatsApp con la interfaz de VICTOR · revisión anterior del 11/10/2026

La revisión siguiente conserva el historial. La interfaz de mensajes nativa fue reemplazada por WhatsApp Web visible, según la petición posterior del propietario.

WhatsApp ahora tiene **controles nativos Qt**, con la paleta Grafito de VICTOR: pestañas Chats/Contactos, buscador por nombre (también sin tildes), lista de conversaciones, mensajes recibidos y enviados, borradores independientes y botón Enviar. La tarjeta **WhatsApp · recientes** aparece en Inicio, debajo de Actividad reciente, con los últimos mensajes de dos conversaciones, contadores sin leer y acceso directo al chat. En pantallas bajas puedes desplazar la columna derecha para ver todas las tarjetas.

La página de WhatsApp ya no es la interfaz visible: la sesión vinculada permanece en segundo plano y transfiere a los controles nativos los datos renderizados por WhatsApp. El QR también se muestra en el diseño de VICTOR. Se conserva el perfil `data/whatsapp_webview2`; no hace falta volver a vincular si WhatsApp mantiene la sesión válida. Cierra VICTOR y ejecuta `iniciar.bat` para cargar esta versión.

El envío comprueba el destinatario abierto y un mensaje saliente nuevo antes de confirmar; no reenvía automáticamente si una confirmación falla. Cambiar de chat o escribir mientras termina un envío conserva el nuevo borrador. Los mensajes entrantes no se usan como órdenes, no se añaden al historial del asistente ni se envían al proveedor IA. Texto, tildes, saltos de línea y emoji se muestran como texto, sin ejecutar HTML recibido.

Se comprobaron QR real, controles nativos, recepción/envío con un navegador real usando conversaciones ficticias, temas y adaptación visual. La cuenta personal sigue pendiente de comprobación; la lectura de datos depende de los controles de la página de WhatsApp y puede requerir ajustes si WhatsApp cambia su estructura. Los mensajes multimedia aparecen como Foto/Audio/Archivo adjunto; esta vista implementa el envío de texto, no un visor multimedia completo. Fuentes técnicas: [comunicación WebView2/nativo](https://learn.microsoft.com/en-us/microsoft-edge/webview2/how-to/communicate-btwn-web-native) y [sincronización de contactos de WhatsApp](https://faq.whatsapp.com/1191526044909364/?locale=en_US).

## Canciones con colaboradores y WhatsApp · revisión anterior del 11/10/2026

La descripción de la página visible de WhatsApp en esta entrada conserva el historial; la revisión actual la reemplaza por la interfaz nativa descrita arriba.

La búsqueda musical compara por separado título y artistas, reconoce créditos `feat.`, `ft.` y `featuring` sin tener que dictarlos, y tolera errores breves del artista. **«Bastardo de Pablo Chil-E»** encuentra **«Bastardo (feat. Ñengo Flow & Jere Klein)» de Pablo Chill-E**. Se comprobó con el catálogo real y la selección final en modo de solo lectura, sin iniciar una canción. Si una búsqueda literal falla, también se consulta título y artista juntos sin el «de» de la frase hablada. El artista sigue siendo una condición de selección, no una razón para elegir otra canción cualquiera.

En **Conexiones → WhatsApp → Conectar WhatsApp**, se abre WhatsApp Web oficial dentro de VICTOR. Vincula el teléfono con el QR; tus chats, los mensajes recibidos y el editor de mensajes permanecen en la misma pestaña. **Nuevo chat** permite buscar por nombre entre los contactos que WhatsApp sincronice. Si faltan nombres o contactos, comprueba los permisos de contactos y su sincronización en el teléfono. No se importa toda la agenda del celular por una API propia.

La sesión utiliza un perfil separado en `data/whatsapp_webview2` y permanece abierto al cambiar de pestaña. En siguientes inicios se recupera ese perfil para seguir recibiendo mensajes mientras VICTOR está abierto. Reconectar conserva la sesión. Para desvincular: **Configuración de WhatsApp → Cerrar sesión**, o **Dispositivos vinculados** desde el teléfono. No hay que introducir los números en VICTOR para cada conversación.

Se verificaron el host nativo, navegación de Conexiones, perfil persistente, cierre y QR oficial; el envío y recepción con una cuenta personal requieren que vincules tu teléfono. Fuentes: [WhatsApp Web y escritorio](https://www.whatsapp.com/download/desktop), [sincronización de contactos](https://faq.whatsapp.com/1191526044909364/?locale=en_US), [búsqueda por título y artista de Spotify](https://developer.spotify.com/documentation/web-api/reference/search).

## Captura de voz, ruido y eco · revisión del 11/10/2026

En **Ajustes → Voz → Ruido y eco** puedes activar la reducción de ruido y la cancelación de eco, y elegir intensidad suave, moderada o intensa. Ambas están activadas por defecto, con reducción moderada. Se usa [WebRTC AEC3 y supresión de ruido](https://github.com/strands-labs/pywebrtc-audio), gratis y local, con una referencia del sonido del dispositivo de salida predeterminado de Windows. Esa referencia solo permanece temporalmente en memoria; no se guarda ni se envía a un proveedor. Las peticiones siguen usando el transcriptor que hayas configurado.

La escucha continua conserva el mismo micrófono entre la activación, el saludo y tu petición. Silero distingue actividad de voz del ruido; la palabra **VICTOR** debe dirigirse al asistente, no aparecer dentro de una conversación cualquiera. La detección de activación es local incluso con un proveedor de transcripción remoto. Se corrigieron pérdidas del principio de las respuestas, tiempos de captura, cambios de dispositivo, cortes de audio y pistas de transcripción que podían convertirse en palabras inventadas.

Cierra VICTOR y abre `iniciar.bat` para cargar la actualización. Usa **Probar micrófono sin ejecutar órdenes**, disponible en ajustes y en la sección Voz: muestra la transcripción sin ejecutar herramientas y recupera después la escucha anterior. Prueba por separado con audífonos y altavoces. El filtro no garantiza eliminar otras personas hablando ni toda la reverberación de la habitación; la cancelación necesita la referencia de salida de Windows y no incluye, por ejemplo, un televisor externo.

Verificación: 117 pruebas dirigidas y una prueba adicional del botón de diagnóstico aprobadas; compilación de 19 archivos y dependencias sin conflictos. Las mediciones de reducción de ruido y eco se hicieron con señales sintéticas, no con tu micrófono ni tu habitación. Detalles en `VERIFICACION.md`.

## Interrumpir la voz y esperar tu petición · revisión anterior del 11/10/2026

La descripción siguiente conserva el historial: en la revisión actual la detección de actividad usa Silero y el filtro textual de eco se complementa con cancelación acústica WebRTC.

En **Continua**, puedes decir **«VICTOR» mientras está hablando**: detiene la respuesta anterior, conserva la música baja, responde «¿En qué te ayudo?» y espera una nueva petición. También puedes interrumpir el propio saludo. Durante la locución se mantiene una captura local en fragmentos solapados para detectar exclusivamente la activación; el resto de ese audio no se envía como orden. Usa Whisper local ya preparado, incluso si tus peticiones habituales usan OpenAI o Google. Si el modelo local no está disponible, aparece un aviso y la escucha habitual continúa.

Después del saludo, la música **permanece baja unos 8 segundos** para darte tiempo a contestar. Si empiezas a hablar, la espera de silencio se prolonga; se respeta además el límite de conversación configurado. Al recibir tu petición conserva la bajada durante el procesamiento y la respuesta, y recupera el volumen cuando VICTOR termina. Si no empiezas a hablar, recupera el volumen progresivamente y vuelve a esperar el nombre. Silenciar la escucha, cancelar o cerrar también libera la espera. Manual y push-to-talk conservan sus controles.

Hay un filtro de similitud para descartar frases reconocidas de su propia voz; no equivale a cancelación acústica completa del eco. La detección depende del micrófono, los altavoces y el tiempo de Whisper. Se verificó con audio sintético guardado y pruebas de procesos/captura simulada; queda pendiente comprobar la interrupción audible en el equipo del propietario.

## Volumen de locutor y una petición por activación · 11/10/2026

Cuando la música suena en el reproductor integrado, VICTOR baja su volumen progresivamente hasta **10 % en 2,5 segundos**, habla al terminar la bajada y restaura el nivel anterior con otro fundido de 2,5 segundos. Si la música ya está por debajo del 10 %, conserva ese nivel. Al activar una conversación, la bajada comienza antes de preparar el saludo y se conserva durante la espera de tu petición; en las demás locuciones se prepara la síntesis antes de bajar el volumen. Varias frases en cola comparten la bajada. Un cambio manual de volumen durante la voz se conserva como el nuevo nivel de restauración. Cancelar la voz también restaura el volumen, excepto al interrumpir para iniciar otra petición, cuando mantiene la bajada. El reproductor tiene recuperación automática si pierde el enlace con el proceso de voz. El fundido se ejecuta en el SDK integrado y no bloquea pausa/siguiente/volumen.

«Ponle pausa a la canción», «pon pausa a la música», «pausa la canción» y «páusala» se dirigen a Spotify sin pedirle interpretación a Gemini cuando hay una canción observada. VICTOR es el asistente; el proveedor seleccionado solo genera las respuestas que necesitan IA. La detección/captura y transcripción del micrófono conservan su tiempo propio; no se promete latencia cero.

## Activación por nombre, conversación y tildes · 11/10/2026

Di **«VICTOR»**, espera **«¿En qué te ayudo?»** y después haz **una petición**. Al enviarla, vuelve a esperar «VICTOR»: las conversaciones de fondo no se entregan a la IA ni ejecutan herramientas. Si no empiezas a hablar en unos 8 segundos tras el saludo, también vuelve a esperar el nombre; si hablas, se prolonga la espera dentro del límite configurado. Funciona igualmente con otra app activa o VICTOR minimizado. También acepta «VICTOR, reproduce…» en una sola frase: primero saluda y después procesa esa orden. En modo Manual o push-to-talk puedes hablar sin el nombre. La captura local sigue usando el micrófono para detectar la activación; no significa que el micrófono esté apagado. El saludo espera al final real de la síntesis; el micrófono no procesa la propia respuesta. Música, preguntas y correo usan las mismas herramientas y permisos del chat. Si una petición de voz necesita autorización según la configuración de seguridad, lee los detalles y escucha la confirmación sin otro botón. En ese caso, las acciones de riesgo alto exigen **«ejecutar»**, o **«cancelar»** para rechazar. Las revisiones extensas que no puede leer completas y las órdenes remotas conservan revisión en el PC.

Esta instalación se dejó en modo **continua**, con inicio automático y voz activados. Se encontró que estaba en manual aunque el inicio automático estaba marcado. Reinicia con `iniciar.bat` para cargar el cambio. Silenciar micrófono pausa la escucha. La voz elegida se conserva; el intercambio de texto con su proceso ahora usa UTF-8 explícito y JSON independiente de la codificación de Windows, para conservar tildes, ñ y signos.

Gemini reintenta hasta dos veces los errores 500/502/503/504 antes de iniciar el stream, con espera progresiva cancelable y el tiempo de red configurado como presupuesto. No repite texto ni herramientas de un stream ya iniciado, ni reintenta claves inválidas o cuotas agotadas. Se conserva el respaldo configurado. Los registros mostraron 503 reales del servicio; una consulta breve con el modelo y clave seleccionados respondió durante la verificación. Esto no garantiza disponibilidad permanente de Google. [Guía oficial de errores y reintentos](https://ai.google.dev/gemini-api/docs/troubleshooting).

## Música aproximada y voz en segundo plano · 11/10/2026

Las órdenes musicales priorizan el título/artista exactos y, si el dictado tiene errores, comparan el nombre y los créditos con los resultados de Spotify. «Sex Playlist 1» encuentra «SEXPLAYLIST1»; «tuki tuk de Chris R» puede elegir «TUKI TUKI» de Kris R.; «interludio de Omar Cobbord» puede encontrar «INTERLUDIO» de Omar Courtz. Espacios, acentos, grafías frecuentes y errores breves se toleran; no se selecciona el primer resultado solo por ser popular. La carátula siempre muestra la canción realmente elegida. Si la búsqueda no ofrece nada suficientemente cercano, se pide otro dato. Las selecciones manuales siguen usando su URI exacta.

Al pedir una canción, VICTOR dice «Solicitud enviada: [título]». Cuando el reproductor integrado confirma esa canción en reproducción, añade «Lo escuchas aquí en VICTOR.IA.» con probabilidad de 20 %, «Escuchándose en Spotify desde VICTOR.IA.» con 20 % y ninguna coletilla con 60 %. Una sola elección por solicitud; los cambios de estado no repiten el mensaje y la aceptación de la API por sí sola no afirma que la canción ya suene.

**Escucha sin botones:** esta instalación tiene modo **continua** e **Iniciar escucha continua al abrir VICTOR** activados en Ajustes → Voz. Reinicia con iniciar.bat, deja la app abierta o minimizada, di «VICTOR» y espera el saludo antes de pedir «reproduce TUKI TUKI de Kris R en Spotify». Para otra petición, vuelve a decir «VICTOR». Silenciar micrófono pausa la escucha; cerrar la app la detiene. Se conserva el motor elegido por el propietario (Whisper local, con base ya descargado), sin cambiar claves ni proveedor de IA.

Con cuenta Spotify conectada, el modo de inicio automático prepara el reproductor integrado sin abrir su sección ni una ventana externa. No transfiere ni inicia música al arrancar: espera a la orden. El host WebView2 de esta app permite autoplay en ese modo; el SDK conecta automáticamente. Inicio de sesión y Premium siguen siendo necesarios para el servicio. Si el runtime bloquea el sonido, el reproductor conserva «Habilitar sonido» como recuperación. La [referencia Spotify del SDK](https://developer.spotify.com/documentation/web-playback-sdk/reference) explica el evento autoplay_failed.

## Respuestas legibles y peticiones de música · 11/10/2026

Chat y Voz renderizan Markdown: negritas, listas, encabezados, tablas y enlaces seleccionables, con espaciado y colores adecuados al tema. Los enlaces verificados que el núcleo añade al final no se repiten si ya están citados en la respuesta; las fuentes adicionales aparecen con nombres de dominio en lugar de URLs largas. El historial conserva el texto original. Las tablas se leen en voz alta como filas con sus encabezados, sin pronunciar las barras ni guiones de formato.

**«Reproduce cualquier canción de Fuerza Regida»**, **«pon algo de Bad Bunny»** y **«reproduce música de Kris R»** buscan canciones por artista y eligen una disponible con ese artista en sus créditos. Se evita repetir la última selección cuando hay otra opción en los resultados. Estas órdenes usan la herramienta real de Spotify, también sin consultar a la IA. Si el artista no coincide o no hay pistas disponibles, no se reproduce un resultado de otro artista. Para títulos concretos se prioriza la coincidencia exacta y se admite la aproximación descrita arriba; puedes entrecomillar un título que coincida con una expresión genérica.

## Voz y claves personales · 11/10/2026

**Reconocimiento OpenAI:** guarda tu clave en **Ajustes → Inteligencia artificial → Claves API personales → OpenAI**. Luego abre **Ajustes → Voz**, elige motor **openai**, modelo **gpt-transcribe** y pulsa **Guardar cambios**. Funciona aunque Gemini, Anthropic u Ollama sean la IA principal del chat. El audio de cada intervención se envía a OpenAI por HTTPS, sin guardar grabaciones del micrófono en disco. Requiere Internet y facturación/saldo de API; la suscripción de ChatGPT no sustituye la clave. La pantalla de voz muestra el motor activo. No necesita permisos repetidos por intervención; puedes volver a Whisper local o Google desde ese selector.

Se integra el servicio público de transcripción de OpenAI; no se afirma que sea el motor interno exacto de ChatGPT. `gpt-transcribe` es el modelo recomendado por la [documentación oficial de OpenAI](https://developers.openai.com/api/docs/guides/speech-to-text), con pistas de idioma y nombres propios. Los modelos `gpt-4o-transcribe` y `gpt-4o-mini-transcribe` permanecen como opciones para cuentas que los tengan disponibles. Una clave ausente o rechazada, falta de saldo, fallo de red o cancelación no genera una orden de reproducción. No se cambia de motor silenciosamente si OpenAI falla.

En **Ajustes → Inteligencia artificial → Claves API personales** puedes pegar, guardar o quitar tu clave de OpenAI, Anthropic y Gemini. Los campos ocultan la entrada y se vacían al guardar. Las claves se guardan con DPAPI para el usuario de Windows en `data/ai_keys.dpapi`, nunca en `config.json`, mensajes ni registros. Tienen prioridad sobre `.env`; quitar una clave personal vuelve a usar la de `.env` si existe. Ollama es local y no requiere clave. Guardar una clave no verifica cuota, permisos ni disponibilidad del modelo; **Comprobar conexiones** realiza una petición de diagnóstico al proveedor seleccionado usando esa clave.

En **Ajustes → Voz** hay vocabulario editable para canciones, artistas y aplicaciones, y correcciones musicales explícitas con formato `lo oído => título correcto`, una por línea. Whisper utiliza cinco candidatos de decodificación y pistas de nombres propios. Las sustituciones personales requieren coincidencia del título/artista completo dentro de una orden musical y no cambian dictado libre; después Spotify puede resolver errores restantes mediante coincidencia aproximada. Esta instalación añade **GAMINA / Kris R** y corrige las variantes que el propietario confirmó, incluyendo «la mina de Chris R» y «la mena». En voz, la corrección se avisa antes de ejecutar la orden. Las instalaciones nuevas no llevan estas correcciones personales.

La voz masculina seleccionada es **Jorge (es-MX-JorgeNeural)**. Luis, de Ecuador, sigue disponible en el selector; **Probar voz seleccionada** permite comparar sin guardar. Se limpian formatos Markdown, enlaces y emojis, y los paréntesis/corchetes se convierten en pausas conservando su contenido. La velocidad ahora también se aplica a Edge. El respaldo SAPI verifica el idioma real para evitar elegir una voz inglesa por la palabra «Desktop». [Catálogo oficial de voces de Microsoft](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts).

Se comprobó la mejora de GAMINA con audio sintetizado; la precisión con la voz y el micrófono del propietario aún necesita prueba real. Ningún reconocedor garantiza transcripción perfecta. Para mayor precisión puedes elegir **Whisper small** y descargarlo desde Ajustes → Voz; consume más recursos que base. Reinicia con `iniciar.bat` para cargar esta versión.

## Actualización de servicios · 11/10/2026

- Google tiene pestañas Calendario, Gmail y Drive con logos locales. La agenda muestra fechas en español y hora local de Windows, incluyendo eventos de todo el día. Los correos muestran asunto, remitente, fecha y resumen; doble clic abre el hilo en Gmail. Drive muestra nombre, tipo y última modificación, y abre el enlace con doble clic. No se duplican IDs, JSON ni URLs en cuadros de texto.
- Spotify muestra la carátula de mayor resolución disponible, conserva los píxeles originales para HiDPI y se adapta a ventanas estrechas. La biblioteca usa tarjetas con nombre y propietario. Los controles tienen respuesta visual optimista, debounce de volumen de 120 ms, coalescencia y deduplicación de envíos. Los errores revierten la predicción; no se inventa una canción reproducida.
- Esta instalación guarda **`action_confirmations=false`** por petición expresa del propietario. Todas las herramientas permitidas se ejecutan sin diálogos. Puedes reactivarlos en **Seguridad → Pedir confirmación antes de acciones → Guardar política**. Las instalaciones nuevas sin configuración conservan las confirmaciones activadas. Se mantienen esquemas, límites de archivos, comandos bloqueados, revocación y autenticación de dispositivos; eliminar diálogos no habilita comandos arbitrarios ni elevación administrativa. La auditoría distingue «Directa (sin diálogo)» de «Confirmada».
- OAuth de Google/Spotify y QR de emparejamiento siguen siendo necesarios para acceder a cuentas/dispositivos. Las instrucciones antiguas de este README que mencionan aprobar/EJECUTAR solo aplican si reactivas las confirmaciones.

### Reproducir dentro de VICTOR, sin Spotify desktop

El panel original **Reproduciendo ahora** se conserva arriba a la izquierda: carátula, título/artistas y controles a su lado, volumen, posición y acceso al mini reproductor. Biblioteca y búsqueda están a la derecha, dentro de la misma app y con su paleta grafito/azul e Inter. En ventanas estrechas se apilan con desplazamiento vertical. El tema claro también se sincroniza. Los controles del panel Qt y el catálogo integrado usan el mismo reproductor; el pie web muestra únicamente estado y enlace a Spotify.

1. Reinicia VICTOR con iniciar.bat y cierra el reproductor externo de versiones anteriores.
2. Abre Conexiones → Spotify. Biblioteca, buscador/filtros y controles están en una sola vista integrada mediante WebView2; no se abre otra ventana de reproducción.
3. Pulsa Activar audio una vez. Necesitas Premium, Web Playback SDK habilitado en tu aplicación del Dashboard y permisos streaming/user-read-email; Conectar Spotify renueva OAuth si faltan. El gesto inicial habilita sonido, no añade confirmaciones por canción.
4. Busca y elige una canción o abre una colección y selecciona una pista/episodio. Abrir playlists no reproduce automáticamente la primera canción. Cambiar de sección mantiene el mismo reproductor y el mini reproductor de Inicio.
5. Di «Reproduce gamina en Spotify»; se comprueba el título entre varios candidatos. Si no coincide, se informa y no se toca otra pista. Añade el artista para distinguir canciones del mismo nombre. Chat y Voz muestran carátula/título/artistas; el estado observado confirma la reproducción.
6. Reconectar reinicia el reproductor dentro de la app. Cerrar VICTOR termina el host y su audio. El navegador sigue siendo necesario únicamente para OAuth o enlaces que elijas abrir.

Windows x64, .NET Framework 4.6.2+ y [WebView2 Evergreen Runtime](https://developer.microsoft.com/microsoft-edge/webview2/) son necesarios; el runtime ya estaba instalado en esta PC. El SDK oficial 1.0.4258.31 y el host compilado se incluyen en victor/gui/webview2, con licencia/procedencia y build.ps1 para recompilar. El perfil está en data/spotify_webview2, sin claves de aplicación embebidas. Se conserva el servidor loopback autenticado, OAuth DPAPI, registro de herramientas y controles SDK. Referencia de integración: [WebView2 en WinForms](https://learn.microsoft.com/microsoft-edge/webview2/get-started/winforms).

Estas instrucciones sustituyen las referencias históricas a una ventana de Edge/Chrome. Audio audible, micrófono y continuidad minimizada pendientes del propietario: ver VERIFICACION.md.

Las órdenes de reproducción del chat/voz se enrutan directamente a Spotify, también con «reproducir», puntuación final, el nombre de activación y «GAMINA de Kris R en Spotify». No se usa una respuesta de la IA como comprobante de ejecución. Las correcciones personales de voz se aplican antes de buscar. Se prioriza la canción exacta y se usa la mejor coincidencia cercana cuando hay errores de dictado; la carátula muestra la selección real. Si no hay una coincidencia suficientemente cercana se informa. La búsqueda por artista usa campos separados y, si el artista está mal escrito, puede consultar solo el título.

### Comprobación realizada

126 pruebas aprobadas en el pase completo (64,172 s); compilación sin errores y ventana Qt real abierta/cerrada. Las pruebas nuevas cubren fechas, metadatos Google, selección de carátula, validación conservada en modo directo, protocolo HTTP/ACK del reproductor y JavaScript ejecutado con SDK/DOM simulados. Las capturas de revisión usan datos de prueba, no correos reales. Véase VERIFICACION.md para el último pase dirigido y las comprobaciones físicas pendientes.

## Navegación y botones

La barra lateral tiene Inicio, Voz, Memoria, Historial, Conexiones, Seguridad y Ajustes. Herramientas se encuentra en Ajustes → Generales → Herramientas avanzadas; sus comandos de voz se conservan. **Las vistas secundarias aparecen como pestañas visibles dentro de cada sección**, con una única selección. El nombre en el encabezado conserva su menú y Ctrl+K permite buscar vistas. F11 y el botón Modo presentación esconden/reponen los paneles. En la esquina superior derecha, de izquierda a derecha: **− minimiza, □ maximiza/restaura, × cierra**, con símbolos estilo Windows sin círculos. Las transiciones de escala/desvanecimiento duran 220–260 ms sin bloquear tareas; restaurar desde la barra de tareas también anima. Son una adaptación Qt para Windows, no el Genie nativo de macOS. La esquina inferior derecha permite redimensionar; el fondo libre del encabezado permite arrastrar la ventana. Los avisos desaparecen tras 5,5 segundos y se conservan en el botón **Ver avisos recientes** del encabezado.

- Inicio: chat, micrófono, enviar/detener, accesos a pantalla/navegador/aplicaciones/memoria, métricas reales, próximo evento si se consulta Calendar y reproductor cuando Spotify devuelve una reproducción real.
- Voz: escucha, parada, manual/push-to-talk/continua, transcripción y respuesta, acceso a ajustes y descarga Whisper con progreso mediante el proceso existente. La banda de micrófono reacciona al PCM capturado y el orbe central al audio de VICTOR. **Voz de VICTOR · activada/desactivada** controla leer respuestas; abrir la sección no cambia esa preferencia. Qt ≥6.8 con buffers PCM permite la medición de TTS; si el motor/backend no la ofrece se avisa y la voz sigue disponible. SAPI renderiza WAV para medirlo, con respaldo directo sin medición; puede añadir espera de preparación. Prueba física pendiente, detallada en VERIFICACION.md.
- Herramientas avanzadas (ocultas del menú principal): Windows/aplicaciones, información del equipo, procesos/disco/batería, volumen, configuración Windows, comandos permitidos; archivos/carpetas; captura/visión; búsqueda web y enlaces.
- Biblioteca: buscar/retomar/crear/borrar chats y guardar/buscar/borrar recuerdos locales.
- Conexiones: Spotify (OAuth, estado, controles, volumen, posición, búsqueda y playlists); Google (OAuth, Calendar, Gmail, Drive y borrador de correo con autorización); Telegram (iniciar, pausar, vincular y revocar usuarios); remoto HTTPS (iniciar, QR, dispositivos y revocación).
- Ajustes: los cuatro proveedores y sus modelos editables, temperatura/tokens/contexto, fallback arrastrable, personalidad, Ollama, visión, voz, preferencias y permisos. **Guardar cambios** valida y persiste; los permisos sensibles requieren confirmación.
- Seguridad: solicitudes reales en un diálogo MEDIO/ALTO, confirmación por voz en el PC, preparación/conexiones y últimas acciones de auditoría. Los resultados de herramientas aparecen en su sección; no se fabrican cuentas ni mediciones para rellenar el diseño.

Se utilizaron las 23 imágenes del ZIP como referencia directa: 21 vistas de escritorio, la confirmación y la página móvil. Se incluyen Inter e IBM Plex Mono con licencias OFL; los iconos son SVG vectoriales recreados. Se conservaron las funciones de los servicios existentes y se enlazaron sus botones al registro de herramientas. `core.py` y `security.py` permanecen idénticos al respaldo previo. Los colores y medidas siguen Grafito; Qt/Windows, contenido real y vectores recreados producen diferencias respecto al raster. No se afirma identidad pixel por pixel.

## Spotify: respuesta rápida sin ocultar errores

### Biblioteca y búsqueda integradas (11/10/2026)

Se retiraron las dos listas Qt duplicadas. La vista integrada conserva biblioteca lateral, buscador superior, seis filtros, listado central con carátulas y duraciones, paginación y barra inferior. Playlists/álbumes/podcasts abren su contenido sin iniciar audio; la canción elegida se reproduce por URI y posición exactas. Buscar no cambia la música; las respuestas obsoletas se descartan. En ventanas estrechas, Biblioteca/Inicio permite volver a tus listas y actualizarlas.

Spotify puede rechazar contenido no autorizado por cuenta, región o permisos de la playlist. Se muestra el error y se permite abrir el enlace expresamente en Spotify. Las operaciones pasan por el registro y la política existente. La lectura de metadatos, EME/DRM y el alojamiento real en Qt fueron comprobados; la reproducción audible sigue pendiente.

## Remoto: pantalla, dedo y teclado en la misma página

`/screen`, `/pointer`, `/keyboard` y `/control` son canales separados; captura, puntero, teclado y sonda de foco no esperan la cola IA. Se coalescen movimientos pendientes; los toques se mapean al marco realmente mostrado, respetando proporción, origen virtual negativo y márgenes. La página avisa de Wi-Fi/HTTPS/certificado y descarta entradas al desconectarse.

Cada sesión QR se vincula al dispositivo/IP y origen HTTPS. El permiso táctil MEDIO es único por conexión/destino y se revalida antes de cada evento; `mouse_click`/`move_mouse` generales conservan sus niveles. El teclado ordinario de la sesión emparejada es MEDIO sin diálogo por palabra. `type_text` fuera del remoto sigue ALTO. El código bloquea dirigir estos canales a la ventana/PID de VICTOR para impedir autorizar sus propios diálogos.

Atajos ALTO en `keyboard_protocol.py`: Ctrl+Alt+Supr, Ctrl+Shift+Escape, Alt+F4, Ctrl+Escape, Win+L, Win+X, Win+R, Sleep, Power, sus superconjuntos y cualquier combinación con Win. Exigen confirmación explícita en el PC cuando `action_confirmations=true`; en el modo directo se omite ese diálogo. Windows bloquea sintetizar Ctrl+Alt+Supr/Power: se informa, no se elude esa protección. El foco editable se comprueba sin leer contenido ni contraseñas. La apertura automática del teclado depende de UI Automation y las reglas del navegador; el botón **Teclado** es la alternativa en la misma página.

## Prueba exacta desde el celular

1. Cierra la versión anterior de VICTOR y la pestaña remota antigua. Abre `iniciar.bat` desde esta carpeta en tu escritorio normal de Windows; no reinstales las dependencias.
2. Conecta PC y celular a la misma Wi-Fi. Abre Bloc de notas con un documento de prueba. En VICTOR, pulsa **Conexiones** en la barra lateral y la pestaña visible **Control remoto**. También puedes buscar «Control PC desde el celular» con Ctrl+K.
3. Pulsa **Iniciar / detener servidor**, espera «Servidor activo» y pulsa **Mostrar QR**. Escanéalo antes de 120 segundos. La URL debe coincidir con `https://<IP-del-PC>:8443/#<código>` (o el puerto REMOTE_PORT configurado). El fragmento QR es de un solo uso: no lo compartas.
4. En el navegador móvil acepta el certificado autofirmado de esa IP: Avanzado → Continuar; en Safari, Mostrar detalles → Visitar sitio web, si se ofrece. Si Windows solicita firewall, permite Python en la red privada. Si el certificado caducó, detén/inicia el servidor y genera otro QR. No desactives globalmente la validación de certificados del navegador.
5. Autoriza **compartir pantalla** en el PC. Mantén «Escritorio completo» para controlar directamente la imagen. Debe aparecer «En vivo». El streaming no tiene el corte anterior de 60 segundos: continúa mientras la página esté conectada, autorizada y activa. El bloqueo/suspensión del PC, la Wi-Fi o la caducidad del certificado pueden interrumpirlo.
6. Desliza un dedo sobre la imagen: debe mover el cursor. El primer movimiento/clic solicita una confirmación MEDIO en el PC para ese canal y destino; acepta. Un toque breve hace clic y dos dedos desplazan verticalmente. No hay un trackpad separado. Las zonas negras fuera de la imagen no se convierten en clics.
7. Toca el área editable de Bloc de notas. Si Windows expone su foco y el navegador permite abrirlo, aparecerá el teclado nativo. Si no aparece, pulsa **Teclado** en la misma página: iOS/Android pueden exigir ese gesto directo. El campo HTML solo sirve de entrada; cada cambio se envía como teclado real al PC.
8. Escribe `Hola áéñ 123 !`, un emoji y una frase normal. Deben reflejarse en Bloc de notas sin pedir EJECUTAR por palabra. Prueba Intro, Retroceso, Escape, flechas y Ctrl+A; desmarca Ctrl después. Los modificadores se presionan y liberan dentro de cada paquete; la composición IME se envía al confirmar el carácter.
9. En un documento desechable, Ctrl+Shift+Escape debe pedir **EJECUTAR** en el PC. Primero rechaza: no debe abrirse el Administrador de tareas. Las combinaciones peligrosas mantienen riesgo ALTO. Alt+F4 puede cerrar trabajo; Ctrl+Alt+Supr no es sintetizable por Windows aunque se autorice y debe mostrar una explicación.
10. Déjalo abierto más de diez minutos con la pantalla del móvil activa: los latidos renuevan la sesión cada tres segundos. No se promete continuidad si el navegador queda suspendido en segundo plano. Apaga Wi-Fi y comprueba que aparece aviso de desconexión; tras unos 15 segundos sin latidos se detiene, sujeto a la planificación del navegador. Restaura Wi-Fi y empareja con otro QR: nunca se repiten entradas pendientes. **Detener** en el móvil, revocar el dispositivo o apagar el servidor en el PC termina el acceso.

## Comprobación y limpieza

109 pruebas de la suite aprobadas, más dos pases de tres pruebas GUI afectadas aprobadas después del contraste claro y la sincronización del reproductor. `compileall` terminó con código 0. Se abrió la ventana Qt y se revisaron capturas de todas las vistas con perfil temporal; esto no verifica cuentas, dispositivos móviles ni streaming del escritorio real. No se intentó capturar ni controlar el escritorio aislado CodexSandboxDesktop. Solo el propietario puede confirmar entrada/streaming reales, latencia Spotify y apertura del teclado iOS/Android.

Se eliminaron cachés Python del código/tests y se trasladaron tres capturas históricas fuera del proyecto, manteniendo respaldo. No se borraron modelos, conversaciones, tokens ni archivos personales. PROGRESO.md y VERIFICACION.md detallan cambios, pruebas y pendientes.

---

# Documentación base histórica

Las instrucciones de claves y proveedores inferiores siguen siendo útiles. Los nombres de navegación, límites remotos y capturas de versiones anteriores quedan sustituidos por las instrucciones actuales de arriba.

# VICTOR.IA v4

Asistente de escritorio modular para **Windows 10/11 y Python 3.11+ de 64 bits**. Interfaz PySide6 (Qt), chat con streaming, cuatro proveedores de IA, herramientas supervisadas de Windows, memoria e historial SQLite y voz opcional.

## Instalar y abrir

1. Descomprime **toda** la carpeta `VICTOR_IA` en una ubicación donde tengas permisos de escritura (por ejemplo, Documentos). No lo ejecutes dentro del ZIP ni como administrador.
2. Ejecuta **instalar.bat**. Crea `.venv`, instala las dependencias y comprueba los imports principales. Requiere Internet para descargar paquetes. Si no encuentra Python, muestra cómo instalarlo; recomendamos Python 3.12 de 64 bits desde python.org.
3. Ejecuta **iniciar.bat**. Se abre la ventana incluso sin claves API. Los comandos locales y los paneles de memoria e historial funcionan sin servicio de IA.

El instalador copia `.env.example` a `.env` si este no existe. Nunca sobrescribe tus claves, configuración ni historial. Puedes repetir la instalación para reparar dependencias. No incluye modelos ni un runtime Python dentro del ZIP.

## Configurar IA

Usa **Ajustes → Inteligencia artificial → Claves API personales** para guardar tus claves cifradas desde la app. Alternativamente, edita `.env` con un editor de texto y completa solo las claves que necesites:

```dotenv
OPENAI_API_KEY=tu_clave
ANTHROPIC_API_KEY=tu_clave
GEMINI_API_KEY=tu_clave
```

También se admiten variables de entorno con esos nombres; tienen prioridad sobre `.env`, pero una clave personal guardada en la app tiene prioridad sobre ambas. Las claves guardadas desde Ajustes se usan en la siguiente petición; los cambios externos de `.env` requieren reiniciar. No se guardan en `config.json` ni se registran en logs; las entradas de la GUI están ocultas y no revelan claves previamente guardadas. `.env` es texto local: protégelo y no lo compartas. Una suscripción de chat no implica saldo/API disponible.

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
- La pestaña Tools fue retirada. Pide las acciones por texto o voz; el registro interno de herramientas conserva sus permisos. Los comandos locales documentados funcionan sin IA; las frases libres requieren un proveedor.
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
- Cerrar aplicaciones usa terminación de proceso y **puede perder cambios sin guardar**. Su confirmación depende de la política elegida en Seguridad. Algunas aplicaciones de Windows usan un proceso distinto del lanzador; en ese caso no se cierran y se informa.

**Riesgos:** bajo = ejecución directa; medio = tarjeta de confirmación dentro del chat con parámetros exactos; alto = tarjeta y escribir `EJECUTAR`. `strict` también confirma operaciones de bajo riesgo. Con `action_confirmations=false` se omiten los diálogos de todos los niveles, incluida la frase EJECUTAR, por decisión del propietario. Las validaciones y bloqueos no se omiten. Cada solicitud y su resultado se registran, sin guardar cuerpos con claves.

La terminal está limitada a `ipconfig`, `whoami`, `hostname` y `systeminfo`, **sin argumentos**, con confirmación si está activada y siempre con `shell=False`. Los comandos arbitrarios, instalación de software, edición del registro y elevación administrativa están **deliberadamente deshabilitados**. La IA no puede modificar las listas de permisos.

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
5. Envía texto o una nota de voz (máximo 60 segundos/15 MB). El audio se descarga temporalmente y muestra la transcripción. Con motor openai seleccionado, se envía a la API de OpenAI usando tu clave; con los otros motores, las notas se transcriben con Whisper local y requieren el modelo descargado. Texto, voz y PC usan el mismo VictorCore y registro de herramientas.

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

Herramientas internas disponibles mediante órdenes naturales interpretadas por IA:

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

La captura de v3 fue sustituida por las capturas actualizadas de **CAPTURAS_V4/**. Se abrió la aplicación real y se revisaron también las variantes a 420 px y panel cerrado.

1. Panel: ocupa su propia parte del layout, nunca tapa el chat. A menos de 800 px se coloca debajo para evitar comprimir ambos hasta hacerlos ilegibles; al ocultarlo el chat recupera el espacio. Bordes de 20 px y botones rápidos iguales; 2×2 al estrecharse.
2. Burbujas: usuario azul a la derecha, asistente gris a la izquierda, máximo 70%, 12 px entre mensajes. El formato JSON de herramientas/historial se presenta como etiquetas y texto, manteniendo avisos de incertidumbre. Rutas largas abreviadas con texto completo en tooltip.
3. Permisos: tarjeta con alerta y contexto, Confirmar en acento y Cancelar secundario. Las acciones altas conservan la palabra EJECUTAR; el cambio es de presentación, no de autoridad.
4. Métricas: reflow 2×2 y estados con punto verde/azul/ámbar. No se inventan lecturas antes de obtener muestras.
5. Compositor: entrada, micrófono y enviar a 52 px de alto, con etiquetas de escucha/conexión discretas. Detener permanece visible.
6. Tema: paleta y estilos centralizados en `victor/gui/theme.py`, incluidos burbujas, estados y confirmación.

La Parte A solo modificó GUI y sus pruebas. La Parte B corrigió la liberación del MP3 de Qt; la Parte C añadió registros Google y autorización de origen local mediante extensiones acotadas del núcleo existente, sin reemplazarlo.

Fuentes de integración: [Google OAuth](https://googleapis.dev/python/google-auth-oauthlib/latest/reference/google_auth_oauthlib.flow.html), [Gmail send](https://developers.google.com/workspace/gmail/api/guides/sending), [Calendar events](https://developers.google.com/calendar/api/v3/reference/events/list), [Drive files](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/list), [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/), [Uvicorn TLS](https://www.uvicorn.org/settings/).

## V4: interfaz, voz y reproducción

El panel lateral contiene **Historial, Memoria, Ajustes, Conectar y Voz**. No hay consola JSON ni pestaña Tools. Se conservan cabecera, CPU/RAM/red/estado, accesos rápidos y chat. Los estilos usan tarjetas de 24 px de radio, títulos de peso alto y cuerpo ligero; el tipo de letra elige Nunito/Rubik si están instalados y usa Segoe UI como respaldo.

**Confirmaciones legibles.** Los nombres de todas las herramientas se traducen desde `gui/tool_labels.py`. Sus detalles muestran frases como «Nivel: 37 de 100», rutas, destinatario y cuerpo del correo; los argumentos internos y validación siguen intactos. Los resultados históricos también se presentan sin el nombre técnico. La información crítica de la confirmación no se abrevia.

**Mini Spotify.** Aparece en la esquina inferior derecha cuando la cuenta conectada devuelve una canción. Consulta cada cinco segundos; tras un fallo espera 30 segundos. Usa carátula real si está disponible, título/artista con tooltip, anterior, reproducción/pausa, siguiente y volumen. Una pausa se muestra hasta cinco minutos. La × oculta el widget sin desconectar; vuelve a estar disponible al cambiar de pista. Se oculta durante confirmaciones para no taparlas. Solo Spotify volumen pasó a riesgo bajo; en seguridad normal no pide confirmación. El modo `strict` conserva su política de confirmar también acciones de bajo riesgo. Los demás controles conservan riesgo medio. El deslizador agrupa cambios durante 450 ms, espera si el núcleo está ocupado y consulta el estado real después. No existe reproducción simulada en la aplicación.

**Asistente de voz.** En ☰ → Voz pulsa Abrir asistente de voz. Oculta el historial y muestra el micrófono grande, estado, última transcripción y respuesta. Activa la lectura de respuestas usando la salida de voz existente; se puede volver al chat. Reutiliza manual, push-to-talk, continua y wake word de Ajustes. Necesita el modelo Whisper ya descargado o el reconocimiento alternativo configurado.

Para confirmar hablando, primero pulsa **Responder a la confirmación** (o el botón de voz dentro de la tarjeta) en el PC. Se detiene la voz de salida, se reinicia la captura y se vincula a esa solicitud concreta. Entonces acepta «sí», «confirmar», «confirmo» o «ejecutar»; «no»/«cancelar» rechazan. También admite acciones altas: es una autorización local explícita solicitada por el usuario. Las grabaciones de una escucha anterior no autorizan una solicitud nueva. Los mensajes/notas de voz recibidos por Telegram nunca se convierten en confirmación local: mantienen sus botones inline y las restricciones remotas. Los botones y la palabra EJECUTAR siguen disponibles como alternativa visual.

## Telegram y lenguaje natural

Telegram ya entrega cada frase libre al mismo VictorCore que el chat; v4 lo comprueba con pruebas nuevas y muestra resultados/confirmaciones legibles. Si falta IA, se entrega el error de configuración al chat remoto. No se creó otro agente ni una ruta de ejecución separada. «Abre Chrome», «abre google.com», redactar/enviar correo y consultar pantalla dependen de los comandos locales o de la IA configurada. Un contacto debe tener una dirección conocida; no se inventan destinatarios.

Se añadió una herramienta interna supervisada para buscar y abrir el primer resultado público de YouTube. Permite al modelo resolver «abre YouTube y pon el video …» desde texto, voz o Telegram. La búsqueda pública puede fallar si YouTube cambia su página, exige consentimiento o bloquea el acceso. Se solicita reproducción automática al navegador, pero **no se afirma que esté sonando**: anuncios y políticas de autoplay pueden impedirlo. No se comprobó esta reproducción con cuenta y navegador reales durante v4. No usa una API key adicional ni elude restricciones de acceso.

## Remoto v4: una sola pantalla móvil

El QR abre el escritorio ocupando la mayor parte de la página y solicita inmediatamente autorizar 60 segundos de captura en el PC. Pantalla, tacto y teclado comparten la misma vista. Sigue haciendo falta el título exacto de la ventana destino y la aprobación del PC.

- Un dedo mueve el cursor a la posición tocada y hace clic. Dos dedos desplazan verticalmente. Se respeta la proporción de la imagen, se rechazan toques en bandas vacías y se tienen en cuenta monitores con coordenadas negativas. Una imagen de referencia caduca a los 30 segundos para no ejecutar sobre una captura antigua.
- **Teclado** enfoca un campo HTML y abre el teclado del celular. El texto se agrupa tras 450 ms de pausa y se pone en una cola acotada (máximo ocho entradas); también hay Retroceso, Intro, Escape, Tab y modificadores. El foco de campos de aplicaciones del PC no se detecta automáticamente: usa el botón Teclado.
- Las entradas siguen pasando por SecurityManager. Texto e Intro requieren confirmación alta en el PC. Por ello **la escritura no se aplica instantáneamente sin autorización**, aunque se prepare mientras escribes. No se ha convertido el canal en un teclado sin permisos.
- El streaming y el control usan trabajadores/conexiones separados. Imágenes de más de tres segundos se atenúan; puedes renovar la transmisión. Cada gesto, confirmación y red añade latencia. No es un sustituto de escritorio remoto profesional; fluidez y compatibilidad de teclado móvil deben probarse en tu Wi-Fi.

Los flujos OAuth de Google y Spotify no fueron modificados. Si actualizas una instalación ya configurada, conserva tu `.env` y `data/`; el ZIP no los incluye. No necesitas reautorizar únicamente por este cambio de GUI.

## Capturas incluidas

`CAPTURAS_V4/01_general.png`, `02_sin_tools.png`, `03_confirmacion.png`, `04_spotify_ejemplo.png` y `05_voz.png` se generaron abriendo widgets Qt reales. **Solo la captura del mini Spotify usa datos de ejemplo**, marcada expresamente en la imagen; no acredita conexión ni reproducción real. La solicitud de confirmación es una prueba visual que se canceló sin ejecutar una acción.
