import subprocess
import sys
import os
from ..utils.file_handler import FileHandler

class PrivilegeHandler:
    @staticmethod
    def set_governor_and_freq(core_id, governor=None, max_freq=None, epp=None):
        script_path = os.path.abspath(sys.argv[0])
        cmd = ['sudo', sys.executable, script_path]
        
        if core_id is not None:
            cmd.extend(['--core', str(core_id)])
        if governor is not None:
            cmd.extend(['--governor', governor])
        if max_freq is not None:
            cmd.extend(['--max-freq', str(max_freq)])
        if epp is not None:
            cmd.extend(['--epp', epp])
            
        try:
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error executing privileged command: {e}")
            return False

    @staticmethod
    def apply_settings(core_id, max_freq=None, governor=None, epp=None):
        governor_path = f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_governor"
        freq_path = f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/cpufreq_set_freq"
        epp_path = f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/energy_performance_preference"

        if governor:
            FileHandler.write_file(governor_path, governor)
        if governor == "userspace" and max_freq:
            FileHandler.write_file(freq_path, max_freq)
        if epp:
            FileHandler.write_file(epp_path, epp) 