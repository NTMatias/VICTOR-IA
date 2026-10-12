"""Official SIWC public-client OAuth and Responses transport. No browser cookies."""
import base64
import hashlib
import json
import secrets
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse
import requests
from victor.ai.account_storage import AccountStorage
from victor.ai.base import BaseProvider, Reply, ToolCall, parse_args
from victor.errors import VictorError, Cancelled, check_cancel

ISSUER='https://auth.openai.com'
RESOURCE='https://api.openai.com/v1'
SCOPES='openid profile email offline_access resource.invoke chatgpt.tokens.use.direct'
USE_SCOPE='chatgpt.tokens.use.direct'


class AccountError(VictorError):
    def __init__(self,message,state='error'):
        super().__init__(message);self.state=state


def safe_error(code='',status=None):
    if code in ('subscription_sharing_usage_limit_exceeded','rate_limit_exceeded') or status==429:
        return AccountError('Límite de la cuenta alcanzado. Revisa Gestionar uso; no se usará una API de pago.','limit')
    if code in ('invalid_grant','invalid_token','token_expired') or status==401:
        return AccountError('La sesión caducó o fue revocada. Vuelve a conectar la cuenta.','expired')
    if code=='access_denied':return AccountError('No autorizaste la conexión o el permiso para usar tu plan.','denied')
    if code=='subscription_sharing_usage_unavailable' or status==403:
        return AccountError('Tu cuenta o esta aplicación no es elegible para usar el plan en esta solicitud. La API sigue disponible como opción independiente.','ineligible')
    if status==404:return AccountError('El modelo no está disponible para esta cuenta. Actualiza los modelos.')
    return AccountError('No se pudo completar la conexión de cuenta. Revisa Internet e inténtalo de nuevo.')


def request_json(method,url,**kwargs):
    try:
        with requests.request(method,url,timeout=(5,15),**kwargs) as response:
            try:payload=response.json()
            except ValueError:payload={}
            if not response.ok:
                error=payload.get('error',{})
                code=error.get('code','') if isinstance(error,dict) else str(error)
                raise safe_error(code,response.status_code)
            return payload
    except requests.RequestException:
        raise AccountError('No se pudo conectar con OpenAI. Revisa Internet; la sesión guardada se conserva.') from None


class ChatGPTAccount:
    def __init__(self,config):
        self.config=config;self.storage=AccountStorage(config.data_dir/'accounts')
        self.state='unverified';self.catalog=[];self.state_lock=threading.Lock()

    def host_id(self):
        path=self.storage.directory/'host.json'
        with self.storage.transaction():
            if path.exists():return json.loads(path.read_text(encoding='utf-8'))['ext_agent_host_id']
            host='urn:uuid:'+str(uuid.uuid4())
            temp=path.with_suffix('.tmp');temp.write_text(json.dumps({'ext_agent_host_id':host}),encoding='utf-8');temp.replace(path)
            return host

    def profiles(self):
        data=self.storage.read()
        return [{'id':key,'label':p.get('email') or p.get('subject','Cuenta'),'active':key==data.get('active')}
                for key,p in data['profiles'].items()]

    def select(self,key):
        with self.storage.transaction():
            data=self.storage.read()
            if key not in data['profiles']:raise AccountError('Cuenta no encontrada.')
            data['active']=key;self.storage.write(data)
        self.state='unverified';self.catalog=[]

    def current(self):
        data=self.storage.read();return dict(data['profiles'].get(data.get('active'),{}))

    def status(self):
        profile=self.current()
        if not profile.get('access_token'):return 'Desconectado'
        labels={'connected':'Conectado · permiso de plan verificado','unverified':'Sesión guardada · pendiente de verificar',
                'expired':'Autenticación caducada','limit':'Límite alcanzado','denied':'Uso del plan no autorizado',
                'ineligible':'Cuenta o aplicación no elegible','error':'Error de conexión'}
        return (profile.get('email') or 'Cuenta ChatGPT')+'\n'+labels.get(self.state,'Pendiente de verificar')

    @staticmethod
    def verify_identity(token,client_id,nonce=None):
        import jwt
        try:
            header=jwt.get_unverified_header(token)
            if header.get('alg')!='RS256':raise ValueError()
            jwks=request_json('GET',ISSUER+'/.well-known/jwks.json')
            jwk=next(k for k in jwks['keys'] if k.get('kid')==header.get('kid'))
            key=jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
            identity=jwt.decode(token,key,algorithms=['RS256'],issuer=ISSUER,audience=client_id,
                                options={'require':['exp','iat','iss','aud','sub']},leeway=30)
            if nonce is not None and not secrets.compare_digest(str(identity.get('nonce','')),nonce):raise ValueError()
            return identity
        except AccountError:raise
        except Exception:
            raise AccountError('No pude validar la identidad de ChatGPT. La sesión anterior no se ha reemplazado.') from None

    def connect(self,cancel,new_account=False):
        host=self.host_id();prior={} if new_account else self.current()
        client=prior.get('client_id') or 'dynamic_agent_client'
        if not new_account and client=='dynamic_agent_client':
            pending=self.storage.read().get('pending_clients',{})
            if len(pending)==1:client=next(iter(pending))
        state=secrets.token_urlsafe(32);nonce=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(64)
        challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
        result={}
        class Callback(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                parsed=urlparse(self.path)
                if parsed.path!='/auth/callback':self.send_error(404);return
                query=parse_qs(parsed.query)
                if any(len(v)!=1 for v in query.values()) or not secrets.compare_digest(query.get('state',[''])[0],state):
                    self.send_error(400);return
                result.update({k:v[0] for k,v in query.items()})
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers()
                self.wfile.write('<p>Vuelve a VICTOR.IA para ver el resultado de la conexión.</p>'.encode())
        with HTTPServer(('127.0.0.1',0),Callback) as server:
            server.timeout=.2;redirect=f'http://127.0.0.1:{server.server_port}/auth/callback'
            params={'client_id':client,'ext_agent_host_id':host,'response_type':'code','redirect_uri':redirect,
                    'scope':SCOPES,'resource':RESOURCE,'state':state,'nonce':nonce,
                    'code_challenge_method':'S256','code_challenge':challenge}
            if client=='dynamic_agent_client':params['agent_name_hint']='VICTOR.IA'
            elif prior.get('id_token'):
                params['id_token_hint']=prior['id_token']
                if prior.get('email'):params['login_hint']=prior['email']
                if USE_SCOPE not in prior.get('scopes',[]):params['prompt']='consent'
            if not webbrowser.open(ISSUER+'/api/accounts/authorize?'+urlencode(params)):
                raise AccountError('No pude abrir el navegador predeterminado para conectar ChatGPT.')
            deadline=time.monotonic()+180
            while not result:
                check_cancel(cancel)
                if time.monotonic()>deadline:raise AccountError('Se agotó el tiempo para iniciar sesión. Pulsa Continuar con ChatGPT de nuevo.')
                server.handle_request()
        check_cancel(cancel)
        if result.get('error'):raise safe_error(result['error'])
        issued=result.get('client_id') or (client if client!='dynamic_agent_client' else '')
        if not issued or issued=='dynamic_agent_client' or not result.get('code'):
            raise AccountError('El registro oficial no devolvió un cliente válido. La integración puede no ser elegible.')
        if client!='dynamic_agent_client' and issued!=client:raise AccountError('El registro recibido no coincide con la cuenta seleccionada.')
        # Retain registration independently of the short-lived code, without replacing the active profile.
        with self.storage.transaction(cancel):
            data=self.storage.read();data.setdefault('pending_clients',{})[issued]={'ext_agent_host_id':host};self.storage.write(data)
        tokens=request_json('POST',ISSUER+'/api/accounts/oauth/token',data={
            'grant_type':'authorization_code','client_id':issued,'code':result['code'],'code_verifier':verifier,
            'redirect_uri':redirect,'resource':RESOURCE})
        identity=self.verify_identity(tokens.get('id_token',''),issued,nonce)
        if prior.get('subject') and identity['sub']!=prior['subject']:raise AccountError('La identidad no coincide con la cuenta seleccionada. Usa Añadir otra cuenta.')
        check_cancel(cancel)
        if not tokens.get('access_token') or tokens.get('token_type','').lower()!='bearer':raise AccountError('La autorización no devolvió un token de acceso válido.')
        profile={'client_id':issued,'subject':identity['sub'],'issuer':identity['iss'],'email':identity.get('email',''),
                 'ext_agent_host_id':host,**tokens,'scopes':str(tokens.get('scope','')).split(),
                 'expires_at':time.time()+float(tokens.get('expires_in',3600))}
        key=hashlib.sha256((issued+'|'+identity['sub']).encode()).hexdigest()
        with self.storage.transaction(cancel):
            data=self.storage.read();data['profiles'][key]=profile;data['active']=key;data.get('pending_clients',{}).pop(issued,None);self.storage.write(data)
        self.state='unverified';self.catalog=[]
        if USE_SCOPE not in profile['scopes']:
            self.state='denied';raise AccountError('Cuenta conectada, pero no autorizaste el uso del plan. Pulsa Continuar con ChatGPT para concederlo.','denied')
        return self.list_models(cancel)

    def refresh_session(self,cancel):
        with self.storage.transaction(cancel):
            data=self.storage.read();key=data.get('active');profile=dict(data['profiles'].get(key,{}))
            if not profile.get('access_token'):raise AccountError('Conecta tu cuenta en Ajustes → IA → Continuar con ChatGPT.','expired')
            if time.time()+90>=profile.get('expires_at',0):
                if not profile.get('refresh_token'):raise AccountError('La sesión caducó. Vuelve a conectar ChatGPT.','expired')
                try:
                    tokens=request_json('POST',ISSUER+'/api/accounts/oauth/token',data={
                        'grant_type':'refresh_token','client_id':profile['client_id'],
                        'refresh_token':profile['refresh_token'],'resource':RESOURCE})
                    if not tokens.get('access_token'):raise AccountError('La renovación no devolvió un token válido.','expired')
                    if tokens.get('id_token'):
                        identity=self.verify_identity(tokens['id_token'],profile['client_id'])
                        if identity['sub']!=profile['subject']:raise AccountError('La identidad cambió durante la renovación.','expired')
                    updated={**profile,**tokens,'expires_at':time.time()+float(tokens.get('expires_in',3600))}
                    if 'scope' in tokens:updated['scopes']=tokens['scope'].split()
                    data['profiles'][key]=updated;self.storage.write(data);profile=updated
                except AccountError as exc:self.state=exc.state;raise
            if USE_SCOPE not in profile.get('scopes',[]):
                self.state='denied';raise AccountError('No autorizaste el permiso para usar tu plan ChatGPT.','denied')
            check_cancel(cancel);return profile['access_token']

    def list_models(self,cancel):
        token=self.refresh_session(cancel)
        try:
            payload=request_json('GET',RESOURCE+'/models',headers={'Authorization':'Bearer '+token})
            check_cancel(cancel)
            models=[{'id':m['slug'],'label':m.get('display_name') or m['slug']} for m in payload.get('models',[])
                    if m.get('visibility')=='list' and isinstance(m.get('slug'),str)]
            if not models:raise AccountError('La cuenta no devolvió modelos elegibles para mostrar.')
            self.catalog=models;self.state='connected';return models
        except AccountError as exc:self.state=exc.state;raise

    def disconnect(self,cancel):
        remote=True
        with self.storage.transaction(cancel):
            data=self.storage.read();key=data.get('active');profile=data['profiles'].get(key,{})
            if profile.get('refresh_token'):
                try:
                    metadata=request_json('GET',ISSUER+'/.well-known/openid-configuration')
                    endpoint=metadata.get('revocation_endpoint','')
                    if urlparse(endpoint).scheme!='https' or urlparse(endpoint).hostname!='auth.openai.com':raise AccountError('Endpoint de revocación inválido.')
                    request_json('POST',endpoint,data={'token':profile['refresh_token'],'token_type_hint':'refresh_token','client_id':profile['client_id']})
                except AccountError:remote=False
            for name in ('access_token','refresh_token','id_token','expires_at','scope','scopes'):profile.pop(name,None)
            self.storage.write(data)
        self.state='unverified';self.catalog=[]
        return 'Sesión cerrada.' if remote else 'Sesión cerrada localmente. No se confirmó la revocación remota; desconecta VICTOR en los ajustes de ChatGPT.'


def responses_input(messages):
    result=[]
    for message in messages:
        if message['role']=='tool':
            result.append({'type':'function_call_output','call_id':message['tool_call_id'],'output':message.get('content','')})
        else:
            if message.get('content'):
                result.append({'role':'developer' if message['role']=='system' else message['role'],'content':message['content']})
            for call in message.get('tool_calls',[]):
                result.append({'type':'function_call','call_id':call['id'],'name':call['function']['name'],
                               'arguments':call['function']['arguments']})
    return result


class ChatGPTProvider(BaseProvider):
    name='OpenAI'
    def __init__(self,account):self.account=account
    def stream(self,messages,system,specs,cfg,emit,cancel,image=None):
        from openai import OpenAI
        check_cancel(cancel)
        token=self.account.refresh_session(cancel)
        model=cfg['account_models']['OpenAI']
        catalog=self.account.catalog or self.account.list_models(cancel)
        if not model:model=catalog[0]['id']
        if model not in [m['id'] for m in catalog]:raise AccountError('Selecciona un modelo disponible de la cuenta ChatGPT en Ajustes → IA.')
        history=responses_input(messages)
        if image:history.append({'role':'user','content':[{'type':'input_text','text':'Analiza la captura según la pregunta.'},
                                                         {'type':'input_image','image_url':'data:image/png;base64,'+image}]})
        options={'model':model,'instructions':system,'input':history,'store':False,'stream':True}
        if specs:options['input'].insert(0,{'type':'additional_tools','role':'developer','tools':[{'type':'function',**s,'strict':False} for s in specs]})
        reply=Reply();complete=False;pending={}
        # close the transport on cancellation, including while waiting for another event.
        with OpenAI(api_key=token,base_url=RESOURCE,timeout=cfg['network_timeout'],max_retries=0) as client:
            done=threading.Event()
            def watch():
                while not done.wait(.05):
                    if cancel.is_set():client.close();return
            watcher=threading.Thread(target=watch,daemon=True);watcher.start()
            try:
                with client.responses.create(**options) as stream:
                    for event in stream:
                        check_cancel(cancel)
                        if event.type=='response.output_text.delta':reply.text+=event.delta;emit(event.delta)
                        elif event.type=='response.output_item.done' and event.item.type=='function_call':
                            pending[event.item.call_id]=ToolCall(event.item.name,parse_args(event.item.arguments),event.item.call_id)
                        elif event.type=='response.failed':raise safe_error(getattr(event.response.error,'code',''))
                        elif event.type in ('response.incomplete','error'):raise AccountError('La respuesta quedó incompleta. Vuelve a intentarlo.')
                        elif event.type=='response.completed':complete=True
                check_cancel(cancel)
                if not complete:raise AccountError('La transmisión terminó antes de completar la respuesta.')
                reply.calls=list(pending.values());self.account.state='connected';return reply
            except Exception as exc:
                check_cancel(cancel)
                error=exc if isinstance(exc,AccountError) else safe_error(getattr(exc,'code',''),getattr(exc,'status_code',None))
                self.account.state=error.state;raise error from None
            finally:done.set();watcher.join(.3)
