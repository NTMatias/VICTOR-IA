"""Click-through voice meter: no idle animation or additional microphone."""
import math
from PySide6.QtCore import Qt,QTimer,QPointF,QPoint,Signal,QRect
from PySide6.QtGui import QColor,QPainter,QRadialGradient,QPen,QGuiApplication,QRegion
from PySide6.QtWidgets import QWidget

class DesktopVoiceOrb(QWidget):
    positionSaved=Signal(int,int)
    WIDTH=110;HEIGHT=110
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle('VICTOR.IA · Voz')
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint|Qt.WindowType.Tool|Qt.WindowType.WindowDoesNotAcceptFocus)
        for attribute in (Qt.WidgetAttribute.WA_TranslucentBackground,Qt.WidgetAttribute.WA_ShowWithoutActivating):self.setAttribute(attribute)
        self.drag_offset=None;self.saved_position=None
        self.resize(self.WIDTH,self.HEIGHT)
        self.setMask(QRegion(QRect(3,3,self.WIDTH-6,self.HEIGHT-6),QRegion.RegionType.Ellipse))
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setToolTip('Mantén pulsado y arrastra para mover')
        self.state='Listo';self.mic_target=self.mic_level=self.tts_target=self.tts_level=0.
        self.corner='bottom-right';self.render_timer=QTimer(self);self.render_timer.setInterval(40);self.render_timer.timeout.connect(self.tick)
        self.reposition();QGuiApplication.instance().screenAdded.connect(self._screen_changed)
        QGuiApplication.instance().screenRemoved.connect(self._screen_changed)
        if QGuiApplication.primaryScreen():QGuiApplication.primaryScreen().availableGeometryChanged.connect(self._screen_changed)
    def _screen_changed(self,*args):self.reposition()
    def reposition(self,corner=None):
        if corner and corner!=self.corner:self.corner=corner;self.saved_position=None
        if self.saved_position is not None:
            self.move(self._clamp(QPoint(*self.saved_position)));return
        screen=QGuiApplication.primaryScreen()
        if not screen:return
        box=screen.availableGeometry();margin=18
        x=box.left()+margin if self.corner.endswith('left') else box.right()-self.width()-margin+1
        y=box.top()+margin if self.corner.startswith('top') else box.bottom()-self.height()-margin+1
        self.move(max(box.left(),x),max(box.top(),y))
    def _clamp(self,position):
        screen=QGuiApplication.screenAt(position+QPoint(self.width()//2,self.height()//2)) or QGuiApplication.primaryScreen()
        if not screen:return position
        box=screen.availableGeometry()
        return QPoint(max(box.left(),min(position.x(),box.right()-self.width()+1)),max(box.top(),min(position.y(),box.bottom()-self.height()+1)))
    def restore_position(self,position):
        self.saved_position=tuple(position) if isinstance(position,(list,tuple)) and len(position)==2 else None
        self.reposition()
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            self.drag_offset=event.globalPosition().toPoint()-self.pos();self.setCursor(Qt.CursorShape.ClosedHandCursor);event.accept()
    def mouseMoveEvent(self,event):
        if self.drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(self._clamp(event.globalPosition().toPoint()-self.drag_offset));event.accept()
    def mouseReleaseEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and self.drag_offset is not None:
            self.drag_offset=None;self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.saved_position=(self.x(),self.y());self.positionSaved.emit(*self.saved_position);event.accept()
    def showEvent(self,event):
        super().showEvent(event);self.reposition();self.update();self._wake()
    def hideEvent(self,event):super().hideEvent(event);self.render_timer.stop()
    def reset(self):
        self.mic_target=self.mic_level=self.tts_target=self.tts_level=0.;self.render_timer.stop();self.update()
    def set_user_level(self,level):self.mic_target=self._level(level);self._wake()
    def set_bot_level(self,level):self.tts_target=self._level(level);self._wake()
    @staticmethod
    def _level(level):
        try:return max(0.,min(1.,float(level))) if math.isfinite(float(level)) else 0.
        except (ValueError,TypeError):return 0.
    def _wake(self):
        if self.isVisible() and max(self.mic_target,self.tts_target,self.mic_level,self.tts_level)>.005:self.render_timer.start()
    def set_state(self,state):self.state=state;self.update()
    def tick(self):
        self.mic_level+=(self.mic_target-self.mic_level)*.4;self.tts_level+=(self.tts_target-self.tts_level)*.4
        if max(self.mic_level,self.tts_level,self.mic_target,self.tts_target)<.005:
            self.mic_level=self.tts_level=0.;self.render_timer.stop()
        self.update()
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        level=max(self.mic_level,self.tts_level);color=QColor('#B39AFF' if self.tts_level>self.mic_level else '#83AFFF')
        center=QPointF(self.width()/2,self.height()/2);radius=22+level*10
        glow=QRadialGradient(center,radius*1.5);a=QColor(color);a.setAlpha(35+int(level*95));glow.setColorAt(0,a);glow.setColorAt(1,QColor(0,0,0,0))
        painter.setPen(Qt.PenStyle.NoPen);painter.setBrush(glow);painter.drawEllipse(center,radius*1.5,radius*1.5)
        core=QRadialGradient(center-QPointF(8,9),radius*1.5);core.setColorAt(0,QColor('#D5DAFF'));core.setColorAt(.35,color);core.setColorAt(1,QColor('#172038'))
        painter.setBrush(core);painter.setPen(QPen(QColor(180,195,255,140),1));painter.drawEllipse(center,radius,radius)
        if level>.02:
            painter.setBrush(Qt.BrushStyle.NoBrush);painter.setPen(QPen(color,1.2));painter.drawEllipse(center,radius+4+level*5,radius+4+level*5)
        painter.end()
