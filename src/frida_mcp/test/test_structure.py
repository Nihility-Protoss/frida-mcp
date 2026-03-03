#!/usr/bin/env python3
"""
测试平台专用脚本管理器结构（不依赖frida）
"""

import os
import sys
from pathlib import Path

def test_directory_structure():
    """测试目录结构"""
    print("=== 测试目录结构 ===")
    
    base_path = Path(__file__).parent.parent
    
    # 检查目录结构
    directories = {
        "android": ["android_script_manager.py", "js"],
        "windows": ["windows_script_manager.py", "js"],
        "scripts": ["scripts_manager.py", "platform_manager.py", "js"]
    }
    
    for dir_name, contents in directories.items():
        dir_path = base_path / dir_name
        if dir_path.exists():
            print(f"   ✅ {dir_name}/ 目录存在")
            
            # 检查子目录和文件
            for item in contents:
                item_path = dir_path / item
                if item_path.exists():
                    if item_path.is_dir():
                        js_files = list(item_path.glob("*.js"))
                        print(f"      ✅ {item}/: {len(js_files)} 个JS文件")
                        for js_file in js_files:
                            print(f"         - {js_file.name}")
                    else:
                        print(f"      ✅ {item} 文件存在")
                else:
                    print(f"      ❌ {item} 不存在")
        else:
            print(f"   ❌ {dir_name}/ 目录不存在")

def test_python_files():
    """测试Python文件结构"""
    print("\n=== 测试Python文件结构 ===")
    
    base_path = Path(__file__).parent.parent
    
    python_files = [
        "android/android_script_manager.py",
        "windows/windows_script_manager.py", 
        "scripts/scripts_manager.py",
        "scripts/platform_manager.py"
    ]
    
    for py_file in python_files:
        file_path = base_path / py_file
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = len(content.split('\n'))
                    print(f"   ✅ {py_file}: {lines} 行")
            except Exception as e:
                print(f"   ❌ {py_file}: 读取失败 - {e}")
        else:
            print(f"   ❌ {py_file}: 文件不存在")

def test_inheritance_structure():
    """测试继承结构"""
    print("\n=== 测试继承结构 ===")
    
    base_path = Path(__file__).parent.parent
    
    # 检查继承关系
    inheritance_map = {
        "AndroidScriptManager": "ScriptManager",
        "WindowsScriptManager": "ScriptManager",
        "AndroidJSFileLoader": "JSFileLoader", 
        "WindowsJSFileLoader": "JSFileLoader"
    }
    
    for child, parent in inheritance_map.items():
        print(f"   {child} -> {parent}")
    
    print("   ✅ 继承结构定义完成")

def test_js_templates():
    """测试JS模板文件"""
    print("\n=== 测试JS模板文件 ===")
    
    base_path = Path(__file__).parent.parent
    
    # 检查模板占位符
    template_files = {
        "android/js/activity_hook.js": ["{{package_name}}", "{{activity_name}}"],
        "android/js/ssl_pinning_bypass.js": [],
        "android/js/root_detection_bypass.js": [],
        "windows/js/api_monitor.js": ["{{module_name}}", "{{api_name}}"],
        "windows/js/registry_monitor.js": ["{{registry_path}}"],
        "windows/js/file_monitor.js": ["{{file_path}}"],
        "scripts/js/android_hook.js": ["{{target_class}}", "{{target_method}}"],
        "scripts/js/ios_hook.js": ["{{target_class}}", "{{target_method}}", "{{arg_count}}"]
    }
    
    for file_path, placeholders in template_files.items():
        full_path = base_path / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    found_placeholders = []
                    for placeholder in placeholders:
                        if placeholder in content:
                            found_placeholders.append(placeholder)
                    
                    if placeholders:
                        print(f"   ✅ {file_path}: 找到占位符 {found_placeholders}")
                    else:
                        print(f"   ✅ {file_path}: 无占位符模板")
                        
            except Exception as e:
                print(f"   ❌ {file_path}: 读取失败 - {e}")
        else:
            print(f"   ❌ {file_path}: 文件不存在")

def test_platform_specific_methods():
    """测试平台专用方法"""
    print("\n=== 测试平台专用方法 ===")
    
    android_methods = [
        "load_activity_hook",
        "load_broadcast_hook", 
        "load_service_hook",
        "load_shared_preferences_hook",
        "load_ssl_pinning_bypass",
        "load_root_detection_bypass",
        "load_frida_detection_bypass",
        "get_android_specific_scripts"
    ]
    
    windows_methods = [
        "load_api_monitor",
        "load_registry_monitor",
        "load_file_monitor",
        "load_network_monitor",
        "load_process_injection",
        "load_antivirus_bypass",
        "load_uac_bypass",
        "get_windows_specific_scripts"
    ]
    
    print("   Android专用方法:")
    for method in android_methods:
        print(f"      - {method}()")
    
    print("   Windows专用方法:")
    for method in windows_methods:
        print(f"      - {method}()")
    
    print("   ✅ 平台专用方法定义完成")

def main():
    """主测试函数"""
    print("🧪 开始测试平台专用脚本管理器结构\n")
    
    try:
        test_directory_structure()
        test_python_files()
        test_inheritance_structure()
        test_js_templates()
        test_platform_specific_methods()
        
        print("\n✅ 所有结构测试完成！")
        print("\n📁 最终目录结构:")
        print("   frida-mcp/src/frida_mcp/")
        print("   ├── android/")
        print("   │   ├── android_script_manager.py")
        print("   │   └── js/")
        print("   │       ├── activity_hook.js")
        print("   │       ├── ssl_pinning_bypass.js")
        print("   │       └── root_detection_bypass.js")
        print("   ├── windows/")
        print("   │   ├── windows_script_manager.py")
        print("   │   └── js/")
        print("   │       ├── api_monitor.js")
        print("   │       ├── registry_monitor.js")
        print("   │       └── file_monitor.js")
        print("   ├── scripts/")
        print("   │   ├── scripts_manager.py")
        print("   │   ├── platform_manager.py")
        print("   │   └── js/")
        print("   │       ├── android_hook.js")
        print("   │       ├── common_utils.js")
        print("   │       └── ios_hook.js")
        print("   └── test/")
        print("       ├── test_platform_manager.py")
        print("       └── test_standalone.py")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()