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
        super().__init__(scripts_dir)
        self.scripts_dir.append(Path(__file__).parent / "windows-js")


class WindowsScriptManager(ScriptManager):
    """Windows平台专用脚本管理器"""

    def __init__(self, scripts_dir: Optional[str] = None):
        """初始化Windows专用脚本管理器"""
        super().__init__(scripts_dir)
        self.file_loader = WindowsJSFileLoader(scripts_dir)
        self.builder = ScriptBuilder()
        self.open_script = self.builder.build()

    def load_monitor_api(self, module_name: str, api_name: str) -> Dict[str, Any]:
        """加载API监控脚本"""
        this_script_filename = "monitor_api.js"
        return self.load_script_from_file(
            this_script_filename,
            module_name=module_name,
            api_name=api_name
        )

    def load_monitor_registry(self, registry_path: str) -> Dict[str, Any]:
        """加载注册表监控脚本"""
        this_script_filename = "monitor_registry.js"
        return self.load_script_from_file(
            this_script_filename,
            registry_path=registry_path
        )

    def load_monitor_file(self, file_path: str) -> Dict[str, Any]:
        """加载文件监控脚本"""
        this_script_filename = "monitor_file.js"
        return self.load_script_from_file(
            this_script_filename,
            file_path=file_path
        )


if __name__ == '__main__':
    a = WindowsScriptManager()
    print(a.get_available_scripts())
