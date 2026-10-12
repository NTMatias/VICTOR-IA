"""App-local Python launcher; no installation, registry edits or credentials copied."""
import ctypes
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parent

def alert(message):
    ctypes.windll.user32.MessageBoxW(None,message,'VICTOR.IA portátil',0x10)

def prepare():
    if sys.platform!='win32' or sys.maxsize<2**32:
        raise RuntimeError('Esta edición necesita Windows 10/11 de 64 bits.')
    if sys.getwindowsversion().build<10240:raise RuntimeError('Esta edición necesita Windows 10/11.')
    directory=ROOT/'runtime'/'webview2'
    executable=directory/'msedgewebview2.exe'
    if not executable.exists():raise RuntimeError('Falta el navegador integrado. Extrae todo el ZIP, no solo el lanzador.')
    if str(ROOT).startswith('\\\\'):raise RuntimeError('Copia VICTOR en una carpeta local, por ejemplo el Escritorio.')
    fs=ctypes.create_unicode_buffer(32)
    if ctypes.windll.kernel32.GetVolumeInformationW(str(ROOT.anchor),None,0,None,None,None,fs,len(fs)) and fs.value!='NTFS':
        raise RuntimeError('Copia la carpeta VICTOR.IA desde la USB al Escritorio antes de abrirla. El navegador integrado de Windows 10 necesita una carpeta local NTFS.')
    if sys.getwindowsversion().build<22000:
        # Only the bundled browser runtime needs these official AppContainer read grants.
        for sid in ('*S-1-15-2-2','*S-1-15-2-1'):
            result=subprocess.run(['icacls',str(directory),'/grant',sid+':(OI)(CI)(RX)'],capture_output=True,timeout=30,
                                  creationflags=subprocess.CREATE_NO_WINDOW,shell=False)
            if result.returncode:raise RuntimeError('No pude preparar el navegador. Extrae VICTOR en tu Escritorio y vuelve a abrirlo.')
    os.environ['WEBVIEW2_BROWSER_EXECUTABLE_FOLDER']=str(directory)
    os.environ['PYTHONIOENCODING']='utf-8'
    return os.environ.copy()

def verify():
    prepare()
    modules=('PySide6.QtWidgets','requests','cryptography','jwt','openai','anthropic','google.genai',
             'faster_whisper','sounddevice','pywebrtc_audio','spotipy','win32api','winpty','PySide6.QtWebEngineWidgets')
    for name in modules:
        importlib.import_module(name);print('OK '+name,flush=True)
    from victor.config import ConfigManager
    from victor.voice.models import cached_model
    from victor.agents.terminal import executable
    config=ConfigManager(ROOT)
    if not cached_model(config):raise RuntimeError('Falta el modelo Whisper local.')
    agents={}
    for agent in ('codex','claude'):
        result=subprocess.run([str(executable(config,agent)),'--version'],capture_output=True,text=True,encoding='utf-8',
                              timeout=25,creationflags=subprocess.CREATE_NO_WINDOW,shell=False)
        if result.returncode:raise RuntimeError('No pude iniciar '+agent+' incluido.')
        agents[agent]=result.stdout.strip()
    print(json.dumps({'python':sys.version.split()[0],'prefix':sys.prefix,'whisper':True,'agents':agents},ensure_ascii=False),flush=True)

def main():
    try:
        if '--verify' in sys.argv:verify();return
        env=prepare()
        python=ROOT/'python'/'pythonw.exe'
        subprocess.Popen([str(python),str(ROOT/'main.py')],cwd=ROOT,env=env,creationflags=subprocess.CREATE_NO_WINDOW,shell=False)
    except Exception as exc:
        message=str(exc) if isinstance(exc,RuntimeError) else 'No pude abrir VICTOR ('+type(exc).__name__+'). Extrae toda la carpeta y ejecuta COMPROBAR VICTOR.bat.'
        if '--verify' in sys.argv:print(message,flush=True)
        else:alert(message)
        raise SystemExit(1)

if __name__=='__main__':main()
