"""
Test configuration management tools: config_get, config_set, config_save, config_init
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_utils import MCPTestClient, TestRunner, run_test_suite


class ConfigTestRunner(TestRunner):
    """Test runner for configuration management tests."""
    
    async def test_config_get(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test config_get - retrieve current configuration."""
        self.print_section("Test 1: Get Configuration")
        result = await client.call("config_get")
        
        if result.get("status") == "success":
            print(f"[+] Active config: {result.get('active_config')}")
            print(f"[+] Global config path: {result.get('paths', {}).get('global', {}).get('path')}")
            print(f"[+] Project config path: {result.get('paths', {}).get('project', {}).get('path')}")
        return self.record("config_get", result)
    
    async def test_config_set(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test config_set - modify configuration values."""
        self.print_section("Test 2: Set Configuration")
        
        # Test setting device_id
        test_device = "local"
        print(f"[*] Setting device_id to: {test_device}")
        
        result = await client.call("config_set", {"device_id": test_device})
        if result.get("status") == "success":
            updated = result.get("active_config", {}).get("device_id")
            print(f"[+] Updated device_id: {updated}")
            if updated == test_device:
                print("[✓] Value updated correctly in memory")
        return self.record("config_set", result)
    
    async def test_config_save(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test config_save - persist configuration to file."""
        self.print_section("Test 3: Save Configuration")
        
        result = await client.call("config_save")
        if result.get("status") == "success":
            print(f"[+] Config saved to: {result.get('path')}")
        return self.record("config_save", result)
    
    async def test_config_init(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test config_init - initialize project configuration."""
        self.print_section("Test 4: Initialize Configuration")
        
        test_path = os.path.abspath("test_frida_mcp_config.json")
        print(f"[*] Initializing with custom path: {test_path}")
        
        result = await client.call("config_init", {"new_project_config_path": test_path})
        
        if result.get("status") == "success":
            print(f"[+] Project config path: {result.get('project_config_path')}")
            
            # Cleanup
            if os.path.exists(test_path):
                os.remove(test_path)
                print(f"[+] Cleaned up temporary file")
        return self.record("config_init", result)
    
    async def run(self):
        """Run all configuration tests."""
        self.print_header("Configuration Management Tests")
        
        async with MCPTestClient(self.url) as client:
            print("\n[+] Connected to MCP server")
            
            await self.test_config_get(client)
            await self.test_config_set(client)
            await self.test_config_save(client)
            await self.test_config_init(client)
            
            self.print_summary()


if __name__ == "__main__":
    run_test_suite(ConfigTestRunner)
