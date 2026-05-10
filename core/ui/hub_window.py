import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QPixmap, QIcon, QColor
from PyQt6.QtCore import Qt, QSize
from core.theme_manager import ThemeManager


def get_asset_path(filename):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_dir, "assets", "hub", filename)


# ─────────────────────────────────────────────────────────────────────
#  AppCard
# ─────────────────────────────────────────────────────────────────────
class AppCard(QFrame):
    def __init__(self, title, subtitle, icon_file, btn_text,
                 btn_type="install", is_disabled=False, parent=None):
        super().__init__(parent)
        self.btn_type = btn_type
        self._is_disabled = is_disabled

        if is_disabled:
            self.setObjectName("appCardDisabled")
        else:
            self.setObjectName("appCard")
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(15)
            shadow.setXOffset(0)
            shadow.setYOffset(4)
            shadow.setColor(QColor(0, 0, 0, 80))
            self.setGraphicsEffect(shadow)

        self.setFixedHeight(180)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Icon
        self._icon_label = QLabel()
        pixmap = QPixmap(get_asset_path(icon_file))
        if not pixmap.isNull():
            self._icon_label.setPixmap(
                pixmap.scaled(100, 100,
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
            )
        self._icon_label.setFixedSize(100, 100)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._icon_label)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(5)

        self._title_label = QLabel(title)
        self._title_label.setWordWrap(True)

        self._subtitle_label = QLabel(subtitle)
        self._subtitle_label.setWordWrap(True)

        content_layout.addWidget(self._title_label)
        content_layout.addWidget(self._subtitle_label)
        content_layout.addStretch()

        action_layout = QHBoxLayout()
        self.action_btn = QPushButton(btn_text)
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if btn_type == "install":
            self.action_btn.setIcon(
                self.style().standardIcon(self.style().StandardPixmap.SP_ArrowDown))
        elif btn_type == "open":
            self.action_btn.setIcon(
                self.style().standardIcon(self.style().StandardPixmap.SP_DialogApplyButton))
        else:
            self.action_btn.setEnabled(False)

        action_layout.addWidget(self.action_btn)
        action_layout.addStretch()

        if btn_type != "disabled":
            self._portable_label = QLabel("🔗 PORTABLE")
            action_layout.addWidget(self._portable_label)
        else:
            self._portable_label = None

        content_layout.addLayout(action_layout)
        main_layout.addLayout(content_layout)

    def apply_styles(self, styles: dict):
        if self._is_disabled:
            self.setStyleSheet(styles["card_disabled"])
        else:
            self.setStyleSheet(styles["card_normal"])
        self._title_label.setStyleSheet(styles["card_title"])
        self._subtitle_label.setStyleSheet(styles["card_subtitle"])
        if self._portable_label:
            self._portable_label.setStyleSheet(styles["portable"])
        if self.btn_type == "install":
            self.action_btn.setStyleSheet(styles["btn_install"])
        elif self.btn_type == "open":
            self.action_btn.setStyleSheet(styles["btn_open"])
        else:
            self.action_btn.setStyleSheet(styles["btn_disabled"])


# ─────────────────────────────────────────────────────────────────────
#  HubWindow
# ─────────────────────────────────────────────────────────────────────
class HubWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Hub")
        self.resize(900, 600)
        self._tm = ThemeManager.instance()
        self.init_ui()
        self._apply_theme()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 40)
        main_layout.setSpacing(20)

        # Header: title + toggle button
        header_layout = QHBoxLayout()
        self.title_label = QLabel("MEDIA HUB")
        self.title_label.setObjectName("hubTitle")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.toggle_btn = QPushButton()
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setFixedHeight(38)
        self.toggle_btn.clicked.connect(self._toggle_dark_mode)
        header_layout.addWidget(self.toggle_btn)

        main_layout.addLayout(header_layout)

        # Cards grid
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        self.media_card = AppCard(
            title="MULTIMEDIA\nCONVERTER",
            subtitle="Video, Audio, and Batch Processing",
            icon_file="media.png", btn_text=" ABRIR", btn_type="open"
        )
        self.media_card.action_btn.clicked.connect(self.launch_media_converter)
        grid_layout.addWidget(self.media_card, 0, 0)

        self.docs_card = AppCard(
            title="DOCUMENT\nCONVERTER",
            subtitle="PDF, Word, Excel, and OCR",
            icon_file="docs.png", btn_text=" ABRIR", btn_type="open"
        )
        self.docs_card.action_btn.clicked.connect(self.launch_document_converter)
        grid_layout.addWidget(self.docs_card, 0, 1)

        self.quality_card = AppCard(
            title="QUALITY\nENHANCER",
            subtitle="AI Image Super Resolution",
            icon_file="quality.webp", btn_text=" ABRIR", btn_type="open"
        )
        self.quality_card.action_btn.clicked.connect(self.launch_quality_enhancer)
        grid_layout.addWidget(self.quality_card, 1, 0)

        self.bg_card = AppCard(
            title="BACKGROUND\nERASER",
            subtitle="AI-Powered Background Removal",
            icon_file="backgrounderaser.webp", btn_text=" ABRIR", btn_type="open"
        )
        self.bg_card.action_btn.clicked.connect(self.launch_bg_remover)
        grid_layout.addWidget(self.bg_card, 1, 1)

        self.link_card = AppCard(
            title="LINK\nCONVERTER",
            subtitle="YouTube, TikTok, Instagram & more",
            icon_file="link_converter.webp", btn_text=" ABRIR", btn_type="open"
        )
        self.link_card.action_btn.clicked.connect(self.launch_link_converter)
        grid_layout.addWidget(self.link_card, 2, 0)

        main_layout.addLayout(grid_layout)

        self._all_cards = [
            self.media_card, self.docs_card, self.quality_card,
            self.bg_card, self.link_card
        ]

    # ── Theme ─────────────────────────────────────────────────────────────────
    def _toggle_dark_mode(self):
        self._tm.toggle()
        self._apply_theme()

    def _apply_theme(self):
        styles = self._tm.hub_styles()
        self.setStyleSheet(styles["window"])
        self.title_label.setStyleSheet(styles["title"])
        self.toggle_btn.setStyleSheet(styles["toggle_btn"])
        self.toggle_btn.setText("☀️  Modo Claro" if self._tm.is_dark else "🌙  Modo Oscuro")
        for card in self._all_cards:
            card.apply_styles(styles)

    # ── Launchers ─────────────────────────────────────────────────────────────
    def launch_media_converter(self):
        from apps.media_converter.ui.index import LauncherWindow
        self.media_window = LauncherWindow()
        self.media_window.show()
        self.close()

    def launch_document_converter(self):
        from apps.document_converter.ui.index import DocumentLauncherWindow
        self.doc_window = DocumentLauncherWindow()
        self.doc_window.show()
        self.close()

    def launch_quality_enhancer(self):
        from apps.media_converter.ui.quality_enhancer import QualityEnhancerUI
        self.quality_window = QualityEnhancerUI()
        self.quality_window.show()
        self.close()

    def launch_link_converter(self):
        from apps.link_converter.link_converter_window import LinkConverterWindow
        self.link_window = LinkConverterWindow()
        self.link_window.show()
        self.close()

    def launch_bg_remover(self):
        from apps.media_converter.ui.bg_remover import BackgroundRemoverUI
        self.bg_window = BackgroundRemoverUI()
        self.bg_window.show()
        self.close()
