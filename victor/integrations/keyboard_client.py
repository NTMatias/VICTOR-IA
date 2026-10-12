"""JavaScript compartido por la página y las pruebas Node (sin DOM para el codec)."""
KEYBOARD_JS = r'''
const VictorKeys = (() => {
  const aliases={Control:'ctrl',Alt:'alt',Shift:'shift',Meta:'win',Enter:'enter',Escape:'esc',Backspace:'backspace',Delete:'delete',Tab:'tab',ArrowLeft:'left',ArrowRight:'right',ArrowUp:'up',ArrowDown:'down',Home:'home',End:'end',PageUp:'pageup',PageDown:'pagedown',F4:'f4',' ':'space'};
  function keyEvent(key,mods=[]) {
    const normalized=aliases[key]||key.toLowerCase();
    const keys=[...new Set(mods.filter(m=>['ctrl','alt','shift','win'].includes(m)))];
    if (!keys.includes(normalized)) keys.push(normalized);
    return {kind:'keys',keys};
  }
  function textEvents(text) {
    const out=[];let buffer='';
    function flush(){if(buffer){out.push({kind:'text',text:buffer});buffer='';}}
    for(const char of text.replace(/\r\n?/g,'\n')) {
      if(char==='\n'||char==='\t'){flush();out.push(keyEvent(char==='\n'?'enter':'tab'));}
      else {if(char.codePointAt(0)<32 || (char.codePointAt(0)>=127&&char.codePointAt(0)<160))throw Error('Texto con controles no permitido.');buffer+=char;if([...buffer].length===128)flush();}
    }
    flush();return out;
  }
  function editEvents(before,after) {
    const a=Array.from(before),b=Array.from(after);let prefix=0;
    while(prefix<a.length && prefix<b.length && a[prefix]===b[prefix])prefix++;
    return Array.from({length:a.length-prefix},()=>keyEvent('backspace')).concat(textEvents(b.slice(prefix).join('')));
  }
  function packet(event,seq,windowTitle) {
    if(!Number.isInteger(seq)||seq<1||!windowTitle)throw Error('Indica la ventana destino.');
    return {type:'key_event',seq,window:windowTitle,...event};
  }
  class Channel {
    constructor(socket,getWindow,notice,onFocus) {
      this.socket=socket;this.getWindow=getWindow;this.notice=notice;this.onFocus=onFocus;
      this.queue=[];this.seq=0;this.active=null;this.closed=false;this.lastSeen=Date.now();this.deadline=0;
      socket.onmessage=e=>{try{this.receive(JSON.parse(e.data));}catch(_){this.fail('Respuesta de teclado inválida. Reconecta con un nuevo QR.');}};
      socket.onclose=()=>this.fail('Teclado desconectado. Revisa Wi-Fi/HTTPS y genera un nuevo QR.');
      socket.onerror=()=>this.fail('Error de teclado. Revisa la conexión y el certificado HTTPS.');
      this.timer=setInterval(()=>{
        if(this.closed)return;
        if(Date.now()-this.lastSeen>15000 || (this.active&&Date.now()>this.deadline)){this.fail('El teclado dejó de responder. La entrada pendiente NO se repetirá. Reconecta con un nuevo QR.');return;}
        if(socket.readyState===1)socket.send(JSON.stringify({type:'ping'}));
      },5000);
    }
    push(events) {
      if(this.closed)throw Error('Teclado desconectado. Vuelve a emparejar.');
      if(this.queue.length+events.length>128){this.fail('Cola llena. Detén la escritura y reconecta.');throw Error('No se enviará la cola pendiente.');}
      const title=this.getWindow();
      if(!title)throw Error('Indica el título exacto de la ventana destino.');
      for(const event of events)this.queue.push({event,title});
      this.pump();
    }
    pump() {
      if(this.closed||this.active||!this.queue.length)return;
      if(this.socket.readyState!==1){this.fail('Teclado sin conexión. Reconecta con un nuevo QR.');return;}
      const {event,title}=this.queue.shift();this.active=packet(event,++this.seq,title);this.deadline=Date.now()+10000;
      this.socket.send(JSON.stringify(this.active));
    }
    receive(msg) {
      this.lastSeen=Date.now();
      if(msg.type==='focus'){this.onFocus(msg);return;}
      if(msg.type==='pong')return;
      if(msg.type==='focus_unavailable'){this.notice(msg.message);return;}
      if(msg.type==='approval_pending'){this.deadline=Date.now()+130000;this.notice(msg.message);return;}
      if(msg.type==='disconnected'){this.fail(msg.message);return;}
      if(msg.type==='key_ack'){
        if(!this.active||msg.seq!==this.active.seq){this.fail('ACK fuera de orden. No se repetirá ninguna tecla. Reconecta.');return;}
        if(!msg.ok){this.fail(msg.error||'Entrada rechazada. Reconecta el teclado.');return;}
        this.active=null;this.notice('Teclado conectado · entrada enviada');this.pump();
      }
    }
    fail(message){if(this.closed)return;this.closed=true;this.queue=[];this.active=null;clearInterval(this.timer);this.socket.close();this.notice(message);}
  }
  return {keyEvent,textEvents,editEvents,packet,Channel};
})();
if(typeof module!=='undefined')module.exports=VictorKeys;
'''
