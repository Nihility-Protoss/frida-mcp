"""
Test Windows fast-loading scripts (memory allocation and file monitoring)
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_utils import MCPTestClient, TestRunner, run_test_suite


class WindowsFastScriptRunner(TestRunner):
    """Test runner for Windows fast-loading scripts."""

    # Configuration
    target_package: str = r"C:\Windows\System32\notepad.exe"
    target_args: str = ""

    async def test_fast_file_monitor(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test windows_fast_load_all_monitor_file."""
        self.print_section("Test 1: Fast File Monitor")
        print("[!] Warning: Generates massive log output")

        result = await client.load_script("windows_fast_load_all_monitor_file")
        return self.record("windows_fast_load_all_monitor_file", result)

    async def test_fast_memory_monitor(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test windows_fast_load_monitor_memory_alloc."""
        self.print_section("Test 2: Fast Memory Monitor")
        print("[!] Warning: Monitors all memory allocations")
        print("[!] Auto-dumps RX/RWX memory to ./memory_dumps/")

        result = await client.load_script("windows_fast_load_monitor_memory_alloc")
        return self.record("windows_fast_load_monitor_memory_alloc", result)

    async def test_get_script(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test get_script_now."""
        self.print_section("Test 3: Get Current Script")
        result = await client.call("get_script_now")
        if result.get("status") == "success":
            print(f"[+] Script size: {len(result.get('message', ''))} chars")
        return self.record("get_script_now", result)

    async def test_trigger_scripts(self, client: MCPTestClient) -> Dict[str, Any]:
        """Trigger all loaded scripts by injecting empty script."""
        self.print_section("Test 4: Trigger All Scripts")
        print("[*] Injecting empty script to trigger all loaded scripts")

        result = await client.call("inject_user_script_run_all", {"script_content": ""})
        if result.get("status") == "success":
            print("[+] All scripts triggered successfully")
        return self.record("inject_user_script_run_all (trigger)", result)

    async def run(self):
        """Run all Windows fast script tests."""
        self.print_header("Windows Fast Script Tests")
        print(f"Target: {self.target_package}")
        if self.target_args:
            print(f"Args: {self.target_args}")

        async with MCPTestClient(self.url) as client:
            print("\n[+] Connected to MCP server")

            # Setup: spawn target
            self.print_section("Setup: Spawn Target")
            spawn_result = await client.spawn(self.target_package, self.target_args)
            if spawn_result.get("status") != "success":
                print("[-] Spawn failed, aborting")
                return
            self.record("spawn", spawn_result)

            # Run tests
            await self.test_fast_file_monitor(client)
            await self.test_fast_memory_monitor(client)
            await self.test_get_script(client)
            await self.test_trigger_scripts(client)

            # Get logs
            self.print_section("Logs")
            await client.get_new_messages()

            # Cleanup
            await client.detach()

            self.print_summary()


if __name__ == "__main__":
    run_test_suite(WindowsFastScriptRunner)
