import signal
import sys
from typing import Optional
from PyQt6.QtWidgets import QApplication

class SignalHandler:
    def __init__(self, app: QApplication, cleanup_callback: Optional[callable] = None):
        """
        Initialize signal handler
        
        Args:
            app: QApplication instance to quit gracefully
            cleanup_callback: Optional callback to run before exit
        """
        self.app = app
        self.cleanup_callback = cleanup_callback
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup handlers for various signals"""
        # SIGINT (Ctrl+C)
        signal.signal(signal.SIGINT, self._handle_signal)
        # SIGTERM (termination request)
        signal.signal(signal.SIGTERM, self._handle_signal)
        # SIGHUP (terminal closed)
        signal.signal(signal.SIGHUP, self._handle_signal)
        # SIGABRT (abort)
        signal.signal(signal.SIGABRT, self._handle_signal)

    def _handle_signal(self, signum: int, frame):
        """
        Handle received signal
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        print(f"\nReceived signal {signal_name}")
        print("Shutting down gracefully...")
        
        # Run cleanup if provided
        if self.cleanup_callback:
            try:
                self.cleanup_callback()
            except Exception as e:
                print(f"Error during cleanup: {e}")

        # Quit application
        self.app.quit()
        
        # Exit with appropriate code
        if signum == signal.SIGINT:
            sys.exit(130)  # 128 + SIGINT(2)
        else:
            sys.exit(0) 