// Observe previews only. WhatsApp itself handles conversations and sending.
(() => {
  if(window!==window.top || location.origin!=='https://web.whatsapp.com')return;
  const post=data=>window.chrome.webview.postMessage({kind:'whatsapp',...data});
  const clean=value=>String(value || '').normalize('NFC').replace(/\s+/g,' ').trim();
  function semanticText(node) {
    if(!node)return '';
    const clone=node.cloneNode(true);
    // SVG titles describe implementation glyphs, not message text.
    for(const glyph of clone.querySelectorAll('svg,[data-icon],[data-testid^="icon-"],script,style'))glyph.remove();
    for(const img of clone.querySelectorAll('img[alt]'))img.replaceWith(document.createTextNode(img.alt));
    for(const badge of clone.querySelectorAll('[data-testid="icon-unread-count"],[aria-label*="unread" i],[aria-label*="no leído" i],[aria-label*="no leídos" i]'))badge.remove();
    return clean(clone.textContent);
  }
  const refs=new Map(),keys=new WeakMap();let serial=0,last='',recent=[];
  function nameOf(row) {
    const span=row.querySelector('[data-testid="cell-frame-title"] [title],span[dir="auto"][title],span[title]');
    return clean(span?.getAttribute('title') || semanticText(span));
  }
  function rowsIn(root) {
    if(!root)return [];
    for(const selector of ['[role="row"]','[data-testid="cell-frame-container"]','[role="listitem"]']) {
      const rows=Array.from(root.querySelectorAll(selector)).filter(row=>nameOf(row));
      if(rows.length)return rows.filter(row=>!rows.some(other=>other!==row && other.contains(row)));
    }
    return [];
  }
  function extract(row) {
    const name=nameOf(row);let known=keys.get(row);
    if(!known || known.name!==name){known={id:'recent-'+(++serial),name};keys.set(row,known);}
    const id=known.id;
    refs.set(id,{row,name});
    if(refs.size>1000)for(const [old,value] of refs){if(!value.row.isConnected)refs.delete(old);if(refs.size<=500)break;}
    const unreadNode=row.querySelector('[data-testid="icon-unread-count"],[aria-label*="unread" i],[aria-label*="no leído" i],[aria-label*="no leídos" i]');
    const unread=Number((unreadNode?.textContent || unreadNode?.getAttribute('aria-label') || '').match(/\d+/)?.[0] || 0);
    const secondary=row.querySelector('[data-testid="cell-frame-secondary"]');
    const candidates=Array.from(row.querySelectorAll('span[title]')).map(node=>clean(node.getAttribute('title'))).filter(value=>value!==name && !/^\d+$/.test(value) && !/^\d{1,2}:\d{2}$/.test(value));
    const preview=semanticText(secondary) || candidates.pop() || '';
    const time=semanticText(row.querySelector('[data-testid="cell-frame-time"]')) ||
      (row.innerText || '').split('\n').map(clean).find(value=>/^\d{1,2}:\d{2}(?:\s*[ap]\.?m\.?)?$/i.test(value) || /^(?:ayer|hoy|yesterday|today)$/i.test(value)) || '';
    return {id,name,preview:preview.slice(0,500),time,unread};
  }
  function snapshot(force=false) {
    const side=document.querySelector('#pane-side, #side [role="grid"]');
    const qr=document.querySelector('[data-ref] canvas,[data-testid="qrcode"] canvas,canvas[aria-label*="QR" i]');
    const state=side?'connected':qr?'qr':'loading';
    document.documentElement.dataset.victorLogin=String(state==='qr');
    if(state==='qr')window.__victorWhatsAppLoginPalette?.();
    const search=document.querySelector('#side [contenteditable="true"][role="textbox"]');
    const filtered=!!clean(search?.innerText || search?.textContent);
    if(side && !filtered)recent=rowsIn(side).slice(0,20).map(extract);
    else if(state==='qr')recent=[];
    const payload={state,recent,chats:recent};const encoded=JSON.stringify(payload);
    if(force || encoded!==last){last=encoded;post({type:'snapshot',payload});}
  }
  window.chrome.webview.addEventListener('message',event=> {
    const request=event.data;if(request?.kind!=='victor_whatsapp' || request.action!=='open')return;
    const saved=refs.get(request.id);
    if(!saved || !saved.row.isConnected || nameOf(saved.row)!==saved.name) {
      post({type:'result',request:request.request,ok:false,error:'Elige la conversación en WhatsApp; la lista de recientes cambió.'});return;
    }
    // Host supplies trusted browser input instead of clicking a passive wrapper.
    const target=saved.row.querySelector('[data-testid="cell-frame-container"],span[dir="auto"][title],span[title]') || saved.row;
    target.scrollIntoView({block:'nearest'});const rect=target.getBoundingClientRect();
    post({type:'target',request:request.request,x:rect.left+Math.min(rect.width/2,100),y:rect.top+rect.height/2,name:saved.name});
  });
  function start(){let timer;new MutationObserver(()=>{clearTimeout(timer);timer=setTimeout(()=>snapshot(),250);}).observe(document.documentElement,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['title','aria-label','data-ref']});setInterval(()=>snapshot(),1500);snapshot(true);}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
