"""Supabase email accounts. No password storage, key upload or local-profile migration."""
import json
import os
from pathlib import Path
import threading
import time
import requests
from .credentials import CredentialStore
from .version import VERSION

class CloudAuth:
    cloud=True
    def __init__(self,data_dir,settings):
        self.data_dir=Path(data_dir);self.settings=settings;self.authenticated=False;self.session=None;self.lock=threading.RLock()
        self.session_file=self.data_dir/'cloud_session.dpapi';self.http=requests.Session();self.owner_id=None;self.record_thread=None
    def is_configured(self):return True
    def username(self):return (self.session or {}).get('user',{}).get('email','')
    def get_hint(self):return ''
    def _request(self,path,body=None,method='POST',authenticated=False):
        headers={'apikey':self.settings['publishable_key'],'Content-Type':'application/json'}
        if authenticated:
            if not self.authenticated or not self.session:raise ValueError('Inicia sesión en la nube.')
            if time.time()+60>=self.session.get('expires_at',0):self._refresh()
            headers['Authorization']='Bearer '+self.session['access_token']
        try:
            with self.http.request(method,self.settings['url']+path,json=body,headers=headers,timeout=(5,15),allow_redirects=False) as response:
                if not 200<=response.status_code<300:
                    if response.status_code==429:raise ValueError('Demasiados intentos. Espera antes de volver a probar.')
                    try:code=response.json().get('code','')
                    except (ValueError,AttributeError):code=''
                    if code=='email_address_not_authorized':raise ValueError('El servicio de correo de VICTOR aún está en modo de pruebas. El administrador debe configurar SMTP antes de admitir registros públicos.')
                    raise ValueError('No se pudo completar el acceso. Revisa los datos, confirma tu correo o comprueba Internet.')
                return response.json() if response.content else {}
        except requests.RequestException:raise ValueError('No se pudo conectar con las cuentas de VICTOR. Comprueba Internet.') from None
    def signup(self,email,password):
        if '@' not in email or not 8<=len(password)<=256:raise ValueError('Escribe un correo válido y una contraseña de al menos 8 caracteres.')
        payload=self._request('/auth/v1/signup',{'email':email,'password':password})
        # Confirmation is required for production. Do not trust metadata for admin privileges.
        if payload.get('access_token'):self._accept(payload);return True
        raise ValueError('Cuenta creada: revisa tu correo y confírmalo antes de entrar.')
    def login(self,email,password):
        self._accept(self._request('/auth/v1/token?grant_type=password',{'email':email,'password':password}))
        return True
    def _accept(self,payload,record_login=True):
        if not payload.get('access_token') or not payload.get('refresh_token') or not payload.get('user',{}).get('id'):raise ValueError('La nube no devolvió una sesión válida.')
        import uuid
        uuid.UUID(payload['user']['id'])
        if self.owner_id and payload['user']['id']!=self.owner_id:raise ValueError('Para cambiar de cuenta, cierra y vuelve a abrir VICTOR. Cada cuenta tiene sus propios datos.')
        with self.lock:
            self.session={k:payload[k] for k in ('access_token','refresh_token','user')}
            self.session['expires_at']=time.time()+float(payload.get('expires_in',3600));self.authenticated=True
            self.owner_id=payload['user']['id']
        if record_login:
            def record():
                try:self._request('/rest/v1/rpc/record_victor_login',{'app_version':VERSION},authenticated=True)
                except (ValueError,TypeError):pass
            self.record_thread=threading.Thread(target=record,name='victor-cloud-access-record',daemon=True);self.record_thread.start()
    def _refresh(self):
        if not self.session:raise ValueError('La sesión caducó.')
        payload=self._request('/auth/v1/token?grant_type=refresh_token',{'refresh_token':self.session['refresh_token']})
        self._accept(payload,record_login=False)
        if self.session_file.exists():self.save_session()
    def save_session(self,remember_days=14):
        if not self.authenticated:raise ValueError('Inicia sesión primero.')
        self.data_dir.mkdir(parents=True,exist_ok=True)
        record={'refresh_token':self.session['refresh_token'],'project':self.settings['url'],'until':time.time()+min(remember_days,14)*86400}
        tmp=self.session_file.with_suffix('.tmp');tmp.write_bytes(CredentialStore.crypt(json.dumps(record).encode()));os.replace(tmp,self.session_file)
        return 'encrypted'
    def check_saved_session(self):
        if not self.session_file.exists():return False
        try:
            saved=json.loads(CredentialStore.crypt(self.session_file.read_bytes(),True))
            if saved['project']!=self.settings['url'] or saved['until']<time.time():return False
            self._accept(self._request('/auth/v1/token?grant_type=refresh_token',{'refresh_token':saved['refresh_token']}));self.save_session();return True
        except Exception:self.authenticated=False;self.session=None;return False
    def clear_saved_session(self):self.session_file.unlink(missing_ok=True)
    def lock_session(self):self.authenticated=False;self.session=None;self.clear_saved_session()
    def logout(self):
        try:self._request('/auth/v1/logout?scope=local',authenticated=True)
        finally:self.lock_session()
    def admin_profiles(self,offset=0):return self._request('/rest/v1/profiles?select=email,created_at,last_login_at,app_version&order=last_login_at.desc.nullslast&limit=200&offset='+str(max(0,int(offset))),method='GET',authenticated=True)
    def admin_events(self,offset=0):return self._request('/rest/v1/login_events?select=occurred_at,app_version,profiles(email)&order=occurred_at.desc&limit=200&offset='+str(max(0,int(offset))),method='GET',authenticated=True)
    def is_admin(self):return self._request('/rest/v1/rpc/is_victor_admin',{},authenticated=True) is True
    def change_password(self,current_password,new_password,new_hint=None):
        email=self.username();self.login(email,current_password)
        self._request('/auth/v1/user',{'password':new_password},method='PUT',authenticated=True);self.clear_saved_session();return True
