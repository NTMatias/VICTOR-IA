"""Nombres y argumentos de herramientas para presentación; no cambia permisos."""
import json
import re

LABELS = {
 'open_application':'🚀 Abrir aplicación','close_application':'🛑 Cerrar aplicación','open_url':'🌐 Abrir página web',
 'open_file':'📂 Abrir archivo o carpeta','create_folder':'📁 Crear carpeta','list_files':'📂 Consultar archivos',
 'create_file':'📝 Crear archivo','move_file':'📁 Mover archivo','copy_file':'📁 Copiar archivo',
 'rename_file':'✏️ Renombrar archivo','delete_file':'🗑️ Eliminar archivo','get_system_info':'💻 Consultar el equipo',
 'control_volume':'🔊 Ajustar volumen','set_volume':'🔊 Ajustar volumen','adjust_volume':'🔊 Cambiar volumen',
 'open_settings':'⚙️ Abrir ajustes de Windows','run_terminal':'⚠️ Ejecutar diagnóstico',
 'take_screenshot':'🖥️ Capturar pantalla','active_window':'🪟 Consultar ventana activa','analyze_screen':'🔍 Analizar pantalla',
 'search_web':'🔎 Buscar en Internet','mouse_click':'🖱️ Hacer clic','move_mouse':'🖱️ Mover el puntero',
 'type_text':'⌨️ Escribir texto','press_keys':'⌨️ Pulsar teclas','remember':'🧠 Guardar recuerdo',
 'recall':'🧠 Consultar recuerdos','forget':'🧠 Olvidar recuerdo','share_screen_telegram':'📱 Enviar captura por Telegram',
 'spotify_play':'🎵 Spotify: reproducir','spotify_resume':'▶️ Spotify: continuar reproducción',
 'spotify_pause':'⏸️ Spotify: pausar','spotify_next':'⏭️ Spotify: siguiente canción',
 'spotify_previous':'⏮️ Spotify: canción anterior','spotify_volume':'🎵 Spotify: ajustar volumen',
 'spotify_current_track':'🎵 Spotify: canción actual','spotify_playlists':'🎵 Spotify: mis listas',
 'spotify_seek':'Spotify: posición de reproducción','spotify_playlist_play':'Spotify: reproducir lista',
 'spotify_item_play':'Spotify: reproducir selección','spotify_search':'Spotify: buscar',
 'spotify_collection':'Spotify: consultar colección',
 'google_unread':'📧 Google: correos sin leer','google_events':'📅 Google: próximos eventos',
 'google_drive_search':'📁 Google: buscar archivos','google_send_email':'📧 Google: enviar correo',
 'remote_pointer_batch':'🖱️ Control remoto: ratón','remote_touch':'🖱️ Control remoto: tocar pantalla',
 'remote_key_event':'⌨️ Control remoto: teclado','remote_screen_stream':'📱 Control remoto: ver pantalla',
 'remote_keyboard_input':'Teclado remoto emparejado','remote_pointer_session':'Control táctil de la sesión',
 'youtube_play_first':'▶️ YouTube: reproducir primer resultado',
}
KEYS = {'level':'Nivel','query':'Búsqueda','name':'Nombre','path':'Ruta','source':'Origen','destination':'Destino',
        'window':'Ventana','keys':'Teclas','button':'Botón','text':'Texto','to':'Destinatario','subject':'Asunto','body':'Mensaje',
        'region':'Región','question':'Pregunta','key':'Clave','value':'Contenido','events':'Acciones','kind':'Acción',
        'action':'Cambio','command':'Diagnóstico','x':'Posición horizontal','y':'Posición vertical',
        'dx':'Desplazamiento horizontal','dy':'Desplazamiento vertical','frame_id':'Imagen de referencia'}
VALUES={'left':'izquierdo','right':'derecho','double':'doble clic','up':'arriba','down':'abajo','mute':'silenciar',
        'move':'mover','enter':'Intro','esc':'Escape','backspace':'Retroceso','delete':'Suprimir','ctrl':'Control','shift':'Mayús'}

def friendly_name(name):
    return LABELS.get(name,str(name).replace('_',' ').replace('-',' ').capitalize())

def plain(value):
    if isinstance(value,dict):return '; '.join(f'{KEYS.get(k,k.replace("_"," ").capitalize())}: {plain(v)}' for k,v in value.items())
    if isinstance(value,list):return ' · '.join(plain(v) for v in value) or 'Ninguno'
    if value is None:return 'Pantalla completa / sin valor adicional'
    if isinstance(value,bool):return 'Sí' if value else 'No'
    return VALUES.get(str(value),str(value))

def argument_text(name,args):
    if name in ('control_volume','set_volume','spotify_volume') and 'level' in args:
        return f"Nivel: {args['level']} de 100"
    if name in ('open_application','close_application') and 'name' in args:
        return 'Aplicación: '+str(args['name'])
    if name in ('move_file','copy_file'):
        return 'Origen: '+str(args.get('source',''))+'\nDestino: '+str(args.get('destination',''))
    if name=='google_send_email':
        return 'Destinatario: '+str(args.get('to',''))+'\nAsunto: '+str(args.get('subject',''))+'\nMensaje:\n'+str(args.get('body',''))
    return '\n'.join(f'{KEYS.get(k,k.replace("_"," ").capitalize())}: {plain(v)}' for k,v in args.items()) or 'Sin parámetros adicionales.'

def confirmation_details(title,details):
    # SecurityManager conserva el documento exacto; aquí solo cambia su representación.
    start=details.find('{')
    if start>=0:
        try:
            args,end=json.JSONDecoder().raw_decode(details[start:])
            if isinstance(args,dict):
                return details[:start].strip()+'\n\n'+argument_text(title,args)+details[start+end:]
        except ValueError:pass
    return readable_names(details)

def readable_names(text):
    for name in sorted(LABELS,key=len,reverse=True):
        text=re.sub(r'\b'+re.escape(name)+r'\b',lambda _:LABELS[name],str(text))
    return text
