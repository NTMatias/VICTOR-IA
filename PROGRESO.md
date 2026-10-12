# VICTOR.IA v2 — progreso y reanudación

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
