
import time
import frida
import subprocess

from util.device_manager import DeviceManager

class AndroidDeviceManager(DeviceManager):
    def __init__(self, log_callback=None):
        super().__init__(log_callback)

    def check_device_connect(self) -> bool:
        """Check if ADB is available and a device is connected"""
        try:
            result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
            if "device" in result.stdout and not result.stdout.strip().endswith("devices"):
                return True
            else:
                self.log("No Android device connected via ADB", error=True)
                return False
        except FileNotFoundError:
            self.log("ADB not found in PATH", error=True)
            return False