"""Regresiones del diseño, latencia sin cuentas y sesión remota sin escritorio."""
import json
import math
import os
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from victor.config import ConfigManager, DEFAULTS
from victor.core import VictorCore
from victor.errors import VictorError
from victor.security import Risk
from victor.integrations.local_remote import LocalRemote
from victor.integrations.remote_touch import decode_pointer, map_pointer, PointerWorker
from victor.integrations.remote_view import POINTER_JS, PAGE
from victor.integrations.spotify import SpotifyManager


class DesignLogic(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.cfg=ConfigManager(Path(self.tmp.name));self.events=[]
        self.core=VictorCore(self.cfg,lambda k,p:self.events.append((k,p)))
        self.remote=LocalRemote(self.cfg,self.core,lambda k,p:self.events.append((k,p)))
        self.cfg.save({'local_remote_enabled':True});self.remote.ready.set();self.remote.address='127.0.0.1'
        token=self.remote.pair(self.remote.qr_url().split('#')[1],'testclient')
        self.origin={'source':'local_web','session':token,'user_id':'LAN testclient'}
    def tearDown(self):
        self.remote.stop()
        if self.remote.capture_thread:self.remote.capture_thread.join(2)
        self.tmp.cleanup()
    def packet(self,seq=1,**changes):
        return dict(type='pointer_event',seq=seq,window='Escritorio completo',frame_id='f',action='move',x=.75,y=.5,**changes)
    def test_pointer_mapping_and_validation(self):
        g={'left':-1920,'top':-200,'width':3840,'height':1200}
        self.assertEqual(map_pointer(g,.75,.5),(960,400));self.assertEqual(map_pointer(g,1,1),(1919,999))
        self.assertEqual(decode_pointer(self.packet())['action'],'move')
        for key,val in [('seq',True),('x',math.nan),('y',2),('action','shutdown'),('window',''),('type','key_event')]:
            event=self.packet();event[key]=val
            with self.subTest(key=key),self.assertRaises(VictorError):decode_pointer(event)
        event=self.packet();event['command']='calc'
        with self.assertRaises(VictorError):decode_pointer(event)
    def test_keepalive_never_resurrects_revocation(self):
        entry=self.remote.sessions[self.origin['session']];entry['expires']=time.monotonic()+1
        self.assertTrue(self.remote.keep_alive(self.origin));self.assertGreater(entry['expires'],time.monotonic()+590)
        entry['expires']=0;self.assertFalse(self.remote.keep_alive(self.origin));self.assertEqual(entry['expires'],0)
    def test_stream_grant_has_no_sixty_second_cutoff(self):
        self.core.security.set_origin(self.origin)
        with patch('threading.Thread') as t:
            t.return_value.is_alive.return_value=False;result=self.remote.start_stream()
        self.remote.capture_thread=None
        self.assertEqual(self.remote.sessions[self.origin['session']]['stream_until'],math.inf)
        self.assertIn('Mientras',result['pantalla_autorizada'])
        self.assertEqual(self.core.registry.tools['remote_screen_stream'].risk,Risk.MEDIUM)
    def test_pointer_worker_one_medium_grant_and_no_core_busy(self):
        approvals=[]
        def approve(kind,request):
            approvals.append(request.risk);request.accepted=True;request.done.set()
        self.core.security.emit=approve;self.core.busy.set()
        self.core.automation.remote_pointer=Mock(return_value={'window':'Editor','owner':'123'})
        self.remote.frame_history['f']={'left':0,'top':0,'width':100,'height':100,'time':time.monotonic()}
        worker=PointerWorker(self.remote,self.origin);worker.thread.start()
        try:
            for seq in (1,2):worker.submit(self.packet(seq))
            deadline=time.monotonic()+2
            while self.core.automation.remote_pointer.call_count<2 and time.monotonic()<deadline:time.sleep(.01)
            self.assertEqual(approvals,[Risk.MEDIUM]);self.assertEqual(self.core.automation.remote_pointer.call_count,2)
            self.cfg.save({'remote_block_all':True})
            with self.assertRaises(VictorError):worker.submit(self.packet(3))
        finally:worker.stop();worker.thread.join(2)
        self.assertFalse(worker.thread.is_alive())
        self.assertEqual(self.core.registry.tools['mouse_click'].risk,Risk.MEDIUM)
        self.assertEqual(self.core.registry.tools['type_text'].risk,Risk.HIGH)
    def test_pointer_websocket_auth_ack_and_cleanup(self):
        from fastapi.testclient import TestClient
        from starlette.websockets import WebSocketDisconnect
        self.core.automation.remote_pointer=Mock(return_value={'window':'Editor','owner':'123'})
        def approve(kind,request):request.accepted=True;request.done.set()
        self.core.security.emit=approve
        self.remote.frame_history['f']={'left':0,'top':0,'width':100,'height':100,'time':time.monotonic()}
        with TestClient(self.remote.create_app()) as client:
            self.assertEqual(client.get('/assets/inter.ttf').status_code,200)
            with client.websocket_connect('/pointer',headers={'origin':'https://127.0.0.1:8443'}) as ws:
                ws.send_json({'session':self.origin['session']});self.assertTrue(ws.receive_json()['ready'])
                ws.send_json(self.packet())
                first=ws.receive_json();second=ws.receive_json()
                self.assertEqual(first['type'],'pointer_pending');self.assertTrue(second['ok'])
                ws.send_json({'type':'ping'});self.assertEqual(ws.receive_json()['type'],'pong')
        self.assertFalse(self.remote.pointer_workers)
    def test_spotify_warm_action_only_one_network_write(self):
        manager=SpotifyManager(self.cfg);client=Mock();client.current_user.return_value={'product':'premium'}
        client.devices.return_value={'devices':[{'id':'pc','type':'Computer','is_active':True}]}
        with patch.object(manager,'client',return_value=client):
            manager.action('volume',10);manager.action('volume',30);manager.action('next')
        self.assertEqual(client.current_user.call_count,1);self.assertEqual(client.devices.call_count,1)
        self.assertEqual(client.volume.call_count,2);self.assertEqual(client.next_track.call_count,1)
        client.current_playback.assert_not_called()
    def test_spotify_observed_device_respects_configured_pc(self):
        manager=SpotifyManager(self.cfg)
        with patch.dict(os.environ,{'SPOTIPY_DEVICE_ID':'my-pc'}):
            manager.observe_playback({'device':{'id':'other','type':'Computer'}});self.assertEqual(manager._device_until,0)
            manager.observe_playback({'device':{'id':'my-pc','type':'Computer'}});self.assertEqual(manager._device_id,'my-pc')
    def test_client_reuses_http_session_per_thread(self):
        manager=SpotifyManager(self.cfg);manager._token={'access_token':'fixture','expires_at':time.time()+3600}
        with patch('spotipy.Spotify') as sdk:
            self.assertIs(manager.client(),manager.client());sdk.assert_called_once()
            manager._token={'access_token':'changed','expires_at':time.time()+3600};manager.client();self.assertEqual(sdk.call_count,2)
    def test_pointer_javascript_coalesces_moves_and_letterbox(self):
        js=POINTER_JS+r"""
const assert=require('assert');
let sent=[];const socket={readyState:1,send:s=>sent.push(JSON.parse(s)),close(){this.readyState=3;}};
const p=new PointerChannel(socket,()=>{},()=>{});
const event={window:'Escritorio completo',frame_id:'f',action:'move',x:.1,y:.2};p.push(event);
for(let i=0;i<30;i++)p.push({...event,x:i/30});
assert.equal(sent.length,1);assert.equal(p.queue.length,0);
socket.onmessage({data:JSON.stringify({type:'pointer_ack',seq:1,ok:true})});assert.equal(sent.length,2);assert.equal(sent[1].x,29/30);
assert.deepEqual(imagePosition(200,150,{left:0,top:0,width:400,height:300},1920,1080),{x:.5,y:.5});
assert.equal(imagePosition(200,5,{left:0,top:0,width:400,height:300},1920,1080),null);
p.fail('done');assert.equal(p.pending,null);assert.equal(p.queue.length,0);
"""
        result=subprocess.run(['node','-e',js],capture_output=True,text=True,encoding='utf-8',timeout=5)
        self.assertEqual(result.returncode,0,result.stderr[-500:])

    def test_seek_playlist_validation_and_medium_confirmation(self):
        requests=[]
        def reject(kind,request):
            if kind=='approval':requests.append(request);request.accepted=False;request.done.set()
        self.core.security.emit=reject
        client=Mock();self.core.spotify.client=Mock(return_value=client);self.core.spotify.device=Mock(return_value='pc')
        for name,args in [('spotify_seek',{'position':1000}),('spotify_playlist_play',{'playlist_id':'A'*22})]:
            result=self.core.registry.execute(name,args)
            self.assertFalse(result['ok']);self.assertEqual(requests[-1].risk,Risk.MEDIUM)
        client.seek_track.assert_not_called();client.start_playback.assert_not_called()
        count=len(requests)
        for name,args in [('spotify_seek',{'position':-1}),('spotify_playlist_play',{'playlist_id':'https://example.com'})]:
            self.assertEqual(self.core.registry.execute(name,args)['error_code'],'schema_validation')
        self.assertEqual(len(requests),count)
        def approve(kind,request):
            if kind=='approval':request.accepted=True;request.done.set()
        self.core.security.emit=approve
        self.assertTrue(self.core.registry.execute('spotify_seek',{'position':1000})['ok'])
        client.seek_track.assert_called_once_with(1000,device_id='pc')
        self.assertTrue(self.core.registry.execute('spotify_playlist_play',{'playlist_id':'A'*22})['ok'])
        client.start_playback.assert_called_once_with(device_id='pc',context_uri='spotify:playlist:'+'A'*22)


class DesignGUI(unittest.TestCase):
    def test_sections_font_buttons_and_pending_approval(self):
        from PySide6.QtWidgets import QApplication, QPushButton
        from PySide6.QtGui import QFontDatabase
        from tests.gui_support import authenticated_gui as GUIManager
        from victor.security import Approval
        q=QApplication.instance() or QApplication([]);q.setQuitOnLastWindowClosed(False)
        def pump(seconds=.05):
            end=time.monotonic()+seconds
            while time.monotonic()<end:q.processEvents();time.sleep(.005)
        with tempfile.TemporaryDirectory() as folder:
            app=GUIManager(ConfigManager(Path(folder)))
            try:
                app.show();pump(.2);self.assertIn('Inter',QFontDatabase.families())
                self.assertTrue({'home','spotify','whatsapp','ia','codex','claude'}.issubset(app.page_widgets))
                fields={'models' if k.startswith('model:') else k for k in app.settings.fields}
                self.assertEqual(fields,set(DEFAULTS)-{'auth_methods','account_models','gemini_account_enabled','desktop_orb_position'})
                for key in app.page_widgets:app.navigate(key);pump(.015);self.assertIs(app.pages.currentWidget(),app.page_widgets[key])
                app.run_tool=Mock();app.sections.file_source.setText('example.txt');app.sections.select_file('delete_file');app.sections.execute_file()
                app.run_tool.assert_called_once_with('delete_file',{'path':'example.txt'})
                app.run_tool.reset_mock();app.settings.analyze_from_settings('Lee el texto')
                self.assertIs(app.pages.currentWidget(),app.page_widgets['vision'])
                app.run_tool.assert_called_once_with('analyze_screen',{'question':'Lee el texto','region':None})
                app.sections.tool_result('analyze_screen',{'ok':True,'result':'Lectura de prueba'})
                self.assertEqual(app.sections.vision_output.toPlainText(),'Lectura de prueba')
                app.config.save({'telegram_allowed_ids':[123,456]});app.sections.refresh_connections()
                app.sections.telegram_users.setCurrentRow(0)
                from PySide6.QtWidgets import QMessageBox
                with patch('victor.gui.panels.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):app.sections.remove_telegram_user()
                self.assertEqual(app.config.get('telegram_allowed_ids'),[456])
                request=Approval('delete_file','example.txt',Risk.HIGH);app.handle_event('approval',request);pump()
                self.assertTrue(app.approval_dialogs[-1].isVisible());self.assertFalse(request.done.is_set())
                app.approval_dialogs[-1].reject();self.assertFalse(request.accepted)
                app.navigate('home');app.resize(420,760);pump(.2);self.assertLessEqual(app.width(),440)
                self.assertGreater(app.entry.width(),85)
                self.assertLessEqual(max(b.width() for b in app.quick_buttons)-min(b.width() for b in app.quick_buttons),2)
                app.config.save({'theme':'Light'});app.refresh_config();pump()
                bubble=app.append_message('assistant','Contraste claro')
                self.assertIn('#20242F',bubble.styleSheet());self.assertTrue(app.dials['cpu'].property('light'))
            finally:
                app.close();pump(8)
            self.assertTrue(app.closed_cleanly)
    def test_button_command_worker_does_not_call_ai(self):
        from victor.gui.widgets import ToolWorker
        with tempfile.TemporaryDirectory() as folder:
            core=VictorCore(ConfigManager(Path(folder)),lambda *args:None)
            core.ai.generate=Mock();core.busy.set();events=[]
            core.registry.tools['get_system_info'].function=lambda:{'ram':55}
            worker=ToolWorker(core,lambda *args:events.append(args))
            try:
                worker.submit('get_system_info',{});deadline=time.monotonic()+2
                while not any(e[0]=='panel_result' for e in events) and time.monotonic()<deadline:time.sleep(.01)
                result=next(e[1][1] for e in events if e[0]=='panel_result');self.assertTrue(result['ok']);core.ai.generate.assert_not_called()
            finally:worker.stop();worker.thread.join(2)

if __name__=='__main__':unittest.main()
