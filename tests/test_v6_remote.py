import asyncio
import ctypes
import itertools
import json
import queue
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from victor.config import ConfigManager
from victor.core import VictorCore
from victor.errors import VictorError
from victor.security import Risk
from victor.integrations.local_remote import LocalRemote
from victor.integrations.keyboard_protocol import decode_event,event_risk,utf16_units,HIGH_RISK_COMBINATIONS
from victor.integrations.keyboard_worker import KeyboardWorker
from victor.integrations.keyboard_client import KEYBOARD_JS
from victor.integrations.remote_view import PAGE
from victor.system.remote_input import chord_inputs,INPUT,bind_target


def packet(seq=1, **kwargs):
    return dict(type='key_event',seq=seq,window='Editor',kind='text',text='á🙂',**kwargs)


class KeyboardCodec(unittest.TestCase):
    def test_window_title_mutation_does_not_redirect_input(self):
        binding={}
        bind_target(binding,'Editor',123,'Editor',987)
        bind_target(binding,'Editor',123,'*Editor',987)
        with self.assertRaises(VictorError):bind_target(binding,'Editor',124,'Editor',987)
        with self.assertRaises(VictorError):bind_target(binding,'Editor',123,'Editor',988)

    def test_unicode_serialization_and_native_sizes(self):
        event=decode_event(json.loads(json.dumps(packet())))
        self.assertEqual(event['text'],'á🙂');self.assertEqual(event_risk(event),Risk.MEDIUM)
        self.assertEqual(utf16_units('🙂'),[0xd83d,0xde42])
        self.assertEqual(ctypes.sizeof(INPUT),40 if ctypes.sizeof(ctypes.c_void_p)==8 else 28)

    def test_all_dangerous_combinations_all_orders(self):
        for combo in HIGH_RISK_COMBINATIONS:
            for keys in itertools.permutations(combo):
                event=decode_event(dict(type='key_event',seq=1,window='Editor',kind='keys',keys=list(keys)))
                self.assertEqual(event_risk(event),Risk.HIGH)
        self.assertEqual(event_risk(decode_event(dict(type='key_event',seq=1,window='Editor',kind='keys',keys=['Shift','Alt','F4']))),Risk.HIGH)

    def test_normal_special_keys_and_aliases(self):
        for keys in [['Enter'],['Escape'],['Backspace'],['ArrowLeft'],['ctrl','c'],['shift','right'],['alt','left']]:
            event=decode_event(dict(type='key_event',seq=1,window='Editor',kind='keys',keys=keys))
            self.assertEqual(event_risk(event),Risk.MEDIUM)
        events=chord_inputs(['ctrl','shift','esc'])
        self.assertEqual([i.u.ki.wVk for i in events],[0x11,0x10,0x1b,0x1b,0x10,0x11])
        self.assertTrue(all(i.u.ki.dwFlags&2 for i in events[3:]))

    def test_reject_bad_payload_and_control_injection(self):
        for event in [dict(packet(),seq=True),dict(packet(),text='a\nshutdown'),dict(packet(),text='\x7f'),
                      dict(packet(),text='x'*257),dict(packet(),extra='ignored?'),dict(packet(),window=''),
                      {'type':'key_event','seq':1,'window':'Editor','kind':'keys','keys':['ctrl','ctrl','a']},
                      {'type':'key_event','seq':1,'window':'Editor','kind':'keys','keys':['ctrl']},
                      {'type':'key_event','seq':1,'window':'Editor','kind':'keys','keys':['f12']},
                      dict(packet(),text='\ud800')]:
            with self.assertRaises(VictorError):decode_event(event)

    def test_browser_codec_and_ack_without_dom(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node no instalado; se requiere para prueba JavaScript')
        script=KEYBOARD_JS+r'''
const assert=require('node:assert/strict');
assert.deepEqual(VictorKeys.textEvents('á🙂\nX\tY').map(e=>e.kind),['text','keys','text','keys','text']);
assert.deepEqual(VictorKeys.editEvents('hola','Hola').map(e=>e.kind),['keys','keys','keys','keys','text']);
assert.deepEqual(VictorKeys.editEvents('🙂','').map(e=>e.keys),[['backspace']]);
let sent=[],notices=[];const socket={readyState:1,send:s=>sent.push(JSON.parse(s)),close:()=>{}};
const channel=new VictorKeys.Channel(socket,()=>'Editor',m=>notices.push(m),()=>{});
channel.push([{kind:'text',text:'uno'},VictorKeys.keyEvent('Enter')]);
assert.equal(sent.length,1);assert.equal(sent[0].seq,1);
channel.receive({type:'key_ack',seq:1,ok:true});assert.equal(sent.length,2);assert.equal(sent[1].seq,2);
channel.receive({type:'key_ack',seq:2,ok:false,error:'Foco perdido'});
assert.equal(channel.closed,true);assert.equal(channel.queue.length,0);assert.equal(sent.length,2);
console.log(JSON.stringify(VictorKeys.packet(VictorKeys.keyEvent('Delete',['alt','ctrl']),1,'Editor')));
'''
        result=subprocess.run([node,'-'],input=script,text=True,encoding='utf-8',capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(event_risk(decode_event(json.loads(result.stdout))),Risk.HIGH)
        js=PAGE.split('<script>',1)[1].split('</script>',1)[0]
        result=subprocess.run([node,'--check','-'],input=js,text=True,encoding='utf-8',capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)


class KeyboardSession(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.cfg=ConfigManager(Path(self.temp.name));self.cfg.save({'local_remote_enabled':True})
        self.events=[];self.core=VictorCore(self.cfg,lambda k,p:self.events.append((k,p)))
        self.remote=LocalRemote(self.cfg,self.core,lambda *_:None)
        self.remote.address='127.0.0.1';self.remote.ready.set()
        token=self.remote.pair(self.remote.qr_url().split('#')[1],'testclient')
        self.remote.sessions[token]['keyboard_channel']='capability'
        self.origin={'source':'local_web','session':token,'keyboard_channel':'capability'}
        self.core.automation.remote_keyboard=Mock()
        self.core.automation.prepare=Mock()

    def worker(self):
        worker=KeyboardWorker(self.remote,self.origin);worker.start()
        def close():worker.stop();worker.thread.join(2)
        self.addCleanup(close);return worker

    def test_text_no_prompt_and_no_core_turn(self):
        worker=self.worker();worker.submit(packet())
        result=worker.outbox.get(timeout=2)
        self.assertTrue(result['ok']);self.assertFalse(self.events)
        self.assertFalse(self.core.busy.is_set());self.core.automation.remote_keyboard.assert_called_once()
        self.core.automation.prepare.assert_not_called()

    def test_danger_requires_explicit_pc_and_denial_no_native_input(self):
        def deny(kind,request):
            self.assertEqual(kind,'approval');self.assertEqual(request.risk,Risk.HIGH)
            request.done.set()
        self.core.security.emit=deny
        worker=self.worker();worker.submit(dict(type='key_event',seq=1,window='Editor',kind='keys',keys=['alt','f4']))
        self.assertEqual(worker.outbox.get(timeout=2)['type'],'approval_pending')
        self.assertFalse(worker.outbox.get(timeout=2)['ok']);self.core.automation.remote_keyboard.assert_not_called()

    def test_confirmation_does_not_hold_session_lock(self):
        approval=threading.Event()
        self.core.security.emit=lambda *_:approval.set()
        worker=self.worker();worker.submit(dict(type='key_event',seq=1,window='Editor',kind='keys',keys=['ctrl','shift','esc']))
        self.assertTrue(approval.wait(1))
        self.assertTrue(self.remote.lock.acquire(timeout=.1));self.remote.lock.release()
        self.assertTrue(self.remote.authorized(self.origin));worker.stop();worker.thread.join(1)
        self.assertFalse(worker.thread.is_alive())

    def test_revocation_sequence_and_certificate_expiry(self):
        worker=self.worker();worker.submit(packet());worker.outbox.get(timeout=2)
        with self.assertRaises(VictorError):worker.submit(packet())
        self.remote.sessions[self.origin['session']]['keyboard_channel']='new'
        with self.assertRaises(VictorError):worker.submit(dict(packet(),seq=2))
        self.remote.sessions[self.origin['session']]['keyboard_channel']='capability'
        self.remote.certificate_expiry=time.time()-1
        self.assertFalse(self.remote.authorized(self.origin))

    def test_other_risks_unchanged_and_fake_capability_rejected(self):
        self.assertEqual(self.core.registry.tools['type_text'].risk,Risk.HIGH)
        self.assertEqual(self.core.registry.tools['remote_touch'].risk,Risk.MEDIUM)
        self.assertEqual(self.core.registry.tools['mouse_click'].risk,Risk.MEDIUM)
        self.core.security.set_origin(dict(self.origin,keyboard_channel='forged'))
        with self.assertRaises(VictorError):self.core.security.confirm('remote_keyboard_input','text',Risk.MEDIUM,threading.Event())
        self.core.security.set_origin(None)

    def test_websocket_serialization_ack_and_peer_binding(self):
        from fastapi.testclient import TestClient
        from starlette.websockets import WebSocketDisconnect
        # No se ejecuta la sonda ni una llamada real al escritorio.
        with patch('asyncio.create_subprocess_exec',new=AsyncMock(side_effect=OSError('test probe disabled'))):
            with TestClient(self.remote.create_app()) as client:
                headers={'origin':'https://127.0.0.1:8443'}
                self.remote.sessions[self.origin['session']]['peer']='different-device'
                with self.assertRaises(WebSocketDisconnect):
                    with client.websocket_connect('/keyboard',headers=headers) as rejected:
                        rejected.send_json({'session':self.origin['session']});rejected.receive_json()
                self.remote.sessions[self.origin['session']]['peer']='testclient'
                with client.websocket_connect('/keyboard',headers=headers) as ws:
                    ws.send_json({'session':self.origin['session']});self.assertTrue(ws.receive_json()['ready'])
                    ws.send_json(packet())
                    while True:
                        result=ws.receive_json()
                        if result['type']=='key_ack':break
                    self.assertTrue(result['ok']);self.assertEqual(result['seq'],1)
                    ws.send_json({'type':'ping'})
                    self.assertEqual(ws.receive_json()['type'],'pong')
                self.assertFalse(self.remote.keyboard_workers)

    def test_approved_danger_revalidates_before_backend(self):
        def approve(kind,request):
            request.accepted=True;request.done.set()
            self.remote.sessions[self.origin['session']]['expires']=0
        self.core.security.emit=approve
        worker=self.worker();worker.submit(dict(type='key_event',seq=1,window='Editor',kind='keys',keys=['ctrl','shift','esc']))
        worker.outbox.get(timeout=2)
        self.assertFalse(worker.outbox.get(timeout=2)['ok'])
        self.core.automation.remote_keyboard.assert_not_called()

    def test_stopping_revokes_queued_events(self):
        worker=KeyboardWorker(self.remote,self.origin)
        worker.submit(packet());worker.stop();worker.start();worker.thread.join(1)
        self.assertFalse(worker.thread.is_alive());self.core.automation.remote_keyboard.assert_not_called()


if __name__=='__main__':unittest.main()
