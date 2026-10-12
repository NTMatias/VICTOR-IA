# VICTOR.IA v7.0.0 — Grafito, música, WhatsApp, imágenes y agentes

- Diseño Grafito, navegación organizada, tipografía Segoe UI y respuestas con Markdown legible.
- Spotify integrado: carátula, biblioteca, búsqueda, controles y coincidencia aproximada por título y artista; intención «cualquier canción de…».
- Voz: activación por VICTOR, saludo y espera de petición, interrupción, reducción progresiva de música y recuperación tras silencio.
- Transcripción OpenAI opcional, Whisper local, WebRTC para ruido/eco, Silero VAD y limpieza de texto para pronunciación.
- WhatsApp Web dentro de la aplicación con la paleta Grafito y tarjeta de conversaciones recientes; retirada de la vista nativa experimental.
- Claves personales protegidas con DPAPI y conexión de cuenta ChatGPT elegible; Gemini exclusivamente mediante API key con enlace a AI Studio.
- Selector de generación de imágenes OpenAI/Gemini, imágenes en conversación, historial, ampliación, guardado y cancelación.
- Agentes de programación: Codex y Claude Code oficiales en terminales ConPTY/xterm, proyectos y catálogo de modelos Codex.
- Limpieza de código y dependencias obsoletas, creación diferida de terminales y distribución portátil Windows x64.

## Procedencia

Copia del proyecto actual del propietario al preparar su publicación. Se excluyen credenciales, sesiones, historial, cachés y dependencias instaladas. Los binarios WebView2 se construyen desde su código fuente.

## Descarga y requisitos

- `VICTOR_IA_v7.0.0_fuente.zip`: código completo de esta etapa, con sus scripts y documentación.
- `VICTOR_IA_v7.0.0_Windows_x64.zip`: paquete portátil con Python, dependencias, Whisper base y navegador. Extraer todo en una carpeta local NTFS y abrir `ABRIR VICTOR.bat`.
- Las fuentes requieren Windows 10/11 x64, Python 3.11+ y las dependencias de su versión. Consultar su README.
- Los servicios online necesitan Internet y las cuentas/claves correspondientes; no se incluye ninguna cuenta ni saldo.

## Límites de esta entrega

La precisión acústica depende del micrófono, altavoces y entorno. La cancelación de eco no garantiza eliminación total. Spotify integrado requiere una cuenta elegible/Premium y OAuth; Google necesita su cliente OAuth. WhatsApp depende de la página oficial y puede requerir vinculación QR. Claude Code en Windows necesita Git Bash. Las imágenes requieren una API key propia con cuota: la prueba real Gemini disponible durante el desarrollo devolvió 429; las pruebas locales de imágenes validan el manejo de respuestas, no crédito disponible. La cuenta ChatGPT no sustituye una clave para generar imágenes. No se incluyen funciones retiradas de login Gemini CLI ni el panel nativo experimental de WhatsApp.

## Verificación antes de publicar

280 pruebas aprobadas, 1 prueba online optativa omitida; SDK WebView2 compilado desde fuente; portátil comprobado con su intérprete y GUI; ZIP con CRC y SHA256 correctos. Se corrigió el ancho del selector de modelos Codex, las etiquetas de herramientas Spotify y pruebas de interfaz que dependían de tiempos fijos o de un navegador externo.
