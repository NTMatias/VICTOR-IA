"""Comprobación sin red y descarga aislada: la GUI puede cancelar el proceso."""
import hashlib
import json
import os
from pathlib import Path


def model_directory(config):
    name = config.get('whisper_model')
    return config.data_dir / 'models' / hashlib.sha256(name.encode()).hexdigest()[:16]


def complete(path):
    p = Path(path)
    return all((p / name).is_file() and (p / name).stat().st_size > 0
               for name in ('model.bin', 'config.json', 'tokenizer.json'))


def cached_model(config):
    name = config.get('whisper_model')
    for candidate in (Path(name), model_directory(config)):
        if complete(candidate):
            return str(candidate.resolve())
    try:
        from faster_whisper.utils import download_model
        result = download_model(name, local_files_only=True)
        return result if complete(result) else None
    except Exception:
        return None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['check', 'download'])
    parser.add_argument('name')
    parser.add_argument('directory')
    args = parser.parse_args()
    os.environ['HF_HUB_ETAG_TIMEOUT'] = '10'
    os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '30'
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    try:
        from faster_whisper.utils import download_model, _MODELS
        if args.mode == 'check':
            path = next((str(p) for p in (Path(args.name), Path(args.directory)) if complete(p)), None)
            if not path:
                try:
                    candidate = download_model(args.name, local_files_only=True)
                    path = candidate if complete(candidate) else None
                except Exception:
                    path = None
            print(json.dumps({'ready': bool(path)}), flush=True)
            return
        from huggingface_hub import snapshot_download
        from tqdm.auto import tqdm
        class Progress(tqdm):
            def update(self, n=1):
                result = super().update(n)
                # Unidades explícitas: no confundir archivos con bytes ni con % global.
                print(json.dumps({'progress': int(self.n), 'total': self.total,
                                  'unit': self.unit}), flush=True)
                return result
        repo = _MODELS.get(args.name, args.name)
        snapshot_download(repo, local_dir=args.directory, cache_dir=str(Path(args.directory) / '.hub'),
                          allow_patterns=['config.json', 'preprocessor_config.json', 'model.bin',
                                          'tokenizer.json', 'vocabulary.*'],
                          tqdm_class=Progress, max_workers=2, etag_timeout=10)
        if not complete(args.directory):
            raise RuntimeError('incomplete model')
        print(json.dumps({'ready': True}), flush=True)
    except Exception as exc:
        print(json.dumps({'error': 'No se pudo preparar Whisper (' + type(exc).__name__ +
                          '). Revisa Internet, espacio disponible y el nombre del modelo.'}), flush=True)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
