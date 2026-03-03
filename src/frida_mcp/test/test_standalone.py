#!/usr/bin/env python3
"""
独立测试平台专用脚本管理器功能（不依赖frida）
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_file_structure():
    """测试文件结构"""
    print("=== 测试文件结构 ===")
    
    base_path = Path(__file__).parent.parent
    
    # 检查目录结构
    directories = [
        "android/js",
        "windows/js",
        "scripts/js"
    ]
    
    for dir_path in directories:
        full_path = base_path / dir_path
        if full_path.exists():
            files = list(full_path.glob("*.js"))
            print(f"   ✅ {dir_path}: {len(files)} 个JS文件")
            for f in files:
                print(f"      - {f.name}")
        else:
            print(f"   ❌ {dir_path}: 目录不存在")

def test_class_structure():
    """测试类结构"""
    print("\n=== 测试类结构 ===")
    
    try:
        # 测试基础类
        from frida_mcp.scripts.scripts_manager import ScriptManager, JSFileLoader, StringReplacer, ScriptBuilder
        print("   ✅ 基础类导入成功")
        
        # 测试Android类
        from frida_mcp.android.android_script_manager import AndroidScriptManager
        print("   ✅ Android类导入成功")
        
        # 测试Windows类
        from frida_mcp.windows.windows_script_manager import WindowsScriptManager
        print("   ✅ Windows类导入成功")
        
        # 测试平台管理器
        from frida_mcp.scripts.platform_manager import PlatformManager, UnifiedScriptManager
        print("   ✅ 平台管理器导入成功")
        
    except ImportError as e:
        print(f"   ❌ 导入失败: {e}")

def test_js_file_loader():
    """测试JS文件加载器"""
    print("\n=== 测试JS文件加载器 ===")
    
    try:
        from frida_mcp.scripts.scripts_manager import JSFileLoader
        
        # 测试通用加载器
        loader = JSFileLoader()
        files = loader.get_available_files()
        print(f"   通用JS文件: {files}")
        
        # 测试Android加载器
        from frida_mcp.android.android_script_manager import AndroidJSFileLoader
        android_loader = AndroidJSFileLoader()
        android_files = android_loader.get_available_files()
        print(f"   Android JS文件: {android_files}")
        
        # 测试Windows加载器
        from frida_mcp.windows.windows_script_manager import WindowsJSFileLoader
        windows_loader = WindowsJSFileLoader()
        windows_files = windows_loader.get_available_files()
        print(f"   Windows JS文件: {windows_files}")
        
    except Exception as e:
        print(f"   测试失败: {e}")

def test_string_replacer():
    """测试字符串替换器"""
    print("\n=== 测试字符串替换器 ===")
    
    try:
        from frida_mcp.scripts.scripts_manager import StringReplacer
        
        replacer = StringReplacer()
        
        # 测试简单替换
        template = "Hello {{name}}, your age is {{age}}"
        result = replacer.replace_placeholders(template, name="Alice", age=25)
        print(f"   模板: {template}")
        print(f"   结果: {result}")
        
        # 测试字典替换
        template2 = "Hook {{class_name}}.{{method_name}}"
        replacements = {"class_name": "TestClass", "method_name": "testMethod"}
        result2 = replacer.replace_with_dict(template2, replacements)
        print(f"   模板2: {template2}")
        print(f"   结果2: {result2}")
        
    except Exception as e:
        print(f"   测试失败: {e}")

def test_platform_detection():
    """测试平台检测"""
    print("\n=== 测试平台检测 ===")
    
    try:
        import platform
        current_platform = platform.system().lower()
        print(f"   当前系统: {current_platform}")
        
        # 模拟平台映射
        if current_platform == 'windows':
            mapped = 'windows'
        elif current_platform in ['linux', 'darwin']:
            mapped = 'android'
        else:
            mapped = 'generic'
        
        print(f"   映射平台: {mapped}")
        
    except Exception as e:
        print(f"   测试失败: {e}")

def test_platform_manager():
    """测试平台管理器"""
    print("\n=== 测试平台管理器 ===")
    
    try:
        from frida_mcp.scripts.platform_manager import PlatformManager
        
        # 测试工厂方法
        android_manager = PlatformManager.create_android_manager()
        windows_manager = PlatformManager.create_windows_manager()
        generic_manager = PlatformManager.create_generic_manager()
        
        print("   ✅ 所有平台管理器创建成功")
        
        # 测试统一接口
        unified_android = PlatformManager.get_platform_manager('android')
        unified_windows = PlatformManager.get_platform_manager('windows')
        unified_generic = PlatformManager.get_platform_manager('generic')
        
        print("   ✅ 统一接口测试成功")
        
    except Exception as e:
        print(f"   测试失败: {e}")

def main():
    """主测试函数"""
    print("🧪 开始独立测试平台专用脚本管理器功能\n")
    
    try:
        test_file_structure()
        test_class_structure()
        test_js_file_loader()
        test_string_replacer()
        test_platform_detection()
        test_platform_manager()
        
        print("\n✅ 所有独立测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()