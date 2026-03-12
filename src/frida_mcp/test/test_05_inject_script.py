"""
Test script management and platform-specific script loading
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_utils import MCPTestClient, TestRunner, run_test_suite


class ScriptTestRunner(TestRunner):
    """Test runner for script management tests."""

    # Configuration
    target_package: str = r"C:\Windows\System32\notepad.exe"
    android_test: bool = False
    windows_test: bool = True

    # Android test parameters
    android_pkg: str = "com.example.app"
    android_activity: str = ".MainActivity"
    android_so: str = "libDexHelper.so"
    android_hook_addrs: list = [0x561d0, 0x52cc0, 0x5ded4]

    # Windows test parameters
    windows_module: str = "kernel32.dll"
    windows_api: str = "CreateFileW"
    windows_reg_path: str = r"SOFTWARE\Test"
    windows_file_path: str = "test.txt"

    async def setup(self, client: MCPTestClient) -> bool:
        """Setup: spawn target process."""
        self.print_section("Setup: Spawn Target")
        result = await client.spawn(self.target_package)
        return result.get("status") == "success"

    async def test_script_management(self, client: MCPTestClient):
        """Test basic script management functions."""
        self.print_section("Script Management")

        # get_script_list
        result = await client.load_script("get_script_list")
        self.record("get_script_list", result)

        # get_script_now
        result = await client.call("get_script_now")
        self.record("get_script_now", result)

        # inject_user_script_run
        result = await client.call("inject_user_script_run", {
            "script_content": "console.log('Test script');",
            "script_name": "test"
        })
        self.record("inject_user_script_run", result)

        # reset_script_now
        result = await client.call("reset_script_now")
        self.record("reset_script_now", result)

        # inject_user_script_run_all
        result = await client.inject_script("console.log('Test all');", "test_all")
        self.record("inject_user_script_run_all", result)

    async def test_android_scripts(self, client: MCPTestClient):
        """Test Android-specific scripts."""
        if not self.android_test:
            return

        self.print_section("Android-Specific Scripts")

        scripts = [
            ("android_load_script_anti_DexHelper_hook_clone", {}),
            ("android_load_script_anti_DexHelper_hook_pthread", {}),
            ("android_load_script_anti_DexHelper", {"hook_addr_list": self.android_hook_addrs}),
            ("android_load_hook_net_libssl", {}),
            ("android_load_hook_clone", {"anti_so_name_tag": self.android_so}),
            ("android_load_hook_activity", {"package_name": self.android_pkg, "activity_name": self.android_activity}),
        ]

        for name, args in scripts:
            result = await client.load_script(name, **args)
            self.record(name, result)

    async def test_windows_scripts(self, client: MCPTestClient):
        """Test Windows-specific scripts."""
        if not self.windows_test:
            return

        self.print_section("Windows-Specific Scripts")

        # Single API monitor
        result = await client.load_script(
            "windows_load_monitor_api",
            module_name=self.windows_module, api_name=self.windows_api)
        self.record("windows_load_monitor_api", result)

        # Registry monitor
        result = await client.load_script(
            "windows_load_monitor_registry",
            api_name="RegSetValueExA", registry_path=self.windows_reg_path)
        self.record("windows_load_monitor_registry", result)

        # File monitor
        result = await client.load_script(
            "windows_load_monitor_file",
            api_name="CreateFileW", file_path=self.windows_file_path)
        self.record("windows_load_monitor_file", result)

    async def run(self):
        """Run all script tests."""
        self.print_header("Script Management Tests")
        print(f"Target: {self.target_package}")
        print(f"Android tests: {self.android_test}")
        print(f"Windows tests: {self.windows_test}")

        async with MCPTestClient(self.url) as client:
            print("\n[+] Connected to MCP server")

            if not await self.setup(client):
                print("[-] Setup failed, aborting")
                return

            await self.test_script_management(client)
            await self.test_android_scripts(client)
            await self.test_windows_scripts(client)

            await client.get_new_messages()
            await client.detach()

            self.print_summary()


if __name__ == "__main__":
    run_test_suite(ScriptTestRunner)
