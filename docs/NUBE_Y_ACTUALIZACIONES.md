# Cuentas en nube, administración, actualizaciones y orbe

Estado: **proyecto Supabase creado y esquema instalado; distribución estable todavía pendiente**. La instalación local está conectada. La prueba real de aislamiento de datos pasó y se revirtió sin conservar sus cuentas ficticias. Falta SMTP para registro público y una cuenta verificada del propietario para su rol dentro de VICTOR. Consulta [el estado de la entrega 8](RELEASE_8_PREPARACION.md).

## Funciones implementadas

- El orbe se arrastra manteniendo pulsado el botón izquierdo. No activa el micrófono ni roba el foco; la zona exterior a su máscara deja pasar los clics. Conserva su posición en la configuración de la cuenta y la ajusta al área disponible si cambia la pantalla. Sigue inmóvil en silencio.
- Cliente de cuentas Supabase con registro por correo, confirmación, inicio de sesión, cambio de contraseña y sesión recordada cifrada con Windows DPAPI. No se migran ni suben contraseñas locales. La nube está desactivada por defecto, por lo que el acceso local actual continúa funcionando.
- Los usuarios aceptan el registro de correo, fechas de acceso y versión. La aplicación no sube conversaciones, grabaciones, memoria ni claves de IA. Cada cuenta obtiene una carpeta local independiente; tampoco hereda las claves de IA del entorno del propietario. Para cambiar de cuenta se cierra y abre VICTOR.
- Panel de administración dentro de Ajustes → Generales: cuentas y accesos, con páginas de 200 registros. La autorización se comprueba en servidor, no mediante un botón oculto. Solo un UUID promovido por el dueño del proyecto puede consultar otras cuentas. Nunca se muestran contraseñas.
- Comprobación de versiones al iniciar la sesión y cada seis horas mientras VICTOR permanece abierto. Aviso no bloqueante, descarga en segundo plano y comprobación de firma Ed25519, tamaño y SHA256. La aplicación sigue funcionando si no hay conexión. La descarga no sobrescribe una instalación que está ejecutándose ni los datos del usuario.

## Activar las cuentas reales

1. Crear o elegir un proyecto propio en Supabase. Obtener su URL HTTPS y su clave **publishable** (o la antigua anon). Nunca copiar `service_role` ni `sb_secret_` a la app o a una distribución.
2. Ejecutar [schema.sql](../cloud/schema.sql) en el editor SQL del proyecto. Activa las políticas por fila, las tablas de perfiles/accesos y el registro de acceso con fecha del servidor. Los clientes no pueden asignarse administradores ni escribir perfiles ajenos.
3. Habilitar confirmación de correo y configurar el envío de correos para usuarios reales. El registro solicita aceptar los datos de cuenta compartidos. La recuperación de contraseña por correo requiere además una página de recuperación configurada en Supabase; no está incluida en esta fase.
4. Copiar `deployment.example.json` a `deployment.json`, introducir URL/clave publicable y poner `cloud.enabled` en `true`. La configuración se valida antes de incluirse en un portátil. Sus valores son públicos por diseño; ninguna clave administrativa debe aparecer en ella.
5. Registrarse como propietario, confirmar el correo y obtener el UUID de esa cuenta desde Supabase Authentication. Promover únicamente ese UUID con la sentencia comentada al final de schema.sql. Después abrir «Administración de cuentas» en VICTOR.
6. Verificar en el servidor que una cuenta ordinaria solo lee su perfil, que no accede al historial de accesos y que no puede insertar privilegios. Estas políticas no pudieron probarse contra un proyecto real porque aún no se proporcionó uno.

El historial de accesos de la app agrupa eventos repetidos dentro de un minuto para limitar escrituras. Las renovaciones automáticas del token no se cuentan como accesos nuevos. Este registro no sustituye los logs de autenticación oficiales de Supabase. No se configuró una política de retención ni un proceso de eliminación de cuentas; definirlos antes de distribuir públicamente.

Las carpetas locales nuevas están en `data/profiles/<UUID>`; las carpetas y claves locales anteriores no se borran ni se copian a otro usuario. El bloqueo de la app no cifra los archivos personales ni sustituye los permisos de Windows.

## Publicar una actualización

El repositorio existente es `NTMatias/VICTOR-IA`. El release estable sigue siendo v7. El borrador v8 no debe promoverse sin resolver los pendientes y reconstruir el paquete definitivo.

1. Inicializar una sola vez la identidad de firma del editor desde el entorno Python del proyecto: `python -m tools.sign_update --init-keys`. La clave privada queda cifrada con DPAPI en `data/update_signing/private.dpapi`, excluida de Git. La pública está en `public.hex`.
2. Poner esa clave pública en `updates.public_key_hex` dentro de deployment.json; conservar el feed `https://github.com/NTMatias/VICTOR-IA/releases/latest/download/update.json` y activar `updates.enabled`.
3. Antes de construir cada versión, actualizar VERSION en `victor/version.py`. Empaquetar el portátil de Windows con el procedimiento existente. El paquete debe incluir deployment.json con los valores públicos correctos.
4. Firmar el ZIP, indicando su versión y la URL final del asset. Ejemplo para una versión futura:

   `python -m tools.sign_update --version 8.0.0 --asset RUTA_AL_ZIP --url https://github.com/NTMatias/VICTOR-IA/releases/download/v8.0.0/VICTOR_IA_v8.0.0_Windows_x64.zip --output update.json`

5. Publicar juntos el ZIP y update.json en un release estable de GitHub con ese tag. El firmador comprueba que la versión contenida en el ZIP coincide; no ejecuta su código. El cliente solo admite assets HTTPS del repositorio y tag esperados, rechaza firmas inválidas y elimina descargas incompletas.
6. Las apps que **ya incorporen este actualizador y su clave pública** detectarán la publicación al abrirse o durante la comprobación periódica. Las versiones antiguas no pueden adquirir mágicamente un actualizador: requieren instalar esta primera versión una vez. Si están cerradas o sin Internet, lo detectarán al volver a abrirse/conectarse.

Se implementaron aviso y descarga verificada, **no sustitución automática de archivos ni instalador silencioso**. La interfaz abre la carpeta de descarga para instalar. La instalación completa automática conservando perfiles, con reversión tras fallos, queda como siguiente fase; no se afirma que esté resuelta mediante descargar un ZIP.

Conservar la identidad de firma. El archivo privado DPAPI depende del usuario/equipo de Windows: copiarlo por sí solo a otra PC no garantiza recuperación. Si se pierde la identidad de firma, los clientes no confiarán en una clave nueva sin una migración o reinstalación explícita.

## Validación disponible y pendiente

Pruebas locales con cuentas, tokens y paquetes ficticios: sesión cifrada, confirmación de correo, separación de carpetas y claves, cambio de usuario, rechazo de claves secretas, firma manipulada, URL/versión incorrecta, SHA256, limpieza de descargas y arrastre persistente del orbe. También se verifican los flujos locales existentes de acceso, voz y Qt.

Comprobado contra el proyecto real: políticas RLS, restricción de escalamiento de privilegios, escritura del acceso y rechazo REST anónimo. Se usaron identidades ficticias dentro de una transacción revertida. Pendiente: registro y entrega real de correo, rol de la cuenta del propietario y distribución a un segundo equipo. No se enviaron correos ni subieron conversaciones o claves personales durante estas pruebas.

Fuentes: [autenticación por contraseña de Supabase](https://supabase.com/docs/guides/auth/passwords), [políticas por fila](https://supabase.com/docs/guides/database/postgres/row-level-security) y [claves publicables y secretas](https://supabase.com/docs/guides/getting-started/api-keys).
