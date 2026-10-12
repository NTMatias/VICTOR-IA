"""Telegram por polling, sin puertos. Toda orden se entrega a la GUI → VictorCore."""
import asyncio
from collections import defaultdict, deque
import hashlib
import logging
import os
from pathlib import Path
import secrets
import tempfile
import threading
import time
from victor.errors import VictorError
from victor.security import Risk
from victor.tools.registry import Tool


class TelegramService:
    def __init__(self, config, core, transcriber, emit):
        self.config, self.core, self.transcriber, self.emit = config, core, transcriber, emit
        self.stop_event = threading.Event()
        self.thread = None
        self.loop = None
        self.application = None
        self.ready = threading.Event()
        self.lock = threading.RLock()
        self.pair_hash, self.pair_expiry, self.pair_attempts = "", 0, 0
        self.rate = defaultdict(deque)
        self.pending = {}
        self.voice_busy = False
        self.log = logging.getLogger("victor.telegram")
        core.registry.register(Tool("share_screen_telegram", "Capturar y enviar la pantalla al chat Telegram autorizado actual. La imagen pasa por servidores de Telegram; puede contener datos personales.",
            {"type": "object", "properties": {}, "additionalProperties": False}, Risk.MEDIUM, self.send_capture))

    @property
    def running(self):
        return bool(self.thread and self.thread.is_alive())

    def authorized(self, user_id):
        return type(user_id) is int and user_id in self.config.get("telegram_allowed_ids")

    def can_execute(self, origin):
        return self.authorized(origin.get("user_id")) and not self.config.get("remote_block_all") and not self.config.get("telegram_paused") and self.ready.is_set()

    def pairing_code(self):
        if not self.ready.is_set():
            raise VictorError("Activa Telegram con un token válido antes de emparejar.")
        code = f"{secrets.randbelow(100000000):08d}"
        with self.lock:
            self.pair_hash = hashlib.sha256(code.encode()).hexdigest()
            self.pair_expiry = time.monotonic()+120
            self.pair_attempts = 0
        return code

    def pair(self, user_id, code):
        with self.lock:
            if not self.pair_hash or time.monotonic() > self.pair_expiry or self.pair_attempts >= 5:
                return False
            self.pair_attempts += 1
            if not secrets.compare_digest(hashlib.sha256(code.encode()).hexdigest(), self.pair_hash):
                return False
            self.pair_hash = ""
            ids = list(dict.fromkeys(self.config.get("telegram_allowed_ids") + [user_id]))
            self.config.save({"telegram_allowed_ids": ids})
            self.log.info("paired user=%s", user_id)
            self.emit("notice", f"Telegram emparejado: usuario {user_id}.")
            return True

    def within_rate(self, user_id):
        now = time.monotonic()
        with self.lock:
            times = self.rate[user_id]
            while times and now-times[0] > 30:
                times.popleft()
            if len(times) >= self.config.get("remote_rate_limit"):
                return False
            times.append(now)
            return True

    def start(self):
        if self.running:
            return
        if not os.environ.get("TELEGRAM_BOT_TOKEN", "").strip():
            self.emit("notice", "Telegram desactivado: falta TELEGRAM_BOT_TOKEN en .env.")
            return
        try:
            import telegram.ext
        except ImportError:
            self.emit("notice", "Telegram desactivado: instala python-telegram-bot con instalar.bat.")
            return
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, name="victor-telegram", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        self.ready.clear()
        with self.lock:
            self.pair_hash = ""
            for request, origin in self.pending.values():
                request.done.set()
            self.pending.clear()
        if getattr(self.core, "active_origin", None):
            self.core.stop()

    def pause(self, paused=True):
        self.config.save({"telegram_paused": paused})
        if paused and getattr(self.core, "active_origin", None):
            self.core.stop()
        self.emit("notice", "Telegram pausado." if paused else "Telegram reanudado.")

    def _run(self):
        try:
            asyncio.run(self._serve())
        except Exception as exc:
            self.log.error("polling stopped error_type=%s", type(exc).__name__)
            self.emit("notice", "Telegram no pudo conectarse. Revisa el token, Internet y que no haya otra instancia del bot.")
        finally:
            self.ready.clear()
            self.loop = None
            self.application = None

    async def _serve(self):
        from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters
        self.loop = asyncio.get_running_loop()
        self.application = (Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).concurrent_updates(4)
            .connect_timeout(8).read_timeout(15).write_timeout(15).get_updates_read_timeout(20).build())
        self.application.add_handler(CallbackQueryHandler(self._callback))
        self.application.add_handler(MessageHandler(filters.ALL, self._message))
        async def on_error(update, context):
            self.log.warning("telegram update error_type=%s", type(context.error).__name__)
            self.emit("notice", "No se pudo completar una operación de Telegram.")
        self.application.add_error_handler(on_error)
        async with self.application:
            await self.application.start()
            try:
                await self.application.updater.start_polling(timeout=10, drop_pending_updates=True, bootstrap_retries=0)
                self.ready.set()
                self.emit("notice", "Telegram conectado. Solo se aceptan chats privados emparejados.")
                while not self.stop_event.is_set():
                    with self.lock:
                        for token, (request, origin) in list(self.pending.items()):
                            if request.done.is_set():
                                self.pending.pop(token, None)
                    await asyncio.sleep(.2)
            finally:
                self.ready.clear()
                if self.application.updater.running:
                    await self.application.updater.stop()
                await self.application.stop()

    async def _message(self, update, context):
        user, chat, message = update.effective_user, update.effective_chat, update.effective_message
        if not user or not chat or not message or chat.type != "private" or chat.id != user.id:
            return
        text = (message.text or "").strip()
        if text.startswith("/vincular "):
            if self.pair(user.id, text.split(maxsplit=1)[1].strip()):
                await message.reply_text("PC emparejado. Usa /ayuda. No compartas el acceso a este bot.")
            return
        if not self.authorized(user.id):
            return
        if not self.within_rate(user.id):
            await message.reply_text("Demasiadas órdenes. Espera 30 segundos.")
            return
        origin = {"source": "telegram", "user_id": user.id, "chat_id": chat.id}
        command = text.split(maxsplit=1)[0].split("@")[0].lower() if text else ""
        if command in ("/pausa", "/reanudar"):
            if self.config.get("remote_block_all"):
                await message.reply_text("El control remoto está bloqueado desde el PC.")
                return
            self.pause(command == "/pausa")
            await message.reply_text("Pausado." if command == "/pausa" else "Reanudado.")
            return
        if command == "/estado":
            await message.reply_text("PC ocupado." if self.core.busy.is_set() else "PC listo." + (" Control pausado." if self.config.get("telegram_paused") else ""))
            return
        if command in ("/ayuda", "/start"):
            await message.reply_text("Envía texto o notas de voz de hasta 60 segundos.\n/estado /captura /pausa /reanudar /ayuda\nLas acciones de alto riesgo se bloquean o requieren confirmación en el PC.")
            return
        if not self.can_execute(origin):
            await message.reply_text("Control remoto pausado o bloqueado desde el PC.")
            return
        if self.core.busy.is_set():
            await message.reply_text("El PC está ocupado. Espera a que termine la orden actual.")
            return
        direct = ("share_screen_telegram", {}) if command == "/captura" else None
        if message.voice:
            if self.voice_busy or message.voice.duration > 60 or (message.voice.file_size or 0) > 15_000_000:
                await message.reply_text("Envía una sola nota de voz, de hasta 60 segundos y 15 MB.")
                return
            self.voice_busy = True
            try:
                with tempfile.TemporaryDirectory(prefix="victor-voice-") as folder:
                    path = Path(folder) / "voice.ogg"
                    remote_file = await message.voice.get_file(read_timeout=15, connect_timeout=8)
                    await remote_file.download_to_drive(path, read_timeout=15, connect_timeout=8)
                    text = await asyncio.to_thread(self.transcriber.transcribe_file, path, self.stop_event)
                await message.reply_text("Transcripción: " + (text[:3500] or "No reconocí una orden."))
            except VictorError as exc:
                await message.reply_text(str(exc))
                return
            except Exception as exc:
                self.log.warning("voice error_type=%s", type(exc).__name__)
                await message.reply_text("No pude descargar o transcribir la nota de voz.")
                return
            finally:
                self.voice_busy = False
        if not text or len(text) > 4000:
            return
        # El hilo GUI vuelve a comprobar permisos y disponibilidad antes de submit().
        self.emit("remote_command", {"text": "Enviar captura por Telegram" if direct else text, "origin": origin, "tool": direct})

    def schedule(self, coroutine):
        if not self.ready.is_set() or self.loop is None:
            coroutine.close()
            raise VictorError("Telegram no está conectado.")
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop)

    def reply(self, origin, text):
        if not self.authorized(origin["user_id"]):
            return
        async def send():
            try:
                for i in range(0, min(len(text), 16000), 3800):
                    await self.application.bot.send_message(origin["chat_id"], text[i:i+3800], read_timeout=15, write_timeout=15)
            except Exception as exc:
                self.log.warning("reply error_type=%s", type(exc).__name__)
                self.emit("notice", "No pude entregar la respuesta en Telegram; está en el historial del PC.")
        try:
            self.schedule(send())
        except VictorError:
            self.emit("notice", "Telegram desconectado; respuesta disponible en el historial del PC.")

    def request_approval(self, request):
        origin = request.origin
        if request.risk == Risk.HIGH or not origin or not self.can_execute(origin):
            request.done.set()
            return
        if len(request.details) > 2800:
            self.reply(origin, "Revisa los parámetros completos y confirma esta acción en el PC.")
            self.emit("approval", request)
            return
        token = secrets.token_urlsafe(12)
        with self.lock:
            self.pending[token] = (request, origin)
        async def send():
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            try:
                await self.application.bot.send_message(origin["chat_id"],
                    "Autorizar una vez: " + request.title + "\n" + request.details[:3000],
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Confirmar", callback_data="v:"+token+":y"),
                                                       InlineKeyboardButton("Cancelar", callback_data="v:"+token+":n")]]))
            except Exception:
                request.done.set()
        try:
            self.schedule(send())
        except VictorError:
            request.done.set()

    def resolve_callback(self, user_id, chat_id, data):
        parts = data.split(":")
        if len(parts) != 3 or parts[0] != "v" or parts[2] not in ("y", "n"):
            return False
        with self.lock:
            pair = self.pending.get(parts[1])
            if not pair:
                return False
            request, origin = pair
            if request.risk == Risk.HIGH or origin["user_id"] != user_id or origin["chat_id"] != chat_id or not self.can_execute(origin):
                return False
            self.pending.pop(parts[1], None)
            if request.done.is_set():
                return False
            request.accepted = parts[2] == "y"
            request.done.set()
            return True

    async def _callback(self, update, context):
        query = update.callback_query
        if not query or not self.authorized(query.from_user.id) or not query.message:
            return
        ok = self.resolve_callback(query.from_user.id, query.message.chat.id, query.data or "")
        await query.answer("Registrado" if ok else "Confirmación inválida o caducada")
        if ok:
            await query.edit_message_reply_markup(reply_markup=None)

    def send_capture(self):
        origin = self.core.security.origin()
        if not origin or not self.can_execute(origin):
            raise VictorError("Enviar capturas requiere un chat Telegram emparejado y activo.")
        capture = self.core.screen.capture()
        async def send():
            with open(capture["captura"], "rb") as photo:
                await self.application.bot.send_photo(origin["chat_id"], photo, caption="Captura autorizada desde VICTOR.IA", read_timeout=20, write_timeout=20)
        future = self.schedule(send())
        try:
            future.result(timeout=30)
        except Exception:
            future.cancel()
            raise VictorError("No pude confirmar la entrega de la captura en Telegram.") from None
        self.log.info("screen sent user=%s", origin["user_id"])
        return {"enviada_a_telegram": True}
