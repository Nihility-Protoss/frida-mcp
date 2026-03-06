import subprocess
import time

from config.default_config import FridaConfig
from .frida_server_manager import FridaServerManager


class AndroidServerManager(FridaServerManager):
    """
    Implementation of FridaServerManager for Android devices via ADB.
    """

    def __init__(self, config: FridaConfig, log_callback=None):
        super().__init__(config, log_callback)
        # Separate default settings for path and server name
        if not self.config.server_path:
            self.config.server_path = "/data/local/tmp"

        if not self.config.server_name:
            self.config.server_name = "frida-server"

    def check_device_connect(self) -> bool:
        """Check if ADB is available and a device is connected"""
        try:
            cmd = [self.config.adb_path, "devices"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if "device" in result.stdout and not result.stdout.strip().endswith("devices"):
                return True
            else:
                self.log(f"No Android device connected via {self.config.adb_path}", error=True)
                return False
        except FileNotFoundError:
            self.log(f"{self.config.adb_path} not found in PATH", error=True)
            return False

    def setup_port_forward(self):
        """Setup ADB port forwarding using config port"""
        if not self.check_device_connect():
            return False

        port = str(self.config.server_port)
        try:
            # Remove existing port forwarding
            subprocess.run([self.config.adb_path, "forward", "--remove-all"], capture_output=True)

            # Setup new port forwarding
            result = subprocess.run(
                [self.config.adb_path, "forward", f"tcp:{port}", f"tcp:{port}"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.log(f"Port forwarding established: localhost:{port} -> device:{port}")
                return True
            else:
                self.log(f"Failed to setup port forwarding: {result.stderr}", error=True)
                return False

        except Exception as e:
            self.log(f"Error setting up port forwarding: {str(e)}", error=True)
            return False

    def _get_full_server_path(self) -> str:
        """Get full path to frida-server on device"""
        path = self.config.server_path
        name = self.config.server_name

        if not name:
            return path

        if path.endswith(name):
            return path

        if path.endswith('/'):
            return f"{path}{name}"
        return f"{path}/{name}"

    def _get_server_name(self) -> str:
        """Get the filename of frida-server"""
        if self.config.server_name:
            return self.config.server_name
        return self.config.server_path.split('/')[-1]

    def start_frida_server(self, **kwargs) -> bool:
        """Start frida-server on the Android device using config"""
        if not self.check_device_connect():
            return False

        server_path = self._get_full_server_path()
        server_name = self._get_server_name()

        self.log(f"Starting frida-server at {server_path}...")

        # Auto setup port forwarding
        self.setup_port_forward()

        # Kill existing frida-server processes
        subprocess.run([self.config.adb_path, "shell", "su", "-c", "pkill", "-f", "frida"], capture_output=True)
        subprocess.run([self.config.adb_path, "shell", "su", "-c", "pkill", "-f", server_name], capture_output=True)
        time.sleep(1)

        # First check if file exists and set permissions
        try:
            # Check if file exists
            check_result = subprocess.run(
                [self.config.adb_path, "shell", "su", "-c", f"ls -la {server_path}"],
                capture_output=True,
                text=True
            )

            if "No such file" in check_result.stderr or "No such file" in check_result.stdout:
                self.log(f"File not found: {server_path}", error=True)
                self.log("Please check the path and ensure frida-server is pushed to device", error=True)
                return False

            # Set execute permission
            subprocess.run(
                [self.config.adb_path, "shell", "su", "-c", f"chmod 755 {server_path}"],
                capture_output=True
            )

            # Start frida-server with different methods based on path
            if "/tmp" in server_path or "/data/local/tmp" in server_path:
                cmd = f"{server_path} -D"
            else:
                cmd = f"cd {'/'.join(server_path.split('/')[:-1])} && ./{server_path.split('/')[-1]} -D"

            # Start in background
            start_result = subprocess.run(
                [self.config.adb_path, "shell"],
                input=f"su -c '{cmd} &'\nexit\n",
                capture_output=True,
                text=True,
                timeout=3
            )

            time.sleep(0.5)  # Wait for server to start

            # Check if server is running
            if self.check_frida_status(silent=True):
                self.log("Frida server started successfully")
                return True
            else:
                # Try alternative method
                self.log("Trying alternative start method...")

                # Try daemonize approach
                subprocess.run(
                    [self.config.adb_path, "shell", "su", "-c", f"daemonize {server_path}"],
                    capture_output=True,
                    timeout=2
                )

                time.sleep(2)
                if self.check_frida_status(silent=True):
                    self.log("Frida server started successfully (daemonize)")
                    return True
                else:
                    self.log("Failed to start frida server", error=True)
                    if start_result.stdout:
                        self.log(f"Debug info: {start_result.stdout}", error=True)
                    if start_result.stderr:
                        self.log(f"Error: {start_result.stderr}", error=True)
                    return False

        except subprocess.TimeoutExpired:
            time.sleep(2)
            if self.check_frida_status(silent=True):
                self.log("Frida server started successfully")
                return True
            else:
                self.log("Server may be starting, please check status", error=True)
                return False

        except Exception as e:
            self.log(f"Error starting frida server: {str(e)}", error=True)
            return False

    def stop_frida_server(self) -> bool:
        """Stop frida-server on the Android device"""
        if not self.check_device_connect():
            return False

        self.log("Stopping frida-server...")
        server_name = self._get_server_name()

        try:
            # Kill by process name patterns
            subprocess.run([self.config.adb_path, "shell", "su", "-c", "pkill", "-f", "frida"], capture_output=True)
            subprocess.run([self.config.adb_path, "shell", "su", "-c", "pkill", "-f", server_name], capture_output=True)

            self.log("Frida server stopped")
            return True

        except Exception as e:
            self.log(f"Error stopping frida server: {str(e)}", error=True)
            return False

    def check_frida_status(self, silent=False) -> bool:
        """Check if frida-server is running on Android"""
        if not self.check_device_connect():
            return False

        server_name = self._get_server_name()

        try:
            result = subprocess.run(
                [self.config.adb_path, "shell", "ps", "-A"],
                capture_output=True,
                text=True
            )

            # Check for frida or custom server name
            is_running = False
            if "frida" in result.stdout.lower() or server_name in result.stdout:
                is_running = True

            if is_running:
                if not silent:
                    self.log("Frida server is running")
                return True
            else:
                if not silent:
                    self.log("Frida server is not running")
                return False

        except Exception as e:
            if not silent:
                self.log(f"Error checking frida status: {str(e)}", error=True)
            return False

    def execute_custom_command(self, command):
        """Execute custom command to start frida-server on Android"""
        if not self.check_device_connect():
            return False

        self.log(f"Executing manual command: {command}")

        try:
            # First kill existing processes
            subprocess.run([self.config.adb_path, "shell", "su", "-c", "pkill", "-f", "frida"], capture_output=True)
            time.sleep(1)

            # Execute the custom command
            result = subprocess.run(
                [self.config.adb_path, "shell"],
                input=f"{command}\nexit\n",
                capture_output=True,
                text=True,
                timeout=5
            )

            self.log("Command executed, checking status...")
            time.sleep(2)

            if self.check_frida_status(silent=True):
                self.log("Frida server started successfully via manual command")
                return True
            else:
                self.log("Server not detected, output:", error=True)
                if result.stdout:
                    self.log(result.stdout)
                if result.stderr:
                    self.log(result.stderr, error=True)
                return False

        except subprocess.TimeoutExpired:
            self.log("Command timeout - server may be running in background")
            time.sleep(2)
            if self.check_frida_status(silent=True):
                self.log("Frida server started successfully")
                return True
            return False

        except Exception as e:
            self.log(f"Error executing command: {str(e)}", error=True)
            return False
