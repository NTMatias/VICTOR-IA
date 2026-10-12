"""Contrato exclusivo del teclado LAN emparejado; no cambia herramientas locales/Telegram."""
from victor.errors import VictorError
from victor.security import Risk

MODIFIERS = ('ctrl', 'alt', 'shift', 'win')
ALIASES = {'control':'ctrl', 'escape':'esc', 'arrowleft':'left', 'arrowright':'right',
           'arrowup':'up', 'arrowdown':'down', 'del':'delete', 'supr':'delete', 'meta':'win'}
KEYS = set('abcdefghijklmnopqrstuvwxyz0123456789') | {
    'enter', 'esc', 'backspace', 'tab', 'space', 'left', 'right', 'up', 'down',
    'home', 'end', 'pageup', 'pagedown', 'delete', 'f4', 'sleep', 'power'}

# Decisión del propietario para v6: texto normal y teclas ordinarias MEDIO,
# autorizados por QR. Estos atajos (y cualquier atajo con Win) siguen ALTO.
# Se comparan conjuntos para impedir eludir la clasificación cambiando el orden.
HIGH_RISK_COMBINATIONS = frozenset({
    frozenset(('ctrl','alt','delete')),   # Pantalla de seguridad / cierre de sesión
    frozenset(('ctrl','shift','esc')),   # Administrador de tareas
    frozenset(('alt','f4')),             # Cerrar ventana / diálogo de apagado
    frozenset(('ctrl','esc')),           # Menú del sistema
    frozenset(('win','l')),             # Bloqueo
    frozenset(('win','x')),             # Menú que permite cerrar sesión/apagar/reiniciar
    frozenset(('win','r')),             # Ejecutar
    frozenset(('sleep',)), frozenset(('power',)),
})


def decode_event(data):
    """Valida antes de encolar; devuelve solo campos conocidos y normalizados."""
    if not isinstance(data, dict) or data.get('type') != 'key_event':
        raise VictorError('Evento de teclado inválido.')
    if type(data.get('seq')) is not int or not 1 <= data['seq'] <= 2**31-1:
        raise VictorError('Secuencia de teclado inválida.')
    window = data.get('window')
    if not isinstance(window, str) or not 1 <= len(window) <= 300 or any(ord(c)<32 for c in window):
        raise VictorError('Indica el título exacto de la ventana destino.')
    kind = data.get('kind')
    field = 'text' if kind == 'text' else 'keys'
    if set(data) != {'type', 'seq', 'window', 'kind', field}:
        raise VictorError('Campos de teclado no permitidos.')
    if kind == 'text':
        value = data.get('text')
        if not isinstance(value, str) or not 1 <= len(value) <= 256 or any(ord(c)<32 or 0x7f<=ord(c)<0xa0 or 0xd800<=ord(c)<=0xdfff for c in value):
            raise VictorError('Texto inválido: máximo 256 caracteres, sin controles.')
    elif kind == 'keys':
        raw = data.get('keys')
        if not isinstance(raw, list) or not 1 <= len(raw) <= 4 or not all(isinstance(k,str) for k in raw):
            raise VictorError('Teclas inválidas.')
        value = [ALIASES.get(k.lower(), k.lower()) for k in raw]
        if len(set(value)) != len(value) or any(k not in KEYS and k not in MODIFIERS for k in value):
            raise VictorError('Tecla no permitida.')
        normal = [k for k in value if k not in MODIFIERS]
        if len(normal) != 1:
            raise VictorError('Un atajo debe tener exactamente una tecla y sus modificadores.')
        value = [k for k in MODIFIERS if k in value] + normal
    else:
        raise VictorError('Tipo de entrada no permitido.')
    return {'type':'key_event', 'seq':data['seq'], 'window':window, 'kind':kind, field:value}


def event_risk(event):
    if event['kind'] == 'text':
        return Risk.MEDIUM
    combo = frozenset(event['keys'])
    return Risk.HIGH if 'win' in combo or any(danger <= combo for danger in HIGH_RISK_COMBINATIONS) else Risk.MEDIUM


def utf16_units(text):
    raw = text.encode('utf-16-le')
    return [int.from_bytes(raw[i:i+2], 'little') for i in range(0,len(raw),2)]
