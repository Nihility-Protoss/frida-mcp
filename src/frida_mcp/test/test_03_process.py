"""
Test process management functions: enumerate_processes, get_process_by_name, resume_process, kill_process
"""

import sys
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_utils import MCPTestClient, TestRunner, run_test_suite


class ProcessTestRunner(TestRunner):
    """Test runner for process management tests."""
    
    # Configuration
    device_id: str = "local"
    process_name: str = "frida-server-16.6.6.exe"  # Set to empty to skip name-based tests
    
    async def test_enumerate_processes(self, client: MCPTestClient) -> List[Dict[str, Any]]:
        """Test enumerate_processes - list all running processes."""
        self.print_section("Test 1: Enumerate Processes")
        
        result = await client.call("enumerate_processes", {"device_id": self.device_id})
        processes = result if isinstance(result, list) else []
        
        if processes:
            print(f"[+] Found {len(processes)} processes")
            # Display first 10 processes
            for proc in processes[:10]:
                print(f"    {proc.get('pid')}: {proc.get('name')}")
            if len(processes) > 10:
                print(f"    ... and {len(processes) - 10} more")
        
        self.record("enumerate_processes", {
            "status": "success" if processes else "error",
            "count": len(processes)
        })
        return processes
    
    async def test_get_process_by_name(self, client: MCPTestClient) -> Dict[str, Any]:
        """Test get_process_by_name - find process by name."""
        self.print_section("Test 2: Get Process by Name")
        
        if not self.process_name:
            print("[!] No process name configured, skipping")
            return self.record("get_process_by_name", {"status": "skipped"})
        
        print(f"[*] Searching for: {self.process_name}")
        result = await client.call("get_process_by_name", {
            "device_id": self.device_id,
            "name": self.process_name
        })
        
        if result.get("found"):
            print(f"[+] Found: {result.get('name')} (PID: {result.get('pid')})")
        else:
            print(f"[-] Not found: {result.get('error', 'Unknown error')}")
        
        return self.record("get_process_by_name", {
            "status": "success" if result.get("found") else "error",
            "result": result
        })
    
    async def test_resume_process(self, client: MCPTestClient, pid: int) -> Dict[str, Any]:
        """Test resume_process - resume a suspended process."""
        self.print_section("Test 3: Resume Process")
        print(f"[!] Caution: This test is disabled by default")
        print(f"[*] Would resume PID: {pid}")
        
        # Uncomment to enable:
        # result = await client.call("resume_process", {"device_id": self.device_id, "pid": pid})
        # return self.record("resume_process", result)
        
        return self.record("resume_process", {"status": "skipped"})
    
    async def test_kill_process(self, client: MCPTestClient, pid: int) -> Dict[str, Any]:
        """Test kill_process - terminate a process."""
        self.print_section("Test 4: Kill Process")
        print(f"[!] Caution: This test is disabled by default")
        print(f"[*] Would kill PID: {pid}")
        
        # Uncomment to enable:
        # result = await client.call("kill_process", {"device_id": self.device_id, "pid": pid})
        # return self.record("kill_process", result)
        
        return self.record("kill_process", {"status": "skipped"})
    
    async def run(self):
        """Run all process management tests."""
        self.print_header("Process Management Tests")
        print(f"Device ID: {self.device_id}")
        print(f"Process Name: {self.process_name or '(not set)'}")
        
        async with MCPTestClient(self.url) as client:
            print("\n[+] Connected to MCP server")
            
            # Enumerate processes
            processes = await self.test_enumerate_processes(client)
            
            # Find process by name
            find_result = await self.test_get_process_by_name(client)
            
            # If found, optionally test resume/kill
            if find_result.get("result", {}).get("found"):
                pid = find_result["result"]["pid"]
                await self.test_resume_process(client, pid)
                await self.test_kill_process(client, pid)
            
            self.print_summary()


if __name__ == "__main__":
    run_test_suite(ProcessTestRunner)
