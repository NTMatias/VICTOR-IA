import base64
from email import message_from_bytes
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch
from victor.config import ConfigManager
from victor.core import VictorCore
from victor.errors import VictorError
from victor.integrations.local_remote import LocalRemote
from victor.gui.widgets import display_text


class ServicesV3(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.config=ConfigManager(Path(self.folder.name))
        self.events=[]
        self.core=VictorCore(self.config,lambda k,p:self.events.append((k,p)))
        self.remote=LocalRemote(self.config,self.core,lambda k,p:self.events.append((k,p)))
        self.config.save({'local_remote_enabled':True})
        self.remote.address='127.0.0.1';self.remote.ready.set()

    def session(self):
        code=self.remote.qr_url().split('#')[1]
        token=self.remote.pair(code,'testclient')
        return {'source':'local_web','session':token,'user_id':'LAN testclient'}

    def test_pairing_revocation_and_expiration(self):
        code=self.remote.qr_url().split('#')[1]
        token=self.remote.pair(code,'testclient')
        with self.assertRaises(VictorError):self.remote.pair(code,'attacker')
        origin={'source':'local_web','session':token}
        self.assertTrue(self.core.security.origin_authorized(origin))
        self.config.save({'remote_block_all':True})
        self.assertFalse(self.core.security.origin_authorized(origin))
        self.config.save({'remote_block_all':False})
        self.remote.sessions[token]['expires']=0
        self.assertFalse(self.remote.authorized(origin))

    def test_local_high_risk_requires_pc(self):
        origin=self.session();self.core.security.set_origin(origin)
        calls=[]
        def deny(kind,request):
            calls.append(kind);request.done.set()
        self.core.security.emit=deny
        result=self.core.registry.execute('type_text',{'window':'Editor','text':'hola'})
        self.assertFalse(result['ok']);self.assertEqual(calls,['approval'])

    def test_pointer_batch_stays_inside_window(self):
        origin=self.session();self.core.security.set_origin(origin)
        gui=Mock();gui.position.return_value=(20,20)
        target=Mock(isActive=True,left=0,right=100,top=0,bottom=100)
        self.core.automation.prepare=Mock(return_value=(gui,target))
        def approve(kind,request):request.accepted=True;request.done.set()
        self.core.security.emit=approve
        result=self.core.registry.execute('remote_pointer_batch',{'window':'Editor','events':[{'kind':'move','dx':500,'dy':-500}]})
        self.assertTrue(result['ok']);gui.moveTo.assert_called_once_with(99,0,duration=.05)
        self.config.save({'local_remote_enabled':False})
        self.assertFalse(self.core.registry.execute('remote_pointer_batch',{'window':'Editor','events':[{'kind':'left','dx':0,'dy':0}]})['ok'])
        gui.click.assert_not_called()

    def test_websocket_routes_only_allowed_tools(self):
        from fastapi.testclient import TestClient
        from starlette.websockets import WebSocketDisconnect
        with TestClient(self.remote.create_app()) as client:
            with self.assertRaises(WebSocketDisconnect):
                with client.websocket_connect('/control',headers={'origin':'https://evil.example'}):pass
            code=self.remote.qr_url().split('#')[1]
            with client.websocket_connect('/control',headers={'origin':'https://127.0.0.1:8443'}) as ws:
                ws.send_json({'code':code});session=ws.receive_json()['session']
                ws.send_json({'tool':'run_terminal','args':{'command':'hostname'}})
                self.assertIn('no permitida',ws.receive_json()['error'])
                time.sleep(.5)
                ws.send_json({'tool':'press_keys','args':{'window':'Editor','keys':['enter']}})
                deadline=time.monotonic()+2
                while not any(k=='remote_command' for k,p in self.events) and time.monotonic()<deadline:time.sleep(.02)
                command=next(p for k,p in self.events if k=='remote_command')
                self.assertEqual(command['origin']['session'],session)
                self.assertEqual(command['tool'][0],'press_keys')
                self.remote.reply(command['origin'],'Prueba',done=True)
                self.assertTrue(ws.receive_json()['done'])
            self.assertNotIn(session,self.remote.sessions)

    def test_screen_worker_produces_jpeg_and_stops(self):
        from PIL import Image
        origin=self.session();self.core.security.set_origin(origin)
        with patch('mss.MSS',side_effect=OSError('test')),patch('PIL.ImageGrab.grab',return_value=Image.new('RGB',(64,64))):
            self.remote.start_stream()
            deadline=time.monotonic()+2
            while not self.remote.frames and time.monotonic()<deadline:time.sleep(.02)
            self.assertTrue(self.remote.frames[origin['session']][1].startswith(b'\xff\xd8'))
            self.remote.stop();self.remote.capture_thread.join(2)
        self.assertFalse(self.remote.capture_thread.is_alive())

    def test_google_read_and_drive_escape(self):
        self.core.google.request=Mock(side_effect=[{'messages':[{'id':'a'}]}, {'payload':{'headers':[{'name':'Subject','value':'Reunión'}]},'snippet':'Contenido real de prueba'}])
        self.assertEqual(self.core.google.unread()['correos_no_leidos'][0]['asunto'],'Reunión')
        self.core.google.request=Mock(return_value={'files':[]})
        self.core.google.files("O'Reilly")
        self.assertIn("O\\'Reilly",self.core.google.request.call_args.kwargs['params']['q'])

    def test_google_send_confirmation_and_mime(self):
        self.core.google.request=Mock(return_value={'id':'sent-test'})
        def deny(kind,request):request.done.set()
        self.core.security.emit=deny
        args={'to':'example@example.com','subject':'Prueba','body':'Texto'}
        self.assertFalse(self.core.registry.execute('google_send_email',args)['ok'])
        self.core.google.request.assert_not_called()
        def approve(kind,request):
            self.assertEqual(request.risk.name,'HIGH');request.accepted=True;request.done.set()
        self.core.security.emit=approve
        self.assertTrue(self.core.registry.execute('google_send_email',args)['ok'])
        raw=self.core.google.request.call_args.kwargs['json']['raw']
        self.assertEqual(message_from_bytes(base64.urlsafe_b64decode(raw))['To'],'example@example.com')

    def test_google_missing_credentials_clear(self):
        with patch.dict('os.environ',{'GOOGLE_CLIENT_ID':'','GOOGLE_CLIENT_SECRET':''}):
            with self.assertRaisesRegex(VictorError,'GOOGLE_CLIENT_ID'):
                self.core.google.authorize(threading.Event())

    def test_structured_result_is_presented_without_json(self):
        text=display_text('{"solicitud_apertura":"Google","ventana_visible":false}')
        self.assertNotIn('{',text);self.assertIn('No',text)
        self.assertNotIn('{',display_text('[Resultado de herramienta open_url]\n{"ok":true,"result":{"url":"https://example.com"}}'))
        self.assertNotIn('{',display_text('{"solicitud_apertura":'))
