import frida
import subprocess
from src.frida_mcp.util.device_manager import DeviceManager


class WindowsDeviceManager(DeviceManager):
    def __init__(self, log_callback=None):
        super().__init__(log_callback)

    def check_device_connect(self) -> bool:
        """Windows local system is always 'connected'"""
        return True

    def connect_device(self, **kwargs) -> bool:
        """Connect to local Windows device"""
        try:
            self.device = frida.get_local_device()
            self.log(f"Connected to local Windows device: {self.device.name}")
            return True
        except Exception as e:
            self.log(f"Failed to connect to local device: {str(e)}", error=True)
            return False

    def start_frida_server(self, **kwargs) -> bool:
        """
        On Windows, frida-server is often not needed for local attachment.
        This could be implemented to start frida-server.exe if remote access is needed.
        """
        self.log("Local Windows attachment doesn't require frida-server by default.")
        return True

    def stop_frida_server(self) -> bool:
        """Stop local frida-server if it was started"""
        self.log("Stopping local frida-server (if any)...")
        try:
            subprocess.run(["taskkill", "/F", "/IM", "frida-server.exe"], capture_output=True)
            return True
        except:
            return False

    def check_frida_status(self, silent=False) -> bool:
        """Check if frida-server.exe is running locally"""
        try:
            result = subprocess.run(["tasklist"], capture_output=True, text=True)
            if "frida-server.exe" in result.stdout:
                if not silent:
                    self.log("Frida server is running locally")
                return True
            else:
                if not silent:
                    self.log("Frida server is not running locally")
                return False
        except Exception as e:
            if not silent:
                self.log(f"Error checking frida status: {str(e)}", error=True)
            return False
