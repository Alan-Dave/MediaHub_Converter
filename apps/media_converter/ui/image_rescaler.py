import sys
import os
import datetime
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog, QMessageBox, 
    QHBoxLayout, QProgressDialog, QRadioButton, QButtonGroup, QSpinBox, QCheckBox
)
from PyQt6.QtGui import QPixmap, QImageReader
from PyQt6.QtCore import Qt

from apps.media_converter.converters.conversion import ImageRescalerLogic
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
        self.allowed_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff', '.gif', '.ico')

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


class ImageRescaler(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reescalador de Imágenes")
        self.setGeometry(100, 100, 520, 700)
        apply_window_theme(self)
        
        self.original_width = 0
        self.original_height = 0
        self.image_path = None
        self.batch_files = []
        
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

        self.label = QLabel("Selecciona o arrastra una imagen para reescalar")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"color: {APP_COLORS['text_main']}; font-size: 14pt; font-weight:600;")
        card_layout.addWidget(self.label)

        self.image_label = ImageDropLabel(self.on_image_dropped, self)
        card_layout.addWidget(self.image_label)

        # Configuraciones de Reescalado
        config_layout = QVBoxLayout()
        
        # Modo: Pixeles o Porcentaje
        mode_layout = QHBoxLayout()
        self.mode_group = QButtonGroup(self)
        self.radio_pixels = QRadioButton("Por Píxeles")
        self.radio_pixels.setChecked(True)
        self.radio_percentage = QRadioButton("Por Porcentaje")
        self.mode_group.addButton(self.radio_pixels)
        self.mode_group.addButton(self.radio_percentage)
        
        self.radio_pixels.setStyleSheet(f"color: {APP_COLORS['text_main']};")
        self.radio_percentage.setStyleSheet(f"color: {APP_COLORS['text_main']};")
        
        mode_layout.addWidget(QLabel("Modo de Reescalado:"))
        mode_layout.addWidget(self.radio_pixels)
        mode_layout.addWidget(self.radio_percentage)
        config_layout.addLayout(mode_layout)
        
        # Opciones de Pixeles
        self.pixels_widget = QWidget()
        pixels_layout = QVBoxLayout(self.pixels_widget)
        pixels_layout.setContentsMargins(0, 0, 0, 0)
        
        wh_layout = QHBoxLayout()
        self.spin_width = QSpinBox()
        self.spin_width.setRange(1, 10000)
        self.spin_width.setValue(800)
        self.spin_height = QSpinBox()
        self.spin_height.setRange(1, 10000)
        self.spin_height.setValue(600)
        
        self.spin_width.valueChanged.connect(self.on_width_changed)
        self.spin_height.valueChanged.connect(self.on_height_changed)
        
        wh_layout.addWidget(QLabel("Ancho:"))
        wh_layout.addWidget(self.spin_width)
        wh_layout.addWidget(QLabel("Alto:"))
        wh_layout.addWidget(self.spin_height)
        pixels_layout.addLayout(wh_layout)
        
        self.check_aspect = QCheckBox("Mantener relación de aspecto")
        self.check_aspect.setChecked(True)
        self.check_aspect.setStyleSheet(f"color: {APP_COLORS['text_main']};")
        pixels_layout.addWidget(self.check_aspect)
        config_layout.addWidget(self.pixels_widget)
        
        # Opciones de Porcentaje
        self.percentage_widget = QWidget()
        percentage_layout = QHBoxLayout(self.percentage_widget)
        percentage_layout.setContentsMargins(0, 0, 0, 0)
        self.spin_percentage = QSpinBox()
        self.spin_percentage.setRange(1, 1000)
        self.spin_percentage.setValue(50)
        self.spin_percentage.setSuffix("%")
        percentage_layout.addWidget(QLabel("Porcentaje:"))
        percentage_layout.addWidget(self.spin_percentage)
        self.percentage_widget.setVisible(False)
        config_layout.addWidget(self.percentage_widget)
        
        # Opciones Generales
        self.check_no_enlarge = QCheckBox("No agrandar si el original es más pequeño")
        self.check_no_enlarge.setChecked(False)
        self.check_no_enlarge.setStyleSheet(f"color: {APP_COLORS['text_main']};")
        config_layout.addWidget(self.check_no_enlarge)
        
        card_layout.addLayout(config_layout)

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

        self.convert_button = QPushButton("Reescalar Imagen")
        self.convert_button.clicked.connect(self.convert_image)
        self.convert_button.setEnabled(False)
        self.convert_button.setStyleSheet(CONVERT_BUTTON_STYLE)
        card_layout.addWidget(self.convert_button)

        # Eventos para cambiar de modo
        self.radio_pixels.toggled.connect(self.toggle_mode)

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

    def toggle_mode(self):
        is_pixels = self.radio_pixels.isChecked()
        self.pixels_widget.setVisible(is_pixels)
        self.percentage_widget.setVisible(not is_pixels)

    def on_width_changed(self, value):
        if self.check_aspect.isChecked() and self.original_width > 0 and self.spin_width.hasFocus():
            aspect_ratio = self.original_height / self.original_width
            new_height = int(value * aspect_ratio)
            self.spin_height.blockSignals(True)
            self.spin_height.setValue(max(1, new_height))
            self.spin_height.blockSignals(False)

    def on_height_changed(self, value):
        if self.check_aspect.isChecked() and self.original_height > 0 and self.spin_height.hasFocus():
            aspect_ratio = self.original_width / self.original_height
            new_width = int(value * aspect_ratio)
            self.spin_width.blockSignals(True)
            self.spin_width.setValue(max(1, new_width))
            self.spin_width.blockSignals(False)

    def go_back(self):
        from apps.media_converter.ui.index import LauncherWindow
        self.index_window = LauncherWindow()
        self.index_window.show()
        self.close()

    def update_original_dimensions(self, file_path):
        reader = QImageReader(file_path)
        size = reader.size()
        if size.isValid():
            self.original_width = size.width()
            self.original_height = size.height()
            self.spin_width.blockSignals(True)
            self.spin_height.blockSignals(True)
            self.spin_width.setValue(self.original_width)
            self.spin_height.setValue(self.original_height)
            self.spin_width.blockSignals(False)
            self.spin_height.blockSignals(False)

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
        self.update_original_dimensions(file_path)
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
        self.original_width = 0
        self.original_height = 0
        self.image_label.clear()
        self.image_label.setText(f"{len(files)} imágenes seleccionadas")
        self.convert_button.setEnabled(True)
        self.remove_button.setEnabled(True)

    def remove_image(self):
        self.image_path = None
        self.batch_files = []
        self.original_width = 0
        self.original_height = 0
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

        modo = "pixeles" if self.radio_pixels.isChecked() else "porcentaje"
        ancho = self.spin_width.value()
        alto = self.spin_height.value()
        porcentaje = self.spin_percentage.value()
        mantener_aspecto = self.check_aspect.isChecked()
        no_agrandar = self.check_no_enlarge.isChecked()

        if self.batch_files:
            if len(self.batch_files) > 5:
                folder_name = "Reescalado_Masivo_" + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = os.path.join(output_dir, folder_name)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                    
            converted = 0
            failed = 0
            total = len(self.batch_files)
            progress = QProgressDialog("Reescalando imágenes...", None, 0, total, self)
            progress.setWindowTitle("Procesando")
            progress.setWindowModality(Qt.WindowModality.ApplicationModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            progress.show()
            QApplication.processEvents()

            try:
                for idx, file_path in enumerate(self.batch_files, start=1):
                    nombre = os.path.basename(file_path)
                    ruta_destino = os.path.join(output_dir, nombre)
                    
                    resultado = ImageRescalerLogic.reescalar_imagen(
                        ruta_origen=file_path,
                        ruta_destino=ruta_destino,
                        modo=modo,
                        ancho_target=ancho,
                        alto_target=alto,
                        porcentaje=porcentaje,
                        mantener_aspecto=mantener_aspecto,
                        no_agrandar=no_agrandar
                    )
                    
                    if str(resultado).startswith("✅"):
                        converted += 1
                    else:
                        failed += 1
                        
                    progress.setLabelText(f"Reescalando imágenes... ({idx}/{total})")
                    progress.setValue(idx)
                    QApplication.processEvents()
            finally:
                progress.close()

            QMessageBox.information(
                self,
                "Reescalado masivo",
                f"Reescalados: {converted}\nFallidos: {failed}",
            )
            try:
                os.startfile(output_dir)
            except AttributeError:
                subprocess.Popen(["xdg-open", output_dir])
            return

        if not self.image_path:
            QMessageBox.warning(self, "Advertencia", "Por favor selecciona una imagen primero.")
            return

        nombre = os.path.basename(self.image_path)
        ruta_destino = os.path.join(output_dir, nombre)

        progress = QProgressDialog("Reescalando imagen...", None, 0, 0, self)
        progress.setWindowTitle("Procesando")
        progress.setWindowModality(Qt.WindowModality.ApplicationModal)
        progress.setMinimumDuration(0)
        progress.show()
        QApplication.processEvents()
        try:
            resultado = ImageRescalerLogic.reescalar_imagen(
                ruta_origen=self.image_path,
                ruta_destino=ruta_destino,
                modo=modo,
                ancho_target=ancho,
                alto_target=alto,
                porcentaje=porcentaje,
                mantener_aspecto=mantener_aspecto,
                no_agrandar=no_agrandar
            )
        finally:
            progress.close()

        if "Error" in resultado:
            QMessageBox.warning(self, "Error", resultado)
        else:
            QMessageBox.information(self, "Conversión", resultado)
            try:
                os.startfile(output_dir)
            except AttributeError:
                subprocess.Popen(['xdg-open', output_dir])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageRescaler()
    window.show()
    sys.exit(app.exec())
