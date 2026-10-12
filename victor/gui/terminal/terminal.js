'use strict';
const term=new Terminal({fontFamily:'"Cascadia Mono",Consolas,monospace',fontSize:14,lineHeight:1.25,
  cursorBlink:true,scrollback:8000,allowProposedApi:false,convertEol:false,
  theme:{background:'#1D2027',foreground:'#E9EAF1',cursor:'#83AFFF',selectionBackground:'#455876'}});
const fit=new FitAddon.FitAddon();term.loadAddon(fit);term.open(document.getElementById('terminal'));
let bridge;
function resize(){try{fit.fit();if(bridge)bridge.resize(term.cols,term.rows);}catch(e){}}
new QWebChannel(qt.webChannelTransport,channel=>{bridge=channel.objects.terminalBridge;term.onData(data=>bridge.input(data));resize();bridge.ready();});
new ResizeObserver(resize).observe(document.getElementById('terminal'));
window.victorTerminal={write:data=>term.write(data),reset:()=>term.reset(),focus:()=>term.focus(),selection:()=>term.getSelection(),
 theme:light=>{term.options.theme=light?{background:'#FFFFFF',foreground:'#20242F',cursor:'#3569B2',selectionBackground:'#D6E0EF'}:{background:'#1D2027',foreground:'#E9EAF1',cursor:'#83AFFF',selectionBackground:'#455876'};document.body.style.background=light?'#FFFFFF':'#1D2027';},
 text:()=>Array.from({length:term.buffer.active.length},(_,i)=>term.buffer.active.getLine(i)?.translateToString(true)||'').join('\n')};
// Preserve the official CLI's native image-paste shortcut; text paste stays bracketed.
document.addEventListener('paste',event=>{
 if(bridge && Array.from(event.clipboardData?.items||[]).some(item=>item.type.startsWith('image/'))){
  event.preventDefault();event.stopImmediatePropagation();bridge.input('\x16');
 }
},true);
