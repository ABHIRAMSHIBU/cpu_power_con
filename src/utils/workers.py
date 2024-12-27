from PyQt6.QtCore import QThread, pyqtSignal
from .file_handler import FileHandler

class FrequencyWorker(QThread):
    finished = pyqtSignal(str)  # frequency
    error = pyqtSignal(str)  # error message
    
    def __init__(self, core_id):
        super().__init__()
        self.core_id = core_id
        
    def run(self):
        try:
            freq = FileHandler.get_cpu_frequency(self.core_id)
            self.finished.emit(freq)
        except Exception as e:
            self.error.emit(str(e))

class GovernorWorker(QThread):
    finished = pyqtSignal(str)  # governor
    error = pyqtSignal(str)  # error message
    
    def __init__(self, core_id):
        super().__init__()
        self.core_id = core_id
        
    def run(self):
        try:
            governor = FileHandler.get_cpu_governor(self.core_id)
            self.finished.emit(governor)
        except Exception as e:
            self.error.emit(str(e))

class AMDPstateWorker(QThread):
    finished = pyqtSignal(dict)  # params
    error = pyqtSignal(str)  # error message
    
    def __init__(self, core_id):
        super().__init__()
        self.core_id = core_id
        
    def run(self):
        try:
            params = FileHandler.get_amd_pstate_params(self.core_id)
            self.finished.emit(params)
        except Exception as e:
            self.error.emit(str(e)) 