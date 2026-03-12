"""
Test injection functionality: attach, spawn, inject, detach
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_utils import MCPTestClient, TestRunner, run_test_suite, DEFAULT_URL


class InjectionTestRunner(TestRunner):
    """Test runner for injection-related tests."""

    # Configuration
    target_package: str = r"C:\Windows\System32\notepad.exe"
    target_name: str = "notepad.exe"
    first_mode: str = "spawn"  # "spawn" or "attach"

    async def test_spawn(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test spawn mode."""
        self.print_section("Test 1: Spawn Mode")
        result = await client.spawn(self.target_package)
        return self.record("spawn", result)

    async def test_attach(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test attach mode."""
        self.print_section("Test 2: Attach Mode")
        result = await client.attach(self.target_name)
        return self.record("attach", result)

    async def test_session_info(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test get_session_info."""
        self.print_section("Test 3: Session Info")
        result = await client.get_session_info()
        return self.record("get_session_info", result)

    async def test_inject(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test script injection."""
        self.print_section("Test 4: Script Injection")
        script = 'console.log("[TEST] Injection test");'
        result = await client.inject_script(script)
        return self.record("inject_script", result)

    async def test_detach(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test detach."""
        self.print_section("Test 5: Detach")
        result = await client.detach()
        return self.record("detach", result)

    async def test_get_messages(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test get_new_messages."""
        self.print_section("Test 6: Get New Messages")
        messages = await client.get_new_messages()
        return self.record("get_new_messages", {
            "status": "success",
            "count": len(messages)
        })

    async def run(self):
        """Run all injection tests."""
        self.print_header("Injection Tests")
        print(f"Target: {self.target_package}")
        print(f"First Mode: {self.first_mode}")

        async with MCPTestClient(self.url) as client:
            print("\n[+] Connected to MCP server")

            if self.first_mode == "spawn":
                # Spawn -> Inject -> Detach -> Attach -> Inject -> Detach
                await self.test_spawn(client)
                await self.test_session_info(client)
                await self.test_inject(client)
                await self.test_get_messages(client)
                await self.test_detach(client)

                await self.test_attach(client)
                await self.test_inject(client)
                await self.test_detach(client)
            else:
                # Attach -> Inject -> Detach -> Spawn -> Inject -> Detach
                await self.test_attach(client)
                await self.test_inject(client)
                await self.test_detach(client)

                await self.test_spawn(client)
                await self.test_inject(client)
                await self.test_detach(client)

            self.print_summary()


if __name__ == "__main__":
    run_test_suite(InjectionTestRunner)
