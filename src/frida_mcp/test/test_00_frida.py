# Baseline Test @test
"""
基础 Frida 连接测试
- 测试设备连接
- 使用 MCP get_new_messages 工具获取日志
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from fastmcp import Client
except ImportError:
    print("Error: 'fastmcp' not found. Please install it using 'pip install fastmcp'")
    sys.exit(1)

# 默认 MCP 服务器地址
DEFAULT_URL = "http://192.168.40.129:8032/mcp"

# 全局变量
device_id = "local"


async def test_get_new_messages(client: Client) -> dict:
    """测试 MCP get_new_messages 工具"""
    print(f"[*] Testing get_new_messages via MCP...")
    try:
        result = await client.call_tool("get_new_messages")

        if hasattr(result, 'content') and result.content:
            messages_result = json.loads(result.content[0].text)
            print(f"[+] Get new messages result:")
            for i in messages_result.get('messages', []):
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


async def run_tests(url: str):
    """运行测试"""
    print(f"[*] Starting baseline Frida test...")
    print(f"[*] MCP Server URL: {url}")
    print("-" * 50)

    try:
        async with Client(url) as client:
            print("[+] Connected to MCP server")

            # 测试 get_new_messages
            print("\n[Test 1] Testing get_new_messages...")
            result = await test_get_new_messages(client)

            # 总结
            print("\n" + "=" * 50)
            print("Test Summary:")
            print(f"- get_new_messages: {'✓' if result['status'] == 'success' else '✗'}")
            print("=" * 50)

    except Exception as e:
        print(f"[-] Failed to connect to MCP server: {e}")
        print("    Tips:")
        print("    1. Ensure the Frida MCP server is running")
        print(f"    2. Verify the server is listening on {url}")
        print("    3. Check your network/firewall settings")


async def main():
    """主函数"""
    await run_tests(DEFAULT_URL)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Test cancelled by user.")
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
