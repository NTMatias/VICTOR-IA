"""Voice selection, observed music cards, and a real embedded Windows child."""
import ctypes
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from victor.config import ConfigManager
from victor.errors import VictorError
from victor.integrations.spotify import SpotifyManager, catalog_item

ID='A'*22

def track(name,identifier=ID,artist='Kris R.',**extra):
    return dict(id=identifier,name=name,uri='spotify:track:'+identifier,artists=[{'name':artist}],album={'images':[]},**extra)

class VoiceSelection(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.manager=SpotifyManager(ConfigManager(Path(self.folder.name)));self.client=Mock()
        self.manager.client=Mock(return_value=self.client);self.manager.browser=Mock(active=True,device_id='embedded')
        self.client.current_user.return_value={'product':'premium'}

    def test_exact_title_wins_over_first_related_hit(self):
        self.client.search.return_value={'tracks':{'items':[track('TUKI TUKI','B'*22),track('GAMINA')]}}
        result=self.manager.play('gamina')
        self.client.start_playback.assert_called_once_with(device_id='embedded',uris=['spotify:track:'+ID])
        self.assertEqual(result['seleccion']['name'],'GAMINA');self.assertNotIn('confirmada',result)

    def test_accents_case_and_artist(self):
        self.client.search.return_value={'tracks':{'items':[track('Canción',artist='Otro'),track('CANCIÓN',artist='Artista')]}}
        self.assertEqual(self.manager.play('cancion de artista')['seleccion']['subtitle'],'Artista')

    def test_scoped_retry_finds_title(self):
        self.client.search.side_effect=[{'tracks':{'items':[track('TUKI TUKI')]}},{'tracks':{'items':[track('GAMINA')]}}]
        self.manager.play('gamina')
        self.assertEqual(self.client.search.call_args.kwargs['q'],'track:"gamina"')

    def test_artist_retry_uses_separate_catalog_fields(self):
        self.client.search.side_effect=[{'tracks':{'items':[]}},{'tracks':{'items':[track('GAMINA')]}}]
        self.manager.play('GAMINA de Kris R')
        self.assertEqual(self.client.search.call_args.kwargs['q'],'track:"GAMINA" artist:"Kris R"')
        self.client.start_playback.assert_called_once_with(device_id='embedded',uris=['spotify:track:'+ID])

    def test_title_containing_de_is_not_mistaken_for_an_artist(self):
        self.client.search.return_value={'tracks':{'items':[track('Después de la Playa')]}}
        self.manager.play('Despues de la Playa');self.client.start_playback.assert_called_once()

    def test_no_match_never_plays_a_different_song(self):
        self.client.search.return_value={'tracks':{'items':[track('TUKI TUKI')]}}
        with self.assertRaisesRegex(VictorError,'suficientemente cercana'):self.manager.play('gamina')
        self.client.start_playback.assert_not_called()

    def test_unavailable_exact_title_is_not_played(self):
        self.client.search.return_value={'tracks':{'items':[track('GAMINA',is_playable=False)]}}
        with self.assertRaises(VictorError):self.manager.play('gamina')
        self.client.start_playback.assert_not_called()


class EmbeddedGuiTests(unittest.TestCase):
    def test_embedded_parent_cards_reconnect_and_close(self):
        if os.name!='nt':self.skipTest('Native Windows WebView2')
        from PySide6.QtWidgets import QApplication
        from victor.gui.app import GUIManager
        from victor.gui.spotify_embed import SpotifyEmbed
        q=QApplication.instance() or QApplication([]);q.setQuitOnLastWindowClosed(False)
        def until(check,seconds=12):
            end=time.monotonic()+seconds
            while not check() and time.monotonic()<end:q.processEvents();time.sleep(.01)
            return check()
        folder=tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        with patch('webbrowser.open') as external:
            app=GUIManager(ConfigManager(Path(folder.name)));embed=app.sections.spotify_embed;events=[];embed.event.connect(events.append)
            try:
                app.core.registry.tools['spotify_playlists'].function=Mock(return_value=[])
                app.show();app.navigate('spotify')
                self.assertTrue(until(lambda:embed.loaded),embed.status.text())
                self.assertEqual(len(app.page_widgets['spotify'].findChildren(SpotifyEmbed)),1)
                self.assertFalse(hasattr(app.sections,'spotify_results'));self.assertFalse(hasattr(app.sections,'playlists'))
                user32=ctypes.WinDLL('user32',use_last_error=True);user32.GetParent.argtypes=[ctypes.c_void_p];user32.GetParent.restype=ctypes.c_void_p
                self.assertEqual(user32.GetParent(embed.host_handle),int(embed.surface.winId()),events)
                user32.GetWindowLongW.argtypes=[ctypes.c_void_p,ctypes.c_int]
                self.assertTrue(user32.GetWindowLongW(embed.host_handle,-16)&0x40000000)
                embed.command({'command':'probe','script':"JSON.stringify({search:!!document.getElementById('search'),library:!!document.getElementById('library'),footer:!!document.getElementById('seek')})"})
                self.assertTrue(until(lambda:any(e['kind']=='probe' for e in events)))
                data=json.loads(json.loads(next(e['result'] for e in events if e['kind']=='probe')))
                self.assertEqual(data,{'search':True,'library':True,'footer':True});external.assert_not_called()
                app.voice_output.speak=Mock()
                app.core.submit=Mock(return_value=False)
                app.send('reproducir GAMINA de Kris R en Spotify.')
                self.assertEqual(app.core.submit.call_args.args[2],('spotify_play',{'query':'GAMINA de Kris R'}))
                app.handle_event('answer','[Resultado de herramienta spotify_play]\n{"ok":true}He enviado la solicitud.')
                self.assertIn('No se confirmó',app.voice_panel.response.text());self.assertNotIn('Preparando resultado',app.voice_panel.response.text())
                app.spotify_command=Mock(return_value=True)
                observed={'id':ID,'name':'GAMINA','artists':'Kris R.','playing':True,'volume':20,'position':12000,'duration':146000,'art_url':''}
                app.handle_event('spotify_browser_state',observed)
                sections=app.sections
                self.assertEqual(sections.spotify_title.text(),'GAMINA');self.assertEqual(sections.spotify_artist.text(),'Kris R.')
                self.assertEqual(sections.spotify_position.maximum(),146000);self.assertEqual(sections.spotify_position.value(),12000)
                sections.spotify_play.click();app.spotify_command.assert_called_once_with('spotify_pause',{})
                self.assertEqual(sections.spotify_play.accessibleName(),'Reproducir');self.assertIn('Actualizando',sections.spotify_status.text())
                app.handle_event('spotify_control_result',('spotify_pause',{'ok':False,'error':'Fixture'},0))
                self.assertEqual(sections.spotify_play.accessibleName(),'Pausar')
                app.spotify_command.reset_mock()
                sections.spotify_volume.setValue(40);sections.spotify_volume.setValue(59)
                self.assertTrue(until(lambda:app.spotify_command.called,1))
                app.spotify_command.assert_called_once_with('spotify_volume',{'level':59})
                sections.spotify_state(dict(observed,volume=20));self.assertEqual(sections.spotify_volume.value(),59)
                app.spotify_command.reset_mock();sections.spotify_position.setValue(61000);sections.spotify_position.sliderReleased.emit()
                app.spotify_command.assert_called_once_with('spotify_seek',{'position':61000})
                sections.toggle_player();self.assertTrue(app.player.dismissed)
                sections.toggle_player();self.assertFalse(app.player.dismissed)
                for theme,expected in [('Light','rgb(246, 247, 250)'),('Dark','rgb(21, 23, 28)')]:
                    app.config.save({'theme':theme});app.refresh_config();events.clear()
                    embed.command({'command':'probe','script':"JSON.stringify({page:getComputedStyle(document.documentElement).backgroundColor,surface:getComputedStyle(document.querySelector('.content')).backgroundColor,font:getComputedStyle(document.body).fontSize,transport:getComputedStyle(document.querySelector('.transport')).display})"})
                    self.assertTrue(until(lambda:any(e['kind']=='probe' and str(e.get('result','')).startswith('"{') for e in events)))
                    palette=json.loads(json.loads(next(e['result'] for e in events if e['kind']=='probe' and str(e.get('result','')).startswith('"{'))))
                    self.assertEqual(palette['page'],expected);self.assertEqual(palette['font'],'13px');self.assertEqual(palette['transport'],'none')
                    self.assertEqual(palette['surface'],'rgb(255, 255, 255)' if theme=='Light' else 'rgb(29, 32, 39)')
                app.current_bubble=app.append_message('assistant','…');app.voice_output.speak=Mock()
                selected=catalog_item(track('GAMINA'),'track')
                app.handle_event('tool_result',('spotify_play',{'ok':True,'result':{'seleccion':selected,'aceptada_por_api':True}}))
                app.handle_event('answer',json.dumps({'orden_enviada':'Reproducir canción','solicitada':'GAMINA'}))
                self.assertTrue(app.voice_panel.response.isHidden());self.assertTrue(app.current_bubble.label.isHidden())
                self.assertEqual(app.voice_panel.music.title.text(),'GAMINA');self.assertNotIn('orden_enviada',app.voice_output.speak.call_args.args[0])
                app.present_spotify({'id':'old','name':'TUKI TUKI','playing':True})
                self.assertEqual(app.voice_panel.music.title.text(),'GAMINA')
                app.present_spotify({'id':ID,'name':'GAMINA','artists':'Kris R.','playing':True})
                self.assertEqual(app.voice_panel.music.status.text(),'Reproduciendo')
                app.handle_event('tool_result',('spotify_play',{'ok':False,'error':'No encontré una coincidencia exacta.'}))
                app.handle_event('answer','No encontré una coincidencia exacta.')
                self.assertFalse(app.voice_panel.response.isHidden());self.assertFalse(app.current_bubble.label.isHidden())
                self.assertIn('coincidencia exacta',app.voice_panel.response.text())
                app.spotify_turn=None;app.voice_panel.show_response();app.handle_event('answer','Respuesta normal')
                self.assertFalse(app.voice_panel.response.isHidden());self.assertEqual(app.voice_panel.response.text(),'Respuesta normal')
                old=embed.host_handle;events.clear();embed.restart()
                self.assertTrue(until(lambda:embed.loaded and embed.host_handle!=old))
                for width in (1600,420):
                    app.resize(width,900)
                    page=app.page_widgets['spotify']
                    self.assertTrue(until(lambda:embed.width()<=app.width() and page.horizontalScrollBar().maximum()==0,2),
                                    f'app={app.size()} embed={embed.size()} viewport={page.viewport().size()} body_min={page.body.minimumSizeHint()} scroll={page.horizontalScrollBar().maximum()}')
                    from PySide6.QtCore import QPoint
                    self.assertLess(sections.spotify_cover.mapTo(page,QPoint(0,0)).x(),sections.spotify_title.mapTo(page,QPoint(0,0)).x())
                    self.assertEqual(page.horizontalScrollBar().maximum(),0)
                    if width==1600:self.assertLess(sections.spotify_now_card.mapTo(page,QPoint(0,0)).x(),embed.mapTo(page,QPoint(0,0)).x())
                    else:self.assertLess(sections.spotify_now_card.mapTo(page,QPoint(0,0)).y(),embed.mapTo(page,QPoint(0,0)).y())
                    self.assertGreaterEqual(embed.surface.height(),240)
                    events.clear()
                    embed.command({'command':'probe','script':"JSON.stringify({width:innerWidth,scroll:document.body.scrollWidth,connect:document.getElementById('connect').getBoundingClientRect().bottom,search:document.getElementById('search-form').getBoundingClientRect().bottom,workspace:document.querySelector('.workspace').getBoundingClientRect().top})"})
                    self.assertTrue(until(lambda:any(e['kind']=='probe' for e in events)))
                    layout=json.loads(json.loads(next(e['result'] for e in events if e['kind']=='probe')))
                    self.assertEqual(layout['width'],layout['scroll']);self.assertLessEqual(layout['connect'],layout['workspace']);self.assertLessEqual(layout['search'],layout['workspace'])
            finally:
                app.window_transitions.close_visual_done=True;app.close();until(lambda:app.closed_cleanly,8);folder.cleanup()
            self.assertTrue(app.closed_cleanly);self.assertFalse(embed.running())


if __name__=='__main__':unittest.main()
