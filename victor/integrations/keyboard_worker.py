"""Cola de teclado propia; no ocupa VictorCore ni el trabajador del ratón."""
import logging
import queue
import threading
import time
from victor.errors import VictorError, check_cancel
from victor.security import Risk
from victor.integrations.keyboard_protocol import decode_event, event_risk


class KeyboardWorker:
    def __init__(self, remote, origin):
        self.remote,self.origin=remote,origin
        self.cancel=threading.Event()
        self.inbox=queue.Queue(maxsize=128)
        self.outbox=queue.Queue(maxsize=256)
        self.last_seq=0
        self.binding={}
        self.thread=threading.Thread(target=self.run,name='victor-remote-keyboard',daemon=True)
        self.log=logging.getLogger('victor.remote.keyboard')

    def start(self):
        self.thread.start()

    def submit(self, packet):
        event=decode_event(packet)
        if event['seq'] != self.last_seq+1:
            raise VictorError('Secuencia repetida o fuera de orden. Reconecta el teclado; no se repetirá la entrada.')
        if self.cancel.is_set() or not self.remote.authorized(self.origin):
            raise VictorError('La sesión de teclado caducó o fue revocada.')
        try:self.inbox.put_nowait(event)
        except queue.Full:raise VictorError('Cola de teclado llena. Detén la escritura y reconecta.') from None
        self.last_seq=event['seq']

    def post(self, result):
        try:self.outbox.put_nowait(result)
        except queue.Full:self.cancel.set()

    def stop(self):
        self.cancel.set()

    def run(self):
        security=self.remote.core.security
        security.set_origin(self.origin)
        try:
            while not self.cancel.is_set() and self.remote.authorized(self.origin):
                try:event=self.inbox.get(timeout=.1)
                except queue.Empty:continue
                risk=event_risk(event)
                started=time.monotonic()
                try:
                    security.validate_origin();check_cancel(self.cancel)
                    if risk==Risk.HIGH:self.post({'type':'approval_pending','seq':event['seq'],'message':'Atajo de alto riesgo: confirma EJECUTAR en el PC.'})
                    security.confirm('remote_keyboard_input',
                                     'Ventana: '+event['window']+'\n'+('Atajo: '+' + '.join(event['keys']) if event['kind']=='keys' else 'Escritura de texto en sesión QR'),
                                     risk,self.cancel)
                    security.validate_origin();check_cancel(self.cancel)
                    if risk==Risk.HIGH and not self.binding:
                        self.remote.core.automation.prepare(event['window'])
                    self.remote.core.automation.remote_keyboard(event['window'],event,self.cancel,security.validate_origin,
                                                               self.binding,risk==Risk.HIGH)
                    self.post({'type':'key_ack','seq':event['seq'],'ok':True})
                    self.log.info('tool=remote_keyboard_input result=success risk=%s seconds=%.3f',risk.name,time.monotonic()-started)
                except Exception as exc:
                    message=str(exc) if isinstance(exc,VictorError) else 'No se pudo enviar la entrada. Revisa la ventana y los permisos de Windows.'
                    self.post({'type':'key_ack','seq':event['seq'],'ok':False,'error':message})
                    self.log.info('tool=remote_keyboard_input result=failed risk=%s type=%s',risk.name,type(exc).__name__)
                    # No reproducir cola tras fallo parcial/cambio de foco.
                    self.cancel.set()
        finally:
            security.set_origin(None)
