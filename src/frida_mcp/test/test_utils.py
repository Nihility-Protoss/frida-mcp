"""
Shared test utilities for Frida MCP test suite.

This module provides common functionality for all test files including:
- MCP client initialization
- Response parsing and validation
- Common test operations (spawn, attach, inject, etc.)
- Result formatting and summary generation
"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path

# Setup path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import MCP client
try:
    from fastmcp import Client
except ImportError:
    print("Error: 'fastmcp' not found. Please install it using 'pip install fastmcp'")
    sys.exit(1)

# Default MCP server URL
DEFAULT_URL = "http://192.168.40.129:8032/mcp"


class MCPTestClient:
    """Wrapper for MCP client with common test operations."""
    
    def __init__(self, url: str = DEFAULT_URL):
        self.url = url
        self._client: Optional[Client] = None
    
    async def __aenter__(self):
        self._client = Client(self.url)
        await self._client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def call(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call an MCP tool and parse the response."""
        try:
            result = await self._client.call_tool(tool_name, arguments=arguments or {})
            return self._parse_result(result)
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @staticmethod
    def _parse_result(result) -> Dict[str, Any]:
        """Parse MCP tool result into a standard dict."""
        if hasattr(result, 'content') and result.content:
            try:
                return json.loads(result.content[0].text)
            except json.JSONDecodeError:
                return {"status": "error", "message": "Invalid JSON response"}
        return {"status": "error", "message": "Empty or invalid response"}
    
    # Common test operations
    async def spawn(self, package_name: str, args: str = "") -> Dict[str, Any]:
        """Spawn a process and return result."""
        print(f"[*] Spawning: {package_name}" + (f" with args: {args}" if args else ""))
        result = await self.call("spawn", {"package_name": package_name, "args": args})
        if result.get("status") == "success":
            print(f"[+] Spawned: {result.get('package', package_name)} (PID: {result.get('pid')})")
        else:
            print(f"[-] Spawn failed: {result.get('message', 'Unknown error')}")
        return result
    
    async def attach(self, target: str) -> Dict[str, Any]:
        """Attach to a running process."""
        print(f"[*] Attaching to: {target}")
        result = await self.call("attach", {"target": target})
        if result.get("status") == "success":
            print(f"[+] Attached to: {result.get('name', target)} (PID: {result.get('pid')})")
        else:
            print(f"[-] Attach failed: {result.get('message', 'Unknown error')}")
        return result
    
    async def detach(self) -> Dict[str, Any]:
        """Detach from current session."""
        print(f"[*] Detaching...")
        result = await self.call("detach")
        status = "success" if result.get("status") == "success" else "error"
        print(f"[+] Detached" if status == "success" else f"[-] Detach failed: {result.get('message')}")
        return result
    
    async def get_session_info(self) -> Dict[str, Any]:
        """Get current session information."""
        result = await self.call("get_session_info")
        if result.get("status") == "success":
            print(f"[+] Session: {result.get('target')} (PID: {result.get('pid')})")
        return result
    
    async def inject_script(self, script_content: str, script_name: str = "test_script") -> Dict[str, Any]:
        """Inject and run a script."""
        print(f"[*] Injecting script: {script_name}")
        result = await self.call("inject_user_script_run_all", {
            "script_content": script_content,
            "script_name": script_name
        })
        if result.get("status") == "success":
            print(f"[+] Script injected successfully")
        else:
            print(f"[-] Inject failed: {result.get('message', 'Unknown error')}")
        return result
    
    async def get_new_messages(self) -> List[str]:
        """Get new log messages."""
        result = await self.call("get_new_messages")
        messages = result.get("messages", [])
        if messages:
            print(f"[+] Retrieved {len(messages)} new messages")
            for msg in messages:
                print(f"    {msg}")
        return messages
    
    async def load_script(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Load a built-in script."""
        print(f"[*] Loading script: {tool_name}")
        result = await self.call(tool_name, kwargs)
        if result.get("status") == "success":
            print(f"[+] Script loaded: {tool_name}")
        else:
            print(f"[-] Load failed: {result.get('message', 'Unknown error')}")
        return result


class TestRunner:
    """Base class for running test suites."""
    
    def __init__(self, url: str = DEFAULT_URL):
        self.url = url
        self.results: Dict[str, Dict[str, Any]] = {}
    
    def print_header(self, title: str):
        """Print test header."""
        print(f"\n{'='*50}")
        print(f"  {title}")
        print(f"{'='*50}")
    
    def print_section(self, title: str):
        """Print test section."""
        print(f"\n[{title}]")
        print("-" * 40)
    
    def record(self, name: str, result: Dict[str, Any]):
        """Record a test result."""
        self.results[name] = result
        return result
    
    def print_summary(self):
        """Print test summary."""
        print(f"\n{'='*50}")
        print("Test Summary:")
        print(f"{'='*50}")
        
        passed = sum(1 for r in self.results.values() if r.get("status") == "success")
        total = len(self.results)
        
        for name, result in self.results.items():
            status = "✓" if result.get("status") == "success" else "✗"
            print(f"  {status} {name}")
        
        print(f"\nTotal: {passed}/{total} passed")
        return passed == total
    
    async def run(self):
        """Override this method in subclasses."""
        raise NotImplementedError("Subclasses must implement run()")


# Convenience function for running tests
def run_test_suite(runner_class: type, url: str = DEFAULT_URL):
    """Run a test suite class."""
    async def main():
        runner = runner_class(url)
        try:
            await runner.run()
        except Exception as e:
            print(f"\n[!] Test suite error: {e}")
            raise
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Test cancelled by user.")
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
