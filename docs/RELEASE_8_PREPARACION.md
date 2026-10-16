# VICTOR.IA 8.0.0: borrador de validación

Esta entrega no está lista para un despliegue público general. No sustituye todavía al release estable 7.

## Instalado y comprobado

- Organización gratuita VICTOR.IA y proyecto VICTOR-IA en Supabase.
- Tablas profiles y login_events, registro con fecha de servidor y roles protegidos.
- Prueba real en PostgreSQL con dos identidades ficticias, revertida: aislamiento de perfiles, historial oculto, escalamiento de privilegios rechazado y un evento de acceso por minuto.
- Endpoints públicos comprobados: autenticación disponible y correo confirmado obligatorio; lectura anónima de perfiles y accesos devuelve 401.
- deployment.json conecta esta instalación con el proyecto usando solo su clave publicable. La identidad privada para firmar actualizaciones permanece cifrada en data/update_signing, fuera de la distribución.
- Página de confirmación: https://ntmatias.github.io/VICTOR-IA/. Elimina los tokens del fragmento inmediatamente y no los almacena ni transmite. Configurada como Site URL en Supabase.
- Suite general: 329 pruebas ejecutadas, sin fallos ni errores, con una prueba online optativa omitida. Después del último arreglo de cancelación se ejecutaron además 84 pruebas de voz, todas aprobadas. Incluyen cuentas, permisos, voz, cancelación, Spotify, WhatsApp, ventanas y agentes.
- Se corrigió una carrera real al probar el micrófono mientras la voz anterior aún se cancelaba: la interfaz espera a que terminen ambas operaciones antes de capturar, sin bloquear Qt.
- Se corrigió el estado ocupado que podía persistir al cancelar una frase todavía en cola, antes de generar audio. La nueva prueba falla con la implementación anterior y aprueba con el arreglo; Detener libera el estado cuando no queda generación ni reproducción activa.
- Las pruebas anteriores a la autenticación ahora inician una sesión ficticia explícita. Las de SAPI se migraron a PCM/Edge y las de Spotify comprueban la transparencia y los degradados actuales. No se reintrodujo el motor retirado ni se desactivaron las barreras de acceso.

## Límites que impiden publicar como estable

1. SMTP externo no configurado. Supabase solo permite correo a miembros del equipo con su servicio de pruebas, actualmente 2 mensajes/hora. Los registros de público requieren un proveedor de correo configurado. No se deshabilitó la confirmación para eludirlo.
2. Todavía no existe una cuenta de usuario de VICTOR en este proyecto. Iniciar sesión en el panel Supabase no crea esa cuenta. No se inventó una contraseña ni se asignó el rol de administrador a una dirección no verificada. El dueño ya puede consultar profiles y login_events desde el Table Editor de Supabase; el panel de administrador de VICTOR requiere registrar y promover su UUID verificado.
3. Los 16 incidentes detectados en la primera ejecución de regresión quedaron resueltos. Esa ejecución no representa el estado actual: la suite final pasó con 329 pruebas, sin fallos ni errores y una omisión optativa.
4. El actualizador implementa aviso, firma y descarga; la sustitución de archivos sigue siendo manual. Está desactivado mientras no haya un paquete estable firmado publicado. Las versiones antiguas requieren instalar una vez la edición con actualizador.
5. No se validó todavía la entrega real de correo ni un ciclo de acceso con la cuenta del propietario, ni la descarga en una segunda PC.

## Activación final

Configurar SMTP en Supabase; registrar y verificar la cuenta del propietario y promover exclusivamente su UUID según cloud/schema.sql; activar updates.enabled; reconstruir, probar y firmar el ZIP de ese estado definitivo y publicar juntos el ZIP y update.json. No publicar sin reconstruir el borrador actual después de cambiar su configuración.

Se comprobó la disponibilidad local de configuración SMTP, Resend, Brevo y SendGrid sin revelar valores: no hay credenciales configuradas. No se contrataron servicios ni se inventaron claves. El propietario dispone además del acceso directo Administrar VICTOR.IA en su Escritorio para consultar el historial desde su sesión de Supabase.

Los datos personales anteriores permanecen en su ubicación original. Las cuentas de nube usan carpetas data/profiles/UUID separadas y no heredan claves privadas del propietario.

Fuente de límites de correo: https://supabase.com/docs/guides/auth/auth-smtp
