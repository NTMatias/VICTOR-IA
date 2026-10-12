"""Native Windows text metrics and antialiasing without changing OS settings."""
from PySide6.QtGui import QFont,QFontDatabase
from PySide6.QtWidgets import QApplication


def family():
    available=set(QFontDatabase.families())
    return next((name for name in ('Segoe UI','Noto Sans','Arial') if name in available),'Sans Serif')


def ui_font(size=14,bold=False):
    font=QFont(family());font.setPixelSize(size)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality)
    font.setHintingPreference(QFont.HintingPreference.PreferVerticalHinting)
    font.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
    return font


def install():
    app=QApplication.instance()
    if app:app.setFont(ui_font())
