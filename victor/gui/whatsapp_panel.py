"""Tarjeta de recientes de WhatsApp; sus mensajes no se incorporan al proveedor IA."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget,QFrame,QLabel,QPushButton,QVBoxLayout,QHBoxLayout,QSizePolicy
from victor.gui.theme import is_light
from victor.gui.widgets import icon
from victor.gui.service_cards import ElidedLabel


def plain(text='',kind=None):
    label=QLabel(text);label.setTextFormat(Qt.TextFormat.PlainText)
    if kind:label.setObjectName(kind)
    return label


def action(text,callback,primary=False):
    button=QPushButton(text);button.setObjectName('primary' if primary else 'normal');button.clicked.connect(callback);return button


def valid_rows(rows):
    if not isinstance(rows,list):return []
    result=[]
    for value in rows[:1000]:
        if not isinstance(value,dict) or not value.get('id') or not value.get('name'):continue
        count=value.get('unread',0)
        try:count=max(0,min(int(count),9999)) if isinstance(count,(int,float)) and not isinstance(count,bool) else 0
        except (ValueError,OverflowError):count=0
        result.append({key:str(value.get(key,'') or '')[:500] for key in ('id','name','preview','time')} | {'unread':count})
    return result



class WhatsAppRecent(QFrame):
    """Resumen de conversaciones; filas planas, avatar y contador independiente."""
    def __init__(self,app):
        super().__init__();self.app=app;self.setObjectName('card');self.rows=[];self.state='disconnected';self.signature=None
        layout=QVBoxLayout(self);layout.setContentsMargins(14,14,14,14);layout.setSpacing(7)
        header=QHBoxLayout();header.setSpacing(8)
        glyph=plain();glyph.setPixmap(icon('mail').pixmap(16,16));header.addWidget(glyph)
        header.addWidget(plain('WhatsApp','cardTitle'),1)
        show=action('Abrir →',lambda:app.navigate('whatsapp'));show.setObjectName('compact');header.addWidget(show);layout.addLayout(header)
        self.subtitle=plain('Mensajes recientes','secondary');layout.addWidget(self.subtitle)
        self.empty=plain('Conecta tu cuenta para ver tus conversaciones.','secondary');self.empty.setWordWrap(True);layout.addWidget(self.empty)
        self.items=QWidget();self.items_layout=QVBoxLayout(self.items);self.items_layout.setContentsMargins(0,0,0,0);self.items_layout.setSpacing(4);layout.addWidget(self.items)
        self.setMinimumWidth(0);self.apply_theme()

    def apply_theme(self):
        light=is_light(self.app.config.get('theme'))
        muted='#616B7D' if light else '#9196A5'
        self.setStyleSheet(
            'QPushButton#waRecentRow {background:transparent;border:0;padding:0;min-height:52px;text-align:left;border-radius:8px;}'
            'QPushButton#waRecentRow:hover {background:'+('#E1E7F1' if light else '#252A34')+';}'
            'QLabel#waInitials {background:'+('#DCE6F4' if light else '#283243')+';color:'+('#344F79' if light else '#A9C8FF')+';border-radius:16px;font-weight:600;}'
            'QLabel#waMessageTime {color:'+muted+';font-size:10px;}'
            'QLabel#waCount {background:#588AD8;color:white;border-radius:9px;font-size:10px;font-weight:600;}'
            'QFrame#waSeparator {background:'+('#D2D8E3' if light else '#30333E')+';border:0;}')

    def update_snapshot(self,snapshot):
        self.state=snapshot.get('state','disconnected')
        if self.state=='connected' and not snapshot.get('contact_mode'):self.rows=valid_rows(snapshot.get('chats',[]))[:2]
        elif self.state in ('qr','disconnected'):self.rows=[]
        signature=(self.state,repr(self.rows))
        if signature==self.signature:return
        self.signature=signature
        while self.items_layout.count():
            widget=self.items_layout.takeAt(0).widget()
            if widget:widget.hide();widget.deleteLater()
        self.empty.setVisible(not self.rows);self.items.setVisible(bool(self.rows))
        self.setMinimumHeight(200 if self.rows else 125)
        self.empty.setText('Aún no hay conversaciones recientes.' if self.state=='connected' else 'Sincronizando tus conversaciones…' if self.state=='loading' else 'Conecta tu cuenta para ver tus conversaciones.')
        for i,row in enumerate(self.rows):
            if i:
                divider=QFrame();divider.setObjectName('waSeparator');divider.setFixedHeight(1);self.items_layout.addWidget(divider)
            button=QPushButton();button.setObjectName('waRecentRow');button.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Fixed)
            button.setEnabled(self.state=='connected');button.setToolTip(row['name']+'\n'+row['preview'])
            button.setAccessibleName(row['name']+', '+str(row['unread'])+' mensajes sin leer. '+row['preview'])
            box=QHBoxLayout(button);box.setContentsMargins(3,6,3,6);box.setSpacing(9)
            initials=''.join(part[0] for part in row['name'].split()[:2]).upper()
            avatar=plain(initials,'waInitials');avatar.setFixedSize(32,32);avatar.setAlignment(Qt.AlignmentFlag.AlignCenter);box.addWidget(avatar)
            texts=QVBoxLayout();texts.setSpacing(4);heading=QHBoxLayout();heading.setSpacing(5)
            name=ElidedLabel(row['name']);name.setTextFormat(Qt.TextFormat.PlainText);name.setStyleSheet('font-weight:600;');heading.addWidget(name,1)
            if row['time']:heading.addWidget(plain(row['time'],'waMessageTime'))
            texts.addLayout(heading)
            lower=QHBoxLayout();lower.setSpacing(6);preview=ElidedLabel(row['preview'] or 'Abrir conversación');preview.setTextFormat(Qt.TextFormat.PlainText);preview.setObjectName('secondary');lower.addWidget(preview,1)
            if row['unread']:
                count=plain(str(row['unread']) if row['unread']<=99 else '99+','waCount');count.setFixedSize(22 if row['unread']>9 else 18,18);count.setAlignment(Qt.AlignmentFlag.AlignCenter);count.setToolTip(str(row['unread'])+' mensajes sin leer');lower.addWidget(count)
            texts.addLayout(lower);box.addLayout(texts,1)
            for label in button.findChildren(QLabel):label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            button.clicked.connect(lambda checked=False,identifier=row['id']:self.open(identifier));self.items_layout.addWidget(button)

    def open(self,identifier):
        self.app.navigate('whatsapp');self.app.sections.whatsapp_embed.open_chat(identifier)
