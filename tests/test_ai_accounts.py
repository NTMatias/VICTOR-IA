"""OAuth fixtures and API-only Gemini routing; no private accounts or charges."""
from copy import deepcopy
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock,patch
from urllib.parse import parse_qs,urlparse,urlencode
import jwt
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from victor.config import ConfigManager,DEFAULTS
from victor.ai.chatgpt_account import ChatGPTAccount,ChatGPTProvider,AccountError,ISSUER,RESOURCE,SCOPES,USE_SCOPE,responses_input
from victor.ai.manager import AIManager
from victor.errors import Cancelled,VictorError


class Accounts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.config=ConfigManager(self.root)
        self.account=ChatGPTAccount(self.config);self.cancel=threading.Event()
        self.key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        self.jwk=json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.key.public_key()));self.jwk['kid']='fixture'
        self.authorization={};self.denied=False;self.bad_nonce=False;self.bad_state=False
    def tearDown(self):self.temp.cleanup()
    def tokens(self,nonce='fixture',scope=SCOPES):
        now=int(time.time())
        identity={'iss':ISSUER,'aud':'oaiapp_fixture','sub':'person-fixture','iat':now,'exp':now+3600,
                  'nonce':nonce,'email':'fixture@example.invalid'}
        return {'id_token':jwt.encode(identity,self.key,algorithm='RS256',headers={'kid':'fixture'}),
                'access_token':'fixture-access','refresh_token':'fixture-refresh','token_type':'Bearer','scope':scope,'expires_in':3600}
    def api(self,method,url,**kwargs):
        if url.endswith('jwks.json'):return {'keys':[self.jwk]}
        if url.endswith('/token'):
            data=kwargs['data'];self.exchange=data
            if data['grant_type']=='refresh_token':return {'access_token':'renewed-fixture','refresh_token':'rotated-fixture','expires_in':3600}
            self.assertEqual(data['redirect_uri'],self.authorization['redirect_uri'][0]);self.assertEqual(data['resource'],RESOURCE)
            expected=base64.urlsafe_b64encode(hashlib.sha256(data['code_verifier'].encode()).digest()).rstrip(b'=').decode()
            self.assertEqual(expected,self.authorization['code_challenge'][0])
            return self.tokens('wrong' if self.bad_nonce else self.authorization['nonce'][0], 'openid profile email' if self.denied else SCOPES)
        if url.endswith('/models'):return {'models':[{'slug':'gpt-fixture','display_name':'Fixture','visibility':'list'},{'slug':'hidden','visibility':'hide'}]}
        if url.endswith('openid-configuration'):return {'revocation_endpoint':ISSUER+'/api/accounts/oauth/revoke'}
        if url.endswith('/revoke'):return {}
        raise AssertionError(url)
    def browser(self,url):
        self.authorization=parse_qs(urlparse(url).query)
        def callback():
            redirect=self.authorization['redirect_uri'][0];state=self.authorization['state'][0]
            invalid=requests.get(redirect+'?'+urlencode({'state':'invalid','code':'never'}),timeout=3)
            self.assertEqual(invalid.status_code,400)
            if self.bad_state:self.cancel.set();return
            requests.get(redirect+'?'+urlencode({'state':state,'code':'fixture-code','client_id':'oaiapp_fixture'}),timeout=3)
        self.browser_thread=threading.Thread(target=callback);self.browser_thread.start();return True
    def connect(self):
        with patch('victor.ai.chatgpt_account.webbrowser.open',side_effect=self.browser),patch('victor.ai.chatgpt_account.request_json',side_effect=self.api):
            try:return self.account.connect(self.cancel)
            finally:self.browser_thread.join(4)
    def test_loopback_pkce_signed_identity_scope_dpapi_and_catalog(self):
        models=self.connect();self.assertEqual([m['id'] for m in models],['gpt-fixture'])
        self.assertEqual(self.authorization['client_id'],['dynamic_agent_client'])
        self.assertEqual(set(self.authorization['scope'][0].split()),set(SCOPES.split()))
        self.assertEqual(self.exchange['client_id'],'oaiapp_fixture')
        self.assertNotIn(b'fixture-access',self.account.storage.path.read_bytes())
        other=ChatGPTAccount(self.config);self.assertEqual(other.host_id(),self.account.host_id())
        self.assertEqual(other.current()['subject'],'person-fixture');self.assertIn('pendiente',other.status())
        with patch('victor.ai.chatgpt_account.request_json',side_effect=self.api):
            self.assertEqual(other.list_models(self.cancel),models)
            self.assertIn('Conectado',other.status())
    def test_bad_nonce_or_state_never_replaces_active_credentials(self):
        self.connect();saved=self.account.storage.path.read_bytes();self.bad_nonce=True
        with self.assertRaises(AccountError):self.connect()
        # Pending registration may be persisted, but verified profile stays unchanged.
        self.assertEqual(self.account.current()['access_token'],'fixture-access')
        self.bad_nonce=False;self.bad_state=True
        with self.assertRaises(Cancelled):self.connect()
        self.assertEqual(self.account.current()['subject'],'person-fixture')
    def test_declined_plan_stores_identity_but_never_infers(self):
        self.denied=True
        with self.assertRaises(AccountError):self.connect()
        self.assertEqual(self.account.current()['subject'],'person-fixture')
        with self.assertRaisesRegex(AccountError,'permiso'):self.account.refresh_session(self.cancel)
    def test_refresh_rotation_and_scope_retention(self):
        self.connect()
        with self.account.storage.transaction():
            data=self.account.storage.read();data['profiles'][data['active']]['expires_at']=0;self.account.storage.write(data)
        with patch('victor.ai.chatgpt_account.request_json',side_effect=self.api) as api:
            self.assertEqual(self.account.refresh_session(self.cancel),'renewed-fixture')
            self.assertEqual(self.account.refresh_session(self.cancel),'renewed-fixture')
            self.assertEqual(api.call_count,1)
        self.assertEqual(self.account.current()['refresh_token'],'rotated-fixture')
        self.assertIn(USE_SCOPE,self.account.current()['scopes']);self.assertNotIn('scope',self.exchange)
    def test_disconnect_clears_tokens_preserves_registration_and_host(self):
        self.connect();host=self.account.host_id()
        with patch('victor.ai.chatgpt_account.request_json',side_effect=self.api):self.account.disconnect(self.cancel)
        self.assertEqual(self.account.current()['client_id'],'oaiapp_fixture');self.assertNotIn('access_token',self.account.current())
        self.assertEqual(self.account.host_id(),host);self.assertEqual(self.account.status(),'Desconectado')
    def test_signature_issuer_audience_and_expiry(self):
        for change in ({'iss':'https://other.invalid'},{'aud':'wrong'},{'exp':1}):
            identity={'iss':ISSUER,'aud':'oaiapp_fixture','sub':'fixture','iat':int(time.time()),'exp':int(time.time())+50,**change}
            token=jwt.encode(identity,self.key,algorithm='RS256',headers={'kid':'fixture'})
            with patch('victor.ai.chatgpt_account.request_json',return_value={'keys':[self.jwk]}),self.assertRaises(AccountError):
                self.account.verify_identity(token,'oaiapp_fixture')


class Responses(unittest.TestCase):
    def setUp(self):
        self.account=NS(refresh_session=Mock(return_value='synthetic'),catalog=[{'id':'gpt-test'}],state='unverified')
        self.provider=ChatGPTProvider(self.account);self.cfg=deepcopy(DEFAULTS);self.cfg['account_models']['OpenAI']='gpt-test'
    def stream(self,events,cancel=None):
        stream=Mock();stream.__enter__=Mock(return_value=iter(events));stream.__exit__=Mock(return_value=False)
        client=Mock();client.responses.create.return_value=stream;client.__enter__=Mock(return_value=client);client.__exit__=Mock(return_value=False)
        emitted=[]
        with patch('openai.OpenAI',return_value=client):
            reply=self.provider.stream([{'role':'user','content':'hola'}],'Soy VICTOR',[{'name':'hardware','description':'hardware','parameters':{'type':'object','properties':{}}}],self.cfg,emitted.append,cancel or threading.Event())
        return reply,client.responses.create.call_args.kwargs,emitted
    def test_stream_complete_and_supported_payload(self):
        call=NS(type='function_call',call_id='call1',name='hardware',arguments='{}')
        reply,body,emitted=self.stream([NS(type='response.output_text.delta',delta='Hola'),NS(type='response.output_item.done',item=call),NS(type='response.completed')])
        self.assertEqual(reply.text,'Hola');self.assertEqual(reply.calls[0].name,'hardware')
        self.assertFalse(body['store']);self.assertTrue(body['stream']);self.assertEqual(body['instructions'],'Soy VICTOR')
        for key in ('temperature','max_output_tokens','previous_response_id','conversation'):self.assertNotIn(key,body)
        self.assertEqual(body['input'][0]['type'],'additional_tools');self.assertEqual(body['input'][0]['role'],'developer')
    def test_gpt_six_keeps_model_and_uses_selected_reasoning(self):
        self.cfg['account_models']['OpenAI']='gpt-6.1-sol';self.cfg['ai_reasoning_effort']='low';self.account.catalog=[{'id':'gpt-6.1-sol'}]
        _,body,_=self.stream([NS(type='response.completed')])
        self.assertEqual(body['model'],'gpt-6.1-sol');self.assertEqual(body['reasoning'],{'effort':'low'});self.assertNotIn('service_tier',body)
    def test_partial_quota_error_and_cancel_are_not_success(self):
        for ending in ([],[NS(type='response.incomplete')],[NS(type='response.failed',response=NS(error=NS(code='subscription_sharing_usage_limit_exceeded')))]):
            with self.assertRaises(AccountError):self.stream([NS(type='response.output_text.delta',delta='partial')]+ending)
        cancel=threading.Event();cancel.set()
        with self.assertRaises(Cancelled):self.stream([],cancel)
    def test_tool_history_preserves_call_ids(self):
        history=responses_input([{'role':'assistant','content':'','tool_calls':[{'id':'call1','function':{'name':'test','arguments':'{}'}}]},
                                 {'role':'tool','tool_call_id':'call1','content':'{"ok":true}'}])
        self.assertEqual(history[0]['call_id'],history[1]['call_id']);self.assertEqual(history[1]['type'],'function_call_output')


class GeminiAPIOnly(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.config=ConfigManager(Path(self.temp.name))
    def tearDown(self):self.temp.cleanup()
    def test_migrate_legacy_login_without_resetting_settings(self):
        saved=self.config.snapshot();saved.update(provider='Gemini',theme='Light',voice_rate=210,gemini_account_enabled=True)
        saved['auth_methods']={'OpenAI':'account','Gemini':'account'}
        self.config.path.write_text(json.dumps(saved),encoding='utf-8')
        legacy=self.config.data_dir/'accounts'/'gemini'/'owner-profile';legacy.parent.mkdir(parents=True);legacy.write_text('preserve')
        migrated=ConfigManager(self.config.root)
        self.assertFalse(migrated.warning);self.assertEqual(migrated.get('auth_methods'),{'OpenAI':'account','Gemini':'api'})
        self.assertFalse(migrated.get('gemini_account_enabled'));self.assertEqual(migrated.get('voice_rate'),210)
        self.assertEqual(migrated.get('theme'),'Light');self.assertEqual(legacy.read_text(),'preserve')
        migrated.save({});self.assertEqual(json.loads(migrated.path.read_text())['auth_methods']['Gemini'],'api')
        for values in ({'auth_methods':{'OpenAI':'api','Gemini':'account'}},{'gemini_account_enabled':True}):
            with self.assertRaises(VictorError):migrated.save(values)
    def test_gemini_api_key_used_for_chat_and_vision(self):
        self.config.save({'provider':'Gemini','vision_provider':'Gemini'})
        manager=AIManager(self.config,lambda *args:None)
        self.assertEqual(set(manager.accounts),{'OpenAI'});self.assertEqual(set(manager.account_providers),{'OpenAI'})
        with patch.object(self.config,'api_key',return_value='synthetic-key'),patch.object(manager.providers['Gemini'],'stream',return_value=NS(text='ok',calls=[])) as api:
            for vision in (False,True):
                self.assertEqual(manager.generate([],'',[],threading.Event(),vision=vision).text,'ok')
                self.assertEqual(api.call_args.args[3]['_api_key'],'synthetic-key')
    def test_missing_key_does_not_launch_cli(self):
        self.config.save({'provider':'Gemini'})
        manager=AIManager(self.config,lambda *args:None)
        with patch.object(self.config,'api_key',return_value=''),patch('subprocess.Popen') as process,patch.object(manager.providers['Gemini'],'stream') as api:
            with self.assertRaisesRegex(VictorError,'GEMINI_API_KEY'):manager.generate([],'',[],threading.Event())
            process.assert_not_called();api.assert_not_called()
    def test_chatgpt_account_retains_no_paid_fallback(self):
        self.config.save({'provider':'OpenAI','fallback':['Gemini'],'auth_methods':{'OpenAI':'account','Gemini':'api'}})
        manager=AIManager(self.config,lambda *args:None)
        with patch.object(manager.account_providers['OpenAI'],'stream',side_effect=AccountError('cuota','limit')),patch.object(manager.providers['Gemini'],'stream') as api:
            with self.assertRaises(VictorError):manager.generate([],'',[],threading.Event())
            api.assert_not_called()

if __name__=='__main__':unittest.main()
