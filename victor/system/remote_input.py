"""SendInput Unicode/chords atómicos, solo para el canal de teclado LAN.

No activa ventanas por cada tecla ni utiliza la pausa global de PyAutoGUI.
Cada paquete contiene pulsar+soltar: nunca deja Ctrl/Alt/Shift retenidos.
"""
import ctypes
from ctypes import wintypes as w
from victor.errors import VictorError, check_cancel
from victor.integrations.keyboard_protocol import utf16_units
from victor.system.apps import require_windows


class KEYBDINPUT(ctypes.Structure):
    _fields_=[('wVk',w.WORD),('wScan',w.WORD),('dwFlags',w.DWORD),('time',w.DWORD),('dwExtraInfo',ctypes.c_size_t)]


class MOUSEINPUT(ctypes.Structure):
    _fields_=[('dx',w.LONG),('dy',w.LONG),('mouseData',w.DWORD),('dwFlags',w.DWORD),('time',w.DWORD),('dwExtraInfo',ctypes.c_size_t)]


class UNION(ctypes.Union):
    _fields_=[('ki',KEYBDINPUT),('mi',MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_=[('type',w.DWORD),('u',UNION)]


VK={'ctrl':0x11,'alt':0x12,'shift':0x10,'win':0x5b,'enter':0x0d,'esc':0x1b,'backspace':8,
    'tab':9,'space':0x20,'left':0x25,'up':0x26,'right':0x27,'down':0x28,'home':0x24,'end':0x23,
    'pageup':0x21,'pagedown':0x22,'delete':0x2e,'f4':0x73,'sleep':0x5f}
EXTENDED={'win','left','right','up','down','home','end','pageup','pagedown','delete'}


def key_input(key, up=False):
    vk=VK[key] if key in VK else ord(key.upper())
    flags=(1 if key in EXTENDED else 0) | (2 if up else 0)
    return INPUT(1, UNION(ki=KEYBDINPUT(vk,0,flags,0,0)))


def chord_inputs(keys):
    return [key_input(k) for k in keys] + [key_input(k,True) for k in reversed(keys)]


def foreground_title():
    require_windows()
    user=ctypes.WinDLL('user32',use_last_error=True)
    user.GetForegroundWindow.restype=w.HWND
    hwnd=user.GetForegroundWindow()
    user.GetWindowTextW.argtypes=[w.HWND,w.LPWSTR,ctypes.c_int]
    title=ctypes.create_unicode_buffer(512)
    user.GetWindowTextW(hwnd,title,len(title))
    return hwnd,title.value


def bind_target(binding, window, hwnd, title, pid):
    """Identidad de ventana, no su título mutable (Bloc de notas añade '*')."""
    if binding.get('requested') != window:
        if title != window or not hwnd or 'VICTOR.IA' in title:
            raise VictorError('Activa la ventana destino antes de escribir.')
        binding.clear();binding.update(requested=window,hwnd=hwnd,pid=pid)
    if binding['hwnd'] != hwnd or binding['pid'] != pid or 'VICTOR.IA' in title:
        raise VictorError('La ventana destino perdió el foco. Tócala de nuevo antes de escribir.')


def send_remote(window,event,cancel,validate,binding=None,reactivate=False):
    require_windows()
    import pyautogui
    pyautogui.FAILSAFE=True
    user=ctypes.WinDLL('user32',use_last_error=True)
    user.SendInput.argtypes=[w.UINT,ctypes.POINTER(INPUT),ctypes.c_int];user.SendInput.restype=w.UINT
    user.GetAsyncKeyState.argtypes=[ctypes.c_int];user.GetAsyncKeyState.restype=ctypes.c_short
    user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
    binding = {} if binding is None else binding
    def pid_of(hwnd):
        pid=w.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid));return pid.value
    if reactivate and binding.get('requested')==window:
        validate();check_cancel(cancel)
        hwnd=binding['hwnd']
        if not binding['pid'] or pid_of(hwnd)!=binding['pid']:
            raise VictorError('La ventana autorizada ya no existe.')
        user.SetForegroundWindow.argtypes=[w.HWND]
        if not user.SetForegroundWindow(hwnd):
            raise VictorError('Windows no permitió volver a la ventana autorizada tras la confirmación.')
    def guard():
        validate();check_cancel(cancel)
        pyautogui.failSafeCheck()
        hwnd,active=foreground_title()
        bind_target(binding,window,hwnd,active,pid_of(hwnd))
        if any(user.GetAsyncKeyState(vk)&0x8000 for vk in (0x10,0x11,0x12,0x5b,0x5c)):
            raise VictorError('Suelta los modificadores del teclado físico antes de escribir remotamente.')
    def send(items):
        guard()
        packet=(INPUT*len(items))(*items)
        sent=user.SendInput(len(packet),packet,ctypes.sizeof(INPUT))
        if sent != len(packet):
            # Recuperación best-effort de modificadores si Windows aceptó un prefijo.
            releases=(INPUT*4)(*[key_input(k,True) for k in ('ctrl','alt','shift','win')])
            user.SendInput(4,releases,ctypes.sizeof(INPUT))
            raise VictorError('Windows bloqueó la entrada total o parcialmente. No se reintentará; revisa aplicaciones elevadas.')
    if event['kind']=='text':
        for char in event['text']:
            items=[]
            for unit in utf16_units(char):
                items.extend([INPUT(1,UNION(ki=KEYBDINPUT(0,unit,4,0,0))),INPUT(1,UNION(ki=KEYBDINPUT(0,unit,6,0,0)))])
            send(items)
    else:
        keys=event['keys']
        if {'ctrl','alt','delete'} <= set(keys) or 'power' in keys:
            raise VictorError('Windows no permite sintetizar Ctrl+Alt+Supr ni la tecla física de encendido mediante SendInput. Usa el teclado del PC.')
        send(chord_inputs(keys))
    return {'entrada_enviada':True}
