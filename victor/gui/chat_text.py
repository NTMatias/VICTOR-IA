"""Markdown de respuestas en Qt, con enlaces seguros y fuentes sin duplicados."""
import html
import re
from urllib.parse import urlsplit
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont, QTextDocument
from PySide6.QtWidgets import QLabel


def web_link(url):
    try:
        parts=urlsplit(url)
        return parts.scheme.lower() in ('https','http') and bool(parts.hostname) and not parts.username
    except ValueError:
        return False


def prepare_markdown(text):
    text=str(text)
    # El núcleo añade enlaces verificados al final. No repetir los que el modelo
    # ya enlazó, ni mostrar largas URLs crudas como un segundo bloque de fuentes.
    marker='\n\nFuentes consultadas:\n'
    if marker in text:
        body,tail=text.rsplit(marker,1)
        lines=tail.splitlines();urls=[];remaining=[]
        for line in lines:
            url=line.strip()
            if web_link(url) and ' ' not in url:
                if url not in body and url not in urls:urls.append(url)
            else:remaining.append(line)
        links=['['+urlsplit(url).hostname.removeprefix('www.')+']('+url+')' for url in urls]
        text=body+('\n\n**Fuentes:** '+ ' · '.join(links) if links else '')
        if any(line.strip() for line in remaining):text+='\n\n'+'\n'.join(remaining).strip()
    # Imágenes permanecen como texto: nunca cargar recursos remotos/locales
    # indicados por el modelo dentro del documento del chat.
    return re.sub(r'!\[([^\]]*)\]\([^\n)]*\)',lambda m:'[Imagen: '+m[1]+']',text)


class ChatDocument(QTextDocument):
    def loadResource(self,kind,url):return None


def markdown_html(text, light=False):
    doc=ChatDocument()
    from victor.gui.typography import ui_font,family
    font=ui_font(15);doc.setDefaultFont(font)
    doc.setMarkdown(prepare_markdown(text),QTextDocument.MarkdownFeature.MarkdownDialectGitHub | QTextDocument.MarkdownFeature.MarkdownNoHTML)
    rendered=doc.toHtml()
    color='#20242F' if light else '#E9EAF1'
    border='#D2D8E3' if light else '#3A4050'
    shade='#E8ECF3' if light else '#1D2027'
    accent='#3569B2' if light else '#A9C8FF'
    rendered=re.sub(r'<body[^>]*>',f'<body style="font-family:{family()}; font-size:15px; color:{color};">',rendered)
    def block_spacing(match):
        tag, before, styles, after = match.groups()
        styles=re.sub(r'(?:margin-top|margin-bottom|line-height):[^;]+;', '',styles)
        spacing='line-height:150%; margin-top:10px; margin-bottom:10px;'
        if tag=='li':spacing='line-height:150%; margin-top:5px; margin-bottom:5px;'
        elif tag.startswith('h'):spacing='margin-top:18px; margin-bottom:10px;'
        return '<'+tag+before+'style="'+styles+spacing+'"'+after+'>'
    rendered=re.sub(r'<(p|li|h[1-6])(\b[^>]*?)style="([^"]*)"([^>]*)>',block_spacing,rendered)
    rendered=re.sub(r'<table[^>]*>',f'<table width="100%" border="1" cellspacing="0" cellpadding="7" style="border-collapse:collapse; border-color:{border};">',rendered)
    rendered=re.sub(r'(<(?:td|th)[^>]*style=")',r'\1border-color:'+border+'; ',rendered)
    rendered=re.sub(r'(<pre[^>]*style=")',r'\1background-color:'+shade+'; padding:10px; ',rendered)
    rendered=re.sub(r'<img\b[^>]*>', '[Imagen]',rendered)
    def safe_anchor(match):
        url=html.unescape(match[1])
        if web_link(url):return '<a href="'+html.escape(url,quote=True)+'" style="color:'+accent+';">'+match[2]+'</a>'
        return '<span>'+match[2]+'</span>'
    rendered=re.sub(r'<a href="([^"]*)"[^>]*>(.*?)</a>',safe_anchor,rendered,flags=re.S)
    return rendered


class MarkdownLabel(QLabel):
    """QLabel conserva selección y ajuste de altura; text() devuelve el original."""
    def __init__(self,text='',parent=None):
        super().__init__(parent);self.raw='';self.light=False
        self.setWordWrap(True);self.setTextFormat(Qt.TextFormat.RichText)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard | Qt.TextInteractionFlag.LinksAccessibleByMouse)
        self.setOpenExternalLinks(False);self.linkActivated.connect(self.open_link)
        self.setText(text)
    def setText(self,text):
        self.raw=str(text);super().setText(markdown_html(self.raw,self.light))
        self.updateGeometry()
    def text(self):return self.raw
    def clear(self):self.setText('')
    def apply_theme(self,light):self.light=light;self.setText(self.raw)
    def open_link(self,url):
        if web_link(url):QDesktopServices.openUrl(QUrl(url))
