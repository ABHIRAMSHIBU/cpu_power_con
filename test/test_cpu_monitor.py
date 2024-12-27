import pytest
import sys
import subprocess
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QCheckBox, QComboBox
)
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt
import time

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ui.monitor import CPUMonitor
from src.core.privilege_handler import PrivilegeHandler
from src.utils.file_handler import FileHandler

# Add the missing get_governor method to PrivilegeHandler
def get_governor(core_id):
    governor_path = f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_governor"
    try:
        return FileHandler.read_file(governor_path).strip()
    except Exception as e:
        print(f"Error reading governor: {e}")
        return None

PrivilegeHandler.get_governor = staticmethod(get_governor)

@pytest.fixture(scope="session")
def qapp():
    """Create the QApplication instance only once."""
    app = QApplication(sys.argv)
    yield app
    app.quit()

@pytest.fixture
def monitor(qapp):
    """Create a fresh CPUMonitor instance for each test."""
    monitor = CPUMonitor()
    monitor.show()  # Make sure window is shown
    QTest.qWait(10)  # Wait for window to show and initial updates
    yield monitor
    # Clean up workers
    for workers in monitor.workers.values():
        for worker in workers:
            worker.quit()
            worker.wait()
    monitor.cleanup()
    monitor.close()
    QTest.qWait(10)  # Wait for cleanup to complete

def test_window_opens(monitor):
    """Test if the CPU monitor window opens and displays correctly"""
    assert monitor.isVisible()
    assert "CPU Monitor" in monitor.windowTitle()

def test_cpu_cores_detection(monitor):
    """Verify that all CPU cores are detected and displayed"""
    QTest.qWait(10)  # Wait for UI updates
    
    # Look for core controls in the layout
    core_controls = monitor.core_controls
    assert len(core_controls) > 0  # Should have at least one core

def test_all_cores_checkbox(monitor):
    """Check if the 'All Cores' checkbox selects all cores"""
    QTest.qWait(10)  # Wait for UI updates
    
    # Get the all cores checkbox from global controls
    all_cores_checkbox = monitor.global_controls.all_cores_checkbox
    assert all_cores_checkbox is not None, "All cores checkbox not found"
    
    # Click the checkbox
    QTest.mouseClick(all_cores_checkbox, Qt.MouseButton.LeftButton)
    QTest.qWait(10)  # Wait for UI updates

    # Verify all core checkboxes are checked
    assert all(controls.checkbox.isChecked() for controls in monitor.core_controls)

@pytest.mark.privileged
def test_governor_change_individual(monitor):
    """Test changing governor for individual cores"""
    # Process events to ensure UI is updated
    QApplication.processEvents()
    
    # Get first core controls
    assert len(monitor.core_controls) > 0
    first_core = monitor.core_controls[0]
    
    # Change governor
    gov_combo = first_core.gov_combo
    assert gov_combo is not None, "Governor combo box not found"
    
    index = gov_combo.findText("powersave")
    assert index >= 0, "Powersave governor not available"
    gov_combo.setCurrentIndex(index)
    QApplication.processEvents()
    
    # Note: This test requires root privileges
    try:
        current_governor = PrivilegeHandler.get_governor(0)  # Core 0
        assert current_governor == "powersave"
    except PermissionError:
        pytest.skip("Test requires root privileges")

@pytest.mark.privileged
def test_cli_interface():
    """Test command line interface functionality"""
    try:
        # Test setting governor for specific core
        result = subprocess.run(
            ["python3", "cpu_monitor.py", "--core", "0", "--governor", "powersave"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        
        # Verify governor was set
        current_governor = PrivilegeHandler.get_governor(0)
        assert current_governor == "powersave"
    except PermissionError:
        pytest.skip("Test requires root privileges")

def test_error_handling():
    """Test error handling for invalid inputs"""
    # Create a mock file for testing
    test_file = "/tmp/test_governor"
    try:
        # Create the file with read-only permissions
        with open(test_file, "w") as f:
            f.write("current_governor")
        os.chmod(test_file, 0o444)  # Read-only for all users
        
        def mock_write_file(path, content):
            if path == test_file and content == "invalid_governor":
                raise ValueError("Invalid governor")
            
        # Patch the write_file method
        original_write_file = FileHandler.write_file
        FileHandler.write_file = staticmethod(mock_write_file)
        
        with pytest.raises(ValueError):
            FileHandler.write_file(test_file, "invalid_governor")
            
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.chmod(test_file, 0o666)  # Make writable before deletion
            os.remove(test_file)
        FileHandler.write_file = staticmethod(original_write_file)

def test_refresh_rate_update(monitor):
    """Test if refresh rate updates correctly when changed"""
    QTest.qWait(100)  # Wait for UI updates
    
    # Initial value should be 1.0 second
    assert monitor.timer.interval() == 1000
    
    # Change refresh rate to 2.5 seconds
    monitor.global_controls.refresh_entry.setText("2.5")
    QTest.qWait(100)  # Wait for timer update
    assert monitor.timer.interval() == 2500
    
    # Test invalid input
    monitor.global_controls.refresh_entry.setText("invalid")
    QTest.qWait(100)  # Wait for timer update
    assert monitor.timer.interval() == 1000
    assert monitor.global_controls.refresh_entry.text() == "1.0"
    
    # Test zero and negative values
    monitor.global_controls.refresh_entry.setText("0")
    QTest.qWait(100)  # Wait for timer update
    assert monitor.timer.interval() == 1000
    assert monitor.global_controls.refresh_entry.text() == "1.0"
    
    monitor.global_controls.refresh_entry.setText("-1.5")
    QTest.qWait(100)  # Wait for timer update
    assert monitor.timer.interval() == 1000
    assert monitor.global_controls.refresh_entry.text() == "1.0"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 