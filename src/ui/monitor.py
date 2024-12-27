from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout
from PyQt6.QtCore import QTimer

from ..core.cpu_manager import CPUManager
from .components import CoreControls, GlobalControls, AMDParamsDialog

class CPUMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPU Monitor")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QGridLayout(self.central_widget)

        self.cpu_manager = CPUManager()
        self.setup_ui()
        self.setup_timer()

    def cleanup(self):
        """Cleanup resources before exit"""
        print("Stopping CPU monitor...")
        if hasattr(self, 'timer'):
            self.timer.stop()
        # Reset any active cores to default governor if needed
        # Add any other cleanup needed

    def setup_ui(self):
        available_preferences = None
        if self.cpu_manager.amd_pstate_active:
            available_preferences = self.cpu_manager.get_cpu_info(0).get(
                "energy_performance_available_preferences", "").split()

        self.global_controls = GlobalControls(
            self.layout,
            self.cpu_manager.available_governors,
            available_preferences
        )

        if self.cpu_manager.amd_pstate_active:
            self.global_controls.amd_params_button.clicked.connect(self.show_amd_params)

        self.global_controls.all_cores_checkbox.stateChanged.connect(self.toggle_all_cores)
        self.global_controls.all_gov_combo.currentIndexChanged.connect(
            lambda: self.update_all_governors(self.global_controls.all_gov_combo.currentText())
        )

        if available_preferences:
            self.global_controls.all_epp_combo.currentIndexChanged.connect(
                lambda: self.update_all_epp(self.global_controls.all_epp_combo.currentText())
            )

        self.core_controls = []
        for i in range(self.cpu_manager.cpu_cores):
            controls = CoreControls(
                i, self.layout, i + 2,
                self.cpu_manager.available_governors,
                available_preferences
            )
            controls.gov_combo.currentIndexChanged.connect(
                lambda _, core_id=i: self.update_governor(core_id)
            )
            if available_preferences:
                controls.epp_combo.currentIndexChanged.connect(
                    lambda _, core_id=i: self.update_epp(core_id)
                )
            self.core_controls.append(controls)

    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_cpu_info)
        self.update_timer_interval()
        self.timer.start()

    def update_timer_interval(self):
        try:
            interval = float(self.global_controls.refresh_entry.text()) * 1000
            self.timer.setInterval(int(interval))
        except ValueError:
            self.global_controls.refresh_entry.setText("1.0")
            self.timer.setInterval(1000)

    def update_cpu_info(self):
        for i, controls in enumerate(self.core_controls):
            info = self.cpu_manager.get_cpu_info(i)
            controls.update_info(info)
            if i == 0 and self.cpu_manager.amd_pstate_active:
                # Update global EPP preferences based on core 0's available preferences
                available_preferences = info.get('energy_performance_available_preferences', '').split()
                self.global_controls.update_epp_preferences(available_preferences)

    def show_amd_params(self):
        params = self.cpu_manager.get_cpu_info(0)
        dialog = AMDParamsDialog(params, self)
        dialog.exec()

    def toggle_all_cores(self, state):
        for controls in self.core_controls:
            controls.checkbox.setChecked(state)

    def update_governor(self, core_id):
        controls = self.core_controls[core_id]
        new_governor = controls.gov_combo.currentText()
        if self.cpu_manager.update_governor(core_id, new_governor):
            # Force an immediate update of the UI after governor change
            info = self.cpu_manager.get_cpu_info(core_id)
            controls.update_info(info)
            if core_id == 0 and self.cpu_manager.amd_pstate_active:
                # Update global EPP preferences based on core 0's available preferences
                available_preferences = info.get('energy_performance_available_preferences', '').split()
                self.global_controls.update_epp_preferences(available_preferences)

    def update_epp(self, core_id):
        controls = self.core_controls[core_id]
        if controls.epp_combo:
            new_epp = controls.epp_combo.currentText()
            self.cpu_manager.update_epp(core_id, new_epp)

    def update_all_governors(self, new_governor):
        selected_cores = [
            i for i, controls in enumerate(self.core_controls)
            if controls.checkbox.isChecked()
        ]
        if self.cpu_manager.update_all_governors(new_governor, selected_cores):
            # Force an immediate update of the UI after governor change
            self.update_cpu_info()

    def update_all_epp(self, new_epp):
        selected_cores = [
            i for i, controls in enumerate(self.core_controls)
            if controls.checkbox.isChecked()
        ]
        self.cpu_manager.update_all_epp(new_epp, selected_cores) 