import sys
import os
import datetime
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog, QMessageBox, QComboBox, QHBoxLayout, QProgressDialog
)
from PyQt6.QtCore import Qt
from apps.media_converter.converters import conversion as Conversion
from apps.media_converter.ui.ui_theme import (
    APP_COLORS,
    BUTTON_STYLE,
    COMBO_STYLE,
    DROP_LABEL_STYLE,
    SOFT_BUTTON_STYLE,
    REMOVE_BUTTON_STYLE,
    CONVERT_BUTTON_STYLE,
    FFMPEG_BUTTON_STYLE,
    apply_window_theme,
    make_card_container,
)

VIDEO_FORMATS = ["mp4", "mkv", "avi", "mov", "webm"]


class FileDropLabel(QLabel):
    def __init__(self, on_file_dropped, allowed_extensions, section_name, parent=None, placeholder="Arrastra aquí un archivo"):
        super().__init__(parent)
        self.main_window = parent
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(placeholder)
        self.setStyleSheet(f"{DROP_LABEL_STYLE}min-height: 140px;")
        self.setAcceptDrops(True)
        self.file_path = None
        self.on_file_dropped = on_file_dropped
        self.allowed_extensions = tuple(ext.lower() for ext in allowed_extensions)
        self.section_name = section_name

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile().lower()
            if file_path.endswith(self.allowed_extensions):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            if file_path.lower().endswith(self.allowed_extensions):
                self.file_path = file_path
                self.setText(os.path.basename(file_path))
                self.on_file_dropped(file_path)
            else:
                QMessageBox.warning(
                    self,
                    "Formato no soportado",
                    f"Este archivo no es compatible con el convertidor de {self.section_name}.",
                )
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self.main_window, 'open_batch_manager'):
                self.main_window.open_batch_manager()


class VideoConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convertidor de Video")
        self.setGeometry(120, 120, 520, 480)
        apply_window_theme(self)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(26, 24, 26, 24)
        card, card_layout = make_card_container()

        top_layout = QHBoxLayout()
        back_btn = QPushButton("← Volver")
        back_btn.setFixedWidth(90)
        back_btn.clicked.connect(self.go_back)
        back_btn.setStyleSheet(SOFT_BUTTON_STYLE)
        top_layout.addWidget(back_btn)
        top_layout.addStretch()
        ffmpeg_btn = QPushButton("Configurar FFmpeg")
        ffmpeg_btn.setFixedWidth(160)
        ffmpeg_btn.clicked.connect(self.show_ffmpeg_help)
        ffmpeg_btn.setStyleSheet(FFMPEG_BUTTON_STYLE)
        top_layout.addWidget(ffmpeg_btn)
        card_layout.addLayout(top_layout)

        self.label = QLabel("Selecciona o arrastra un archivo de video para convertir")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"color: {APP_COLORS['text_main']}; font-size: 14pt; font-weight:600;")
        card_layout.addWidget(self.label)

        self.file_label = FileDropLabel(
            self.on_file_dropped,
            [".mp4", ".mkv", ".avi", ".mov", ".webm"],
            "video",
            self,
            placeholder="Arrastra aquí un archivo de video",
        )
        card_layout.addWidget(self.file_label)

        combo_layout = QHBoxLayout()
        self.from_combo = QComboBox()
        self.from_combo.addItems(VIDEO_FORMATS)
        self.from_combo.setEnabled(False)
        combo_layout.addWidget(QLabel("Formato de origen:"))
        combo_layout.addWidget(self.from_combo)

        self.to_combo = QComboBox()
        self.to_combo.addItems(VIDEO_FORMATS)
        combo_layout.addWidget(QLabel("Formato de destino:"))
        combo_layout.addWidget(self.to_combo)
        card_layout.addLayout(combo_layout)

        self.select_button = QPushButton("Seleccionar Archivo")
        self.select_button.clicked.connect(self.select_file)
        self.select_button.setStyleSheet(BUTTON_STYLE)
        card_layout.addWidget(self.select_button)

        self.select_folder_button = QPushButton("Seleccionar Carpeta")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.select_folder_button.setStyleSheet(BUTTON_STYLE)
        card_layout.addWidget(self.select_folder_button)

        self.remove_button = QPushButton("Quitar Archivo")
        self.remove_button.clicked.connect(self.remove_file)
        self.remove_button.setEnabled(False)
        self.remove_button.setStyleSheet(REMOVE_BUTTON_STYLE)
        card_layout.addWidget(self.remove_button)

        self.convert_button = QPushButton("Convertir Archivo")
        self.convert_button.clicked.connect(self.convert_file)
        self.convert_button.setEnabled(False)
        self.convert_button.setStyleSheet(CONVERT_BUTTON_STYLE)
        card_layout.addWidget(self.convert_button)

        self.from_combo.setStyleSheet(COMBO_STYLE)
        self.to_combo.setStyleSheet(COMBO_STYLE)
        for i in range(combo_layout.count()):
            widget = combo_layout.itemAt(i).widget()
            if isinstance(widget, QLabel):
                widget.setStyleSheet(f"color: {APP_COLORS['text_muted']};")

        self.layout.addWidget(card)
        self.setLayout(self.layout)
        self.file_path = None
        self.batch_files = []

    def open_batch_manager(self):
        if len(self.batch_files) > 1:
            from core.ui.batch_dialog import BatchDialog
            from PyQt6.QtWidgets import QDialog
            dialog = BatchDialog(self.batch_files, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.batch_files = dialog.get_files()
                if len(self.batch_files) == 0:
                    self.remove_file()
                else:
                    self.file_label.setText(f"{len(self.batch_files)} videos seleccionados")
        elif len(self.batch_files) == 1 or self.file_path:
            pass

    def select_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Seleccionar Archivo de Video", "", "Video (*.mp4 *.mkv *.avi *.mov *.webm)")
        if file_path:
            self.batch_files = []
            self.file_path = file_path
            self.file_label.setText(os.path.basename(file_path))
            ext = os.path.splitext(file_path)[1].lstrip('.').lower()
            if ext in VIDEO_FORMATS:
                idx = self.from_combo.findText(ext)
                if idx != -1:
                    self.from_combo.setCurrentIndex(idx)
                self.from_combo.setEnabled(False)
                dests = [f for f in VIDEO_FORMATS if f != ext]
                self.to_combo.clear()
                self.to_combo.addItems(dests)
            self.convert_button.setEnabled(True)
            self.remove_button.setEnabled(True)

    def on_file_dropped(self, file_path):
        self.batch_files = []
        self.file_path = file_path
        self.file_label.setText(os.path.basename(file_path))
        ext = os.path.splitext(file_path)[1].lstrip('.').lower()
        if ext in VIDEO_FORMATS:
            idx = self.from_combo.findText(ext)
            if idx != -1:
                self.from_combo.setCurrentIndex(idx)
            self.from_combo.setEnabled(False)
            dests = [f for f in VIDEO_FORMATS if f != ext]
            self.to_combo.clear()
            self.to_combo.addItems(dests)
        self.convert_button.setEnabled(True)
        self.remove_button.setEnabled(True)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Video")
        if not folder_path:
            return
        valid_exts = {".mp4", ".mkv", ".avi", ".mov", ".webm"}
        files = []
        for name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, name)
            if os.path.isfile(file_path):
                if os.path.splitext(name)[1].lower() in valid_exts:
                    files.append(file_path)
        if not files:
            QMessageBox.warning(self, "Sin archivos", "No se encontraron videos compatibles en la carpeta.")
            return
        self.file_path = None
        self.batch_files = files
        self.file_label.setText(f"{len(files)} videos seleccionados")
        self.from_combo.clear()
        self.from_combo.addItem("varios")
        self.to_combo.clear()
        self.to_combo.addItems(VIDEO_FORMATS)
        self.convert_button.setEnabled(True)
        self.remove_button.setEnabled(True)

    def remove_file(self):
        self.file_path = None
        self.batch_files = []
        self.file_label.setText("Arrastra aquí un archivo de video")
        self.convert_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.from_combo.clear()
        self.from_combo.addItems(VIDEO_FORMATS)
        self.from_combo.setCurrentIndex(0)
        self.from_combo.setEnabled(False)
        self.to_combo.clear()
        self.to_combo.addItems(VIDEO_FORMATS)

    def choose_output_folder(self):
        return QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de salida")

    def convert_file(self):
        output_dir = self.choose_output_folder()
        if not output_dir:
            return

        if self.batch_files:
            if len(self.batch_files) > 5:
                folder_name = "Conversion_Masiva_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = os.path.join(output_dir, folder_name)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    
            to_format = self.to_combo.currentText()
            converted = 0
            skipped = 0
            failed = 0
            total = len(self.batch_files)
            progress = QProgressDialog("Convirtiendo videos...", None, 0, total, self)
            progress.setWindowTitle("Procesando")
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            QApplication.processEvents()

            try:
                for idx, source in enumerate(self.batch_files, start=1):
                    from_format = os.path.splitext(source)[1].lstrip(".").lower()
                    if from_format == to_format:
                        skipped += 1
                    else:
                        base = os.path.splitext(os.path.basename(source))[0]
                        destino_path = os.path.join(output_dir, f"{base}.{to_format}")
                        result = Conversion.VideoFormats.convertir(source, destino_path, formato_destino=to_format)
                        if str(result).startswith("✅"):
                            converted += 1
                        else:
                            failed += 1
                    progress.setLabelText(f"Convirtiendo videos... ({idx}/{total})")
                    progress.setValue(idx)
                    QApplication.processEvents()
            finally:
                progress.close()

            msg = f"Convertidos: {converted}\nFallidos: {failed}"
            if skipped > 0:
                msg += f"\n\nSe omitieron {skipped} videos porque ya estaban en formato {to_format.upper()}."

            QMessageBox.information(
                self,
                "Conversión masiva",
                msg,
            )
            try:
                os.startfile(output_dir)
            except Exception:
                try:
                    subprocess.Popen(["xdg-open", output_dir])
                except Exception:
                    pass
            return

        if not self.file_path:
            QMessageBox.warning(self, "Advertencia", "Por favor selecciona un archivo primero.")
            return
        from_format = self.from_combo.currentText()
        to_format = self.to_combo.currentText()
        if from_format == to_format:
            QMessageBox.warning(self, "Advertencia", "El formato de origen y destino no pueden ser iguales.")
            return
        base = os.path.splitext(os.path.basename(self.file_path))[0]
        destino_path = os.path.join(output_dir, f"{base}.{to_format}")

        progress = QProgressDialog("Convirtiendo video...", None, 0, 0, self)
        progress.setWindowTitle("Procesando")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()

        try:
            resultado = Conversion.VideoFormats.convertir(self.file_path, destino_path, formato_destino=to_format)
        finally:
            progress.close()

        if resultado.startswith('✅'):
            QMessageBox.information(self, "Éxito", resultado)
        else:
            QMessageBox.critical(self, "Error", resultado)

        try:
            os.startfile(output_dir)
        except Exception:
            try:
                subprocess.Popen(['xdg-open', output_dir])
            except Exception:
                pass

    def go_back(self):
        from apps.media_converter.ui.index import LauncherWindow
        self.index_window = LauncherWindow()
        self.index_window.show()
        self.close()

    def show_ffmpeg_help(self):
        QMessageBox.information(
            self,
            "Configurar FFmpeg",
            "FFmpeg es necesario para convertir audio y video.\n\n"
            "Instalación recomendada (PowerShell):\n"
            "winget install \"FFmpeg (Essentials Build)\"\n\n"
            "Si ya lo tienes, también puedes definir:\n"
            "FFMPEG_PATH=C:\\ruta\\a\\ffmpeg.exe",
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoConverter()
    window.show()
    sys.exit(app.exec())
