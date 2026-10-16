'use strict';
const endpoint = 'https://igqveyxbwhnadyubtsnj.supabase.co';
const publicKey = 'sb_publishable_orvUlW5_weHB3Lkh4dbmSA_hXOqHtZH';
const form = document.getElementById('password-form');
const password = document.getElementById('password');
const confirmation = document.getElementById('confirm');
const save = document.getElementById('save');
let accessToken = '', epoch = 0, activeRequest;
function render(title, message) {
 document.getElementById('title').textContent = title;
 document.getElementById('message').textContent = message;
}
function reset() {
 epoch++;
 if (activeRequest) activeRequest.abort();
 accessToken = '';
 form.hidden = true;
 password.value = confirmation.value = '';
 save.disabled = false;
}
async function request(path, token, method = 'GET', body) {
 const controller = new AbortController();
 activeRequest = controller;
 const timer = setTimeout(() => controller.abort(), 15000);
 try {
  return await fetch(endpoint + path, {method, headers:{apikey:publicKey, Authorization:'Bearer ' + token, 'Content-Type':'application/json'}, body:body === undefined ? undefined : JSON.stringify(body), signal:controller.signal, cache:'no-store', credentials:'omit', redirect:'error'});
 } finally {
  clearTimeout(timer);
  if (activeRequest === controller) activeRequest = undefined;
 }
}
async function finishConfirmation(result) {
 reset();
 const current = epoch;
 const token = result.get('access_token');
 const type = result.get('type');
 if (result.has('error') || !token || token.length > 16384) {
  render('Enlace pendiente o caducado', 'Vuelve a VICTOR.IA e intenta iniciar sesión. Si necesitas otro enlace, solicítalo al administrador.');
  return;
 }
 render('Comprobando tu cuenta', 'Espera un momento…');
 try {
  const response = await request('/auth/v1/user', token);
  if (current !== epoch) return;
  if (!response.ok) throw new Error('invalid link');
  if (type === 'invite' || type === 'recovery') {
   accessToken = token;
   form.hidden = false;
   render('Establece tu contraseña', 'El enlace está verificado. Elige la contraseña con la que entrarás a VICTOR.IA.');
  } else {
   render('Correo confirmado', 'Vuelve a VICTOR.IA e inicia sesión con tu correo y contraseña. Ya puedes cerrar esta pestaña.');
  }
 } catch (_) {
  if (current === epoch) render('El enlace no pudo comprobarse', 'Puede haber caducado o faltar conexión. Solicita otro enlace si no puedes entrar a VICTOR.IA.');
 }
}
form.addEventListener('submit', async event => {
 event.preventDefault();
 if (!accessToken || save.disabled) return;
 if (password.value.length < 12 || password.value.length > 256 || password.value !== confirmation.value) {
  render('Revisa tu contraseña', 'Las contraseñas deben coincidir y tener entre 12 y 256 caracteres.');
  return;
 }
 const current = epoch, token = accessToken;
 save.disabled = true;
 render('Guardando contraseña', 'Espera un momento…');
 try {
  const response = await request('/auth/v1/user', token, 'PUT', {password:password.value});
  if (current !== epoch) return;
  if (!response.ok) throw new Error('password rejected');
  reset();
  render('Tu cuenta está lista', 'Ya puedes iniciar sesión en VICTOR.IA con tu correo y contraseña. Cierra esta pestaña.');
  try { await request('/auth/v1/logout?scope=local', token, 'POST'); } catch (_) {}
 } catch (_) {
  if (current === epoch) {
   save.disabled = false;
   password.value = confirmation.value = '';
   render('No se pudo guardar', 'Revisa tu conexión e inténtalo otra vez. Si el enlace caducó, solicita uno nuevo.');
  }
 }
});
addEventListener('hashchange', () => {
 const result = new URLSearchParams(location.hash.slice(1));
 history.replaceState(null, '', location.pathname);
 void finishConfirmation(result);
});
addEventListener('pagehide', reset);
void finishConfirmation(pendingLink);
pendingLink = null;
