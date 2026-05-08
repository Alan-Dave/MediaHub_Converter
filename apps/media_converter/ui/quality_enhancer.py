import sys
import os
import datetime
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog, QMessageBox, 
    QHBoxLayout, QProgressDialog
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt

from apps.media_converter.converters.conversion import ImageEnhancerLogic
from apps.media_converter.ui.ui_theme import (
    APP_COLORS,
    BUTTON_STYLE,
    DROP_LABEL_STYLE,
    SOFT_BUTTON_STYLE,
    REMOVE_BUTTON_STYLE,
    CONVERT_BUTTON_STYLE,
    apply_window_theme,
    make_card_container,
)

class ImageDropLabel(QLabel):
    def __init__(self, on_image_dropped, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("Arrastra aquí una imagen")
        self.setStyleSheet(f"{DROP_LABEL_STYLE}min-height: 180px;")
        self.setAcceptDrops(True)
        self.image_path = None
        self.on_image_dropped = on_image_dropped
        self.allowed_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff')

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(self.allowed_extensions):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_path = event.mimeData().urls()[0].toLocalFile()
            if file_path.lower().endswith(self.allowed_extensions):
                self.image_path = file_path
                pixmap = QPixmap(file_path)
                self.setPixmap(pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
                self.on_image_dropped(file_path)
            else:
                QMessageBox.warning(self, "Formato no soportado", "Este archivo no es una imagen válida.")
        else:
            event.ignore()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if hasattr(self.main_window, 'open_batch_manager'):
                self.main_window.open_batch_manager()


class QualityEnhancerUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mejorador de Calidad con IA (4x)")
        self.setGeometry(100, 100, 480, 560)
        apply_window_theme(self)
        
        self.image_path = None
        self.batch_files = []
        
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(26, 24, 26, 24)
        card, card_layout = make_card_container()

        top_layout = QHBoxLayout()
        back_btn = QPushButton("← Volver al Hub")
        back_btn.setFixedWidth(130)
        back_btn.clicked.connect(self.go_back)
        back_btn.setStyleSheet(SOFT_BUTTON_STYLE)
        top_layout.addWidget(back_btn)
        top_layout.addStretch()
        card_layout.addLayout(top_layout)

        self.label = QLabel("Selecciona o arrastra una imagen para mejorar su calidad")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"color: {APP_COLORS['text_main']}; font-size: 13pt; font-weight:600;")
        self.label.setWordWrap(True)
        card_layout.addWidget(self.label)

        self.info_label = QLabel("La imagen aumentará su resolución por 4x utilizando Inteligencia Artificial (EDSR).\nNota: Puede tardar unos minutos en completarse y el primer uso descargará el modelo.")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet(f"color: {APP_COLORS['text_muted']}; font-size: 10pt;")
        self.info_label.setWordWrap(True)
        card_layout.addWidget(self.info_label)

        self.image_label = ImageDropLabel(self.on_image_dropped, self)
        card_layout.addWidget(self.image_label)

        # Botones de Acción
        self.select_button = QPushButton("Seleccionar Imagen")
        self.select_button.clicked.connect(self.select_image)
        self.select_button.setStyleSheet(BUTTON_STYLE)
        card_layout.addWidget(self.select_button)

        self.select_folder_button = QPushButton("Seleccionar Carpeta")
        self.select_folder_button.clicked.connect(self.select_folder)
        self.select_folder_button.setStyleSheet(BUTTON_STYLE)
        card_layout.addWidget(self.select_folder_button)

        self.remove_button = QPushButton("Quitar Archivo")
        self.remove_button.clicked.connect(self.remove_image)
        self.remove_button.setEnabled(False)
        self.remove_button.setStyleSheet(REMOVE_BUTTON_STYLE)
        card_layout.addWidget(self.remove_button)

        self.convert_button = QPushButton("Mejorar Calidad")
        self.convert_button.clicked.connect(self.convert_image)
        self.convert_button.setEnabled(False)
        self.convert_button.setStyleSheet(CONVERT_BUTTON_STYLE)
        card_layout.addWidget(self.convert_button)

        self.layout.addWidget(card)
        self.setLayout(self.layout)

    def open_batch_manager(self):
        if len(self.batch_files) > 1:
            from core.ui.batch_dialog import BatchDialog
            from PyQt6.QtWidgets import QDialog
            dialog = BatchDialog(self.batch_files, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.batch_files = dialog.get_files()
                if len(self.batch_files) == 0:
                    self.remove_image()
                else:
                    self.image_label.clear()
                    self.image_label.setText(f"{len(self.batch_files)} imágenes seleccionadas")
        elif len(self.batch_files) == 1 or self.image_path:
            pass

    def go_back(self):
        from core.ui.hub_window import HubWindow
        self.index_window = HubWindow()
        self.index_window.show()
        self.close()

    def select_image(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Seleccionar Imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp *.webp *.tiff)")
        if file_path:
            self.on_image_dropped(file_path)

    def on_image_dropped(self, file_path):
        self.batch_files = []
        self.image_path = file_path
        pixmap = QPixmap(file_path)
        self.image_label.setPixmap(pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio))
        self.convert_button.setEnabled(True)
        self.remove_button.setEnabled(True)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta de Imágenes")
        if not folder_path:
            return
        valid_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
        files = []
        for name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, name)
            if os.path.isfile(file_path):
                ext = os.path.splitext(name)[1].lower()
                if ext in valid_exts:
                    files.append(file_path)
        if not files:
            QMessageBox.warning(self, "Sin archivos", "No se encontraron imágenes compatibles en la carpeta.")
            return
        self.image_path = None
        self.batch_files = files
        self.image_label.clear()
        self.image_label.setText(f"{len(files)} imágenes seleccionadas")
        self.convert_button.setEnabled(True)
        self.remove_button.setEnabled(True)

    def remove_image(self):
        self.image_path = None
        self.batch_files = []
        self.image_label.clear()
        self.image_label.setText("Arrastra aquí una imagen")
        self.convert_button.setEnabled(False)
        self.remove_button.setEnabled(False)

    def choose_output_folder(self):
        return QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de salida")

    def convert_image(self):
        output_dir = self.choose_output_folder()
        if not output_dir:
            return

        if self.batch_files:
            if len(self.batch_files) > 5:
                folder_name = "Mejorado_Masivo_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = os.path.join(output_dir, folder_name)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    
            converted = 0
            failed = 0
            total = len(self.batch_files)
            progress = QProgressDialog("Mejorando calidad... Esto tomará un tiempo por cada imagen.", None, 0, total, self)
            progress.setWindowTitle("Procesando")
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            QApplication.processEvents()

            try:
                for idx, file_path in enumerate(self.batch_files, start=1):
                    nombre = os.path.splitext(os.path.basename(file_path))[0]
                    ext = os.path.splitext(file_path)[1]
                    ruta_destino = os.path.join(output_dir, f"{nombre}_4x{ext}")
                    
                    resultado = ImageEnhancerLogic.mejorar_calidad(
                        ruta_origen=file_path,
                        ruta_destino=ruta_destino
                    )
                    
                    if str(resultado).startswith("✅"):
                        converted += 1
                    else:
                        failed += 1
                        
                    progress.setLabelText(f"Mejorando calidad... ({idx}/{total})")
                    progress.setValue(idx)
                    QApplication.processEvents()
            finally:
                progress.close()

            QMessageBox.information(
                self,
                "Proceso Masivo",
                f"Procesados con éxito: {converted}\nFallidos: {failed}",
            )
            try:
                os.startfile(output_dir)
            except AttributeError:
                subprocess.Popen(["xdg-open", output_dir])
            return

        if not self.image_path:
            QMessageBox.warning(self, "Advertencia", "Por favor selecciona una imagen primero.")
            return

        nombre = os.path.splitext(os.path.basename(self.image_path))[0]
        ext = os.path.splitext(self.image_path)[1]
        ruta_destino = os.path.join(output_dir, f"{nombre}_4x{ext}")

        progress = QProgressDialog("Mejorando calidad... Esto puede demorar bastante.", None, 0, 0, self)
        progress.setWindowTitle("Procesando")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        try:
            resultado = ImageEnhancerLogic.mejorar_calidad(
                ruta_origen=self.image_path,
                ruta_destino=ruta_destino
            )
        finally:
            progress.close()

        if "Error" in resultado:
            QMessageBox.warning(self, "Error", resultado)
        else:
            QMessageBox.information(self, "Proceso Completado", resultado)
            try:
                os.startfile(output_dir)
            except AttributeError:
                subprocess.Popen(['xdg-open', output_dir])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QualityEnhancerUI()
    window.show()
    sys.exit(app.exec())
