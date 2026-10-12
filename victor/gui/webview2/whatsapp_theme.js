// Palette only: retain WhatsApp's original controls, media and interaction.
(() => {
  if(window!==window.top || location.origin!=='https://web.whatsapp.com')return;
  const dark={bg:'#15171C',deep:'#111318',surface:'#1D2027',raised:'#22252E',input:'#16181E',border:'#30333E',text:'#E9EAF1',muted:'#9196A5',secondary:'#B8BCC8',outgoing:'#283243',selected:'#303745',accent:'#83AFFF',button:'#588AD8'};
  const light={bg:'#F6F7FA',deep:'#EEF0F5',surface:'#FFFFFF',raised:'#F2F4F8',input:'#F6F7FA',border:'#D2D8E3',text:'#20242F',muted:'#616B7D',secondary:'#475266',outgoing:'#DCE6F4',selected:'#D6E0EF',accent:'#588AD8',button:'#588AD8'};
  let theme='dark';
  const loginColors=new WeakMap();
  function toneLogin(p) {
    if(document.documentElement.dataset.victorLogin!=='true' || !document.body)return;
    const canvas=document.querySelector('[data-ref] canvas,[data-testid="qrcode"] canvas,canvas[aria-label*="QR" i]');
    for(const node of document.body.querySelectorAll('div,section,header,h1,h2,h3,p,span,a,button,ol,ul,li,label')) {
      if(canvas && node.closest('[data-ref], [data-testid="qrcode"]'))continue;
      const style=getComputedStyle(node),rect=node.getBoundingClientRect();let old=loginColors.get(node);
      if(!old) {
        old={};
        if(style.backgroundColor==='rgb(252, 245, 235)')old.bg='bg';
        else if(style.backgroundColor==='rgb(255, 255, 255)' && rect.width>340 && !(canvas && node.contains(canvas) && rect.height<340))old.bg='surface';
        else if(style.backgroundColor==='rgb(255, 255, 255)' && rect.width<64 && rect.height<64)old.bg='raised';
        const bg=style.backgroundColor.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if(bg && Number(bg[1])<80 && Number(bg[2])>120 && Number(bg[3])<190)old.bg='button';
        const fg=style.color.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if(fg && [1,2,3].every(i=>Number(fg[i])<90))old.fg='text';
        if(style.borderTopColor==='rgb(29, 31, 31)' || style.borderTopColor==='rgb(0, 0, 0)')old.border=true;
        loginColors.set(node,old);
      }
      if(old.bg)node.style.setProperty('background-color',p[old.bg],'important');
      if(old.fg)node.style.setProperty('color',p.text,'important');
      if(old.border)node.style.setProperty('border-color',p.border,'important');
      if(node.tagName==='A')node.style.setProperty('color',p.accent,'important');
      if(old.bg==='button') {
        node.style.setProperty('background-color',p.button,'important');node.style.setProperty('color','#FFFFFF','important');node.style.setProperty('border-color',p.button,'important');
      }
    }
  }
  function apply(value) {
    theme=value==='light'?'light':'dark';const p=theme==='light'?light:dark;
    document.documentElement.dataset.victorTheme=theme;
    const vars={
      'app-background':p.bg,'app-background-deeper':p.deep,'background-default':p.bg,'background-default-hover':p.raised,'background-default-active':p.selected,
      'panel-background':p.surface,'panel-background-lighter':p.raised,'panel-background-colored':p.surface,'panel-background-deep':p.deep,
      'drawer-background':p.surface,'drawer-section-background':p.surface,'dropdown-background':p.raised,'dropdown-background-hover':p.selected,
      'conversation-panel-background':p.bg,'conversation-panel-border':p.border,'compose-background':p.surface,'compose-input-background':p.input,
      'incoming-background':p.raised,'incoming-background-deeper':p.raised,'outgoing-background':p.outgoing,'outgoing-background-deeper':p.outgoing,
      'message-primary':p.text,'primary':p.text,'primary-strong':p.text,'primary-title':p.text,'secondary':p.muted,'secondary-strong':p.secondary,'secondary-lighter':p.muted,
      'icon':p.muted,'icon-lighter':p.secondary,'icon-fixed':p.secondary,'border-default':p.border,'border-strong':p.border,'border-bubble':p.border,
      'search-container-background':p.surface,'search-input-container-background':p.input,'search-input-background':p.input,
      'button-primary-background':p.button,'button-primary-background-hover':p.accent,'button-primary':'#FFFFFF','button-secondary':p.accent,'button-secondary-background':p.raised,
      'active-tab-marker':p.accent,'unread-background':p.button,'unread-marker-background':p.button,'unread-marker-text':'#FFFFFF','teal':p.accent,'teal-light':p.accent,'link':p.accent,
      'wallpaper-background':p.bg,'progress-primary':p.accent,'progress-background':p.border,'intro-background':p.bg,'intro-border':p.border,
      'WDS-color-bg-default':p.bg,'WDS-color-bg-alternative':p.surface,'WDS-color-bg-surface':p.surface,'WDS-color-bg-elevated':p.raised,
      'WDS-color-text-primary':p.text,'WDS-color-text-secondary':p.muted,'WDS-color-icon-primary':p.secondary,'WDS-color-border-default':p.border,
      'WDS-color-green-400':p.accent,'WDS-color-green-500':p.button,'WDS-color-green-600':p.button,
      'navbar-background':p.surface,'avatar-background':p.outgoing,'panel-input-background':p.input,
      'WDS-background-wash-plain':p.bg,'WDS-background-wash-inset':p.input,'WDS-background-elevated-wash-plain':p.surface,'WDS-background-elevated-wash-inset':p.raised,
      'WDS-systems-chat-background-wallpaper':p.bg,'WDS-systems-chat-surface-composer':p.surface,'WDS-systems-chat-surface-tray':p.bg,
      'WDS-systems-bubble-surface-incoming':p.raised,'WDS-systems-bubble-surface-outgoing':p.outgoing,'WDS-systems-bubble-surface-system':p.surface,
      'WDS-content-default':p.text,'WDS-content-deemphasized':p.muted,'WDS-content-action-default':p.text,'WDS-content-action-emphasized':p.accent,
      'WDS-content-external-link':p.accent,'WDS-content-on-accent':'#FFFFFF','WDS-content-read':p.accent,'WDS-systems-bubble-content-deemphasized':p.muted
    };
    for(const [key,v] of Object.entries(vars))if(/^#[0-9a-f]{6}$/i.test(v))vars[key+'-RGB']=[1,3,5].map(i=>parseInt(v.slice(i,i+2),16)).join(', ');
    for(const root of [document.documentElement,document.body])if(root)for(const [key,v] of Object.entries(vars))root.style.setProperty('--'+key,v,'important');
    let style=document.getElementById('victor-whatsapp-palette');
    if(!style){style=document.createElement('style');style.id='victor-whatsapp-palette';(document.head || document.documentElement).append(style);}
    style.textContent=`
      html[data-victor-theme],html[data-victor-theme] body,html[data-victor-theme] #app {background:${p.bg}!important;color:${p.text}!important;color-scheme:${theme};}
      html[data-victor-theme] #side,html[data-victor-theme] #main header,html[data-victor-theme] #main footer {background:${p.surface}!important;color:${p.text}!important;}
      html[data-victor-theme] #side {border-right:1px solid ${p.border}!important;}
      html[data-victor-theme] #pane-side {background:${p.bg}!important;}
      html[data-victor-theme] #main {background:${p.bg}!important;}
      html[data-victor-theme] [data-testid="conversation-panel-background"] {background:${p.bg}!important;background-image:none!important;}
      html[data-victor-theme] input,html[data-victor-theme] textarea,html[data-victor-theme] [contenteditable="true"] {color:${p.text}!important;caret-color:${p.accent}!important;}
      html[data-victor-theme] ::selection {background:${p.button};color:white;}
      html[data-victor-theme] ::-webkit-scrollbar-thumb {background:${p.border};border-radius:6px;}
    `;
    toneLogin(p);
  }
  window.__victorWhatsAppTheme=apply;
  window.__victorWhatsAppLoginPalette=()=>toneLogin(theme==='light'?light:dark);
  apply(theme);
  document.addEventListener('DOMContentLoaded',()=>apply(theme),{once:true});
})();
