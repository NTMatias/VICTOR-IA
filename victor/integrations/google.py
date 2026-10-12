"""OAuth de escritorio y REST Google con credenciales protegidas por Windows."""
import base64
from datetime import datetime, timezone
from email.message import EmailMessage
import json
import os
import threading
from victor.errors import VictorError, check_cancel
from victor.integrations.spotify import EncryptedCache
from victor.security import Risk
from victor.tools.registry import Tool

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/drive.metadata.readonly']


class GoogleManager:
    def __init__(self, config):
        self.config = config
        self.cache = EncryptedCache(config.data_dir / 'google.oauth')
        self.lock = threading.RLock()

    def authorize(self, cancel):
        check_cancel(cancel)
        client, secret = os.getenv('GOOGLE_CLIENT_ID'), os.getenv('GOOGLE_CLIENT_SECRET')
        if not client or not secret:
            raise VictorError('Faltan GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET en .env. Crea un cliente OAuth de escritorio en Google Cloud.')
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError:
            raise VictorError('Google desactivado: instala google-auth-oauthlib con instalar.bat.') from None
        flow = InstalledAppFlow.from_client_config({'installed': {'client_id': client, 'client_secret': secret,
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth', 'token_uri': 'https://oauth2.googleapis.com/token',
            'redirect_uris': ['http://127.0.0.1']}}, SCOPES, autogenerate_code_verifier=True)
        original_request = flow.oauth2session.request
        def bounded_request(*args, **kwargs):
            kwargs['timeout'] = 15
            return original_request(*args, **kwargs)
        flow.oauth2session.request = bounded_request
        # La espera tiene límite; el cierre del PC espera como máximo este timeout.
        with self.lock:
            creds = flow.run_local_server(host='127.0.0.1', bind_addr='127.0.0.1', port=0, timeout_seconds=90,
                                          authorization_prompt_message='', success_message='Puedes volver a VICTOR.IA.')
            check_cancel(cancel)
            self.cache.save_token_to_cache(json.loads(creds.to_json()))
        return {'conectado': True}

    def request(self, method, url, **kwargs):
        import requests
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            with self.lock:
                token = self.cache.get_cached_token()
                if not token:
                    raise VictorError('Conecta Google desde el panel Conectar del PC.')
                creds = Credentials.from_authorized_user_info(token, SCOPES)
                if not creds.valid:
                    class BoundedRequest(Request):
                        def __call__(self, *args, **kw):
                            kw['timeout'] = 15
                            return super().__call__(*args, **kw)
                    creds.refresh(BoundedRequest())
                    self.cache.save_token_to_cache(json.loads(creds.to_json()))
                access = creds.token
            with requests.request(method, url, headers={'Authorization': 'Bearer ' + access}, timeout=(8,20), **kwargs) as response:
                response.raise_for_status()
                return response.json()
        except VictorError:
            raise
        except Exception as exc:
            import logging
            logging.getLogger('victor.google').warning('request failed type=%s', type(exc).__name__)
            raise VictorError('Google no pudo completar la operación. Revisa conexión, permisos y APIs habilitadas; vuelve a conectar si caducó el acceso.') from None

    def unread(self):
        base = 'https://gmail.googleapis.com/gmail/v1/users/me/messages'
        result = self.request('GET',base,params={'q':'is:unread','maxResults':5})
        rows=[]
        for item in result.get('messages',[]):
            msg=self.request('GET',base+'/'+item['id'],params={'format':'metadata','metadataHeaders':['Subject','From','Date']})
            headers={h['name'].lower():h['value'] for h in msg.get('payload',{}).get('headers',[])}
            rows.append({'asunto':headers.get('subject','Sin asunto'),'remitente':headers.get('from',''), 'resumen':msg.get('snippet','')})
        return {'correos_no_leidos':rows, 'limite':5}

    def events(self):
        data=self.request('GET','https://www.googleapis.com/calendar/v3/calendars/primary/events',params={
            'timeMin':datetime.now(timezone.utc).isoformat(), 'singleEvents':'true','orderBy':'startTime','maxResults':10})
        return {'eventos':[{'titulo':e.get('summary','Sin título'),'inicio':e.get('start',{}).get('dateTime',e.get('start',{}).get('date'))} for e in data.get('items',[])]}

    def files(self, query):
        escaped=query.replace('\\','\\\\').replace("'","\\'")
        data=self.request('GET','https://www.googleapis.com/drive/v3/files',params={
            'q':f"trashed = false and name contains '{escaped}'",'pageSize':20,'fields':'files(id,name,webViewLink,mimeType)'})
        return {'archivos':data.get('files',[])}

    def send_email(self, to, subject, body):
        if any(c in to+subject for c in '\r\n') or '@' not in to:
            raise VictorError('Destinatario o asunto inválido.')
        message=EmailMessage()
        message['To'],message['Subject']=to,subject
        message.set_content(body)
        data=self.request('POST','https://gmail.googleapis.com/gmail/v1/users/me/messages/send',json={
            'raw':base64.urlsafe_b64encode(message.as_bytes()).decode('ascii')})
        return {'correo_enviado':True,'id':data['id'],'destinatario':to}


def register_google(core):
    manager=GoogleManager(core.config)
    def add(name, desc, fn, risk=Risk.LOW, **props):
        core.registry.register(Tool(name,desc,{'type':'object','properties':props,'required':list(props),'additionalProperties':False},risk,fn))
    add('google_unread','Lee hasta cinco correos no leídos de la cuenta conectada.',manager.unread)
    def events():
        result=manager.events()
        rows=result['eventos']
        core.emit('google_summary', 'Próximo evento: '+str(rows[0]['titulo'])+' · '+str(rows[0]['inicio']) if rows else '')
        return result
    add('google_events','Próximos diez eventos del calendario principal.',events)
    add('google_drive_search','Busca metadatos de archivos Drive por nombre.',manager.files,query={'type':'string','minLength':1,'maxLength':200})
    add('google_send_email','Enviar correo real: revisa destinatario, asunto y cuerpo completos.',manager.send_email,Risk.HIGH,
        to={'type':'string','maxLength':320},subject={'type':'string','maxLength':200},body={'type':'string','maxLength':12000})
    return manager
