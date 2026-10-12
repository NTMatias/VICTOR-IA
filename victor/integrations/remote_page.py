"""Cliente local sin CDN; credenciales solo en memoria y fragmento del QR."""
PAGE = r'''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VICTOR · Remoto local</title><style>
body{background:#0d111c;color:#edf2ff;font:16px system-ui;margin:20px;max-width:700px}button,input,textarea{box-sizing:border-box;font:inherit;padding:12px;border-radius:12px;border:1px solid #39465f;background:#222b3b;color:inherit;margin:4px}input,textarea{width:100%}button{touch-action:manipulation}#pad{height:220px;background:#171e2e;border:1px solid #397bfa;border-radius:18px;touch-action:none;display:grid;place-items:center;margin:12px 0}img{max-width:100%;border-radius:12px}small{color:#9ba9c3}</style>
<h1>VICTOR · Remoto local</h1><p id="status">Conectando…</p><small>Cada lote requiere confirmación en el PC. No se envía entrada mientras el PC esté ocupado.</small>
<input id="window" placeholder="Título exacto de la ventana del PC"><div id="pad">Desliza para mover el puntero</div>
<button id="left">Clic</button><button id="right">Clic derecho</button><button id="double">Doble clic</button><button id="up">Scroll ↑</button><button id="down">Scroll ↓</button>
<textarea id="text" placeholder="Texto a escribir (confirmación EJECUTAR en el PC)"></textarea><button id="write">Enviar texto</button>
<p><label><input type="checkbox" id="ctrl" style="width:auto">Ctrl</label><label><input type="checkbox" id="alt" style="width:auto">Alt</label><label><input type="checkbox" id="shift" style="width:auto">Shift</label></p>
<button data-key="enter">Enter</button><button data-key="esc">Escape</button><button data-key="backspace">Backspace</button><button data-key="tab">Tab</button>
<button id="screen">Ver pantalla · 60 s</button><button id="stop">Detener sesión</button><p><img id="view" alt="La pantalla aparece después de autorizar en el PC"></p>
<script>
const status=document.getElementById('status'), target=document.getElementById('window');let ws,video,session='',pending=false,events=[],dx=0,dy=0,last=null,imageURL='';
const code=location.hash.slice(1);history.replaceState(null,'',location.pathname);
function connect(path,auth){return new Promise((resolve,reject)=>{const s=new WebSocket('wss://'+location.host+path);s.onopen=()=>s.send(JSON.stringify(auth));s.onerror=()=>reject(Error('No se pudo conectar. Revisa HTTPS y la conexión local.'));s.onmessage=e=>{const msg=JSON.parse(e.data);if(msg.error){s.close();reject(Error(msg.error));}else resolve([s,msg]);};});}
function send(tool,args){if(!ws||ws.readyState!==1||pending){status.textContent='PC ocupado: espera y vuelve a enviar.';return;}pending=true;ws.send(JSON.stringify({tool,args}));status.textContent='Revisa y confirma en el PC.';}
function flush(){if(dx||dy){events.push({kind:'move',dx:Math.max(-500,Math.min(500,Math.round(dx))),dy:Math.max(-500,Math.min(500,Math.round(dy)))});dx=dy=0;}if(events.length&&!pending){const batch=events.splice(0,20);send('remote_pointer_batch',{window:target.value,events:batch});}else events=[];}
const pad=document.getElementById('pad');pad.onpointerdown=e=>{last=[e.clientX,e.clientY];pad.setPointerCapture(e.pointerId)};pad.onpointermove=e=>{if(last){dx+=e.clientX-last[0];dy+=e.clientY-last[1];last=[e.clientX,e.clientY]}};pad.onpointerup=()=>{last=null;flush()};pad.onpointercancel=()=>{last=null;dx=dy=0};setInterval(()=>{if(last)flush()},500);
for(const [id,kind] of [['left','left'],['right','right'],['double','double'],['up','up'],['down','down']])document.getElementById(id).onclick=()=>{events.push({kind,dx:0,dy:0});flush()};
document.getElementById('write').onclick=()=>send('type_text',{window:target.value,text:document.getElementById('text').value});
document.querySelectorAll('[data-key]').forEach(b=>b.onclick=()=>{const keys=['ctrl','alt','shift'].filter(k=>document.getElementById(k).checked);keys.push(b.dataset.key);send('press_keys',{window:target.value,keys})});
document.getElementById('screen').onclick=()=>send('remote_screen_stream',{});
document.getElementById('stop').onclick=()=>{if(ws)ws.close();if(video)video.close();status.textContent='Sesión detenida';};
(async()=>{try{[ws,{session}]=await connect('/control',{code});status.textContent='Conectado. Indica la ventana destino.';ws.onmessage=e=>{const m=JSON.parse(e.data);status.textContent=m.message||m.error||'Listo';if(m.done)pending=false;};ws.onclose=()=>{pending=false;status.textContent='Sesión cerrada. Genera otro QR en el PC.'};[video]=await connect('/screen',{session});video.binaryType='blob';video.onmessage=e=>{if(e.data instanceof Blob){if(imageURL)URL.revokeObjectURL(imageURL);imageURL=URL.createObjectURL(e.data);document.getElementById('view').src=imageURL}else{status.textContent=JSON.parse(e.data).error||'Pantalla detenida'}};}catch(e){status.textContent=e.message;}})();
</script></html>'''
