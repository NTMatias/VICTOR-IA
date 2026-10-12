"""Reproducible clean Windows x64 directory with a vendored Python runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

SOURCE=Path(__file__).resolve().parents[1]
IGNORED=shutil.ignore_patterns('__pycache__','*.pyc','*.pyo','.cache','.hub')

def copy(source,target):
    if source.is_dir():shutil.copytree(source,target,ignore=IGNORED)
    else:target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)

def build(destination,webview,dependencies=None,public=False):
    dependencies=(dependencies or SOURCE).resolve()
    root=destination.resolve()/'VICTOR.IA'
    if root.exists():raise RuntimeError('La carpeta de salida ya existe. Usa una carpeta nueva para conservar la anterior.')
    root.mkdir(parents=True)
    print('Copiando aplicación y dependencias...',flush=True)
    copy(SOURCE/'victor',root/'victor')
    for name in ('main.py','portable_start.py','requirements.txt','README.md','PORTABLE_CUENTAS.md','.env.example'):
        copy(SOURCE/name,root/name)
    copy(SOURCE/'.env.example',root/'.env')
    for extra in ('docs','RELEASE.md','CHANGELOG.md','THIRD_PARTY_NOTICES.md','VERIFICACION.md'):
        if (SOURCE/extra).exists():copy(SOURCE/extra,root/extra)
    runtime=root/'python';runtime.mkdir()
    base=Path(sys.base_prefix)
    for name in ('python.exe','pythonw.exe','python3.dll','python312.dll','vcruntime140.dll','vcruntime140_1.dll','LICENSE.txt','DLLs','tcl'):
        copy(base/name,runtime/name)
    shutil.copytree(base/'Lib',runtime/'Lib',ignore=lambda folder,names:[name for name in names if name=='__pycache__' or name.endswith(('.pyc','.pyo')) or (Path(folder)==base/'Lib' and name in ('site-packages','test'))])
    copy(dependencies/'.venv'/'Lib'/'site-packages',runtime/'Lib'/'site-packages')
    (runtime/'python312._pth').write_text('Lib\nLib/site-packages\nDLLs\n..\nimport site\n',encoding='utf-8')
    print('Incluyendo navegador, voz local y agentes de programación...',flush=True)
    copy(webview,root/'runtime'/'webview2')
    node=shutil.which('node')
    if not node:raise RuntimeError('No se encontró Node.js para la versión portátil.')
    copy(Path(node),root/'runtime'/'node'/'node.exe')
    license_path=Path(node).with_name('LICENSE')
    if license_path.exists():copy(license_path,root/'runtime'/'node'/'LICENSE')
    else:
        import subprocess,requests
        version=subprocess.check_output([node,'--version'],text=True).strip()
        license_response=requests.get('https://raw.githubusercontent.com/nodejs/node/'+version+'/LICENSE',timeout=25)
        license_response.raise_for_status();(root/'runtime'/'node'/'LICENSE').write_bytes(license_response.content)
    copy(dependencies/'data'/'agent_cli',root/'data'/'agent_cli')
    if public:
        # Do not ship personal vocabulary, corrections, voice selection or theme preferences.
        sys.path.insert(0,str(SOURCE))
        from victor.config import DEFAULTS
        saved=dict(DEFAULTS)
    else:
        saved=json.loads((dependencies/'data'/'config.json').read_text(encoding='utf-8'))
    cfg={key:saved[key] for key in ('theme','language','whisper_model','edge_voice','voice_rate','tts_backend','voice_vocabulary','voice_corrections') if key in saved}
    cfg.update(provider='OpenAI',auth_methods={'OpenAI':'account','Gemini':'api'},account_models={'OpenAI':'','Gemini':'auto'},
               voice_mode='manual',voice_background_listening=False,voice_enabled=False,voice_backend='whisper',
               fallback=[],gemini_account_enabled=False,microphone='')
    (root/'data'/'config.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    model=hashlib.sha256(cfg.get('whisper_model','base').encode()).hexdigest()[:16]
    copy(dependencies/'data'/'models'/model,root/'data'/'models'/model)
    if (SOURCE/'THIRD_PARTY_NOTICES.md').exists():copy(SOURCE/'THIRD_PARTY_NOTICES.md',root/'THIRD_PARTY_NOTICES.md')
    (root/'workspace').mkdir()
    for name,verify in (('ABRIR VICTOR.bat',False),('COMPROBAR VICTOR.bat',True)):
        content='@echo off\ncd /d "%~dp0"\n"%~dp0python\\python.exe" -X utf8 "%~dp0portable_start.py"'+(' --verify\npause\n' if verify else '\n')
        (root/name).write_text(content,encoding='ascii',newline='\r\n')
    (root/'LEEME_USB.txt').write_text(
        'VICTOR.IA PORTATIL - Windows 10/11 de 64 bits\n\n'
        '1. Extrae TODO el ZIP en el Escritorio.\n2. Abre VICTOR.IA/ABRIR VICTOR.bat.\n'
        '3. Ajustes > Inteligencia artificial: conecta una cuenta ChatGPT elegible o guarda una API key.\n'
        'Gemini SOLO usa API key: Obtener API key de Gemini abre https://aistudio.google.com/apikey.\n'
        'No hay inicio de sesion Google para Gemini ni conector Gemini CLI.\n\n'
        'Pide generar una imagen para elegir ChatGPT/OpenAI o Gemini; requiere clave API propia.\n'
        'Agentes de programacion contiene Codex y Claude Code oficiales. Claude Code necesita Git Bash.\n'
        'No necesitas Python, VS Code ni Node.js instalados. Los servicios en la nube requieren Internet.\n'
        'No se incluyen claves, sesiones ni mensajes personales. Whisper y ordenes locales no requieren cuenta IA.\n'
        'Spotify/Gmail: configura OAuth en .env. WhatsApp: vincula el QR.\n'
        'No ejecutes dentro del ZIP ni en USB FAT32; extrae a una carpeta local NTFS.\n'
        'Lee PORTABLE_CUENTAS.md para instrucciones completas.\n',encoding='utf-8-sig')
    files={}
    for path in root.rglob('*'):
        if path.is_file():
            if path.stat().st_size>=4_000_000_000:raise RuntimeError('Archivo incompatible con FAT32: '+str(path))
            files[path.relative_to(root).as_posix()]=hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
    manifest={'files':files,'bytes':sum((root/name).stat().st_size for name in files),'python':sys.version.split()[0]}
    (root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'root':str(root),'files':len(files),'bytes':manifest['bytes']}),flush=True)
    return root

def archive(root,target):
    manifest=json.loads((root/'MANIFEST.json').read_text())
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for index,(name,digest) in enumerate(manifest['files'].items(),1):
            path=root/name
            with path.open('rb') as f:
                if hashlib.file_digest(f,'sha256').hexdigest()!=digest:raise RuntimeError('Cambió un archivo desde la compilación: '+name)
            z.write(path,'VICTOR.IA/'+name)
            if index%3000==0:print(f'Empaquetados {index}/{len(manifest["files"])} archivos',flush=True)
        z.write(root/'MANIFEST.json','VICTOR.IA/MANIFEST.json')
    print(json.dumps({'zip':str(target),'bytes':target.stat().st_size}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--destination',type=Path);parser.add_argument('--webview',type=Path)
    parser.add_argument('--archive',type=Path);parser.add_argument('--root',type=Path)
    parser.add_argument('--dependencies',type=Path,help='Installation containing .venv and clean distributable CLI/model files')
    parser.add_argument('--public',action='store_true',help='Use defaults instead of personal preferences')
    args=parser.parse_args()
    if args.archive:archive(args.root,args.archive)
    else:build(args.destination,args.webview,args.dependencies,args.public)
