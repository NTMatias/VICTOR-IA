"""Windows ConPTY: real interactive CLIs, bounded UI output and full VT input."""
import os
from pathlib import Path
import queue
import shutil
import threading
import time
from victor.errors import VictorError


def executable(config,agent):
    if agent not in ('codex','claude'):raise VictorError('Agente desconocido.')
    base=config.data_dir/'agent_cli'/'node_modules'
    if agent=='codex':
        candidates=list((base/'@openai'/'codex-win32-x64').glob('vendor/*/*/codex.exe'))
    else:candidates=[base/'@anthropic-ai'/'claude-code-win32-x64'/'claude.exe']
    native=shutil.which(agent+'.exe')
    if native:candidates.append(Path(native))
    shim=shutil.which(agent+'.cmd') or shutil.which(agent)
    if shim:
        modules=Path(shim).parent/'node_modules'
        if agent=='codex':candidates += list((modules/'@openai').glob('codex*/vendor/*/*/codex.exe'))
        else:candidates += [modules/'@anthropic-ai'/'claude-code'/'bin'/'claude.exe',modules/'@anthropic-ai'/'claude-code-win32-x64'/'claude.exe']
    return next((str(path.resolve()) for path in candidates if path.is_file()),'')


class AgentTerminal:
    def __init__(self,config,agent):
        self.config=config;self.agent=agent;self.process=None;self.thread=None;self.events=queue.Queue(maxsize=256)
        self.stopped=threading.Event();self.lock=threading.RLock();self.rows=28;self.cols=110
    def running(self):return bool(self.thread and self.thread.is_alive())
    def publish(self,kind,value):
        while not self.stopped.is_set():
            try:self.events.put((kind,value),timeout=.1);return
            except queue.Full:continue
    def start(self,directory,command=None,model=''):
        if self.running():raise VictorError('Ya hay una sesión de este agente abierta.')
        root=Path(directory).expanduser().resolve()
        if not root.is_dir():raise VictorError('Elige una carpeta de proyecto existente.')
        args=command or [executable(self.config,self.agent)]
        if not args[0]:raise VictorError('No encontré el CLI oficial. Instálalo desde la documentación del agente.')
        self.stopped.clear();self.events=queue.Queue(maxsize=256)
        def run():
            process=None
            try:
                from winpty import PtyProcess,Backend
                env=os.environ.copy()
                # Keep official agent account sessions, without inheriting paid API credentials from VICTOR.
                for key in ('OPENAI_API_KEY','ANTHROPIC_API_KEY','CODEX_API_KEY','GEMINI_API_KEY','GOOGLE_API_KEY'):
                    env.pop(key,None)
                node=self.config.root/'runtime'/'node'
                if node.exists():env['PATH']=str(node)+os.pathsep+env.get('PATH','')
                env['TERM']='xterm-256color';env['COLORTERM']='truecolor';env.pop('NO_COLOR',None)
                launch=list(args)
                if self.agent=='codex' and command is None:
                    from victor.agents.codex_models import list_models,select_model
                    from victor.errors import check_cancel
                    self.publish('status','Consultando los modelos del CLI oficial…')
                    models=list_models(args[0],str(root),env,self.stopped);selected=select_model(models,model)
                    self.publish('models',{'items':models,'selected':selected['id']})
                    launch+=['--model',selected['id']]
                    if selected.get('effort') in ('none','minimal','low','medium','high','xhigh','max','ultra'):
                        launch+=['-c','model_reasoning_effort="'+selected['effort']+'"']
                    check_cancel(self.stopped)
                process=PtyProcess.spawn(launch,cwd=str(root),env=env,dimensions=(self.rows,self.cols),backend=Backend.ConPTY)
                with self.lock:self.process=process
                if self.stopped.is_set():process.close(force=True);return
                self.publish('started',str(root))
                while not self.stopped.is_set():
                    try:chunk=process.read(32768)
                    except EOFError:break
                    if chunk:self.publish('output',chunk)
                    if not process.isalive():break
                if not self.stopped.is_set():self.publish('exit',process.exitstatus)
            except Exception as exc:
                if not self.stopped.is_set():self.publish('error',str(exc) if isinstance(exc,VictorError) else 'No pude abrir la terminal del agente ('+type(exc).__name__+'). Comprueba Windows 10 de 64 bits y el CLI instalado.')
            finally:
                with self.lock:self.process=None
                if process:
                    try:process.close(force=True)
                    except Exception:pass
        self.thread=threading.Thread(target=run,name='victor-'+self.agent+'-terminal',daemon=True);self.thread.start()
    def write(self,text):
        if not isinstance(text,str) or len(text)>1048576:return
        with self.lock:
            if self.process and not self.stopped.is_set():
                try:self.process.write(text)
                except (OSError,EOFError):pass
    def resize(self,cols,rows):
        self.cols=max(20,min(400,int(cols)));self.rows=max(5,min(200,int(rows)))
        with self.lock:
            if self.process:
                try:self.process.setwinsize(self.rows,self.cols)
                except (OSError,EOFError):pass
    def interrupt(self):self.write('\x03')
    def stop(self):
        self.stopped.set()
        def close():
            with self.lock:process=self.process
            if process:
                try:process.close(force=True)
                except Exception:pass
        threading.Thread(target=close,name='victor-terminal-close',daemon=True).start()
