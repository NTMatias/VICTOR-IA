# Cambios por versión

La serie v1–v6 procede de seis ZIP reales conservados durante el desarrollo. v7 recoge la aplicación actual, con las revisiones posteriores del 10–12 de octubre de 2026. No se han fabricado versiones intermedias ni fechas de commits: el historial Git importa esas etapas al publicar.

## [v1.0.0 — Base del asistente](https://github.com/NTMatias/VICTOR-IA/releases/tag/v1.0.0)

- Primera interfaz de escritorio con CustomTkinter y chat con respuestas en streaming.
- Proveedores OpenAI, Anthropic, Gemini y Ollama; configuración de modelos y claves personales.
- Memoria e historial SQLite, herramientas de Windows y confirmaciones según el riesgo.
- Capturas, visión y entrada/salida de voz opcionales.

## [v2.0.0 — Interfaz Qt, voz y primeras conexiones](https://github.com/NTMatias/VICTOR-IA/releases/tag/v2.0.0)

- Migración de CustomTkinter a PySide6/Qt, interfaz adaptable y métricas del equipo.
- Órdenes locales directas, búsqueda web y mejoras del enrutamiento de herramientas.
- Whisper local, Edge TTS y escucha continua; configuración de Ollama CPU/GPU.
- Integraciones iniciales de Spotify y Telegram con control de usuarios autorizados.

## [v3.0.0 — Google y control remoto HTTPS](https://github.com/NTMatias/VICTOR-IA/releases/tag/v3.0.0)

- Integración Google OAuth para Gmail, Calendar y Drive.
- Control remoto local HTTPS y emparejamiento por QR.
- Chat con burbujas, controles rápidos consistentes y tarjetas de confirmación.
- Mejoras de organización, cierre y manejo de errores de servicios.

## [v4.0.0 — Voz dedicada y controles más claros](https://github.com/NTMatias/VICTOR-IA/releases/tag/v4.0.0)

- Sección de voz independiente, confirmaciones de acciones y etiquetas de herramientas en español.
- Mini reproductor de Spotify y mejor organización de la interfaz.
- Conversación por Telegram y reproducción supervisada de YouTube.
- Página remota unificada con pantalla, interacción táctil y teclado.

## [v5.0.0 — Presentación, diagnóstico y preparación de voz](https://github.com/NTMatias/VICTOR-IA/releases/tag/v5.0.0)

- Refinamiento visual inspirado en Nextendo conservando la paleta del proyecto.
- Modo presentación F11 y panel de preparación con descarga del modelo Whisper.
- Diagnóstico asíncrono de conexiones y registro visible de acciones.
- Consulta de Spotify adaptativa y mejoras de tolerancia de la palabra de activación.

## [v6.0.0 — Teclado remoto incremental](https://github.com/NTMatias/VICTOR-IA/releases/tag/v6.0.0)

- Canal WebSocket de teclado separado de los canales de pantalla y control.
- Texto incremental Unicode/IME, confirmaciones ACK y cola serializada sin duplicar reintentos.
- Autorización de escritura ordinaria por sesión emparejada y confirmación local para atajos de riesgo alto.
- Procesos acotados para captura, foco y entrada; recuperación de desconexiones.

## [v7.0.0 — Grafito, música, WhatsApp, imágenes y agentes](https://github.com/NTMatias/VICTOR-IA/releases/tag/v7.0.0)

- Diseño Grafito, navegación organizada, tipografía Segoe UI y respuestas con Markdown legible.
- Spotify integrado: carátula, biblioteca, búsqueda, controles y coincidencia aproximada por título y artista; intención «cualquier canción de…».
- Voz: activación por VICTOR, saludo y espera de petición, interrupción, reducción progresiva de música y recuperación tras silencio.
- Transcripción OpenAI opcional, Whisper local, WebRTC para ruido/eco, Silero VAD y limpieza de texto para pronunciación.
- WhatsApp Web dentro de la aplicación con la paleta Grafito y tarjeta de conversaciones recientes; retirada de la vista nativa experimental.
- Claves personales protegidas con DPAPI y conexión de cuenta ChatGPT elegible; Gemini exclusivamente mediante API key con enlace a AI Studio.
- Selector de generación de imágenes OpenAI/Gemini, imágenes en conversación, historial, ampliación, guardado y cancelación.
- Agentes de programación: Codex y Claude Code oficiales en terminales ConPTY/xterm, proyectos y catálogo de modelos Codex.
- Limpieza de código y dependencias obsoletas, creación diferida de terminales y distribución portátil Windows x64.

## Evolución dentro de v7

- 10/10/2026 — diseño Grafito, Spotify y remoto
- Corrección de arranque — aviso bs4
- 11/10/2026 — correcciones gráficas y niveles de voz
- 11/10/2026 — tarjetas recortadas, orden y transiciones de ventana
- 11/10/2026 — referencia final de controles Windows
- 11/10/2026 — servicios ordenados y Spotify sin diálogos
- 11/10/2026 — diagnóstico y corrección de Gemini
- 11/10/2026 — Spotify: biblioteca navegable y búsqueda visual
- 11/10/2026 — Spotify integrado: sustituye las dos listas Qt y la ventana externa
- 11/10/2026 — Restauración del panel de carátula y coherencia visual de Spotify
- 11/10/2026 — Spotify por voz: ejecutar la orden y retirar respuestas ficticias
- 11/10/2026 — Voz, claves personales, Markdown y música por artista
- 11/10/2026 — Reconocimiento de OpenAI integrado
- 11/10/2026 — Canción cercana, coletillas de radio y escucha continua
- 11/10/2026 — VICTOR solo activa, saluda y escucha la petición
- 11/10/2026 — Fundido de música, activación por petición y pausa directa
- 11/10/2026 — Interrupción por VICTOR y música baja durante la espera
- 11/10/2026 — Auditoría de reconocimiento y procesamiento acústico
- 11/10/2026 — Título/artista y pestaña WhatsApp
- 11/10/2026 — WhatsApp nativo y mensajes recientes en Inicio
- 11/10/2026 — Regreso a WhatsApp Web y rediseño de recientes
- 12/10/2026 — Cuentas de IA y preparación USB
- 12/10/2026 — Revisión actual: fuentes, imágenes, agentes y Gemini solo por API
- 12/10/2026 — Corrección real de Codex, recientes, imágenes y limpieza

[Registro detallado](docs/REGISTRO_DESARROLLO.md) · [Notas históricas de uso](docs/NOTAS_DESARROLLO.md).
