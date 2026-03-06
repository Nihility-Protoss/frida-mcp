# Baseline Test @1

import asyncio
import json
import sys
from typing import Dict, Any

# We'll use the high-level Client from fastmcp which is already in dependencies
try:
    from fastmcp import Client
except ImportError:
    print("Error: 'fastmcp' not found. Please install it using 'pip install fastmcp'")
    sys.exit(1)

# Default configuration for Frida MCP server in streamable-http mode
# When transport="streamable-http", the endpoint is typically /sse
DEFAULT_URL = "http://192.168.40.129:8032/mcp"


async def test_frida_mcp_connection(url: str = DEFAULT_URL):
    """
    一个简洁的测试脚本，用于验证 Frida MCP 服务器在 streamable-http 模式下的连接性。
    """
    print(f"[*] Testing streamable-http connection to: {url}")

    try:
        # 使用 FastMCP 的高层级 Client，它会自动处理 SSE (streamable-http) 传输
        async with Client(url) as client:
            print("[+] Connection established successfully!")

            # 1. 发现所有可用的工具 (验证工具是否都在)
            tools = await client.list_tools()
            print(f"[+] Server reports {len(tools)} tools available.")

            # 2. 调用核心资源/工具进行基本功能验证
            print("[*] Reading 'frida://version' resource...")
            # 使用 read_resource 直接读取资源，而不是调用 tool
            version_resource = await client.read_resource("frida://version")
            print(f"[+] Frida Version (via resource): {version_resource}")

            print("[*] Calling 'config_get' to verify active configuration...")
            result = await client.call_tool("config_get")

            # 解析并打印活跃配置
            if hasattr(result, 'content') and result.content:
                config_json = json.loads(result.content[0].text)
                active_config = config_json.get("active_config", {})
                print(f"[+] Active Config: {json.dumps(active_config, indent=2)}")
            else:
                print(f"[!] Unexpected response format: {result}")

            print("\n[✔] streamable-http connection test PASSED.")

    except Exception as e:
        print(f"[-] Connection test FAILED: {e}")
        print("    Tips:")
        print("    1. Ensure the Frida MCP server is running (python frida_mcp.py)")
        print(f"    2. Verify the server is listening on {url}")
        print("    3. If running remotely, check your firewall/network settings.")


if __name__ == "__main__":
    # 支持从命令行传入自定义 URL
    target_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL

    try:
        asyncio.run(test_frida_mcp_connection(target_url))
    except KeyboardInterrupt:
        print("\n[*] Test cancelled by user.")
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
