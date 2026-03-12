"""
Test basic MCP client connection and core resources
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_utils import MCPTestClient, run_test_suite


async def test_connection():
    """Test basic MCP server connection and resource access."""
    print("[*] Testing MCP server connection...")
    
    async with MCPTestClient() as client:
        print("[+] Connection established")
        
        # List available tools
        tools = await client._client.list_tools()
        print(f"[+] Server reports {len(tools)} tools available")
        
        # Read version resource
        print("[*] Reading frida://version...")
        version = await client._client.read_resource("frida://version")
        print(f"[+] Version: {version}")
        
        # Read config resource
        print("[*] Reading frida://config...")
        config = await client.call("config_get")
        if config.get("status") == "success":
            print(f"[+] Active config loaded")
            print(f"    OS: {config.get('active_config', {}).get('os')}")
            print(f"    Device: {config.get('active_config', {}).get('device_id')}")
        
        print("\n[✔] Connection test PASSED")


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(test_connection())
    except KeyboardInterrupt:
        print("\n[*] Test cancelled.")
    except Exception as e:
        print(f"\n[!] Test FAILED: {e}")
