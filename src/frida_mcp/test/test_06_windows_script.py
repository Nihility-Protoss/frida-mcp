# Baseline Test @6
"""
测试 Windows 专用快速加载脚本功能
测试以下内容：
- windows_fast_load_all_monitor_file: 加载 Windows 平台的所有文件监控 API
- windows_fast_load_monitor_memory_alloc: 加载 Windows 平台的内存分配监控脚本
"""

import asyncio
import json
import sys
from typing import Dict, Any
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from fastmcp import Client
except ImportError:
    print("Error: 'fastmcp' not found. Please install it using 'pip install fastmcp'")
    sys.exit(1)

# 默认 MCP 服务器地址
DEFAULT_URL = "http://192.168.40.129:8032/mcp"

# 目标进程配置
target_package: str = r"D:\tools\Ez_ShellcodeRun.x64.exe"  # 程序路径
target_args: str = r"D:\tools\Ez_ShellcodeRun.x64.exe.i64"  # 启动参数


async def test_spawn(client: Client, package_name: str, args: str = "") -> Dict[str, Any]:
    """测试 spawn 模式注入"""
    print(f"[*] Testing spawn with package: {package_name}")
    if args:
        print(f"[*] Arguments: {args}")
    
    try:
        result = await client.call_tool(
            "spawn",
            arguments={
                "package_name": package_name,
                "args": args
            })

        if hasattr(result, 'content') and result.content:
            spawn_result = json.loads(result.content[0].text)
            print(f"[+] Spawn result: {spawn_result}")

            if spawn_result.get('status') == 'success':
                full_command = spawn_result.get('package', package_name)
                print(f"[+] Successfully spawned: {full_command}")
                return {"status": "success", "message": spawn_result.get('message', 'Spawn successful')}
            else:
                print(f"[-] Failed to spawn: {spawn_result.get('message', 'Unknown error')}")
                return {"status": "error", "message": spawn_result.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] spawn failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_windows_fast_load_all_monitor_file(client: Client) -> Dict[str, Any]:
    """测试 Windows 全量文件监控（谨慎使用）"""
    print(f"[*] Testing windows_fast_load_all_monitor_file...")
    print(f"[!] Warning: This may generate a large amount of log information")
    try:
        result = await client.call_tool(
            "windows_fast_load_all_monitor_file",
            arguments={"run_script_bool": False})

        if hasattr(result, 'content') and result.content:
            load_result = json.loads(result.content[0].text)
            print(f"[+] Load result: {load_result}")

            if load_result.get('status') == 'success':
                print(f"[+] Successfully loaded all file monitor hooks")
                return {"status": "success", "message": load_result.get('message', 'Load successful')}
            else:
                print(f"[-] Failed to load: {load_result.get('message', 'Unknown error')}")
                return {"status": "error", "message": load_result.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] windows_fast_load_all_monitor_file failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_windows_fast_load_monitor_memory_alloc(client: Client) -> Dict[str, Any]:
    """测试 Windows 内存分配监控（谨慎使用）"""
    print(f"[*] Testing windows_fast_load_monitor_memory_alloc...")
    print(f"[!] Warning: This may generate a large amount of log information")
    try:
        result = await client.call_tool(
            "windows_fast_load_monitor_memory_alloc",
            arguments={"run_script_bool": False})

        if hasattr(result, 'content') and result.content:
            load_result = json.loads(result.content[0].text)
            print(f"[+] Load result: {load_result}")

            if load_result.get('status') == 'success':
                print(f"[+] Successfully loaded memory allocation monitor")
                return {"status": "success", "message": load_result.get('message', 'Load successful')}
            else:
                print(f"[-] Failed to load: {load_result.get('message', 'Unknown error')}")
                return {"status": "error", "message": load_result.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] windows_fast_load_monitor_memory_alloc failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_get_script_now(client: Client) -> Dict[str, Any]:
    """测试获取当前脚本"""
    print(f"[*] Testing get_script_now...")
    try:
        result = await client.call_tool("get_script_now")

        if hasattr(result, 'content') and result.content:
            script_result = json.loads(result.content[0].text)
            print(f"[+] Current script info: {script_result.get('message', 'N/A')}...")

            if script_result.get('status') == 'success':
                return {"status": "success", "script": script_result}
            else:
                print(f"[-] Failed to get script: {script_result.get('message', 'Unknown error')}")
                return {"status": "error", "message": script_result.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] get_script_now failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_inject_user_script_run_all(client: Client, script_content: str = "") -> Dict[str, Any]:
    """测试注入并运行所有脚本（传入空 script 触发已加载的脚本）"""
    print(f"[*] Testing inject_user_script_run_all...")
    if not script_content:
        print(f"[*] Triggering all loaded scripts with empty script content")
    try:
        result = await client.call_tool(
            "inject_user_script_run_all",
            arguments={"script_content": script_content})

        if hasattr(result, 'content') and result.content:
            inject_result = json.loads(result.content[0].text)
            print(f"[+] Inject result: {inject_result}")

            if inject_result.get('status') == 'success':
                print(f"[+] Successfully injected and executed scripts")
                return {"status": "success", "message": inject_result.get('message', 'Inject successful')}
            else:
                print(f"[-] Failed to inject: {inject_result.get('message', 'Unknown error')}")
                return {"status": "error", "message": inject_result.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] inject_user_script_run_all failed: {e}")
        return {"status": "error", "message": str(e)}


async def run_all_tests(url: str):
    """运行所有 Windows 快速加载脚本测试"""
    print(f"[*] Starting Windows fast load script tests...")
    print(f"[*] MCP Server URL: {url}")
    print(f"[*] Target Package: {target_package}")
    if target_args:
        print(f"[*] Target Args: {target_args}")
    print("-" * 50)

    try:
        async with Client(url) as client:
            print("[+] Connected to MCP server")

            # 测试 1: Spawn 模式启动目标进程
            print("\n[Test 1] Spawning target process...")
            spawn_result = await test_spawn(client, target_package, target_args)

            if spawn_result['status'] != 'success':
                print("[-] Spawn failed, aborting tests")
                return

            # 测试 2: 全量文件监控（注意会产生大量日志）
            print("\n[Test 2] Testing windows_fast_load_all_monitor_file...")
            print("[!] Note: This will hook all file APIs and generate massive logs")
            fast_file_result = await test_windows_fast_load_all_monitor_file(client)

            # 测试 3: 内存分配监控
            print("\n[Test 3] Testing windows_fast_load_monitor_memory_alloc...")
            print("[!] Note: This will monitor memory allocations and auto-dump RX/RWX memory")
            fast_mem_result = await test_windows_fast_load_monitor_memory_alloc(client)

            # 测试 4: 获取当前脚本
            print("\n[Test 4] Getting current script...")
            get_script_result = await test_get_script_now(client)

            # 测试 5: 注入并运行所有已加载的脚本（传入空 script 触发）
            print("\n[Test 5] Injecting and running all loaded scripts...")
            inject_all_result = await test_inject_user_script_run_all(client, "")

            # 断开对话
            detach_result = await client.call_tool("detach")

            # 总结
            print("\n" + "=" * 50)
            print("Test Summary:")
            print(f"- spawn: {'✓' if spawn_result['status'] == 'success' else '✗'}")
            print(f"- windows_fast_load_all_monitor_file: {'✓' if fast_file_result['status'] == 'success' else '✗'}")
            print(f"- windows_fast_load_monitor_memory_alloc: {'✓' if fast_mem_result['status'] == 'success' else '✗'}")
            print(f"- get_script_now: {'✓' if get_script_result['status'] == 'success' else '✗'}")
            print(f"- inject_user_script_run_all: {'✓' if inject_all_result['status'] == 'success' else '✗'}")
            print("=" * 50)

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
