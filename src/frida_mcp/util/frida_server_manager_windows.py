import subprocess
import os

from config.default_config import FridaConfig
from .frida_server_manager import FridaServerManager


class WindowsServerManager(FridaServerManager):
    """
    Implementation of FridaServerManager for local Windows systems.
    """

    def __init__(self, config: FridaConfig, log_callback=None):
        super().__init__(config, log_callback)

    def _get_full_server_path(self) -> str:
        """Get full path to frida-server on Windows with proper path separators"""
        path = self.config.server_path
        name = self._get_server_name()

        if not path:
            return name

        # Normalize slashes for Windows
        path = os.path.normpath(path)

        if path.endswith(name):
            return path

        return os.path.join(path, name)

    def _get_server_name(self) -> str:
        """Get the filename of frida-server for Windows"""
        name = self.config.server_name or "frida-server.exe"
        if not name.lower().endswith(".exe"):
            name += ".exe"
        return name

    def check_device_connect(self) -> bool:
        """Windows local system is always 'connected'"""
        return True

    def start_frida_server(self, **kwargs) -> bool:
        """Start frida-server on Windows if not already running"""
        server_name = self._get_server_name()
        if self.check_frida_status(silent=True):
            self.log(f"Frida server ({server_name}) is already running")
            return True

        server_path = self._get_full_server_path()

        self.log(f"Starting frida-server at: {server_path}")
        try:
            # Start frida-server as a background process
            subprocess.Popen(
                [server_path],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            self.log(f"Failed to start frida-server: {str(e)}", error=True)
            return False

    def stop_frida_server(self) -> bool:
        """Stop local frida-server using taskkill"""
        server_name = self._get_server_name()
        self.log(f"Stopping {server_name}...")
        try:
            subprocess.run(["taskkill", "/F", "/IM", server_name], capture_output=True)
            return True
        except Exception:
            return False

    def check_frida_status(self, silent=False) -> bool:
        """Check if frida-server is running using tasklist (supports multiple name patterns)"""
        try:
            # Get all processes once for a more flexible check
            result = subprocess.run(["tasklist"], capture_output=True, text=True)
            output = result.stdout.lower()

            # Patterns to check
            patterns = ["frida-server.exe", "frida-server", "frida_server.exe", "frida_server"]
            if self.config.server_name:
                config_name = self.config.server_name.lower()
                patterns.append(config_name)
                if not config_name.endswith(".exe"):
                    patterns.append(f"{config_name}.exe")

            # Find any match
            found_name = None
            for p in patterns:
                if p in output:
                    found_name = p
                    break

            is_running = found_name is not None
            if not silent:
                if is_running:
                    self.log(f"Frida server is running (matched: {found_name})")
                else:
                    self.log("Frida server is not running")
            return is_running
        except Exception as e:
            if not silent:
                self.log(f"Error checking status: {str(e)}", error=True)
            return False
