"""Public deployment settings; secret/service-role keys are forbidden in clients."""
import base64
import json
import re
from pathlib import Path

def deployment(root):
    path=Path(root)/'deployment.json'
    if not path.is_file():return {}
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict):raise ValueError('Configuración de distribución inválida.')
    if set(value)-{'cloud','updates'}:raise ValueError('La configuración pública contiene campos no admitidos.')
    cloud=value.get('cloud',{})
    if not isinstance(cloud,dict) or set(cloud)-{'enabled','url','publishable_key'}:raise ValueError('Campos de nube inválidos; no incluyas secretos.')
    updates=value.get('updates',{})
    if not isinstance(updates,dict) or set(updates)-{'enabled','manifest_url','public_key_hex'}:raise ValueError('Campos de actualización inválidos; no incluyas claves privadas.')
    if str(cloud.get('publishable_key','')).startswith('sb_secret_'):raise ValueError('No incluyas claves secretas en la distribución.')
    key=cloud.get('publishable_key','')
    if isinstance(key,str) and key.count('.')==2:
        try:
            part=key.split('.')[1];role=json.loads(base64.urlsafe_b64decode(part+'='*(-len(part)%4))).get('role')
        except Exception:raise ValueError('Clave publicable inválida.') from None
        if role!='anon':raise ValueError('No se distribuyen claves service_role ni tokens de usuario.')
    if cloud.get('enabled'):
        if not re.fullmatch(r'https://[a-z0-9-]+\.supabase\.co',cloud.get('url','')):raise ValueError('Usa la dirección HTTPS de tu proyecto Supabase.')
        key=cloud.get('publishable_key','')
        if not key.startswith('sb_publishable_'):
            try:
                part=key.split('.')[1];claims=json.loads(base64.urlsafe_b64decode(part+'='*(-len(part)%4)))
                if claims.get('role')!='anon':raise ValueError()
            except Exception:raise ValueError('El cliente solo admite una clave publicable; nunca una clave secreta o service_role.') from None
    return value
