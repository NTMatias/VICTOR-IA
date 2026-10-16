"""Delete only the explicitly retired TTS model/runtime and its dedicated tools."""
import argparse
import json
from pathlib import Path
import shutil

def main():
    root=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    names=['data/tts_latam','data/tts_runtime']
    names += ['victor/voice/'+name+'.py' for name in ('tts_assets','tts_client','tts_compact','tts_worker','tts_setup','tts_maintenance','tts_hardware','tts_engine','tts_benchmark','tts_audio')]
    names += ['tools/'+name+'.py' for name in ('activate_latam_int8','convert_latam_gguf','prepare_latam_int8','tts_gui_probe','tts_low_ram_recycling_probe','validate_latam_architecture','validate_latam_int8','optimization_report')]
    removed=[]
    for name in names:
        path=root/name
        if not path.exists():continue
        resolved=path.resolve()
        if path.is_symlink() or not resolved.is_relative_to(root) or resolved==root:raise RuntimeError('Ruta de retiro insegura.')
        if path.is_dir():
            items=list(path.rglob('*'))
            if any(p.is_symlink() or not p.resolve().is_relative_to(root) for p in items):raise RuntimeError('No se retiran enlaces fuera del proyecto.')
            size=sum(p.stat().st_size for p in items if p.is_file())
            if args.apply:shutil.rmtree(path)
        else:
            size=path.stat().st_size
            if args.apply:path.unlink()
        removed.append({'path':name,'bytes':size})
    result={'apply':args.apply,'files':removed,'total_bytes':sum(x['bytes'] for x in removed)}
    (root/'docs/edge_retirement.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
