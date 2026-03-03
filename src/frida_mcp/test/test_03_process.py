# Baseline Test @3
"""
测试进程管理相关函数
测试以下四个函数：
- enumerate_processes
- get_process_by_name
- resume_process
- kill_process
"""

import asyncio
import json
import sys
from typing import Dict, Any

# 使用FastMCP的Client
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from fastmcp import Client
except ImportError:
    print("Error: 'fastmcp' not found. Please install it using 'pip install fastmcp'")
    sys.exit(1)

# 默认MCP服务器地址
DEFAULT_URL = "http://192.168.40.129:8032/mcp"

# 全局变量，由用户输入
device_id: str = "local"  # 设备ID，如USB设备或本地设备
process_name: str = "frida-server-16.6.6.exe"  # 进程名称，用于测试

async def test_enumerate_processes(client: Client) -> Dict[str, Any]:
    """测试枚举进程函数"""
    print(f"[*] Testing enumerate_processes...")
    try:
        result = await client.call_tool(
            "enumerate_processes",
            arguments={"device_id": device_id})
        
        if hasattr(result, 'content') and result.content:
            processes = [json.loads(i.text) for i in result.content]
            print(f"[+] Found {len(result.content)} processes")

            # 显示所有进程
            for i, proc in enumerate(processes):
                print(f"    {proc['pid']}: {proc['name']}")
            
            # if len(processes) > 10:
            #     print(f"    ... and {len(processes) - 10} more")
                
            return {"status": "success", "processes": processes}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}
            
    except Exception as e:
        print(f"[-] enumerate_processes failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_get_process_by_name(client: Client) -> Dict[str, Any]:
    """测试通过名称查找进程函数"""
    print(f"[*] Testing get_process_by_name with name: {process_name}")
    try:
        result = await client.call_tool(
            "get_process_by_name",
            arguments={"device_id": device_id, "name": process_name})
        
        if hasattr(result, 'content') and result.content:
            print(result.content)
            process_info = json.loads(result.content[0].text)
            
            if process_info.get('found'):
                print(f"[+] Found process: {process_info['name']} (PID: {process_info['pid']})")
                return {"status": "success", "process": process_info}
            else:
                print(f"[-] Process '{process_name}' not found")
                return {"status": "error", "message": process_info.get('error', 'Process not found')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}
            
    except Exception as e:
        print(f"[-] get_process_by_name failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_resume_process(client: Client, pid: int) -> Dict[str, Any]:
    """测试恢复进程函数"""
    print(f"[*] Testing resume_process with PID: {pid}")
    try:
        result = await client.call_tool(
            "resume_process",
            arguments={"device_id": device_id, "pid": pid})
        
        if hasattr(result, 'content') and result.content:
            resume_result = json.loads(result.content[0].text)
            
            if resume_result.get('status') == 'success':
                print(f"[+] Successfully resumed process {pid}")
                return {"status": "success", "message": resume_result['message']}
            else:
                print(f"[-] Failed to resume process: {resume_result.get('message', 'Unknown error')}")
                return {"status": "error", "message": resume_result.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}
            
    except Exception as e:
        print(f"[-] resume_process failed: {e}")
        return {"status": "error", "message": str(e)}


async def test_kill_process(client: Client, pid: int) -> Dict[str, Any]:
    """测试终止进程函数"""
    print(f"[*] Testing kill_process with PID: {pid}")
    try:
        result = await client.call_tool(
            "kill_process",
            arguments={"device_id": device_id, "pid": pid})
        
        if hasattr(result, 'content') and result.content:
            kill_result = json.loads(result.content[0].text)
            
            if kill_result.get('status') == 'success':
                print(f"[+] Successfully killed process {pid}")
                return {"status": "success", "message": kill_result['message']}
            else:
                print(f"[-] Failed to kill process: {kill_result.get('message', 'Unknown error')}")
                return {"status": "error", "message": kill_result.get('message', 'Unknown error')}
        else:
            print(f"[!] Unexpected response: {result}")
            return {"status": "error", "message": "Invalid response format"}
            
    except Exception as e:
        print(f"[-] kill_process failed: {e}")
        return {"status": "error", "message": str(e)}


async def run_all_tests(url: str):
    """运行所有进程管理测试"""
    print(f"[*] Starting process management tests...")
    print(f"[*] MCP Server URL: {url}")
    print(f"[*] Device ID: {device_id}")
    print(f"[*] Process Name: {process_name}")
    print("-" * 50)
    
    try:
        async with Client(url) as client:
            print("[+] Connected to MCP server")
            
            # 1. 测试枚举进程
            enumerate_result = await test_enumerate_processes(client)
            
            # 2. 测试通过名称查找进程
            if process_name:
                get_process_result = await test_get_process_by_name(client)
                
                # 如果找到了进程，获取PID用于后续测试
                if get_process_result['status'] == 'success':
                    test_pid = get_process_result['process']['pid']
                    
                    # 3. 测试恢复进程（仅当进程存在时）
                    print("[*] Testing resume_process test (use with caution)")
                    resume_result = {"status": "pass"}
                    resume_result = await test_resume_process(client, test_pid)

                    # 4. 测试终止进程（仅当进程存在时）
                    print("[*] Testing kill_process test (use with caution)")
                    kill_process = {"status": "pass"}
                    kill_process = await test_kill_process(client, test_pid)
                    
                    print("\n[+] Test completed. Use resume_process and kill_process with caution.")
                else:
                    print(f"[-] Process '{process_name}' not found, skipping PID-based tests")
            else:
                print("[-] No process name provided, skipping get_process_by_name test")
                
            # 总结
            print("\n" + "=" * 50)
            print("Test Summary:")
            print(f"- enumerate_processes: {'✓' if enumerate_result['status'] == 'success' else '✗'}")
            if process_name:
                print(f"- get_process_by_name: {'✓' if get_process_result['status'] == 'success' else '✗'}")
                print(f"- resume_process: {'✓' if resume_result['status'] == 'success' else '✗'}")
                print(f"- kill_process: {'✓' if kill_process['status'] == 'success' else '✗'}")
            
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