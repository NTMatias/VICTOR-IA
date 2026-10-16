"""Measure project metadata and document verified Edge migration results."""
import json
import os
from pathlib import Path

def main():
    root=Path(__file__).resolve().parents[1];logical=0;unique=0;seen=set()
    for directory,folders,files in os.walk(root,followlinks=False):
        folders[:]=[n for n in folders if not (Path(directory)/n).is_symlink()]
        for name in files:
            path=Path(directory)/name
            if path.is_symlink():continue
            try:stat=path.stat()
            except OSError:continue
            logical+=stat.st_size;key=(stat.st_dev,stat.st_ino)
            if key not in seen:unique+=stat.st_size;seen.add(key)
    result={'logical_bytes':logical,'unique_file_bytes':unique,'note':'Hardlinks deduplicated; not NTFS allocated-cluster usage. Before writing this report.'}
    (root/'docs/edge_sizes.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    doc=f'''# Voz ligera y latencia — VICTOR.IA

Actualizado: 14 de octubre de 2026. Estado actual: Edge TTS; Chatterbox está retirado.

## Cambios implementados

- Se retiraron los modelos, el entorno PyTorch dedicado, el instalador y las herramientas exclusivas de Chatterbox. Se liberaron 1.921.394.952 bytes adicionales. Tamaño actual del proyecto: aproximadamente {logical/1e9:.2f} GB lógicos ({unique/1e9:.2f} GB de archivos únicos al descontar enlaces físicos). Las cuentas, historiales, Whisper y las integraciones se conservan. No se quitaron bibliotecas compartidas de la interfaz.
- Edge TTS 7.3.1 corrigió el rechazo WebSocket observado con 7.2.8. La lista real del servicio confirmó Luis de Ecuador, Jorge de México y Gonzalo de Colombia como voces masculinas. Se usa una sola voz seleccionada; se conservan el identificador y velocidad previamente guardados cuando existen. Si Chatterbox dejó el identificador vacío, se usa es-EC-LuisNeural. Velocidad inicial nueva: +3%; tono +0Hz. Ambos son ajustables.
- No se abren procesos de voz ni se cargan modelos TTS. Un hilo de red mantiene un bucle asíncrono. Dos solicitudes como máximo permiten preparar una frase mientras se reproduce la anterior. Cada frase tiene 12 bloques PCM de búfer; la cola de reproducción admite dos frases y la cola de texto 48. Caché RAM de hasta ocho frases y 2 MiB. Solo el saludo público se conserva en disco, hasta ocho variantes de 256 KiB.
- Se decodifica MP3 incrementalmente con el parser de PyAV y un resampler PCM mono de 24 kHz. Los paquetes de red no se reproducen como archivos independientes. Se conservan el comienzo y final de cada frase, sin recortes de silencio agresivos. Sounddevice reproduce fuera de Qt y conserva la medición real de niveles.
- El segmentador ya emite preguntas cortas sin esperar la respuesta completa. Conserva decimales recibidos en varios tokens, abreviaturas y bloques de código. Una ampliación del texto final no reinicia ni repite el prefijo ya hablado.
- Detener cambia la época, descarta texto/audio pendiente, cancela tareas de red y aborta el dispositivo de salida. La llamada VICTOR sigue pudiendo interrumpir; se mantienen la espera de respuesta y el volumen de música reducido. La bajada progresiva de música sigue siendo una espera intencional de 2–3 segundos, solicitada anteriormente.
- SpanishSpeechNormalizer expande porcentajes, unidades, temperaturas, fechas válidas y horas con contexto explícito. Las monedas se expanden cuando se especifica USD/dólares; $ sin moneda permanece ambiguo. Conserva nombres y números de productos. El diccionario personal modifica solo la pronunciación; el texto mostrado no cambia. No se inventan emociones ni SSML avanzado.
- ChatGPT/OpenAI reutiliza su cliente y conexiones HTTP entre turnos, rota al cambiar credenciales o timeout y cierra la conexión pendiente al cancelar. Conserva OAuth, controles, herramientas y ausencia de cambio silencioso a API de pago. GPT-6 tiene razonamiento low por defecto, ajustable a medium/high; no se cambió el modelo ni se habilitaron tarifas de prioridad. La interfaz agrupa deltas consecutivos antes de rehacer el formato. El resumen de contexto evita sumas repetidas. Las métricas se consultan cada 10 segundos en segundo plano y cada dos en primer plano.

## Pruebas y resultados reales

Las mediciones son de este equipo, no de hardware real de 4 GB. En la última serie Edge hubo ocho frases nuevas, con primer PCM decodificado entre 0,82 y 1,87 segundos; el saludo repetido necesitó menos de 1 ms para entregar PCM. Pico RSS del proceso de prueba: aproximadamente 70 MB, incluyendo Python, bibliotecas y cachés. Esto no es la RAM total de la app. Una serie anterior tuvo una espera de 13,19 segundos: la red no ofrece latencia constante. No se garantiza que el audio nuevo sea instantáneo.

En la prueba real de salida, el saludo precalentado se empezó a escribir al dispositivo en 0,273 segundos; la reproducción completa duró 2,356 segundos. No había música ni ducking activo. La primera escritura no mide la latencia acústica adicional del dispositivo.

La interfaz minimizada en una sesión ficticia, sin micrófono, sin TTS activo y sin sesiones de navegador, midió 135.512.064 bytes RSS y 0% de CPU registrada sobre un núcleo durante cinco segundos. Es una muestra corta y aislada. Whisper, las pestañas WebView2 de Spotify/WhatsApp y agentes activos aumentan el consumo. No se promete que todas las funciones simultáneas ocupen esa memoria ni CPU cero permanente.

Dos solicitudes reales de texto «Hola» con la cuenta configurada y razonamiento previo tardaron 68,82 y 5,05 segundos hasta el primer texto. Con low se midieron 55,03 y 2,63 segundos. Son muestras pequeñas, variables y no prueban una mejora porcentual general: la primera llamada todavía puede ser lenta por el servicio/red y preparación inicial. Se registra first_text_seconds para diagnóstico. No se elimina la espera del proveedor mediante cambios del cliente.

Artefactos: docs/edge_benchmark.json (PCM/red, sin altavoz), docs/edge_playback.json (reproducción real), docs/background_benchmark.json, docs/chat_latency_baseline.json, docs/chat_latency.json, docs/edge_retirement.json y docs/edge_sizes.json. Los resultados anteriores LATAM permanecen como historial técnico; no describen el motor activo.

Las pruebas cubren normalización, texto extenso, segmentación, orden, doce turnos consecutivos, cancelación, saludo/cache, límites de búfer, reutilización de HTTP, OAuth, activación por VICTOR, restauración de música, permisos y cierre de Qt. No equivalen a validar cuentas externas de todas las integraciones ni calidad perceptual perfecta de la voz.

73 pruebas seleccionadas distintas pasaron: un conjunto de 64 más nueve pruebas adicionales de las suites completas de interrupción y volumen. Se actualizaron los fixtures que dependían del proceso SAPI retirado para comprobar el flujo Edge en hilos; no se deshabilitaron sus comprobaciones de cancelación y volumen.

## Instalación y distribución

Instalar requirements.txt y requirements-optional.txt en el entorno habitual. Dependencias TTS: edge-tts>=7.3.1,<8, PyAV, sounddevice y NumPy. PyAV ya formaba parte del reconocimiento Whisper; no se instala un modelo de voz. Edge requiere Internet y envía el texto a su servicio, sin API TTS de pago. No hay sustitución silenciosa por SAPI.

El empaquetador portátil ya no incluye data/tts_runtime ni data/tts_latam. Conserva fuentes, bibliotecas de interfaz y Whisper. Hay que generar de nuevo cualquier distribución/USB antigua para llevar esta versión; este trabajo actualiza la carpeta del proyecto. Reiniciar VICTOR para abandonar procesos/código de la sesión anterior.

Fuentes técnicas: [Edge TTS](https://github.com/rany2/edge-tts), [latencia OpenAI](https://developers.openai.com/api/docs/guides/latency-optimization), [GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [cuentas ChatGPT e inferencia](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference). Las recomendaciones de streaming y reutilización no son garantías de tiempo de respuesta.
'''
    (root/'TTS_LOCAL.md').write_text(doc,encoding='utf-8');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
