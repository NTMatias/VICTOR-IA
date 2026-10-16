import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication,QLabel,QPlainTextEdit
from victor.config import ConfigManager
from victor.core import VictorCore
from victor.security import Approval,Risk
from tests.gui_support import authenticated_gui as GUIManager
from victor.gui.tool_labels import LABELS,confirmation_details,friendly_name
from victor.gui.spotify_player import register_player
from victor.integrations.local_remote import LocalRemote
from victor.plugins.video import register_video,first_video
from victor.ai.base import Reply


class V4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt=QApplication.instance() or QApplication([])
        cls.qt.setQuitOnLastWindowClosed(False)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.cfg=ConfigManager(Path(self.temp.name))
        self.events=[]
        self.core=VictorCore(self.cfg,lambda k,p:self.events.append((k,p)))

    def pump(self,seconds=.1):
        end=time.monotonic()+seconds
        while time.monotonic()<end:self.qt.processEvents();time.sleep(.01)

    def test_labels_cover_every_registered_tool(self):
        app=GUIManager(self.cfg)
        try:
            self.assertEqual(set(app.core.registry.tools)-set(LABELS),set())
            self.assertNotIn('Tools',[w.text() for w in app.nav_buttons.values()])
        finally:
            app.close()
            for _ in range(50):
                self.pump(.05)
                if app.closed_cleanly:break
        self.assertTrue(app.closed_cleanly)

    def test_confirmation_spanish_and_preserves_full_email(self):
        text=confirmation_details('spotify_volume','Ajustar Spotify\n\n'+json.dumps({'level':37}))
        self.assertIn('Nivel: 37 de 100',text);self.assertNotIn('{',text)
        text=confirmation_details('google_send_email','Enviar\n'+json.dumps({'to':'a@example.com','subject':'Prueba','body':'Línea uno\nLínea dos'})+'\nAdvertencia')
        self.assertIn('Línea uno\nLínea dos',text);self.assertIn('a@example.com',text);self.assertIn('Advertencia',text)
        self.assertEqual(friendly_name('nueva_herramienta'),'Nueva herramienta')

    def test_volume_only_risk_change_and_resume(self):
        before={n:t.risk for n,t in self.core.registry.tools.items()}
        register_player(self.core)
        self.assertEqual(self.core.registry.tools['spotify_volume'].risk,Risk.LOW)
        for name in ('spotify_play','spotify_pause','spotify_next','spotify_previous'):
            self.assertEqual(self.core.registry.tools[name].risk,before[name])
        self.assertEqual(self.core.registry.tools['spotify_resume'].risk,Risk.MEDIUM)

    def test_voice_confirmation_local_armed_only(self):
        app=GUIManager(self.cfg)
        app.voice_input.start=Mock();app.voice_output.speak=Mock()
        try:
            app.show_voice(True)
            request=Approval('google_send_email','Enviar\n'+json.dumps({'to':'a@example.com','subject':'Prueba','body':'Texto'}),Risk.HIGH)
            app.handle_event('approval',request)
            self.assertFalse(request.done.is_set())
            app.listen_approval()
            self.assertTrue(app.voice_confirmation_active())
            app.handle_voice_text('ejecutar', request)
            self.assertTrue(request.accepted)
            self.assertFalse(app.voice_confirmation_active())
            other=Approval('move_file','Mover',Risk.MEDIUM)
            app.handle_event('approval',other)
            with patch.object(app,'send') as send:
                app.handle_voice_text('sí')
                send.assert_called_once_with('sí',voice=True)
            self.assertFalse(other.done.is_set())
            app.player.update_state({'id':'test','name':'Tema de prueba','artists':'Ejemplo','playing':False,'volume':30,'art':b''})
            self.assertEqual(app.player.play.accessibleName(),'Reproducir')
            app.player.dismiss();self.assertTrue(app.player.isHidden())
        finally:
            app.close()
            for _ in range(50):
                self.pump(.05)
                if app.closed_cleanly:break
        self.assertTrue(app.closed_cleanly)

    def test_remote_touch_maps_virtual_desktop(self):
        remote=LocalRemote(self.cfg,self.core,lambda *a:None)
        self.cfg.save({'local_remote_enabled':True});remote.ready.set()
        token=remote.pair(remote.qr_url().split('#')[1],'test')
        self.core.security.set_origin({'source':'local_web','session':token,'user_id':'LAN test'})
        remote.frame_history['f']={'left':-1920,'top':0,'width':3840,'height':1080,'time':time.monotonic()}
        self.core.automation.move_mouse=Mock();self.core.automation.mouse_click=Mock(return_value={'clic':True})
        def approve(k,p):self.assertEqual(p.risk,Risk.MEDIUM);p.accepted=True;p.done.set()
        self.core.security.emit=approve
        args={'window':'Editor','x':.75,'y':.5,'frame_id':'f','action':'click'}
        self.assertTrue(self.core.registry.execute('remote_touch',args)['ok'])
        self.core.automation.mouse_click.assert_called_once_with('Editor',960,540,'left')
        remote.frame_history['f']['time']=0
        self.assertFalse(self.core.registry.execute('remote_touch',args)['ok'])

    def test_telegram_free_language_uses_same_ai(self):
        self.cfg.save({'telegram_enabled':True,'telegram_allowed_ids':[123]})
        self.core.ai.generate=Mock(return_value=Reply('Respuesta de IA de prueba',[]))
        conversation=self.core.history.create()
        self.assertTrue(self.core.submit('Explícame con calma cómo organizar mi trabajo',conversation,origin={'source':'telegram','user_id':123,'chat_id':123}))
        self.core.thread.join(5)
        self.core.ai.generate.assert_called_once()
        self.assertIn(('answer','Respuesta de IA de prueba'),self.events)

    def test_telegram_missing_ai_reports_error(self):
        self.cfg.save({'telegram_enabled':True,'telegram_allowed_ids':[123],'provider':'OpenAI','fallback':[]})
        with patch.dict('os.environ',{'OPENAI_API_KEY':''}):
            self.core.submit('Explícame algo interesante',self.core.history.create(),origin={'source':'telegram','user_id':123,'chat_id':123})
            self.core.thread.join(5)
        self.assertTrue(any(k=='error' and 'OPENAI_API_KEY' in p for k,p in self.events))

    def test_youtube_first_result_and_bounded_id(self):
        doc='var ytInitialData = '+json.dumps({'contents':[{'videoRenderer':{'videoId':'abcdefghijk','title':{'runs':[{'text':'Primer resultado'}]}}},{'videoRenderer':{'videoId':'zzzzzzzzzzz'}}]})
        self.assertEqual(first_video(doc),('abcdefghijk','Primer resultado'))
        register_video(self.core)
        self.assertEqual(self.core.registry.tools['youtube_play_first'].risk,Risk.MEDIUM)
