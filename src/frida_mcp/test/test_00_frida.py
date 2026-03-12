"""
Basic Frida connectivity test using MCP client
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_utils import MCPTestClient


async def test_basic_connection():
    """Test basic connectivity and get_new_messages."""
    print("[*] Testing basic Frida MCP connectivity...")
    
    async with MCPTestClient() as client:
        print("[+] Connected to MCP server")
        
        # Try to get new messages (should work even without session)
        print("[*] Testing get_new_messages...")
        messages = await client.get_new_messages()
        
        print(f"[+] Test complete - retrieved {len(messages)} messages")


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(test_basic_connection())
    except KeyboardInterrupt:
        print("\n[*] Test cancelled.")
    except Exception as e:
        print(f"\n[!] Test FAILED: {e}")
