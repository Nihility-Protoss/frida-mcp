# Baseline Test @5
"""
测试脚本注入相关 API
测试 README.md 第 95-113 行中提到的所有 API：

脚本管理:
- get_script_list: 获得当前 injector 下所有可用的内置 script 文件名列表
- get_script_now: 获得当前 injector 中已经构建好的 script
- reset_script_now: 重置当前 injector 中的 script
- inject_user_script_run: 注入并运行用户自定义脚本（字符串形式）
- inject_user_script_run_all: 注入并运行用户自定义脚本（文件路径形式）

Android 专用脚本工具:
- android_load_script_anti_DexHelper_hook_clone
- android_load_script_anti_DexHelper_hook_pthread
- android_load_script_anti_DexHelper
- android_load_hook_net_libssl
- android_load_hook_clone
- android_load_hook_activity

Windows 专用脚本工具:
- windows_load_monitor_api
- windows_load_monitor_registry
- windows_load_monitor_file
"""

import asyncio
import json
import sys
from typing import Dict, Any
from pathlib import Path

from mcp.types import CallToolResult

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from fastmcp import Client
except ImportError:
    print("Error: 'fastmcp' not found. Please install it using 'pip install fastmcp'")
    sys.exit(1)

# 默认 MCP 服务器地址
DEFAULT_URL = "http://192.168.40.129:8032/mcp"

# 全局变量，由用户输入
target = "notepad.exe"
target_package: str = r"C:\Windows\System32\notepad.exe"

# Android 测试参数（可选）
android_test: bool = False  # 是否测试 Android API
android_package_name: str = "com.example.app"  # Android 包名
android_activity_name: str = ".MainActivity"  # Android Activity 名称
android_so_name: str = "libDexHelper.so"  # Android SO 文件名
android_hook_addr_list: list = [0x561d0, 0x52cc0, 0x5ded4, 0x5e410, 0x5fb48, 0x592c8, 0x69470]  # Hook 地址列表

# Windows 测试参数（可选）
windows_test: bool = True  # 是否测试 Windows API
windows_module_name: str = "kernel32.dll"  # Windows 模块名称
windows_api_name: str = "CreateFileW"  # Windows API 名称
windows_registry_path: str = "SOFTWARE\\Test"  # Windows 注册表路径
windows_file_path: str = "C:\\test.txt"  # Windows 文件路径


async def test_get_script_list(client: Client) -> Dict[str, Any]:
    """测试获取脚本列表"""
    print(f"[*] Testing get_script_list...")
    try:
        result = await client.call_tool("get_script_list")

        if hasattr(result, 'content') and result.content:
            script_list = json.loads(result.content[0].text)
            print(f"[+] Available scripts: {script_list}")
            return {"status": "success", "scripts": script_list}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] get_script_list failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_get_script_now(client: Client) -> Dict[str, Any]:
    """测试获取当前脚本"""
    print(f"[*] Testing get_script_now...")
    try:
        result = await client.call_tool("get_script_now")

        if hasattr(result, 'content') and result.content:
            script_now = json.loads(result.content[0].text)
            print(f"[+] Current script: {script_now['message']}")
            return {"status": "success", "script": script_now}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] get_script_now failed: {e}")
        return {"status": "error", "message": str(e)}


def fast_result(result: CallToolResult) -> Dict[str, Any]:
    if hasattr(result, 'content') and result.content:
        reset_result = json.loads(result.content[0].text)
        if reset_result.get("message"):
            print(f"[+] Reset result: {reset_result['message']}")
        else:
            print(f"[+] Reset result: {reset_result}")
        return {"status": "success", "message": reset_result}
    else:
        print(f"[!] Unexpected response: {result}")
        return {"status": "error", "message": "Invalid response format"}


async def test_reset_script_now(client: Client) -> Dict[str, Any]:
    """测试重置当前脚本"""
    print(f"[*] Testing reset_script_now...")
    try:
        result = await client.call_tool("reset_script_now")

        return fast_result(result)

    except Exception as e:
        print(f"[-] reset_script_now failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_inject_user_script_run(client: Client, script_content: str) -> Dict[str, Any]:
    """测试注入用户脚本（字符串形式）"""
    print(f"[*] Testing inject_user_script_run...")
    try:
        result = await client.call_tool(
            "inject_user_script_run",
            arguments={"script_content": script_content})

        return fast_result(result)

    except Exception as e:
        print(f"[-] inject_user_script_run failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_inject_user_script_run_all(client: Client, script_content: str) -> Dict[str, Any]:
    """测试注入用户脚本（内容形式）"""
    print(f"[*] Testing inject_user_script_run_all with script content")
    try:
        result = await client.call_tool(
            "inject_user_script_run_all",
            arguments={"script_content": script_content})

        return fast_result(result)

    except Exception as e:
        print(f"[-] inject_user_script_run_all failed: {e}")
        return {"status": "error", "message": str(e)}


from test_04_inject import test_get_new_messages, test_get_messages


# Android 专用 API 测试函数

async def test_android_load_script_anti_DexHelper_hook_clone(client: Client) -> Dict[str, Any]:
    """测试 Android 反 DexHelper 检测（hook clone）"""
    print(f"[*] Testing android_load_script_anti_DexHelper_hook_clone...")
    try:
        result = await client.call_tool(
            "android_load_script_anti_DexHelper_hook_clone")

        return fast_result(result)

    except Exception as e:
        print(f"[-] android_load_script_anti_DexHelper_hook_clone failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_android_load_script_anti_DexHelper_hook_pthread(client: Client) -> Dict[str, Any]:
    """测试 Android 反 DexHelper 检测（hook pthread）"""
    print(f"[*] Testing android_load_script_anti_DexHelper_hook_pthread...")
    try:
        result = await client.call_tool(
            "android_load_script_anti_DexHelper_hook_pthread")

        return fast_result(result)

    except Exception as e:
        print(f"[-] android_load_script_anti_DexHelper_hook_pthread failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_android_load_script_anti_DexHelper(client: Client) -> Dict[str, Any]:
    """测试 Android 反 DexHelper 检测（完整版）"""
    print(f"[*] Testing android_load_script_anti_DexHelper...")
    try:
        result = await client.call_tool(
            "android_load_script_anti_DexHelper",
            arguments={"hook_addr_list": android_hook_addr_list})

        return fast_result(result)

    except Exception as e:
        print(f"[-] android_load_script_anti_DexHelper failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_android_load_hook_net_libssl(client: Client) -> Dict[str, Any]:
    """测试 Android 网络库 SSL Hook"""
    print(f"[*] Testing android_load_hook_net_libssl...")
    try:
        result = await client.call_tool("android_load_hook_net_libssl")

        return fast_result(result)

    except Exception as e:
        print(f"[-] android_load_hook_net_libssl failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_android_load_hook_clone(client: Client) -> Dict[str, Any]:
    """测试 Android clone 系统调用 Hook"""
    print(f"[*] Testing android_load_hook_clone...")
    try:
        result = await client.call_tool(
            "android_load_hook_clone",
            arguments={"anti_so_name_tag": android_so_name})

        return fast_result(result)

    except Exception as e:
        print(f"[-] android_load_hook_clone failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_android_load_hook_activity(client: Client) -> Dict[str, Any]:
    """测试 Android Activity 生命周期 Hook"""
    print(f"[*] Testing android_load_hook_activity...")
    try:
        result = await client.call_tool(
            "android_load_hook_activity",
            arguments={
                "package_name": android_package_name,
                "activity_name": android_activity_name
            })

        return fast_result(result)

    except Exception as e:
        print(f"[-] android_load_hook_activity failed: {e}")
        return {"status": "error", "message": str(e)}


# Windows 专用 API 测试函数

async def test_windows_load_monitor_api(client: Client) -> Dict[str, Any]:
    """测试 Windows API 监控"""
    print(f"[*] Testing windows_load_monitor_api...")
    try:
        result = await client.call_tool(
            "windows_load_monitor_api",
            arguments={
                "module_name": windows_module_name,
                "api_name": windows_api_name
            })

        return fast_result(result)

    except Exception as e:
        print(f"[-] windows_load_monitor_api failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_windows_load_monitor_registry(client: Client) -> Dict[str, Any]:
    """测试 Windows 注册表监控"""
    print(f"[*] Testing windows_load_monitor_registry...")
    try:
        result = await client.call_tool(
            "windows_load_monitor_registry",
            arguments={
                "api_name": "RegSetValueExA",
                "registry_path": windows_registry_path
            })
        result = await client.call_tool(
            "windows_load_monitor_registry",
            arguments={
                "api_name": "RegSetValueExW",
                "registry_path": ""
            })

        return fast_result(result)

    except Exception as e:
        print(f"[-] windows_load_monitor_registry failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_windows_load_monitor_file(client: Client) -> Dict[str, Any]:
    """测试 Windows 文件监控"""
    print(f"[*] Testing windows_load_monitor_file...")
    try:
        result = await client.call_tool(
            "windows_load_monitor_file",
            arguments={
                "api_name": "CreateFileA",
                "file_path": windows_file_path
            })
        result = await client.call_tool(
            "windows_load_monitor_file",
            arguments={
                "api_name": "WriteFile",
                "file_path": ""
            })
        return fast_result(result)

    except Exception as e:
        print(f"[-] windows_load_monitor_file failed: {e}")
        return {"status": "error", "message": str(e)}


async def run_all_tests(url: str):
    """运行所有脚本注入测试"""
    print(f"[*] Starting script injection tests...")
    print(f"[*] MCP Server URL: {url}")
    print(f"[*] Target Package: {target_package}")
    print(f"[*] Android Test: {android_test}")
    print(f"[*] Windows Test: {windows_test}")
    print("-" * 50)

    try:
        async with Client(url) as client:
            print("[+] Connected to MCP server")

            # 首先通过 spawn 启动目标进程
            print(f"\n[Setup] Spawning target process: {target_package}")
            spawn_result = await client.call_tool(
                "spawn",
                arguments={
                    "package_name": target_package
                })
            print(f"[+] Spawn result: {spawn_result}")

            # 测试脚本管理 API
            print("\n[Test Group 1] Script Management APIs")
            print("-" * 50)

            # 1. get_script_list
            get_script_list_result = await test_get_script_list(client)

            # 2. get_script_now
            get_script_now_result = await test_get_script_now(client)

            # 3. inject_user_script_run (字符串形式)
            simple_script = "console.log('Hello from inject_user_script_run');"
            inject_user_script_run_result = await test_inject_user_script_run(client, simple_script)

            # 4. reset_script_now
            reset_script_now_result = await test_reset_script_now(client)

            # 5. inject_user_script_run_all (内容形式)
            test_script_content_inner = """
console.log("[TEST] Simple console log from file");
console.log("[TEST] Script loaded successfully");
"""

            inject_user_script_run_all_result = await test_inject_user_script_run_all(client, test_script_content_inner)

            # 测试 Android 专用 API（可选）
            if android_test:
                print("\n[Test Group 2] Android-Specific APIs")
                print("-" * 50)

                android_load_script_anti_DexHelper_hook_clone_result = await test_android_load_script_anti_DexHelper_hook_clone(
                    client)
                android_load_script_anti_DexHelper_hook_pthread_result = await test_android_load_script_anti_DexHelper_hook_pthread(
                    client)
                android_load_script_anti_DexHelper_result = await test_android_load_script_anti_DexHelper(client)
                android_load_hook_net_libssl_result = await test_android_load_hook_net_libssl(client)
                android_load_hook_clone_result = await test_android_load_hook_clone(client)
                android_load_hook_activity_result = await test_android_load_hook_activity(client)

            # 测试 Windows 专用 API（可选）
            if windows_test:
                print("\n[Test Group 3] Windows-Specific APIs")
                print("-" * 50)

                windows_load_monitor_api_result = await test_windows_load_monitor_api(client)
                windows_load_monitor_registry_result = await test_windows_load_monitor_registry(client)
                windows_load_monitor_file_result = await test_windows_load_monitor_file(client)

            # 获取消息
            print("\n[Test 7] Get script now...")
            get_script_now_result = await test_get_script_now(client)
            print("\n[Test 8] Testing get_new_messages...")
            get_new_messages_result = await test_get_new_messages(client)

            # 总结
            print("\n" + "=" * 50)
            print("Test Summary:")
            print("\nScript Management:")
            print(f"- get_script_list: {'✓' if get_script_list_result['status'] == 'success' else '✗'}")
            print(f"- get_script_now: {'✓' if get_script_now_result['status'] == 'success' else '✗'}")
            print(f"- inject_user_script_run: {'✓' if inject_user_script_run_result['status'] == 'success' else '✗'}")
            print(f"- reset_script_now: {'✓' if reset_script_now_result['status'] == 'success' else '✗'}")
            print(
                f"- inject_user_script_run_all: {'✓' if inject_user_script_run_all_result['status'] == 'success' else '✗'}")

            if android_test:
                print("\nAndroid-Specific:")
                print(
                    f"- android_load_script_anti_DexHelper_hook_clone: {'✓' if android_load_script_anti_DexHelper_hook_clone_result['status'] == 'success' else '✗'}")
                print(
                    f"- android_load_script_anti_DexHelper_hook_pthread: {'✓' if android_load_script_anti_DexHelper_hook_pthread_result['status'] == 'success' else '✗'}")
                print(
                    f"- android_load_script_anti_DexHelper: {'✓' if android_load_script_anti_DexHelper_result['status'] == 'success' else '✗'}")
                print(
                    f"- android_load_hook_net_libssl: {'✓' if android_load_hook_net_libssl_result['status'] == 'success' else '✗'}")
                print(
                    f"- android_load_hook_clone: {'✓' if android_load_hook_clone_result['status'] == 'success' else '✗'}")
                print(
                    f"- android_load_hook_activity: {'✓' if android_load_hook_activity_result['status'] == 'success' else '✗'}")

            if windows_test:
                print("\nWindows-Specific:")
                print(
                    f"- windows_load_monitor_api: {'✓' if windows_load_monitor_api_result['status'] == 'success' else '✗'}")
                print(
                    f"- windows_load_monitor_registry: {'✓' if windows_load_monitor_registry_result['status'] == 'success' else '✗'}")
                print(
                    f"- windows_load_monitor_file: {'✓' if windows_load_monitor_file_result['status'] == 'success' else '✗'}")

    except Exception as e:
        print(f"[-] Failed to connect to MCP server: {e}")
        print("    Tips:")
        print("    1. Ensure the Frida MCP server is running")
        print(f"    2. Verify the server is listening on {url}")
        print("    3. Check your network/firewall settings")


async def main():
    """主函数"""
    await run_all_tests(DEFAULT_URL)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Test cancelled by user.")
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
