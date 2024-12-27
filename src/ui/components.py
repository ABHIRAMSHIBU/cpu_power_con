from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QGridLayout, QComboBox,
    QPushButton, QDialog, QVBoxLayout, QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt
from ..utils.file_handler import FileHandler

class AMDParamsDialog(QDialog):
    def __init__(self, params, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AMD P-State Parameters")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        text_display = QTextEdit()
        text_display.setReadOnly(True)
        
        formatted_text = "AMD P-State Driver Parameters:\n\n"
        for param, value in params.items():
            formatted_text += f"{param}: {value}\n"
        
        text_display.setText(formatted_text)
        layout.addWidget(text_display)
        self.setLayout(layout)

class CoreControls:
    def __init__(self, core_id, layout, row, available_governors, available_preferences=None):
        self.core_id = core_id
        self.checkbox = QCheckBox(f"Core {core_id}")
        layout.addWidget(self.checkbox, row, 0, alignment=Qt.AlignmentFlag.AlignLeft)

        self.freq_label = QLabel("Frequency: N/A")
        layout.addWidget(self.freq_label, row, 1, alignment=Qt.AlignmentFlag.AlignLeft)

        self.gov_label = QLabel("Governor: N/A")
        layout.addWidget(self.gov_label, row, 2, alignment=Qt.AlignmentFlag.AlignLeft)

        self.gov_combo = QComboBox()
        self.gov_combo.addItems(available_governors)
        layout.addWidget(self.gov_combo, row, 3, alignment=Qt.AlignmentFlag.AlignLeft)

        if available_preferences:
            self.epp_label = QLabel("EPP: N/A")
            layout.addWidget(self.epp_label, row, 4, alignment=Qt.AlignmentFlag.AlignLeft)

            self.epp_combo = QComboBox()
            self.epp_combo.addItems(available_preferences)
            layout.addWidget(self.epp_combo, row, 5, alignment=Qt.AlignmentFlag.AlignLeft)
        else:
            self.epp_label = None
            self.epp_combo = None

    def update_frequency(self, freq):
        try:
            self.freq_label.setText(f"Frequency: {int(freq) // 1000 if freq.isdigit() else 'N/A'} MHz")
        except (ValueError, AttributeError):
            self.freq_label.setText("Frequency: N/A")

    def update_governor(self, governor):
        self.gov_label.setText(f"Governor: {governor}")
        if governor in [self.gov_combo.itemText(i) for i in range(self.gov_combo.count())]:
            self.gov_combo.setCurrentText(governor)

    def update_amd_params(self, params):
        if self.epp_combo and 'energy_performance_preference' in params:
            epp = params.get('energy_performance_preference', 'N/A')
            self.epp_label.setText(f"EPP: {epp}")
            available_preferences = params.get('energy_performance_available_preferences', '').split()
            if available_preferences:
                current_items = [self.epp_combo.itemText(i) for i in range(self.epp_combo.count())]
                if available_preferences != current_items:
                    self.epp_combo.clear()
                    self.epp_combo.addItems(available_preferences)
            if epp in [self.epp_combo.itemText(i) for i in range(self.epp_combo.count())]:
                self.epp_combo.setCurrentText(epp)

class GlobalControls:
    def __init__(self, layout, available_governors, available_preferences=None):
        self.refresh_label = QLabel("Refresh Speed (seconds):")
        layout.addWidget(self.refresh_label, 0, 0, alignment=Qt.AlignmentFlag.AlignRight)

        self.refresh_entry = QLineEdit("1.0")
        layout.addWidget(self.refresh_entry, 0, 1, alignment=Qt.AlignmentFlag.AlignLeft)

        if FileHandler.is_amd_pstate():
            self.amd_label = QLabel("AMD P-State Driver Active")
            layout.addWidget(self.amd_label, 0, 2, alignment=Qt.AlignmentFlag.AlignLeft)

            self.amd_params_button = QPushButton("Show AMD P-State Parameters")
            layout.addWidget(self.amd_params_button, 0, 3, alignment=Qt.AlignmentFlag.AlignLeft)

        self.all_cores_checkbox = QCheckBox("All Cores")
        layout.addWidget(self.all_cores_checkbox, 1, 0, alignment=Qt.AlignmentFlag.AlignLeft)

        self.all_gov_combo = QComboBox()
        self.all_gov_combo.addItems(available_governors)
        layout.addWidget(self.all_gov_combo, 1, 2, alignment=Qt.AlignmentFlag.AlignLeft)

        if available_preferences:
            self.all_epp_combo = QComboBox()
            self.all_epp_combo.addItems(available_preferences)
            layout.addWidget(self.all_epp_combo, 1, 3, alignment=Qt.AlignmentFlag.AlignLeft)
        else:
            self.all_epp_combo = None

    def update_epp_preferences(self, available_preferences):
        if self.all_epp_combo and available_preferences:
            current_items = [self.all_epp_combo.itemText(i) for i in range(self.all_epp_combo.count())]
            if available_preferences != current_items:
                self.all_epp_combo.clear()
                self.all_epp_combo.addItems(available_preferences) 