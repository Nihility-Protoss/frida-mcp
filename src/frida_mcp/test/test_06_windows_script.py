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
target_package: str = r"C:\Windows\System32\notepad.exe"  # 程序路径
target_args: str = ""  # 启动参数，如 "test.txt --arg1 value1"


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


async def test_get_new_messages(client: Client) -> Dict[str, Any]:
    """测试获取新消息"""
    print(f"[*] Testing get_new_messages...")
    try:
        result = await client.call_tool("get_new_messages")

        if hasattr(result, 'content') and result.content:
            messages_result = json.loads(result.content[0].text)
            print(f"[+] Get new messages result:")
            for i in messages_result['messages']:
                print(f"[+] {i}")

            if messages_result.get('status') == 'success':
                messages = messages_result.get('messages', [])
                remaining = messages_result.get('remaining', 0)
                print(f"[+] Retrieved {len(messages)} new messages, {remaining} remaining")
                return {"status": "success", "messages": messages, "remaining": remaining}
            else:
                print(f"[-] Failed to get new messages: {messages_result.get('message', 'Unknown error')}")
                return {"status": "error", "message": messages_result.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] get_new_messages failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_windows_fast_load_all_monitor_file(client: Client) -> Dict[str, Any]:
    """测试 Windows 全量文件监控（谨慎使用）"""
    print(f"[*] Testing windows_fast_load_all_monitor_file...")
    print(f"[!] Warning: This may generate a large amount of log information")
    try:
        result = await client.call_tool(
            "windows_fast_load_all_monitor_file",
            arguments={"run_script_bool": True})

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
            arguments={"run_script_bool": True})

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


async def test_detach(client: Client) -> Dict[str, Any]:
    """测试断开会话"""
    print(f"[*] Testing detach...")
    try:
        result = await client.call_tool("detach")

        if hasattr(result, 'content') and result.content:
            detach_result = json.loads(result.content[0].text)
            print(f"[+] Detach result: {detach_result}")

            if detach_result.get('status') == 'success':
                print(f"[+] Successfully detached")
                return {"status": "success", "message": detach_result.get('message', 'Detach successful')}
            else:
                print(f"[-] Failed to detach: {detach_result.get('message', 'Unknown error')}")
                return {"status": "error", "message": detach_result.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] detach failed: {e}")
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

            # 获取文件监控产生的日志
            print("\n[Test 3] Getting logs from file monitor...")
            file_logs_result = await test_get_new_messages(client)

            # 测试 4: 内存分配监控
            print("\n[Test 4] Testing windows_fast_load_monitor_memory_alloc...")
            print("[!] Note: This will monitor memory allocations and auto-dump RX/RWX memory")
            fast_mem_result = await test_windows_fast_load_monitor_memory_alloc(client)

            # 获取内存监控产生的日志
            print("\n[Test 5] Getting logs from memory monitor...")
            mem_logs_result = await test_get_new_messages(client)

            # 测试 6: Detach
            print("\n[Test 6] Testing detach...")
            detach_result = await test_detach(client)

            # 总结
            print("\n" + "=" * 50)
            print("Test Summary:")
            print(f"- spawn: {'✓' if spawn_result['status'] == 'success' else '✗'}")
            print(f"- windows_fast_load_all_monitor_file: {'✓' if fast_file_result['status'] == 'success' else '✗'}")
            print(f"- get_new_messages (file logs): {'✓' if file_logs_result['status'] == 'success' else '✗'}")
            print(f"- windows_fast_load_monitor_memory_alloc: {'✓' if fast_mem_result['status'] == 'success' else '✗'}")
            print(f"- get_new_messages (mem logs): {'✓' if mem_logs_result['status'] == 'success' else '✗'}")
            print(f"- detach: {'✓' if detach_result['status'] == 'success' else '✗'}")
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
