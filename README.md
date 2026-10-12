# VICTOR.IA

Asistente de escritorio modular para **Windows 10/11 y Python 3.11+ de 64 bits**. Interfaz CustomTkinter, chat con streaming, cuatro proveedores de IA, herramientas supervisadas de Windows, memoria e historial SQLite y voz opcional.

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
ollama pull llama3.2
ollama serve
```

Si Ollama ya está ejecutándose no necesitas `ollama serve`. Selecciona **Ollama** y el nombre exacto del modelo descargado. Solo se aceptan servidores de loopback locales. Un modelo con visión se configura por separado; un modelo de texto no puede analizar imágenes.

**Fallback**: escribe proveedores separados por comas, por ejemplo `Gemini, Ollama`. El principal se intenta primero; si falta su clave o falla, se prueba el siguiente y se informa del cambio. Está vacío inicialmente para no enviar conversaciones a proveedores adicionales sin configurarlos. En visión se utiliza solo el proveedor de visión seleccionado, sin fallback silencioso de imágenes. Una respuesta parcial fallida se borra antes de mostrar la del respaldo.

## Uso

- **Enter** envía; **Mayús+Enter** agrega una línea. Hay streaming de texto de todos los adaptadores.
- **Detener** corta la voz, cancela confirmaciones y evita las siguientes acciones. Una petición de red ya iniciada puede tardar hasta el timeout en devolver el control; las acciones completadas no se deshacen.
- **Nueva conversación**, búsqueda y eliminación están en la columna izquierda. El historial vuelve a aparecer al abrir la aplicación.
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

La carpeta `workspace/`, creada automáticamente, es la única raíz autorizada por defecto. Añade otras **rutas absolutas**, una por línea, en Configuración. No autorices todo tu disco. Las rutas relativas se resuelven dentro de la primera raíz.

- Se bloquean carpetas del sistema, datos internos del asistente, `.env`, enlaces simbólicos/junctions, rutas UNC/dispositivos, flujos NTFS y rutas fuera de las raíces autorizadas.
- Crear archivos admite texto (`txt`, `md`, `csv`, `json`, `log`, `yaml`, `yml`). No crea ejecutables ni scripts. Nunca sobrescribe destinos existentes.
- Mover/copiar/renombrar/eliminar admite **archivos individuales**, no árboles de carpetas. La eliminación usa `send2trash`; nunca hay borrado permanente como fallback.
- Abrir archivos admite un conjunto de extensiones de documentos, texto y medios. No abre scripts, accesos directos, ejecutables ni documentos con macros.
- Las aplicaciones iniciales incluyen calculadora, bloc de notas, Paint, explorador y navegadores conocidos. Puedes registrar aliases con un JSON como `{"editor": "C:/Apps/Editor/editor.exe"}`. Solo acepta `.exe` existentes y bloquea intérpretes y herramientas administrativas conocidas. Registra exclusivamente programas que conozcas.
- Cerrar aplicaciones usa terminación de proceso y **puede perder cambios sin guardar**. Por ello requiere autorización y muestra una advertencia. Algunas aplicaciones de Windows usan un proceso distinto del lanzador; en ese caso no se cierran y se informa.

**Riesgos:** bajo = ejecución directa; medio = diálogo con parámetros exactos; alto = diálogo y escribir `EJECUTAR`. `strict` también confirma operaciones de bajo riesgo. No existe modo que elimine las confirmaciones de alto riesgo. Cada solicitud y su resultado se registran, sin guardar cuerpos con claves.

La terminal está limitada a `ipconfig`, `whoami`, `hostname` y `systeminfo`, **sin argumentos**, siempre con confirmación explícita y `shell=False`. Los comandos arbitrarios, instalación de software, edición del registro y elevación administrativa están **deliberadamente deshabilitados**. La IA no puede modificar las listas de permisos.

## Ratón y teclado

Cada acción pasa por seguridad y necesita el **título exacto de la ventana**. La ventana se activa y se verifica antes de enviar la entrada. Los clics y movimientos deben estar dentro de sus límites. Un cambio de foco interrumpe la escritura. `type_text` admite Unicode y no añade Enter; Enter/Delete requieren autorización explícita aparte. No automatiza la propia ventana de VICTOR.IA ni aplicaciones elevadas.

PyAutoGUI mantiene `FAILSAFE=True`: mueve el puntero a una esquina para abortar. Se ejecutan acciones individuales, no macros ilimitadas. Un clic o atajo puede tener consecuencias en la aplicación destino: revisa los parámetros del diálogo.

## Voz

El instalador intenta instalar cada dependencia de voz por separado. Si falla alguna, el chat continúa disponible. Entrada: `SpeechRecognition` + `sounddevice` + `numpy`, sin necesidad de PyAudio. Salida: `pyttsx3` y SAPI en un proceso aislado y cancelable.

- **Manual:** pulsa Micrófono para capturar una frase, terminando por silencio o a los 15 segundos.
- **Push-to-talk:** mantén presionado Micrófono; suelta para transcribir, máximo 15 segundos.
- **Continua:** activa Micrófono y di **VICTOR** antes del comando. No escucha durante el procesamiento de un turno ni mientras reproduce su propia voz.
- El interruptor **Voz** activa/desactiva la lectura de respuestas. Puedes elegir velocidad e ID de una voz instalada de Windows.

El modo Google envía audio para reconocimiento y solicita consentimiento al activarlo. La wake word se detecta **después de transcribir**, no mediante un motor local especializado; en modo continuo también se transcriben segmentos que finalmente se descartan por no contener la palabra. Depende del ruido, pronunciación y disponibilidad del servicio.

Para reconocimiento local alternativo:

```powershell
.venv\Scripts\python -m pip install faster-whisper
.venv\Scripts\python -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')"
```

El segundo comando descarga el modelo; puede ocupar cientos de MB. Después selecciona `whisper` y `base` en Configuración. El asistente exige que el modelo esté descargado (`local_files_only=True`) para no iniciar descargas imprevistas. Puede usarse una ruta a un modelo local. La velocidad depende de tu CPU. El chat y herramientas no dependen de Whisper.

Si el micrófono predeterminado falla, permite el acceso a micrófonos para aplicaciones de escritorio en Windows. Para enumerar dispositivos:

```powershell
.venv\Scripts\python -c "import sounddevice; print(sounddevice.query_devices())"
```

Introduce el ID del dispositivo de entrada en Configuración. El umbral de voz es fijo y puede funcionar peor con micrófonos muy débiles o ambientes ruidosos.

## Pantalla, visión y búsqueda

`take_screenshot` acepta `region: null` para todos los monitores o `[x, y, ancho, alto]` para una región dentro del escritorio. Conserva las últimas 30 capturas en `data/captures`. `active_window` devuelve el título y geometría. Las capturas de visión se reducen a 1600 píxeles por lado como máximo; no es OCR determinista.

Para «¿Qué hay en mi pantalla?» configura un proveedor y modelo de **visión**. Antes de transmitir una captura aparece el proveedor, archivo y pregunta en una confirmación. Sin clave o con un modelo no compatible se muestra un error; no se inventa un análisis. El permiso es por captura, no permanente.

La búsqueda usa DuckDuckGo, con timeout y caché de cinco minutos. Se detectan expresiones como noticias, hoy, precio, busca e investiga; también puede solicitarla el modelo. Se leen hasta cuatro páginas HTML, con tamaño limitado, sin redirects automáticos y rechazando direcciones privadas/locales. Páginas bloqueadas, de contenido dinámico o no HTML pueden dejar solo el extracto del buscador. Las respuestas incorporan las fuentes y las limitaciones de lectura. Los resultados son datos no confiables, nunca autorización para actuar.

## Arquitectura y datos

`main.py` inicia la aplicación. `victor/core.py` coordina un turno por vez, los adaptadores de `ai/` generan peticiones, y `tools/registry.py` valida esquemas y consulta `SecurityManager` antes de ejecutar. Los plugins son registros internos explícitos; no se carga código arbitrario descargado.

La GUI usa una cola de eventos y solo el hilo principal toca Tk. Red, herramientas y reconocimiento corren fuera del hilo de interfaz. La síntesis vive en un proceso separado. Cerrar cancela tareas y espera a los trabajadores de forma no bloqueante; existe un límite de cierre (timeout de red + 15 segundos) para servicios/controladores que no responden. Los trabajadores pendientes son daemon como último recurso; no se promete interrumpir de inmediato código nativo de terceros.

`data/` contiene SQLite, configuración, logs rotativos (2 MB × 5 archivos) y capturas. Son datos **locales sin cifrar**. No se registran claves API ni cuerpos HTTP. Los proveedores online reciben mensajes, contexto y recuerdos seleccionados para responder. Copia `data/` con la aplicación cerrada para respaldar la información. No compartas esa carpeta si contiene información privada.

El contexto usa un presupuesto de caracteres, mensajes recientes y recuerdos relevantes. Cuando crece, genera un **resumen extractivo local** (sin coste API) que conserva principio y desenlace de mensajes; no es una síntesis semántica y puede omitir detalles. El historial íntegro permanece en SQLite. La ventana carga los últimos 200 mensajes y lista hasta 60 conversaciones; las búsquedas consultan la base completa.

## Solución de problemas

- **No hay Python:** instala Python 3.12 x64 con Tkinter y soporte `venv`; marca Add to PATH. Python de 32 bits puede impedir instalar dependencias.
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

La última prueba abre una ventana real, guarda título/visibilidad/geometría y, si `mss` está disponible, una captura; después cierra. Las pruebas unitarias no usan claves, no gastan saldo, no controlan aplicaciones personales ni borran archivos reales. La prueba de papelera usa un mock; consulta `VERIFICACION.md` para saber qué se ejecutó de verdad antes de esta entrega.

## Documentación oficial de las integraciones

- [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [Anthropic Messages](https://platform.claude.com/docs/en/api/http/messages)
- [Google GenAI SDK](https://googleapis.github.io/python-genai/)
- [Ollama Chat API](https://docs.ollama.com/api/chat)

Los servicios externos, modelos, cuotas y hardware no se incluyen en el proyecto. Las funciones deshabilitadas deliberadamente se explican arriba; no hay acciones simuladas que se presenten como realizadas.
