"""
Frida MCP Server - Minimal Android Hook Service using FastMCP
"""

import time
import os
from typing import Optional, Dict, Any, Deque, List
from collections import deque
from pydantic import Field
import platform # New import

import frida
from mcp.server.fastmcp import FastMCP

from config.default_config import load_config

from util.device_manager_android import AndroidDeviceManager
from util.device_manager_windows import WindowsDeviceManager
from util.inject import BaseInjector # New import
from util.inject_android import AndroidInjector
from util.inject_windows import WindowsInjector # New import

# Global state management - simplified
device: Optional[frida.core.Device] = None
injector: Optional[BaseInjector] = None
device_manager: Optional[DeviceManager] = None # New global variable

# Global message buffer (store raw log lines)
messages_buffer: Deque[str] = deque(maxlen=5000)

# Append client-side Frida logs to the global buffer
def _frida_log(text: str) -> None:
    try:
        messages_buffer.append(f"[frida] {text}")
    except Exception:
        pass

# Initialize FastMCP
mcp = FastMCP("frida-mcp")


CONFIG = load_config()



def _resolve_script_content(initial_script: Optional[str], script_file_path: Optional[str]) -> tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    解析脚本内容，优先使用文件路径，fallback到代码字符串
    
    Args:
        initial_script: JS代码字符串
        script_file_path: JS文件绝对路径
        
    Returns:
        tuple: (script_content, error_response)
        - 成功时返回 (script_content_string, None)
        - 失败时返回 (None, error_dict)
    """
    if script_file_path:
        if not os.path.isabs(script_file_path):
            return None, {
                "status": "error",
                "message": "script_file_path must be an absolute path"
            }
        if not script_file_path.endswith('.js'):
            return None, {
                "status": "error", 
                "message": "script_file_path must be a .js file"
            }
        try:
            with open(script_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            _frida_log(f"Loaded JS script from file: {script_file_path}")
            return content, None
        except Exception as e:
            return None, {
                "status": "error",
                "message": f"Failed to read JS file {script_file_path}: {str(e)}"
            }
    elif initial_script:
        return initial_script, None
    else:
        return None, None

# Internal helper function for device connection
async def ensure_device_connected(device_id: Optional[str] = None) -> bool:
    """
    Internal helper to ensure device is connected.
    Returns True if successful, False otherwise.
    """
    global device, injector, device_manager
    
    if device:
        try:
            # Test if device is still connected
            device.id
            if injector and device_manager: # Ensure injector and device_manager are also set if device is connected
                return True
        except:
            device = None
            injector = None
            device_manager = None
    
    # Determine OS and choose appropriate injector and device manager
    current_os = platform.system()
    
    # Resolution order (minimal change):
    # 1) Explicit device_id param
    # 2) device_id from CONFIG
    # 3) USB device
    # 4) Remote device via localhost:server_port (requires external port-forward)
    device_id_to_use = device_id or CONFIG.device_id
    try:
        if device_id_to_use:
            device = frida.get_device(device_id_to_use)
            if current_os == "Windows":
                injector = WindowsInjector(device, messages_buffer, _frida_log)
                device_manager = WindowsDeviceManager(CONFIG)
            else: # Default to Android for other OS or if not Windows
                injector = AndroidInjector(device, messages_buffer, _frida_log)
                device_manager = AndroidDeviceManager(CONFIG)
            return True
    except Exception:
        pass
    try:
        device = frida.get_usb_device(timeout=5)
        if current_os == "Windows":
            injector = WindowsInjector(device, messages_buffer, _frida_log)
            device_manager = WindowsDeviceManager(CONFIG)
        else: # Default to Android for other OS or if not Windows
            injector = AndroidInjector(device, messages_buffer, _frida_log)
            device_manager = AndroidDeviceManager(CONFIG)
        return True
    except Exception:
        pass
    try:
        port = int(CONFIG.server_port or 27042)
        # Ensure ADB port forwarding before attempting remote connect (Android specific)
        if current_os != "Windows":
            try:
                dm = AndroidDeviceManager(CONFIG)
                dm.setup_port_forward()
                time.sleep(0.5)
            except Exception:
                pass
        
        manager = frida.get_device_manager()
        device_remote = manager.add_remote_device(f"127.0.0.1:{port}")
        if device_remote:
            device = device_remote
            if current_os == "Windows":
                injector = WindowsInjector(device, messages_buffer, _frida_log)
                device_manager = WindowsDeviceManager(CONFIG)
            else: # Default to Android for other OS or if not Windows
                injector = AndroidInjector(device, messages_buffer, _frida_log)
                device_manager = AndroidDeviceManager(CONFIG)
            return True
    except Exception:
        pass
    return False

# Frida Server Start/Stop

@mcp.tool()
async def start_android_frida_server() -> Dict[str, Any]:
    """
    启动 Android 设备上的 frida-server。

    - 来源: 使用 config.json 的 server_path/server_name/server_port
    - 返回: {status, message}
    """
    dm = AndroidDeviceManager(CONFIG)
    # If already running, no-op
    if dm.check_frida_status(silent=True):
        return {
            "status": "success",
            "message": "frida-server already running",
        }
    ok = dm.start_frida_server()
    return {
        "status": "success" if ok else "error",
        "message": "frida-server started" if ok else "failed to start frida-server"
    }


@mcp.tool()
async def stop_android_frida_server() -> Dict[str, Any]:
    """
    停止 Android 设备上的 frida-server。

    - 返回: {status, message}
    """
    dm = AndroidDeviceManager(CONFIG)
    # If not running, no-op
    if not dm.check_frida_status(silent=True):
        return {"status": "success", "message": "frida-server already stopped"}
    ok = dm.stop_frida_server()
    return {"status": "success" if ok else "error", "message": "frida-server stopped" if ok else "failed to stop frida-server"}


@mcp.tool()
async def check_android_frida_status() -> Dict[str, Any]:
    """
    检测 Android frida-server 是否在运行。

    - 返回: {status, running}
    """
    dm = AndroidDeviceManager(CONFIG)
    running = bool(dm.check_frida_status(silent=True))
    return {"status": "success", "running": running}


@mcp.tool()
async def start_windows_frida_server() -> Dict[str, Any]:
    """
    启动 Windows 本地 frida-server。

    - 来源: 使用 config.json 的 server_path/server_name
    - 返回: {status, message}
    """
    dm = WindowsDeviceManager(CONFIG)
    if dm.check_frida_status(silent=True):
        return {
            "status": "success",
            "message": "frida-server already running",
        }
    ok = dm.start_frida_server()
    return {
        "status": "success" if ok else "error",
        "message": "frida-server started" if ok else "failed to start frida-server"
    }


@mcp.tool()
async def stop_windows_frida_server() -> Dict[str, Any]:
    """
    停止 Windows 本地 frida-server。

    - 返回: {status, message}
    """
    dm = WindowsDeviceManager(CONFIG)
    if not dm.check_frida_status(silent=True):
        return {"status": "success", "message": "frida-server already stopped"}
    ok = dm.stop_frida_server()
    return {"status": "success" if ok else "error", "message": "frida-server stopped" if ok else "failed to stop frida-server"}


@mcp.tool()
async def check_windows_frida_status() -> Dict[str, Any]:
    """
    检测 Windows 本地 frida-server 是否在运行。

    - 返回: {status, running}
    """
    dm = WindowsDeviceManager(CONFIG)
    running = bool(dm.check_frida_status(silent=True))
    return {"status": "success", "running": running}

# Frida Tools Function

@mcp.tool()
def enumerate_processes(
        device_id: Optional[str] = Field(default=None,
                                         description="Optional ID of the device to enumerate processes from. Uses USB device if not specified.")
) -> List[Dict[str, Any]]:
    """List all processes running on the system.

    Returns:
        A list of process information dictionaries containing:
        - pid: Process ID
        - name: Process name
    """
    if device_id:
        _device = frida.get_device(device_id)
    else:
        _device = frida.get_usb_device()
    processes = _device.enumerate_processes()
    return [{"pid": _process.pid, "name": _process.name} for _process in processes]

@mcp.tool()
def enumerate_devices() -> List[Dict[str, Any]]:
    """List all devices connected to the system.

    Returns:
        A list of device information dictionaries containing:
        - id: Device ID
        - name: Device name
        - type: Device type
    """
    devices = frida.enumerate_devices()
    return [
        {
            "id": _device.id,
            "name": _device.name,
            "type": _device.type,
        }
        for _device in devices
    ]


@mcp.tool()
def get_device(device_id: str = Field(description="The ID of the device to get")) -> Dict[str, Any]:
    """Get a device by its ID.

    Returns:
        Information about the device
    """
    try:
        _device = frida.get_device(device_id)
        return {
            "id": _device.id,
            "name": _device.name,
            "type": _device.type,
        }
    except frida.InvalidArgumentError:
        raise ValueError(f"Device with ID {device_id} not found")


@mcp.tool()
def get_usb_device() -> Dict[str, Any]:
    """Get the USB device connected to the system.

    Returns:
        Information about the USB device
    """
    try:
        _device = frida.get_usb_device()
        return {
            "id": _device.id,
            "name": _device.name,
            "type": _device.type,
        }
    except frida.InvalidArgumentError:
        raise ValueError("No USB device found")


@mcp.tool()
def get_local_device() -> Dict[str, Any]:
    """Get the local device.

    Returns:
        Information about the local device
    """
    try:
        _device = frida.get_local_device()
        return {
            "id": _device.id,
            "name": _device.name,
            "type": _device.type,
        }
    except frida.InvalidArgumentError:  # Or other relevant Frida exceptions
        raise ValueError("No local device found or error accessing it.")


@mcp.tool()
def get_process_by_name(
        name: str = Field(description="The name (or part of the name) of the process to find. Case-insensitive."),
        device_id: Optional[str] = Field(default=None,
                                         description="Optional ID of the device to search the process on. Uses USB device if not specified.")) -> dict:
    """Find a process by name."""
    if device_id:
        _device = frida.get_device(device_id)
    else:
        _device = frida.get_usb_device()
    for proc in _device.enumerate_processes():
        if name.lower() in proc.name.lower():
            return {"pid": proc.pid, "name": proc.name, "found": True}
    return {"found": False, "error": f"Process '{name}' not found"}

@mcp.tool()
async def get_frontmost_application(device_id: str = Field(description="The ID of the device to get")) -> Dict[str, Any]:
    """
    获取当前前台应用信息。

    - 返回: {status, application?{identifier,name,pid}, message?}
    """

    try:
        frontmost = frida.get_device(device_id).get_frontmost_application()
        if frontmost:
            return {
                "status": "success",
                "application": {
                    "identifier": frontmost.identifier,
                    "name": frontmost.name,
                    "pid": frontmost.pid
                }
            }
        else:
            return {
                "status": "success",
                "application": None,
                "message": "No frontmost application found"
            }
    except frida.InvalidArgumentError:
        raise ValueError(f"Device with ID {device_id} not found")
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# Frida Resource

@mcp.resource("frida://version")
def get_version() -> str:
    """Get the Frida version."""
    return frida.__version__


@mcp.resource("frida://usb_processes")
def get_processes_resource() -> str:
    """Get a list of all processes from the USB device as a readable string."""
    _device = frida.get_usb_device()
    processes = _device.enumerate_processes()
    return "\n".join([f"PID: {p.pid}, Name: {p.name}" for p in processes])


@mcp.resource("frida://devices")
def get_devices_resource() -> str:
    """Get a list of all devices as a readable string."""
    devices = frida.enumerate_devices()
    return "\n".join([f"ID: {d.id}, Name: {d.name}, Type: {d.type}" for d in devices])

# Js Console Log

@mcp.tool()
async def get_messages(max_messages: int = 100) -> Dict[str, Any]:
    """
    获取全局 hook/log 文本缓冲（非消费模式）。

    Args:
      - max_messages: 返回的最大条数（默认 100）

    Returns:
      - {status, messages, remaining}
    """
    if max_messages is None or max_messages < 0:
        max_messages = 0
    buffer = messages_buffer
    if not buffer or len(buffer) == 0:
        return {
            "status": "success",
            "messages": [],
            "remaining": 0
        }
    snapshot = list(buffer)
    if max_messages > 0:
        snapshot = snapshot[-max_messages:]
    else:
        snapshot = []
    return {
        "status": "success",
        "messages": snapshot,
        "remaining": len(buffer)
    }


# MCP Tool Handlers using FastMCP decorators

@mcp.tool()
async def list_applications() -> Dict[str, Any]:
    """
    列出设备上的已安装应用（含运行与未运行）。

    - 返回: {status, count, applications:[{identifier,name,pid?}]}
    """
    if not await ensure_device_connected():
        return {
            "status": "error",
            "message": "Failed to connect to device. Ensure frida-server is running."
        }
    
    if not device_manager:
        return {
            "status": "error",
            "message": "Device manager not initialized. Device not connected?"
        }

    try:
        applications = device_manager.get_applications()
        app_list = []
        for app in applications:
            app_list.append({
                "identifier": app.identifier,
                "name": app.name,
                "pid": app.pid if hasattr(app, 'pid') else None
            })
        
        # Sort by name for easier reading
        app_list.sort(key=lambda x: x["name"].lower())
        
        return {
            "status": "success",
            "count": len(app_list),
            "applications": app_list
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
async def attach(
    target: str,
    initial_script: Optional[str] = None,
    script_file_path: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    附加到运行中的进程，并可选注入脚本。

    Args:
      - target: PID 字符串或包名
      - initial_script: 可选注入的 Frida JS 代码字符串
      - script_file_path: 可选注入的 JS 文件绝对路径（优先于 initial_script）
      - output_file: 可选的本地电脑文件路径，用于保存 hook 输出（非安卓设备路径）

    Returns:
      - {status, pid, target, name, script_loaded, message}
    """
    # Ensure device is connected
    if not await ensure_device_connected():
        return {
            "status": "error",
            "message": "Failed to connect to device. Ensure frida-server is running."
        }
    
    if not target or not target.strip():
        return {
            "status": "error",
            "message": "Target cannot be empty"
        }
    
    # 解析脚本内容
    script_content, error_response = _resolve_script_content(initial_script, script_file_path)
    if error_response:
        return error_response
        
    if injector:
        return await injector.attach(target, script_content, output_file)
    else:
        return {"status": "error", "message": "Injector not initialized. Device not connected?"}


@mcp.tool()
async def spawn(
    package_name: str,
    initial_script: Optional[str] = None,
    script_file_path: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    拉起应用（挂起态）并附加，可选在恢复前注入脚本。

    Args:
      - package_name: 应用包名
      - initial_script: 可选注入的 Frida JS 代码字符串
      - script_file_path: 可选注入的 JS 文件绝对路径（优先于 initial_script）
      - output_file: 可选的本地电脑文件路径，用于保存 hook 输出（非安卓设备路径）

    Returns:
      - {status, pid, package, script_loaded, message}
    """
    # Ensure device is connected
    if not await ensure_device_connected():
        return {
            "status": "error",
            "message": "Failed to connect to device. Ensure frida-server is running."
        }
    
    # 解析脚本内容
    script_content, error_response = _resolve_script_content(initial_script, script_file_path)
    if error_response:
        return error_response
        
    if injector:
        return await injector.spawn(package_name, script_content, output_file)
    else:
        return {"status": "error", "message": "Injector not initialized. Device not connected?"}


if __name__ == "__main__":
    mcp.run()