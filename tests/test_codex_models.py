import json,sys,tempfile,threading,time
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
from victor.agents.codex_models import list_models,select_model
from victor.errors import VictorError,Cancelled


class Models(unittest.TestCase):
    def test_account_catalog_default_overrides_retired_global_model(self):
        rows=[{'id':'available-custom-model','default':True},{'id':'another-model','default':False}]
        self.assertEqual(select_model(rows)['id'],'available-custom-model')
        self.assertEqual(select_model(rows,'another-model')['id'],'another-model')
        with self.assertRaises(VictorError):select_model(rows,'retired-model')
    def test_real_jsonrpc_fixture_pagination_hidden_models_and_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            script=Path(folder)/'rpc.py'
            script.write_text('''import sys,json
for line in sys.stdin:
 r=json.loads(line)
 if r['method']=='initialize':out={}
 elif r['method']=='initialized':continue
 elif r['params'].get('cursor'):out={'data':[{'model':'second-model','displayName':'Second','isDefault':True}],'nextCursor':None}
 else:out={'data':[{'model':'hidden-model','hidden':True},{'model':'first-model','isDefault':False}],'nextCursor':'page2'}
 print(json.dumps({'id':r['id'],'result':out}),flush=True)
''',encoding='utf-8')
            real=subprocess.Popen;processes=[]
            def spawn(args,**kwargs):
                self.assertEqual(args[1],'app-server')
                p=real([sys.executable,'-X','utf8',str(script)],**kwargs);processes.append(p);return p
            with patch('subprocess.Popen',side_effect=spawn):
                rows=list_models('codex.exe',folder,None,threading.Event())
            self.assertEqual([r['id'] for r in rows],['first-model','second-model']);self.assertEqual(select_model(rows)['id'],'second-model')
            self.assertIsNotNone(processes[0].poll())
    def test_cancel_stops_server_before_starting_a_session(self):
        with tempfile.TemporaryDirectory() as folder:
            script=Path(folder)/'slow.py';script.write_text('import sys,time\nsys.stdin.readline()\ntime.sleep(30)\n')
            real=subprocess.Popen;processes=[]
            def spawn(args,**kwargs):
                p=real([sys.executable,str(script)],**kwargs);processes.append(p);return p
            cancel=threading.Event();timer=threading.Timer(.2,cancel.set);timer.start();start=time.monotonic()
            try:
                with patch('subprocess.Popen',side_effect=spawn),self.assertRaises(Cancelled):list_models('codex.exe',folder,None,cancel)
                self.assertLess(time.monotonic()-start,3);self.assertIsNotNone(processes[0].poll())
            finally:timer.cancel()

if __name__=='__main__':unittest.main()
