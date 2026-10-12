"""Smooth local music fades and real speech-process gate, without owner audio."""
from contextlib import contextmanager
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from victor.config import ConfigManager, ROOT
from victor.errors import Cancelled, VictorError
from victor.voice.output import VoiceOutput
from victor.voice.music_ducking import MusicDucker
from victor.gui.spotify_commands import spotify_command


class RadioVolume(unittest.TestCase):
    def test_javascript_actual_ramps_restore_user_changes_low_volume_and_cancel(self):
        node=shutil.which('node')
        if not node: self.skipTest('Node requerido')
        html=(ROOT/'victor/integrations/spotify_web.html').read_text(encoding='utf-8')
        source=html[html.index('class MusicDucking'):html.index('const ducking=')]
        script="const assert=require('node:assert/strict');function message(){};\n"+source+'''
let volume=1,paused=false,points=[];
const player={async getVolume(){return volume;},async setVolume(v){volume=v;points.push(v);},async getCurrentState(){return {paused};}};
(async()=>{
 const duck=new MusicDucking(()=>player);const t=performance.now();
 await duck.begin('lease');
 assert(performance.now()-t>=2400);assert(performance.now()-t<3500);
 assert(Math.abs(volume-.1)<1e-6);assert(points.length>=20);
 assert(points.every((v,i)=>i===0||v<=points[i-1]+1e-6));assert(points.every((v,i)=>i===0||Math.abs(v-points[i-1])<.08));
 assert.equal(await duck.displayedVolume(),1);
 await duck.setUserVolume(.35);assert.equal(volume,.1);assert.equal(await duck.displayedVolume(),.35);
 const up=performance.now();points=[];await duck.end('lease');assert(performance.now()-up>=2400);
 assert.equal(volume,.35);assert(points.every((v,i)=>i===0||v>=points[i-1]-1e-6));
 volume=.05;points=[];await duck.begin('low');assert.equal(volume,.05);await duck.end('low');assert.equal(volume,.05);
 paused=true;volume=.7;await duck.begin('paused');assert.equal(volume,.7);assert.equal(duck.lease,null);
 paused=false;volume=1;const start=duck.begin('cancel').then(()=>null,e=>e);await new Promise(r=>setTimeout(r,180));
 await duck.end('cancel');assert.match((await start).message,/cancelada/);assert.equal(volume,1);
 assert.equal(duck.original,null);console.log('Real clock smooth ramps, cancellation and user-volume restore OK');
 let release;player.getCurrentState=()=>new Promise(r=>release=r);
 const slow=duck.begin('slow').then(()=>null,e=>e);await duck.end('slow');release({paused:false});
 assert.match((await slow).message,/cancelada/);assert.equal(volume,1);assert.equal(duck.lease,null);
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'duck.js';path.write_text(script,encoding='utf-8')
            r=subprocess.run([node,str(path)],capture_output=True,text=True,encoding='utf-8',timeout=20)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_sdk_pause_ack_is_not_blocked_by_fade(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node requerido')
        html=(ROOT/'victor/integrations/spotify_web.html').read_text(encoding='utf-8')
        source=html.split('<script>')[1].split('</script>')[0]
        before=r'''
const assert=require('node:assert/strict'),elements=new Map(),listeners={},commands=[],results=[];
let volume=1,paused=false;
const delay=ms=>new Promise(r=>setTimeout(r,ms));
global.window={addEventListener:(n,f)=>listeners[n]=f};
global.document={getElementById:id=>{if(!elements.has(id))elements.set(id,{textContent:'',disabled:false,hidden:true});return elements.get(id);},createElement:()=>({}),head:{appendChild(){}}};
Object.defineProperty(globalThis,'navigator',{value:{sendBeacon:()=>true},configurable:true});
global.location={search:''};
global.fetch=async(path,opts)=>{let data={};if(path==='commands')data=commands.splice(0);if(path==='result')results.push({...JSON.parse(opts.body),time:performance.now()});return {ok:true,json:async()=>data};};
global.Spotify={Player:class{
 constructor(){this.listeners={};}addListener(n,f){this.listeners[n]=f;}disconnect(){}activateElement(){return Promise.resolve();}
 async connect(){await this.listeners.ready({device_id:'fixture'});return true;}
 async getVolume(){return volume;}async setVolume(v){volume=v;}
 async getCurrentState(){return {paused,position:0,duration:120000,track_window:{current_track:{id:'fixture',name:'Canción',artists:[],album:{images:[]}}}};}
 async pause(){paused=true;}async resume(){paused=false;}
}};
'''
        after=r'''
(async()=>{
 window.onSpotifyWebPlaybackSDKReady();await elements.get('connect').onclick();
 commands.push({id:1,action:'duck_begin',args:{lease:'fixture'}});
 await delay(350);assert(volume<1&&volume>.1);assert(!results.some(r=>r.id===1));
 const sent=performance.now();commands.push({id:2,action:'pause',args:{}});
 while(!results.some(r=>r.id===2)&&performance.now()-sent<650)await delay(10);
 const ack=results.find(r=>r.id===2);assert(ack&&ack.ok);assert(ack.time-sent<650);assert(paused);
 assert(!results.some(r=>r.id===1));
 const start=performance.now();while(!results.some(r=>r.id===1)&&performance.now()-start<3500)await delay(20);
 assert(results.find(r=>r.id===1)?.ok);assert(Math.abs(volume-.1)<1e-6);
 commands.push({id:3,action:'duck_end',args:{lease:'fixture'}});
 const up=performance.now();while(!results.some(r=>r.id===3)&&performance.now()-up<3500)await delay(20);
 assert(results.find(r=>r.id===3)?.ok);assert.equal(volume,1);listeners.pagehide();
})().catch(e=>{console.error(e);process.exitCode=1;listeners.pagehide?.();}).finally(()=>process.exit(process.exitCode||0));
'''
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'sdk.js';path.write_text(before+source+after,encoding='utf-8')
            result=subprocess.run([node,str(path)],capture_output=True,text=True,encoding='utf-8',timeout=15)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_internal_lease_restores_on_error_and_skips_disconnected_player(self):
        browser=Mock();browser.active=True;events=[]
        d=MusicDucker(lambda:browser,lambda *e:events.append(e))
        with self.assertRaises(RuntimeError):
            with d.hold(lambda:False):raise RuntimeError('speech failed')
        actions=[call.args[0] for call in browser.command.call_args_list]
        self.assertEqual(actions,['duck_begin','duck_end'])
        lease=browser.command.call_args_list[0].args[1]
        self.assertEqual(browser.command.call_args_list[1].args[1],lease)
        browser.reset_mock();browser.command.side_effect=[VictorError('control failed'),{}]
        with self.assertRaises(VictorError):
            with d.hold(lambda:False):pass
        self.assertEqual([call.args[0] for call in browser.command.call_args_list],['duck_begin','duck_end'])
        browser.reset_mock();browser.active=False
        with d.hold(lambda:False) as held:self.assertFalse(held)
        browser.command.assert_not_called()
        browser.active=True;browser.command.side_effect=None;browser.command.return_value={'ducked':False}
        with d.hold(lambda:False) as held:self.assertFalse(held)

    def test_real_child_waits_for_volume_gate_and_stop_restores(self):
        # Use the real worker parser/gate, replacing only synthesis and playback.
        script='''from victor.voice import output
from victor.voice.levels import report_meter
def fake_sapi(payload,path=None):
    if path is not None:path.write_bytes(b'x'*45)
output.speak_sapi=fake_sapi
output.play_audio=lambda path:report_meter('tts_level',.5)
output.speak_worker()
'''
        real_popen=subprocess.Popen
        def child(args,**kwargs):return real_popen([sys.executable,'-c',script],**kwargs)
        for cancel in (False,True):
            with self.subTest(cancel=cancel),tempfile.TemporaryDirectory() as folder:
                cfg=ConfigManager(Path(folder));cfg.save({'voice_enabled':True,'tts_backend':'sapi'})
                begun=threading.Event();release=threading.Event();restored=threading.Event();pcm=threading.Event();finished=threading.Event();events=[]
                class Ducker:
                    @contextmanager
                    def hold(self,cancelled):
                        begun.set()
                        try:
                            while not release.wait(.02):
                                if cancelled():raise Cancelled('cancel')
                            yield True
                        finally:restored.set()
                def emit(k,v):
                    events.append((k,v))
                    if k=='tts_level' and v==.5:pcm.set()
                with patch('victor.voice.output.subprocess.Popen',side_effect=child):
                    voice=VoiceOutput(cfg,emit);voice.music_ducker=Ducker()
                    try:
                        voice.speak('¿En qué te ayudo?',completed=finished)
                        self.assertTrue(begun.wait(5));self.assertFalse(pcm.is_set())
                        if cancel:voice.stop()
                        else:release.set()
                        self.assertTrue(finished.wait(5));self.assertTrue(restored.wait(5))
                        self.assertEqual(pcm.is_set(),not cancel)
                        self.assertFalse(any(k=='error' for k,v in events),events)
                    finally:voice.close();voice.thread.join(5)
                    self.assertFalse(voice.thread.is_alive())

    def test_loopback_paused_ack_does_not_retain_empty_music_lease(self):
        import requests
        from victor.integrations.spotify_web import SpotifyWebPlayer
        player=SpotifyWebPlayer(Mock(),Mock());url=player.start();observed=[];errors=[];actions=[]
        def hold():
            try:
                with MusicDucker(lambda:player,Mock()).hold(lambda:False) as held:observed.append(held)
            except Exception as e:errors.append(e)
        try:
            requests.post(url+'ready',json={'device':'A'*32},timeout=2).raise_for_status()
            worker=threading.Thread(target=hold);worker.start();deadline=time.monotonic()+3
            while worker.is_alive() and time.monotonic()<deadline:
                for command in requests.get(url+'commands',timeout=2).json():
                    actions.append(command['action'])
                    result={'id':command['id'],'ok':True}
                    if command['action']=='duck_begin':result['ducked']=False
                    requests.post(url+'result',json=result,timeout=2).raise_for_status()
                time.sleep(.005)
            worker.join(1)
            self.assertFalse(worker.is_alive());self.assertEqual(errors,[])
            self.assertEqual(observed,[False]);self.assertEqual(actions,['duck_begin','duck_end'])
        finally:player.stop();player.thread.join(2)


class DirectIdentity(unittest.TestCase):
    def test_manual_capture_accepts_request_without_wake(self):
        from victor.voice.input import VoiceInput
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'voice_mode':'manual'})
            events=[];voice=VoiceInput(cfg,lambda *e:events.append(e),lambda:True)
            with patch.object(voice,'listen',return_value='¿qué hora es?'):voice._run()
            self.assertEqual([v for k,v in events if k=='voice_text'],['¿qué hora es?'])

    def test_pause_variants_go_to_tool_not_model(self):
        from victor.core import VictorCore
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'action_confirmations':False})
            events=[];core=VictorCore(cfg,lambda *e:events.append(e))
            pause=Mock(return_value={'aceptada_por_api':True});core.registry.tools['spotify_pause'].function=pause
            core.ai.generate=Mock(side_effect=AssertionError('Do not ask Gemini to pause'))
            try:
                for phrase in ('ponle pausa a la canción','pon pausa a la música','pausa la canción','páusala'):
                    tool=spotify_command(phrase,state={'id':'track'})
                    self.assertEqual(tool,('spotify_pause',{}))
                    start=time.monotonic();self.assertTrue(core.submit(phrase,core.history.create(),tool))
                    while core.busy.is_set() and time.monotonic()-start<2:time.sleep(.005)
                    self.assertFalse(core.busy.is_set());self.assertLess(time.monotonic()-start,2)
                self.assertEqual(pause.call_count,4);core.ai.generate.assert_not_called()
                _,system=core.context.build(core.history.create())
                self.assertIn('VICTOR.IA',system);self.assertIn('solo el motor',system)
            finally:core.stop()

    def test_standalone_wake_never_submitted_to_ai(self):
        from victor.gui.app import GUIManager
        config=Mock();config.get.side_effect=lambda k:{'wake_word':'VICTOR','conversation_window':45}[k]
        app=SimpleNamespace(config=config,confirmation_target=None,voice_confirmation_active=lambda:False,
                            voice_input=SimpleNamespace(conversation_until=0),handle_event=Mock(),send=Mock())
        GUIManager.handle_voice_text(app,'VICTOR')
        app.send.assert_not_called();self.assertEqual(app.handle_event.call_args.args[0],'voice_wake')


if __name__=='__main__':unittest.main()
