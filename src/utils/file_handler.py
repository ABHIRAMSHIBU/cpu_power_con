import os

class FileHandler:
    @staticmethod
    def read_file(file_path):
        try:
            with open(file_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
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
        cpuinfo = FileHandler.read_file("/proc/cpuinfo")
        return "AMD" in cpuinfo if cpuinfo != "N/A" else False

    @staticmethod
    def is_amd_pstate():
        driver = FileHandler.read_file("/sys/devices/system/cpu/cpu0/cpufreq/scaling_driver")
        return "amd-pstate" in driver if driver != "N/A" else False

    @staticmethod
    def get_amd_pstate_params(core_id):
        base_path = f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/"
        params = {}
        
        parameter_files = [
            "energy_performance_preference",
            "energy_performance_available_preferences",
            "scaling_driver",
            "amd_pstate_highest_perf",
            "amd_pstate_lowest_perf"
        ]
        
        for param in parameter_files:
            params[param] = FileHandler.read_file(f"{base_path}{param}")
        
        return params

    @staticmethod
    def get_max_freq(core_id):
        return FileHandler.read_file(f"/sys/devices/system/cpu/cpu{core_id}/cpufreq/scaling_max_freq") 