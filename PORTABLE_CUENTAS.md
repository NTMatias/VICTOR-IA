# Llevar VICTOR.IA al colegio

La versión portátil actual incluye Python y dependencias, Whisper base, Node.js, Codex, Claude Code, Qt WebEngine y WebView2 para Windows 10/11 de 64 bits. No necesita Python ni VS Code instalados. **Claude Code requiere Git Bash**, y Ollama requiere su servidor/modelo por separado.

1. Extrae todo el ZIP en una carpeta local NTFS, por ejemplo el Escritorio. La USB FAT32 sirve para transportarlo; no ejecutes dentro del ZIP.
2. Abre `VICTOR.IA/ABRIR VICTOR.bat`. `COMPROBAR VICTOR.bat` comprueba dependencias, Whisper y versiones de los agentes.
3. En **Ajustes → Inteligencia artificial**, selecciona proveedor. ChatGPT puede usar cuenta elegible con OAuth oficial o API key. **Gemini solo usa API key**: pulsa **Obtener API key de Gemini** para abrir [Google AI Studio](https://aistudio.google.com/apikey), pega la clave en Claves API personales y guarda.

La integración Gemini CLI y su inicio de sesión Google están retirados. Una configuración antigua se adapta al cargar, conservando las demás preferencias. No se reutilizan credenciales de Antigravity. Las conexiones Gmail, Calendar y Drive son independientes.

No se incluyen claves, cuentas, perfiles de navegador, conversaciones, capturas ni proyectos personales. Las conexiones deben autorizarse en la otra PC. Spotify y Gmail requieren los datos OAuth de tu aplicación en `.env`; WhatsApp usa el QR oficial. Internet es necesario para servicios en la nube. Whisper y órdenes locales funcionan sin cuenta IA.

## Imágenes y agentes

Escribe «genera una imagen de…» y elige ChatGPT/OpenAI o Gemini antes de generar. Cada proveedor necesita su API key con permisos y cuota propios. Una suscripción ChatGPT conectada para texto no sustituye la clave de Images API. Las imágenes aparecen en la conversación y permiten ampliar, guardar y recuperar desde el historial.

**Agentes de programación → Codex / Claude Code** ejecuta los CLIs oficiales completos dentro del terminal de VICTOR. Elige tu carpeta y abre el agente. Los permisos, autenticación, comandos slash, historial y herramientas son los propios del CLI. Adjuntar archivos pega las rutas para revisar antes de enviar. Interrumpir envía Ctrl+C; cerrar termina el proceso. Claude Code en Windows necesita Git Bash. La comprobación de versión no confirma elegibilidad de cuenta ni ejecuta tareas de IA.

## Verificación

Las pruebas de OAuth usan tokens sintéticos firmados y servidor loopback; no prueban una suscripción real. Las pruebas de API e imágenes usan respuestas sintéticas, sin consumir saldo. Se comprueban migración de ajustes, clave obligatoria para Gemini, ausencia de procesos Gemini CLI, conservación de ChatGPT, archivos de imagen, historial, cancelación y terminal ConPTY. Autoriza tus cuentas y prueba solicitudes reales desde la interfaz.

- [Claves Gemini](https://ai.google.dev/gemini-api/docs/api-key)
- [Sign in with ChatGPT](https://developers.openai.com/siwc/token-sharing-open-source/sign-in)
- [Limitaciones del acceso por cuenta](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)
- [Codex CLI](https://developers.openai.com/codex/cli/)
- [Claude Code](https://code.claude.com/docs/en/setup)
