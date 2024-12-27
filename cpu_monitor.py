import sys
import os
import argparse
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QGridLayout, QComboBox, QPushButton, QMainWindow,
    QDialog, QVBoxLayout, QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer

class CPUMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPU Monitor")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QGridLayout(self.central_widget)

        # Refresh speed controls
        self.layout.addWidget(QLabel("Refresh Speed (seconds):"), 0, 0, alignment=Qt.AlignmentFlag.AlignRight)
        self.refresh_speed_entry = QLineEdit("1.0")
        self.layout.addWidget(self.refresh_speed_entry, 0, 1, alignment=Qt.AlignmentFlag.AlignLeft)

        self.cpu_cores = os.cpu_count()
        self.frequency_labels = []
        self.governor_labels = []
        self.governor_comboboxes = []
        self.amd_pstate_active = self.is_amd_pstate()
        self.amd_pstate_labels = []
        self.epp_comboboxes = []

        if self.amd_pstate_active:
            amd_label = QLabel("AMD P-State Driver Active")
            self.layout.addWidget(amd_label, 0, 2, alignment=Qt.AlignmentFlag.AlignLeft)

        self.available_governors = self.get_available_governors()

        # Add this after initializing the layout in __init__
        if self.is_amd_cpu() and self.is_amd_pstate():
            self.amd_params_button = QPushButton("Show AMD P-State Parameters")
            self.amd_params_button.clicked.connect(self.show_amd_params)
            # Add button to the right of the refresh speed
            self.layout.addWidget(self.amd_params_button, 0, 3, 1, 1,
                                alignment=Qt.AlignmentFlag.AlignLeft)

        # Add "All Cores" row
        self.all_cores_checkbox = QCheckBox("All Cores")
        self.all_cores_checkbox.stateChanged.connect(self.toggle_all_cores)
        self.layout.addWidget(self.all_cores_checkbox, 1, 0, alignment=Qt.AlignmentFlag.AlignLeft)

        self.all_gov_combo = QComboBox()
        self.all_gov_combo.addItems(self.available_governors)
        self.all_gov_combo.currentIndexChanged.connect(lambda index: self.update_all_governors(self.all_gov_combo.itemText(index)))
        self.layout.addWidget(self.all_gov_combo, 1, 2, alignment=Qt.AlignmentFlag.AlignLeft)
        self.all_governor_combobox = self.all_gov_combo

        if self.amd_pstate_active:
            all_epp_combo = QComboBox()
            available_preferences = self.get_amd_pstate_parameters().get("energy_performance_available_preferences", "").split()
            all_epp_combo.addItems(available_preferences)
            all_epp_combo.currentIndexChanged.connect(lambda index: self.update_all_epp(all_epp_combo.itemText(index)))
            self.layout.addWidget(all_epp_combo, 1, 3, alignment=Qt.AlignmentFlag.AlignLeft)
            self.all_epp_combobox = all_epp_combo

        self.core_checkboxes = []
        for i in range(self.cpu_cores):
            core_checkbox = QCheckBox(f"Core {i}")
            self.layout.addWidget(core_checkbox, i + 2, 0, alignment=Qt.AlignmentFlag.AlignLeft)
            self.core_checkboxes.append(core_checkbox)

            freq_label = QLabel("Frequency: N/A")
            self.layout.addWidget(freq_label, i + 2, 1, alignment=Qt.AlignmentFlag.AlignLeft)
            self.frequency_labels.append(freq_label)

            gov_label = QLabel("Governor: N/A")
            self.layout.addWidget(gov_label, i + 2, 2, alignment=Qt.AlignmentFlag.AlignLeft)
            self.governor_labels.append(gov_label)

            gov_combo = QComboBox()
            gov_combo.addItems(self.available_governors)
            current_governor = self.get_cpu_governor(i)
            if current_governor in self.available_governors:
                gov_combo.setCurrentText(current_governor)
            self.layout.addWidget(gov_combo, i + 2, 3, alignment=Qt.AlignmentFlag.AlignLeft)
            self.governor_comboboxes.append(gov_combo)
            gov_combo.currentIndexChanged.connect(lambda index, core_id=i: self.update_governor(core_id))

            if self.amd_pstate_active:
                pstate_label = QLabel("EPP: N/A")
                self.layout.addWidget(pstate_label, i + 2, 4, alignment=Qt.AlignmentFlag.AlignLeft)
                self.amd_pstate_labels.append(pstate_label)

                epp_combo = QComboBox()
                available_preferences = self.get_amd_pstate_parameters(i).get("energy_performance_available_preferences", "").split()
                epp_combo.addItems(available_preferences)
                current_epp = self.get_amd_pstate_params(i).get('energy_performance_preference', 'N/A')
                if current_epp in available_preferences:
                    epp_combo.setCurrentText(current_epp)
                epp_combo.currentIndexChanged.connect(self.create_update_epp_handler(i))
                self.layout.addWidget(epp_combo, i + 2, 5, alignment=Qt.AlignmentFlag.AlignLeft)
                self.epp_comboboxes.append(epp_combo)

        self.update_cpu_info()

    def toggle_all_cores(self, state):
        checked = state == Qt.CheckState.Checked
        for checkbox in self.core_checkboxes:
            checkbox.setChecked(checked)

    def is_amd_cpu(self):
        try:
            with open("/proc/cpuinfo") as f:
                return any("AMD" in line for line in f if line.startswith("vendor_id"))
        except FileNotFoundError:
            return False

    def get_amd_pstate_parameters(self, core_num=0):
        params = {}
        base_path = f"/sys/devices/system/cpu/cpu{core_num}/cpufreq/"
        
        # List of important AMD P-State parameters to check
        parameter_files = [
            "energy_performance_preference",
            "energy_performance_available_preferences",
            "scaling_driver",
            "amd_pstate_highest_perf",
            "amd_pstate_lowest_perf"
        ]
        
        for param in parameter_files:
            try:
                with open(f"{base_path}{param}") as f:
                    params[param] = f.read().strip()
            except FileNotFoundError:
                params[param] = "Not available"
        
        return params
    def show_amd_params(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("AMD P-State Parameters")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        
        params = self.get_amd_pstate_parameters()
        
        text_display = QTextEdit()
        text_display.setReadOnly(True)
        formatted_text = "AMD P-State Driver Parameters:\n\n"
        for param, value in params.items():
            formatted_text += f"{param}: {value}\n"
        text_display.setText(formatted_text)
        layout.addWidget(text_display)
        
        dialog.setLayout(layout)
        dialog.exec()

    def apply_epp(self):
        selected_epp = self.epp_dropdown.currentText()
        script_path = os.path.abspath(__file__)
        for i in range(self.cpu_cores):
            subprocess.run(['sudo', sys.executable, script_path,
                            "--core", str(i),
                            "--epp", selected_epp],
                            check=True)
        print(f"EPP set to {selected_epp} for all cores")
        self.update_cpu_info()


    def is_amd_pstate(self):
        try:
            with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver") as f:
                driver = f.read().strip()
                return "amd-pstate" in driver
        except FileNotFoundError:
            return False

    def get_amd_pstate_params(self, core_id):
        params = {}
        try:
            with open(f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/energy_performance_preference") as f:
                params['energy_performance_preference'] = f.read().strip()
        except FileNotFoundError:
            params['energy_performance_preference'] = "N/A"
        return params

    def get_available_governors(self):
        try:
            with open("/sys/devices/system/cpu/cpufreq/policy0/scaling_available_governors") as f:
                governors = f.read().strip().split()
                return governors
        except FileNotFoundError:
            return ["conservative", "ondemand", "userspace", "powersave", "performance", "schedutil"]

    def get_cpu_frequency(self, core_id):
        try:
            with open(f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_cur_freq") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "N/A"

    def get_cpu_governor(self, core_id):
        try:
            with open(f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_governor") as f:
                return f.read().strip()
        except FileNotFoundError:
            return "N/A"

    def update_cpu_info(self):
        for i in range(self.cpu_cores):
            freq = self.get_cpu_frequency(i)
            self.frequency_labels[i].setText(f"Frequency: {int(freq) // 1000 if freq.isdigit() else 'N/A'} MHz")
            governor = self.get_cpu_governor(i)
            self.governor_labels[i].setText(f"Governor: {governor}")
            if self.amd_pstate_active:
                params = self.get_amd_pstate_params(i)
                self.amd_pstate_labels[i].setText(f"EPP: {params.get('energy_performance_preference', 'N/A')}")
                available_preferences = self.get_amd_pstate_parameters(i).get("energy_performance_available_preferences", "").split()
                current_epp = self.get_amd_pstate_params(i).get('energy_performance_preference', 'N/A')
                if current_epp in available_preferences and i < len(self.epp_comboboxes):
                    self.epp_comboboxes[i].setCurrentText(current_epp)
            
            current_governor = self.get_cpu_governor(i)
            if current_governor in self.available_governors and i < len(self.governor_comboboxes):
                self.governor_comboboxes[i].setCurrentText(current_governor)
        try:
            refresh_rate = float(self.refresh_speed_entry.text()) * 1000
        except ValueError:
            refresh_rate = 1000  # Default to 1 second if input is invalid
            self.refresh_speed_entry.setText("1.0")
        self.timer =  QTimer()
        self.timer.timeout.connect(self.update_cpu_info)
        self.timer.start(int(refresh_rate))


    def create_update_epp_handler(self, core_id):
        def handler():
            if core_id >= 0:
                self.update_epp(core_id)
        return handler

    def create_update_all_governors_handler(self):
        return lambda index: self.update_all_governors(self.all_governor_combobox.itemText(index))

    def create_update_all_epp_handler(self):
        return lambda index: self.update_all_epp(self.all_epp_combobox.itemText(index))

    def update_epp(self, core_id):
        if core_id < len(self.epp_comboboxes):
            selected_epp = self.epp_comboboxes[core_id].currentText()
            script_path = os.path.abspath(__file__)
            subprocess.run(['sudo', sys.executable, script_path,
                            "--core", str(core_id),
                            "--epp", selected_epp],
                            check=True)
            print(f"EPP set to {selected_epp} for core {core_id}")
        else:
            print(f"No EPP combobox found for core {core_id}")
        self.update_cpu_info()

    def update_all_epp(self, new_epp):
        script_path = os.path.abspath(__file__)
        for i in range(self.cpu_cores):
            if self.core_checkboxes[i].isChecked():
                subprocess.run(['sudo', sys.executable, script_path,
                                "--core", str(i),
                                "--epp", new_epp],
                                check=True)
                print(f"EPP set to {new_epp} for core {i}")
        self.update_cpu_info()

    def update_governor(self, core_id):
        new_governor = self.governor_comboboxes[core_id].currentText()
        script_path = os.path.abspath(__file__)
        print(f"Setting governor for core {core_id} to {new_governor}")
        if new_governor == "userspace":
            try:
                with open(f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_max_freq") as f:
                    max_freq = f.read().strip()

                script_path = os.path.abspath(__file__)
                print(f"Running command: ['sudo', {sys.executable}, {script_path}, '--core', {str(core_id)}, '--governor', 'userspace', '--max-freq', {max_freq}]")
                subprocess.run(['sudo', sys.executable, script_path, 
                              "--core", str(core_id),
                              '--governor', "userspace", "--max-freq", max_freq],
                              check=True)
            except FileNotFoundError:
                print(f"Error: Could not find scaling_max_freq for core {core_id}")
                return
            except subprocess.CalledProcessError:
                print(f"Error: Failed to set governor for core {core_id}")
                return
        else:
            print(f"Running command: ['sudo', {sys.executable}, {script_path}, '--core', {str(core_id)}, '--governor', {new_governor}]")
            subprocess.run(['sudo', sys.executable, script_path, 
                            "--core", str(core_id),
                            '--governor', new_governor],
                            check=True)
        # Optionally provide feedback to the user
        print(f"Governor for core {core_id} set to {new_governor}")
        self.governor_labels[core_id].setText(f"Governor: {new_governor}")
        if self.amd_pstate_active:
            available_preferences = self.get_amd_pstate_parameters(core_id).get("energy_performance_available_preferences", "").split()
            current_epp = self.get_amd_pstate_params(core_id).get('energy_performance_preference', 'N/A')
            if current_epp in available_preferences and core_id < len(self.epp_comboboxes):
                self.epp_comboboxes[core_id].clear()
                self.epp_comboboxes[core_id].addItems(available_preferences)
                self.epp_comboboxes[core_id].setCurrentText(current_epp)

    def update_all_governors(self, new_governor):
        script_path = os.path.abspath(__file__)
        for i in range(self.cpu_cores):
            if self.core_checkboxes[i].isChecked():
                if new_governor == "userspace":
                    try:
                        with open(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_max_freq") as f:
                            max_freq = f.read().strip()

                        script_path = os.path.abspath(__file__)
                        subprocess.run(['sudo', sys.executable, script_path, 
                                      "--core", str(i),
                                      '--governor', "userspace", "--max-freq", max_freq],
                                      check=True)
                    except FileNotFoundError:
                        print(f"Error: Could not find scaling_max_freq for core {i}")
                        return
                    except subprocess.CalledProcessError:
                        print(f"Error: Failed to set governor for core {i}")
                        return
                else:
                    subprocess.run(['sudo', sys.executable, script_path, 
                                    "--core", str(i),
                                    '--governor', new_governor],
                                    check=True)
                print(f"Governor for core {i} set to {new_governor}")
                self.governor_labels[i].setText(f"Governor: {new_governor}")
        self.update_cpu_info()

def set_governor_and_max_freq(core_id, max_freq=None, governor=None, epp=None):
    governor_path = f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_governor"
    freq_path = f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/cpufreq_set_freq"
    epp_path = f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/energy_performance_preference"
    try:
        if governor:
            with open(governor_path, 'w') as f:
                f.write(governor)
        if governor == "userspace":
            with open(freq_path, 'w') as f:
                f.write(max_freq)
        if epp:
            with open(epp_path, 'w') as f:
                print(epp)
                f.write(epp)
    except Exception as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CPU Monitor")
    parser.add_argument("--core", type=int, help="Core ID to set governor for")
    parser.add_argument("--governor", type=str, help="Governor to set")
    parser.add_argument("--max-freq", type=str, help="Max frequency to set")
    parser.add_argument("--epp", type=str, help="Energy Performance Preference to set")
    args = parser.parse_args()

    if args.core is not None:
        if args.governor is not None and args.max_freq is not None:
            set_governor_and_max_freq(args.core, governor=args.governor, max_freq=args.max_freq)
        elif args.max_freq is not None:
            set_governor_and_max_freq(args.core, governor="userspace" ,max_freq=args.max_freq)
        elif args.governor is not None:
            set_governor_and_max_freq(args.core, governor=args.governor)
        if args.epp is not None:
            set_governor_and_max_freq(args.core, epp=args.epp)
    else:
        app = QApplication(sys.argv)
        monitor = CPUMonitor()
        monitor.show()
        sys.exit(app.exec())
