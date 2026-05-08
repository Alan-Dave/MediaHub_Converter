import sys
import os
import datetime
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog, QMessageBox, QHBoxLayout, QProgressDialog
)
from PyQt6.QtCore import Qt, QTimer
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
                    "Este archivo no es compatible con este tipo de conversión.",
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
                    self.file_label.setText(f"{len(self.batch_files)} archivos seleccionados")
        elif len(self.batch_files) == 1 or self.file_path:
            pass

    def select_file(self):
        file_dialog = QFileDialog()
        filter_str = f"Archivos (*.{self.from_ext})"
        file_path, _ = file_dialog.getOpenFileName(self, "Seleccionar Archivo", "", filter_str)
        if file_path:
            self.batch_files = []
            self.file_path = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.convert_button.setEnabled(True)
            self.remove_button.setEnabled(True)

    def on_file_dropped(self, file_path):
        self.batch_files = []
        self.file_path = file_path
        self.file_label.setText(os.path.basename(file_path))
        self.convert_button.setEnabled(True)
        self.remove_button.setEnabled(True)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if not folder_path:
            return
        valid_ext = f".{self.from_ext}"
        files = []
        for name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, name)
            if os.path.isfile(file_path):
                if os.path.splitext(name)[1].lower() == valid_ext:
                    files.append(file_path)
        if not files:
            QMessageBox.warning(self, "Sin archivos", f"No se encontraron archivos {valid_ext} en la carpeta.")
            return
        self.file_path = None
        self.batch_files = files
        self.file_label.setText(f"{len(files)} archivos seleccionados")
        self.convert_button.setEnabled(True)
        self.remove_button.setEnabled(True)

    def remove_file(self):
        self.file_path = None
        self.batch_files = []
        self.file_label.setText(f"Arrastra aquí un archivo .{self.from_ext}")
        self.convert_button.setEnabled(False)
        self.remove_button.setEnabled(False)

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
                    
            converted = 0
            failed = 0
            total = len(self.batch_files)
            progress = QProgressDialog("Convirtiendo documentos...", None, 0, total, self)
            progress.setWindowTitle("Procesando")
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            QApplication.processEvents()

            try:
                for idx, source in enumerate(self.batch_files, start=1):
                    base = os.path.splitext(os.path.basename(source))[0]
                    destino_path = os.path.join(output_dir, f"{base}.{self.to_ext}")
                    result = Conversion.DocumentFormats.convertir(source, destino_path, self.from_ext, self.to_ext)
                    if str(result).startswith("✅"):
                        converted += 1
                    else:
                        failed += 1
                    progress.setLabelText(f"Convirtiendo... ({idx}/{total})")
                    progress.setValue(idx)
                    QApplication.processEvents()
            finally:
                progress.close()

            QMessageBox.information(
                self,
                "Conversión masiva",
                f"Convertidos: {converted}\nFallidos: {failed}",
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

        base = os.path.splitext(os.path.basename(self.file_path))[0]
        destino_path = os.path.join(output_dir, f"{base}.{self.to_ext}")

        progress = QProgressDialog("Convirtiendo documento...", None, 0, 0, self)
        progress.setWindowTitle("Procesando")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()

        try:
            resultado = Conversion.DocumentFormats.convertir(self.file_path, destino_path, self.from_ext, self.to_ext)
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
        from apps.document_converter.ui.index import DocumentLauncherWindow
        self.index_window = DocumentLauncherWindow()
        self.index_window.show()
        self.close()
