"""Tokens visuales compartidos por toda la interfaz Qt."""
COLORS = {"background": "#0d111c", "surface": "#171e2e", "border": "#29344a", "text": "#edf2ff",
          "muted": "#9ba9c3", "accent": "#397bfa", "assistant": "#222b3b", "success": "#5fdfbf"}
STYLE = '''
QMainWindow, QWidget#root { background: #0d111c; color: #edf2ff; }
QWidget { color: #edf2ff; font-family: 'Segoe UI Variable', 'Segoe UI'; font-size: 13px; }
QLabel { background: transparent; }
QFrame#card, QFrame#drawer { background: #171e2e; border: 1px solid #29344a; border-radius: 16px; }
QPushButton { background: #222c40; border: 1px solid #303c55; border-radius: 12px; padding: 10px 13px; }
QPushButton:hover { background: #2b3b58; }
QPushButton:disabled { color: #6d7990; }
QPushButton#primary { background: #397bfa; border: 0; }
QPushButton#mic { border-radius: 26px; background: #397bfa; font-size: 22px; }
QLineEdit, QPlainTextEdit, QListWidget { background: #101725; border: 1px solid #303c55; border-radius: 9px; padding: 7px; }
QComboBox { background: #222c40; border-radius: 7px; padding: 7px; }
QComboBox QAbstractItemView { background: #171e2e; selection-background-color: #397bfa; }
QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: 0; }
QScrollBar:vertical { background: #111827; width: 7px; border-radius: 3px; }
QScrollBar::handle:vertical { background: #39465f; border-radius: 3px; min-height: 25px; }
QTabWidget::pane { border: 0; } QTabBar::tab { background: #171e2e; padding: 8px; }
QTabBar::tab:selected { color: #76a8ff; border-bottom: 2px solid #397bfa; }
QDialog, QMessageBox { background: #171e2e; }
QToolTip { background: #222c40; color: white; }
'''
