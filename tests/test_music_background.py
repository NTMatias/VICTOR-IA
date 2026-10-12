"""Errores de dictado, mensajes de radio y escucha sin foco, con servicios simulados."""
from collections import Counter
from pathlib import Path
import tempfile
import threading
import time
import unittest
import json
import base64
from unittest.mock import Mock, patch, PropertyMock
from victor.config import ConfigManager
from victor.errors import VictorError
from victor.integrations.spotify import SpotifyManager, catalog_item
from victor.voice.input import VoiceInput
from victor.voice.music_radio import radio_phrase
from tests.test_spotify_embed import track


class ApproximateMusic(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup)
        self.manager=SpotifyManager(ConfigManager(Path(self.folder.name)));self.client=Mock()
        self.manager.client=Mock(return_value=self.client);self.manager.browser=Mock(active=True,device_id='embedded')
        self.client.current_user.return_value={'product':'premium'}
    def results(self,*rows):return {'tracks':{'items':list(rows)}}
    def test_reported_title_and_artist_mistakes_choose_actual_track(self):
        for query,row in [('Sex Playlist 1',track('SEXPLAYLIST1',artist='Omar Courtz')),
                          ('tuki tuk de Chris r',track('TUKI TUKI',artist='Kris R.')),
                          ('interludio de Omar Cobbord',track('I N T E R L U D I O',artist='Omar Courtz'))]:
            with self.subTest(query=query):
                self.client.search.return_value=self.results(track('GAMINA','B'*22,popularity=100),row)
                result=self.manager.play(query)
                self.assertEqual(result['seleccion']['name'],row['name'])
                self.assertEqual(self.client.start_playback.call_args.kwargs['uris'],[row['uri']])
                self.assertLessEqual(self.client.search.call_count,2)
                self.client.search.reset_mock()
    def test_exact_title_and_artist_beat_popular_fuzzy_result(self):
        self.client.search.return_value=self.results(track('TUKI TUKI','B'*22,popularity=100),track('TUKI TUK',artist='Kris R.',popularity=1))
        self.assertEqual(self.manager.play('TUKI TUK de Kris R')['seleccion']['name'],'TUKI TUK')
        self.assertEqual(self.client.search.call_count,1)
    def test_best_candidate_rank_is_not_search_order_or_popularity(self):
        self.client.search.return_value=self.results(track('TUKI TAKI','B'*22,popularity=100),track('TUKI TUKI',popularity=1),track('TUKI TUKI','C'*22,artist='Chris Brown',popularity=100))
        result=self.manager.play('tuki tuk de Chris R')
        self.assertEqual(result['seleccion']['id'],'A'*22)
        self.assertEqual(result['coincidencia']['tipo'],'aproximada')
    def test_misspelled_artist_retries_title_only(self):
        self.client.search.side_effect=[self.results(),self.results(),self.results(track('INTERLUDIO',artist='Omar Courtz'))]
        self.manager.play('interludio de Omar Cobbord')
        self.assertEqual(self.client.search.call_args.kwargs['q'],'interludio')
        self.assertEqual(self.client.search.call_count,3)
    def test_unrelated_track_or_wrong_artist_and_unavailable_never_play(self):
        for query,row in [('GAMINA de Kris R',track('TUKI TUKI')),
                          ('tuki tuk de Kris R',track('TUKI TUKI',artist='Omar Courtz')),
                          ('tuki tuk de Kris R',track('TUKI TUKI',is_playable=False))]:
            with self.subTest(query=query,artist=row['artists']):
                self.client.search.return_value=self.results(row)
                with self.assertRaises(VictorError):self.manager.play(query)
                self.client.start_playback.assert_not_called()


class BackgroundVoice(unittest.TestCase):
    def test_wake_word_required_again_after_one_command_without_focus(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));cfg.save({'voice_mode':'continua'})
            events=[]
            def emit(kind,value):
                events.append((kind,value))
                if kind=='voice_wake':value.set()
            voice=VoiceInput(cfg,emit,lambda:True)
            voice.background_context=lambda:True
            phrases=iter(['VICTOR reproduce TUKI TUKI en Spotify','reproduce otra canción en Spotify',
                          'VICTOR reproduce GAMINA de Kris R en Spotify','','',''])
            def listen():
                try:return next(phrases)
                except StopIteration:voice.stop();return ''
            with patch.object(voice,'listen',side_effect=listen):voice._run()
            commands=[value for kind,value in events if kind=='voice_text']
            self.assertEqual(commands,['reproduce TUKI TUKI en Spotify','reproduce GAMINA de Kris R en Spotify'])
            self.assertFalse(any(kind=='notice' for kind,value in events))
    def test_background_startup_validation(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder))
            with self.assertRaises(VictorError):cfg.save({'voice_background_listening':'true'})
            cfg.save({'voice_background_listening':True,'voice_mode':'continua'})
            self.assertTrue(ConfigManager(Path(folder)).get('voice_background_listening'))


class Radio(unittest.TestCase):
    def test_exact_twenty_twenty_sixty_probability_buckets(self):
        with patch('victor.voice.music_radio.random.randrange',side_effect=range(100)):
            counts=Counter(radio_phrase() for _ in range(100))
        self.assertEqual(counts,{'Lo escuchas aquí en VICTOR.IA.':20,'Escuchándose en Spotify desde VICTOR.IA.':20,'':60})


class BackgroundPlayer(unittest.TestCase):
    def test_background_connect_does_not_transfer_or_start_existing_music(self):
        import requests
        from victor.integrations.spotify_web import SpotifyWebPlayer
        manager=Mock();player=SpotifyWebPlayer(manager,Mock())
        try:
            url=player.start()
            response=requests.post(url+'ready',json={'device':'A'*32,'background':True},timeout=2)
            self.assertEqual(response.status_code,200);self.assertTrue(player.active)
            manager.client.assert_not_called()
            response=requests.post(url+'ready',json={'device':'A'*32,'background':False},timeout=2)
            self.assertEqual(response.status_code,200)
            manager.client.return_value.transfer_playback.assert_called_once_with('A'*32,force_play=False)
            manager.client.return_value.start_playback.assert_not_called()
        finally:
            player.stop()
            if player.thread:player.thread.join(2)

    def test_native_player_autoplay_with_silent_audio_no_spotify_account(self):
        import os
        if os.name!='nt':self.skipTest('WebView2 requiere Windows')
        from PySide6.QtWidgets import QApplication
        from victor.gui.app import GUIManager
        from victor.voice.openai_transcription import wav_audio
        import numpy as np
        q=QApplication.instance() or QApplication([]);q.setQuitOnLastWindowClosed(False)
        def until(check,seconds=12):
            deadline=time.monotonic()+seconds
            while not check() and time.monotonic()<deadline:q.processEvents();time.sleep(.01)
            return check()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder,patch('victor.voice.input.VoiceInput.start'):
            cfg=ConfigManager(Path(folder));app=GUIManager(cfg);events=[];embed=app.sections.spotify_embed;embed.event.connect(events.append)
            try:
                cfg.save({'voice_background_listening':True,'voice_mode':'continua','voice_backend':'google'})
                app.show();app.navigate('spotify')
                self.assertTrue(until(lambda:embed.loaded),embed.status.text())
                self.assertIn('--autoplay-policy=no-user-gesture-required',embed.process.processEnvironment().value('WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'))
                self.assertIn('handsfree=1',embed.process.arguments()[1])
                self.assertTrue(until(lambda:embed.pipe is not None))
                app.showMinimized()
                # Cero PCM: no reproduce una canción ni usa credenciales personales.
                wav=base64.b64encode(wav_audio(np.zeros(16000,dtype=np.float32))).decode()
                script="window.autoplayResult='waiting'; window.testAudio=new Audio('data:audio/wav;base64,"+wav+"'); window.testAudio.play().then(()=>window.autoplayResult='playing').catch(e=>window.autoplayResult=e.name); 'started';"
                embed.command({'command':'probe','script':script})
                self.assertTrue(until(lambda:any(e.get('kind')=='probe' for e in events)))
                events.clear()
                # Después de ejecutar la promesa, consultar el estado real del elemento.
                deadline=time.monotonic()+8;played=False
                while time.monotonic()<deadline and not played:
                    events.clear();embed.command({'command':'probe','script':'JSON.stringify({status:window.autoplayResult,sdk:typeof window.onSpotifyWebPlaybackSDKReady})'})
                    self.assertTrue(until(lambda:any(e.get('kind')=='probe' for e in events),3))
                    data=json.loads(json.loads(next(e['result'] for e in events if e.get('kind')=='probe')))
                    played=data['status']=='playing'
                    if not played:until(lambda:False,.1)
                self.assertTrue(played,data)
                self.assertEqual(data['sdk'],'function')
            finally:
                app.close();self.assertTrue(until(lambda:app.closed_cleanly))


class BackgroundGUI(unittest.TestCase):
    def test_auto_start_minimized_pause_mode_switch_and_verified_radio(self):
        from PySide6.QtWidgets import QApplication
        from victor.gui.app import GUIManager
        q=QApplication.instance() or QApplication([]);q.setQuitOnLastWindowClosed(False)
        def pump(seconds=.15):
            until=time.monotonic()+seconds
            while time.monotonic()<until:q.processEvents();time.sleep(.005)
        with tempfile.TemporaryDirectory() as folder,patch('victor.gui.spotify_embed.SpotifyEmbed.start'),patch('victor.voice.input.VoiceInput.start') as start:
            cfg=ConfigManager(Path(folder));cfg.save({'voice_background_listening':True,'voice_mode':'continua','voice_backend':'google'})
            app=GUIManager(cfg)
            try:
                app.show();app.showMinimized();pump(.8)
                start.assert_called_once();self.assertTrue(app.voice_background)
                app.queue_continuous_listening();app.pause_mic();pump(.2)
                start.assert_called_once();self.assertFalse(app.voice_restart_timer.isActive())
                # Un worker aún cerrando no se reinicia hasta completar la parada.
                app.voice_input.stop_event.set();app.queue_continuous_listening()
                with patch.object(type(app.voice_input),'running',new_callable=PropertyMock,side_effect=[True,False]):
                    pump(.35)
                self.assertEqual(start.call_count,2)
                app.voice_panel.set_mode('manual');pump(.2)
                self.assertEqual(start.call_count,2)
                app.voice_panel.set_mode('continua');pump(.2)
                self.assertEqual(start.call_count,3)
                app.pause_mic();app.voice_output.speak=Mock();app.core.spotify.browser=Mock(active=True)
                selected=catalog_item(track('TUKI TUKI'),'track')
                observed={'id':'A'*22,'name':'TUKI TUKI','artists':'Kris R.','playing':True}
                # La aceptación HTTP no afirma que ya se esté escuchando.
                app.handle_event('tool_result',('spotify_play',{'ok':True,'result':{'seleccion':selected,'aceptada_por_api':True}}))
                with patch('victor.voice.music_radio.random.randrange',return_value=0):app.handle_event('answer','ACK')
                self.assertEqual(app.voice_output.speak.call_args_list[0].args[0],'Solicitud enviada: TUKI TUKI.')
                self.assertEqual(app.voice_output.speak.call_count,1)
                app.present_spotify(dict(observed,id='B'*22));self.assertEqual(app.voice_output.speak.call_count,1)
                app.present_spotify(observed)
                self.assertEqual(app.voice_output.speak.call_args.args[0],'Lo escuchas aquí en VICTOR.IA.')
                app.present_spotify(observed);self.assertEqual(app.voice_output.speak.call_count,2)
                # Si el estado llega primero, conservar el título al responder.
                app.voice_output.speak.reset_mock()
                app.handle_event('tool_result',('spotify_play',{'ok':True,'result':{'seleccion':selected,'aceptada_por_api':True}}))
                app.present_spotify(observed)
                with patch('victor.voice.music_radio.random.randrange',return_value=20):app.handle_event('answer','ACK')
                self.assertEqual([call.args[0] for call in app.voice_output.speak.call_args_list],['Solicitud enviada: TUKI TUKI.','Escuchándose en Spotify desde VICTOR.IA.'])
                app.voice_output.speak.reset_mock()
                app.handle_event('tool_result',('spotify_play',{'ok':False,'error':'No hay resultado'}));app.handle_event('answer','No hay resultado')
                self.assertEqual(app.voice_output.speak.call_args.args[0],'No hay resultado')
            finally:
                app.close();until=time.monotonic()+8
                while not app.closed_cleanly and time.monotonic()<until:pump(.1)
            self.assertTrue(app.closed_cleanly)
