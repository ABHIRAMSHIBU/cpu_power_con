#!/usr/bin/env python3
import sys
import os
import argparse
from src.core.privilege_handler import PrivilegeHandler
from src.ui.monitor import CPUMonitor
from src.ui.tui import CPUMonitorTUI
from src.utils.signal_handler import SignalHandler
from PyQt6.QtWidgets import QApplication, QMessageBox, QMainWindow, QWidget, QGridLayout, QTableWidget, QTableWidgetItem, QHBoxLayout, QLabel, QSpinBox, QPushButton
from PyQt6.QtCore import Qt, QTimer
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
        self.setGeometry(100, 100, 1000, 600)
        self.refresh_period = 5000  # Default refresh period in milliseconds
        self.is_paused = False
        self.all_processes = []  # Store all processes
        self.visible_range = (0, 0)  # Track visible range
        self.row_height = 30  # Approximate height of each row

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)

        # Create control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        self.refresh_label = QLabel("Refresh Period (ms):")
        self.refresh_input = QSpinBox()
        self.refresh_input.setRange(1000, 10000)  # Increased minimum to 1 second
        self.refresh_input.setValue(self.refresh_period)
        self.refresh_input.valueChanged.connect(self.update_refresh_period)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self.toggle_pause)
        
        control_layout.addWidget(self.refresh_label)
        control_layout.addWidget(self.refresh_input)
        control_layout.addWidget(self.pause_button)
        control_layout.addStretch()
        
        layout.addWidget(control_panel, 0, 0)

        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["PID", "Process Name", "Core", "CPU %", "Memory %"])
        self.table.verticalScrollBar().valueChanged.connect(self.handle_scroll)
        self.table.verticalHeader().setDefaultSectionSize(self.row_height)
        layout.addWidget(self.table, 1, 0)

        # Initialize process CPU tracking
        self.prev_cpu_times = {}
        
        # Set up timer for auto-refresh
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_processes)
        self.timer.start(self.refresh_period)

        self.load_processes()

    def calculate_visible_range(self):
        scrollbar = self.table.verticalScrollBar()
        viewport_height = self.table.viewport().height()
        scroll_position = scrollbar.value()
        
        # Calculate visible rows
        start_row = max(0, scroll_position // self.row_height - 5)  # Add 5 rows buffer above
        visible_rows = viewport_height // self.row_height + 10  # Add 5 rows buffer below
        end_row = start_row + visible_rows
        
        return start_row, end_row

    def handle_scroll(self, value):
        if not self.is_paused:
            self.update_visible_processes()

    def update_visible_processes(self):
        if not self.all_processes:
            return

        start_row, end_row = self.calculate_visible_range()
        if (start_row, end_row) == self.visible_range:
            return

        self.visible_range = (start_row, end_row)
        visible_processes = self.all_processes[start_row:end_row]
        
        self.update_table_content(visible_processes, start_row)

    def update_table_content(self, processes, start_row):
        if not processes:
            return

        self.table.setRowCount(len(self.all_processes))  # Keep total row count
        
        for row, (pid, name, core, cpu, mem) in enumerate(processes, start=start_row):
            # Create items with proper sorting
            pid_item = QTableWidgetItem()
            pid_item.setData(Qt.ItemDataRole.DisplayRole, int(pid))
            
            name_item = QTableWidgetItem(name)
            
            core_item = QTableWidgetItem()
            core_item.setData(Qt.ItemDataRole.DisplayRole, int(core))
            
            cpu_item = QTableWidgetItem()
            cpu_item.setData(Qt.ItemDataRole.DisplayRole, float(cpu))
            cpu_item.setText(f"{cpu:.1f}%")
            
            mem_item = QTableWidgetItem()
            mem_item.setData(Qt.ItemDataRole.DisplayRole, float(mem))
            mem_item.setText(f"{mem:.1f}%")
            
            self.table.setItem(row, 0, pid_item)
            self.table.setItem(row, 1, name_item)
            self.table.setItem(row, 2, core_item)
            self.table.setItem(row, 3, cpu_item)
            self.table.setItem(row, 4, mem_item)

    def toggle_pause(self, checked):
        self.is_paused = checked
        if checked:
            self.pause_button.setText("Resume")
            self.timer.stop()
        else:
            self.pause_button.setText("Pause")
            self.timer.start(self.refresh_period)
            self.load_processes()  # Immediate refresh when resuming

    def update_refresh_period(self, value):
        self.refresh_period = value
        if not self.is_paused:
            self.timer.setInterval(value)

    def calculate_cpu_percent(self, pid):
        try:
            proc = psutil.Process(pid)
            # Get current CPU times
            current_time = proc.cpu_times()
            current_total = sum(current_time)
            
            # Get previous CPU times
            if pid in self.prev_cpu_times:
                prev_total = self.prev_cpu_times[pid]
                # Calculate CPU usage
                cpu_percent = ((current_total - prev_total) / (self.refresh_period / 1000)) * 100
            else:
                cpu_percent = 0
                
            # Store current total for next calculation
            self.prev_cpu_times[pid] = current_total
            
            return min(cpu_percent, 100.0)  # Cap at 100%
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    def load_processes(self):
        try:
            if self.is_paused:
                return

            processes = []
            # Get all processes at once
            for proc in psutil.process_iter(['pid', 'name', 'cpu_affinity', 'memory_percent']):
                try:
                    info = proc.info
                    pid = info['pid']
                    
                    # Calculate CPU percentage more efficiently
                    cpu_percent = self.calculate_cpu_percent(pid)
                    
                    # Get memory percentage
                    memory_percent = info['memory_percent']
                    
                    # Add entry for each core
                    for core_id in info['cpu_affinity']:
                        processes.append((
                            pid,
                            info['name'],
                            core_id,
                            cpu_percent,
                            memory_percent
                        ))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Store all processes but only display visible ones
            self.all_processes = sorted(processes, key=lambda x: x[0])  # Sort by PID initially
            self.update_visible_processes()
            
            # Enable sorting after initial load
            if not self.table.isSortingEnabled():
                self.table.setSortingEnabled(True)
                self.table.resizeColumnsToContents()

        except Exception as e:
            print(f"Error updating process list: {e}")

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
