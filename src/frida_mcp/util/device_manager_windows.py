from src.frida_mcp.util.device_manager import DeviceManager


class WindowsDeviceManager(DeviceManager):
    def __init__(self, log_callback=None):
        super().__init__(log_callback)

    def check_device_connect(self) -> bool:
        """Windows Device Connect check"""
        return True
