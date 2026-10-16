"""Diseño Grafito: colores y medidas del paquete visual del propietario."""
from pathlib import Path
COLORS = {"background": "#111318", "surface": "#1D2027", "border": "#30333E", "text": "#E9EAF1",
          "muted": "#9196A5", "accent": "#83AFFF", "assistant": "#22252E", "success": "#68CCA4"}
LABEL_STYLES = {"muted": "color: #9196A5;", "heading": "font-size: 29px; font-weight: 650;",
                "caption": "font-size: 11px; color: #9196A5;", "metric": "font-size: 21px; font-weight: 600;",
                "error": "color: #F28F95; font-size: 12px;"}
def load_fonts():
    from PySide6.QtGui import QFontDatabase
    for name in ("Inter.ttf", "IBMPlexMono.ttf"):
        QFontDatabase.addApplicationFont(str(Path(__file__).parent / "assets" / name))
def title_font():
    from victor.gui.typography import ui_font
    return ui_font(29,True)
def state_style(state):
    color = {"Listo": COLORS["success"], "Escuchando": COLORS["accent"], "Pensando": "#E9BE72",
             "Respondiendo": "#83AFFF", "Error": "#F28F95", "Desconectado": "#F28F95"}.get(state, COLORS["muted"])
    return "color: " + color + "; font-size: 12px;"
def bubble_style(role, light=False):
    start,end=(("#DBE8FB","#E9DFF5") if role=="user" else ("#FFFFFF","#F2F0FA")) if light else (("#30435F","#40314E") if role=="user" else ("#293043","#30283C"))
    background=f"qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {start},stop:1 {end})"
    return "QFrame {border: 1px solid "+("#D2D8E3" if light else "#4B4860")+"; border-radius: 16px; background: "+background+";} QLabel {border: 0; background: transparent; color: "+("#20242F" if light else "#E9EAF1")+";}"
def is_light(theme):
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtCore import Qt
    return theme == "Light" or (theme == "System" and QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Light)
def theme_style(theme):
    if not is_light(theme): return STYLE
    style = STYLE
    for old, new in {"#111318":"#EEF0F5", "#15171C":"#F6F7FA", "#16181E":"#F6F7FA", "#191C22":"#F8F9FC",
                     "#1D2027":"#FFFFFF", "#22252E":"#F2F4F8", "#252A34":"#E1E7F1", "#30333E":"#D2D8E3",
                     "#E9EAF1":"#20242F", "#9196A5":"#616B7D", "#B8BCC8":"#475266",
                     "#303745":"#D6E0EF"}.items(): style = style.replace(old, new)
    return style + LIGHT_GLASS
STYLE = r"""
QMainWindow, QWidget#outer { background: #111318; color: #E9EAF1; }
QWidget { color: #E9EAF1; font-family: 'Segoe UI', 'Inter', 'Noto Sans', Arial; font-size: 14px; }
QWidget#shell, QWidget#root, QWidget#pageBody { background: #15171C; }
QFrame#sidebar { background: #15171C; border: 1px solid #30333E; border-top-left-radius: 16px; border-bottom-left-radius: 16px; }
QFrame#header { background: #191C22; border-bottom: 1px solid #30333E; border-top-right-radius: 16px; }
QFrame#card, QFrame#player, QFrame#chatFrame { background: #1D2027; border: 1px solid #30333E; border-radius: 12px; }
QFrame#approval { background: #22252E; border: 1px solid #776342; border-radius: 12px; }
QFrame#composer { background: #22252E; border: 1px solid #30333E; border-radius: 12px; }
QLabel { background: transparent; border: 0; }
QLabel#secondary, QLabel#caption { color: #9196A5; }
QLabel#sectionTitle { font-size: 29px; font-weight: 650; }
QLabel#cardTitle { font-size: 14px; font-weight: 600; }
QLabel#badge { color: #68CCA4; background: #21372F; border: 1px solid #315746; padding: 5px 10px; border-radius: 12px; font-size: 11px; }
QLabel#proactive { color: #9196A5; }
QPushButton { background: #22252E; border: 1px solid #30333E; border-radius: 8px; padding: 9px 14px; min-height: 16px; }
QPushButton:hover { background: #252A34; border-color: #627899; }
QPushButton:pressed, QPushButton:checked { background: #303745; border-color: #83AFFF; }
QPushButton:disabled { color: #686D7A; }
QPushButton#primary { background: #588AD8; border: 1px solid #749DE1; color: white; }
QPushButton#danger { color: #F28F95; background: #35262B; border-color: #70434C; }
QPushButton#nav { text-align: left; border: 0; background: transparent; border-radius: 9px; padding: 13px 16px; color: #B8BCC8; }
QPushButton#nav:checked { background: #252A34; color: #E9EAF1; border-left: 2px solid #83AFFF; }
QPushButton#nav:hover { background: #22252E; }
QPushButton#compact { padding: 4px 7px; }
QPushButton#orbBtn { background: #1D2330; border: 1px solid #3A4C6B; border-radius: 8px; padding: 6px 12px; color: #83AFFF; }
QPushButton#orbBtn:hover { background: #252F42; border-color: #83AFFF; }
QPushButton#orbBtn:checked { background: #283750; border-color: #68CCA4; color: #68CCA4; }
QPushButton#lockBtn { background: transparent; border: 1px solid #30333E; border-radius: 8px; padding: 6px 10px; color: #9196A5; }
QPushButton#lockBtn:hover { background: #22252E; border-color: #F28F95; color: #F28F95; }
QPushButton#mic { border-radius: 8px; }
QPushButton#voiceMic { background: #252A34; border: 1px solid #30333E; border-radius: 60px; }
QLineEdit, QPlainTextEdit, QListWidget, QSpinBox, QDoubleSpinBox { background: #16181E; border: 1px solid #30333E; border-radius: 8px; padding: 8px 11px; selection-background-color: #588AD8; }
QLineEdit { min-height: 18px; }
QComboBox { background: #16181E; border: 1px solid #30333E; border-radius: 8px; padding: 8px 11px; min-height: 18px; }
QComboBox QAbstractItemView { background: #1D2027; color: #E9EAF1; selection-background-color: #303745; }
QComboBox::drop-down { border: 0; width: 25px; }
QListWidget::item { padding: 15px; border-bottom: 1px solid #30333E; border-radius: 8px; }
QListWidget::item:selected { background: #283243; border: 1px solid #455876; }
QCheckBox { spacing: 10px; padding: 4px 0; }
QCheckBox::indicator { width: 28px; height: 16px; border-radius: 8px; background: #464B57; }
QCheckBox::indicator:checked { background: #588AD8; border: 3px solid #83AFFF; }
QSlider::groove:horizontal { height: 4px; background: #373C48; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #83AFFF; border-radius: 2px; }
QSlider::handle:horizontal { background: #C4DCFF; border: 3px solid #588AD8; width: 14px; height: 14px; margin: -7px 0; border-radius: 9px; }
QProgressBar { border: 0; border-radius: 3px; background: #30333E; text-align: center; }
QProgressBar::chunk { background: #83AFFF; border-radius: 3px; }
QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: 0; }
QScrollBar:vertical { width: 6px; background: transparent; }
QScrollBar::handle:vertical { background: #464B57; border-radius: 3px; min-height: 28px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QTabWidget::pane { border: 0; }
QTabBar::tab { background: #191C22; color: #9196A5; padding: 9px 15px; margin-right: 1px; border-radius: 6px; }
QTabBar::tab:selected { background: #303745; color: #E9EAF1; }
QDialog, QMessageBox { background: #1D2027; }
QToolTip { background: #22252E; color: #E9EAF1; border: 1px solid #30333E; padding: 5px; }
"""

# Translucent layers retain readable text: opacity belongs to backgrounds only.
GLASS = r"""
QMainWindow { background: transparent; }
QWidget#outer { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(48,36,66,238),stop:0.5 rgba(22,29,45,242),stop:1 rgba(37,32,58,238)); border-radius:20px; }
QWidget#shell, QWidget#root, QWidget#pageBody { background: transparent; }
QFrame#sidebar { background:qlineargradient(x1:0,y1:0,x2:0.8,y2:1,stop:0 rgba(55,45,76,190),stop:1 rgba(22,31,48,210)); border-color:rgba(169,167,220,48); }
QFrame#header { background:rgba(48,43,65,145); border-color:rgba(169,167,220,42); }
QFrame#card, QFrame#chatFrame, QFrame#composer { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(57,59,83,170),stop:1 rgba(37,35,56,190)); border:1px solid rgba(171,172,222,48); border-radius:18px; }
QPushButton { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(78,77,108,160),stop:1 rgba(48,52,77,180)); border-color:rgba(171,172,222,55); border-radius:11px; }
QPushButton:hover { background:rgba(107,99,153,175); border-color:#9DAFF5; }
QPushButton#primary { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #698FDC,stop:1 #9273CE); border-color:#A4A2EE; }
QPushButton#nav { background:transparent; }
QPushButton#nav:checked { background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 rgba(105,143,220,110),stop:1 rgba(146,115,206,65)); border-left:2px solid #A4A2EE; }
QLineEdit, QPlainTextEdit, QListWidget, QSpinBox, QDoubleSpinBox, QComboBox { background:rgba(19,24,39,155); border-color:rgba(171,172,222,48); border-radius:11px; }
QFrame#player, QFrame#spotifyHero { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(89,48,99,230),stop:0.45 rgba(43,33,60,237),stop:1 rgba(19,24,39,242)); border:1px solid rgba(182,139,215,85); border-radius:20px; }
QFrame#player QLabel#songTitle, QFrame#spotifyHero QLabel#songTitle { font-size:22px; font-weight:700; color:#F4F2FF; }
QFrame#player QLabel#nowBadge, QFrame#spotifyHero QLabel#nowBadge { color:#69E2A2; font-size:10px; font-weight:700; letter-spacing:1px; }
QFrame#player QLabel#cover { background:rgba(162,116,181,70); border-radius:13px; color:#DCC8FA; font-size:30px; }
QPushButton#musicPlay { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #39DC88,stop:1 #109E62); border:1px solid #69E2A2; border-radius:23px; padding:0; min-width:44px; max-width:44px; min-height:44px; max-height:44px; }
QPushButton#musicPlay:hover { background:#48E598; }
QPushButton#musicTransport { background:transparent; border:0; padding:0; min-height:0; }
QPushButton#musicTransport:hover { background:rgba(184,164,221,45); }
QFrame#player QSlider::sub-page:horizontal, QFrame#spotifyHero QSlider::sub-page:horizontal { background:#3DCD87; }
QFrame#player QSlider::handle:horizontal, QFrame#spotifyHero QSlider::handle:horizontal { background:#F0FFF6; border:2px solid #8DEAB7; width:11px; height:11px; margin:-5px 0; border-radius:7px; }
QDialog, QMessageBox { background:#29283B; }
"""
LIGHT_GLASS = r"""
QMainWindow { background:transparent; }
QWidget#outer { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(238,226,250,245),stop:0.5 rgba(230,240,252,245),stop:1 rgba(243,232,246,245)); }
QFrame#sidebar, QFrame#header { background:rgba(255,255,255,150); border-color:#D5CCE6; }
QFrame#card, QFrame#chatFrame, QFrame#composer { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 rgba(255,255,255,205),stop:1 rgba(243,238,251,205)); border-color:#D5CCE6; }
QPushButton { background:rgba(255,255,255,165); border-color:#D5CCE6; }
QPushButton:hover { background:#E8DFF6; }
QPushButton#primary { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #5C83C8,stop:1 #8862BA); color:white; }
QPushButton#nav:checked { background:#E2DCF4; }
QLineEdit, QPlainTextEdit, QListWidget, QSpinBox, QDoubleSpinBox, QComboBox { background:rgba(255,255,255,180); border-color:#D5CCE6; }
QFrame#player, QFrame#spotifyHero { background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #EEE0F5,stop:0.5 #F4F0FC,stop:1 #E3EEF9); border-color:#C9B8DE; }
QFrame#player QLabel#songTitle, QFrame#spotifyHero QLabel#songTitle { color:#272236; }
QFrame#player QLabel#nowBadge, QFrame#spotifyHero QLabel#nowBadge { color:#147546; }
QFrame#player QLabel#cover { background:#DDD0ED; color:#755096; }
QPushButton#musicPlay { background:#2DCB7B; border-color:#159F5B; }
QPushButton#musicTransport { background:transparent; border:0; }
QDialog, QMessageBox { background:#F5F0FB; }
"""
STYLE += GLASS
