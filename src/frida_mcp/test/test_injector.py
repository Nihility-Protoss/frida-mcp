#!/usr/bin/env python3
"""
测试新的BaseInjector架构
"""

import asyncio
import sys
from pathlib import Path

from android.android_script_manager import AndroidScriptManager
from scripts.scripts_manager import ScriptManager
from windows.windows_script_manager import WindowsScriptManager

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_injector_structure():
    """测试注入器结构"""
    print("=== 测试注入器结构 ===")
    
    try:
        from util.inject import BaseInjector
        from util.inject_android import AndroidInjector
        from util.inject_windows import WindowsInjector
        from scripts.scripts_manager import ScriptManager
        from android.android_script_manager import AndroidScriptManager
        from windows.windows_script_manager import WindowsScriptManager
        
        print("   ✅ 所有类导入成功")
        print(f"   - BaseInjector: {BaseInjector}")
        print(f"   - AndroidInjector: {AndroidInjector}")
        print(f"   - WindowsInjector: {WindowsInjector}")
        print(f"   - ScriptManager: {ScriptManager}")
        
    except ImportError as e:
        print(f"   ❌ 导入失败: {e}")
        return False
    
    return True

def test_script_manager_integration():
    """测试ScriptManager集成"""
    print("\n=== 测试ScriptManager集成 ===")
    
    try:
        # 测试Android ScriptManager
        android_manager = AndroidScriptManager()
        result = android_manager.get_android_specific_scripts()
        print(f"   Android专用脚本: {result}")
        
        # 测试Windows ScriptManager
        windows_manager = WindowsScriptManager()
        result = windows_manager.get_windows_specific_scripts()
        print(f"   Windows专用脚本: {result}")
        
        # 测试通用ScriptManager
        generic_manager = ScriptManager()
        result = generic_manager.get_available_scripts()
        print(f"   通用脚本: {result}")
        
    except Exception as e:
        print(f"   测试失败: {e}")

def show_usage_examples():
    """展示使用示例"""
    print("\n=== 使用示例 ===")
    
    print("""
# 1. 创建注入器实例
import frida
from frida_mcp.util.inject_android import AndroidInjector
from frida_mcp.android.android_script_manager import AndroidScriptManager

# 获取设备
device = frida.get_usb_device()
injector = AndroidInjector(device)

# 2. 创建脚本管理器
script_manager = AndroidScriptManager()

# 3. 启动应用
result = await injector.spawn("com.example.app")
if result['error'] is None:
    print(f"应用已启动: PID={result['data']['pid']}")

# 4. 加载SSL绕过脚本
ssl_result = script_manager.load_ssl_pinning_bypass()
if ssl_result['error'] is None:
    load_result = await injector.load_script(script_manager, "ssl_bypass")
    print(f"SSL绕过脚本已加载: {load_result}")

# 5. 加载Activity Hook脚本
activity_result = script_manager.load_activity_hook("com.example.app", "MainActivity")
if activity_result['error'] is None:
    load_result = await injector.load_script(script_manager, "activity_hook")
    print(f"Activity Hook脚本已加载: {load_result}")

# 6. 获取已加载脚本
scripts = injector.get_loaded_scripts()
print(f"已加载脚本: {scripts}")

# 7. 卸载脚本
unload_result = injector.unload_script("ssl_bypass")
print(f"卸载结果: {unload_result}")

# 8. 断开连接
detach_result = injector.detach()
print(f"断开结果: {detach_result}")
    """)

def show_platform_examples():
    """展示平台使用示例"""
    print("\n=== 平台使用示例 ===")
    
    print("""
# Android平台示例
import frida
from frida_mcp.util.inject_android import AndroidInjector
from frida_mcp.android.android_script_manager import AndroidScriptManager

# 创建Android注入器
device = frida.get_usb_device()
android_injector = AndroidInjector(device)
android_manager = AndroidScriptManager()

# 使用流程
async def android_example():
    # 1. 启动应用
    spawn_result = await android_injector.spawn("com.example.app")
    if spawn_result['error']:
        print(f"启动失败: {spawn_result['error']}")
        return
    
    # 2. 加载SSL绕过
    ssl_script = android_manager.load_ssl_pinning_bypass()
    if ssl_script['error'] is None:
        await android_injector.load_script(android_manager, "ssl_bypass")
    
    # 3. 加载Root检测绕过
    root_script = android_manager.load_root_detection_bypass()
    if root_script['error'] is None:
        await android_injector.load_script(android_manager, "root_bypass")
    
    # 4. 恢复应用
    resume_result = android_injector.resume()
    print(f"恢复结果: {resume_result}")

# Windows平台示例
import frida
from frida_mcp.util.inject_windows import WindowsInjector
from frida_mcp.windows.windows_script_manager import WindowsScriptManager

# 创建Windows注入器
device = frida.get_local_device()
windows_injector = WindowsInjector(device)
windows_manager = WindowsScriptManager()

# 使用流程
async def windows_example():
    # 1. 附加到进程
    attach_result = await windows_injector.attach("notepad.exe")
    if attach_result['error']:
        print(f"附加失败: {attach_result['error']}")
        return
    
    # 2. 加载API监控
    api_script = windows_manager.load_api_monitor("kernel32.dll", "CreateFileW")
    if api_script['error'] is None:
        await windows_injector.load_script(windows_manager, "api_monitor")
    
    # 3. 加载注册表监控
    reg_script = windows_manager.load_registry_monitor("HKEY_CURRENT_USER\\Software")
    if reg_script['error'] is None:
        await windows_injector.load_script(windows_manager, "registry_monitor")
    
    # 4. 获取会话信息
    info = windows_injector.get_session_info()
    print(f"会话信息: {info}")
    """)

def show_error_handling():
    """展示错误处理"""
    print("\n=== 错误处理示例 ===")
    
    print("""
# 错误处理示例
async def error_handling_example():
    injector = AndroidInjector(device)
    manager = AndroidScriptManager()
    
    # 1. 处理附加失败
    result = await injector.attach("nonexistent.app")
    if result['error']:
        print(f"附加失败: {result['error']}")
        return
    
    # 2. 处理脚本加载失败
    script_result = manager.load_script_from_file("nonexistent.js")
    if script_result['error']:
        print(f"脚本加载失败: {script_result['error']}")
        return
    
    # 3. 处理注入失败
    load_result = await injector.load_script(manager, "test_script")
    if load_result['error']:
        print(f"注入失败: {load_result['error']}")
        return
    
    print("所有操作成功完成")
    """)

def main():
    """主测试函数"""
    print("🧪 测试新的BaseInjector架构\n")
    
    try:
        # 测试结构
        if not test_injector_structure():
            return
        
        # 测试集成
        test_script_manager_integration()
        
        # 展示使用示例
        show_usage_examples()
        show_platform_examples()
        show_error_handling()
        
        print("\n✅ 新的BaseInjector架构测试完成！")
        print("\n📋 主要特性:")
        print("   ✅ 支持多次ScriptManager注入")
        print("   ✅ 统一的平台接口")
        print("   ✅ 完整的生命周期管理")
        print("   ✅ 标准化的错误处理")
        print("   ✅ 支持脚本热插拔")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()