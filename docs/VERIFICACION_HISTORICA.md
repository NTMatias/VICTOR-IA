# Verificación actual — 12/10/2026 — proyecto Desktop/VICTOR_IA

## Correcciones y limpieza posteriores

- **53 pruebas dirigidas aprobadas** para modelos Codex, imágenes, WhatsApp Web, diseño, GUI, cuentas/credenciales; dependencias sin conflictos y compilación correcta. Tras diferir la carga de renderizadores de terminal hasta abrir su sección, se repitieron 23 pruebas afectadas: aprobadas. Interfaz aislada inspeccionada en oscuro/claro/560px, selector de imágenes, recientes con datos ficticios y TUI Codex REAL funcionando dentro de la app, sin tareas adicionales de IA. Cierre limpio.
- Codex 0.162.1 real: catálogo descubierto mediante `model/list`; `gpt-6.1-sol` recomendado. Inferencia real de control produjo `OK`, evento `turn.completed`, código de salida 0, cero herramientas/cambios. El modelo global anterior `gpt-5.4` se conserva en la configuración ajena a VICTOR pero no se hereda al abrir desde VICTOR.
- WhatsApp: cuatro pruebas WebView2 reales/fixtures aprobadas; SVG con títulos `ic-image` y `wds-ic-read` excluido de previews, texto legítimo y clic real del navegador preservados. No se enviaron mensajes a contactos reales. Cuenta y perfil del propietario no utilizados por esas pruebas.
- Imágenes: pregunta de capacidad, botón directo, selector, adjuntos/historial/PNG y errores verificados con fixtures. **Solicitud REAL a Gemini Nano Banana 2.1 rechazada con HTTP 429 por cuota**; no se generó imagen real y no se alteró facturación. El modelo requiere nivel de API de pago según documentación oficial. No presentar los fixtures como una imagen generada con la cuenta del usuario.
- Limpieza completada: **1.248.937.734 bytes**, 37 destinos, cero archivos pendientes. Registro exacto/backup de código en `work/victor_cleanup` fuera del proyecto. Datos persistentes y secretos fuera de los destinos borrados. Auditoría de módulos tras limpieza sin candidatos sin referencia; dependencias nativas activas conservadas.

## Revisión actual: Gemini por API, tipografía, imágenes y agentes

- **55 pruebas distintas dirigidas aprobadas**: 35 cuentas/credenciales/diseño, 10 imágenes/agentes/GUI y 10 Gemini/artistas. Se repitieron las 22 pruebas afectadas por el último ajuste: cancelación de proceso de imágenes, recarga durante generación y etiqueta completa del menú. `pip check` y compilación correctos.
- Gemini no tiene AccountPanel ni proveedor de cuenta; conserva proveedor API y clave cifrada. Se comprueban migración de configuración antigua sin restablecer preferencias, ausencia de lanzamiento CLI si falta clave, chat/visión mediante clave y conservación del flujo ChatGPT sin respaldo de pago.
- Botón de Google AI Studio probado con navegador simulado; destino oficial `https://aistudio.google.com/apikey`. Interfaz inspeccionada en capturas aisladas, sin datos privados.
- Segoe UI verificada en la ventana; Codex y Claude Code oficiales respondieron a `--version` mediante ConPTY. Terminal Unicode/redimensionado/cierre y xterm WebChannel verificados. CLI completo integrado; no se ejecutaron tareas de programación que consuman cuenta.
- Generación y conservación de imágenes verificadas con respuestas sintéticas. No se consumió saldo real ni se comprobó la elegibilidad de una cuenta para cada modelo. El código usa las APIs oficiales; Gemini REST extrae las imágenes finales de `steps/model_output/content`.
- El ZIP anterior de USB no se ha actualizado en esta revisión. La sección siguiente es la verificación histórica de esa entrega.

## Cuentas y portátil

- **Entrega USB verificada:** `<USB>` tiene 1.010.507.181 bytes. Los CRC de todos los archivos del ZIP son correctos; SHA256 del ZIP copiado coincide con el de origen: `ff56fa060c7aa97bc17390cc813738b3f0435df3bdda738140222843416822e9`. Se comprobó lista del manifiesto y ausencia de datos privados en `data/` y de claves no vacías en `.env`. Guía y comprobante escritos y sincronizados en la USB; no se formateó ni se borró contenido previo.

- **101 pruebas distintas dirigidas aprobadas**: 28 en `test_ai_accounts`, `test_gemini_errors`, `test_voice_and_credentials`, `test_gui_qt`; 73 en `test_voice_interrupt`, `test_voice_pipeline`, `test_radio_ducking`, `test_wake_conversation`, `test_whatsapp_embed`, `test_music_artist_match`, `test_spotify_voice_commands`. Se repitieron los grupos afectados por ajustes finales; no se contó dos veces una prueba repetida.
- OAuth: callback HTTP real, PKCE, firma JWT/JWKS, issuer/audiencia/expiración/nonce/state, denegación de scope, DPAPI, persistencia, rotación de refresh y revocación con identidades sintéticas. Responses con texto/funciones y finalización; cuota, parcial y cancelación no son éxito. No se autorizaron cuentas personales ni se consumieron APIs de pago.
- Gemini: CLI 0.63.0 real comprobado con --help/--version. Subprocesos de fixture verificaron NDJSON, eliminación de claves del entorno, policy/core allowlist, cuota y terminación al cancelar. Inicio de sesión Google/consulta real requiere autorización del usuario; no se presenta el fixture como prueba de su suscripción.
- GUI real sin claves, con métodos de cuenta: arranque, imágenes en 1450px/560px, cero desbordamiento horizontal y cierre limpio. Dependencias sin conflictos y compilación Python correctas.
- Portátil real con su Python 3.12 y _pth aislado, PATH restringido a Windows: 12 módulos/dependencias nativas importados, Gemini CLI incluido, Whisper base offline transcribió `Victoria, reproduce GAMINA de Kris R en Spotify.` usando el decodificador de VICTOR. Silero incluido. La GUI abrió y WhatsApp llegó a QR usando WebView2 Fixed Runtime incluido; cierre limpio. No se utilizó el micrófono del usuario ni se enviaron mensajes a contactos.
- El acceso directo al decodificador de faster-whisper 1.2.1 con PyAV 19 no admite metadata_errors; la comprobación final utiliza el decodificador compatible que ya incorpora VICTOR para archivos y PCM para micrófono. No se degradaron las dependencias de audio en uso.
- La elegibilidad de ChatGPT, los permisos reales de Google, el acceso de la red del colegio y las restricciones de ejecución de esa PC no se pudieron comprobar aquí. La app permite conectar/probar y muestra errores en español.

## Última revisión — WhatsApp Web visible, paleta y recientes

- **Cuatro pruebas WhatsApp aprobadas en 14,757 s**: navegación/tema/cierre, página oficial dentro de HWND hijo visible con perfil conservado, rechazo de URL inicial ajena y fixture con recent→chat mediante ratón confiable del navegador. La app ya no presenta editor/historial nativos de WhatsApp ni puede quedarse en su estado «Abriendo conversación».
- **Trece pruebas de regresión aprobadas en 14,209 s**: estado de WhatsApp, BackgroundGUI, EmbeddedGuiTests y AudioLevels; no se ejecutó toda la suite.
- Fixture comprueba contacto con emoji, preview que contiene un número legítimo separado de su badge, temas oscuro/claro por colores CSS calculados, recepción con Inicio visible, contador independiente y ausencia de envío del mensaje al núcleo IA. Página de prueba no vinculada a una cuenta real.
- Capturas inspeccionadas: recientes claros/oscuros y WhatsApp oficial en vinculación, con fondos Grafito, texto contrastado y QR intacto. Variables WDS actuales revisadas en la página real para adaptar burbujas, compositor, superficies y enlaces. Perfil temporal; no se usó la sesión personal para enviar mensajes.
- Fuentes C# de producción y de fixture separados por WHATSAPP_TEST; producción usa WhatsAppWebHost.exe. Archivos Python compilados. Perfil vinculado, claves, OAuth y preferencias del propietario conservados.

Pendiente con cuenta real: corroborar toda la apariencia de chats/menús autenticados. La interacción usa los controles originales de WhatsApp; los previews de Inicio siguen dependiendo de su estructura DOM.

## Última revisión — interfaz nativa y tarjeta de mensajes recientes

- **17 pruebas aprobadas en 28,597 s**: cuatro casos WhatsAppEmbed, cuatro de estado nativo, BackgroundGUI, EmbeddedGuiTests y AudioLevels. Se preserva selección/reproductor Spotify y cierre de la aplicación con la sesión WhatsApp.
- Integración con Chromium/WebView2 real y fixture local: abre destinatario desde Inicio, muestra conversación, envía texto con tildes/salto de línea/emoji mediante controles Qt y comprueba una nueva burbuja saliente; conserva solicitud duplicada sin enviar dos veces; recibe mensajes con Inicio visible y actualiza su tarjeta; abre un contacto sincronizado; cambia al tema claro. Los contenidos recibidos con HTML/instrucciones no llaman al núcleo ni ejecutan herramientas.
- Pruebas del estado nativo: confirmación tardía conserva borradores nuevos/de otros contactos, fallo mantiene borrador sin inventar mensaje, resultados filtrados no reemplazan recientes, desvinculación borra datos de la vista y deshabilita envío, desajuste de conversación deshabilita el editor.
- Se verificó el QR de WhatsApp real dentro del panel nativo, con perfil temporal sin vincular. HWND de sesión es hijo de un viewport fuera del panel visible; no aparece la página de WhatsApp como interfaz. Perfil conservado al reconectar y cierre de proceso comprobados. No se enviaron mensajes a personas reales ni se leyó la agenda personal durante la verificación.
- Inspección visual de interfaz nativa y tarjeta de Inicio a 1640×950 y 1366×768. Vista compacta incorpora desplazamiento de columna derecha. Las capturas contienen exclusivamente datos ficticios de pruebas.
- Compilación de seis archivos Python y del host C# de producción. El fixture solo está habilitado en un host separado compilado con WHATSAPP_TEST; la aplicación normal utiliza WhatsAppNativeHost.exe.

Pendiente con cuenta real: contactos/historial sincronizados y envío/recepción con el teléfono vinculado. La adaptación usa el DOM renderizado de WhatsApp; un cambio de estructura del sitio puede necesitar ajustar selectores. Esta vista envía texto y muestra marcadores de mensajes multimedia.

## Última revisión — búsqueda por artista y WhatsApp

- **33 pruebas aprobadas en 6,006 s**: nuevas regresiones del título Bastardo y sus colaboradores, búsqueda por artista, errores de dictado, títulos que contienen «de», canciones no disponibles, no reproducir un título ajeno, selección de voz, comandos directos y chat/artista.
- **20 adicionales aprobadas** de catálogo, ApproximateMusic, BackgroundGUI y niveles de audio; la invocación incluyó por error un nombre de clase inexistente (`EmbeddedGUI`) y terminó con un error de carga, no una regresión. Invocación corregida: **EmbeddedGuiTests, una prueba aprobada en 10,460 s**, con Spotify nativo y cierre.
- **Tres pruebas WhatsApp aprobadas en 9,711 s**: pestaña y rutas de Conexiones/tema/cierre; página real dentro de un HWND hijo Qt, navegación sin duplicar proceso, reconexión conservando perfil y cierre; rechazo de URL inicial ajena o sin HTTPS. Perfil temporal, sin cuenta vinculada ni envío de mensajes.
- Comprobación real de Spotify en modo lectura: `SpotifyManager.play('Bastardo de Pablo Chil-E')` con la función final de reproducción sustituida encontró **Bastardo (feat. Ñengo Flow & Jere Klein)** y los tres artistas oficiales; similitud 0,987. No se cambió la canción del propietario.
- Vista real de WhatsApp cargó `https://web.whatsapp.com`, título WhatsApp, documento completo y QR visible. Captura de la página inspeccionada visualmente. No se comprobó sincronización de una agenda real ni intercambio de mensajes: necesita vincular el teléfono del propietario desde la nueva pestaña.
- Compilación del nuevo host C# x64 y de siete archivos Python, salida 0. Se conservan el WebView2 Runtime instalado y las DLL oficiales anteriores, sin alterar SpotifyHost.exe.

Fuentes: [filtros track/artist](https://developer.spotify.com/documentation/web-api/reference/search), [WhatsApp en ordenador](https://www.whatsapp.com/download/desktop), [contactos en dispositivos vinculados](https://faq.whatsapp.com/1191526044909364/?locale=en_US).

## Revisión actual — ruido, eco y reconocimiento

- **117 pruebas dirigidas aprobadas en 57,091 s**: voice_pipeline, voice_interrupt, openai_voice, ui_repairs.AudioLevels, wake_conversation, v2_voice, voice_and_credentials, music_background, radio_ducking, dos casos de v5, spotify_voice_commands, spotify_embed, service_update y chat_and_artist. No equivale a toda la suite.
- **Una prueba GUI adicional aprobada en 2,157 s**: el diagnóstico conserva el texto reconocido, muestra los ajustes acústicos y no envía ninguna herramienta al núcleo; cierre limpio. Compilación de 19 archivos modificados, salida 0; `pip check` sin dependencias rotas.
- Regresiones cubren captura persistente, conservación del inicio de respuesta, conversión de tasas nativas, desbordamientos, audio obsoleto, desconexión, cambio del micrófono predeterminado, activación Unicode y por dirección explícita, cancelación de resultados, idioma/modelo y diagnóstico sin órdenes. El final de audio se comprobó con un proceso hijo real y reproducción sustituida.
- Pruebas de DSP usan WebRTC nativo y Whisper base real con señales sintéticas. Ruido estacionario: aproximadamente **11,97 dB** de reducción después de adaptación; eco con retardos sintéticos de 40/100 ms: aproximadamente **22,28 dB**. Son resultados del ensayo, no garantías para otra habitación. En la muestra de doble voz, el filtro corrigió «espotita» a «Spotify»; no corrigió todos los nombres. Silero rechazó 600/600 ventanas de ruido gaussiano fuerte.
- Se detectó y corrigió que el antiguo prompt explicativo de Whisper podía reaparecer como palabras reconocidas. Se detectó también la resolución de unos 15,625 ms de `monotonic` en este Python/Windows, que permitía reproducir fragmentos previos como si fueran nuevos; la captura usa ahora el reloj preciso `perf_counter`.
- Comprobación local de WASAPI: referencia abrió y cerró correctamente; sin señal de salida presente, cero fragmentos. Enumeración de micrófono predeterminado correcta. No se grabó el micrófono físico, no se llamó una API de transcripción ni se alteró Spotify durante estos ensayos.
- Pendiente de validación con el propietario: voz real, ruido/eco de su habitación, audífonos/altavoces y funcionamiento durante juegos. Reiniciar `iniciar.bat` y usar **Ajustes → Voz → Probar micrófono sin ejecutar órdenes**. AEC toma la salida predeterminada de Windows; no elimina por completo reverberación ni voces ajenas.

Fuentes: [WebRTC AEC3 y NS](https://github.com/strands-labs/pywebrtc-audio), [WASAPI loopback](https://github.com/s0d3s/PyAudioWPatch), [Silero e integración Whisper](https://github.com/SYSTRAN/faster-whisper), [callback de captura](https://python-sounddevice.readthedocs.io/en/latest/api/streams.html).

Las verificaciones siguientes conservan el historial de revisiones anteriores.

## 11/10/2026 — Interrumpir la voz y mantener baja la música al esperar

- **70 pruebas dirigidas aprobadas en 34,989 s**: interrupción, radio_ducking, wake_conversation, v2_voice, spotify_voice_commands, service_update, spotify_catalog, music_background, ui_repairs.AudioLevels y v5.test_missing_wake_guidance. Después se añadieron dos regresiones de actividad durante captura y ASR local con proveedor OpenAI: **10 pruebas de interrupción aprobadas en 4,840 s**. **34 adicionales aprobadas en 22,299 s**: OpenAI, voz/credenciales, Spotify integrado y chat/artista. Compilación de once archivos afectados: salida 0. No se ejecutó toda la suite.
- **Pase final afectado: 18 pruebas aprobadas en 18,966 s** (`test_radio_ducking` y `test_voice_interrupt`), tras añadir el contrato del ACK en el servidor loopback real. Proceso padre/hijo Python real, síntesis/reproducción sustituidas: cortar una locución y saludar de nuevo conserva un único lease musical. La música no se libera al acabar el saludo ni durante una espera de prueba. Finalizar la espera libera el lease; cerrar con la espera activa también lo libera. Continúan los controles de pausa/cancelación/rampas del pase anterior. El loopback transmite un ACK ducked=false cuando no hay música activa para no guardar un lease vacío.
- Captura sounddevice simulada con callback en un hilo durante inferencia: ventanas solapadas de 1,2–3,2 s, buffer acotado, frases sin nombre y frases semejantes a TTS rechazadas. Solo devuelve VICTOR aunque la transcripción contenga más texto; nada de ese fragmento se entrega como orden. Activación durante una respuesta y durante un saludo reemplaza el turno anterior; una orden antigua de correo esperando el saludo no llega al núcleo. Prueba del controlador GUI con objetos simulados verifica cancelación y saludo sin liberar el volumen.
- Reloj controlado: saludo → 4 s de silencio conserva escucha → 9 s libera una vez → frase posterior sin VICTOR ignorada. PCM de voz durante una petición prolonga el plazo de silencio. Una petición consume la activación y devuelve el siguiente turno al nombre. ASR wake_only usa Whisper con beam=3, sin prompt de nombres y sin llamar al servicio OpenAI aunque esté seleccionado para las peticiones.
- **Whisper real, archivos sintéticos guardados**: modo local wake_only reconoce «Victor» en wake-luis.mp3 y «¿En qué te ayudo? Canción, café y español.» en greeting-luis.mp3. Evidencia `work/voice_update/interrupt-local-probe.json` en el workspace Codex. No se genera audio nuevo ni se reproduce en los altavoces del propietario durante la prueba.
- No se cambiaron claves, OAuth, motor/proveedor elegido ni preferencias del usuario; no se enviaron órdenes a Spotify real. **Pendiente físico:** interrumpir con micrófono/altavoces, latencia durante juego y recuperación audible tras silencio. El filtro de similitud textual reduce autoactivaciones pero no implementa cancelación acústica completa del eco. Función de interrupción en modo Continua con modelo Whisper local preparado. Reiniciar iniciar.bat.

## 11/10/2026 — Volumen de locutor, una petición por activación y pausa directa

- **62 pruebas dirigidas aprobadas en 31,499 s**: `tests.test_radio_ducking`, `test_wake_conversation`, `test_v2_voice`, `test_spotify_voice_commands`, `test_service_update`, `test_spotify_catalog`, `test_music_background`, `test_ui_repairs.AudioLevels` y `test_v5.V5.test_missing_wake_guidance`. Compilación de catorce archivos Python afectados: salida 0. No se ejecutó toda la suite.
- JavaScript real del reproductor con SDK simulado y reloj real: bajada progresiva durante 2,5 s con más de veinte pasos, límite de salto por paso, subida al volumen anterior, nivel inferior a 10 % sin aumento, cambio manual durante voz respetado, canción pausada sin atenuación y cancelación durante fade restaurando el nivel. Cancelación mientras getCurrentState aún espera no inicia una bajada tardía. Script completo con polling SDK: la pausa recibe ACK en menos de 650 ms mientras el fundido de 2,5 s todavía no ha terminado. Es una medida de fixture, no una promesa para la red o el micrófono real.
- Pipe real padre/hijo Python: se reemplazan solo síntesis y reproducción; el worker real espera el ACK antes de emitir PCM. Cancelar mientras espera la bajada no reproduce audio, libera la espera y restaura el lease. Se conserva comprobación Unicode y se controla el cierre de stdin si el hijo ya terminó. SDK desconectado no solicita fundido; errores al iniciar y al hablar siempre solicitan restauración.
- Núcleo real con función Spotify simulada y generación IA configurada para fallar si se invoca: cuatro variantes de pausa ejecutan exclusivamente spotify_pause. Contexto identifica VICTOR.IA y distingue proveedor como motor. Palabra VICTOR aislada no se envía al modelo. Continua ignora conversación ambiental antes y después de una petición, saluda al reactivar y admite una orden; Manual acepta petición sin nombre. Pruebas de arranque/minimización/modos y cierre GUI aprobadas.
- Se conservaron archivos de credenciales y preferencias reales; no se enviaron órdenes a Spotify ni se capturó el micrófono ni se reprodujo voz en los altavoces del propietario durante esta entrega. El fundido se implementa para el reproductor Spotify integrado, no para audio ajeno a VICTOR. **Pendiente físico:** decir VICTOR desde otra aplicación, escuchar saludo con música atenuada, dar una orden de pausa, comprobar recuperación y repetir activación después de la petición. Reiniciar con iniciar.bat para cargar los cambios.

Las comprobaciones anteriores se conservan como historial. El comportamiento actual reemplaza la ventana de varias peticiones por una petición por activación.

## 11/10/2026 — Activación en dos pasos, codificación de voz y Gemini

- **35 pruebas dirigidas aprobadas en 5,579 s**: tests.test_wake_conversation, test_v2_voice, test_spotify_voice_commands, test_gemini_errors, test_ui_repairs.AudioLevels y variantes/límites/aviso de activación de test_v5, más confirmación local de test_v4. Comprueban nombre solo y orden inline, saludo antes de capturar/enviar, pausa durante saludo, conversación sin foco, vuelta a reposo al caducar, envío al núcleo, controles con estado observado, Unicode en un proceso Python real con stdin cp1252, lectura del pipe y señal de finalización, no transcripción de la propia respuesta, reintento 503 hasta éxito, tope/presupuesto/cancelación y no repetición de streams/errores de cuota o clave. Una prueba GUI + VictorCore de correo lee destinatario/asunto/cuerpo, arma la escucha sin botón, rechaza «confirmar» para riesgo alto y exige «ejecutar»; solo entonces llama una función Mock, sin enviar correo real. No arma remoto ni revisiones que tendría que truncar.
- **31 pruebas aprobadas en 16,306 s**: tests.test_music_background, test_voice_and_credentials y test_openai_voice. Incluyen GUI minimizada/inicio automático/pausa/modos, autoplay WebView2 con WAV de ceros, reglas musicales/radio, almacenamiento DPAPI, controles de ajustes y ASR OpenAI con SDK simulado.
- **Comprobación real breve de Gemini**: petición «Responde solamente OK», sin herramientas ni historial ni datos personales, con la clave/modelo ya configurados; respuesta completada. Se imprimió solo estado, nunca clave ni cuerpo HTTP. Los registros previos contienen varios `ServerError status=503` y respuestas correctas: el problema del pantallazo es indisponibilidad intermitente de Google, no una clave que siempre falla. Fuente: https://ai.google.dev/gemini-api/docs/troubleshooting.
- **Audio real sintetizado, entrada sintética**: es-EC-LuisNeural produjo MP3 de «Víctor.» (11.232 bytes) y «¿En qué te ayudo? Canción, café y español.» (29.232 bytes). Whisper base local reconoció `VICTOR` y la segunda frase con tildes/ñ conservadas. Evidencia `work/voice_update/wake-probe.json` en el workspace Codex y script `work/probe_wake_greeting.py`. No se reproduce este audio en el equipo del propietario ni se accede a su micrófono.
- **Limitación de la comprobación GUI general**: al ampliar a tests.test_ui_repairs entero, la prueba de caducidad del aviso recibía un callback tardío de Spotify no configurado. Aislando ese catálogo apareció además desbordamiento horizontal en la página Spotify a 420 px. Se restauró ese fixture y no se declara aprobada esa prueba general; las siete pruebas dirigidas de audio del módulo sí aprobaron. Estos resultados no acreditan funcionamiento del micrófono físico, del sonido audible ni de una sesión de juego.

## 11/10/2026 — Similitud musical, radio y modo de juego

- **41 pruebas aprobadas en 27,456 s**: tests.test_music_background, test_spotify_embed.VoiceSelection, test_v2_voice, test_spotify_voice_commands, test_chat_and_artist y test_voice_and_credentials.
- **25 aprobadas en 8,670 s**: test_spotify_catalog, test_service_update y test_openai_voice. Las primeras comprobaciones JS fallaron porque los mocks DOM no definían location; se añadió el objeto realista y Promise de activateElement, y se verificaron tanto conexión manual como handsfree. No se ocultó un fallo de aplicación mediante fallback de location.
- Pase final tras reducir intervalo de captura, arrancar el host desde ajustes y probarlo minimizado: **16 aprobadas en 17,545 s**, test_music_background + test_v2_voice + test_spotify_embed.EmbeddedGuiTests. Compilación de catorce archivos Python: salida 0.
- Catálogo simulado: Sex Playlist 1 → SEXPLAYLIST1; tuki tuk/Chris R → TUKI TUKI/Kris R.; interludio/Omar Cobbord → INTERLUDIO/Omar Courtz. Exacta vence a aproximada/popular, puntuación vence al primer resultado, consulta título tras artista mal escrito, no reproducir pista/creditos ajenos ni pistas no disponibles. No se llama a LLM para estas órdenes.
- Probabilidades exhaustivas sobre los cien posibles valores aleatorios: frase A=20, frase B=20, sin frase=60. GUI verifica ACK solo «Solicitud enviada», observación de otra pista no habla, observación correcta habla una vez; estado previo a answer conserva título; fallos no llevan coletilla.
- Inicio automático GUI con VoiceInput.start simulado sin micrófono: inicia minimizada, respeta pausa, espera worker anterior y cambios manual/continua. Worker simulado requiere VICTOR en cada orden en segundo plano aunque exista ventana de conversación; ruido/silencio no repiten avisos.
- Host WebView2 real: entorno del proceso usa autoplay-policy solo en handsfree, URL activa autoconexión, DOM SDK válido; play() de WAV silencioso de 16 kHz se resuelve con la ventana minimizada y sin clic. Es PCM cero, sin canción real ni comprobación audible. SDK Node simulado comprueba activateElement/connect automáticos, comandos, volumen, desconexión y bandera background hacia servidor.
- Servidor loopback real con cliente Spotify simulado: ready/background registra dispositivo sin transferir ni iniciar música; ready manual conserva transferencia anterior. Cuenta del propietario no se consultó ni recibió órdenes de reproducción en esta entrega.
- Configuración real: Whisper/base local disponible, cuenta Spotify guardada; habilitadas continua/inicio automático/salida de voz, con copia previa. **Pendiente:** micrófono, palabra de activación, audio audible y rendimiento durante un juego real del propietario; la sesión aislada no permite esas pruebas físicas.
- Fuente de implementación: [SDK Spotify](https://developer.spotify.com/documentation/web-playback-sdk/reference) y [flags WebView2](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/webview-features-flags). Microsoft clasifica los flags como herramientas de desarrollo sin garantía de estabilidad para distribución; el cambio se valida en el runtime instalado y se conserva Habilitar sonido para recuperar autoplay bloqueado.

## 11/10/2026 — Motor OpenAI para reconocer voz

- `python -m unittest tests.test_openai_voice tests.test_voice_and_credentials tests.test_v2_voice tests.test_spotify_voice_commands tests.test_chat_and_artist -q`: **33 aprobadas en 15,337 s**. Compilación de ocho archivos Python con salida 0. Un pase adicional de SettingsGUI genera capturas y termina limpio: **1 aprobada en 6,247 s**.
- SDK AsyncOpenAI instalado con MockTransport real: multipart hacia `/v1/audio/transcriptions`, modelo gpt-transcribe, WAV identificado por nombre/MIME, pistas keywords/languages y JSON de texto. Archivo mono 16 kHz/int16 validado leyendo cabecera/muestras; límites y PyAV real sobre WAV sintético comprobados. GPT-4o usa language ISO y no recibe parámetros exclusivos del modelo nuevo.
- Clave solo OpenAI aun conversando con Gemini; config sin clave. Falta de clave falla antes de abrir micrófono. Errores 401/403/404/429/503 y timeout presentan mensajes sin contenido HTTP y no emiten voice_text. Cancelación durante petición aborta la tarea en menos de 1 s, cierra el cliente y no permite resultados tardíos.
- Captura simulada comprueba PCM hacia Transcriber con OpenAI/Whisper y la ruta Google separada. La frase exacta de la captura humana «Reproduce la mina de Chris r» se corrige y llega al parser como spotify_play(query='GAMINA de Kris R'); otros artistas no se sustituyen. No hay reproducción real en esta comprobación.
- GUI Qt: selector OpenAI/modelo guardados y recargados, todos los DEFAULTS expuestos, estado de clave sin revelar su valor, proveedor de conversación intacto y motor visible en la sesión de voz. Capturas amplias/estrechas inspeccionadas en `work/voice_update` del workspace Codex; página sin desplazamiento horizontal, con desplazamiento vertical para el resto de controles.
- Estado real: Google seguía seleccionado y las correcciones/vocabulario estaban vacíos. Se restauraron solo las preferencias musicales confirmadas, guardando copia previa; la instalación no tiene clave OpenAI, por lo que aún conserva Google como motor activo. Para usar la integración: reiniciar, guardar clave OpenAI en Ajustes → IA y seleccionar openai/gpt-transcribe en Ajustes → Voz → Guardar cambios.
- **Límite de verificación:** no se hizo una transcripción contra el servicio real ni se capturó la voz del propietario. Las pruebas usan audio y claves sintéticos, sin consumo de API. La integración usa la API pública documentada de OpenAI; no establece qué motor interno exacto emplea ChatGPT ni garantiza transcripción perfecta.

## 11/10/2026 — Reconocimiento, claves API, síntesis y presentación

- 56 pruebas dirigidas aprobadas (17,302 s): test_voice_and_credentials, test_v2_voice, test_gemini_errors, test_adapters, test_ui_repairs.AudioLevels, test_spotify_voice_commands, test_victor.StorageTests, test_chat_and_artist, test_spotify_embed.VoiceSelection y test_gui_qt. Tras las últimas ampliaciones del parser musical y las tablas habladas, las **31 pruebas afectadas volvieron a pasar en 6,931 s**. Compilación final de los 23 archivos Python modificados/nuevos: salida 0.
- Claves exclusivamente sintéticas: DPAPI real guarda/recupera sin texto plano; prioridad personal/entorno y borrado por proveedor; fallo de cifrado/archivo dañado preserva bytes anteriores; cada SDK recibe la clave personal sin variables de entorno; fallback local no recibe la clave del proveedor anterior. No se llamaron APIs de IA con claves personales para esta comprobación.
- GUI real Qt: guardar/quitar clave vacía los campos ocultos; estado del proveedor seleccionado; prueba de voz sin guardar; ajustes responsive sin barra horizontal. Capturas en work/voice_update del workspace Codex.
- Síntesis real Edge: Jorge y Luis disponibles; MP3 Jorge generado (61.056 bytes). Grabación sintética Luis «Victoria, reproduce Gamina de Kris R en Spotify»: configuración anterior reconoció «Victoria, reproduce la mina de crezán en Spotify»; pistas/beam nuevo reconocieron «Victoria, reproduce GAMINA de Kris R N Spotify». La normalización de la preposición convierte «N Spotify» en «en Spotify» y el parser obtiene spotify_play(query='GAMINA de Kris R'). Es una prueba sintética, no la voz real del usuario.
- TTS: signos de formato no llegan al motor; decimales, horas, preguntas y contenido entre paréntesis conservados. Voz SAPI inglesa no se selecciona por tener «Desktop» en el nombre. Archivo de audio generado disponible en work/voice_update/jorge-preview.mp3; sin reproducirlo en altavoces físicos.
- Markdown: formato de caracteres, listas, tabla de tres columnas, enlaces seleccionables y fuentes deduplicadas comprobados en QTextDocument; actualización por tokens; temas oscuro/claro y estrecho con capturas de widgets en work/chat_update. Bloqueados HTML/imágenes externas y protocolos file/javascript al pulsar enlaces.
- Spotify por artista: fixtures eligen solo pistas disponibles con créditos coincidentes, no repiten la última si hay alternativas y fallan sin reproducir si el artista no coincide. Peticiones incompletas piden artista; consultas concretas y títulos entrecomillados conservan coincidencia exacta. No se envió una orden de reproducción a la cuenta real durante estos cambios.
- Limitaciones: no hay acceso al micrófono/altavoces del escritorio físico desde esta sesión. Una prueba GUI antigua de maximizar ventana falló en el escritorio aislado y la limpieza temporal de WebView2; esa prueba de ventanas no confirma ni invalida los cambios de voz/credenciales. Las pruebas nuevas de ajustes y chat terminaron con cierre limpio y las dirigidas de Qt GUI pasaron.

## 11/10/2026 — Orden real de GAMINA y corrección de «Preparando resultado»

- Historial leído solo para diagnóstico: la respuesta del modelo contenía un supuesto wrapper Spotify y una frase añadida. No era JSON válido ni correspondía a una ejecución de spotify_play. La orden en infinitivo con punto final pasaba a IA; ahora el GUI la dirige al registro real.
- `python -m unittest tests.test_spotify_voice_commands tests.test_spotify_embed tests.test_spotify_catalog tests.test_service_update tests.test_v5.V5.test_gui_prediction_rejection_debounce_and_presentation -q`: **27 aprobadas en 23,476 s**. Nuevas regresiones de voz, puntuación, título/artista, respuesta ficticia, SDK/catalogo/Qt y compatibilidad de controles. Compilación de los seis archivos Python modificados: salida 0. Véase el pase adicional tras el último guard debajo.
- Pase final adicional tras conservar los comprobantes de herramientas Spotify realmente ejecutadas y añadir el fallo de coincidencia: `python -m unittest tests.test_spotify_voice_commands tests.test_spotify_embed -q`, **11 aprobadas en 10,048 s**. Incluye ejecución real del core con herramienta simulada, éxito/fallo sin llamar a IA, GUI/WebView2, búsqueda por artista, redimensionado, tarjetas y cierre. Compilación final: salida 0.
- Prueba real autorizada tras la corrección humana **GAMINA de Kris R**: búsqueda y start_playback al dispositivo VICTOR activo. current_playback confirmó la canción solicitada y is_playing=true en ese mismo dispositivo. No se usó Spotify desktop como destino ni se abrió otra ventana. No hay captura de audio físico; esta comprobación es del estado Spotify.
- Para repetir desde la versión corregida: reinicia VICTOR y di «Victoria, reproduce GAMINA de Kris R en Spotify». Debe ejecutar spotify_play y mostrar la carátula/metadatos. Si la transcripción sigue diciendo «la mena», no se debe reproducir otra canción ni mostrar una confirmación ficticia; corrige título/artista. «Preparando resultado» ya no queda como respuesta final de un wrapper Spotify malformado.

## 11/10/2026 — Panel de carátula restaurado y tema Spotify unificado

**22 pruebas dirigidas aprobadas en 22,488 s**, después del ajuste final de tamaños mínimos, y compilación de los siete archivos Python afectados con salida 0.

Comando: `python -m unittest tests.test_spotify_embed tests.test_spotify_catalog tests.test_service_update tests.test_v5.V5.test_gui_prediction_rejection_debounce_and_presentation -q`.

- Panel Qt original restaurado arriba a la izquierda: carátula/título/artistas, transportes a su derecha, volumen con debounce, posición y mini reproductor. La prueba GUI verifica pausa optimista/reversión al fallar, envío único de volumen, conservación de intención ante snapshots antiguos y seek exacto. Un único host WebView2, reconexión y cierre limpio siguen comprobados.
- Paleta obtenida del DOM real: fondo oscuro `rgb(21, 23, 28)`, superficie `rgb(29, 32, 39)`; claro `rgb(246, 247, 250)` y `rgb(255, 255, 255)`. Fuente base 13 px. Cambio Dark/Light sincronizado; transportes web duplicados ocultos, elementos del SDK conservados. Buscador, biblioteca y filtros siguen disponibles.
- Prueba de redimensionado 1600/420: panel a la izquierda en amplio, apilado en estrecho, barra horizontal de Qt en cero y DOM sin desbordamiento. La página tiene desplazamiento vertical para conservar los controles y los resultados, sin recortarlos. Recalculados los mínimos de botones que podían conservar medidas de la ventana amplia.
- Cuenta real consultada para biblioteca/búsqueda únicamente. Inspección visual de grab de widgets Qt y CapturePreview WebView2 en oscuro/claro y estrecho; composición de ambas capturas en `work/spotify_graphite` del workspace de Codex. La carátula muestra metadatos de catálogo con estado en pausa inyectado para revisión. No se activó audio ni se alteró la reproducción del propietario; la comprobación audible anterior sigue pendiente.

Para verlo: cierra y vuelve a abrir VICTOR mediante iniciar.bat. El panel «Reproduciendo ahora» debe estar arriba a la izquierda y el catálogo integrado a su derecha. En una ventana estrecha, desplázate hacia abajo para la biblioteca/búsqueda. Los pasos anteriores de Activar audio, selección de canciones y playlists siguen aplicando.

## 11/10/2026 — Reproductor dentro de VICTOR y canción exacta por voz

**Resultado final: 27 pruebas dirigidas aprobadas en 23,015 s**, después de todos los ajustes, y compileall con salida 0. Al comando de 22 pruebas indicado abajo se añadieron `tests.test_integrations.Integrations.test_spotify_play_real_state_contract`, las tres regresiones Spotify de `DesignLogic` (control rápido, dispositivo configurado, validación/confirmaciones) y `tests.test_v4.V4.test_volume_only_risk_change_and_resume`. La prueba GUI final también comprueba que un fallo Spotify vuelve a mostrar el error normal, y el cierre/reinicio cancela controles pendientes. No se ejecutó toda la suite del proyecto.

- `python -m unittest tests.test_spotify_embed tests.test_spotify_catalog tests.test_service_update tests.test_v5.V5.test_gui_prediction_rejection_debounce_and_presentation -q`: **22 aprobadas en 22,082 s**. Cinco casos de selección por voz (GAMINA frente al primer TUKI TUKI, acentos/artista, búsqueda por título, ausencia de coincidencia y contenido no disponible). Se conservan contratos de biblioteca, URI/posición/paginación, validaciones loopback, comandos SDK/desconexión, Google y mini reproductor. Pruebas ajustadas a la retirada de los controles Qt duplicados.
- `python -m unittest tests.test_spotify_embed.EmbeddedGuiTests -q`: **1 aprobada en 9,004 s**, después del último ajuste móvil. Host real de WebView2, estilo WS_CHILD/padre Qt, una sola vista, DOM real con biblioteca/buscador/progreso, ningún navegador externo, reconexión, cierre y tarjetas sin JSON técnico; respuesta IA normal restaurada. Anchuras 1600/420: buscador y Activar audio dentro del encabezado y sin desbordamiento horizontal.
- `powershell -File victor/gui/webview2/build.ps1`: host C# compilado con éxito. `python -m compileall -q main.py victor tests`: salida 0. No se repitió la suite completa ajena al cambio.
- Cuenta real, solo consultas: 48 resultados para GAMINA y selección correcta GAMINA — Kris R., Los Money Makers. start_playback interceptado en la prueba de selección. Vista integrada real: ancho 1300, scrollWidth 1300; estrecha: 276/276. Carátulas y tarjetas revisadas mediante CapturePreview de WebView2 y grab de widgets Qt, sin captura física del escritorio.
- WebView2 Runtime respondió **supported** a requestMediaKeySystemAccess(com.widevine.alpha) con audio/mp4 AAC. Esto verifica capacidad DRM, **no** una licencia Spotify ni reproducción audible de punta a punta. Audio, micrófono y funcionamiento continuo/minimizado quedan pendientes del usuario. Las tarjetas de la inspección muestran solicitud pendiente, sin afirmar que se escuchó música.

### Pasos exactos para el propietario

1. Cierra VICTOR y la antigua ventana «VICTOR · Spotify». Ejecuta iniciar.bat desde <CARPETA_LOCAL>
2. Abre Conexiones → Spotify. Debes ver un único reproductor completo dentro de VICTOR; no debe abrirse otra ventana. Si el aviso indica que falta el runtime, instala [Microsoft Edge WebView2 Evergreen](https://developer.microsoft.com/microsoft-edge/webview2/) y pulsa Reconectar. Esta PC ya tiene el runtime.
3. Pulsa Activar audio una vez. Requiere Spotify Premium y permisos streaming/user-read-email. Si faltan, pulsa Conectar Spotify para OAuth y vuelve a Activar audio. No necesitas reinstalar paquetes ni abrir Spotify desktop.
4. Busca GAMINA. Pulsa el título GAMINA — Kris R., Los Money Makers y confirma que escuchas esa canción, no TUKI TUKI. Prueba también un resultado diferente, siguiente/anterior, pausa, volumen y posición.
5. Abre una playlist: debe mostrar sus canciones sin empezar a sonar la primera. Elige una pista intermedia. Comprueba filtros, más resultados y podcasts/episodios disponibles para tu cuenta.
6. Cambia a Voz y di «Victoria, reproduce gamina en Spotify» (o tu palabra de activación configurada). Comprueba audio y tarjeta con título/artista/carátula, sin «Orden enviada», «Aceptada por API» ni JSON. Si hay otro tema con el mismo nombre, añade el artista.
7. Cambia entre Inicio, Voz y Conexiones, y minimiza/restaura. La música debe continuar; no debe crearse otro reproductor. Cierra VICTOR: el audio y su proceso interno deben terminar. Si falla la conexión, usa Reconectar dentro de la app y vuelve a Activar audio.

Las verificaciones inferiores son históricas; donde mencionan una ventana externa, quedan sustituidas por esta integración.


## 11/10/2026 — Spotify: navegación, búsqueda y diseño web

1. `python -m unittest tests.test_spotify_catalog tests.test_service_update tests.test_v5.V5.test_gui_prediction_rejection_debounce_and_presentation -q`: **17 aprobadas en 18,962 s**. Ocho pruebas nuevas cubren búsqueda sin reproducción, paginación, formato `track`/`item`, nulos/duplicados e índices originales, episodios/álbumes, pistas no disponibles, reproducción por URI y offset exactos, error 403 sin cuerpo sensible, rutas HTTP reales loopback con registro/validación y rechazo de herramientas arbitrarias, recursos locales, cierre del servidor, JavaScript ejecutado por Node (navegación/paginación/selección/respuestas obsoletas/URLs permitidas/progreso), GUI y ausencia de desbordamiento en 1600/420 px.
2. Regresiones existentes: puente SDK/ACK, desconexión, tarjetas Google/Spotify, scopes, controles SDK sin REST, predicción/reversión, volumen/debounce y cierre limpio. ACK con fixture 15,7 ms y callback visual 0,46 ms: **no son tiempos de reproducción audible ni latencia de Spotify**. Un pase previo descubrió 4 px de scroll horizontal en la ventana estrecha; fue corregido antes del pase final.
3. `python -m compileall -q main.py victor tests`: salida 0. Sin reinstalación ni cambios de core/security/theme/configuración/Gemini/control remoto. No se repitió la suite completa previamente aprobada.
4. API real, usando el OAuth ya existente sin mostrar tokens: búsqueda «GAMINA», 48 resultados (track, playlist, show, episode, album); cinco playlists; primera página de la primera playlist con 50 de 59 elementos y 50 URLs de carátula. Después, navegación real en navegador por la nueva página: **59/59 elementos cargados** y carátulas visibles, manteniendo «Sin reproducción» y sin pulsar Activar audio. Búsqueda real en esa página: 48 filas. No se enviaron órdenes de reproducción a la cuenta durante estas verificaciones.
5. Capturas revisadas en `<CARPETA_LOCAL>`: `web_playlist.png`, `web_search.png`, `app_1600.png`, `app_420.png`. Web con consultas reales. Qt con metadatos e imágenes de consultas reales inyectados en un perfil temporal para inspección; estado en pausa/volumen/posición inyectado, sin reproducción audible real. No se capturó ni controló el escritorio aislado.

### Prueba pendiente de audio en tu PC

1. Cierra VICTOR y la ventana web anterior, y vuelve a ejecutar `iniciar.bat`.
2. En Conexiones → Spotify, pulsa Actualizar playlists. Haz clic en una playlist: deben aparecer sus canciones sin cambiar lo que suena; espera a que termine la carga progresiva.
3. Activa el reproductor VICTOR y pulsa Activar audio en su ventana. Mantén ambas ventanas abiertas.
4. En la app, selecciona una canción intermedia de la playlist y pulsa Reproducir canción seleccionada (o doble clic). Verifica título y audio; siguiente debe seguir la cola de la colección según el modo shuffle de Spotify.
5. Busca «GAMINA» y elige un resultado distinto del primero. Buscar debe mostrar resultados sin cambiar el audio; doble clic reproduce la elección. Prueba filtros y Más resultados.
6. En la ventana web, abre la biblioteca o busca desde la barra superior. Abre una playlist/podcast/álbum; pulsa el título de la canción/episodio deseado. Verifica audio y controles inferiores. La compatibilidad audible de episodios y las restricciones de cada cuenta/contenido quedan pendientes, no se declaran aprobadas.
7. Prueba Volver, actualizar, pausa, siguiente, volumen y posición; la app debe seguir fluida. Un 403 al explorar playlists ajenas se explica como restricción de Spotify y ofrece abrirlas en su servicio.

## 11/10/2026 — Gemini: error real de modelo y saturación externa

1. SDK instalado `google-genai 1.75.0`, clave local cargada sin imprimirla. Petición real de streaming con todos los esquemas de herramientas: `gemini-2.5-flash` devolvió 404 NOT_FOUND. Google especificó que ese modelo ya no está disponible para usuarios nuevos y recomendó `gemini-3.8-flash`. Era un rechazo de modelo, no un diagnóstico de fallo de red.
2. El modelo recomendado devolvió 503 UNAVAILABLE en el primer intento y `OK` en el siguiente, mediante GeminiProvider real; cero herramientas solicitadas/ejecutadas. Se guardó ese modelo en la configuración existente y se recargó, verificando que las otras preferencias/modelos se conservaron.
3. Prueba final real por AIManager, configuración guardada y mensaje de saludo: 503 a los 26,09 s. El mensaje nuevo indica saturación temporal. No se afirma disponibilidad continua ni respuesta al saludo dentro de la GUI. Para probarla: cerrar VICTOR.IA, abrir `iniciar.bat`, seleccionar Gemini si corresponde y enviar «hola». Ante saturación, esperar y volver a intentar o configurar otro proveedor de respaldo con sus propias credenciales.
4. `python -m unittest tests.test_gemini_errors tests.test_adapters tests.test_victor.AITests -q`: **17 pruebas aprobadas en 2,600 s**. Incluyen excepciones reales del SDK con códigos 400/401/403/404/429/500/503, diagnóstico de modelo, no exposición de claves/cuerpos, códigos de otros SDK, respaldo, cancelación y adaptadores con streaming simulado. Estas pruebas unitarias no hacen llamadas de red.
5. `python -m compileall -q main.py victor tests`: salida 0. Sin reinstalaciones ni repetición de la suite completa previamente aprobada. No se cambió core.py, security.py, interfaz, Spotify ni control remoto.

## 11/10/2026 — Google, Spotify y modo sin confirmaciones

### Ejecutado realmente en este entorno

1. `python -m compileall -q main.py victor tests`: salida 0. No se reinstalaron dependencias.
2. Suite completa: **126 pruebas aprobadas en 64,172 s**. Un pase previo detectó un desbordamiento de 92 px en Diagnóstico; se corrigió el ancho obsoleto de la página al volver a mostrar sus layouts. La suite completa posterior pasó.
3. Tras los últimos ajustes de recepción de eventos SDK/herramientas por voz, volumen y auditoría: **9 pruebas dirigidas aprobadas en 13,709 s** (`test_service_update` y el caso de predicción/debounce de V5). Después del ajuste de desconexión del audio al perder el servidor: caso JavaScript aprobado en **0,452 s**, ejecutado por Node 24.18.0, sin instalar paquetes. Compilación final de Python aprobada.
4. Pruebas nuevas ejecutadas: fecha ISO/RFC y todo el día, remitente, tipo de archivo, selección de mayor resolución; metadatos Google con API simulada; política directa para LOW/MEDIUM/HIGH, registro de «Directa», origen revocado, cancelación, carpeta fuera de la lista y argumentos inválidos; scopes del SDK; controles locales sin llamar a REST; HTTP real loopback con token fixture, rechazo de Origin/capability inválidos, device ready, transferencia simulada, command/ACK una sola vez, validación de estado, offline y cierre del servidor; JavaScript real con DOM/SDK simulados, comandos next/volume, ACK, desconexión y botón reconectar. El ACK loopback fue 12,5 ms en el pase completo y 24,8 ms en el dirigido: **no es latencia de Spotify ni tiempo audible**.
5. Ventana Qt real abierta, navegada y cerrada limpiamente. Capturas de sus propios widgets en `<CARPETA_LOCAL>`: calendar.png, gmail.png, drive.png, spotify.png y spotify_narrow.png. Revisadas directamente. Datos de correo/eventos/playlist y la portada son **fixtures visuales**, no consultas a cuentas reales. Se detectó y corrigió el doble pintado de texto de QListWidget; las capturas corregidas muestran un solo título/subtítulo/resumen por fila. El producto conserva Inter, paleta, logos locales y orden − □ ×.
6. Configuración de la instalación real guardada y recargada: `action_confirmations=false`. No se imprimieron ni cambiaron claves; core.py, theme.py y los servicios de streaming táctil no fueron modificados. Los niveles de riesgo de las herramientas permanecen iguales; cambia el paso de diálogo según la preferencia explícita del propietario. Se conservan validación de origen, bloqueos y esquemas. Nuevos perfiles sin esta preferencia mantienen confirmaciones activadas.

Los errores de captura/conexión impresos por la suite proceden de mocks de errores inducidos. No se reintentó capturar el escritorio con MSS/ImageGrab ni controlar mouse/teclado físicos en CodexSandboxDesktop. Advertencias de deprecación de dependencias existentes no hicieron fallar los tests.

### Qué aún requiere tu PC y tu cuenta

- OAuth real con los nuevos scopes, Premium y permisos de Web Playback SDK en tu aplicación Spotify.
- DRM y reproducción audible en Edge/Chrome, salida de audio correcta, controles por voz y medición de latencia audible de volumen/siguiente/anterior. Eliminar el diálogo y usar comandos SDK locales reduce pasos en el código; **no confirma por sí mismo que tu red/cuenta responda casi instantáneamente**.
- El reproductor implementado abre una **ventana web propia de VICTOR**. No se embebió audio Spotify dentro del widget Qt ni se afirmó disponibilidad de Widevine en QtWebEngine. Esa parte literal de «dentro de mi app» permanece como límite explícito; la ventana web sí está programada para ser el dispositivo reproductor, independiente de Spotify desktop.
- Se enriquecieron los campos obtenidos de Google, pero las consultas con tu cuenta y enlaces a tus correos/archivos aún requieren prueba real. Las pruebas aquí usan respuestas simuladas.

### Pasos para probar el reproductor sin Spotify desktop

1. Cierra VICTOR y ejecuta `<CARPETA_LOCAL>` en tu escritorio. No ejecutes instalar.bat de nuevo.
2. En Spotify Dashboard, comprueba que tu aplicación tiene Web Playback SDK habilitado y que tu cuenta Premium está autorizada. Mantén la URI de retorno ya registrada en `.env`.
3. En **Conexiones → Spotify**, pulsa **Conectar Spotify** de nuevo; concede `streaming` y `user-read-email` junto con los permisos existentes. El token viejo puede carecer de streaming; el reproductor lo informa.
4. Pulsa **Activar reproductor VICTOR** y, en la ventana web, **Activar audio**. Espera «Conectado · Elige una canción en VICTOR». Ese clic es necesario por la política de audio del navegador.
5. Busca una canción o actualiza/selecciona una playlist en VICTOR. Cuando suene, cierra Spotify desktop: el audio debe seguir desde la ventana web. Mantén VICTOR y esa ventana abiertas. Comprueba título, artista y carátula reales en ambos lugares.
6. Arrastra el volumen, pulsa pausa/reanudar/anterior/siguiente y comprueba que no aparece Autorizar/EJECUTAR. La GUI cambia inmediatamente; el audio real depende de la confirmación del SDK. Anota la diferencia audible con un cronómetro si notas demora.
7. Cierra la ventana web: al perder su sesión debe dejar de mostrarse como dispositivo SDK activo. Para reconectar, pulsa Activar reproductor VICTOR y Activar audio de nuevo. Si cierras VICTOR, el servidor para y la página desconecta el SDK al detectar la pérdida; vuelve a abrir un reproductor nuevo después de reiniciar.
8. En Google, prueba Actualizar agenda, Actualizar correos y buscar Drive. Deben aparecer fechas legibles y tarjetas sin URLs/JSON duplicados; doble clic abre el elemento. Los enlaces Gmail usan la primera sesión de Gmail del navegador (`u/0`); si tienes varias cuentas abiertas, selecciona la cuenta conectada.

Las verificaciones históricas siguientes conservan sus resultados originales. Las instrucciones antiguas de confirmaciones aplican solo cuando vuelves a activar «Pedir confirmación»; el perfil actual ejecuta directamente las herramientas permitidas, conserva sus bloqueos y registra el modo de autorización.


## Referencia final confirmada — controles Windows

El propietario confirmó **− □ ×** de izquierda a derecha. Símbolos sin círculos, hitbox 44×30, contraste claro/oscuro y hover rojo en cerrar. Las transiciones ya verificadas se conservan. **2 pruebas afectadas aprobadas en 13,412 s** (WindowControls y QtGUI); orden y color del trazo comprobados, además de tarjetas/tamaños/transiciones/cierre. Compilación de app.py, widgets.py y test_window_controls.py: salida 0. Captura Qt del encabezado revisada directamente en `<CARPETA_LOCAL>`; helper abrió y cerró la ventana limpiamente. No se repitieron las demás pruebas ni se reinstalaron dependencias.

No se quitaron herramientas ni se modificó seguridad. Se comprobaron las definiciones de `open_application`/`open_url` (LOW) y la política existente: en nivel normal no piden confirmación; en Strict sí. La propuesta de ocultar paneles técnicos para una interfaz centrada en voz es una recomendación, no una eliminación implementada.

## Último ajuste — tarjetas y animaciones de ventana

- Causa del recorte reproducida: las tarjetas heredaban QSizePolicy.Fixed y la altura del QPushButton normal. Además, la adaptación de etiquetas eliminaba el indicador height-for-width. Corregidos ambos casos; alturas medidas: 80 px a 1920/1600, 103 px para «Abrir aplicación» a 420, con título/descripción completos y dentro de la tarjeta.
- Nueva prueba WindowControls aprobada en **8,470 s**, incluidos temas Dark/Light/Dark y tres anchos, clic funcional sin ejecutar Windows real, orden ×/□/−, capa de transición visible, geometría/opacidad cambiando a mitad de animación, no superposición, maximizado/restaurado/minimizado final y workers terminados al cerrar.
- **4 pruebas GUI afectadas existentes aprobadas, 19,788 s** (UIRepairs, QtGUI y DesignGUI). Solo se ejecutaron pruebas relacionadas; el total de 117 de la sección anterior corresponde al pase anterior, no se declara una nueva suite completa.
- Compilación final de `victor/gui` y los tests afectados: **salida 0**. Capturas Qt propias fuera del producto: `<CARPETA_LOCAL>`, `tiles_fixed_420.png`, `tiles_fixed_1600.png`. Se revisó directamente la imagen ancha: textos legibles y controles en el orden solicitado.
- Transiciones de 260 ms (minimizar/maximizar/restaurar) y 220 ms (cerrar), escala/desvanecimiento InOutCubic. Captura exclusivamente del widget Qt, sin MSS/ImageGrab; no se alteran datos ni workers durante la escala. La parada de tareas sigue siendo la original tras la transición de cierre. No es una reproducción del Genie nativo de macOS; es una transición fluida implementada en Windows/Qt.

## Correcciones gráficas del 11/10 — ejecutado y límites

- Compilación final `python -m compileall -q main.py victor tests`: **salida 0**, ejecutada después del último ajuste de producto. Sin reinstalar dependencias.
- **117 pruebas aprobadas, 48,476 s**, incluido `tests/test_ui_repairs.py` (8 nuevas). Después del ajuste final de lectura numérica/altura de proveedores, **4 pruebas GUI afectadas aprobadas, 17,833 s**: UIRepairs, DesignGUI y QtGUI. No se repitió la suite completa por este ajuste exclusivamente visual.
- Pruebas nuevas: RMS Int16/Int32/UInt8/Float, silencio/datos inválidos/NaN, QAudioBuffer real con PCM fixture, protocolo JSON limitado, niveles recibidos antes de terminar un proceso simulado, epoch cancelado/pipe cerrado, limpieza del worker, salida SAPI directa/render a archivo con engine simulado, RMS del micrófono con InputStream simulado, selección exclusiva, navegación por botones reales, avisos que expiran/interrumpen fade, controles minimizar/maximizar/restaurar y recorrido de las 21 vistas a 420 px.
- Se abrió la ventana Qt real y se tomaron capturas de sus propios widgets en 1600×900 y 420×760; no se capturó el escritorio. Todas las páginas sin scroll horizontal, aviso desaparecido y cierre limpio. Capturas revisadas: `<CARPETA_LOCAL>` (ia, spotify, telegram, remote, windows, voice, narrow_ia/voice/remote, wide_restored, light_ia). Los niveles 0,70 de micrófono y 0,65 de TTS de la revisión son **fixtures inyectadas**, no voz de una persona ni respuesta audible.
- Se conservan los colores/tema existentes; logos de proveedor sustituyen pictogramas genéricos y hay una sola pestaña seleccionada por fila. Conexiones muestra sus cuatro vistas sin depender del menú del encabezado. Los avisos duran 5,5 s + fade 240 ms y quedan disponibles en «Ver avisos recientes».
- Cambios GUI: app, panels, widgets, voice_panel y maintenance; cambios de audio: input, output y nuevo levels. No se modificaron core, security, theme, servicios remotos ni módulos Spotify. Las trazas de captura/red de la suite son errores inducidos por mocks, no nuevos intentos de usar MSS/ImageGrab o cuentas reales. Sin reinstalar dependencias.

### Voz: implementación real, prueba física pendiente

El micrófono emite RMS de los bloques PCM existentes cada ~100 ms (ganancia visual y límite 0–1). La banda representa esos valores; al terminar escucha se limpia. La respuesta hablada transmite JSON por stdout desde el proceso aislado y el orbe se suaviza cada 40 ms. `QAudioBufferOutput` suministra el PCM decodificado durante la reproducción: la señal visual depende del audio, no de un seno aleatorio ni del texto. Requiere Qt ≥6.8 y backend que entregue buffers (FFmpeg); si no llegan, se muestra que el nivel no está disponible. La salida de audio sigue funcionando en ese caso.

Edge conserva su archivo MP3. SAPI intenta generar WAV con pyttsx3 y reproducirlo por Qt para medir PCM; si la generación/reproducción falla, se conserva SAPI directo y se avisa que no hay medición, sin animación inventada. Generar el WAV completo puede añadir espera inicial, indicada como «Preparando voz». Este entorno tiene PySide6 6.11.2; se verificó el objeto QAudioBuffer y el transporte con fixtures, **no** la reproducción física, las voces de Windows del usuario ni la respuesta a su micrófono. No se promete que el cambio de volumen maestro de Windows cambie la amplitud PCM medida.

1. Cierra VICTOR y abre `iniciar.bat` en tu escritorio normal. No reinstales las dependencias.
2. En **Voz**, activa explícitamente **Voz de VICTOR**, elige Manual para la prueba y pulsa el micrófono. Habla primero suave y luego más fuerte: debe cambiar la banda «Micrófono». El motor/modelo de reconocimiento debe estar listo en Ajustes → Voz.
3. Di «hola» con IA configurada o escribe un mensaje en Inicio y vuelve a Voz durante la respuesta. El orbe central debe variar con el audio hablado. Sin PCM disponible debe aparecer el aviso correspondiente; no confundirlo con una prueba de sonido aprobada.
4. Prueba Detener y cambia entre Manual/Push-to-talk/Continua: la selección debe ser única y el nivel anterior no debe quedarse congelado al finalizar escucha.
5. Para Telegram, pulsa **Conexiones → Telegram**. Para pantalla del celular, pulsa **Conexiones → Control remoto → Iniciar / detener servidor → Mostrar QR**. Los pasos completos de emparejamiento, certificado y teclado siguen más abajo; esta sesión solo cambia su acceso visual, no el streaming ni sus permisos.

## Registro anterior — 10/10/2026

## Ejecutado de verdad

- Corrección posterior del aviso bs4: BeautifulSoup 4.15.0 e imports GUI ya funcionaban con `.venv/Scripts/python.exe`. El activador apuntaba a una carpeta anterior y resolvía Python global. iniciar.bat ahora invoca su propio intérprete por ruta absoluta. Prueba del launcher real con `--smoke-test`: código 0, `window_open=true`, apertura y cierre; evidencia externa `work/inicio_corregido.json`. Sin reinstalar dependencias ni repetir la suite; este cambio solo afecta al script de inicio.

- Suite completa existente + nuevas: **109 pruebas aprobadas, 45,748 s**, ejecución `python -X utf8 -m unittest discover -s tests -q` desde el .venv existente. El primer pase relacionado tuvo dos regresiones GUI que se corrigieron. La nueva prueba del volumen detectó una fixture contaminada por polling sin cuenta; se aisló el polling en esa prueba, no en el producto.
- Tras el último ajuste de contraste claro: **3 pruebas GUI aprobadas, 14,687 s** (`tests.test_design.DesignGUI` y `tests.test_gui_qt`). No se repitió la suite completa sin necesidad; estas son las verificaciones posteriores a ese cambio.
- Último ajuste de sincronización visual mini/panel Spotify: **3 pruebas afectadas aprobadas, 20,163 s** (`tests.test_v5.V5.test_gui_prediction_rejection_debounce_and_presentation` y `tests.test_design.DesignGUI`). Confirman que el panel grande cambia icono/aviso pendiente al instante y comparte el volumen optimista.
- Compilación final de `main.py`, `victor`, `tests`: **código 0**. No se reinstaló ninguna dependencia.
- Ventana Qt real visible; 21 páginas recorridas y capturadas, modal ALTO rechazado sin acción, 420×760 con campo de texto 103 px y accesos de 133/134 px, tema claro legible y cierre limpio. Solo se capturaron widgets propios con Qt, no el escritorio del PC. Capturas fuera del proyecto: `<CARPETA_LOCAL>` (`actual_sheet.jpg`, `actual_<sección>.png`, `final_narrow.png`, `final_light.png`, `actual_confirmation.png`). Las conversaciones/métricas inyectadas en la revisión visual final son fixtures identificadas, no consultas IA/Spotify ni mediciones de la cuenta del usuario.
- Archivo nuevo `tests/test_design.py`: 12 pruebas de coordinación GUI/servicios, coordenadas virtuales/letterbox, rechazo de eventos inválidos, no resurrección de sesión, grant sin corte 60 s, canal WebSocket/ACK/limpieza, puntero MEDIO sin esperar Core.busy, ruta de fuente, coalescencia JavaScript con Node, reducción de red Spotify, dispositivo configurado, cliente HTTP reutilizado y seek/playlists MEDIO/schema/rechazo/API simulada. Regresión nueva en test_v5: slider protegido de snapshots atrasados y confirmación real de nivel.
- Tests anteriores de Unicode/IME, teclas especiales, replay, foco simulado, riesgo ALTO, revocación y cierre siguen pasando. Las trazas MSS/ImageGrab y ConnectionError de la suite son fallos inducidos con mocks; no constituyen nuevos intentos de captura real. La advertencia de Starlette/httpx no fue un fallo y no motivó reinstalar librerías.
- Comparación exacta contra el respaldo previo: `core.py` y `security.py` idénticos. Cambios en 14 módulos de producto: GUI (app, panels, widgets, theme, voice_panel, spotify_player, maintenance, tool_labels), integrations (spotify, local_remote, remote_touch, remote_view), system (input_automation, remote_input). Cuatro tests existentes adaptados a navegación/caché/control nuevos; un test nuevo, cuatro assets fuente/licencia y tres documentos actualizados.

## Comparación visual directa con el ZIP

Se abrieron los PNG reales, incluido Ajustes IA de la subcarpeta (más completo que su duplicado raíz), no solo un texto descriptivo. Coinciden la paleta Grafito, tipografía Inter/IBM Plex Mono, panel lateral220px, header68px, márgenes externos24/22px, disposición de tarjetas/columnas, chat, métricas/reproductor a la derecha, superficies redondeadas y jerarquía de títulos29px. Los iconos son trazos SVG recreados; el ZIP no contiene SVG/fuentes vectoriales del original. Difieren textos y datos reales, anchos naturales de burbujas, detalles de iconos/controles, proporciones de algunas tarjetas y rasterización de Qt/Windows. La vista estrecha se adapta a iconos y dos columnas. **No se declara una copia pixel por pixel** ni se inventa la canción/eventos/cuentas del mockup. La sección Spotify sin cuenta muestra indicación clara; con estado real se habilitan los controles.

## Spotify: qué se midió y qué no

Callback visual optimista: **0,87 ms**, con `spotify_command` simulado; no es latencia de audio ni de la API Spotify real. Test de red: tres órdenes calientes (dos volúmenes y siguiente) comparten una consulta inicial Premium y una inicial devices; cada orden hace luego solo su escritura, sin current_playback adicional. Debounce120ms y slider sin retroceso comprobados en Qt con mocks. Polling, portada y controles tienen trabajadores separados y timeouts; metadatos de cuenta5min/dispositivo5s, sesiones HTTP por trabajador cerradas al terminar. Play/pausa/siguiente/anterior siguen MEDIO, volumen LOW anterior conservado. **Pendiente** medir con cuenta Premium y Spotify de escritorio reales, incluyendo cualquier tiempo de autorización exigida por la política.

## Remoto: implementación y límites reales

Canales separados `/screen`, `/pointer`, `/keyboard`, `/control`; puntero/teclado en workers propios, captura existente y sonda de foco terminable. Mapeo validado sobre imagen decodificada, letterbox y origen de escritorio virtual; SendInput comprueba destino, falla segura, esquinas y PID propio. La imagen inicial solicita compartir pantalla, MEDIO; primer control táctil confirma un grant MEDIO por canal/destino, sin bajar riesgos de otras herramientas. QR autoriza texto ordinario MEDIO, atajos ALTO mantienen diálogo EJECUTAR. Los latidos3s renuevan una sesión todavía válida; una revocada/caducada no resucita. Streaming no expira a los60s dentro de esa sesión; la suspensión del navegador/PC y el certificado siguen siendo límites. Se mantiene la confirmación independiente por alto riesgo.

No se intentó MSS/ImageGrab ni input nativo real en **CodexSandboxDesktop**, cuya limitación ya estaba diagnosticada. No se han verificado TLS en el navegador del teléfono, transmisión de pantalla real, apertura del teclado iOS/Android, campo editable real ni gestos de un dedo/dos dedos con PC físico. Los tests de WebSocket usan TestClient y entrada simulada; no equivalen a Wi-Fi ni escritorio real. La apertura automática de teclado puede necesitar **Teclado** por restricciones de gesto del navegador. No se afirma que esos extremos estén probados.

## Pasos exactos que debe ejecutar el propietario

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

## Limpieza aplicada

Se comprobaron rutas absolutas antes de eliminar/mover. Se eliminaron 77 archivos .pyc de 11 directorios __pycache__ de raíz/victor/tests (860655 bytes). Se archivaron 3 capturas CAPTURAS_V5 (154239 bytes) fuera del proyecto en `<CARPETA_LOCAL>`. Los paths históricos CAPTURAS_V5 de los registros inferiores ya no están en la carpeta del producto. `.venv`, `data`, `.env`, `workspace`, modelos, tokens e historial no se borraron. No se generó ZIP nuevo porque esta petición pide modificar la instalación existente.

---

# Historial anterior de verificación (no describe esta sesión)

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
