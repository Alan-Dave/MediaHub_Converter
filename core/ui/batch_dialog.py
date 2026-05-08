import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel, QListWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt
from core.ui.hub_theme import HUB_WINDOW_STYLE

class BatchDialog(QDialog):
    def __init__(self, batch_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Administrar Archivos en Lote")
        self.resize(500, 400)
        self.setStyleSheet(HUB_WINDOW_STYLE)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        self.original_files = list(batch_files)
        self.current_files = list(batch_files)
        
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Label
        lbl = QLabel(f"Archivos listos para procesar ({len(self.current_files)}):")
        lbl.setStyleSheet("color: white; font-weight: bold; font-size: 12pt;")
        layout.addWidget(lbl)
        
        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2b2b36;
                color: white;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 5px;
                font-size: 11pt;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3a3a46;
            }
            QListWidget::item:selected {
                background-color: #5d5dff;
                border-radius: 4px;
            }
        """)
        self.update_list()
        layout.addWidget(self.list_widget)
        
        # Tip
        tip = QLabel("Consejo: Mantén presionado Ctrl o Shift para seleccionar múltiples archivos.")
        tip.setStyleSheet("color: #aaa; font-size: 9pt;")
        layout.addWidget(tip)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.remove_btn = QPushButton("Quitar Seleccionados")
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4d;
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #ff6666; }
            QPushButton:pressed { background-color: #cc0000; }
        """)
        self.remove_btn.clicked.connect(self.remove_selected)
        btn_layout.addWidget(self.remove_btn)
        
        btn_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                border-radius: 6px;
                padding: 10px;
            }
            QPushButton:hover { background-color: #555; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)
        
        self.accept_btn = QPushButton("Guardar Cambios")
        self.accept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.accept_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.accept_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.accept_btn)
        
        layout.addLayout(btn_layout)

    def update_list(self):
        self.list_widget.clear()
        for f in self.current_files:
            item = QListWidgetItem(os.path.basename(f))
            item.setData(Qt.ItemDataRole.UserRole, f)
            self.list_widget.addItem(item)

    def remove_selected(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            if file_path in self.current_files:
                self.current_files.remove(file_path)
                
        self.update_list()
        
    def get_files(self):
        return self.current_files
