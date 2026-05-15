import sys
import os
import datetime
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QTransform, QPixmap
from apps.document_converter.converters import conversion as Conversion
from apps.document_converter.ui.ui_theme import (
    APP_COLORS,
    BUTTON_STYLE,
    DROP_LABEL_STYLE,
    SOFT_BUTTON_STYLE,
    REMOVE_BUTTON_STYLE,
    CONVERT_BUTTON_STYLE,
    apply_window_theme,
    make_card_container,
)

class FileDropLabel(QLabel):
    def __init__(self, on_file_dropped, allowed_extensions, parent=None, placeholder="Arrastra aquí un archivo"):
        super().__init__(parent)
        self.main_window = parent
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(placeholder)
        self.setStyleSheet(f"{DROP_LABEL_STYLE}min-height: 140px;")
        self.setAcceptDrops(True)
        self.file_path = None
        self.on_file_dropped = on_file_dropped
        self.allowed_extensions = tuple(ext.lower() for ext in allowed_extensions)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and len(event.mimeData().urls()) > 0:
            valid = any(
                url.toLocalFile().lower().endswith(self.allowed_extensions)
                for url in event.mimeData().urls()
            )
            if valid:
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            valid_files = [
                url.toLocalFile()
                for url in event.mimeData().urls()
                if url.toLocalFile().lower().endswith(self.allowed_extensions)
            ]
            invalid_count = len(event.mimeData().urls()) - len(valid_files)
            if valid_files:
                self.on_file_dropped(valid_files)
            if invalid_count > 0:
                QMessageBox.warning(
                    self,
                    "Formato no soportado",
                    f"{invalid_count} archivo(s) no son compatibles con este tipo de conversión y fueron ignorados.",
                )
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self.main_window, 'open_batch_manager'):
                self.main_window.open_batch_manager()

class RotatingLabel(QLabel):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.original_pixmap = pixmap
        self.angle = 0
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setPixmap(self.original_pixmap)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_pixmap)
        self.timer.start(40) # Velocidad de rotación

    def rotate_pixmap(self):
        self.angle = (self.angle + 2) % 360
        transform = QTransform().rotate(self.angle)
        rotated_pixmap = self.original_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        self.setPixmap(rotated_pixmap)

class ConversionWorker(QThread):
    progress_updated = pyqtSignal(int, str)
    finished = pyqtSignal(int, int, list, bool) # converted, failed, errors, was_cancelled

    def __init__(self, files, output_dir, from_ext, to_ext, progress_dialog):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.from_ext = from_ext
        self.to_ext = to_ext
        self.progress_dialog = progress_dialog

    def run(self):
        import time
        converted = 0
        failed = 0
        errors = []
        total = len(self.files)
        was_cancelled = False
        
        for idx, source in enumerate(self.files, start=1):
            while self.progress_dialog.is_paused and not self.progress_dialog.is_cancelled:
                time.sleep(0.2)
                
            if self.progress_dialog.is_cancelled:
                was_cancelled = True
                break
                
            base = os.path.splitext(os.path.basename(source))[0]
            destino_path = os.path.join(self.output_dir, f"{base}.{self.to_ext}")
            
            self.progress_updated.emit(idx - 1, f"Convirtiendo... ({idx}/{total})")
            
            result = Conversion.DocumentFormats.convertir(source, destino_path, self.from_ext, self.to_ext)
            if str(result).startswith("✅"):
                converted += 1
            else:
                failed += 1
                errors.append(f"{os.path.basename(source)}: {str(result)}")
                
            self.progress_updated.emit(idx, f"Completado ({idx}/{total})")
            
        self.finished.emit(converted, failed, errors, was_cancelled)

class DocumentConverterWindow(QWidget):
    def __init__(self, from_ext, to_ext, title="Convertidor de Documentos"):
        super().__init__()
        self.from_ext = from_ext.lower().replace(".", "")
        self.to_ext = to_ext.lower().replace(".", "")
        self.window_title_text = title
        
        self.setWindowTitle(self.window_title_text)
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
        card_layout.addLayout(top_layout)

        # Layout visual de iconos (Origen -> Flechas -> Destino)
        icons_layout = QHBoxLayout()
        icons_layout.setSpacing(20)
        icons_layout.addStretch()
        
        from PyQt6.QtGui import QPixmap
        assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets', 'apps', 'document_converter'))
        
        ext_to_icon = {
            "docx": "word.png",
            "pdf": "pdf.png",
            "jpg": "jpg.png",
            "pptx": "ppt.png",
            "xlsx": "excel.png",
            "html": "html.png"
        }
        
        src_icon_name = ext_to_icon.get(self.from_ext, "pdf.png")
        src_label = QLabel()
        src_pix = QPixmap(os.path.join(assets_dir, src_icon_name))
        if not src_pix.isNull():
            src_label.setPixmap(src_pix.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icons_layout.addWidget(src_label)
        
        arrow_pix = QPixmap(os.path.join(assets_dir, "flechas.png"))
        if not arrow_pix.isNull():
            scaled_pix = arrow_pix.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            arrow_label = RotatingLabel(scaled_pix)
            arrow_label.setFixedSize(60, 60) # Para evitar que tiemble al rotar
        else:
            arrow_label = QLabel()
        icons_layout.addWidget(arrow_label)
        
        dest_icon_name = ext_to_icon.get(self.to_ext, "pdf.png")
        dest_label = QLabel()
        dest_pix = QPixmap(os.path.join(assets_dir, dest_icon_name))
        if not dest_pix.isNull():
            dest_label.setPixmap(dest_pix.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        icons_layout.addWidget(dest_label)
        
        icons_layout.addStretch()
        card_layout.addLayout(icons_layout)

        self.label = QLabel(f"Convertir de {self.from_ext.upper()} a {self.to_ext.upper()}")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"color: {APP_COLORS['text_main']}; font-size: 14pt; font-weight:600; margin-top: 10px;")
        card_layout.addWidget(self.label)

        self.file_label = FileDropLabel(
            self.on_file_dropped,
            [f".{self.from_ext}"],
            self,
            placeholder=f"Arrastra aquí un archivo .{self.from_ext}",
        )
        card_layout.addWidget(self.file_label)

        self.select_button = QPushButton("Seleccionar Archivo")
        self.select_button.clicked.connect(self.select_file)
        self.select_button.setStyleSheet(BUTTON_STYLE)
        card_layout.addWidget(self.select_button)

        self.select_folder_button = QPushButton("Seleccionar Carpeta")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.select_folder_button.setStyleSheet(BUTTON_STYLE)
        card_layout.addWidget(self.select_folder_button)

        self.remove_button = QPushButton("Quitar todo")
        self.remove_button.clicked.connect(self.remove_file)
        self.remove_button.setEnabled(False)
        self.remove_button.setStyleSheet(REMOVE_BUTTON_STYLE)
        card_layout.addWidget(self.remove_button)

        self.convert_button = QPushButton("Convertir Archivo")
        self.convert_button.clicked.connect(self.convert_file)
        self.convert_button.setEnabled(False)
        self.convert_button.setStyleSheet(CONVERT_BUTTON_STYLE)
        card_layout.addWidget(self.convert_button)

        self.layout.addWidget(card)
        self.setLayout(self.layout)
        self.file_path = None
        self.batch_files = []

    def open_batch_manager(self):
        if self.batch_files:
            from core.ui.batch_dialog import BatchDialog
            from PyQt6.QtWidgets import QDialog
            dialog = BatchDialog(self.batch_files, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.batch_files = dialog.get_files()
                if len(self.batch_files) == 0:
                    self.remove_file()
                elif len(self.batch_files) == 1:
                    self.file_label.setText(os.path.basename(self.batch_files[0]))
                else:
                    self.file_label.setText(f"{len(self.batch_files)} archivos seleccionados")

    def select_file(self):
        file_dialog = QFileDialog()
        filter_str = f"Archivos (*.{self.from_ext})"
        file_paths, _ = file_dialog.getOpenFileNames(self, "Seleccionar Archivos", "", filter_str)
        if file_paths:
            self.file_path = None
            for fp in file_paths:
                if fp not in self.batch_files:
                    self.batch_files.append(fp)
            self._refresh_label()

    def on_file_dropped(self, file_paths):
        self.file_path = None
        for fp in file_paths:
            if fp not in self.batch_files:
                self.batch_files.append(fp)
        self._refresh_label()

    def _refresh_label(self):
        if not self.batch_files:
            return
        if len(self.batch_files) == 1:
            self.file_label.setText(os.path.basename(self.batch_files[0]))
        else:
            self.file_label.setText(f"{len(self.batch_files)} archivos seleccionados")
        self.convert_button.setEnabled(True)
        self.remove_button.setEnabled(True)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if not folder_path:
            return
        valid_ext = f".{self.from_ext}"
        self.file_path = None
        for name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, name)
            if os.path.isfile(file_path) and os.path.splitext(name)[1].lower() == valid_ext:
                if file_path not in self.batch_files:
                    self.batch_files.append(file_path)
        if not self.batch_files:
            QMessageBox.warning(self, "Sin archivos", f"No se encontraron archivos {valid_ext} en la carpeta.")
            return
        self._refresh_label()

    def remove_file(self):
        self.file_path = None
        self.batch_files = []
        self.file_label.setText(f"Arrastra aquí un archivo .{self.from_ext}")
        self.convert_button.setEnabled(False)
        self.remove_button.setEnabled(False)

    def choose_output_folder(self):
        return QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de salida")

    def convert_file(self):
        if not self.batch_files:
            QMessageBox.warning(self, "Advertencia", "Por favor selecciona al menos un archivo primero.")
            return

        output_dir = self.choose_output_folder()
        if not output_dir:
            return

        if len(self.batch_files) > 5:
            folder_name = "Conversion_Masiva_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(output_dir, folder_name)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
        from core.ui.advanced_progress import AdvancedProgressDialog
        self.progress = AdvancedProgressDialog("Iniciando conversión...", len(self.batch_files), self)
        self.progress.show()

        # Deshabilitar botones mientras convierte
        self.convert_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.select_button.setEnabled(False)
        self.select_folder_button.setEnabled(False)

        # Iniciar thread
        self.worker = ConversionWorker(self.batch_files, output_dir, self.from_ext, self.to_ext, self.progress)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.finished.connect(lambda c, f, e, canc: self.conversion_finished(c, f, e, canc, output_dir))
        self.worker.start()

    def update_progress(self, value, text):
        self.progress.setValue(value)
        self.progress.setLabelText(text)

    def conversion_finished(self, converted, failed, errors, was_cancelled, output_dir):
        self.progress.close()
        
        # Rehabilitar botones
        self.convert_button.setEnabled(True)
        self.remove_button.setEnabled(True)
        self.select_button.setEnabled(True)
        self.select_folder_button.setEnabled(True)

        if was_cancelled:
            QMessageBox.warning(
                self,
                "Conversión Cancelada",
                f"Proceso cancelado por el usuario.\nSe completaron {converted} archivos de {len(self.batch_files)} antes de cancelar."
            )
        elif failed > 0:
            error_msg = "\n".join(errors[:5]) # Mostrar máximo 5 errores
            if len(errors) > 5:
                error_msg += f"\n... y {len(errors) - 5} más."
                
            QMessageBox.warning(
                self,
                "Conversión completada con errores",
                f"Convertidos: {converted}\nFallidos: {failed}\n\nErrores:\n{error_msg}"
            )
        else:
            QMessageBox.information(
                self,
                "Conversión exitosa",
                f"Se convirtieron {converted} archivo(s) correctamente."
            )

        try:
            os.startfile(output_dir)
        except Exception:
            try:
                subprocess.Popen(["xdg-open", output_dir])
            except Exception:
                pass

    def go_back(self):
        from apps.document_converter.ui.index import DocumentLauncherWindow
        self.index_window = DocumentLauncherWindow()
        self.index_window.show()
        self.close()
