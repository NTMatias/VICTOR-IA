"""Adaptador de coordenadas normalizadas, sin cambiar el controlador de entrada."""
import time
from victor.errors import VictorError
from victor.security import Risk
from victor.tools.registry import Tool


def register_touch(remote):
    remote.frame_history={}
    def touch(window,x,y,frame_id,action):
        if not remote.authorized(remote.core.security.origin() or {}):
            raise VictorError('La sesión remota ya no está autorizada.')
        with remote.lock:
            geometry=remote.frame_history.get(frame_id)
        if not geometry or time.monotonic()-geometry['time']>30:
            raise VictorError('La imagen de referencia caducó. Espera una imagen actual y vuelve a tocar.')
        px=geometry['left']+min(geometry['width']-1,int(x*geometry['width']))
        py=geometry['top']+min(geometry['height']-1,int(y*geometry['height']))
        remote.core.automation.move_mouse(window,px,py)
        remote.core.security.validate_origin()
        if action=='click':
            return remote.core.automation.mouse_click(window,px,py,'left')
        return remote.pointer_batch(window,[{'kind':action,'dx':0,'dy':0}])
    remote.core.registry.register(Tool('remote_touch','Tocar una imagen reciente del escritorio: mueve el cursor y hace clic o scroll en la ventana autorizada.',
        {'type':'object','properties':{'window':{'type':'string','minLength':1,'maxLength':300},
          'x':{'type':'number','minimum':0,'maximum':1},'y':{'type':'number','minimum':0,'maximum':1},
          'frame_id':{'type':'string','minLength':1,'maxLength':40},'action':{'enum':['click','up','down']}},
         'required':['window','x','y','frame_id','action'],'additionalProperties':False},Risk.MEDIUM,touch))
