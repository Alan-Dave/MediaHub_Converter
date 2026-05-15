import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
import sys
from apps.document_converter.ui.ui_theme import (
    get_app_colors,
    get_soft_button_style,
    get_doc_btn_style,
    apply_window_theme,
    make_card_container,
)


class DocumentLauncherWindow(QWidget):
    """Menú principal del Convertidor de Documentos."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convertidor de Documentos")
        self.setGeometry(200, 200, 700, 500)
        apply_window_theme(self)
        self._colors = get_app_colors()
        self.init_ui()

    def init_ui(self):
        # Configurar Stacked Widget
        self.stacked_widget = QStackedWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

        # Construir la página del menú
        self.menu_page = QWidget()
        root_layout = QVBoxLayout(self.menu_page)
        root_layout.setContentsMargins(28, 24, 28, 24)
        root_layout.setSpacing(0)
        main_card, layout = make_card_container()

        title = QLabel("Convertidor de Documentos")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size: 22pt; font-weight: 700; color: {self._colors['text_main']}; margin-bottom: 24px;")
        layout.addWidget(title)

        # Contenedor de las dos columnas
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(40)

        BTN_STYLE = get_doc_btn_style()

        def add_menu_button(layout, text, icon_name):
            btn = QPushButton(f"  {text}")
            btn.setStyleSheet(BTN_STYLE)
            btn.setMinimumHeight(60)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            if icon_name:
                icon_path = os.path.abspath(os.path.join(
                    os.path.dirname(__file__), '..', '..', '..', 'assets', 'apps', 'document_converter', icon_name
                ))
                if os.path.exists(icon_path):
                    btn.setIcon(QIcon(icon_path))
                    btn.setIconSize(QSize(28, 28))
                    
            btn.clicked.connect(lambda checked, t=text: self.dummy_action(t))
            layout.addWidget(btn)

        # Columna Izquierda: A PDF
        left_col = QVBoxLayout()
        left_title = QLabel("CONVERTIR A PDF")
        left_title.setStyleSheet(f"color: {self._colors['text_muted']}; font-weight: bold; font-size: 14pt; margin-bottom: 12px;")
        left_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_col.addWidget(left_title)

        a_pdf_options = [
            ("JPG a PDF", "jpg.png"),
            ("WORD a PDF", "word.png"),
            ("POWERPOINT a PDF", "ppt.png"),
            ("EXCEL a PDF", "excel.png"),
            ("HTML a PDF", "html.png"),
        ]

        for text, icon in a_pdf_options:
            add_menu_button(left_col, text, icon)

        left_col.addStretch()

        # Columna Derecha: DESDE PDF
        right_col = QVBoxLayout()
        right_title = QLabel("CONVERTIR DESDE PDF")
        right_title.setStyleSheet(f"color: {self._colors['text_muted']}; font-weight: bold; font-size: 14pt; margin-bottom: 12px;")
        right_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_col.addWidget(right_title)

        desde_pdf_options = [
            ("PDF a JPG", "pdf.png"),
            ("PDF a WORD", "word.png"),
            ("PDF a POWERPOINT", "ppt.png"),
            ("PDF a EXCEL", "excel.png"),
            ("PDF a PDF/A", "pdf.png"),
        ]

        for text, icon in desde_pdf_options:
            add_menu_button(right_col, text, icon)
            
        right_col.addStretch()

        columns_layout.addLayout(left_col)
        columns_layout.addLayout(right_col)

        layout.addLayout(columns_layout)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch()
        
        real_exit_btn = QPushButton("Salir")
        real_exit_btn.setFixedWidth(120)
        real_exit_btn.clicked.connect(self.close)
        real_exit_btn.setStyleSheet(get_soft_button_style())
        footer.addWidget(real_exit_btn)
        
        exit_btn = QPushButton("← Volver al Hub")
        exit_btn.setFixedWidth(160)
        exit_btn.clicked.connect(self.go_to_hub)
        exit_btn.setStyleSheet(get_soft_button_style())
        footer.addWidget(exit_btn)
        
        footer.addStretch()

        layout.addLayout(footer)

        root_layout.addWidget(main_card)
        self.stacked_widget.addWidget(self.menu_page)
        self.loaded_pages = {}

    def go_home(self):
        self.stacked_widget.setCurrentWidget(self.menu_page)

    def dummy_action(self, option):
        from apps.document_converter.ui.converter_window import DocumentConverterWindow
        parts = option.split(" a ")
        if len(parts) == 2:
            from_str = parts[0].strip().lower()
            to_str = parts[1].strip().lower()
            
            ext_map = {
                "word": "docx",
                "powerpoint": "pptx",
                "excel": "xlsx",
                "pdf/a": "pdf"
            }
            from_ext = ext_map.get(from_str, from_str)
            to_ext = ext_map.get(to_str, to_str)
            
            tool_id = f"doc_{from_ext}_to_{to_ext}"
            if tool_id not in self.loaded_pages:
                tool_widget = DocumentConverterWindow(from_ext=from_ext, to_ext=to_ext, title=f"Convertir {option}")
                tool_widget.parent_navigator = self
                self.stacked_widget.addWidget(tool_widget)
                self.loaded_pages[tool_id] = tool_widget
                
            self.stacked_widget.setCurrentWidget(self.loaded_pages[tool_id])
        else:
            QMessageBox.information(self, "Error", "Acción no reconocida.")

    def go_to_hub(self):
        from core.ui.hub_window import HubWindow
        self.hub_window = HubWindow()
        self.hub_window.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DocumentLauncherWindow()
    window.show()
    sys.exit(app.exec())
