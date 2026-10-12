"""Adaptador de coordenadas normalizadas, sin cambiar el controlador de entrada."""
import time
from victor.errors import VictorError
from victor.security import Risk
from victor.tools.registry import Tool


def decode_pointer(packet):
    """Contrato cerrado: coordenadas normalizadas sobre el contenido de la imagen."""
    import math
    if not isinstance(packet,dict) or set(packet)!={'type','seq','window','frame_id','action','x','y'}:
        raise VictorError('Evento de puntero inválido.')
    if packet['type']!='pointer_event' or type(packet['seq']) is not int or not 1<=packet['seq']<=2**31-1:
        raise VictorError('Secuencia de puntero inválida.')
    if packet['action'] not in ('move','click','up','down'):
        raise VictorError('Acción de puntero no permitida.')
    for key,limit in (('window',300),('frame_id',40)):
        if not isinstance(packet[key],str) or not 1<=len(packet[key])<=limit or any(ord(c)<32 for c in packet[key]):
            raise VictorError('Destino o imagen inválidos.')
    for key in ('x','y'):
        v=packet[key]
        if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1:
            raise VictorError('Coordenadas fuera de la imagen.')
    return dict(packet)


def map_pointer(geometry,x,y):
    return (geometry['left']+min(geometry['width']-1,int(x*geometry['width'])),
            geometry['top']+min(geometry['height']-1,int(y*geometry['height'])))


class PointerWorker:
    """Permiso MEDIO por sesión de control; valida origen e imagen en cada evento.

    No reduce el riesgo de mouse_click/move_mouse ni autoriza herramientas altas.
    El único permiso abarca el puntero y scroll; no permite pulsar VICTOR.IA
    para autorizar sus propios diálogos. Revocación/cierre descartan la cola.
    """
    def __init__(self,remote,origin):
        import queue,threading,logging
        self.remote,self.origin=remote,origin; self.cancel=threading.Event()
        self.inbox=queue.Queue(maxsize=32); self.outbox=queue.Queue(maxsize=64)
        self.last_seq=0; self.granted=False; self.window=None
        self.log=logging.getLogger('victor.remote.pointer')
        self.thread=threading.Thread(target=self.run,name='victor-remote-pointer',daemon=True)
    def submit(self,packet):
        import queue
        event=decode_pointer(packet)
        if event['seq']!=self.last_seq+1 or self.cancel.is_set() or not self.remote.authorized(self.origin):
            raise VictorError('Puntero revocado o fuera de secuencia. Reconecta la sesión.')
        try:self.inbox.put_nowait(event)
        except queue.Full:raise VictorError('Cola del puntero llena. Suelta la pantalla y vuelve a intentar.') from None
        self.last_seq=event['seq']
    def stop(self): self.cancel.set()
    def post(self,data):
        import queue
        try:self.outbox.put_nowait(data)
        except queue.Full:self.cancel.set()
    def run(self):
        import queue
        from victor.errors import check_cancel
        security=self.remote.core.security; security.set_origin(self.origin)
        try:
            while not self.cancel.is_set() and self.remote.authorized(self.origin):
                try:event=self.inbox.get(timeout=.1)
                except queue.Empty:continue
                try:
                    security.validate_origin();check_cancel(self.cancel)
                    if not self.granted or self.window!=event['window']:
                        self.post({'type':'pointer_pending','seq':event['seq'],'message':'Autoriza en el PC el control táctil de esta sesión.'})
                        security.confirm('remote_pointer_session','Controlar movimiento, clic y scroll desde este celular.\nDestino: '+event['window']+'\nEl permiso dura hasta desconectar o detener. No autoriza atajos de alto riesgo.',Risk.MEDIUM,self.cancel)
                        security.validate_origin();check_cancel(self.cancel)
                        self.granted=True;self.window=event['window']
                    with self.remote.lock:geometry=self.remote.frame_history.get(event['frame_id'])
                    if not geometry or time.monotonic()-geometry['time']>30:
                        raise VictorError('La imagen de referencia caducó. Toca una imagen actual.')
                    x,y=map_pointer(geometry,event['x'],event['y'])
                    result=self.remote.core.automation.remote_pointer(event['window'],x,y,event['action'],self.cancel,security.validate_origin)
                    self.post({'type':'pointer_ack','seq':event['seq'],'ok':True,**result})
                    self.log.info('tool=remote_pointer_session result=success risk=MEDIUM')
                except Exception as exc:
                    self.post({'type':'pointer_ack','seq':event['seq'],'ok':False,'error':str(exc) if isinstance(exc,VictorError) else 'No pude controlar el puntero. Revisa permisos y escritorio desbloqueado.'})
                    if not self.granted:self.cancel.set()
        finally:security.set_origin(None)


def install_pointer_route(app,remote,authenticate):
    import asyncio,json
    from fastapi import WebSocket
    @app.websocket('/pointer')
    async def pointer(ws:WebSocket):
        worker=None;origin=None
        try:
            origin=await authenticate(ws,False)
            if not origin:return
            worker=PointerWorker(remote,origin)
            with remote.lock:remote.pointer_workers.add(worker)
            worker.thread.start();stamp=time.monotonic();count=0
            while remote.authorized(origin) and not worker.cancel.is_set():
                while not worker.outbox.empty():await asyncio.wait_for(ws.send_json(worker.outbox.get_nowait()),3)
                try:data=json.loads(await asyncio.wait_for(ws.receive_text(),.02))
                except asyncio.TimeoutError:continue
                if data=={'type':'ping'}:await ws.send_json({'type':'pong'});continue
                now=time.monotonic()
                if now-stamp>=1:stamp=now;count=0
                count+=1
                if count>80:raise VictorError('Demasiados eventos del puntero.')
                worker.submit(data)
        except Exception as exc:
            try:await ws.send_json({'type':'disconnected','message':str(exc) if isinstance(exc,VictorError) else 'Puntero desconectado. Genera otro QR.'})
            except Exception:pass
        finally:
            if worker:
                worker.stop()
                with remote.lock:remote.pointer_workers.discard(worker)
            import anyio
            with anyio.CancelScope(shield=True):
                if worker:await asyncio.to_thread(worker.thread.join,1)
                try:await ws.close(code=1000)
                except Exception:pass


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
