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
        self.load_script_from_file("android_base_utils.js")
        self.open_script = self.builder.build()

    def reset_script(self) -> Dict[str, Any]:
        self.name = []
        self.builder = ScriptBuilder()
        self.load_script_from_file("android_base_utils.js")
        self.open_script = self.builder.build()
        return {'error': None, 'data': self.open_script}

    def load_anti_DexHelper(self, hook_addr_list: List[int]) -> Dict[str, Any]:
        this_script_filename = "anti_libDexHelper.so.js"

        return self.load_script_from_file(
            this_script_filename,
            hook_addr_list=str(hook_addr_list)
        )

    def load_anti_DexHelper_hook_clone(self) -> Dict[str, Any]:
        this_script_filename = "anti_libDexHelper.so_hook_clone.js"

        return self.load_script_from_file(
            this_script_filename
        )

    def load_anti_DexHelper_hook_pthread(self) -> Dict[str, Any]:
        this_script_filename = "anti_libDexHelper.so_hook_pthread_create.js"

        return self.load_script_from_file(
            this_script_filename
        )

    def load_hook_net_libssl(self) -> Dict[str, Any]:
        this_script_filename = "hook_net_libssl.so.js"

        return self.load_script_from_file(
            this_script_filename
        )

    def load_hook_clone(self, anti_so_name_tag: str = "DexHelper") -> Dict[str, Any]:
        this_script_filename = "hook_clone.js"

        return self.load_script_from_file(
            this_script_filename,
            anti_so_name_tag=anti_so_name_tag
        )

    def load_hook_activity(self, package_name: str, activity_name: str) -> Dict[str, Any]:
        this_script_filename = "hook_activity.js"

        return self.load_script_from_file(
            this_script_filename,
            package_name=package_name,
            activity_name=activity_name
        )

    def load_hook_crypto(self) -> Dict[str, Any]:
        """加载加密/解密操作Hook脚本
        Hook javax.crypto.Cipher 和 java.security.MessageDigest
        """
        this_script_filename = "hook_crypto.js"

        return self.load_script_from_file(this_script_filename)

    def load_hook_java_common(self, target_key: str = "") -> Dict[str, Any]:
        """加载常用Java类Hook脚本
        Hook Map, StringBuilder, Base64, Dialog, Toast, Snackbar
        
        Args:
            target_key: 监控的 Map key（可选）
        """
        this_script_filename = "hook_java_common.js"

        return self.load_script_from_file(
            this_script_filename,
            target_key=target_key
        )

    def load_hook_native_common(
        self,
        block_so_name: str = "",
        newstringutf_filter: str = "",
        newstringutf_length: int = 0,
        register_target_class: str = ""
    ) -> Dict[str, Any]:
        """加载常用Native层Hook脚本
        Hook SO加载、NewStringUTF、RegisterNatives等
        
        Args:
            block_so_name: 要阻止加载的SO名称
            newstringutf_filter: NewStringUTF过滤字符串
            newstringutf_length: NewStringUTF过滤长度
            register_target_class: 要监控的RegisterNatives目标类
        """
        this_script_filename = "hook_native_common.js"

        return self.load_script_from_file(
            this_script_filename,
            block_so_name=block_so_name,
            newstringutf_filter=newstringutf_filter,
            newstringutf_length=newstringutf_length,
            register_target_class=register_target_class
        )

    def load_hook_dex(self) -> Dict[str, Any]:
        """加载DEX加载监控脚本
        Hook DexClassLoader, PathClassLoader, InMemoryClassLoader
        """
        this_script_filename = "hook_dex.js"

        return self.load_script_from_file(this_script_filename)

    def load_delay_hook(
        self,
        target_so: str = "",
        delay_ms: int = 1000,
        target_function: str = "",
        target_class: str = "",
        target_method: str = ""
    ) -> Dict[str, Any]:
        """加载延迟Hook模板脚本，支持按SO加载或按时间延迟执行Hook
        Args:
            target_so: 等待加载的目标SO名称（为空则使用delay_ms）
            delay_ms: 延迟毫秒数
            target_function: 要Hook的Native函数名
            target_class: 要Hook的Java类名
            target_method: 要Hook的Java方法名
        """
        this_script_filename = "delay_hook.js"

        return self.load_script_from_file(
            this_script_filename,
            target_so=target_so,
            delay_ms=delay_ms,
            target_function=target_function,
            target_class=target_class,
            target_method=target_method
        )


if __name__ == '__main__':
    a = AndroidScriptManager()
    print(a.get_available_scripts())
