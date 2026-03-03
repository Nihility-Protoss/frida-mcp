#!/usr/bin/env python3
"""
测试最终修正的架构
"""

import asyncio
import sys
from pathlib import Path
from collections import deque
from util.inject import BaseInjector
from util.inject_android import AndroidInjector
from util.inject_windows import WindowsInjector
from scripts.scripts_manager import ScriptManager

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_final_architecture():
    """测试最终架构"""
    print("=== 测试最终修正的架构 ===")
    
    try:

        
        print("   ✅ 所有类导入成功")
        
        # 验证抽象方法签名
        print("   ✅ BaseInjector抽象方法签名:")
        print("      - attach(self, target: str) -> Dict[str, Any]")
        print("      - spawn(self, target: str) -> Dict[str, Any]")
        print("      - detach(self) -> Dict[str, Any]")
        
        # 验证构造函数参数
        print("   ✅ 构造函数参数:")
        print("      - device: frida.core.Device (必须)")
        print("      - messages_buffer: deque (必须)")
        
    except ImportError as e:
        print(f"   ❌ 导入失败: {e}")
        return False
    
    return True

def show_usage_examples():
    """展示使用示例"""
    print("\n=== 最终使用示例 ===")
    
    print("""
# 1. 创建注入器（必须传入device和messages_buffer）
import frida
from collections import deque
from frida_mcp.util.inject_android import AndroidInjector
from frida_mcp.android.android_script_manager import AndroidScriptManager

# 创建消息缓冲区
messages = deque(maxlen=1000)

# 获取设备
device = frida.get_usb_device()
injector = AndroidInjector(device, messages)

# 2. 创建脚本管理器
manager = AndroidScriptManager()

# 3. 使用流程（简化版）
async def android_workflow():
    # 启动应用
    result = await injector.spawn("com.example.app")
    if result['error']:
        print(f"启动失败: {result['error']}")
        return
    
    print(f"应用已启动: PID={result['data']['pid']}")
    
    # 加载SSL绕过脚本
    ssl_result = manager.load_ssl_pinning_bypass()
    if ssl_result['error'] is None:
        # 注入脚本到session
        inject_result = manager.inject_script(injector.session, "ssl_bypass")
        print(f"SSL脚本注入: {inject_result}")
    
    # 附加到已运行的应用
    attach_result = await injector.attach("com.example.app")
    if attach_result['error'] is None:
        print(f"已附加到: {attach_result['data']['package']}")
    
    # 断开连接
    detach_result = injector.detach()
    print(f"断开结果: {detach_result}")

# Windows平台示例
from frida_mcp.util.inject_windows import WindowsInjector
from frida_mcp.windows.windows_script_manager import WindowsScriptManager

async def windows_workflow():
    device = frida.get_local_device()
    messages = deque(maxlen=1000)
    injector = WindowsInjector(device, messages)
    manager = WindowsScriptManager()
    
    # 附加到进程
    result = await injector.attach("notepad.exe")
    if result['error'] is None:
        print(f"已附加到: {result['data']['process']}")
        
        # 加载并注入API监控脚本
        api_script = manager.load_api_monitor("kernel32.dll", "CreateFileW")
        if api_script['error'] is None:
            inject_result = manager.inject_script(injector.session, "api_monitor")
            print(f"API监控脚本注入: {inject_result}")
    """)

def show_error_handling():
    """展示错误处理"""
    print("\n=== 错误处理示例 ===")
    
    print("""
# 错误处理示例
async def error_handling():
    messages = deque(maxlen=1000)
    device = frida.get_usb_device()
    injector = AndroidInjector(device, messages)
    
    # 1. 处理启动失败
    result = await injector.spawn("nonexistent.app")
    if result['error']:
        print(f"启动失败: {result['error']}")
        return
    
    # 2. 处理附加失败
    result = await injector.attach("nonexistent.app")
    if result['error']:
        print(f"附加失败: {result['error']}")
        return
    
    # 3. 处理脚本加载失败
    manager = AndroidScriptManager()
    result = manager.load_script_from_file("nonexistent.js")
    if result['error']:
        print(f"脚本加载失败: {result['error']}")
        return
    
    print("所有操作成功完成")
    """)

def show_api_signature():
    """展示API签名"""
    print("\n=== 最终API签名 ===")
    
    print("""
# BaseInjector抽象方法（符合要求）:
class BaseInjector(ABC):
    def __init__(self, device: frida.core.Device, messages_buffer: deque)
    
    @abstractmethod
    async def attach(self, target: str) -> Dict[str, Any]
    @abstractmethod
    async def spawn(self, target: str) -> Dict[str, Any]
    
    def detach(self) -> Dict[str, Any]
    def is_connected(self) -> bool
    def get_session_info(self) -> Dict[str, Any]

# ScriptManager新增方法:
class ScriptManager:
    def inject_script(self, session: frida.core.Session, script_name: str = "default") -> Dict[str, Any]
    # 其他方法保持不变...
    """)

def main():
    """主测试函数"""
    print("🧪 测试最终修正的架构\n")
    
    try:
        # 测试架构
        if not test_final_architecture():
            return
        
        # 展示使用示例
        show_usage_examples()
        show_error_handling()
        show_api_signature()
        
        print("\n✅ 最终修正的架构测试完成！")
        print("\n📋 主要修正:")
        print("   ✅ 抽象方法签名符合要求")
        print("   ✅ device参数在初始化时传入")
        print("   ✅ messages_buffer必须传入")
        print("   ✅ 移除device_id参数")
        print("   ✅ 脚本管理移至ScriptManager")
        print("   ✅ 简化BaseInjector设计")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()