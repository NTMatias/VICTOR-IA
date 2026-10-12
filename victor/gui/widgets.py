import math
import json
import re
from PySide6.QtCore import Qt, QTimer, Signal, QRectF, QObject
from PySide6.QtGui import QColor, QPainter, QPen, QIcon, QPixmap, QFont
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QPlainTextEdit, QDialog
from victor.security import Risk
from victor.gui.theme import COLORS, bubble_style
from victor.gui.tool_labels import friendly_name, confirmation_details, readable_names


ICON_PATHS = {
    "image": '<rect x="2" y="3" width="20" height="18" rx="2"/><circle cx="8" cy="8" r="2"/><path d="m2 18 6-6 4 4 4-6 6 8"/>',
    "home": '<path d="m3 10 9-7 9 7v10H4V10M9 20v-7h6v7"/>',
    "mic": '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"/>',
    "grid": '<rect x="3" y="3" width="6" height="6" rx="1"/><rect x="15" y="3" width="6" height="6" rx="1"/><rect x="3" y="15" width="6" height="6" rx="1"/><rect x="15" y="15" width="6" height="6" rx="1"/>',
    "memory": '<path d="M9 4a4 4 0 0 0-6 4c-4 4-1 10 3 10 0 4 6 3 6 0V6c0-3-3-4-3-2M15 4a4 4 0 0 1 6 4c4 4 1 10-3 10 0 4-6 3-6 0"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/>',
    "link": '<path d="m10 13 4-4M8 16l-2 2a4 4 0 0 1-6-6l5-5a4 4 0 0 1 6 0M16 8l2-2a4 4 0 0 1 6 6l-5 5a4 4 0 0 1-6 0"/>',
    "shield": '<path d="m12 2 9 4v6c0 6-9 10-9 10S3 18 3 12V6ZM8 11l3 3 5-6"/>',
    "settings": '<path d="m9 2 6 0 1 3 3 2 3 0 0 6-3 1-2 3 0 3-6 0-1-3-3-2-3 0 0-6 3-1 2-3ZM9 12a3 3 0 1 0 6 0 3 3 0 1 0-6 0"/>',
    "screen": '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M12 17v4M7 21h10"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><ellipse cx="12" cy="12" rx="4" ry="10"/><path d="M2 12h20"/>',
    "folder": '<path d="M2 5h7l2 3h11v13H2Z"/>',
    "file": '<path d="M5 2h9l5 5v15H5ZM14 2v6h5M8 12h8M8 16h8"/>',
    "search": '<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>',
    "send": '<path d="m2 3 20 8-20 10 4-9ZM6 12l16-1"/>',
    "stop": '<rect x="5" y="5" width="14" height="14" rx="2"/>',
    "plus": '<path d="M12 3v18M3 12h18"/>',
    "trash": '<path d="M3 6h18M8 6V3h8v3M6 6v16h12V6M10 9v10M14 9v10"/>',
    "close": '<path d="m5 5 14 14M19 5 5 19"/>',
    "check": '<path d="m4 12 5 5L20 6"/>',
    "refresh": '<path d="M20 8a9 9 0 1 0 0 9M20 2v6h-6"/>',
    "volume": '<path d="M3 9h4l5-5v16l-5-5H3ZM16 8a6 6 0 0 1 0 8M19 5a10 10 0 0 1 0 14"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 5 10 8 10-8"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 2v6M17 2v6M3 10h18M7 14h4"/>',
    "copy": '<rect x="7" y="7" width="14" height="14" rx="2"/><path d="M7 17H3V3h14v4"/>',
    "arrow": '<path d="M12 20V4M6 10l6-6 6 6"/>',
    "edit": '<path d="m3 16 13-13 5 5-13 13-6 1ZM14 5l5 5"/>',
    "list": '<path d="M7 5h14M7 12h14M7 19h14M2 5h1M2 12h1M2 19h1"/>',
    "lock": '<rect x="5" y="10" width="14" height="12" rx="2"/><path d="M8 10V6a4 4 0 0 1 8 0v4"/>',
    "terminal": '<rect x="2" y="3" width="20" height="18" rx="2"/><path d="m6 8 4 4-4 4M13 16h5"/>',
    "fullscreen": '<path d="M3 9V3h6M15 3h6v6M21 15v6h-6M9 21H3v-6"/>',
    "play": '<path d="m7 3 14 9-14 9Z"/>',
    "pause": '<path d="M8 3v18M16 3v18"/>',
    "next": '<path d="m5 4 12 8-12 8ZM19 4v16"/>',
    "previous": '<path d="m19 4-12 8 12 8ZM5 4v16"/>',
    "wifi": '<path d="M2 8a16 16 0 0 1 20 0M5 12a11 11 0 0 1 14 0M8 16a6 6 0 0 1 8 0M12 20h.1"/>',
    "cpu": '<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M8 2v3M16 2v3M8 19v3M16 19v3M2 8h3M2 16h3M19 8h3M19 16h3"/>',
    "brand": '<path fill="#283446" stroke="none" d="m12 1 10 6-2 13-8 4-8-4L2 7Z"/><path stroke="#83AFFF" stroke-width="3.5" d="m7 8 5 10 5-10"/>',
    "wave": '<path stroke-width=".65" d="M2 10v4M4 8v8M6 5v14M8 7v10M10 3v18M12 5v14M14 2v20M16 6v12M18 4v16M20 8v8M22 10v4"/>',
}

def icon(name, color="#83AFFF", size=20):
    """Iconos vectoriales de trazo consistente; independientes de emoji/fuentes."""
    from PySide6.QtSvg import QSvgRenderer
    body = ICON_PATHS.get(name, ICON_PATHS["grid"])
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{body}</g></svg>'
    pix = QPixmap(size*2, size*2); pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix); QSvgRenderer(svg.encode()).render(painter); painter.end()
    pix.setDevicePixelRatio(2)
    return QIcon(pix)

class DashboardDial(QFrame):
    def __init__(self, caption, color):
        super().__init__(); self.caption, self.color, self.value = caption, color, None
        self.unit='%' if caption!='Red' else 'KB/s'
        self.setMinimumSize(76, 90)
    def set_value(self, value):
        self.value = min(100, max(0, value)) if self.unit=='%' else max(0,value); self.update()
    def paintEvent(self, event):
        p=QPainter(self); p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        size=min(62, self.width()-12); x=(self.width()-size)/2
        r=QRectF(x, 5, size, size)
        p.setPen(QPen(QColor('#373C48'), 6)); p.drawEllipse(r)
        p.setPen(QPen(QColor(self.color), 6)); p.drawArc(r, 90*16, int(-(self.value or 0)*3.6*16) if self.unit=='%' else 0)
        from victor.gui.typography import ui_font
        p.setPen(QColor('#20242F' if self.property('light') else COLORS['text'])); f=ui_font(14,True); p.setFont(f)
        reading='—' if self.value is None else f'{self.value:.0f}%' if self.unit=='%' else f'{self.value:.0f}'
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, reading)
        f.setPixelSize(11); f.setWeight(QFont.Weight.Normal); p.setFont(f); p.setPen(QColor(COLORS['muted']))
        p.drawText(QRectF(0,size+12,self.width(),16), Qt.AlignmentFlag.AlignCenter, self.caption if self.unit=='%' else 'Red · KB/s')

class ToolWorker:
    """Cola acotada propia: controles GUI sin depender del turno de la IA."""
    def __init__(self, core, emit, event='panel_result'):
        import threading
        from collections import deque
        from victor.tools.registry import ToolRegistry
        self.cancel=threading.Event(); self.shutdown=threading.Event(); self.wake=threading.Condition(); self.jobs=deque()
        self.core=core;self.active=threading.Event()
        self.emit, self.event = emit, event
        self.registry=ToolRegistry(core.security, self.cancel, emit); self.registry.tools=core.registry.tools
        self.thread=threading.Thread(target=self.run, name='victor-'+event, daemon=True); self.thread.start()
    def submit(self, name, args, coalesce=False):
        with self.wake:
            if self.shutdown.is_set(): return False
            if coalesce: self.jobs=type(self.jobs)(job for job in self.jobs if job[0]!=name)
            if len(self.jobs)>=16: return False
            self.jobs.append((name,dict(args))); self.wake.notify(); return True
    def stop(self):
        self.shutdown.set()
        self.interrupt()
    def interrupt(self):
        self.cancel.set()
        with self.wake: self.jobs.clear(); self.wake.notify_all()
    def run(self):
        try:self.run_jobs()
        finally:self.core.spotify.close_client()

    def run_jobs(self):
        import time
        from victor.errors import Cancelled
        while not self.shutdown.is_set():
            with self.wake:
                while not self.jobs and not self.shutdown.is_set(): self.wake.wait(.5)
                if self.shutdown.is_set(): return
                name,args=self.jobs.popleft()
                self.cancel.clear()
            if not self.core.busy.is_set(): self.core.cancel.clear()
            started=time.monotonic()
            self.active.set()
            try: result=self.registry.execute(name,args)
            except Cancelled: result={'ok':False,'error':'Acción cancelada.'}
            finally:self.active.clear()
            self.emit(self.event, (name, result, time.monotonic()-started))


def display_text(text):
    """Presentación local de resultados; conserva incertidumbre y no añade acciones."""
    def render(value):
        if isinstance(value, dict):
            return "\n".join(f"{str(k).replace('_', ' ').capitalize()}: {render(v)}" for k, v in value.items())
        if isinstance(value, list):
            return "\n".join("• " + render(v) for v in value) or "Sin elementos."
        if isinstance(value, bool):
            return "Sí" if value else "No"
        return "No disponible" if value is None else str(value)
    if isinstance(text,(dict,list)):return render(text)
    raw = str(text).strip()
    prefix = ''
    spotify_wrapper=raw.startswith('[Resultado de herramienta spotify_')
    if raw.startswith('[Resultado de herramienta ') and '\n' in raw:
        prefix, raw = raw.split('\n', 1)
        prefix = friendly_name(prefix.removeprefix('[Resultado de herramienta ').removesuffix(']')) + '\n'
    try:
        value = json.loads(raw.removeprefix('```json').removeprefix('```').removesuffix('```').strip())
        if isinstance(value, (dict, list)):
            raw = render(value)
    except (ValueError, TypeError):
        if spotify_wrapper:
            raw = 'Respuesta sin ejecución verificada. No confirma que Spotify haya reproducido la canción.'
        elif raw.startswith(('{', '[{', '```json')):
            raw = 'Preparando resultado…'
    return readable_names(prefix + re.sub(r"(?:[A-Za-z]:[/\\])[^\n]{70,}", lambda m: m[0][:20] + "…" + m[0][-35:], raw))


class MessageRow(QFrame):
    def __init__(self, role, text):
        super().__init__()
        self.bubble = Bubble(role, text)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if role == "user":
            layout.addStretch()
        else:
            avatar=QLabel('V'); avatar.setAlignment(Qt.AlignmentFlag.AlignCenter); avatar.setFixedSize(30,30)
            avatar.setStyleSheet('color:#A9C8FF; background:#2B3F59; border-radius:10px; font-weight:700;')
            layout.addWidget(avatar,alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.bubble)
        if role != "user":
            layout.addStretch()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        maximum=max(120,int(self.width()*.70))
        self.bubble.setMaximumWidth(maximum)
        self.bubble.setMinimumWidth(min(maximum, max(240,min(720,self.bubble.label.fontMetrics().horizontalAdvance(self.bubble.label.text())+32))))


class Composer(QPlainTextEdit):
    submitted = Signal()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.submitted.emit()
        else:
            super().keyPressEvent(event)


class Bubble(QFrame):
    def __init__(self, role, text):
        super().__init__()
        self.setStyleSheet(bubble_style(role))
        self.role = role
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 11, 15, 11)
        speaker=QLabel('TÚ' if role=='user' else 'VICTOR');self.speaker=speaker
        speaker.setStyleSheet('font-size:11px; font-weight:600; color:#B8BCC8;')
        layout.addWidget(speaker)
        if role == 'user':self.label = QLabel(text)
        else:
            from victor.gui.chat_text import MarkdownLabel
            self.label = MarkdownLabel(text)
        self.label.setWordWrap(True)
        if role == 'user':
            self.label.setTextFormat(Qt.TextFormat.PlainText)
            self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.label)
        self.set_text(text)

    def apply_theme(self, light):
        self.setStyleSheet(bubble_style(self.role,light))
        if self.role != 'user':self.label.apply_theme(light)
        self.speaker.setStyleSheet('font-size:11px; font-weight:600; color:'+('#475266' if light else '#B8BCC8')+';')

    def set_text(self, text):
        if hasattr(self,'music'):self.music.hide();self.label.show()
        self.label.setText(display_text(text) if self.role != "user" else text)

    def show_image(self,record):
        from victor.gui.images import ImageCard
        if hasattr(self,'generated_image'):self.generated_image.deleteLater()
        self.generated_image=ImageCard(record,self);self.layout().addWidget(self.generated_image)
        self.label.setToolTip('')

    def show_music(self,state):
        if not hasattr(self,'music'):
            from victor.gui.spotify_embed import SpotifyNowPlaying
            self.music=SpotifyNowPlaying(self);self.layout().addWidget(self.music)
        self.label.clear();self.label.setToolTip('');self.label.hide();self.music.update_state(state);self.music.show()


class ApprovalCard(QFrame):
    """Confirmación dentro del chat; la aprobación no puede producirla el modelo."""
    def __init__(self, request, parent=None):
        super().__init__(parent)
        self.request = request
        self.setObjectName("approval")
        layout = QVBoxLayout(self)
        title = QLabel("Autorizar: " + friendly_name(request.title))
        title.setStyleSheet('font-size:20px; font-weight:650;')
        if request.origin:
            title.setText(title.text() + " · " + str(request.origin["user_id"]))
        title.setWordWrap(True)
        layout.addWidget(title)
        details = QPlainTextEdit(confirmation_details(request.title, request.details))
        details.setReadOnly(True)
        details.setMaximumHeight(210)
        layout.addWidget(details)
        self.phrase = None
        if request.risk == Risk.HIGH:
            layout.addWidget(QLabel("Escribe EJECUTAR para autorizar en este PC"))
            self.phrase = QLineEdit()
            layout.addWidget(self.phrase)
        row = QHBoxLayout()
        self.approve = QPushButton("Confirmar")
        self.approve.setObjectName("primary")
        self.decline = QPushButton("Cancelar")
        self.approve.setIcon(icon('check'));self.decline.setIcon(icon('close'))
        self.approve.clicked.connect(lambda: self.resolve(True))
        self.decline.clicked.connect(lambda: self.resolve(False))
        row.addWidget(self.approve)
        row.addWidget(self.decline)
        layout.addLayout(row)
        if self.phrase:
            self.approve.setEnabled(False)
            self.phrase.textChanged.connect(lambda text: self.approve.setEnabled(text == "EJECUTAR"))

    def resolve(self, accepted):
        if self.request.done.is_set() or (accepted and self.phrase and self.phrase.text() != "EJECUTAR"):
            return
        self.request.accepted = accepted
        self.request.done.set()
        self.approve.setEnabled(False)
        self.decline.setEnabled(False)
        if self.phrase:
            self.phrase.setEnabled(False)
        self.layout().addWidget(QLabel("Autorizado una vez" if accepted else "Cancelado"))


class ApprovalDialog(QDialog):
    def __init__(self, parent, request):
        super().__init__(parent)
        self.setWindowTitle("VICTOR.IA · Confirmación explícita")
        self.setModal(True)
        self.resize(508, 440)
        self.card = ApprovalCard(request)
        layout = QVBoxLayout(self)
        layout.addWidget(self.card)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_done)
        self.timer.start(100)

    def check_done(self):
        if self.card.request.done.is_set():
            self.accept()

    def reject(self):
        self.card.resolve(False)
        super().reject()


class ListeningWave(QFrame):
    """Historial del nivel medido: nunca inventa audio durante el silencio."""
    def __init__(self):
        super().__init__()
        from collections import deque
        self.level=0.;self.target=0.;self.history=deque([0.]*32,maxlen=32)
        self.active = False
        self.setFixedHeight(38)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)

    def set_active(self, active):
        if active and not self.active:self.history=type(self.history)([0.]*32,maxlen=32)
        self.active = active
        if not active:
            self.target=0.;self.level=0.;self.history=type(self.history)([0.]*32,maxlen=32)
        if self.isVisible():self.timer.start(40)
        self.update()

    def set_level(self,level):
        self.target=max(0.,min(1.,float(level))) if math.isfinite(float(level)) else 0.
        self.history.append(self.target)
        if self.isVisible():self.timer.start(40)

    def showEvent(self,event):
        super().showEvent(event)
        if self.active:self.timer.start(40)

    def hideEvent(self,event):
        super().hideEvent(event);self.timer.stop()

    def tick(self):
        self.level+=(self.target-self.level)*.35
        if not self.isVisible() or self.window().isMinimized():self.timer.stop();return
        if not self.active and self.level<.002:self.timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(COLORS["accent"]), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for i in range(32):
            height = 3 + self.history[i]*28
            x = self.width() / 2 + (i-16) * 6
            painter.drawLine(int(x), int(19-height/2), int(x), int(19+height/2))


class AdaptiveButton(QPushButton):
    """Elide solo al pintar: conserva texto, accesibilidad y acción completos."""
    def __init__(self,*args,**kwargs):
        from PySide6.QtWidgets import QSizePolicy
        super().__init__(*args,**kwargs);self.setSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Fixed)
    def minimumSizeHint(self):
        hint=super().minimumSizeHint()
        if self.window().width()<800:hint.setWidth(min(100,hint.width()))
        return hint
    def paintEvent(self,event):
        from PySide6.QtWidgets import QStylePainter,QStyleOptionButton,QStyle
        painter=QStylePainter(self);option=QStyleOptionButton();self.initStyleOption(option)
        content=self.style().subElementRect(QStyle.SubElement.SE_PushButtonContents,option,self)
        room=max(0,content.width()-(self.iconSize().width()+4 if not self.icon().isNull() else 0))
        if self.width()<self.sizeHint().width():option.text='\n'.join(self.fontMetrics().elidedText(line,Qt.TextElideMode.ElideRight,room) for line in self.text().split('\n'))
        if option.text!=self.text() and not self.toolTip():self.setToolTip(self.text())
        painter.drawControl(QStyle.ControlElement.CE_PushButton,option)


class ActionTile(AdaptiveButton):
    """Tarjeta con contenido: su altura depende del layout, no del texto del botón."""
    def __init__(self):
        from PySide6.QtWidgets import QSizePolicy
        super().__init__();self.setStyleSheet('QPushButton {padding:0; min-height:80px;}')
        policy=QSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Preferred);policy.setHeightForWidth(True);self.setSizePolicy(policy)
    def hasHeightForWidth(self):return True
    def heightForWidth(self,width):
        layout=self.layout()
        return max(80,layout.totalHeightForWidth(width) if layout else 80)
    def sizeHint(self):
        hint=super().sizeHint()
        if self.layout():hint=hint.expandedTo(self.layout().totalSizeHint())
        hint.setHeight(max(80,hint.height()));return hint
    def minimumSizeHint(self):
        hint=super().minimumSizeHint();hint.setWidth(min(100,hint.width()));hint.setHeight(80);return hint
    def sync_height(self):
        needed=self.heightForWidth(self.width())
        if self.minimumHeight()!=needed:self.setMinimumHeight(needed);self.updateGeometry()
    def resizeEvent(self,event):super().resizeEvent(event);self.sync_height()


class ResponsiveButtons(QFrame):
    """Cuadrícula que envuelve botones sin recortar sus textos en ventanas pequeñas."""
    def __init__(self,buttons,columns=4,cell_width=130):
        from PySide6.QtWidgets import QGridLayout
        super().__init__();self.buttons=list(buttons);self.columns=columns;self.cell_width=cell_width;self.current_columns=0;self.available_width=None
        self.grid=QGridLayout(self);self.grid.setContentsMargins(0,0,0,0);self.grid.setSpacing(8)
        self.arrange()
    def arrange(self):
        available=min(self.width(),self.available_width) if self.available_width is not None else self.width()
        columns=max(1,min(self.columns,(max(available,self.cell_width)+8)//(self.cell_width+8)))
        if columns==self.current_columns:return
        self.current_columns=columns
        for i in range(self.columns):self.grid.setColumnStretch(i,1 if i<columns else 0)
        for i,widget in enumerate(self.buttons):self.grid.addWidget(widget,i//columns,i%columns)
    def resizeEvent(self,event):super().resizeEvent(event);self.arrange()


def brand_icon(provider,light=False,size=26):
    from pathlib import Path
    from PySide6.QtSvg import QSvgRenderer
    svg=(Path(__file__).parent/'assets'/(provider.lower()+'.svg')).read_text(encoding='utf-8')
    if light:svg=svg.replace('#E9EAF1','#20242F')
    pix=QPixmap(size,size);pix.fill(Qt.GlobalColor.transparent)
    painter=QPainter(pix);QSvgRenderer(svg.encode()).render(painter);painter.end()
    return QIcon(pix)


class WindowControl(QPushButton):
    """Símbolos de ventana estilo Windows: sin círculos y con hitbox accesible."""
    def __init__(self,action,callback):
        super().__init__();self.action=action;self.setFixedSize(44,30)
        self.setStyleSheet('border:0; padding:0; min-width:44px; min-height:30px; max-width:44px; max-height:30px; background:transparent;')
        title={'close':'Cerrar','minimize':'Minimizar','maximize':'Maximizar / restaurar'}[action]
        self.setToolTip(title);self.setAccessibleName(title);self.clicked.connect(callback)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.underMouse() or self.isDown():
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(QColor('#C42B1C' if self.action=='close' else '#394152'));p.drawRoundedRect(self.rect(),4,4)
        light=getattr(self.window(),'config',None) and self.window().config.get('theme')=='Light'
        p.setPen(QPen(QColor('#FFFFFF' if self.action=='close' and (self.underMouse() or self.isDown()) else '#20242F' if light else '#E9EAF1'),1.1));p.setBrush(Qt.BrushStyle.NoBrush)
        cx,cy=self.width()/2,self.height()/2
        if self.action=='close':p.drawLine(int(cx-4),int(cy-4),int(cx+4),int(cy+4));p.drawLine(int(cx-4),int(cy+4),int(cx+4),int(cy-4))
        elif self.action=='minimize':p.drawLine(int(cx-4),int(cy),int(cx+4),int(cy))
        elif self.window().isMaximized():
            p.drawLine(int(cx-2),int(cy-4),int(cx+4),int(cy-4));p.drawLine(int(cx+4),int(cy-4),int(cx+4),int(cy+2))
            p.drawRect(QRectF(cx-4,cy-2,6,6))
        else:p.drawRect(QRectF(cx-4,cy-4,8,8))


class WindowSnapshot(QFrame):
    """Capa efímera de una captura Qt propia; no captura el escritorio."""
    def __init__(self,window,pixmap):
        super().__init__(window,Qt.WindowType.Tool|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.WindowDoesNotAcceptFocus)
        self.pixmap=pixmap;self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground);self.setStyleSheet('background:transparent;border:0;')
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(self.rect(),self.pixmap)


class WindowTransitions(QObject):
    """Escala/fade sin sleeps, cambios repetidos ni reemplazar el cierre de workers."""
    def __init__(self,window):
        from collections import deque
        super().__init__(window);self.window=window;self.animation=None;self.overlay=None;self.normal_geometry=None
        self.close_visual_done=False;self.completed=deque(maxlen=20)
    @property
    def running(self):return self.animation is not None
    def cancel(self,restore=True):
        if self.animation:self.animation.stop();self.animation.deleteLater();self.animation=None
        if self.overlay:self.overlay.hide();self.overlay.deleteLater();self.overlay=None
        if restore and not self.window.closing:self.window.show()
    def start(self,action):
        from PySide6.QtCore import QPropertyAnimation,QParallelAnimationGroup,QRect,QEasingCurve
        w=self.window
        if w.closing:return False
        if self.running:
            if action!='close':return False
            self.cancel()
        screen=w.screen();available=screen.availableGeometry() if screen else w.geometry()
        before=w.geometry();after=QRect(before);restore=action in ('restore','restore_minimized')
        if action=='maximize':self.normal_geometry=QRect(before);after=available
        elif action=='restore' and self.normal_geometry is not None:after=QRect(self.normal_geometry)
        elif action=='minimize':after=QRect(available.center().x()-80,available.bottom()-72,160,64)
        elif action=='restore_minimized':before=QRect(available.center().x()-80,available.bottom()-72,160,64)
        elif action=='close':after=QRect(before.center().x()-int(before.width()*.45),before.center().y()-int(before.height()*.45),int(before.width()*.9),int(before.height()*.9))
        else:
            if action!='restore':raise ValueError('Unknown window transition')
        pixmap=w.grab()
        def complete():
            if action=='close':self.close_visual_done=True;w.close()
            elif action=='minimize':w.showMinimized()
            elif action=='maximize':w.showMaximized();w.activateWindow()
            elif restore:w.showNormal();w.setGeometry(after);w.activateWindow()
        if pixmap.isNull():QTimer.singleShot(0,complete);return False
        self.overlay=WindowSnapshot(w,pixmap);self.overlay.setGeometry(before)
        self.overlay.setWindowOpacity(.12 if action=='restore_minimized' else 1.)
        group=QParallelAnimationGroup(self);self.animation=group
        geometry=QPropertyAnimation(self.overlay,b'geometry',group);geometry.setStartValue(before);geometry.setEndValue(after)
        opacity=QPropertyAnimation(self.overlay,b'windowOpacity',group);opacity.setStartValue(.12 if action=='restore_minimized' else 1.);opacity.setEndValue(.05 if action in ('close','minimize') else 1.)
        for animation in (geometry,opacity):
            animation.setDuration(220 if action=='close' else 260);animation.setEasingCurve(QEasingCurve.Type.InOutCubic);group.addAnimation(animation)
        def finish():
            overlay=self.overlay;self.overlay=None;self.animation=None;self.completed.append(action)
            complete()
            if overlay:overlay.hide();overlay.deleteLater()
            group.deleteLater()
        group.finished.connect(finish)
        w.hide();self.overlay.show();group.start();return True


class TransientNotice(QLabel):
    """Avisos con caducidad y fade; un mensaje nuevo cancela el fade anterior."""
    def __init__(self):
        from collections import deque
        from PySide6.QtWidgets import QGraphicsOpacityEffect
        from PySide6.QtCore import QPropertyAnimation
        super().__init__();self.history=deque(maxlen=20);self.setWordWrap(True);self.setTextFormat(Qt.TextFormat.PlainText)
        self.effect=QGraphicsOpacityEffect(self);self.setGraphicsEffect(self.effect)
        self.fade=QPropertyAnimation(self.effect,b'opacity',self);self.fade.setDuration(240)
        self.fade.finished.connect(self.dismiss)
        self.expiry=QTimer(self);self.expiry.setSingleShot(True);self.expiry.timeout.connect(self.start_fade);self.hide()
    def setText(self,text):
        from datetime import datetime
        self.expiry.stop();self.fade.stop();self.effect.setOpacity(1.)
        super().setText(str(text))
        if not text:self.hide();return
        self.history.append(datetime.now().strftime('%H:%M:%S')+' · '+str(text))
        self.show();self.expiry.start(5500)
    def clear(self):self.dismiss()
    def dismiss(self):
        self.expiry.stop();self.fade.stop();super().clear();self.hide();self.effect.setOpacity(1.)
    def start_fade(self):
        self.fade.setStartValue(self.effect.opacity());self.fade.setEndValue(0.);self.fade.start()


class AudioOrb(QPushButton):
    """Orbe de la voz de VICTOR: amplitud del audio, no una animación aleatoria."""
    def __init__(self):
        from PySide6.QtWidgets import QSizePolicy
        super().__init__();self.level=0.;self.target=0.;self.active=False
        self.setMinimumSize(150,150);self.setMaximumSize(250,250);self.setSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Preferred)
        self.setStyleSheet('border:0;padding:0;min-width:150px;min-height:150px;background:transparent;')
        self.timer=QTimer(self);self.timer.setInterval(40);self.timer.timeout.connect(self.tick)
        self.setAccessibleName('Activar o desactivar micrófono')
    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(250,250)
    def set_level(self,level):
        self.target=max(0.,min(1.,float(level))) if math.isfinite(float(level)) else 0.
        if self.isVisible():self.timer.start()
    def set_active(self,active):
        self.active=active
        if not active:self.set_level(0.)
        self.update()
    def showEvent(self,event):super().showEvent(event);self.timer.start()
    def hideEvent(self,event):super().hideEvent(event);self.timer.stop()
    def tick(self):
        self.level+=(self.target-self.level)*(.45 if self.target>self.level else .2)
        self.update()
        if self.window().isMinimized() or (self.target==0 and self.level<.002):self.timer.stop()
    def paintEvent(self,event):
        from PySide6.QtGui import QRadialGradient
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        radius=min(self.width(),self.height())*(.35+.06*self.level);cx=self.width()/2;cy=self.height()/2
        glow=QRadialGradient(cx,cy,radius*1.4);c=QColor('#83AFFF');c.setAlpha(int(20+90*self.level));glow.setColorAt(0,c);glow.setColorAt(1,QColor(0,0,0,0))
        p.setPen(Qt.PenStyle.NoPen);p.setBrush(glow);p.drawEllipse(QRectF(cx-radius*1.4,cy-radius*1.4,radius*2.8,radius*2.8))
        p.setBrush(QColor('#252A34'));p.setPen(QPen(QColor('#455876'),1));p.drawEllipse(QRectF(cx-radius,cy-radius,radius*2,radius*2))
        p.setPen(QPen(QColor('#83AFFF'),3,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        for i in range(11):
            weight=1-abs(i-5)/6;height=8+weight*(16+80*self.level);x=cx+(i-5)*8
            p.drawLine(int(x),int(cy-height/2),int(x),int(cy+height/2))
