#!/usr/bin/env python3
"""
测试新的错误处理格式（返回dict格式）
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def test_error_format():
    """测试错误处理格式"""
    print("=== 测试错误处理格式（返回dict）===")
    
    try:
        # 测试平台管理器
        from frida_mcp.scripts.platform_manager import PlatformManager
        
        # 测试自动平台检测
        platform = PlatformManager.detect_platform()
        print(f"   检测到的平台: {platform}")
        
        # 测试创建管理器
        manager = PlatformManager.create_manager('android')
        print(f"   创建的管理器类型: {type(manager).__name__}")
        
        # 测试文件加载（成功情况）
        result = manager.get_available_scripts()
        print(f"   获取脚本列表结果: {result}")
        
        if result['error'] is None:
            print(f"   ✅ 成功获取 {len(result['data'])} 个脚本")
        else:
            print(f"   ❌ 错误: {result['error']}")
        
        # 测试文件加载（失败情况）
        result = manager.load_script_from_file("nonexistent.js")
        print(f"   加载不存在的文件: {result}")
        
        if result['error']:
            print(f"   ✅ 正确处理错误: {result['error']}")
        else:
            print(f"   ❌ 应该返回错误")
        
        # 测试平台专用方法
        android_manager = PlatformManager.create_manager('android')
        result = android_manager.load_ssl_pinning_bypass()
        print(f"   Android SSL绕过: {result}")
        
        if result['error'] is None:
            print(f"   ✅ SSL绕过脚本长度: {len(result['data'])} 字符")
        
        windows_manager = PlatformManager.create_manager('windows')
        result = windows_manager.load_api_monitor("kernel32.dll", "CreateFileW")
        print(f"   Windows API监控: {result}")
        
        if result['error'] is None:
            print(f"   ✅ API监控脚本长度: {len(result['data'])} 字符")
        
        # 测试模板替换
        android_manager = PlatformManager.create_manager('android')
        result = android_manager.load_activity_hook(
            package_name="com.example.test",
            activity_name="MainActivity"
        )
        
        if result['error'] is None:
            script = result['data']
            if "com.example.test" in script and "MainActivity" in script:
                print("   ✅ 模板替换成功")
            else:
                print("   ❌ 模板替换失败")
        
    except Exception as e:
        print(f"   测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_usage_example():
    """测试使用示例"""
    print("\n=== 使用示例 ===")
    
    try:
        from frida_mcp.scripts.platform_manager import PlatformManager
        
        # 示例1：自动检测平台
        platform = PlatformManager.detect_platform()
        manager = PlatformManager.create_manager(platform)
        
        print(f"   # 当前平台: {platform}")
        print(f"   manager = PlatformManager.create_manager('{platform}')")
        
        # 示例2：指定平台
        android_manager = PlatformManager.create_manager('android')
        result = android_manager.load_ssl_pinning_bypass()
        
        if result['error'] is None:
            print(f"   # Android SSL绕过脚本已加载，长度: {len(result['data'])} 字符")
        
        # 示例3：错误处理
        result = android_manager.load_script_from_file("invalid.js")
        if result['error']:
            print(f"   # 错误处理: {result['error']}")
        
        # 示例4：获取可用脚本
        result = android_manager.get_available_scripts()
        if result['error'] is None:
            print(f"   # 可用Android脚本: {result['data']}")
        
    except Exception as e:
        print(f"   示例测试失败: {e}")

def main():
    """主测试函数"""
    print("🧪 测试新的错误处理格式\n")
    
    try:
        test_error_format()
        test_usage_example()
        
        print("\n✅ 错误处理格式测试完成！")
        print("\n📋 新的API格式:")
        print("   所有方法返回: {'error': str, 'data': any}")
        print("   - error: None 表示成功")
        print("   - error: str 表示错误信息")
        print("   - data: 实际返回的数据")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()