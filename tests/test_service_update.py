"""Servicios con fixtures; no conecta cuentas ni reproduce audio real."""
import json
import tempfile
import threading
import time
import unittest
import shutil
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch
import requests
from victor.config import ConfigManager
from victor.core import VictorCore
from victor.errors import VictorError
from victor.security import Risk
from victor.integrations.google import GoogleManager
from victor.integrations.spotify import SpotifyManager
from victor.integrations.spotify_web import SpotifyWebPlayer, decode_state
from victor.gui.service_cards import friendly_date, sender, file_type
from victor.gui.spotify_player import best_cover


class ServiceContracts(unittest.TestCase):
    def test_dates_sender_and_resolution(self):
        self.assertEqual(friendly_date('2026-10-17',True),'Sáb 17 oct 2026 · Todo el día')
        self.assertIn('oct 2026',friendly_date('2026-10-17T11:45:00-05:00'))
        self.assertNotIn('T11:',friendly_date('2026-10-17T11:45:00-05:00'))
        self.assertEqual(friendly_date('not-a-date'),'Fecha no disponible')
        self.assertEqual(sender('Uber Eats <uber@example.com>'),('Uber Eats','uber@example.com'))
        self.assertEqual(file_type('video/quicktime'),'Vídeo')
        self.assertEqual(best_cover([{'url':'small','width':64,'height':64},{'url':'large','width':640,'height':640}]),'large')
        self.assertEqual(best_cover([]),'')

    def test_google_returns_presentation_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            manager=GoogleManager(ConfigManager(Path(folder)))
            manager.request=Mock(side_effect=[{'messages':[{'id':'m1'}]}, {'threadId':'thread1','snippet':'Hola &amp; adiós','payload':{'headers':[{'name':'Date','value':'Sat, 17 Oct 2026 11:45:00 -0500'},{'name':'From','value':'Persona <p@example.com>'}]}}])
            row=manager.unread()['correos_no_leidos'][0]
            self.assertEqual(row['thread_id'],'thread1');self.assertIn('2026',row['fecha'])
            manager.request=Mock(return_value={'items':[{'summary':'Fiesta','start':{'date':'2026-10-17'},'htmlLink':'https://calendar.google.com/event','location':'Casa'}]})
            row=manager.events()['eventos'][0];self.assertTrue(row['todo_el_dia']);self.assertEqual(row['lugar'],'Casa')
            manager.request=Mock(return_value={'files':[]});manager.files('prueba')
            self.assertIn('modifiedTime',manager.request.call_args.kwargs['params']['fields'])

    def test_direct_mode_retains_validation_and_logs(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'action_confirmations':False,'security':'strict'})
            core=VictorCore(cfg,Mock());core.registry.tools['spotify_next'].function=Mock(return_value={'ok':True})
            with self.assertLogs('victor.security',level='INFO') as logs:
                for risk in Risk:core.security.confirm('fixture','test',risk,threading.Event())
            self.assertTrue(any('owner_direct_mode' in line for line in logs.output));core.emit.assert_not_called()
            from victor.gui.maintenance import audit_rows
            audit=Path(folder)/'audit.log';audit.write_text('\n'.join(logs.output),encoding='utf-8')
            self.assertIn('Directa (sin diálogo)',audit_rows(audit,{'fixture':'HIGH'})[-1])
            self.assertTrue(core.registry.execute('spotify_next',{})['ok'])
            self.assertFalse(any(call.args[0] in ('approval','remote_approval') for call in core.emit.call_args_list))
            self.assertFalse(core.registry.execute('spotify_volume',{'level':101})['ok'])
            with self.assertRaises(VictorError):core.security.path(str(Path(folder).parent/'outside.txt'))
            core.security.set_origin({'source':'local_web','session':'forged'})
            with self.assertRaises(VictorError):core.security.confirm('fixture','test',Risk.LOW,threading.Event())
            core.security.set_origin(None);cancel=threading.Event();cancel.set()
            with self.assertRaises(VictorError):core.security.confirm('fixture','test',Risk.LOW,cancel)

    def test_sdk_state_validation(self):
        state={'id':'track','name':'Canción','artists':'Artista','art_url':'','playing':True,'volume':70,'position':100,'duration':200}
        self.assertEqual(decode_state(state)['volume'],70)
        for changed in ({'volume':101},{'position':-1},{'playing':'true'},{'artists':[]},{'duration':True}):
            with self.assertRaises(ValueError):decode_state(dict(state,**changed))

    def test_sdk_controls_skip_rest_and_scope_checked(self):
        with tempfile.TemporaryDirectory() as folder:
            manager=SpotifyManager(ConfigManager(Path(folder)));manager.browser=Mock(active=True,device_id='web-device')
            manager.browser.command.return_value={'aceptada_por_api':True};manager.client=Mock()
            self.assertEqual(manager.action('volume',34)['nivel_solicitado'],34)
            manager.browser.command.assert_called_once_with('volume',{'level':34});manager.client.assert_not_called()
            manager.seek(150);manager.browser.command.assert_called_with('seek',{'position':150})
            manager._token={'access_token':'fixture','scope':'user-read-private'}
            with self.assertRaises(VictorError):manager.streaming_token()
            manager._token['scope']='streaming user-read-email';self.assertEqual(manager.streaming_token(),'fixture')

    def test_loopback_bridge_commands_ack_and_access(self):
        manager=Mock();manager.streaming_token.return_value='fixture-token';events=[]
        player=SpotifyWebPlayer(manager,lambda *e:events.append(e));url=player.start()
        try:
            self.assertEqual(requests.get(url,timeout=2).status_code,200)
            self.assertEqual(requests.get(url+'token',timeout=2).json()['token'],'fixture-token')
            self.assertEqual(requests.get(url+'token',headers={'Origin':'https://evil.example'},timeout=2).status_code,403)
            self.assertEqual(requests.get(url.replace(player.secret,'invalid'),timeout=2).status_code,403)
            self.assertEqual(requests.post(url+'ready',json={'device':'fixturedevice0000001'},timeout=2).status_code,200)
            self.assertTrue(player.active);manager.client().transfer_playback.assert_called_once_with('fixturedevice0000001',force_play=False)
            output=[];worker=threading.Thread(target=lambda:output.append(player.command('next')));start=time.perf_counter();worker.start()
            for _ in range(50):
                commands=requests.get(url+'commands',timeout=2).json()
                if commands:break
                time.sleep(.005)
            self.assertEqual(commands[0]['action'],'next')
            self.assertEqual(requests.get(url+'commands',timeout=2).json(),[])
            requests.post(url+'result',json={'id':commands[0]['id'],'ok':True},timeout=2);worker.join(2)
            self.assertFalse(worker.is_alive());self.assertTrue(output[0]['aceptada_por_api']);self.assertEqual(player.pending,{})
            print(f'SDK bridge fixture ACK: {(time.perf_counter()-start)*1000:.1f} ms (sin audio real)')
            self.assertEqual(requests.post(url+'state',json={'volume':-1},timeout=2).status_code,400)
            requests.post(url+'offline',json={},timeout=2);self.assertFalse(player.active)
        finally:
            player.stop();player.thread.join(2)
        self.assertFalse(player.thread.is_alive())

    def test_javascript_sdk_commands_and_disconnect(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node no disponible para validar JavaScript')
        html=(Path(__file__).parents[1]/'victor/integrations/spotify_web.html').read_text(encoding='utf-8')
        script=html.split('<script>')[1].split('</script>')[0]
        before=r'''
const assert=require('node:assert/strict');
const elements=new Map();const listeners={};const commands=[{id:1,action:'next',args:{}},{id:2,action:'volume',args:{level:75}}];
const calls=[],results=[];let disconnectedNetwork=false;
global.window={addEventListener:(name,fn)=>listeners[name]=fn};
global.document={getElementById:id=>{if(!elements.has(id))elements.set(id,{textContent:'',disabled:false,hidden:true});return elements.get(id);},createElement:()=>({}),head:{appendChild:()=>{}}};
Object.defineProperty(globalThis,'navigator',{value:{sendBeacon:()=>true},configurable:true});
global.fetch=async(path,opts)=>{if(disconnectedNetwork)throw Error('fixture offline');let data={};if(path==='token')data={token:'fixture'};if(path==='ready')calls.push(['ready',JSON.parse(opts.body)]);if(path==='commands')data=commands.splice(0);if(path==='result')results.push(JSON.parse(opts.body));return {ok:true,json:async()=>data};};
global.Spotify={Player:class{constructor(){this.listeners={};}addListener(n,f){this.listeners[n]=f;}disconnect(){}activateElement(){calls.push('activate');return Promise.resolve();}async connect(){await this.listeners.ready({device_id:'fixture'});return true;}async nextTrack(){calls.push('next');}async previousTrack(){calls.push('previous');}async setVolume(n){calls.push(['volume',n]);}async getVolume(){return .75;}async getCurrentState(){return null;}async pause(){}async resume(){}async togglePlay(){}async seek(){}}};
'''
        after=r'''
(async()=>{window.onSpotifyWebPlaybackSDKReady();if(!handsfree)await elements.get('connect').onclick();await new Promise(r=>setTimeout(r,180));assert(calls.includes('next'));assert.deepEqual(calls.find(c=>Array.isArray(c)&&c[0]==='volume'),['volume',.75]);assert.equal(calls.find(c=>Array.isArray(c)&&c[0]==='ready')[1].background,handsfree);assert.equal(calls.filter(c=>c==='activate').length,1);assert.deepEqual(results,[{id:1,ok:true},{id:2,ok:true}]);await elements.get('prev').onclick();assert(calls.includes('previous'));disconnectedNetwork=true;await new Promise(r=>setTimeout(r,180));assert.match(elements.get('status').textContent,/Conexión perdida/);assert.equal(elements.get('connect').disabled,false);listeners.pagehide();console.log('SDK DOM contract OK (simulado)');})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        for query in ('','?handsfree=1'):
            with self.subTest(query=query),tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'sdk_test.js';path.write_text(before+'\nglobal.location={search:'+json.dumps(query)+'};\n'+script+'\n'+after,encoding='utf-8')
                result=subprocess.run([node,str(path)],capture_output=True,text=True,encoding='utf-8',timeout=12)
                self.assertEqual(result.returncode,0,result.stderr)


class ServiceViews(unittest.TestCase):
    def test_service_cards_navigation_and_close(self):
        from PySide6.QtWidgets import QApplication
        from victor.gui.app import GUIManager
        q=QApplication.instance() or QApplication([]);q.setQuitOnLastWindowClosed(False)
        def pump(seconds=.1):
            end=time.monotonic()+seconds
            while time.monotonic()<end:q.processEvents();time.sleep(.005)
        with tempfile.TemporaryDirectory() as folder:
            app=GUIManager(ConfigManager(Path(folder)))
            try:
                app.show();pump();self.assertTrue(app.nav_buttons['windows'].isHidden())
                s=app.sections
                s.tool_result('google_unread',{'ok':True,'result':{'correos_no_leidos':[{'asunto':'Prueba de correo','remitente':'Persona <test@example.com>','resumen':'Contenido de prueba','fecha':'Sat, 17 Oct 2026 11:45:00 -0500','thread_id':'t1'}]}})
                self.assertEqual(s.google_tabs.currentIndex(),1);self.assertEqual(s.mail_results.count(),1)
                self.assertIn('Persona',s.mail_results.item(0).text());self.assertNotIn('test@example.com',s.mail_results.item(0).text())
                app.run_tool=Mock();s.open_service_item(s.mail_results.item(0));app.run_tool.assert_called_once_with('open_url',{'url':'https://mail.google.com/mail/u/0/#inbox/t1'})
                s.tool_result('google_events',{'ok':True,'result':{'eventos':[{'titulo':'Prueba de agenda','inicio':'2026-10-17','todo_el_dia':True}]}})
                self.assertIn('Todo el día',s.events.item(0).text())
                s.tool_result('google_drive_search',{'ok':True,'result':{'archivos':[{'name':'Prueba.MOV','mimeType':'video/quicktime','webViewLink':'https://drive.google.com/file/d/test','modifiedTime':'2026-10-11T12:30:00Z'}]}})
                self.assertEqual(s.google_tabs.currentIndex(),2);self.assertNotIn('https:',s.drive_results.item(0).text())
                s.tool_result('spotify_playlists',{'ok':True,'result':[{'nombre':'Playlist de prueba','id':'0'*22,'propietario':'Persona','url':'https://open.spotify.com/playlist/test'}]})
                self.assertFalse(hasattr(s,'playlists'))
                for width in (1600,420):
                    app.resize(width,900 if width==1600 else 760)
                    for page in ('google',):
                        app.navigate(page);pump(.15);self.assertEqual(app.page_widgets[page].horizontalScrollBar().maximum(),0)
                self.assertTrue(hasattr(s,'spotify_cover'));self.assertFalse(hasattr(s,'spotify_results'))
                app.spotify_command=Mock(return_value=True)
                state={'id':'one','name':'Primera','artists':'Fixture','playing':True,'volume':50,'position':0,'duration':100,'art':b'','art_url':''}
                app.player.update_state(state);app.player.action('spotify_next')
                app.handle_event('spotify_browser_state',dict(state,id='two',name='Segunda'))
                app.player.reconcile('spotify_next',{'ok':True,'result':{'aceptada_por_api':True}})
                self.assertEqual(app.player.state['name'],'Segunda')
            finally:
                app.window_transitions.close_visual_done=True;app.close();pump(3)
            self.assertTrue(app.closed_cleanly)


if __name__=='__main__':unittest.main()
