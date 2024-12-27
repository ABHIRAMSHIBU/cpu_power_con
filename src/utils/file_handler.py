import os

class FileHandler:
    _is_amd_pstate_cache = None
    _is_amd_cpu_cache = None

    @staticmethod
    def read_file(file_path, suppress_warnings=False):
        if not os.path.exists(file_path):
            if not suppress_warnings:
                print(f"Warning: File not found: {file_path}")
            return "N/A"
            
        if not os.access(file_path, os.R_OK):
            if not suppress_warnings:
                print(f"Error: Permission denied reading {file_path}. Try running with sudo.")
            return "N/A"
            
        try:
            with open(file_path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            if not suppress_warnings:
                print(f"Error reading {file_path}: {e}")
            return "N/A"

    @staticmethod
    def write_file(file_path, content):
        try:
            with open(file_path, 'w') as f:
                f.write(str(content))
            return True
        except Exception as e:
            print(f"Error writing to file {file_path}: {e}")
            return False

    @staticmethod
    def get_cpu_frequency(core_id):
        return FileHandler.read_file(f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_cur_freq")

    @staticmethod
    def get_cpu_governor(core_id):
        return FileHandler.read_file(f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_governor")

    @staticmethod
    def get_available_governors():
        governors = FileHandler.read_file("/sys/devices/system/cpu/cpufreq/policy0/scaling_available_governors")
        if governors != "N/A":
            return governors.split()
        return ["conservative", "ondemand", "userspace", "powersave", "performance", "schedutil"]

    @staticmethod
    def is_amd_cpu():
        if FileHandler._is_amd_cpu_cache is None:
            cpuinfo = FileHandler.read_file("/proc/cpuinfo")
            FileHandler._is_amd_cpu_cache = "AMD" in cpuinfo if cpuinfo != "N/A" else False
        return FileHandler._is_amd_cpu_cache

    @staticmethod
    def is_amd_pstate():
        if FileHandler._is_amd_pstate_cache is None:
            if not FileHandler.is_amd_cpu():
                FileHandler._is_amd_pstate_cache = False
            else:
                driver = FileHandler.read_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver")
                FileHandler._is_amd_pstate_cache = "amd-pstate" in driver if driver != "N/A" else False
        return FileHandler._is_amd_pstate_cache

    @staticmethod
    def get_amd_pstate_params(core_id):
        if not FileHandler.is_amd_pstate():
            return {}
            
        base_path = f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/"
        params = {}
        
        # Core parameters that should always be available
        core_params = [
            "energy_performance_preference",
            "energy_performance_available_preferences",
            "scaling_driver"
        ]
        
        # Optional AMD-specific parameters
        amd_params = [
            "amd_pstate_highest_perf",
            "amd_pstate_lowest_perf"
        ]
        
        # Get core parameters
        for param in core_params:
            params[param] = FileHandler.read_file(f"{base_path}{param}")
            
        # Only try AMD parameters if we confirmed it's an AMD CPU with P-state
        # Suppress warnings for these optional parameters
        for param in amd_params:
            value = FileHandler.read_file(f"{base_path}{param}", suppress_warnings=True)
            if value != "N/A":  # Only add if the file exists and is readable
                params[param] = value
        
        return params

    @staticmethod
    def get_max_freq(core_id):
        return FileHandler.read_file(f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_max_freq") 