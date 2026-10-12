"""WebSocket separado con ACK ordenado, latido, revocación y foco aislado."""
import asyncio
import json
import secrets
import os
import subprocess
import sys
import time
from pathlib import Path
from victor.errors import VictorError
from victor.integrations.keyboard_worker import KeyboardWorker


def install_keyboard_route(app, remote, authenticate):
    from fastapi import WebSocket
    @app.websocket('/keyboard')
    async def keyboard(ws: WebSocket):
        worker=None;focus_task=None;origin=None
        write_lock=asyncio.Lock()  # Solo serializa este socket, nunca captura o SendInput.
        async def send(data):
            async with write_lock:
                await asyncio.wait_for(ws.send_json(data),3)
        async def focus_probe():
            process=None
            try:
                process=await asyncio.create_subprocess_exec(sys.executable,'-m','victor.system.remote_focus',
                    cwd=str(Path(__file__).resolve().parents[2]),stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                first=True
                while remote.authorized(origin):
                    line=await asyncio.wait_for(process.stdout.readline(),8 if first else 2)
                    first=False
                    if not line:break
                    data=json.loads(line)
                    if data.get('type')=='focus':await send(data)
            except asyncio.CancelledError:raise
            except Exception:
                try:await send({'type':'focus_unavailable','message':'No se pudo detectar el campo. Usa el botón Teclado.'})
                except Exception:pass
            finally:
                if process and process.returncode is None:
                    process.kill()
                    await process.wait()
        try:
            origin=await authenticate(ws,False)
            if not origin:return
            capability=secrets.token_urlsafe(24)
            with remote.lock:
                remote.sessions[origin['session']]['keyboard_channel']=capability
            origin=dict(origin,keyboard_channel=capability)
            worker=KeyboardWorker(remote,origin)
            with remote.lock:remote.keyboard_workers.add(worker)
            worker.start()
            focus_task=asyncio.create_task(focus_probe())
            start=time.monotonic();count=0
            while remote.authorized(origin):
                while not worker.outbox.empty():await send(worker.outbox.get_nowait())
                if worker.cancel.is_set():break
                try:data=json.loads(await asyncio.wait_for(ws.receive_text(),.02))
                except asyncio.TimeoutError:continue
                if isinstance(data,dict) and data=={'type':'ping'}:
                    await send({'type':'pong'});continue
                now=time.monotonic()
                if now-start>=1:start=now;count=0
                count+=1
                if count>100:raise VictorError('Demasiados eventos de teclado. Reconecta y escribe más despacio.')
                worker.submit(data)
            await send({'type':'disconnected','message':'Teclado detenido o sesión caducada. Genera un nuevo QR para reconectar.'})
        except Exception as exc:
            try:await send({'type':'disconnected','message':str(exc) if isinstance(exc,VictorError) else 'Conexión de teclado interrumpida. Revisa Wi-Fi y vuelve a emparejar.'})
            except Exception:pass
        finally:
            if worker:
                worker.stop()
                with remote.lock:remote.keyboard_workers.discard(worker)
            if focus_task:
                focus_task.cancel()
            if origin:
                with remote.lock:
                    entry=remote.sessions.get(origin['session'])
                    if entry and entry.get('keyboard_channel')==origin.get('keyboard_channel'):
                        entry.pop('keyboard_channel',None)
            # Starlette puede cancelar el endpoint al desconectar. Limpiar incluso
            # dentro de su cancel scope; revocación anterior ya fue síncrona.
            import anyio
            with anyio.CancelScope(shield=True):
                if focus_task:
                    try:await focus_task
                    except asyncio.CancelledError:pass
                if worker:await asyncio.to_thread(worker.thread.join,1)
                try:await ws.close(code=1000)
                except Exception:pass
