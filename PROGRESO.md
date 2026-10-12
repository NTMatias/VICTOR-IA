# VICTOR.IA v2 — progreso y reanudación

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
