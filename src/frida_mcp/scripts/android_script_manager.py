"""
Android平台专用脚本管理器
"""

from pathlib import Path
from typing import Optional, Dict, Any

from scripts.scripts_manager import ScriptManager, JSFileLoader, ScriptBuilder


class AndroidJSFileLoader(JSFileLoader):
    """Android平台专用JS文件加载器"""
    
    def __init__(self, scripts_dir: Optional[str] = None):
        """初始化Android专用JS文件加载器"""
        if scripts_dir:
            super().__init__(scripts_dir)
        else:
            # 默认使用android目录下的js子目录
            super().__init__(str(Path(__file__).parent / "android-js"))

class AndroidScriptManager(ScriptManager):
    """Android平台专用脚本管理器"""
    
    def __init__(self, scripts_dir: Optional[str] = None):
        """初始化Android专用脚本管理器"""
        super().__init__(scripts_dir)
        # 替换为Android专用文件加载器
        self.file_loader = AndroidJSFileLoader(scripts_dir)
        self.builder = ScriptBuilder()
        self.open_script = self.builder.build()
    
    def load_activity_hook(self, package_name: str, activity_name: str) -> Dict[str, Any]:
        """加载Activity生命周期Hook脚本"""
        return self.load_script_from_file(
            "activity_hook.js",
            package_name=package_name,
            activity_name=activity_name
        )
    
    def load_broadcast_hook(self, package_name: str, action: str) -> Dict[str, Any]:
        """加载广播接收器Hook脚本"""
        return self.load_script_from_file(
            "broadcast_hook.js",
            package_name=package_name,
            action=action
        )
    
    def load_service_hook(self, package_name: str, service_name: str) -> Dict[str, Any]:
        """加载服务Hook脚本"""
        return self.load_script_from_file(
            "service_hook.js",
            package_name=package_name,
            service_name=service_name
        )
    
    def load_shared_preferences_hook(self, package_name: str, pref_name: str) -> Dict[str, Any]:
        """加载SharedPreferences Hook脚本"""
        return self.load_script_from_file(
            "shared_prefs_hook.js",
            package_name=package_name,
            pref_name=pref_name
        )
    
    def load_ssl_pinning_bypass(self) -> Dict[str, Any]:
        """加载SSL证书固定绕过脚本"""
        return self.load_script_from_file("ssl_pinning_bypass.js")
    
    def load_root_detection_bypass(self) -> Dict[str, Any]:
        """加载Root检测绕过脚本"""
        return self.load_script_from_file("root_detection_bypass.js")
    
    def load_frida_detection_bypass(self) -> Dict[str, Any]:
        """加载Frida检测绕过脚本"""
        return self.load_script_from_file("frida_detection_bypass.js")
    
    def get_android_specific_scripts(self) -> Dict[str, Any]:
        """获取Android平台专用脚本列表"""
        return self.file_loader.get_available_scripts()