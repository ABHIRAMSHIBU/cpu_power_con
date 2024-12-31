#!/usr/bin/env python3
import sys
import os
import argparse
from src.core.privilege_handler import PrivilegeHandler
from src.ui.monitor import CPUMonitor
from src.ui.tui import CPUMonitorTUI
from src.utils.signal_handler import SignalHandler
from PyQt6.QtWidgets import QApplication, QMessageBox, QMainWindow, QWidget, QGridLayout, QTableWidget, QTableWidgetItem
from PyQt6.QtCore import Qt
import psutil

def check_root_access():
    test_file = "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
    try:
        with open(test_file, 'r') as f:
            f.read()
        return True
    except PermissionError:
        return False
    except FileNotFoundError:
        # If the file doesn't exist, we can't determine if we have root access
        return True

class ProcessWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Running Processes")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["PID", "Process Name", "Core"])
        layout.addWidget(self.table, 0, 0)

        self.load_processes()

    def load_processes(self):
        processes = []
        for process in psutil.process_iter(['pid', 'name', 'cpu_affinity']):
            try:
                core_ids = process.info['cpu_affinity']
                for core_id in core_ids:
                    processes.append((process.info['pid'], process.info['name'], core_id))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        self.table.setRowCount(len(processes))
        for row, (pid, name, core) in enumerate(processes):
            self.table.setItem(row, 0, QTableWidgetItem(str(pid)))
            self.table.setItem(row, 1, QTableWidgetItem(name))
            self.table.setItem(row, 2, QTableWidgetItem(str(core)))
        self.table.resizeColumnsToContents()

def main():
    parser = argparse.ArgumentParser(description="CPU Monitor")
    parser.add_argument("--core", type=int, help="Core ID to set governor for")
    parser.add_argument("--governor", type=str, help="Governor to set")
    parser.add_argument("--max-freq", type=str, help="Max frequency to set")
    parser.add_argument("--epp", type=str, help="Energy Performance Preference to set")
    parser.add_argument("--tui", action="store_true", help="Use terminal user interface instead of GUI")
    args = parser.parse_args()

    if args.core is not None:
        PrivilegeHandler.apply_settings(
            args.core,
            max_freq=args.max_freq,
            governor=args.governor,
            epp=args.epp
        )
    else:
        if not check_root_access():
            if args.tui:
                print("Error: Root privileges required. Please run with sudo.")
                return 1
            else:
                app = QApplication(sys.argv)
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setText("Root privileges required")
                msg.setInformativeText("CPU Monitor requires root privileges to read and modify CPU settings.\nPlease run the application with sudo.")
                msg.setWindowTitle("Permission Error")
                msg.exec()
                return 1

        if args.tui:
            monitor = CPUMonitorTUI()
            monitor.start()
        else:
            app = QApplication(sys.argv)
            monitor = CPUMonitor()
            # Setup signal handler with cleanup callback
            signal_handler = SignalHandler(app, cleanup_callback=monitor.cleanup)
            monitor.show()
            sys.exit(app.exec())

if __name__ == "__main__":
    main()
