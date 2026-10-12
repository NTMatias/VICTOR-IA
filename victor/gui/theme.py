"""Tokens visuales compartidos por toda la interfaz Qt."""
COLORS = {"background": "#0d111c", "surface": "#171e2e", "border": "#29344a", "text": "#edf2ff",
          "muted": "#9ba9c3", "accent": "#397bfa", "assistant": "#222b3b", "success": "#5fdfbf"}
LABEL_STYLES = {"muted": "color: #9ba9c3;", "heading": "font-size: 26px; font-weight: 600;",
                "caption": "font-size: 10px; color: #9ba9c3;", "metric": "font-size: 18px; font-weight: 600;",
                "error": "color: #f2b7a9; font-size: 11px;"}

def state_style(state):
    color = {"Listo": COLORS["success"], "Escuchando": COLORS["accent"], "Pensando": "#e9bd69"}.get(state, COLORS["muted"])
    return LABEL_STYLES["metric"] + "color: " + color + ";"

def bubble_style(role):
    return "QFrame {border: 0; border-radius: 16px; background: " + (COLORS["accent"] if role == "user" else COLORS["assistant"]) + ";}"

def theme_style(theme):
    return STYLE if theme != "Light" else STYLE.replace("#0d111c", "#e8edf6").replace("#171e2e", "#f3f6fd").replace("#edf2ff", "#182238")
STYLE = '''
QMainWindow, QWidget#root { background: #0d111c; color: #edf2ff; }
QWidget { color: #edf2ff; font-family: 'Segoe UI Variable', 'Segoe UI'; font-size: 13px; }
QLabel { background: transparent; }
QLabel#proactive { background: #171e2e; border: 1px solid #397bfa; border-radius: 12px; padding: 12px; }
QFrame#card, QFrame#drawer { background: #171e2e; border: 1px solid #29344a; border-radius: 16px; }
QFrame#approval { background: #292637; border: 1px solid #806a43; border-radius: 16px; padding: 8px; }
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
