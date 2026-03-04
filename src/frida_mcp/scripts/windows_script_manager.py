"""
Windows平台专用脚本管理器
"""

from pathlib import Path
from typing import Optional, Dict, Any

from scripts.scripts_manager import ScriptManager, JSFileLoader, ScriptBuilder


class WindowsJSFileLoader(JSFileLoader):
    """Windows平台专用JS文件加载器"""
    
    def __init__(self, scripts_dir: Optional[str] = None):
        """初始化Windows专用JS文件加载器"""
        if scripts_dir:
            super().__init__(scripts_dir)
        else:
            # 默认使用windows目录下的js子目录
            super().__init__(str(Path(__file__).parent / "windows-js"))

class WindowsScriptManager(ScriptManager):
    """Windows平台专用脚本管理器"""
    
    def __init__(self, scripts_dir: Optional[str] = None):
        """初始化Windows专用脚本管理器"""
        super().__init__(scripts_dir)
        self.file_loader = WindowsJSFileLoader(scripts_dir)
        self.builder = ScriptBuilder()
        self.open_script = self.builder.build()
    
    def load_api_monitor(self, module_name: str, api_name: str) -> Dict[str, Any]:
        """加载API监控脚本"""
        this_script_filename = "api_monitor.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in WindowsScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename,
            module_name=module_name,
            api_name=api_name
        )
    
    def load_registry_monitor(self, registry_path: str) -> Dict[str, Any]:
        """加载注册表监控脚本"""
        this_script_filename = "registry_monitor.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in WindowsScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename,
            registry_path=registry_path
        )
    
    def load_file_monitor(self, file_path: str) -> Dict[str, Any]:
        """加载文件监控脚本"""
        this_script_filename = "file_monitor.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in WindowsScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename,
            file_path=file_path
        )
    
    def load_network_monitor(self, port: int) -> Dict[str, Any]:
        """加载网络监控脚本"""
        this_script_filename = "network_monitor.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in WindowsScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename,
            port=str(port)
        )
    
    def load_process_injection(self, target_process: str, dll_path: str) -> Dict[str, Any]:
        """加载进程注入脚本"""
        this_script_filename = "process_injection.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in WindowsScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename,
            target_process=target_process,
            dll_path=dll_path
        )
    
    def load_antivirus_bypass(self) -> Dict[str, Any]:
        """加载杀毒软件绕过脚本"""
        this_script_filename = "antivirus_bypass.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in WindowsScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(this_script_filename)
        
    def load_uac_bypass(self) -> Dict[str, Any]:
        """加载UAC绕过脚本"""
        this_script_filename = "uac_bypass.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in WindowsScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(this_script_filename)

if __name__ == '__main__':
    a = WindowsScriptManager()
    print(a.get_available_scripts())