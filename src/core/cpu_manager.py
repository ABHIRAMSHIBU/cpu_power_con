import os
from ..utils.file_handler import FileHandler
from .privilege_handler import PrivilegeHandler

class CPUManager:
    def __init__(self):
        self.cpu_cores = os.cpu_count()
        self.amd_pstate_active = FileHandler.is_amd_pstate()
        self.available_governors = FileHandler.get_available_governors()

    def update_governor(self, core_id, new_governor):
        if new_governor == "userspace":
            max_freq = FileHandler.get_max_freq(core_id)
            if max_freq != "N/A":
                return PrivilegeHandler.set_governor_and_freq(core_id, governor=new_governor, max_freq=max_freq)
        else:
            return PrivilegeHandler.set_governor_and_freq(core_id, governor=new_governor)
        return False

    def update_epp(self, core_id, new_epp):
        return PrivilegeHandler.set_governor_and_freq(core_id, epp=new_epp)

    def get_cpu_info(self, core_id):
        info = {
            'frequency': FileHandler.get_cpu_frequency(core_id),
            'governor': FileHandler.get_cpu_governor(core_id),
        }
        
        if self.amd_pstate_active:
            info.update(FileHandler.get_amd_pstate_params(core_id))
        
        return info

    def update_all_governors(self, new_governor, selected_cores):
        success = True
        for core_id in selected_cores:
            if not self.update_governor(core_id, new_governor):
                success = False
        return success

    def update_all_epp(self, new_epp, selected_cores):
        success = True
        for core_id in selected_cores:
            if not self.update_epp(core_id, new_epp):
                success = False
        return success 