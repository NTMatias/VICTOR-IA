import base64
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import queue
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock,patch
from types import SimpleNamespace as NS
from PIL import Image
from victor.ai.images import ImageArchive,ImageService,MODELS,wants_image,image_capability_question,api_error,openai_image,gemini_image,normalize_image
from victor.config import ConfigManager
from victor.database import Database
from victor.history import ConversationManager
from victor.agents.terminal import AgentTerminal,executable
from victor.errors import VictorError,Cancelled


def png():
    data=io.BytesIO();Image.new('RGB',(256,256),'#83AFFF').save(data,'PNG');return data.getvalue()


class Images(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.cfg=ConfigManager(self.root)
        self.db=Database(self.cfg.data_dir/'test.db');self.archive=ImageArchive(self.cfg,self.db);self.history=ConversationManager(self.db)
    def tearDown(self):self.temp.cleanup()
    def test_image_request_intents_and_questions(self):
        for text in ('genera una imagen de un perro','Crea una foto de Ecuador','VICTOR, dibújame un gato','puedes generar una imagen de un avión','quisiera que generes una ilustración','quiero que me generes una imagen de un iPhone','puedes dibujarme un gato'):
            self.assertTrue(wants_image(text),text)
        for text in ('cómo generar una imagen','no generes una imagen','analiza esta imagen','qué es una imagen','reproduce una foto en Spotify'):
            self.assertFalse(wants_image(text),text)
        self.assertTrue(image_capability_question('una pregunta, tú puedes generar imágenes?'))
        self.assertFalse(image_capability_question('Puedes generar una imagen de un gato?'))
    def test_openai_uses_key_and_supported_generation_api(self):
        client=Mock();client.__enter__=Mock(return_value=client);client.__exit__=Mock(return_value=False)
        client.images.generate.return_value=NS(data=[NS(b64_json=base64.b64encode(png()).decode())])
        with patch('openai.OpenAI',return_value=client) as factory:
            blob=openai_image({'key':'fixture-secret','model':MODELS['OpenAI'],'prompt':'Un gato'})
        self.assertEqual(blob,png());self.assertEqual(factory.call_args.kwargs['api_key'],'fixture-secret')
        self.assertEqual(client.images.generate.call_args.kwargs['output_format'],'png')
        self.assertEqual(client.images.generate.call_args.kwargs['n'],1)
    def test_gemini_interactions_and_native_images_exclude_thoughts(self):
        encoded=base64.b64encode(png()).decode();response=Mock()
        response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        response.json.return_value={'status':'completed','steps':[{'type':'thought','content':[{'type':'image','data':'ignore'}]},{'type':'model_output','content':[{'type':'image','data':encoded,'mime_type':'image/png'}]}]}
        with patch('requests.post',return_value=response) as request:
            self.assertEqual(gemini_image({'key':'synthetic','model':MODELS['Gemini'],'prompt':'Un gato'}),png())
            self.assertTrue(request.call_args.args[0].endswith('/interactions'))
            self.assertFalse(request.call_args.kwargs['json']['store'])
        response.json.return_value={'candidates':[{'finishReason':'STOP','content':{'parts':[{'thought':True,'inlineData':{'data':'bad'}},{'inlineData':{'mimeType':'image/png','data':encoded}}]}}]}
        with patch('requests.post',return_value=response):
            self.assertEqual(gemini_image({'key':'synthetic','model':'gemini-3.1-flash-image','prompt':'Un gato'}),png())
        response.json.return_value={'status':'in_progress','output_image':{'data':encoded}}
        with patch('requests.post',return_value=response),self.assertRaises(VictorError):
            gemini_image({'key':'synthetic','model':MODELS['Gemini'],'prompt':'x'})
    def test_verified_image_history_roundtrip_and_path_restriction(self):
        path=self.archive.directory/('a'*32+'.png');dimensions=normalize_image(png(),path)
        conv=self.history.create();self.history.add(conv,'user','Genera imagen')
        record=self.archive.store(conv,path,'Gemini',MODELS['Gemini'],dimensions)
        other=ImageArchive(self.cfg,self.db);self.assertEqual(other.attachment(record['message_id'])['path'],str(path))
        with self.assertRaises(VictorError):other.store(conv,self.root/'not-trusted.png','Gemini','m',dimensions)
        with self.assertRaises(Exception):normalize_image(b'<script>bad</script>',path)
        self.history.delete(conv);self.assertIsNone(other.attachment(record['message_id']))
    def test_no_key_or_invalid_model_never_starts_worker(self):
        service=ImageService(self.cfg,self.archive)
        with patch.object(self.cfg,'api_key',return_value=''),patch('subprocess.Popen') as spawn:
            with self.assertRaises(VictorError):service.generate('image','OpenAI',MODELS['OpenAI'],threading.Event())
            with self.assertRaises(VictorError):service.generate('image','Gemini','--yolo',threading.Event())
            spawn.assert_not_called()
    def test_quota_message_identifies_billing_and_never_exposes_response(self):
        exc=RuntimeError('private-response-do-not-display');exc.status_code=429
        message=api_error(exc,'Gemini')
        self.assertIn('429',message);self.assertIn('facturación',message);self.assertIn('No se cambió',message)
        self.assertNotIn('private-response',message)
    def test_cancel_terminates_real_worker_without_network(self):
        import subprocess
        fixture=self.root/'image_fixture.py'
        fixture.write_text('import sys,time\nsys.stdin.buffer.readline()\ntime.sleep(30)\n',encoding='utf-8')
        factory=subprocess.Popen;processes=[]
        def spawn(args,**kwargs):
            self.assertNotIn('synthetic-key',' '.join(args))
            process=factory([sys.executable,'-X','utf8',str(fixture)],**kwargs);processes.append(process);return process
        cancel=threading.Event();timer=threading.Timer(.3,cancel.set);timer.start();start=time.monotonic()
        try:
            with patch.object(self.cfg,'api_key',return_value='synthetic-key'),patch('subprocess.Popen',side_effect=spawn):
                with self.assertRaises(Cancelled):ImageService(self.cfg,self.archive).generate('image','Gemini',MODELS['Gemini'],cancel)
            self.assertLess(time.monotonic()-start,3);self.assertEqual(len(processes),1);self.assertIsNotNone(processes[0].poll())
        finally:
            timer.cancel()
            for process in processes:
                if process.poll() is None:process.kill();process.wait()


class Terminal(unittest.TestCase):
    def test_conpty_unicode_input_resize_and_close(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);cfg=ConfigManager(root);fixture=root/'terminal_fixture.py'
            fixture.write_text('import sys\nprint("READY ñ á ✓",flush=True)\nprint("INPUT:"+input(),flush=True)\n',encoding='utf-8')
            terminal=AgentTerminal(cfg,'codex');terminal.start(root,[sys.executable,'-X','utf8',str(fixture)])
            events=[];deadline=time.monotonic()+8
            try:
                while time.monotonic()<deadline:
                    try:events.append(terminal.events.get(timeout=.1))
                    except queue.Empty:pass
                    if 'READY' in ''.join(value for kind,value in events if kind=='output'):break
                self.assertIn('READY ñ á', ''.join(value for kind,value in events if kind=='output'))
                terminal.resize(100,30);terminal.write('texto de prueba\r')
                deadline=time.monotonic()+6
                while terminal.running() and time.monotonic()<deadline:
                    try:events.append(terminal.events.get(timeout=.1))
                    except queue.Empty:pass
                self.assertIn('INPUT:texto de prueba',''.join(value for kind,value in events if kind=='output'))
                self.assertFalse(terminal.running())
            finally:terminal.stop();terminal.thread.join(5)
    def test_stop_while_waiting_and_cli_discovery(self):
        with tempfile.TemporaryDirectory() as folder:
            cfg=ConfigManager(Path(folder));terminal=AgentTerminal(cfg,'claude')
            terminal.start(Path(folder),[sys.executable,'-X','utf8','-c','print("READY",flush=True);input()'])
            deadline=time.monotonic()+6
            while terminal.process is None and terminal.running() and time.monotonic()<deadline:time.sleep(.05)
            terminal.stop();terminal.thread.join(5);self.assertFalse(terminal.running())
            with patch('shutil.which',return_value=None):self.assertEqual(executable(cfg,'claude'),'')


class UI(unittest.TestCase):
    def pump(self,qt,seconds=.1):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:qt.processEvents();time.sleep(.005)
    def test_chooser_image_card_reload_and_agent_terminal_rendering(self):
        from PySide6.QtWidgets import QApplication,QDialog
        from tests.gui_support import authenticated_gui as GUIManager
        qt=QApplication.instance() or QApplication([]);qt.setQuitOnLastWindowClosed(False)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as folder:
            app=GUIManager(ConfigManager(Path(folder)))
            try:
                app.show();app.resize(1320,960)
                self.assertTrue(all(page.surface is None for page in app.agent_pages.values()))
                self.assertEqual(set(app.settings.account_panels),{'OpenAI'})
                app.navigate('ia');app.settings.select_provider('Gemini');self.pump(qt)
                self.assertTrue(app.settings.model_stack.isVisible())
                self.assertTrue(app.settings.account_cards['Gemini'].isVisible())
                with patch('victor.gui.panels.webbrowser.open') as browser:
                    app.settings.gemini_key_link.click()
                    browser.assert_called_once_with('https://aistudio.google.com/apikey')
                app.navigate('home')
                with patch.object(app.core,'submit') as submit:
                    app.send('una pregunta, tú puedes generar imágenes?')
                    self.assertIsNone(app.images.pending);submit.assert_not_called()
                    self.assertIn('Sí, puedo generar imágenes',app.core.history.messages(app.conversation_id)[-1]['content'])
                app.quick_buttons[-1].click();self.assertIsNotNone(app.images.pending)
                self.assertFalse(app.images.pending.generate.isEnabled());app.images.pending.reject();self.pump(qt)
                self.assertEqual(app.groups['Agentes de programación'],[('codex','Codex'),('claude','Claude Code')])
                app.send('Genera una imagen de prueba')
                chooser=app.images.pending;self.assertIsNotNone(chooser);self.pump(qt)
                with patch.object(app.config,'api_key',return_value='fixture-never-sent'):
                    chooser.provider.setCurrentIndex(1);chooser.refresh()
                    self.assertTrue(chooser.generate.isEnabled())
                    ready=threading.Event()
                    def generated(*args):
                        if not ready.wait(5):raise RuntimeError('fixture timeout')
                        path=app.images.archive.directory/('b'*32+'.png');normalize_image(png(),path);return path,{'width':256,'height':256}
                    with patch.object(app.images.service,'generate',side_effect=generated):
                        chooser.accept();self.pump(qt,.1)
                        app.load_conversation(app.conversation_id);self.pump(qt,.1)
                        ready.set();self.pump(qt,.7)
                rows=app.core.history.messages(app.conversation_id)
                self.assertEqual(rows[-1]['role'],'assistant')
                self.assertIsNotNone(app.images.archive.attachment(rows[-1]['id']))
                app.load_conversation(app.conversation_id);self.pump(qt)
                self.assertTrue(app.chat_body.findChildren(__import__('victor.gui.images',fromlist=['ImageCard']).ImageCard))
                page=app.agent_pages['codex'];app.navigate('codex');deadline=time.monotonic()+10
                while not page.web_ready and time.monotonic()<deadline:self.pump(qt,.05)
                self.assertTrue(page.web_ready,'Local xterm failed to load or connect the channel')
                fixture=Path(folder)/'ui_fixture.py';fixture.write_text('print("CODING TERMINAL ñ",flush=True)\n',encoding='utf-8')
                page.backend.start(Path(folder),[sys.executable,'-X','utf8',str(fixture)])
                self.pump(qt,2)
                result=[];page.surface.page().runJavaScript('window.victorTerminal.text()',result.append)
                deadline=time.monotonic()+3
                while not result and time.monotonic()<deadline:self.pump(qt,.05)
                self.assertIn('CODING TERMINAL ñ',result[0])
                app.config.save({'theme':'Light'});app.refresh_config();self.pump(qt)
                app.resize(560,860);self.pump(qt,.2)
                self.assertEqual(app.page_widgets['codex'].horizontalScrollBar().maximum(),0)
            finally:
                if app.images.pending:app.images.pending.reject()
                app.window_transitions.close_visual_done=True;app.close();deadline=time.monotonic()+12
                while not app.closed_cleanly and time.monotonic()<deadline:self.pump(qt,.1)
                self.assertTrue(app.closed_cleanly)

if __name__=='__main__':unittest.main()
