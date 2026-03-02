import asyncio
import json
import os
import sys
from typing import Dict, Any

try:
    from fastmcp import Client
except ImportError:
    print("Error: 'fastmcp' not found. Please install it using 'pip install fastmcp'")
    sys.exit(1)

# Frida MCP server connection settings
DEFAULT_URL = "http://192.168.40.129:8032/mcp"

async def test_config_tools(url: str = DEFAULT_URL):
    """
    测试 Frida MCP 的配置管理工具: config_get, config_set, config_save, config_init
    """
    print(f"[*] Testing configuration tools at: {url}")
    
    try:
        async with Client(url) as client:
            print("[+] Connection established.")
            
            # --- 1. Test config_get ---
            print("\n[1] Testing 'config_get'...")
            result = await client.call_tool("config_get")
            config_data = json.loads(result.content[0].text)
            print(f"    - Status: {config_data.get('status')}")
            print(f"    - Active Config: {config_data.get('active_config')}")
            original_config = config_data.get('active_config')

            # --- 2. Test config_set ---
            print("\n[2] Testing 'config_set'...")
            # 修改 device_id 进行测试
            test_device_id = "test_device_123"
            set_result = await client.call_tool("config_set", arguments={"device_id": test_device_id})
            set_data = json.loads(set_result.content[0].text)
            print(f"    - Status: {set_data.get('status')}")
            print(f"    - Updated device_id: {set_data.get('active_config', {}).get('device_id')}")
            
            if set_data.get('active_config', {}).get('device_id') == test_device_id:
                print("    [✔] config_set successfully updated memory.")
            else:
                print("    [✘] config_set failed to update memory.")

            # --- 3. Test config_save ---
            print("\n[3] Testing 'config_save'...")
            save_result = await client.call_tool("config_save")
            save_data = json.loads(save_result.content[0].text)
            print(f"    - Status: {save_data.get('status')}")
            print(f"    - Saved to: {save_data.get('path')}")
            
            if save_data.get('status') == "success":
                print("    [✔] config_save reported success.")
            else:
                print(f"    [✘] config_save failed: {save_data.get('message')}")

            # --- 4. Test config_init ---
            print("\n[4] Testing 'config_init'...")
            # 创建一个临时的测试配置路径
            test_init_path = os.path.abspath("test_frida_mcp_config.json")
            init_result = await client.call_tool("config_init", arguments={"new_project_config_path": test_init_path})
            init_data = json.loads(init_result.content[0].text)
            print(f"    - Status: {init_data.get('status')}")
            print(f"    - New Project Config Path: {init_data.get('project_config_path')}")
            
            if init_data.get('status') == "success" and init_data.get('project_config_path') == test_init_path:
                print("    [✔] config_init successfully initialized new project path.")
                # 清理生成的临时文件
                if os.path.exists(test_init_path):
                    os.remove(test_init_path)
                    print(f"    - Cleaned up temporary test file: {test_init_path}")
            else:
                print(f"    [✘] config_init failed: {init_data.get('message')}")

            # --- 5. Restore original config (Optional but good practice) ---
            print("\n[5] Restoring original device_id...")
            await client.call_tool("config_set", arguments={"device_id": original_config.get("device_id")})
            print(f"    - Restored device_id to: {original_config.get('device_id')}")

            print("\n" + "="*50)
            print("CONFIGURATION TOOLS TEST COMPLETE")
            print("="*50)
            
    except Exception as e:
        print(f"[-] Test FAILED: {e}")

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    try:
        asyncio.run(test_config_tools(target_url))
    except KeyboardInterrupt:
        print("\n[*] Test cancelled.")
