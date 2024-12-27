#!/usr/bin/env python3
import sys
import os
import argparse
from src.core.privilege_handler import PrivilegeHandler
from src.ui.monitor import CPUMonitor
from src.utils.signal_handler import SignalHandler
from PyQt6.QtWidgets import QApplication, QMessageBox

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

def main():
    parser = argparse.ArgumentParser(description="CPU Monitor")
    parser.add_argument("--core", type=int, help="Core ID to set governor for")
    parser.add_argument("--governor", type=str, help="Governor to set")
    parser.add_argument("--max-freq", type=str, help="Max frequency to set")
    parser.add_argument("--epp", type=str, help="Energy Performance Preference to set")
    args = parser.parse_args()

    if args.core is not None:
        PrivilegeHandler.apply_settings(
            args.core,
            max_freq=args.max_freq,
            governor=args.governor,
            epp=args.epp
        )
    else:
        app = QApplication(sys.argv)
        
        if not check_root_access():
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setText("Root privileges required")
            msg.setInformativeText("CPU Monitor requires root privileges to read and modify CPU settings.\nPlease run the application with sudo.")
            msg.setWindowTitle("Permission Error")
            msg.exec()
            return 1
            
        monitor = CPUMonitor()
        # Setup signal handler with cleanup callback
        signal_handler = SignalHandler(app, cleanup_callback=monitor.cleanup)
        monitor.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()
