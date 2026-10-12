# Audio sintético de regresión

`wake-luis.wav` y `gamina-command.wav` son frases de prueba sintetizadas con es-EC-LuisNeural durante el desarrollo de VICTOR. No son grabaciones del micrófono del propietario. Se decodificaron a mono 16 kHz para probar VAD, ruido, eco y nombres musicales; no contienen claves ni datos de cuentas.

Las pruebas DSP usan semillas fijas, ruido y un eco generado matemáticamente. No reproducen audio ni abren micrófonos reales. El benchmark de ASR solo carga un modelo Whisper local que ya esté descargado; no usa servicios de transcripción ni credenciales reales.
