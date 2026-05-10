"""
apps/document_converter/ui/ui_theme.py
────────────────────────────────────────
Thin shim that reads current styles from the global ThemeManager.
All constants are kept as module-level aliases so existing imports work unchanged.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QWidget
from core.theme_manager import ThemeManager

RADIUS_LG = 18
RADIUS_MD = 12
RADIUS_SM = 10


def _tm():
    return ThemeManager.instance()


def apply_window_theme(widget: QWidget) -> None:
    widget.setStyleSheet(_tm().app_styles()["window"])


def make_card_container() -> tuple:
    card = QFrame()
    card.setObjectName("mainCard")
    card.setStyleSheet(_tm().app_styles()["card"])
    layout = QVBoxLayout(card)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(14)
    return card, layout


def _s(key: str) -> str:
    return _tm().app_styles()[key]


APP_COLORS = _tm().app_colors()


def get_button_style()        -> str: return _s("button")
def get_soft_button_style()   -> str: return _s("soft_button")
def get_remove_button_style() -> str: return _s("remove_button")
def get_convert_button_style()-> str: return _s("convert_button")
def get_ffmpeg_button_style() -> str: return _s("ffmpeg_button")
def get_combo_style()         -> str: return _s("combo")
def get_drop_label_style()    -> str: return _s("drop_label")
def get_app_colors()          -> dict: return _tm().app_colors()
def get_doc_btn_style()       -> str: return _s("doc_btn")


BUTTON_STYLE        = get_button_style()
SOFT_BUTTON_STYLE   = get_soft_button_style()
REMOVE_BUTTON_STYLE = get_remove_button_style()
CONVERT_BUTTON_STYLE= get_convert_button_style()
FFMPEG_BUTTON_STYLE = get_ffmpeg_button_style()
COMBO_STYLE         = get_combo_style()
DROP_LABEL_STYLE    = get_drop_label_style()
