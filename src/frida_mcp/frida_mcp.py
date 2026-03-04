"""
Frida MCP Server - Minimal Android Hook Service using FastMCP
"""

import os
from collections import deque
from typing import Optional, Dict, Any, Deque, List

import frida
from mcp.server.fastmcp import FastMCP
from pydantic import Field

import config.default_config as cfg_module
from config.default_config import load_config, GLOBAL_CONFIG_PATH
from config.guard_config import guard_os
from scripts.scripts_manager import ScriptManager
from util.frida_server_manager_android import AndroidServerManager
from util.frida_server_manager_windows import WindowsServerManager
from util.inject import BaseInjector
from util.inject_android import AndroidInjector
from util.inject_windows import WindowsInjector

__version__ = "0.2.0"

# Global MCP server settings
MCP_HOST: str = "0.0.0.0"
MCP_PORT: int = 8032

# Global state management - simplified
injector: Optional[BaseInjector] = None
# Global message buffer (store raw log lines)
messages_buffer: Deque[str] = deque(maxlen=5000)


# Append client-side Frida logs to the global buffer
def _frida_mcp_log(text: str) -> None:
    messages_buffer.append(f"[frida-mcp] {text}")


# Initialize FastMCP
mcp = FastMCP(name="frida-mcp", host=MCP_HOST, port=MCP_PORT)

CONFIG = load_config()


@mcp.tool()
def config_set(
        server_path: Optional[str] = None,
        server_name: Optional[str] = None,
        server_port: Optional[int] = None,
        device_id: Optional[str] = None,
        adb_path: Optional[str] = None,
        os: Optional[str] = Field(default=None, description="Target OS. Allowed: 'Android' or 'Windows'"),
        save_to: Optional[str] = Field(default=None,
                                       description="Optional: 'global' or 'project' to persist changes immediately.")
) -> Dict[str, Any]:
    """
    更新当前内存中的 Frida 配置。
    
    Args:
      - server_path: frida-server 路径
      - server_name: frida-server 文件名
      - server_port: frida-server 端口
      - device_id: 默认设备 ID
      - adb_path: adb 可执行文件路径
      - save_to: 可选，'global' 或 'project'，指定是否立即持久化到对应文件

    Returns:
        {status, message, active_config?, persisted_to?}
    """
    global CONFIG

    # Update memory
    if server_path is not None: CONFIG.server_path = server_path
    if server_name is not None: CONFIG.server_name = server_name
    if server_port is not None: CONFIG.server_port = server_port
    if device_id is not None: CONFIG.device_id = device_id
    if adb_path is not None: CONFIG.adb_path = adb_path
    if os is not None:
        val = (os or "").strip().lower()
        if val in ("android", "windows"):
            CONFIG.os = "Android" if val == "android" else "Windows"
        else:
            return {
                "status": "error",
                "message": "Invalid 'os'. Use 'Android' or 'Windows'. Example: config_set(os='Android')"
            }

    # Optional persistence
    persisted_to = None
    if save_to:
        target_path = GLOBAL_CONFIG_PATH if save_to.lower() == 'global' else cfg_module.PROJECT_CONFIG_PATH
        CONFIG.save(target_path)
        persisted_to = target_path

    return {
        "status": "success",
        "active_config": CONFIG.to_dict(),
        "persisted_to": persisted_to,
        "message": "Configuration updated in memory." + (f" Persisted to {persisted_to}." if persisted_to else "")
    }


@mcp.tool()
def config_save() -> Dict[str, Any]:
    """
    将当前内存中的活跃配置保存到当前项目配置文件 (PROJECT_CONFIG_PATH) 中。

    Returns:
        {status, message, path?, config?}
    """
    global CONFIG
    target_path = cfg_module.PROJECT_CONFIG_PATH

    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        CONFIG.save(target_path)
        return {
            "status": "success",
            "message": f"Active configuration saved to {target_path}",
            "path": target_path,
            "config": CONFIG.to_dict()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save configuration: {str(e)}"
        }


@mcp.tool()
def config_init(
        new_project_config_path: Optional[str] = Field(default=None,
                                                       description="Optional custom absolute path for the project config file.")
) -> Dict[str, Any]:
    """
    初始化项目配置。建议在每个项目开始时运行一次。
    
    功能:
    - 将当前活跃的配置写入项目配置文件。
    - 如果 MCP_HOST 为 0.0.0.0 (允许远程调用)，自动将配置文件覆盖写保存在全局配置目录的新文件 frida.mcp.config.json 中。
    - 支持通过 new_project_config_path 自定义配置文件路径，并将其设为当前活跃的 PROJECT_CONFIG_PATH。
    - 如果目标路径不存在，则自动复制当前配置到该位置。

    Returns:
        {status, message, project_config_path?, current_active_config?}
    """
    global CONFIG

    # 1. Determine target path
    if new_project_config_path:
        # Custom path provided by user
        target_path = os.path.abspath(new_project_config_path)
    elif MCP_HOST == "0.0.0.0":
        # Remote mode: Save in global directory (frida_mcp/config/frida.mcp.config.json)
        target_path = os.path.join(os.path.dirname(GLOBAL_CONFIG_PATH), "frida.mcp.config.json")
    else:
        # Default local project path
        target_path = os.path.abspath(cfg_module.PROJECT_CONFIG_PATH)

    try:
        # 2. Update the module's PROJECT_CONFIG_PATH variable to reflect current target
        cfg_module.PROJECT_CONFIG_PATH = target_path

        # 3. Handle file existence and saving
        if not os.path.exists(target_path):
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            _frida_mcp_log(f"Init new config file at: {target_path}")

        # Save current active CONFIG to the target path
        CONFIG.save(target_path)

        # 4. Reload CONFIG to apply the change immediately
        CONFIG = load_config()

        return {
            "status": "success",
            "message": "Project initialized successfully.",
            "project_config_path": target_path,
            "current_active_config": CONFIG.to_dict()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to initialize project: {str(e)}"
        }


def _get_device(device_id: Optional[str]) -> frida.core.Device:
    did = device_id or getattr(CONFIG, "device_id", None)
    if did:
        return frida.get_device(did)
    if getattr(CONFIG, "os", None) == "Windows":
        return frida.get_local_device()
    return frida.get_usb_device()


# Frida Server Start/Stop

@mcp.tool()
def start_android_frida_server() -> Dict[str, Any]:
    """
    启动 Android 设备上的 frida-server。

    - 来源: 使用 config.json 的 server_path/server_name/server_port
    Returns:
        {status, message}
    """
    err = guard_os("Android", CONFIG, "start_android_frida_server")
    if err:
        return err
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
def stop_android_frida_server() -> Dict[str, Any]:
    """
    停止 Android 设备上的 frida-server。

    Returns:
        {status, message}
    """
    err = guard_os("Android", CONFIG, "stop_android_frida_server")
    if err:
        return err
    dm = AndroidServerManager(CONFIG)
    if not dm.check_frida_status(silent=True):
        return {"status": "success", "message": "frida-server already stopped"}
    ok = dm.stop_frida_server()
    return {"status": "success" if ok else "error",
            "message": "frida-server stopped" if ok else "failed to stop frida-server"}


@mcp.tool()
def check_android_frida_status() -> Dict[str, Any]:
    """
    检测 Android frida-server 是否在运行。

    Returns:
        {status, message}
    """
    err = guard_os("Android", CONFIG, "check_android_frida_status")
    if err:
        return err
    dm = AndroidServerManager(CONFIG)
    running = bool(dm.check_frida_status(silent=True))
    return {"status": "success", "running": running}


@mcp.tool()
def start_windows_frida_server() -> Dict[str, Any]:
    """
    启动 Windows 本地 frida-server。

    - 来源: 使用 config.json 的 server_path/server_name
    Returns:
        {status, message}
    """
    err = guard_os("Windows", CONFIG, "start_windows_frida_server")
    if err:
        return err
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
def stop_windows_frida_server() -> Dict[str, Any]:
    """
    停止 Windows 本地 frida-server。

    Returns:
        {status, message}
    """
    err = guard_os("Windows", CONFIG, "stop_windows_frida_server")
    if err:
        return err
    dm = WindowsServerManager(CONFIG)
    if not dm.check_frida_status(silent=True):
        return {"status": "success", "message": "frida-server already stopped"}
    ok = dm.stop_frida_server()
    return {"status": "success" if ok else "error",
            "message": "frida-server stopped" if ok else "failed to stop frida-server"}


@mcp.tool()
def check_windows_frida_status() -> Dict[str, Any]:
    """
    检测 Windows 本地 frida-server 是否在运行。

    Returns:
        {status, running}
    """
    err = guard_os("Windows", CONFIG, "check_windows_frida_status")
    if err:
        return err
    dm = WindowsServerManager(CONFIG)
    running = bool(dm.check_frida_status(silent=True))
    return {"status": "success", "running": running}


@mcp.tool()
def check_frida_status() -> Dict[str, Any]:
    """
        检测 目标 os 的 frida-server 是否在运行。

    Returns:
        {status, running}
    """
    current = getattr(CONFIG, "os", None)
    if current == "Windows":
        return check_windows_frida_status()
    elif current == "Android":
        return check_android_frida_status()
    else:
        return {"status": "error", "running": False}


# Frida Tools Function

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
def get_device(
        device_id: Optional[str] = Field(default=None, description="Optional device id; uses config if omitted")
) -> Dict[str, Any]:
    """Get a device by its ID.

    Returns:
        {status, id, name, type}
    """
    try:
        _device = frida.get_device(device_id)
        return {
            "status": "success",
            "id": _device.id,
            "name": _device.name,
            "type": _device.type,
        }
    except frida.InvalidArgumentError:
        return {
            "status": "error",
            "id": "",
            "name": "",
            "type": "",
        }


@mcp.tool()
def get_usb_device() -> Dict[str, Any]:
    """Get the USB device connected to the system.

    Returns:
        {status, id, name, type}
    """
    try:
        _device = frida.get_usb_device()
        return {
            "status": "success",
            "id": _device.id,
            "name": _device.name,
            "type": _device.type,
        }
    except frida.InvalidArgumentError:
        return {
            "status": "error",
            "id": "",
            "name": "",
            "type": "",
        }


@mcp.tool()
def get_local_device() -> Dict[str, Any]:
    """Get the local device.

    Returns:
        {status, id, name, type}
    """
    try:
        _device = frida.get_local_device()
        return {
            "status": "success",
            "id": _device.id,
            "name": _device.name,
            "type": _device.type,
        }
    except frida.InvalidArgumentError:
        return {
            "status": "error",
            "id": "",
            "name": "",
            "type": "",
        }


@mcp.tool()
def list_applications(
        device_id: Optional[str] = Field(default=None, description="Optional device id; uses config if omitted")
) -> Dict[str, Any]:
    """
    列出设备上的已安装应用（含运行与未运行）。

    - 返回: {status, count, applications:[{identifier,name,pid?}]}
    """
    try:
        _device = _get_device(device_id)
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
def get_frontmost_application(
        device_id: Optional[str] = Field(default=None, description="Optional device id; uses config if omitted")
) -> Dict[str, Any]:
    """
    获取当前前台应用信息。
    Returns:
        {status, application?{identifier,name,pid}, message?}
    """

    try:
        frontmost = _get_device(device_id).get_frontmost_application()
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


# Process Management

@mcp.tool()
def enumerate_processes(
        device_id: Optional[str] = Field(default=None, description="Optional device id; uses config if omitted")
) -> List[Dict[str, Any]]:
    """List all processes running on the system.

    Returns:
        A list of process information dictionaries containing:
        - pid: Process ID
        - name: Process name
    """
    _device = _get_device(device_id)

    processes = _device.enumerate_processes()
    return [{"pid": _process.pid, "name": _process.name} for _process in processes]


@mcp.tool()
def get_process_by_name(
        name: str = Field(description="Process name (substring, case-insensitive)"),
        device_id: Optional[str] = Field(default=None, description="Optional device id; uses config if omitted")
) -> Dict[str, Any]:
    """
    Find a process by name.
    Returns:
        {found, error?, pid?, name?}
    """
    _device = _get_device(device_id)

    for proc in _device.enumerate_processes():
        if name.lower() in proc.name.lower():
            return {"pid": proc.pid, "name": proc.name, "found": True}
    return {"found": False, "error": f"Process '{name}' not found"}


@mcp.tool()
def resume_process(
        pid: int = Field(description="Process id to resume"),
        device_id: Optional[str] = Field(default=None, description="Optional device id; uses config if omitted")
) -> Dict[str, Any]:
    """
    恢复被挂起的进程，暂未测试成功
    Returns:
        {status, pid, message}
    """
    try:
        _device = _get_device(device_id)
        _device.resume(pid)
        return {"status": "success", "pid": pid, "message": f"Process {pid} resumed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def kill_process(
        pid: int = Field(description="Process id to kill"),
        device_id: Optional[str] = Field(default=None, description="Optional device id; uses config if omitted")
) -> Dict[str, Any]:
    """
    终止正在运行的进程。
    Returns:
        {status, pid, message}
    """
    try:
        _device = _get_device(device_id)
        _device.kill(pid)
        return {"status": "success", "pid": pid, "message": f"Process {pid} killed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Frida Resource

@mcp.resource("frida://version")
def get_version() -> Dict[str, Any]:
    """Get the Frida version."""
    return {
        "frida": frida.__version__,
        "frida_mcp": __version__,
    }


@mcp.resource("frida://config")
def config_get() -> Dict[str, Any]:
    """
    获取当前活跃的配置、全局和项目配置文件的路径及其状态。
    """
    return {
        "status": "success",
        "active_config": CONFIG.to_dict(),
        "paths": {
            "global": {
                "path": GLOBAL_CONFIG_PATH,
                "exists": os.path.exists(GLOBAL_CONFIG_PATH)
            },
            "project": {
                "path": cfg_module.PROJECT_CONFIG_PATH,
                "exists": os.path.exists(cfg_module.PROJECT_CONFIG_PATH)
            }
        }
    }


# Console Log

@mcp.tool()
def get_messages(max_messages: int = 100) -> Dict[str, Any]:
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

def injector_init() -> Dict[str, Any]:
    global injector
    if injector is None:
        # 手动构建 injector 结构体
        if CONFIG.device_id is None:
            return {
                "status": "error",
                "message": "Device Id not Set. Please call config_set first."
            }

        if getattr(CONFIG, "os", None) == "Android":
            injector = AndroidInjector(device=_get_device(CONFIG.device_id), messages_buffer=messages_buffer)
        elif getattr(CONFIG, "os", None) == "Windows":
            injector = WindowsInjector(device=_get_device(CONFIG.device_id), messages_buffer=messages_buffer)
        else:
            return {
                "status": "error",
                "message": f"OS {getattr(CONFIG, "os", None)} is not supported."
            }
        return {
            "status": "success",
            "message": "injector init success"
        }
    else:
        return {
            "status": "success",
            "message": "injector init before."
        }


@mcp.tool()
async def attach(target: str) -> Dict[str, Any]:
    """
    附加到运行中的进程，建立session连接。

    Args:
      - target: PID 字符串或包名

    Returns:
      - {status, pid, target, name, message}
    """
    if not target or not target.strip():
        return {
            "status": "error",
            "message": "Target cannot be empty"
        }

    injector_init()

    # 使用新的injector架构，device已在初始化时传入
    attach_result = await injector.attach(target.strip())
    if attach_result['error']:
        return {
            "status": "error",
            "message": attach_result['error']
        }

    return {
        "status": "success",
        "pid": attach_result['data']['pid'],
        "target": target.strip(),
        "name": attach_result['data'].get('name', target.strip()),
        "message": f"Successfully attached to {target.strip()}"
    }


@mcp.tool()
async def spawn(package_name: str) -> Dict[str, Any]:
    """
    拉起应用（挂起态）并附加，建立session连接。

    Args:
      - package_name: 应用包名 / 应用程序地址

    Returns:
      - {status, pid, package, message}
    """
    if not package_name or not package_name.strip():
        return {
            "status": "error",
            "message": "Package name cannot be empty"
        }

    injector_init()

    spawn_result = await injector.spawn(package_name.strip())
    if spawn_result['error']:
        return {
            "status": "error",
            "message": spawn_result['error']
        }

    return {
        "status": "success",
        "pid": spawn_result['data']['pid'],
        "package": package_name.strip(),
        "message": f"Successfully spawned {package_name.strip()}"
    }


@mcp.tool()
async def inject_user_script_run(
        script_content: str,
        script_name: str = "user_script"
) -> Dict[str, Any]:
    """
    将JavaScript脚本注入到当前活跃的session中，仅执行注入的部分。
    返回值中的 message 为调用 get_messages 函数得到的最后20条日志。

    Args:
      - script_content: 要注入的Frida JS代码字符串
      - script_name: 脚本名称标识符，默认为"user_script"

    Returns:
      - {status, ?script_name, ?script_content_length, message}
    """
    if not injector:
        return {
            "status": "error",
            "message": "Injector not initialized. Please call attach/spawn first."
        }

    if not injector.is_connected():
        return {
            "status": "error",
            "message": "No active session. Please call attach or spawn."
        }
    try:
        script_manager = ScriptManager()
        script_manager.add_custom_section(script_name, script_content)

        inject_result = injector.inject_script(script_manager)

        if inject_result['error']:
            return {
                "status": "error",
                "message": f"Failed to inject script: {inject_result['error']}"
            }

        return {
            "status": "success",
            "script_name": script_name,
            "script_content_length": len(script_content),
            "message": get_messages(20)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error injecting script: {str(e)}"
        }


@mcp.tool()
async def inject_user_script_run_all(
        script_content: Optional[str] = None,
        script_name: str = "custom_script"
) -> Dict[str, Any]:
    """
    将JavaScript脚本注入到当前活跃的session中，执行 ScriptManager 中所有内容。
    返回值中的 message 为调用 get_messages 函数得到的最后20条日志。

    Args:
      - script_content: 要注入的Frida JS代码字符串，为空时注入 ScriptManager 中已有的内容
      - script_name: 脚本名称标识符，默认为"custom_script"

    Returns:
      - {status, ?script_name, ?script_content_length, message}
    """
    if not injector:
        return {
            "status": "error",
            "message": "Injector not initialized. Please call attach/spawn first."
        }

    if not injector.is_connected():
        return {
            "status": "error",
            "message": "No active session. Please call attach or spawn."
        }

    try:
        if script_content:
            injector.script_manager.add_custom_section(script_name, script_content)

        inject_result = injector.inject_script()

        if inject_result['error']:
            return {
                "status": "error",
                "message": f"Failed to inject script: {inject_result['error']}"
            }

        return {
            "status": "success",
            "script_name": script_name,
            "script_content_length": len(script_content),
            "message": get_messages(20)
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error injecting script: {str(e)}"
        }


@mcp.tool()
async def detach() -> Dict[str, Any]:
    """
    断开当前活跃的session连接。

    Returns:
      - {status, message}
    """
    if not injector:
        return {
            "status": "error",
            "message": "Injector not initialized. Please call attach/spawn first."
        }

    detach_result = injector.detach()
    if detach_result['error']:
        return {
            "status": "error",
            "message": detach_result['error']
        }

    return {
        "status": "success",
        "message": "Successfully detached from target"
    }


@mcp.tool()
async def get_session_info() -> Dict[str, Any]:
    """
    获取当前活跃的session信息。

    Returns:
      - {status, target, pid, message}
    """
    if not injector:
        return {
            "status": "error",
            "message": "Injector not initialized. Please call attach/spawn first."
        }

    session_info = injector.get_session_info()
    if session_info['error']:
        return {
            "status": "error",
            "message": session_info['error']
        }

    return {
        "status": "success",
        "target": session_info['data']['target'],
        "pid": session_info['data']['pid'],
        "message": f"Active session: {session_info['data']['target']} (PID: {session_info['data']['pid']})"
    }


if __name__ == "__main__":
    # Ensure the server doesn't shut down immediately. 
    # For transport="streamable-http", FastMCP should use the host/port from constructor.
    print(f"[*] Frida MCP Server Starting...")
    print(f"[*] Transport: streamable-http")

    try:
        # Pass host and port directly to run() just in case the constructor ones aren't being picked up for streamable-http
        mcp.run(transport="streamable-http")
        # mcp.run()
    except KeyboardInterrupt:
        print("\n[*] Server stopped by user.")
    except Exception as e:
        print(f"[*] Server error: {e}")
