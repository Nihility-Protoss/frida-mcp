"""
Android平台专用脚本管理器
"""

from pathlib import Path
from typing import Optional, Dict, Any, List

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
        self.file_loader = AndroidJSFileLoader(scripts_dir)
        self.builder = ScriptBuilder()
        self.open_script = self.builder.build()
    

    def load_broadcast_hook(self, package_name: str, action: str) -> Dict[str, Any]:
        """加载广播接收器Hook脚本"""
        this_script_filename = "broadcast_hook.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in AndroidScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename,
            package_name=package_name,
            action=action
        )
    
    def load_service_hook(self, package_name: str, service_name: str) -> Dict[str, Any]:
        """加载服务Hook脚本"""
        this_script_filename = "service_hook.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in AndroidScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename,
            package_name=package_name,
            service_name=service_name
        )
    
    def load_shared_preferences_hook(self, package_name: str, pref_name: str) -> Dict[str, Any]:
        """加载SharedPreferences Hook脚本"""
        this_script_filename = "shared_prefs_hook.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in AndroidScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename,
            package_name=package_name,
            pref_name=pref_name
        )
    
    def load_ssl_pinning_bypass(self) -> Dict[str, Any]:
        """加载SSL证书固定绕过脚本"""
        this_script_filename = "ssl_pinning_bypass.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in AndroidScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(this_script_filename)
    
    def load_root_detection_bypass(self) -> Dict[str, Any]:
        """加载Root检测绕过脚本"""
        this_script_filename = "root_detection_bypass.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in AndroidScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(this_script_filename)
    
    def load_frida_detection_bypass(self) -> Dict[str, Any]:
        """加载Frida检测绕过脚本"""
        this_script_filename = "frida_detection_bypass.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in AndroidScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(this_script_filename)

    def load_anti_DexHelper(self, hook_addr_list: List[int]) -> Dict[str, Any]:
        this_script_filename = "anti_libDexHelper.so.js"

        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in AndroidScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename,
            hook_addr_list = str(hook_addr_list)
        )

    def load_anti_DexHelper_hook_clone(self) -> Dict[str, Any]:
        this_script_filename = "anti_libDexHelper.so_hook_clone.js"

        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in AndroidScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename
        )

    def load_anti_DexHelper_hook_pthread(self) -> Dict[str, Any]:
        this_script_filename = "anti_libDexHelper.so_hook_pthread_create.js"

        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in AndroidScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename
        )

    def load_hook_clone(self, anti_so_name_tag:str = "DexHelper") -> Dict[str, Any]:
        this_script_filename = "hook_clone.js"

        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in AndroidScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename,
            anti_so_name_tag=anti_so_name_tag
        )

    def load_activity_hook(self, package_name: str, activity_name: str) -> Dict[str, Any]:
        """加载Activity生命周期Hook脚本"""
        this_script_filename = "hook_activity.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in AndroidScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename,
            package_name=package_name,
            activity_name=activity_name
        )


if __name__ == '__main__':
    a = AndroidScriptManager()
    print(a.get_available_scripts())
