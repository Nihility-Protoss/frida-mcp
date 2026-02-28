from abc import ABC, abstractmethod
from src.frida_mcp.config.default_config import FridaConfig


class FridaServerManager(ABC):
    """
    Abstract base class for managing the Frida server process on different platforms.
    Focuses solely on starting, stopping, and checking the status of the server.
    """
    def __init__(self, config: FridaConfig, log_callback=None):
        self.log = log_callback or print
        self.config = config
    
    @abstractmethod
    def check_device_connect(self) -> bool:
        """Check if the physical/virtual device is accessible (e.g., via ADB or local)"""
        pass
    
    @abstractmethod
    def start_frida_server(self, **kwargs) -> bool:
        """Start the frida-server on the device/system"""
        pass
    
    @abstractmethod
    def stop_frida_server(self) -> bool:
        """Stop the frida-server on the device/system"""
        pass
    
    @abstractmethod
    def check_frida_status(self, silent=False) -> bool:
        """Check if the frida-server is currently running"""
        pass
