"""Claves sintéticas y audio simulado: sin consumo de APIs ni micrófono físico."""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
from victor.config import ConfigManager, DEFAULTS, KEYS
from victor.errors import VictorError
from victor.ai.manager import AIManager
from victor.ai.base import Reply
from victor.voice.text import correct_music_command, recognition_vocabulary, speech_text
from victor.voice.output import speak_sapi


class Credentials(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.cfg=ConfigManager(self.root)
    def tearDown(self):self.temp.cleanup()

    def test_windows_encrypted_roundtrip_precedence_and_removal(self):
        with patch.dict(os.environ, {v:'environment-fixture' for v in KEYS.values()}):
            self.cfg.credentials.update({p:'personal-fixture-'+p for p in KEYS})
            self.cfg.save({'name':'Prueba'})
            other=ConfigManager(self.root)
            for p in KEYS:
                self.assertEqual(other.api_key(p),'personal-fixture-'+p)
                self.assertIn('cifrada',other.credential_source(p))
            self.assertNotIn(b'personal-fixture',self.cfg.credentials.path.read_bytes())
            self.assertNotIn('personal-fixture',self.cfg.path.read_text())
            self.assertNotIn('_api_key',other.snapshot())
            other.credentials.update({'Gemini':None})
            self.assertEqual(other.api_key('Gemini'),'environment-fixture')
            self.assertEqual(other.api_key('OpenAI'),'personal-fixture-OpenAI')

    def test_failed_encrypt_and_corrupt_file_preserve_previous_bytes(self):
        self.cfg.credentials.update({'Gemini':'old-fixture'})
        previous=self.cfg.credentials.path.read_bytes()
        crypt=self.cfg.credentials.crypt
        def fail_encrypt(data,decrypt=False):
            if decrypt:return crypt(data,True)
            raise VictorError('cifrado no disponible')
        with patch.object(self.cfg.credentials,'crypt',side_effect=fail_encrypt):
            with self.assertRaises(VictorError):self.cfg.credentials.update({'Gemini':'new-fixture'})
        self.assertEqual(self.cfg.credentials.path.read_bytes(),previous)
        self.cfg.credentials.path.write_bytes(b'corrupt')
        with self.assertRaises(VictorError):self.cfg.credentials.update({'Gemini':'new-fixture'})
        self.assertEqual(self.cfg.credentials.path.read_bytes(),b'corrupt')
        self.assertFalse(self.cfg.credentials.path.with_suffix('.tmp').exists())

    def test_invalid_keys_never_write_a_file(self):
        for values in ({'Gemini':'invalid key'}, {'OpenAI':''}, {'Ollama':'no-key-needed'}, {'Gemini':'line\nbreak'}):
            with self.assertRaises(VictorError):self.cfg.credentials.update(values)
        self.assertFalse(self.cfg.credentials.path.exists())

    def test_manager_uses_personal_keys_next_request_and_fallback_isolated(self):
        with patch.dict(os.environ, {},clear=True):
            manager=AIManager(self.cfg,lambda *args:None)
            for p in KEYS:
                self.cfg.save({'provider':p,'fallback':[]})
                self.cfg.credentials.update({p:'personal-fixture-'+p})
                with patch.object(manager.providers[p],'stream',return_value=Reply('ok')) as stream:
                    self.assertEqual(manager.generate([],'',[],threading.Event()).text,'ok')
                    self.assertEqual(stream.call_args.args[3]['_api_key'],'personal-fixture-'+p)
            self.cfg.save({'provider':'Gemini','fallback':['Ollama']})
            with patch.object(manager.providers['Gemini'],'stream',side_effect=ConnectionError()),patch.object(manager.providers['Ollama'],'stream',return_value=Reply('local')) as local:
                manager.generate([],'',[],threading.Event())
                self.assertNotIn('_api_key',local.call_args.args[3])

    def test_all_sdks_receive_personal_key_without_environment(self):
        from victor.ai.openai_provider import OpenAIProvider
        from victor.ai.anthropic_provider import AnthropicProvider
        from victor.ai.gemini_provider import GeminiProvider
        cfg=deepcopy(DEFAULTS);cfg['_api_key']='personal-sdk-fixture'
        with patch.dict(os.environ,{},clear=True):
            for cls,sdk_path in [(OpenAIProvider,'openai.OpenAI'),(AnthropicProvider,'anthropic.Anthropic'),(GeminiProvider,'google.genai.Client')]:
                with self.subTest(provider=cls.name),patch(sdk_path) as sdk:
                    if cls is AnthropicProvider:
                        sdk.return_value.__enter__.return_value.messages.stream.return_value.__enter__.return_value.get_final_message.return_value.content=[]
                    cls().stream([{'role':'user','content':'Hola'}],'',[],cfg,lambda t:None,threading.Event())
                    self.assertEqual(sdk.call_args.kwargs['api_key'],'personal-sdk-fixture')


class VoiceText(unittest.TestCase):
    corrections='la mina de Chris R => GAMINA de Kris R\nla mena => GAMINA de Kris R\ngamina de Chris R => GAMINA de Kris R'
    def test_personalized_music_correction_preserves_other_speech(self):
        for text in ['reproduce la mina de Chris R','Reproducir la mena en Spotify.','pon la canción GAMINA de Chris R']:
            self.assertIn('GAMINA de Kris R',correct_music_command(text,self.corrections))
        for text in ['la mina de Chris R','abre la mina de Chris R','reproduce la mina de otro artista','reproduce la mena remix','cancela','reproduce una playlist de la mena']:
            self.assertEqual(correct_music_command(text,self.corrections),text)
        cfg=deepcopy(DEFAULTS);cfg.update(voice_vocabulary='GAMINA, Kris R',voice_corrections=self.corrections,applications={'Discord':'C:/Discord.exe'})
        self.assertIn('Discord',recognition_vocabulary(cfg));self.assertIn('Kris R',recognition_vocabulary(cfg))
        from victor.gui.spotify_commands import spotify_command
        normalized=correct_music_command('reproduce GAMINA de Kris R N Spotify',self.corrections)
        self.assertEqual(spotify_command(normalized),('spotify_play',{'query':'GAMINA de Kris R'}))
    def test_invalid_corrections_rejected_when_saving(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder))
            with self.assertRaises(VictorError):cfg.save({'voice_corrections':'incorrecto'})
            cfg.save({'voice_corrections':self.corrections})
            self.assertEqual(ConfigManager(Path(folder)).get('voice_corrections'),self.corrections)
    def test_punctuation_and_markup_are_pauses_not_names(self):
        value=speech_text('## ¡Hola!\n**Escucha** GAMINA (de Kris R). [Buscar](https://example.com) cuesta 40%. 🎵')
        self.assertEqual(value,'¡Hola! Escucha GAMINA, de Kris R. Buscar cuesta 40 por ciento.')
        self.assertEqual(speech_text('¿Vienes? Son las 11:45; hay 3,5 litros.'),'¿Vienes? Son las 11:45; hay 3,5 litros.')
        self.assertNotIn('print',speech_text('Ejemplo: ```python\nprint(1)\n```'))
        table=speech_text('| Motor | Internet |\n| --- | --- |\n| Local | No |\n| Nube | Sí |')
        self.assertEqual(table,'Motor: Local; Internet: No. Motor: Nube; Internet: Sí.')
        self.assertNotIn('---',speech_text('Resumen\n---\nFinal'))
    def test_sapi_does_not_match_es_inside_desktop(self):
        engine=Mock();engine.getProperty.return_value=[NS(name='Microsoft David Desktop',languages=['en-US'],id='english'),NS(name='Microsoft Spanish',languages=['es-MX'],id='spanish')]
        with patch('pyttsx3.init',return_value=engine):speak_sapi({'text':'Hola','rate':175,'language':'es-EC'})
        engine.setProperty.assert_any_call('voice','spanish')
        self.assertNotIn(unittest.mock.call('voice','english'),engine.setProperty.call_args_list)
        engine.getProperty.return_value=[NS(name='David Desktop',languages=['en-US'],id='english')]
        with patch('pyttsx3.init',return_value=engine),self.assertRaises(VictorError):speak_sapi({'text':'Hola','rate':175,'language':'es'})


class SettingsGUI(unittest.TestCase):
    def test_personal_key_save_remove_voice_preview_and_responsive_pages(self):
        import time
        from PySide6.QtWidgets import QApplication, QLineEdit
        from victor.gui.app import GUIManager
        q=QApplication.instance() or QApplication([]);q.setQuitOnLastWindowClosed(False)
        def pump(seconds=.1):
            until=time.monotonic()+seconds
            while time.monotonic()<until:q.processEvents();time.sleep(.005)
        from PySide6.QtWidgets import QMessageBox
        with tempfile.TemporaryDirectory() as folder,patch('victor.gui.spotify_embed.SpotifyEmbed.start'),patch('victor.gui.panels.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):
            app=GUIManager(ConfigManager(Path(folder)))
            try:
                app.show();app.resize(1200,900);app.navigate('ia');pump(.2)
                fields=app.settings.api_key_fields
                self.assertEqual(set(fields),set(KEYS))
                for w in fields.values():
                    self.assertEqual(w.echoMode(),QLineEdit.EchoMode.Password)
                    self.assertEqual(w.text(),'')
                fields['Gemini'].setText('gui-key-fixture')
                self.assertTrue(app.settings.save_api_keys('Gemini'))
                self.assertEqual(app.config.api_key('Gemini'),'gui-key-fixture')
                self.assertEqual(fields['Gemini'].text(),'')
                self.assertIn('cifrada',app.settings.api_key_status['Gemini'].text())
                self.assertNotIn('gui-key-fixture',app.settings.api_key_status['Gemini'].text())
                app.config.save({'provider':'Gemini'});app.refresh_config()
                self.assertEqual(app.connection_label.text(),'Gemini · sin verificar')
                self.assertEqual(app.error_label.text(),'')
                app.settings.remove_api_key('Gemini')
                self.assertEqual(app.config.credentials.get('Gemini'),'')
                app.navigate('voice_settings');pump(.1)
                app.settings.fields['edge_voice'].setCurrentText('es-MX-JorgeNeural')
                with patch.object(app.voice_output,'speak') as speak:
                    app.settings.preview_voice()
                    self.assertEqual(speak.call_args.kwargs['settings']['edge_voice'],'es-MX-JorgeNeural')
                    self.assertTrue(speak.call_args.kwargs['force'])
                app.settings.fields['voice_corrections'].setPlainText(VoiceText.corrections)
                from victor.config import DEFAULTS
                self.assertEqual({'models' if k.startswith('model:') else k for k in app.settings.fields},set(DEFAULTS)-{'auth_methods','account_models','gemini_account_enabled'})
                self.assertEqual(set(app.settings.account_panels),{'OpenAI'})
                self.assertIn('openai',[app.settings.fields['voice_backend'].itemText(i) for i in range(app.settings.fields['voice_backend'].count())])
                app.settings.fields['voice_backend'].setCurrentText('openai')
                app.settings.fields['openai_transcription_model'].setCurrentText('gpt-transcribe')
                self.assertIn('Falta tu clave',app.settings.recognition_state.text())
                app.settings.save(app.settings.GROUPS['voice_settings'])
                self.assertEqual(app.config.get('voice_corrections'),VoiceText.corrections)
                self.assertEqual(app.config.get('voice_backend'),'openai')
                self.assertEqual(ConfigManager(Path(folder)).get('openai_transcription_model'),'gpt-transcribe')
                self.assertIn('OpenAI',app.voice_panel.recognizer.text())
                self.assertEqual(app.config.get('provider'),'Gemini')
                fields['OpenAI'].setText('openai-gui-fixture');app.settings.save_api_keys('OpenAI')
                self.assertIn('Clave configurada',app.settings.recognition_state.text())
                if os.getenv('VICTOR_TEST_PREVIEWS'):
                    directory=Path(os.environ['VICTOR_TEST_PREVIEWS']);directory.mkdir(parents=True,exist_ok=True)
                    for key in ('ia','voice_settings'):
                        app.navigate(key);app.resize(1200,900);pump(.2);app.grab().save(str(directory/(key+'.png')))
                        app.resize(560,860);pump(.2);app.grab().save(str(directory/(key+'-narrow.png')))
                for page in ('ia','voice_settings'):
                    app.navigate(page);app.resize(560,860);pump(.2)
                    self.assertEqual(app.page_widgets[page].horizontalScrollBar().maximum(),0)
            finally:
                app.close()
                until=time.monotonic()+8
                while not app.closed_cleanly and time.monotonic()<until:pump(.1)
            self.assertTrue(app.closed_cleanly)


if __name__=='__main__':unittest.main()
