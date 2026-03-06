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
        super().__init__(scripts_dir)
        self.scripts_dir.append(Path(__file__).parent / "android-js")


class AndroidScriptManager(ScriptManager):
    """Android平台专用脚本管理器"""

    def __init__(self, scripts_dir: Optional[str] = None):
        """初始化Android专用脚本管理器"""
        super().__init__(scripts_dir)
        self.file_loader = AndroidJSFileLoader(scripts_dir)
        self.builder = ScriptBuilder()
        self.open_script = self.builder.build()

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
            hook_addr_list=str(hook_addr_list)
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

    def load_hook_net_libssl(self) -> Dict[str, Any]:
        this_script_filename = "hook_net_libssl.so.js"
        if this_script_filename not in self.get_available_scripts().get("data"):
            return {
                'error': f"Not {this_script_filename} in AndroidScriptManager, "
                         f"call get_script_list check list",
                'data': None
            }
        return self.load_script_from_file(
            this_script_filename
        )

    def load_hook_clone(self, anti_so_name_tag: str = "DexHelper") -> Dict[str, Any]:
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

    def load_hook_activity(self, package_name: str, activity_name: str) -> Dict[str, Any]:
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
