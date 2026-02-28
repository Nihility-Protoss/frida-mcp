import subprocess
import time
import frida
from src.frida_mcp.util.device_manager import DeviceManager

class AndroidDeviceManager(DeviceManager):
    def __init__(self, log_callback=None):
        super().__init__(log_callback)
        self.frida_server_path = "/data/local/tmp/frida-server"

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

    def setup_port_forward(self, port="27042"):
        """Setup ADB port forwarding"""
        if not self.check_device_connect():
            return False
        
        try:
            # Remove existing port forwarding
            subprocess.run(["adb", "forward", "--remove-all"], capture_output=True)
            
            # Setup new port forwarding
            result = subprocess.run(
                ["adb", "forward", f"tcp:{port}", f"tcp:{port}"],
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

    def connect_device(self, port="27042", **kwargs) -> bool:
        """Connect to Android USB device via Frida"""
        try:
            # Setup port forwarding first
            if self.setup_port_forward(port):
                time.sleep(1)
            
            try:
                # Try direct USB connection first
                self.device = frida.get_usb_device(timeout=5)
                self.log(f"Connected to USB device: {self.device.name}")
                return True
            except:
                # If direct USB fails, try via forwarded port
                self.log("Direct USB connection failed, trying via forwarded port...")
                device_manager = frida.get_device_manager()
                self.device = device_manager.add_remote_device(f"127.0.0.1:{port}")
                self.log(f"Connected via forwarded port: 127.0.0.1:{port}")
                return True
                
        except Exception as e:
            self.log(f"Failed to connect: {str(e)}", error=True)
            self.log("Tip: Make sure frida-server is running on device", error=True)
            return False

    def start_frida_server(self, server_path=None, port="27042", **kwargs) -> bool:
        """Start frida-server on the Android device"""
        if not self.check_device_connect():
            return False
        
        if server_path:
            self.frida_server_path = server_path
        
        self.log(f"Starting frida-server at {self.frida_server_path}...")
        
        # Auto setup port forwarding
        self.setup_port_forward(port)
        
        # Kill existing frida-server processes
        subprocess.run(["adb", "shell", "su", "-c", "pkill", "-f", "frida"], capture_output=True)
        subprocess.run(["adb", "shell", "su", "-c", "pkill", "-f", self.frida_server_path.split('/')[-1]], capture_output=True)
        time.sleep(1)
        
        # First check if file exists and set permissions
        try:
            # Check if file exists
            check_result = subprocess.run(
                ["adb", "shell", "su", "-c", f"ls -la {self.frida_server_path}"],
                capture_output=True,
                text=True
            )
            
            if "No such file" in check_result.stderr or "No such file" in check_result.stdout:
                self.log(f"File not found: {self.frida_server_path}", error=True)
                self.log("Please check the path and ensure frida-server is pushed to device", error=True)
                return False
            
            # Set execute permission
            subprocess.run(
                ["adb", "shell", "su", "-c", f"chmod 755 {self.frida_server_path}"],
                capture_output=True
            )
            
            # Start frida-server with different methods based on path
            if "/tmp" in self.frida_server_path or "/data/local/tmp" in self.frida_server_path:
                cmd = f"{self.frida_server_path} -D"
            else:
                cmd = f"cd {'/'.join(self.frida_server_path.split('/')[:-1])} && ./{self.frida_server_path.split('/')[-1]} -D"
            
            # Start in background
            start_result = subprocess.run(
                ["adb", "shell"],
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
                    ["adb", "shell", "su", "-c", f"daemonize {self.frida_server_path}"],
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
        
        try:
            # Kill by process name patterns
            subprocess.run(["adb", "shell", "su", "-c", "pkill", "-f", "frida"], capture_output=True)
            subprocess.run(["adb", "shell", "su", "-c", "pkill", "-f", self.frida_server_path.split('/')[-1]], capture_output=True)
            
            self.log("Frida server stopped")
            return True
            
        except Exception as e:
            self.log(f"Error stopping frida server: {str(e)}", error=True)
            return False

    def check_frida_status(self, silent=False) -> bool:
        """Check if frida-server is running on Android"""
        if not self.check_device_connect():
            return False
        
        server_name = self.frida_server_path.split('/')[-1]
        
        try:
            result = subprocess.run(
                ["adb", "shell", "ps", "-A"],
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
            subprocess.run(["adb", "shell", "su", "-c", "pkill", "-f", "frida"], capture_output=True)
            time.sleep(1)
            
            # Execute the custom command
            result = subprocess.run(
                ["adb", "shell"],
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