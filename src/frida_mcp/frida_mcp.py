"""
Frida MCP Server - Minimal Android Hook Service using FastMCP
"""

import time
import os
import json # New import
from typing import Optional, Dict, Any, Deque, List
from collections import deque
from pydantic import Field
import platform # New import

import frida
from mcp.server.fastmcp import FastMCP

from config.default_config import load_config, GLOBAL_CONFIG_PATH, PROJECT_CONFIG_PATH, FridaConfig

from util.frida_server_manager_android import AndroidServerManager
from util.frida_server_manager_windows import WindowsServerManager
from util.inject import BaseInjector
from util.inject_android import AndroidInjector
from util.inject_windows import WindowsInjector

# Global state management - simplified
device: Optional[frida.core.Device] = None
injector: Optional[BaseInjector] = None

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

@mcp.tool()
async def set_mcp_config(
    scope: str = Field(description="Scope: 'global' (package dir) or 'project' (current folder)"),
    server_path: Optional[str] = None,
    server_name: Optional[str] = None,
    server_port: Optional[int] = None,
    device_id: Optional[str] = None,
    adb_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    即时设置 Frida MCP 配置并保存到 config.json。
    """
    global CONFIG
    path = GLOBAL_CONFIG_PATH if scope.lower() == 'global' else PROJECT_CONFIG_PATH
    
    # Load existing config for that path if it exists
    current = FridaConfig()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            current = FridaConfig.from_dict(data)
        except:
            pass
    
    # Update fields only if they are provided
    if server_path is not None: current.server_path = server_path
    if server_name is not None: current.server_name = server_name
    if server_port is not None: current.server_port = server_port
    if device_id is not None: current.device_id = device_id
    if adb_path is not None: current.adb_path = adb_path
    
    # Save to file
    current.save(path)
    
    # Reload global CONFIG (so other tools use the updated values)
    CONFIG = load_config()
    
    return {
        "status": "success",
        "scope": scope,
        "path": path,
        "current_active_config": CONFIG.to_dict(),
        "message": f"Configuration saved to {path} and reloaded."
    }

@mcp.tool()
async def get_mcp_config() -> Dict[str, Any]:
    """
    获取当前活跃的配置以及全局和项目配置文件的状态。
    """
    return {
        "active_config": CONFIG.to_dict(),
        "global_config": {
            "path": GLOBAL_CONFIG_PATH,
            "exists": os.path.exists(GLOBAL_CONFIG_PATH)
        },
        "project_config": {
            "path": PROJECT_CONFIG_PATH,
            "exists": os.path.exists(PROJECT_CONFIG_PATH)
        }
    }



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
    Internal helper to ensure device is connected and managers are initialized.
    """
    global device, injector
    
    if device:
        try:
            device.id
            if injector:
                return True
        except:
            device = None
            injector = None
    
    current_os = platform.system()
    
    # Initialize Injector based on OS
    if current_os == "Windows":
        injector = WindowsInjector(messages_buffer, _frida_log)
    else:
        injector = AndroidInjector(messages_buffer, _frida_log)

    # Device acquisition logic
    device_id_to_use = device_id or CONFIG.device_id
    try:
        if device_id_to_use:
            device = frida.get_device(device_id_to_use)
            return True
    except: pass

    try:
        device = frida.get_usb_device(timeout=1)
        return True
    except: pass

    try:
        port = int(CONFIG.server_port or 27042)
        # For Android, ensure ADB port forwarding before attempting remote connect
        if current_os != "Windows":
            try:
                # Temporarily create an AndroidServerManager to setup port forwarding
                temp_server_manager = AndroidServerManager(CONFIG)
                temp_server_manager.setup_port_forward()
                time.sleep(0.5)
            except: pass
        
        manager = frida.get_device_manager()
        device_remote = manager.add_remote_device(f"127.0.0.1:{port}")
        if device_remote:
            device = device_remote
            return True
    except: pass

    return False

# Frida Server Start/Stop

@mcp.tool()
async def start_android_frida_server() -> Dict[str, Any]:
    """
    启动 Android 设备上的 frida-server。

    - 来源: 使用 config.json 的 server_path/server_name/server_port
    - 返回: {status, message}
    """
    dm = AndroidServerManager(CONFIG)
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
    dm = AndroidServerManager(CONFIG)
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
    dm = AndroidServerManager(CONFIG)
    running = bool(dm.check_frida_status(silent=True))
    return {"status": "success", "running": running}


@mcp.tool()
async def start_windows_frida_server() -> Dict[str, Any]:
    """
    启动 Windows 本地 frida-server。

    - 来源: 使用 config.json 的 server_path/server_name
    - 返回: {status, message}
    """
    dm = WindowsServerManager(CONFIG)
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
    dm = WindowsServerManager(CONFIG)
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
    dm = WindowsServerManager(CONFIG)
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
async def list_applications(
    device_id: Optional[str] = Field(default=None, description="Optional ID of the device to list applications from.")
) -> Dict[str, Any]:
    """
    列出设备上的已安装应用（含运行与未运行）。

    - 返回: {status, count, applications:[{identifier,name,pid?}]}
    """
    try:
        _device = frida.get_device(device_id) if device_id else device
        applications = _device.enumerate_applications()
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
    device_id: Optional[str] = Field(default=None, description="Optional ID of the device to attach to."),
    initial_script: Optional[str] = None,
    script_file_path: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    附加到运行中的进程，并可选注入脚本。

    Args:
      - target: PID 字符串或包名
      - device_id: 可选的设备 ID
      - initial_script: 可选注入的 Frida JS 代码字符串
      - script_file_path: 可选注入的 JS 文件绝对路径（优先于 initial_script）
      - output_file: 可选的本地电脑文件路径，用于保存 hook 输出（非安卓设备路径）

    Returns:
      - {status, pid, target, name, script_loaded, message}
    """
    # Ensure device is connected
    if not await ensure_device_connected(device_id):
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
        return await injector.attach(target, device_id, script_content, output_file)
    else:
        return {"status": "error", "message": "Injector not initialized. Device not connected?"}


@mcp.tool()
async def spawn(
    package_name: str,
    device_id: Optional[str] = Field(default=None, description="Optional ID of the device to spawn on."),
    initial_script: Optional[str] = None,
    script_file_path: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    拉起应用（挂起态）并附加，可选在恢复前注入脚本。

    Args:
      - package_name: 应用包名
      - device_id: 可选的设备 ID
      - initial_script: 可选注入的 Frida JS 代码字符串
      - script_file_path: 可选注入的 JS 文件绝对路径（优先于 initial_script）
      - output_file: 可选的本地电脑文件路径，用于保存 hook 输出（非安卓设备路径）

    Returns:
      - {status, pid, package, script_loaded, message}
    """
    # Ensure device is connected
    if not await ensure_device_connected(device_id):
        return {
            "status": "error",
            "message": "Failed to connect to device. Ensure frida-server is running."
        }
    
    # 解析脚本内容
    script_content, error_response = _resolve_script_content(initial_script, script_file_path)
    if error_response:
        return error_response
        
    if injector:
        return await injector.spawn(package_name, device_id, script_content, output_file)
    else:
        return {"status": "error", "message": "Injector not initialized. Device not connected?"}


if __name__ == "__main__":
    mcp.run()