# Baseline Test @4
"""
测试注入功能相关函数
测试以下内容：
- attach: 附加到运行中的进程
- spawn: 拉起应用（挂起态）并注入
- inject_user_script_run_all: 注入并运行用户自定义脚本（文件路径形式）
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

# 全局变量，由用户输入
target_package: str = r"C:\Windows\System32\notepad.exe"  # 目标进程包名或 PID
target = "notepad.exe"
first_test_mode: str = "spawn"  # 首先测试哪种模式: "spawn" 或 "attach"


async def test_attach(client: Client, target: str) -> Dict[str, Any]:
    """测试 attach 模式注入"""
    print(f"[*] Testing attach with target: {target}")
    try:
        result = await client.call_tool(
            "attach",
            arguments={
                "target": target
            })

        if hasattr(result, 'content') and result.content:
            attach_result = json.loads(result.content[0].text)
            print(f"[+] Attach result: {attach_result}")

            if attach_result.get('status') == 'success':
                print(f"[+] Successfully attached to {target}")
                return {"status": "success", "message": attach_result.get('message', 'Attach successful')}
            else:
                print(f"[-] Failed to attach: {attach_result.get('message', 'Unknown error')}")
                return {"status": "error", "message": attach_result.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] attach failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_spawn(client: Client, package_name: str) -> Dict[str, Any]:
    """测试 spawn 模式注入"""
    print(f"[*] Testing spawn with package: {package_name}")
    try:
        result = await client.call_tool(
            "spawn",
            arguments={
                "package_name": package_name
            })

        if hasattr(result, 'content') and result.content:
            spawn_result = json.loads(result.content[0].text)
            print(f"[+] Spawn result: {spawn_result}")

            if spawn_result.get('status') == 'success':
                print(f"[+] Successfully spawned {package_name}")
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


async def test_inject_user_script_run_all(client: Client, script_content: str) -> Dict[str, Any]:
    """测试通过内容注入用户脚本"""
    print(f"[*] Testing inject_user_script_run_all with script content")
    try:
        result = await client.call_tool(
            "inject_user_script_run_all",
            arguments={"script_content": script_content})

        if hasattr(result, 'content') and result.content:
            inject_result = json.loads(result.content[0].text)
            print(f"[+] Inject result: {inject_result}")

            if inject_result.get('status') == 'success':
                print(f"[+] Successfully injected script")
                return {"status": "success", "message": inject_result.get('message', 'Inject successful')}
            else:
                print(f"[-] Failed to inject script: {inject_result.get('message', 'Unknown error')}")
                return {"status": "error", "message": inject_result.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] inject_user_script_run_all failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_get_session_info(client: Client) -> Dict[str, Any]:
    """测试获取会话信息"""
    print(f"[*] Testing get_session_info...")
    try:
        result = await client.call_tool("get_session_info")

        if hasattr(result, 'content') and result.content:
            session_info = json.loads(result.content[0].text)
            print(f"[+] Session info: {session_info}")

            if session_info.get('status') == 'success':
                print(f"[+] Active session: {session_info.get('target')} (PID: {session_info.get('pid')})")
                return {"status": "success", "session": session_info}
            else:
                print(f"[-] No active session: {session_info.get('message', 'Unknown error')}")
                return {"status": "error", "message": session_info.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] get_session_info failed: {e}")
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


async def test_get_messages(client: Client, max_messages: int = 100) -> Dict[str, Any]:
    """测试获取消息缓冲区内容"""
    print(f"[*] Testing get_messages (max_messages={max_messages})...")
    try:
        result = await client.call_tool(
            "get_messages",
            arguments={"max_messages": max_messages})

        if hasattr(result, 'content') and result.content:
            messages_result = json.loads(result.content[0].text)
            print(f"[+] Get messages result: ")
            for i in messages_result['messages']:
                print(f"[+] {i}")

            if messages_result.get('status') == 'success':
                messages = messages_result.get('messages', [])
                remaining = messages_result.get('remaining', 0)
                print(f"[+] Retrieved {len(messages)} messages, {remaining} remaining")
                return {"status": "success", "messages": messages, "remaining": remaining}
            else:
                print(f"[-] Failed to get messages: {messages_result.get('message', 'Unknown error')}")
                return {"status": "error", "message": messages_result.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}

    except Exception as e:
        print(f"[-] get_messages failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_get_new_messages(client: Client) -> Dict[str, Any]:
    """测试获取新消息（自上次输出后的所有log数据）"""
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


async def run_all_tests(url: str):
    """运行所有注入功能测试"""
    print(f"[*] Starting injection tests...")
    print(f"[*] MCP Server URL: {url}")
    print(f"[*] Target Package: {target_package}")
    print(f"[*] First Test Mode: {first_test_mode}")
    print("-" * 50)

    try:
        async with Client(url) as client:
            print("[+] Connected to MCP server")

            if first_test_mode == "spawn":
                # 测试 1: Spawn 模式（拉起应用）
                print("\n[Test 1] Testing spawn mode...")
                spawn_result = await test_spawn(client, target_package)

                # 获取会话信息
                session_info = await test_get_session_info(client)

                # 测试 2: 注入用户脚本
                print("\n[Test 2] Testing inject_user_script_run_all...")
                # 创建一个简单的测试脚本
                test_script_content = """
console.log("[TEST] Simple console log test");
console.log("[TEST] Script injected successfully");
"""

                inject_result = await test_inject_user_script_run_all(client, test_script_content)

                # 测试 3: Detach
                print("\n[Test 3] Testing detach...")
                detach_result = await test_detach(client)

                # 重新连接并测试 4: Attach 模式（附加到已运行的进程）
                print("\n[Test 4] Testing attach mode...")
                print("[*] Ensure the target process is running before testing attach.")
                attach_result = await test_attach(client, target)

                # 再次获取会话信息
                session_info_attach = await test_get_session_info(client)

                # 再次测试注入用户脚本
                print("\n[Test 5] Testing inject_user_script_run_all after attach...")
                inject_result_attach = await test_inject_user_script_run_all(client, test_script_content)

                # 再次测试 Detach
                print("\n[Test 6] Testing detach after attach...")
                detach_result_attach = await test_detach(client)

            else:  # first_test_mode == "attach"
                # 测试 1: Attach 模式（附加到已运行的进程）
                print("\n[Test 1] Testing attach mode...")
                print("[*] Ensure the target process is running before testing attach.")
                attach_result = await test_attach(client, target)

                # 获取会话信息
                session_info_attach = await test_get_session_info(client)

                # 测试 2: 注入用户脚本
                print("\n[Test 2] Testing inject_user_script_run_all...")
                # 创建一个简单的测试脚本
                test_script_content = """
console.log("[TEST] Simple console log test");
console.log("[TEST] Script injected successfully");
"""

                inject_result_attach = await test_inject_user_script_run_all(client, test_script_content)

                # 测试 3: Detach
                print("\n[Test 3] Testing detach...")
                detach_result_attach = await test_detach(client)

                # 重新连接并测试 4: Spawn 模式（拉起应用）
                print("\n[Test 4] Testing spawn mode...")
                spawn_result = await test_spawn(client, target_package)

                # 获取会话信息
                session_info = await test_get_session_info(client)

                # 再次测试注入用户脚本
                print("\n[Test 5] Testing inject_user_script_run_all after spawn...")
                inject_result = await test_inject_user_script_run_all(client, test_script_content)

                # 再次测试 Detach
                print("\n[Test 6] Testing detach after spawn...")
                detach_result = await test_detach(client)

            # 获取消息
            print("\n[Test 7] Testing get_new_messages...")
            get_new_messages_result = await test_get_new_messages(client)

            print("\n[Test 8] Testing get_messages...")
            get_messages_result = await test_get_messages(client, max_messages=5)

            # 总结
            print("\n" + "=" * 50)
            print("Test Summary:")
            if first_test_mode == "spawn":
                print(f"- spawn: {'✓' if spawn_result['status'] == 'success' else '✗'}")
                print(f"- inject_user_script_run_all (after spawn): {'✓' if inject_result['status'] == 'success' else '✗'}")
                print(f"- detach (after spawn): {'✓' if detach_result['status'] == 'success' else '✗'}")
                print(f"- attach: {'✓' if attach_result['status'] == 'success' else '✗'}")
                print(f"- inject_user_script_run_all (after attach): {'✓' if inject_result_attach['status'] == 'success' else '✗'}")
                print(f"- detach (after attach): {'✓' if detach_result_attach['status'] == 'success' else '✗'}")
            else:  # first_test_mode == "attach"
                print(f"- attach: {'✓' if attach_result['status'] == 'success' else '✗'}")
                print(f"- inject_user_script_run_all (after attach): {'✓' if inject_result_attach['status'] == 'success' else '✗'}")
                print(f"- detach (after attach): {'✓' if detach_result_attach['status'] == 'success' else '✗'}")
                print(f"- spawn: {'✓' if spawn_result['status'] == 'success' else '✗'}")
                print(f"- inject_user_script_run_all (after spawn): {'✓' if inject_result['status'] == 'success' else '✗'}")
                print(f"- detach (after spawn): {'✓' if detach_result['status'] == 'success' else '✗'}")

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
