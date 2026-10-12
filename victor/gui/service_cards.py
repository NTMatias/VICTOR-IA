"""Listas de servicios: texto legible, logos locales y enlaces sin datos técnicos."""
from datetime import datetime
from email.utils import parsedate_to_datetime, parseaddr
from html import unescape
from PySide6.QtCore import Qt, QSize, QUrl
from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy, QStyledItemDelegate, QStyleOptionViewItem, QStyle
from victor.gui.widgets import brand_icon


def friendly_date(value, all_day=False):
    if not value:
        return 'Fecha no disponible'
    try:
        day = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        try:
            day = parsedate_to_datetime(str(value))
        except (ValueError, TypeError):
            return 'Fecha no disponible'
    if day.tzinfo and not all_day:
        day = day.astimezone()
    months = ('ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic')
    weekdays = ('Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom')
    date = f'{weekdays[day.weekday()]} {day.day} {months[day.month-1]} {day.year}'
    return date + (' · Todo el día' if all_day or len(str(value)) == 10 else day.strftime(' · %H:%M'))


def sender(value):
    name, address = parseaddr(value or '')
    return name or address or 'Remitente desconocido', address


def file_type(mime):
    if mime == 'application/vnd.google-apps.folder': return 'Carpeta'
    if mime.startswith('video/'): return 'Vídeo'
    if mime.startswith('image/'): return 'Imagen'
    if mime.startswith('audio/'): return 'Audio'
    return {'application/pdf': 'PDF', 'application/vnd.google-apps.document': 'Documento',
            'application/vnd.google-apps.spreadsheet': 'Hoja de cálculo',
            'application/vnd.google-apps.presentation': 'Presentación'}.get(mime, 'Archivo')


class StatusText(QLabel):
    """Estado corto compatible con el canal de resultados de las secciones."""
    def __init__(self, text=''):
        super().__init__(text)
        self.setObjectName('secondary'); self.setWordWrap(True)
        self.setTextFormat(Qt.TextFormat.PlainText)
    def setPlainText(self, text): self.setText(str(text))
    def toPlainText(self): return self.text()


class ElidedLabel(QLabel):
    """Una línea con elipsis visual, tooltip completo y sin ensanchar la ventana."""
    def __init__(self, text):
        super().__init__(text); self.full_text = text
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setText(self.fontMetrics().elidedText(self.full_text, Qt.TextElideMode.ElideRight, self.contentsRect().width()))


class CoverArt(QWidget):
    """Conserva la imagen original para HiDPI, sin imponer 240 px en pantallas pequeñas."""
    def __init__(self):
        super().__init__();self.image=QPixmap();self.setMinimumSize(80,80);self.setMaximumSize(240,240)
        policy=QSizePolicy(QSizePolicy.Policy.Preferred,QSizePolicy.Policy.Preferred)
        policy.setHeightForWidth(True);self.setSizePolicy(policy)
        self.setAccessibleName('Carátula del álbum')
    def sizeHint(self):return QSize(240,240)
    def minimumSizeHint(self):return QSize(80,80)
    def hasHeightForWidth(self):return True
    def heightForWidth(self,width):return min(width,240)
    def setPixmap(self,image):self.image=image;self.update()
    def clear(self):self.image=QPixmap();self.update()
    def paintEvent(self,event):
        painter=QPainter(self);painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if not self.image.isNull():
            size=self.image.size();size.scale(self.size(),Qt.AspectRatioMode.KeepAspectRatio)
            from PySide6.QtCore import QRect
            painter.drawPixmap(QRect((self.width()-size.width())//2,0,size.width(),size.height()),self.image)


class CardDelegate(QStyledItemDelegate):
    """Pinta la selección; el contenido pertenece al widget de la tarjeta."""
    def paint(self, painter, option, index):
        copy=QStyleOptionViewItem(option);self.initStyleOption(copy,index);copy.text=''
        copy.widget.style().drawControl(QStyle.ControlElement.CE_ItemViewItem,copy,painter,copy.widget)


class ServiceList(QListWidget):
    """Filas con tres niveles tipográficos. El QListWidget conserva selección y enlaces."""
    def __init__(self, brand):
        super().__init__(); self.brand = brand
        self.setItemDelegate(CardDelegate(self))
        self.setMinimumHeight(230); self.setMinimumWidth(0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet('QListWidget::item {padding:0; margin:3px 0; border-radius:10px;}')
    def add_card(self, title, subtitle='', detail='', url=None, identifier=None):
        text = '\n'.join(str(x) for x in (title, subtitle, detail) if x)
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, url)
        item.setData(Qt.ItemDataRole.UserRole+1, identifier)
        item.setToolTip(text + ('\nDoble clic para abrir' if url else ''))
        item.setSizeHint(QSize(0, 106 if detail else 84)); self.addItem(item)
        row = QWidget(); row.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        box = QHBoxLayout(row); box.setContentsMargins(14,12,14,12); box.setSpacing(14)
        logo = QLabel(); logo.setPixmap(brand_icon(self.brand, size=32).pixmap(32,32))
        logo.setFixedSize(36,36); box.addWidget(logo, alignment=Qt.AlignmentFlag.AlignTop)
        lines = QVBoxLayout(); lines.setSpacing(5)
        for index, value in enumerate((title, subtitle, detail)):
            if not value: continue
            line = ElidedLabel(unescape(str(value)).replace('\n',' ')); line.setTextFormat(Qt.TextFormat.PlainText)
            line.setObjectName('cardTitle' if index == 0 else 'secondary')
            line.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            line.setMinimumWidth(0); line.setToolTip(line.text()); lines.addWidget(line)
        box.addLayout(lines, 1); self.setItemWidget(item, row)
        return item

