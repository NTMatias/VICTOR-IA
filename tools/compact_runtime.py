"""Remove only runtime-irrelevant compiler archives and reproducible bytecode."""
import argparse
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def candidates(root=ROOT):
    root=Path(root).resolve()
    result=list((root/'data/tts_runtime/env/Lib/site-packages/torch/lib').glob('*.lib'))
    for directory in ('victor','tools','tests','.venv','data/tts_runtime/env','data/tts_runtime/source'):
        for path in (root/directory).rglob('*.pyc'):
            if '__pycache__' in path.parts:result.append(path)
    for path in result:
        if not path.resolve().is_relative_to(root):raise RuntimeError('Cleanup target escapes project')
        if path.is_symlink():raise RuntimeError('Refusing symbolic cleanup target')
    return sorted(set(result))

def trim_torch(root=ROOT):
    removed=[]
    for path in candidates(root):
        size=path.stat().st_size
        try:path.unlink()
        except PermissionError:continue
        removed.append({'path':str(path.relative_to(root)),'bytes':size})
    return removed

def deduplicate_agent(root=ROOT):
    import hashlib
    def digest(path):
        checksum=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024**2),b''):checksum.update(block)
        return checksum.hexdigest()
    root=Path(root).resolve();base=root/'data/agent_cli/node_modules/@anthropic-ai'
    source=base/'claude-code-win32-x64/claude.exe';target=base/'claude-code/bin/claude.exe'
    if not source.is_file() or not target.is_file() or source.samefile(target):return 0
    for file in (source,target):
        if file.is_symlink() or not file.resolve().is_relative_to(root):raise RuntimeError('Ruta de agente inválida.')
    if source.stat().st_size!=target.stat().st_size or digest(source)!=digest(target):return 0
    temporary=target.with_suffix('.hardlink-tmp')
    if temporary.exists():raise RuntimeError('Conserva primero el archivo temporal de deduplicación existente.')
    try:
        os.link(source,temporary);temporary.replace(target)
    finally:
        if temporary.exists():temporary.unlink()
    return source.stat().st_size

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    items=candidates();report={'apply':args.apply,'candidate_bytes':sum(p.stat().st_size for p in items),'candidate_files':len(items)}
    if args.apply:
        report['removed']=trim_torch()
        report['hardlink_bytes_saved']=deduplicate_agent()
        previous=ROOT/'docs/runtime_cleanup.json'
        if previous.is_file():report['previous_cleanup']=json.loads(previous.read_text())
    else:report['files']=[str(p.relative_to(ROOT)) for p in items]
    (ROOT/'docs').mkdir(exist_ok=True)
    (ROOT/'docs/runtime_cleanup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Removed' if args.apply else 'Candidates',report['candidate_bytes'],'bytes')
if __name__=='__main__':main()
