import os
import sys
import json
import subprocess
import zipfile
import tempfile
import threading

import requests
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QGridLayout, QFrame,
    QGraphicsDropShadowEffect, QProgressDialog, QMessageBox,
    QApplication
)
from PyQt6.QtGui import QPixmap, QIcon, QColor, QDrag
from PyQt6.QtCore import QMimeData, Qt, QSize, QThread, pyqtSignal

from core.theme_manager import ThemeManager
from core.updater import CheckUpdateThread, UpdateDialog
from core.config import APP_REGISTRY


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers de rutas y detección de instalación
# ─────────────────────────────────────────────────────────────────────────────

def get_asset_path(filename):
    """Devuelve la ruta absoluta de un asset del Launcher."""
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_dir, "assets", "hub", filename)


def get_apps_install_dir() -> str:
    """Carpeta raíz donde se instalan las micro-apps: %LOCALAPPDATA%\\MediaHub\\apps\\"""
    local = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    path = os.path.join(local, "MediaHub", "apps")
    os.makedirs(path, exist_ok=True)
    return path


def get_app_exe(app_id: str) -> str | None:
    """
    Devuelve la ruta al ejecutable de una micro-app si está instalada,
    o None si no lo está.
    """
    reg = APP_REGISTRY.get(app_id)
    if not reg:
        return None
    install_dir = os.path.join(get_apps_install_dir(), reg["dir"])
    exe_path = os.path.join(install_dir, reg["exe"])
    return exe_path if os.path.isfile(exe_path) else None


def launch_app(app_id: str):
    """Lanza la micro-app instalada como proceso independiente."""
    exe = get_app_exe(app_id)
    if exe:
        subprocess.Popen([exe], creationflags=subprocess.CREATE_NO_WINDOW
                         if sys.platform == "win32" else 0)


# ─────────────────────────────────────────────────────────────────────────────
#  Worker de descarga / instalación
# ─────────────────────────────────────────────────────────────────────────────

class InstallWorker(QThread):
    """Descarga el último release de una micro-app desde GitHub y lo extrae."""

    progress   = pyqtSignal(int, str)   # (porcentaje, texto)
    finished   = pyqtSignal(str)        # mensaje de éxito
    error      = pyqtSignal(str)        # mensaje de error

    def __init__(self, app_id: str, parent=None):
        super().__init__(parent)
        self.app_id = app_id

    def run(self):
        reg = APP_REGISTRY.get(self.app_id)
        if not reg:
            self.error.emit("App desconocida.")
            return

        repo   = reg["repo"]
        api    = f"https://api.github.com/repos/{repo}/releases/latest"

        try:
            self.progress.emit(5, "Consultando GitHub…")
            resp = requests.get(api, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            self.error.emit(f"No se pudo obtener la release:\n{e}")
            return

        # Buscar el asset ZIP o EXE
        asset_url  = None
        asset_name = None
        for asset in data.get("assets", []):
            name = asset["name"]
            if name.endswith(".zip") or name.endswith(".exe"):
                asset_url  = asset["browser_download_url"]
                asset_name = name
                break

        if not asset_url:
            self.error.emit("No se encontró ningún archivo de instalación en la release.")
            return

        # Descargar
        self.progress.emit(10, f"Descargando {asset_name}…")
        try:
            tmp_dir  = tempfile.mkdtemp()
            tmp_file = os.path.join(tmp_dir, asset_name)
            with requests.get(asset_url, stream=True, timeout=60) as dl:
                dl.raise_for_status()
                total = int(dl.headers.get("content-length", 0))
                downloaded = 0
                with open(tmp_file, "wb") as f:
                    for chunk in dl.iter_content(chunk_size=65536):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = 10 + int(downloaded / total * 70)
                            self.progress.emit(pct, f"Descargando… {downloaded // 1024} KB")
        except Exception as e:
            self.error.emit(f"Error al descargar:\n{e}")
            return

        # Instalar
        self.progress.emit(82, "Instalando…")
        install_base = get_apps_install_dir()
        dest_dir = os.path.join(install_base, reg["dir"])
        os.makedirs(dest_dir, exist_ok=True)

        try:
            if asset_name.endswith(".zip"):
                with zipfile.ZipFile(tmp_file, "r") as zf:
                    zf.extractall(dest_dir)
            else:
                # Si es un .exe de instalador, lanzarlo directamente
                subprocess.run([tmp_file, "/SILENT", f"/DIR={dest_dir}"],
                               check=True)
        except Exception as e:
            self.error.emit(f"Error al instalar:\n{e}")
            return

        self.progress.emit(100, "¡Instalación completada!")
        self.finished.emit(reg["name"])


# ─────────────────────────────────────────────────────────────────────────────
#  AppCard
# ─────────────────────────────────────────────────────────────────────────────

class AppCard(QFrame):
    def __init__(self, card_id, title, subtitle, icon_file,
                 is_disabled=False, parent=None):
        super().__init__(parent)
        self.card_id    = card_id
        self._is_disabled = is_disabled
        self.setAcceptDrops(True)

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

        # Botón principal (Instalar / Abrir)
        self.action_btn = QPushButton()
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        action_layout.addWidget(self.action_btn)
        action_layout.addStretch()

        # Etiqueta de estado
        self._status_label = QLabel()
        action_layout.addWidget(self._status_label)

        content_layout.addLayout(action_layout)
        main_layout.addLayout(content_layout)

        # Actualizar botón según estado instalado
        self.refresh_state()

    def refresh_state(self):
        """Actualiza el botón según si la app está instalada."""
        if self._is_disabled or self.card_id not in APP_REGISTRY:
            self._set_btn_state("disabled")
            return

        exe = get_app_exe(self.card_id)
        if exe:
            self._set_btn_state("open")
        else:
            self._set_btn_state("install")

    def _set_btn_state(self, state: str):
        """state: 'open' | 'install' | 'disabled'"""
        self._btn_state = state
        if state == "open":
            self.action_btn.setText(" ABRIR")
            self.action_btn.setIcon(
                self.style().standardIcon(self.style().StandardPixmap.SP_DialogApplyButton))
            self.action_btn.setEnabled(True)
            self._status_label.setText("✅ Instalado")
        elif state == "install":
            self.action_btn.setText(" INSTALAR")
            self.action_btn.setIcon(
                self.style().standardIcon(self.style().StandardPixmap.SP_ArrowDown))
            self.action_btn.setEnabled(True)
            self._status_label.setText("⬇ No instalado")
        else:
            self.action_btn.setText(" PRÓXIMAMENTE")
            self.action_btn.setEnabled(False)
            self._status_label.setText("")

    # ── Drag & Drop ──────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos()

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not hasattr(self, 'drag_start_position'):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.card_id)
        drag.setMimeData(mime_data)
        pixmap = self.grab()
        drag.setPixmap(pixmap.scaled(300, 150,
                                     Qt.AspectRatioMode.KeepAspectRatio,
                                     Qt.TransformationMode.SmoothTransformation))
        drag.setHotSpot(event.pos())
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.source() != self:
            event.acceptProposedAction()

    def dropEvent(self, event):
        source_id = event.mimeData().text()
        target_id = self.card_id
        if hasattr(self.window(), "swap_cards"):
            self.window().swap_cards(source_id, target_id)
        event.acceptProposedAction()

    # ── Styles ───────────────────────────────────────────────────────────────

    def apply_styles(self, styles: dict):
        if self._is_disabled:
            self.setStyleSheet(styles["card_disabled"])
        else:
            self.setStyleSheet(styles["card_normal"])
        self._title_label.setStyleSheet(styles["card_title"])
        self._subtitle_label.setStyleSheet(styles["card_subtitle"])
        self._status_label.setStyleSheet(styles.get("portable", ""))
        state = getattr(self, "_btn_state", "disabled")
        if state == "install":
            self.action_btn.setStyleSheet(styles["btn_install"])
        elif state == "open":
            self.action_btn.setStyleSheet(styles["btn_open"])
        else:
            self.action_btn.setStyleSheet(styles["btn_disabled"])


# ─────────────────────────────────────────────────────────────────────────────
#  HubWindow  —  MediaHub Launcher
# ─────────────────────────────────────────────────────────────────────────────

class HubWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Hub — Launcher")
        self.resize(900, 800)
        self._tm = ThemeManager.instance()
        self._workers: dict[str, InstallWorker] = {}
        self.init_ui()
        self._apply_theme()

        # Verificar actualizaciones del Launcher en background
        self.update_thread = CheckUpdateThread(self)
        self.update_thread.update_available.connect(self.show_update_dialog)
        self.update_thread.start()

    def show_update_dialog(self, version, description, download_url, size_mb):
        dialog = UpdateDialog(version, description, download_url, size_mb, self)
        dialog.exec()

    # ── Layout ───────────────────────────────────────────────────────────────

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 30, 40, 40)
        main_layout.setSpacing(20)

        # Header
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

        # Cards
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)

        self.media_card = AppCard(
            card_id="media", title="MULTIMEDIA CONVERTER",
            subtitle="Video, Audio, Imagen y más",
            icon_file="media.png")
        self.media_card.action_btn.clicked.connect(
            lambda: self._handle_card("media"))

        self.docs_card = AppCard(
            card_id="docs", title="DOCUMENT CONVERTER",
            subtitle="PDF, Word, Excel, PowerPoint",
            icon_file="docs.png")
        self.docs_card.action_btn.clicked.connect(
            lambda: self._handle_card("docs"))

        self.image_tools_card = AppCard(
            card_id="image_tools", title="IMAGE TOOLS",
            subtitle="BG Eraser · Quality 4x · Watermark",
            icon_file="quality.webp")
        self.image_tools_card.action_btn.clicked.connect(
            lambda: self._handle_card("image_tools"))

        self.link_card = AppCard(
            card_id="link", title="LINK CONVERTER",
            subtitle="YouTube, TikTok, Instagram & more",
            icon_file="link_converter.webp")
        self.link_card.action_btn.clicked.connect(
            lambda: self._handle_card("link"))

        self.subtitle_card = AppCard(
            card_id="subtitle", title="SUBTITLE GENERATOR",
            subtitle="Whisper AI — transcripción local",
            icon_file="subtitle.png")
        self.subtitle_card.action_btn.clicked.connect(
            lambda: self._handle_card("subtitle"))

        self._card_dict = {
            "media":       self.media_card,
            "docs":        self.docs_card,
            "image_tools": self.image_tools_card,
            "link":        self.link_card,
            "subtitle":    self.subtitle_card,
        }

        # Orden persistido
        default_order = ["media", "docs", "image_tools", "link", "subtitle"]
        order = default_order[:]
        try:
            appdata = os.environ.get('ProgramData', '')
            path = os.path.join(appdata, "MediaHub", "settings.json")
            with open(path, 'r') as f:
                saved = json.load(f).get("hub_order", [])
                if len(saved) == len(order) and all(k in self._card_dict for k in saved):
                    order = saved
        except Exception:
            pass

        self._all_cards = [self._card_dict[k] for k in order]
        cols = 2
        for i, card in enumerate(self._all_cards):
            self.grid_layout.addWidget(card, i // cols, i % cols)

        main_layout.addLayout(self.grid_layout)

    # ── Card handler (Instalar / Abrir) ───────────────────────────────────────

    def _handle_card(self, app_id: str):
        card = self._card_dict.get(app_id)
        if not card:
            return
        state = getattr(card, "_btn_state", "disabled")
        if state == "open":
            launch_app(app_id)
        elif state == "install":
            self._start_install(app_id)

    def _start_install(self, app_id: str):
        if app_id in self._workers:
            return  # ya se está instalando

        reg = APP_REGISTRY.get(app_id)
        if not reg:
            return

        card = self._card_dict[app_id]
        card.action_btn.setEnabled(False)
        card._status_label.setText("⏳ Descargando…")

        worker = InstallWorker(app_id, parent=self)
        worker.progress.connect(lambda pct, msg: self._on_install_progress(app_id, pct, msg))
        worker.finished.connect(lambda name: self._on_install_done(app_id, name))
        worker.error.connect(lambda err: self._on_install_error(app_id, err))
        self._workers[app_id] = worker
        worker.start()

    def _on_install_progress(self, app_id: str, pct: int, msg: str):
        card = self._card_dict.get(app_id)
        if card:
            card._status_label.setText(f"⏳ {msg}")

    def _on_install_done(self, app_id: str, name: str):
        self._workers.pop(app_id, None)
        card = self._card_dict.get(app_id)
        if card:
            card.refresh_state()
            styles = self._tm.hub_styles()
            card.apply_styles(styles)
        QMessageBox.information(self, "Instalación completa",
                                f"✅ {name} se instaló correctamente.\n"
                                f"Ya puedes abrirlo desde el Hub.")

    def _on_install_error(self, app_id: str, err: str):
        self._workers.pop(app_id, None)
        card = self._card_dict.get(app_id)
        if card:
            card.refresh_state()
            styles = self._tm.hub_styles()
            card.apply_styles(styles)
        QMessageBox.critical(self, "Error de instalación", err)

    # ── Drag & Drop ──────────────────────────────────────────────────────────

    def swap_cards(self, id1, id2):
        idx1 = next(i for i, c in enumerate(self._all_cards) if c.card_id == id1)
        idx2 = next(i for i, c in enumerate(self._all_cards) if c.card_id == id2)
        self._all_cards[idx1], self._all_cards[idx2] = \
            self._all_cards[idx2], self._all_cards[idx1]
        for card in self._all_cards:
            self.grid_layout.removeWidget(card)
        cols = 2
        for i, card in enumerate(self._all_cards):
            self.grid_layout.addWidget(card, i // cols, i % cols)
        self.save_layout()

    def save_layout(self):
        order = [c.card_id for c in self._all_cards]
        appdata = os.environ.get('ProgramData', '')
        if appdata:
            path = os.path.join(appdata, "MediaHub", "settings.json")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump({"hub_order": order}, f)

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _toggle_dark_mode(self):
        self._tm.toggle()
        self._apply_theme()

    def _apply_theme(self):
        styles = self._tm.hub_styles()
        self.setStyleSheet(styles["window"])
        self.title_label.setStyleSheet(styles["title"])
        self.toggle_btn.setStyleSheet(styles["toggle_btn"])
        self.toggle_btn.setText(
            "☀️  Modo Claro" if self._tm.is_dark else "🌙  Modo Oscuro")
        for card in self._all_cards:
            card.apply_styles(styles)
