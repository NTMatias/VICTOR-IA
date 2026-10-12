# Verificación de la publicación v7.0.0

- Suite completa: 281 casos, 280 aprobados y 1 prueba online optativa omitida; ejecución local en Windows con Python 3.12.
- La prueba omitida carga WhatsApp real y puede habilitarse con VICTOR_RUN_LIVE_TESTS=1; las pruebas del host, paleta, clic y recepción usan fixtures locales sin cuentas ni mensajes reales.
- pip check correcto y compilación Python correcta para las siete etapas.
- Hosts Spotify y WhatsApp compilados desde C# con el SDK NuGet oficial fijado y su SHA256 comprobado.
- Intérprete portátil: imports, Whisper local, Codex 0.162.1 y Claude Code 2.1.197 verificados.
- GUI portátil abierta y cerrada correctamente con 49 herramientas, modo manual y terminales diferidos; captura sin cuentas ni datos personales.
- ZIP portátil: 15.706 archivos, CRC correcto y manifest SHA256. Las claves, perfiles, conversaciones e historial personales no se copiaron.
- Revisión de las siete fuentes: sin coincidencias con credenciales reales del propietario ni inclusión de sus carpetas privadas.

Las verificaciones actuales no repiten la autenticación real de cada servicio ni la reproducción física con todos los micrófonos y altavoces. La prueba real Gemini de imágenes durante el desarrollo devolvió 429 por cuota; las pruebas de generación automatizadas utilizan respuestas simuladas.

## Repetir la suite

Tras instalar las dependencias y construir los hosts, ejecutar desde la raíz:

`powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
`

[Verificación histórica conservada](docs/VERIFICACION_HISTORICA.md).
