"""Biblioteca, selección exacta, paginación y UI; datos simulados, sin audio real."""
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
from victor.integrations.spotify import SpotifyManager, catalog_item
from victor.integrations.spotify_web import SpotifyWebPlayer
from victor.errors import VictorError

ID='A'*22
ID2='B'*22


def track(identifier=ID, **values):
    return dict(id=identifier,uri='spotify:track:'+identifier,type='track',name='Canción de prueba',
                artists=[{'name':'Artista de prueba'}],duration_ms=185000,
                album={'images':[{'url':'https://i.scdn.co/image/fixture','width':640,'height':640}]},**values)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.manager=SpotifyManager(ConfigManager(Path(self.folder.name)))
        self.client=Mock();self.manager.client=Mock(return_value=self.client)

    def test_search_never_plays_and_paginates(self):
        self.client.search.return_value={'tracks':{'items':[track(),None],'next':'next'},'shows':{'items':[{'id':ID2,'type':'show','name':'Podcast','publisher':'Autor'}]}}
        result=self.manager.search_catalog('prueba','all',10)
        self.assertEqual(result['next_offset'],20);self.assertEqual([r['kind'] for r in result['items']],['track','show'])
        self.assertEqual(result['items'][0]['image'],'https://i.scdn.co/image/fixture')
        self.client.start_playback.assert_not_called();self.client.search.assert_called_once_with(q='prueba',type='track,playlist,show,episode,album',limit=10,offset=10)

    def test_playlist_order_nulls_duplicates_and_both_response_formats(self):
        self.client.playlist_items.return_value={'items':[{'track':track()},None,{'item':track()}],'next':'next','total':80}
        result=self.manager.collection_items('playlist',ID2,50)
        self.assertEqual(result['next_offset'],53);self.assertEqual([r['position'] for r in result['items']],[50,52])
        self.assertEqual(result['items'][0]['context'],'spotify:playlist:'+ID2)
        self.client.start_playback.assert_not_called()
        self.client.playlist_items.assert_called_once_with(ID2,limit=50,offset=50)

    def test_show_album_and_unavailable(self):
        self.client.show_episodes.return_value={'items':[{'id':ID,'uri':'spotify:episode:'+ID,'type':'episode','name':'Episodio'}],'next':None,'total':1}
        row=self.manager.collection_items('show',ID2,0)['items'][0]
        self.assertEqual(row['context'],'');self.assertEqual(row['kind'],'episode')
        self.client.album_tracks.return_value={'items':[track(is_local=True)],'next':None,'total':1}
        self.assertFalse(self.manager.collection_items('album',ID2,0)['items'][0]['available'])
        self.assertFalse(catalog_item(track(is_playable=False),'track')['available'])

    def test_exact_selection_preserves_playlist_position(self):
        self.manager.device=Mock(return_value='web-device')
        self.manager.play_item('spotify:track:'+ID,'spotify:playlist:'+ID2,52)
        self.client.start_playback.assert_called_once_with(device_id='web-device',context_uri='spotify:playlist:'+ID2,offset={'position':52})
        self.client.search.assert_not_called()
        self.manager.play_item('spotify:episode:'+ID,'',0)
        self.client.start_playback.assert_called_with(device_id='web-device',uris=['spotify:episode:'+ID])
        with self.assertRaises(VictorError):self.manager.play_item('file:bad','',0)

    def test_playlist_denied_reports_actual_restriction(self):
        from spotipy.exceptions import SpotifyException
        self.client.playlist_items.side_effect=SpotifyException(403,-1,'sensitive response')
        with self.assertRaisesRegex(VictorError,'propietario o colaborador') as caught:self.manager.collection_items('playlist',ID,0)
        self.assertNotIn('sensitive',str(caught.exception))

    def test_browser_uses_registry_and_rejects_arbitrary_tools(self):
        core=VictorCore(self.manager.config,Mock());core.config.save({'action_confirmations':False})
        core.registry.tools['spotify_search'].function=Mock(return_value={'items':[]})
        core.registry.tools['spotify_item_play'].function=Mock(return_value={'aceptada_por_api':True})
        player=SpotifyWebPlayer(self.manager,Mock(),core.registry);url=player.start()
        self.addCleanup(player.stop)
        def post(tool,args):return requests.post(url+'browse',json={'tool':tool,'args':args},timeout=3)
        self.assertEqual(post('spotify_search',{'query':'hola','category':'all','offset':0}).json(),{'items':[]})
        self.assertEqual(post('delete_file',{'path':'anything'}).status_code,400)
        self.assertEqual(post('spotify_item_play',{'uri':'file:bad','context':'','position':0}).status_code,400)
        core.registry.tools['spotify_item_play'].function.assert_not_called()
        self.assertEqual(post('spotify_item_play',{'uri':'spotify:track:'+ID,'context':'','position':0}).status_code,200)
        self.assertEqual(requests.get(url+'font',timeout=3).status_code,200)
        self.assertEqual(requests.get(url+'logo',timeout=3).status_code,200)
        player.stop();player.thread.join(2);self.assertFalse(player.thread.is_alive())


class CatalogJavaScript(unittest.TestCase):
    def test_web_navigation_search_and_exact_selection(self):
        node=shutil.which('node')
        if not node:self.skipTest('Node no disponible')
        html=(Path(__file__).parents[1]/'victor/integrations/spotify_web.html').read_text(encoding='utf-8')
        script=html.split('<script>')[1].split('</script>')[0]
        before=r"""
const assert=require('node:assert/strict');const events={};const calls=[];const elements=new Map();let stale;
global.location={search:''};
class Element{constructor(){this.children=[];this.style={};this.dataset={};this.value='';this.classList={toggle(){}};}append(...nodes){this.children.push(...nodes);}replaceChildren(...nodes){this.children=[...nodes];}focus(){}}
global.window={addEventListener:(name,fn)=>events[name]=fn};
global.document={getElementById:id=>{if(!elements.has(id))elements.set(id,new Element());return elements.get(id);},createElement:()=>new Element(),head:{appendChild(){}}};
Object.defineProperty(globalThis,'navigator',{value:{sendBeacon(){return true;}},configurable:true});
const track={id:'A'.repeat(22),kind:'track',name:'GAMINA',subtitle:'Kris R.',uri:'spotify:track:'+'A'.repeat(22),available:true,duration:146000,context:'spotify:playlist:'+'B'.repeat(22),position:52};
const list={id:'B'.repeat(22),kind:'playlist',name:'Mi lista'};
global.fetch=async(path,opts)=>{const request=JSON.parse(opts.body||'{}');calls.push(request);let data={};
 if(request.tool==='spotify_playlists')data=[list];
 if(request.tool==='spotify_collection')data={items:[track],total:2,next_offset:request.args.offset?null:50};
 if(request.tool==='spotify_search'){if(request.args.query==='old')return new Promise(resolve=>stale=()=>resolve({ok:true,json:async()=>({items:[{...track,name:'OLD'}],next_offset:null})}));data={items:[track],next_offset:request.args.offset?null:10};}
 return {ok:true,json:async()=>data};};
"""
        after=r"""
(async()=>{
 await new Promise(r=>setTimeout(r,0));assert.equal(elements.get('library').children.length,1);
 await elements.get('library').children[0].onclick();assert.equal(elements.get('results').children.length,3);
 assert.deepEqual(calls.filter(c=>c.tool==='spotify_collection').map(c=>c.args.offset),[0,50]);
 assert.equal(calls.filter(c=>c.tool==='spotify_item_play').length,0);
 ready=true;player={activateElement(){}};await choose(track);
 assert.deepEqual(calls.find(c=>c.tool==='spotify_item_play').args,{uri:track.uri,context:track.context,position:52});
 const count=calls.length;await choose({...track,available:false});assert.equal(calls.length,count);
 elements.get('search').value='gamina';await searchCatalog();await searchCatalog(nextSearch);
 assert.equal(calls.filter(c=>c.tool==='spotify_search')[1].args.offset,10);
 elements.get('search').value='old';const old=searchCatalog();await new Promise(r=>setTimeout(r,0));
 elements.get('search').value='new';await searchCatalog();stale();await old;
 assert.equal(elements.get('results').children[1].children[2].children[0].children[0].textContent,'GAMINA');
 assert.equal(imageNode('https://evil.example/a').src,'logo');assert.equal(linkNode({url:'javascript:alert(1)'}).href,'https://open.spotify.com');
 updateProgress({duration:146000,position:61000});assert.equal(elements.get('elapsed').textContent,'1:01');
 console.log('catalog navigation / exact URI / pagination / stale search OK');
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'catalog_test.js';path.write_text(before+'\n'+script+'\n'+after,encoding='utf-8')
            result=subprocess.run([node,str(path)],capture_output=True,text=True,encoding='utf-8',timeout=12)
        self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
