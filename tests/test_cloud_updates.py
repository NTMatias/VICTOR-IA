import base64
import hashlib
import json
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt,QPointF,QPoint
from victor.updates import verify_manifest,Updates
from victor.cloud_auth import CloudAuth
from victor.deployment import deployment
from victor.config import ConfigManager
from victor.gui.desktop_orb import DesktopVoiceOrb
from victor.version import VERSION

UID='11111111-2222-4333-8444-555555555555'
class Cloud(unittest.TestCase):
    def test_secret_key_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'deployment.json';path.write_text(json.dumps({'cloud':{'enabled':True,'url':'https://example.supabase.co','publishable_key':'sb_secret_DO_NOT_SHIP'}}))
            with self.assertRaises(ValueError):deployment(folder)
    def test_cloud_login_records_only_version_and_never_password_to_disk(self):
        with tempfile.TemporaryDirectory() as folder:
            auth=CloudAuth(Path(folder),{'url':'https://example.supabase.co','publishable_key':'sb_publishable_fixture'})
            payload={'access_token':'synthetic-access','refresh_token':'synthetic-refresh','expires_in':3600,'user':{'id':UID,'email':'fixture@example.com'}}
            with patch.object(auth,'_request',side_effect=[payload,{}]) as request:
                auth.login('fixture@example.com','fictitious-password')
                auth.record_thread.join(1)
                self.assertTrue(auth.authenticated);self.assertEqual(request.call_args.args[1],{'app_version':VERSION})
            self.assertEqual(list(Path(folder).iterdir()),[])
            auth.save_session();blob=auth.session_file.read_bytes();self.assertNotIn(b'synthetic-refresh',blob);self.assertNotIn(b'fictitious-password',blob)
            auth.lock_session();self.assertFalse(auth.authenticated);self.assertFalse(auth.session_file.exists())
    def test_registration_requires_email_confirmation(self):
        with tempfile.TemporaryDirectory() as folder:
            auth=CloudAuth(Path(folder),{})
            with patch.object(auth,'_request',return_value={'user':{'id':UID}}):
                with self.assertRaisesRegex(ValueError,'revisa tu correo'):auth.signup('fixture@example.com','fictitious-password')
            self.assertFalse(auth.authenticated)
    def test_missing_smtp_is_explained_without_exposing_server_response(self):
        with tempfile.TemporaryDirectory() as folder:
            auth=CloudAuth(Path(folder),{'url':'https://example.supabase.co','publishable_key':'sb_publishable_fixture'})
            response=SimpleNamespace(status_code=400,json=lambda:{'code':'email_address_not_authorized','msg':'private server details'})
            with patch.object(auth.http,'request',return_value=nullcontext(response)):
                with self.assertRaisesRegex(ValueError,'configurar SMTP') as raised:
                    auth.signup('fixture@example.com','fictitious-password')
            self.assertNotIn('private server details',str(raised.exception))
    def test_switching_account_cannot_expose_previous_profiles(self):
        with tempfile.TemporaryDirectory() as folder:
            auth=CloudAuth(Path(folder),{});auth.owner_id=UID
            with self.assertRaisesRegex(ValueError,'cambiar de cuenta'):
                auth._accept({'access_token':'fixture','refresh_token':'fixture','user':{'id':'aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee'}})
            self.assertFalse(auth.authenticated)
    def test_profile_does_not_inherit_owner_api_key_or_workspace(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict('os.environ',{'OPENAI_API_KEY':'fictitious-owner-key'}):
            root=Path(folder);config=ConfigManager(root,data_dir=root/'data/profiles'/UID)
            self.assertEqual(config.api_key('OpenAI'),'');self.assertEqual(config.get('allowed_folders'),[str(config.data_dir/'workspace')])

class Update(unittest.TestCase):
    def setUp(self):
        self.key=Ed25519PrivateKey.generate();self.public=self.key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex();self.asset=b'controlled-release-fixture'
        self.record={'version':'8.0.0','asset_url':'https://github.com/NTMatias/VICTOR-IA/releases/download/v8.0.0/VICTOR.zip','size':len(self.asset),'sha256':hashlib.sha256(self.asset).hexdigest()}
    def envelope(self,record=None):
        payload=json.dumps(record or self.record).encode();return {'payload':base64.b64encode(payload).decode(),'signature':base64.b64encode(self.key.sign(payload)).decode()}
    def response(self,data):
        response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False);response.iter_content.return_value=[data];return response
    def test_signature_and_version_and_download_destination(self):
        self.assertEqual(verify_manifest(self.envelope(),self.public),self.record)
        bad=self.envelope();bad['payload']=base64.b64encode(b'{}').decode()
        with self.assertRaises(Exception):verify_manifest(bad,self.public)
        for url in ('http://127.0.0.1/private.zip','https://github.com/other/project/x.zip',self.record['asset_url'].replace('/v8.0.0/','/v1.0.0/')):
            with self.assertRaises(ValueError):verify_manifest(self.envelope({**self.record,'asset_url':url}),self.public)
    def test_download_checks_hash_and_cleans_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            manager=Updates(folder,lambda *args:None)
            for valid in (True,False):
                manager.check=Mock(return_value=self.record)
                with patch.object(manager,'_open',return_value=self.response(self.asset if valid else b'bad')):
                    if valid:
                        path=manager.download(self.record);self.assertEqual(path.read_bytes(),self.asset)
                    else:
                        with self.assertRaises(ValueError):manager.download(self.record)
                        self.assertFalse(list((Path(folder)/'data/updates').glob('*.part')))
    def test_network_targets_reject_before_request(self):
        manager=Updates('.',lambda *args:None)
        with patch('requests.get') as get:
            with self.assertRaises(ValueError):manager._open('http://127.0.0.1/file')
            get.assert_not_called()
    def test_disabled_configuration_does_not_start_worker(self):
        with tempfile.TemporaryDirectory() as folder:
            manager=Updates(folder,lambda *args:None);manager.start();self.assertIsNone(manager.thread)

class Drag(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.qt=QApplication.instance() or QApplication([])
    def test_hold_move_release_and_restore(self):
        orb=DesktopVoiceOrb();orb.show();self.qt.processEvents();signals=[];orb.positionSaved.connect(lambda x,y:signals.append([x,y]))
        try:
            before=orb.pos();start=before+QPoint(50,50)
            event=lambda point:SimpleNamespace(button=lambda:Qt.MouseButton.LeftButton,buttons=lambda:Qt.MouseButton.LeftButton,globalPosition=lambda:QPointF(point),accept=lambda:None)
            orb.mousePressEvent(event(start));orb.mouseMoveEvent(event(start-QPoint(150,80)));orb.mouseReleaseEvent(event(start))
            self.assertNotEqual(before,orb.pos());self.assertEqual(signals[-1],[orb.x(),orb.y()]);saved=orb.pos();orb.hide();orb.show();self.assertEqual(orb.pos(),saved)
            self.assertTrue(orb.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus)
        finally:orb.close()

if __name__=='__main__':unittest.main()
