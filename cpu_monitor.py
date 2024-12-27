#!/usr/bin/env python3
import sys
import argparse
from src.core.privilege_handler import PrivilegeHandler
from src.ui.monitor import CPUMonitor
from src.utils.signal_handler import SignalHandler
from PyQt6.QtWidgets import QApplication

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
        monitor = CPUMonitor()
        # Setup signal handler with cleanup callback
        signal_handler = SignalHandler(app, cleanup_callback=monitor.cleanup)
        monitor.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()
