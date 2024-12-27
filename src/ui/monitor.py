from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout
from PyQt6.QtCore import QTimer

from ..core.cpu_manager import CPUManager
from .components import CoreControls, GlobalControls, AMDParamsDialog
from ..utils.workers import FrequencyWorker, GovernorWorker, AMDPstateWorker

class CPUMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPU Monitor")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QGridLayout(self.central_widget)

        self.cpu_manager = CPUManager()
        self.setup_ui()
        self.setup_workers()
        self.setup_timer()
        
        # Do an initial update
        self.update_cpu_info()

    def cleanup(self):
        """Cleanup resources before exit"""
        print("Stopping CPU monitor...")
        if hasattr(self, 'timer'):
            self.timer.stop()
        
        # Stop all workers and wait for them to finish
        if hasattr(self, 'workers'):
            for workers in self.workers.values():
                for worker in workers:
                    worker.quit()
                    worker.wait()

    def setup_workers(self):
        self.workers = {
            'frequency': [],
            'governor': [],
            'amd_pstate': []
        }
        
        for i in range(self.cpu_manager.cpu_cores):
            # Frequency worker
            freq_worker = FrequencyWorker(i)
            freq_worker.finished.connect(
                lambda freq, core_id=i: self.core_controls[core_id].update_frequency(freq)
            )
            freq_worker.error.connect(
                lambda err, core_id=i: print(f"Error reading frequency for core {core_id}: {err}")
            )
            self.workers['frequency'].append(freq_worker)
            
            # Governor worker
            gov_worker = GovernorWorker(i)
            gov_worker.finished.connect(
                lambda gov, core_id=i: self.core_controls[core_id].update_governor(gov)
            )
            gov_worker.error.connect(
                lambda err, core_id=i: print(f"Error reading governor for core {core_id}: {err}")
            )
            self.workers['governor'].append(gov_worker)
            
            # AMD P-state worker if needed
            if self.cpu_manager.amd_pstate_active:
                pstate_worker = AMDPstateWorker(i)
                pstate_worker.finished.connect(
                    lambda params, core_id=i: self.core_controls[core_id].update_amd_params(params)
                )
                pstate_worker.error.connect(
                    lambda err, core_id=i: print(f"Error reading AMD P-state for core {core_id}: {err}")
                )
                self.workers['amd_pstate'].append(pstate_worker)

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

        # Connect refresh rate text box to update timer
        self.global_controls.refresh_entry.textChanged.connect(self.update_timer_interval)

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
            value = float(self.global_controls.refresh_entry.text())
            if value <= 0:
                raise ValueError("Refresh rate must be positive")
            self.timer.setInterval(int(value * 1000))
        except ValueError:
            self.global_controls.refresh_entry.setText("1.0")
            self.timer.setInterval(1000)

    def update_cpu_info(self):
        # Start all workers if they're not already running
        for worker_type in self.workers.values():
            for worker in worker_type:
                if not worker.isRunning():
                    worker.start()
                    worker.wait()  # Wait for worker to finish before starting next one

    def show_amd_params(self):
        if self.cpu_manager.amd_pstate_active and self.workers['amd_pstate']:
            worker = self.workers['amd_pstate'][0]  # Use core 0's worker
            worker.finished.connect(self._show_amd_params_dialog)
            worker.start()
    
    def _show_amd_params_dialog(self, params):
        dialog = AMDParamsDialog(params, self)
        # Disconnect the signal to avoid memory leaks
        self.workers['amd_pstate'][0].finished.disconnect(self._show_amd_params_dialog)
        dialog.exec()

    def toggle_all_cores(self, state):
        for controls in self.core_controls:
            controls.checkbox.setChecked(state)

    def update_governor(self, core_id):
        controls = self.core_controls[core_id]
        new_governor = controls.gov_combo.currentText()
        if self.cpu_manager.update_governor(core_id, new_governor):
            # Force an immediate update of the UI after governor change
            governor = self.cpu_manager.get_cpu_governor(core_id)
            controls.update_governor(governor)
            
            # Update AMD P-state params if needed
            if core_id == 0 and self.cpu_manager.amd_pstate_active:
                params = self.cpu_manager.get_amd_pstate_params(core_id)
                self.global_controls.update_epp_preferences(
                    params.get('energy_performance_available_preferences', '').split()
                )

    def update_epp(self, core_id):
        controls = self.core_controls[core_id]
        if controls.epp_combo:
            new_epp = controls.epp_combo.currentText()
            if self.cpu_manager.update_epp(core_id, new_epp):
                # Force an immediate update of AMD P-state params
                params = self.cpu_manager.get_amd_pstate_params(core_id)
                controls.update_amd_params(params)

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