"""Exercise the public invitation page offline, with fictitious tokens and no mail."""
import shutil
import subprocess
import unittest
from pathlib import Path


@unittest.skipUnless(shutil.which('node'), 'Node is required for browser-script fixtures')
class AccountConfirmationTests(unittest.TestCase):
    def test_invitation_password_and_expired_links(self):
        script = r"""
const vm = require('node:vm'), fs = require('node:fs'), assert = require('node:assert/strict');
const source = fs.readFileSync(process.argv[1], 'utf8');
function fixture(link, handler) {
 const nodes = {}, events = {}, calls = [];
 for (const id of ['password-form','password','confirm','save','title','message'])
  nodes[id] = {hidden:true, value:'', disabled:false, textContent:'', addEventListener:(kind,fn)=>events[id+':'+kind]=fn};
 const location = {hash:'#'+link, pathname:'/VICTOR-IA/'};
 const context = vm.createContext({URLSearchParams, AbortController, setTimeout, clearTimeout, pendingLink:new URLSearchParams(link), location,
  history:{replaceState:()=>location.hash=''}, document:{getElementById:id=>nodes[id]},
  addEventListener:(kind,fn)=>events[kind]=fn,
  fetch:async(url,options)=>{calls.push({url,options}); return handler(url,options);}});
 vm.runInContext(source,context);
 return {nodes,events,calls,location,context};
}
const tick = ()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 let f=fixture('access_token=fictitious-token&type=invite',()=>({ok:true})); await tick();
 assert.equal(f.calls.length,1); assert.equal(f.nodes['password-form'].hidden,false);
 f.nodes.password.value='fictional-test-password'; f.nodes.confirm.value='does-not-match';
 await f.events['password-form:submit']({preventDefault(){}}); assert.equal(f.calls.length,1);
 f.nodes.confirm.value=f.nodes.password.value;
 await f.events['password-form:submit']({preventDefault(){}});
 assert.equal(f.calls[1].options.method,'PUT'); assert.equal(f.calls[2].url.endsWith('/logout?scope=local'),true);
 for (const call of f.calls) {
  assert.equal(call.url.startsWith('https://igqveyxbwhnadyubtsnj.supabase.co/auth/v1/'),true);
  assert.equal(call.url.includes('fictitious-token'),false); assert.equal(call.options.credentials,'omit');
  assert.equal(call.options.cache,'no-store'); assert.equal(call.options.redirect,'error');
 }
 assert.equal(f.nodes.password.value,''); assert.equal(f.nodes.confirm.value,'');
 assert.equal(f.nodes['password-form'].hidden,true);
 f=fixture('access_token=expired&type=invite',()=>({ok:false})); await tick();
 assert.equal(f.nodes['password-form'].hidden,true);
 f=fixture('error=expired',()=>{throw Error('must not fetch')}); await tick(); assert.equal(f.calls.length,0);
 f=fixture('access_token=fictitious&type=signup',()=>({ok:true})); await tick();
 assert.equal(f.nodes['password-form'].hidden,true); assert.equal(f.nodes.title.textContent,'Correo confirmado');
 f=fixture('access_token=fictitious&type=recovery',()=>({ok:true})); await tick();
 assert.equal(f.nodes['password-form'].hidden,false); f.events.pagehide();
 assert.equal(f.nodes['password-form'].hidden,true);
 let release;
 f=fixture('access_token=slow&type=invite',()=>new Promise(resolve=>release=resolve));
 f.location.hash='#error=expired'; f.events.hashchange(); release({ok:true}); await tick();
 assert.equal(f.nodes['password-form'].hidden,true); assert.equal(f.location.hash,'');
 console.log('Offline invitation checks passed');
})().catch(error=>{console.error(error.message); process.exitCode=1});
"""
        result = subprocess.run(
            [shutil.which('node'), '-e', script, str(Path(__file__).resolve().parents[1] / 'cloud/account.js')],
            capture_output=True, text=True, timeout=25,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
