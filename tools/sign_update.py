"""Publisher-only Ed25519 signing. The private key stays encrypted on this Windows PC."""
import argparse
import base64
import hashlib
import json
import ast
import zipfile
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,PublicFormat,NoEncryption
from victor.credentials import CredentialStore
from victor.updates import version

def main():
    p=argparse.ArgumentParser();p.add_argument('--init-keys',action='store_true');p.add_argument('--version');p.add_argument('--asset',type=Path);p.add_argument('--url');p.add_argument('--output',type=Path,default=Path('update.json'));args=p.parse_args()
    root=Path(__file__).resolve().parents[1];directory=root/'data/update_signing';private=directory/'private.dpapi';public=directory/'public.hex'
    if args.init_keys:
        if private.exists():raise ValueError('La clave ya existe. No se reemplazó.')
        key=Ed25519PrivateKey.generate();directory.mkdir(parents=True,exist_ok=True)
        private.write_bytes(CredentialStore.crypt(key.private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption())))
        public.write_text(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex())
        print('Claves creadas. Copia únicamente public.hex a la configuración pública; respalda la clave privada cifrada.');return
    if not args.version or not args.asset or not args.url:raise ValueError('Indica --version, --asset y --url.')
    version(args.version)
    with zipfile.ZipFile(args.asset) as archive:
        candidates=[entry for entry in archive.infolist() if entry.filename.endswith('/victor/version.py') or entry.filename=='victor/version.py']
        if len(candidates)!=1 or candidates[0].file_size>4096:raise ValueError('El ZIP debe incluir un único victor/version.py.')
        tree=ast.parse(archive.read(candidates[0]).decode('utf-8'))
        installed=next((ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='VERSION' for target in node.targets)),None)
        if installed is None or version(installed)!=version(args.version):raise ValueError('La versión del ZIP no coincide con la publicación. Actualiza victor/version.py antes de empaquetar.')
    checksum=hashlib.sha256()
    with args.asset.open('rb') as stream:
        for block in iter(lambda:stream.read(1024**2),b''):checksum.update(block)
    record={'version':args.version,'asset_url':args.url,'size':args.asset.stat().st_size,'sha256':checksum.hexdigest()}
    payload=json.dumps(record,separators=(',',':'),sort_keys=True).encode()
    key=Ed25519PrivateKey.from_private_bytes(CredentialStore.crypt(private.read_bytes(),True))
    args.output.write_text(json.dumps({'payload':base64.b64encode(payload).decode(),'signature':base64.b64encode(key.sign(payload)).decode()},indent=2),encoding='utf-8')
    print('Aviso firmado. Publica el ZIP y update.json juntos en el release de GitHub.')

if __name__=='__main__':main()
