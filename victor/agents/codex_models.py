"""Discover models through the installed official CLI, without an inference request."""
import json
import queue
import re
import subprocess
import threading
import time
from victor.errors import VictorError,check_cancel


def list_models(executable,directory,env,cancel):
    process=subprocess.Popen([executable,'app-server'],cwd=directory,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL,text=True,encoding='utf-8',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),shell=False)
    events=queue.Queue(maxsize=128)
    def read():
        try:
            for line in iter(process.stdout.readline,''):
                if len(line)>4_000_000:continue
                try:events.put_nowait(json.loads(line))
                except (ValueError,queue.Full):continue
        except (OSError,ValueError):pass
    reader=threading.Thread(target=read,name='victor-codex-models',daemon=True);reader.start()
    deadline=time.monotonic()+20
    def send(value):process.stdin.write(json.dumps(value)+'\n');process.stdin.flush()
    def reply(identity):
        while time.monotonic()<deadline:
            check_cancel(cancel)
            try:result=events.get(timeout=.1)
            except queue.Empty:
                if process.poll() is not None:break
                continue
            if isinstance(result,dict) and result.get('id')==identity:
                if result.get('error'):raise VictorError('Codex no pudo consultar sus modelos. Revisa la conexión y el inicio de sesión del CLI.')
                return result.get('result',{})
        raise VictorError('No pude obtener los modelos de Codex. Revisa Internet y vuelve a abrir la sesión.')
    try:
        send({'id':0,'method':'initialize','params':{'clientInfo':{'name':'victor_ia','title':'VICTOR.IA','version':'1.0'}}})
        reply(0);send({'method':'initialized','params':{}})
        models=[];cursor=None
        for identity in range(1,6):
            params={'limit':100,'includeHidden':False}
            if cursor:params['cursor']=cursor
            send({'id':identity,'method':'model/list','params':params});result=reply(identity)
            for row in result.get('data',[]):
                model=row.get('model') or row.get('id')
                if not row.get('hidden') and isinstance(model,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}',model):
                    models.append({'id':model,'label':str(row.get('displayName') or model)[:200],
                                   'default':row.get('isDefault') is True,'effort':row.get('defaultReasoningEffort')})
            cursor=result.get('nextCursor')
            if not cursor:break
        if not models:raise VictorError('Codex no devolvió modelos disponibles. Conecta una cuenta compatible en el CLI.')
        return models
    finally:
        if process.poll() is None:process.terminate()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)
        for stream in (process.stdin,process.stdout):
            try:stream.close()
            except OSError:pass
        reader.join(1)


def select_model(models,preferred=''):
    if preferred:
        selected=next((row for row in models if row['id']==preferred),None)
        if not selected:raise VictorError('El modelo elegido ya no aparece en Codex. Elige Automático y abre una nueva sesión.')
        return selected
    return next((row for row in models if row['default']),models[0])
