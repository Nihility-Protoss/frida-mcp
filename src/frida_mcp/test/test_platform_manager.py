#!/usr/bin/env python3
"""
测试平台专用脚本管理器功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_platform_detection():
    """测试平台检测功能"""
    print("=== 测试平台检测 ===")
    
    try:
        from frida_mcp.scripts.scripts_manager import ScriptManager
        manager = ScriptManager()
        platform = manager.get_platform()
        print(f"   检测到的平台: {platform}")
        return platform
    except ImportError as e:
        print(f"   导入失败: {e}")
        return None

def test_platform_managers():
    """测试各平台管理器"""
    print("\n=== 测试各平台管理器 ===")
    
    try:
        from frida_mcp.scripts.platform_manager import PlatformManager
        
        # 测试Android管理器
        print("1. 测试Android管理器...")
        android_manager = PlatformManager.create_android_manager()
        android_scripts = android_manager.get_android_specific_scripts()
        print(f"   Android专用脚本: {android_scripts}")
        
        # 测试Windows管理器
        print("2. 测试Windows管理器...")
        windows_manager = PlatformManager.create_windows_manager()
        windows_scripts = windows_manager.get_windows_specific_scripts()
        print(f"   Windows专用脚本: {windows_scripts}")
        
        # 测试通用管理器
        print("3. 测试通用管理器...")
        generic_manager = PlatformManager.create_generic_manager()
        generic_scripts = generic_manager.get_available_scripts()
        print(f"   通用脚本: {generic_scripts}")
        
    except ImportError as e:
        print(f"   导入失败: {e}")

def test_unified_manager():
    """测试统一脚本管理器"""
    print("\n=== 测试统一脚本管理器 ===")
    
    try:
        from frida_mcp.scripts.platform_manager import UnifiedScriptManager
        
        # 创建统一管理器
        unified = UnifiedScriptManager('android')
        print(f"   当前平台: {unified.get_current_platform()}")
        print(f"   平台脚本: {unified.get_platform_scripts()}")
        
        # 切换到Windows平台
        print("   切换到Windows平台...")
        unified.switch_platform('windows')
        print(f"   切换后平台: {unified.get_current_platform()}")
        print(f"   Windows脚本: {unified.get_platform_scripts()}")
        
    except ImportError as e:
        print(f"   导入失败: {e}")

def test_file_loading():
    """测试文件加载功能"""
    print("\n=== 测试文件加载功能 ===")
    
    try:
        from frida_mcp.android.android_script_manager import AndroidScriptManager
        from frida_mcp.windows.windows_script_manager import WindowsScriptManager
        
        # 测试Android文件加载
        android_manager = AndroidScriptManager()
        android_scripts = android_manager.get_android_specific_scripts()
        print(f"   Android可用脚本: {android_scripts}")
        
        # 测试Windows文件加载
        windows_manager = WindowsScriptManager()
        windows_scripts = windows_manager.get_windows_specific_scripts()
        print(f"   Windows可用脚本: {windows_scripts}")
        
    except ImportError as e:
        print(f"   导入失败: {e}")

def test_template_replacement():
    """测试模板替换功能"""
    print("\n=== 测试模板替换功能 ===")
    
    try:
        from frida_mcp.android.android_script_manager import AndroidScriptManager
        
        android_manager = AndroidScriptManager()
        android_scripts = android_manager.get_android_specific_scripts()
        
        if android_scripts:
            # 测试Activity Hook替换
            activity_hook = android_manager.load_activity_hook(
                package_name="com.example.test",
                activity_name="MainActivity"
            )
            
            # 检查替换结果
            if "com.example.test" in activity_hook:
                print("   ✓ 包名替换成功")
            if "MainActivity" in activity_hook:
                print("   ✓ Activity名替换成功")
            print(f"   脚本长度: {len(activity_hook)} 字符")
        
    except ImportError as e:
        print(f"   导入失败: {e}")

def main():
    """主测试函数"""
    print("🧪 开始测试平台专用脚本管理器功能\n")
    
    try:
        # 运行所有测试
        current_platform = test_platform_detection()
        test_platform_managers()
        test_unified_manager()
        test_file_loading()
        test_template_replacement()
        
        if current_platform:
            print(f"\n✅ 所有测试完成！当前平台: {current_platform}")
        else:
            print("\n⚠️  部分测试跳过（缺少依赖）")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()