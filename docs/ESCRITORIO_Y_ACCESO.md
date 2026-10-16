# Escritorio, acceso y organización de VICTOR.IA

Implementado el 14 de octubre de 2026 en la carpeta del proyecto. No se creó ninguna contraseña real: al abrir la app, el propietario crea su acceso.

## Orbe

Ventana pequeña encima del escritorio, inicialmente abajo a la derecha y fuera de la barra de tareas. Los clics la atraviesan y no recibe foco. Azul para la voz detectada del micrófono; violeta para el audio de VICTOR. Comparte los niveles existentes y no abre otra captura. El nivel de micrófono se muestra únicamente cuando el detector existente reconoce actividad de voz; esto no identifica biométricamente al hablante ni garantiza eliminar toda voz ajena.

No tiene animación en silencio ni una animación ficticia de pensamiento. El temporizador de dibujo trabaja a 25 FPS solamente mientras hay señal o termina de suavizarla. Se puede ocultar desde «Orbe voz» y cambiar de esquina en Ajustes → Generales. Las preferencias se guardan. Se conserva la activación por VICTOR y la escucha manual: mostrar el orbe no enciende el micrófono.

Las pruebas verifican banderas de Qt, ausencia de foco, esquinas dentro del área disponible, dibujo y parada del temporizador. No se certificó superposición en juegos con pantalla completa exclusiva ni sobre el escritorio seguro de Windows.

## Acceso local

Una cuenta local de propietario con nombre y contraseña de 8–256 caracteres. La app pregunta antes de crear el núcleo y abrir integraciones en el arranque normal. La verificación PBKDF2-HMAC-SHA256 con sal aleatoria y 600.000 iteraciones se ejecuta fuera del hilo de interfaz. Se mantienen compatibles las huellas de 200.000 iteraciones del borrador previo. No se almacena la contraseña original.

Recordar sesión está desactivado inicialmente. Si se activa, Windows DPAPI cifra la sesión recordada y la vincula a la huella del perfil. Cambiar contraseña, bloquear o salir invalida esa sesión. Cinco intentos incorrectos activan una espera de 30 segundos en el proceso actual. Un archivo dañado no permite crear una contraseña por encima del anterior; requiere recuperar el perfil, sin borrar historiales automáticamente.

«Bloquear app» detiene captura y voz, oculta el orbe y detiene servicios remotos y navegadores integrados. El núcleo y el registro de herramientas rechazan nuevas peticiones mientras está bloqueada la sesión y vuelven a comprobar el acceso antes de ejecutar herramientas. Una acción ya completada no se revierte; otras aplicaciones y trabajos de programación ya lanzados no se eliminan.

Cambiar contraseña está en Ajustes → Generales. El nombre local no sustituye las conexiones separadas a ChatGPT, Google o WhatsApp. Los archivos de acceso se guardan dentro de data, excluida de Git y de la distribución pública. El portátil conserva preferencias del orbe pero crea un acceso nuevo en el equipo destino.

Este bloqueo protege la entrada por la interfaz. No cifra la base de datos, no separa los historiales entre varios usuarios, no sustituye la sesión de Windows y no impide que alguien con permisos sobre el código o los archivos los modifique. Todavía no hay cuentas sincronizadas entre computadoras ni recuperación por correo: requieren definir un servidor y el tratamiento de datos personales.

## Interfaz

La navegación queda agrupada en Asistente (Inicio/Voz), Tu espacio (Historial/Memoria), Trabajo (Herramientas/Conexiones/Agentes de programación) y Configuración (Seguridad/Ajustes). Se mantienen las páginas y herramientas existentes, la paleta y las adaptaciones para ventanas estrechas. El acceso al orbe y al bloqueo queda en la barra superior; las preferencias están en Generales.

## Pruebas

35 pruebas seleccionadas superadas inicialmente: creación y verificación de acceso, sesión cifrada, rechazo de sesión falsificada, perfil dañado, espera por fallos, bloqueo de núcleo/herramientas, orbe estático, escucha e interrupción, confirmaciones de correo con datos ficticios y ciclo de vida Qt. No se enviaron correos reales ni se usaron cuentas personales. Las vistas previas de desktop_preview usan un perfil temporal ficticio.

## Mejoras generales que conviene abordar después

1. Mantener Inicio centrado en conversar y usar el panel lateral para información opcional; conservar herramientas avanzadas dentro de sus secciones.
2. Cargar navegadores, agentes y modelos únicamente cuando se necesitan, midiendo CPU y memoria del conjunto de procesos. El orbe debe seguir siendo una vista ligera, no otro asistente o motor de audio.
3. Unificar los estados «esperando VICTOR», «escuchando», «procesando» y «hablando», con tiempos medidos y errores que indiquen cómo resolverlos.
4. Si se necesitan cuentas en varias PC, diseñar autenticación de servidor y separación real de perfiles antes de sincronizar datos. Mantener las claves personales cifradas localmente y definir qué datos se sincronizan.
5. Publicar instaladores y portátiles reproducibles con pruebas de acceso, voz y cancelación antes de cada release. Probar también un equipo real de 4 GB y un juego en segundo plano.
