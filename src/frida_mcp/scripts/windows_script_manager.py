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
        self.load_script_from_file("windows_base_utils.js")
        self.open_script = self.builder.build()

    def reset_script(self) -> Dict[str, Any]:
        self.name = []
        self.builder = ScriptBuilder()
        self.load_script_from_file("windows_base_utils.js")
        self.open_script = self.builder.build()
        return {'error': None, 'data': self.open_script}

    def load_monitor_api(self, module_name: str, api_name: str) -> Dict[str, Any]:
        """加载API监控脚本"""
        this_script_filename = "monitor_api.js"
        return self.load_script_from_file(
            this_script_filename,
            module_name=module_name,
            api_name=api_name
        )

    def load_monitor_registry(
            self, api_name:str, registry_path: str = ""
    ) -> Dict[str, Any]:
        """
        加载注册表监控脚本

        Args:
            api_name: 要监控的注册表API名称 (如 RegOpenKeyExW, RegSetValueExW, RegQueryValueExW 等)
            registry_path: 要监控的注册表路径关键字 可以为空

        Returns:

        """
        this_script_base_name = "monitor_registry.js"
        if this_script_base_name not in self.name:
            self.load_script_from_file(this_script_base_name)
        this_script_filename = "monitor_registry_api.js"
        return self.load_script_from_file(
            this_script_filename,
            api_name=api_name,
            registry_path=registry_path
        )

    def load_monitor_file(self, api_name:str, file_path: str) -> Dict[str, Any]:
        """
        加载文件监控脚本

        Args:
            api_name: 要监控的文件API名称 (如 CreateFileW, WriteFile, ReadFile 等)
            file_path: 要监控的文件路径关键字（可以为空，监控所有路径）

        Returns:

        """
        this_script_base_name = "monitor_file.js"
        if this_script_base_name not in self.name:
            self.load_script_from_file(this_script_base_name)
        this_script_filename = "monitor_file_api.js"
        return self.load_script_from_file(
            this_script_filename,
            api_name=api_name,
            file_path=file_path
        )

    def fast_load_all_monitor_file(self) -> Dict[str, Any]:
        """
        加载所有文件监控 API 脚本，可能造成极大量的 log 信息，请谨慎使用
        Returns:

        """
        this_script_filename = "monitor_file_all.js"
        return self.load_script_from_file(
            this_script_filename,
        )


if __name__ == '__main__':
    a = WindowsScriptManager()
    print(a.get_available_scripts())
