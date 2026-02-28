from abc import ABC, abstractmethod
import frida


class DeviceManager(ABC):
    def __init__(self, log_callback=None):
        self.device = None
        self.log = log_callback or print
        self.frida_server_path = ""
    
    @abstractmethod
    def check_device_connect(self) -> bool:
        """Check if device is connected"""
        pass
    
    @abstractmethod
    def connect_device(self, **kwargs) -> bool:
        """Connect to device (USB, Local, etc.)"""
        pass
    
    def connect_remote_device(self, host):
        """Connect to remote device via network"""
        try:
            device_manager = frida.get_device_manager()
            self.device = device_manager.add_remote_device(host)
            self.log(f"Connected to remote device: {host}")
            return True
        except Exception as e:
            self.log(f"Failed to connect to remote device: {str(e)}", error=True)
            return False
    
    @abstractmethod
    def start_frida_server(self, **kwargs) -> bool:
        """Start frida-server on the device"""
        pass
    
    @abstractmethod
    def stop_frida_server(self) -> bool:
        """Stop frida-server on the device"""
        pass
    
    @abstractmethod
    def check_frida_status(self, silent=False) -> bool:
        """Check if frida-server is running"""
        pass
    
    def get_applications(self):
        """Get list of applications on the device"""
        if not self.device:
            return []
        
        try:
            apps = self.device.enumerate_applications()
            return apps
        except Exception as e:
            self.log(f"Error listing applications: {str(e)}", error=True)
            return []
    
    def spawn_application(self, package_name):
        """Spawn an application"""
        if not self.device:
            raise Exception("No device connected")
        
        pid = self.device.spawn([package_name])
        return pid
    
    def resume_application(self, pid):
        """Resume a spawned application"""
        if not self.device:
            raise Exception("No device connected")
        
        self.device.resume(pid)
    
    def attach_to_process(self, pid):
        """Attach to a process"""
        if not self.device:
            raise Exception("No device connected")
        
        session = self.device.attach(pid)
        return session