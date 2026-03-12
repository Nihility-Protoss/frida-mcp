"""
Frida MCP Server - Minimal Android Hook Service using FastMCP
"""

import os
from typing import Optional, Dict, Any, Union, List, Annotated

import frida
from mcp.server.fastmcp import FastMCP

import config.default_config as cfg_module
from config.default_config import load_config, GLOBAL_CONFIG_PATH
from config.guard_config import guard_os
from scripts.scripts_manager import ScriptManager
from util.frida_server_manager_android import AndroidServerManager
from util.frida_server_manager_windows import WindowsServerManager
from util.inject import BaseInjector
from util.inject_android import AndroidInjector
from util.inject_windows import WindowsInjector
from util.message_class import MessageLog

__version__ = "0.4.0"

# Global MCP server settings
MCP_HOST: str = "0.0.0.0"
MCP_PORT: int = 8032

# Global state management - simplified
injector: Optional[Union[BaseInjector, AndroidInjector, WindowsInjector]] = None
# Global message buffer (store raw log lines)
messages_buffer: MessageLog = MessageLog()


# Append client-side Frida logs to the global buffer
def _frida_mcp_log(text: str) -> None:
    messages_buffer.append(f"[frida-mcp] {text}")


# Initialize FastMCP
mcp = FastMCP(name="frida-mcp", host=MCP_HOST, port=MCP_PORT)

CONFIG = load_config()


@mcp.tool()
def config_set(
    server_path: Annotated[Optional[str], "Path to frida-server binary"] = None,
    server_name: Annotated[Optional[str], "Name of frida-server executable"] = None,
    server_port: Annotated[Optional[int], "Port number for frida-server communication"] = None,
    device_id: Annotated[Optional[str], "Default device identifier for connections"] = None,
    adb_path: Annotated[Optional[str], "Path to ADB executable (Android only)"] = None,
    os: Annotated[Optional[str], "Target OS ('Android' or 'Windows'). Must be set before using platform-specific features"] = None,
    save_to: Annotated[Optional[str], "Persistence option - 'global' or 'project' to persist changes immediately"] = None,
) -> Dict[str, Any]:
    """
    Update the current in-memory Frida configuration.

    Args:
        server_path: Path to frida-server binary
        server_name: Name of frida-server executable
        server_port: Port number for frida-server communication
        device_id: Default device identifier for connections
        adb_path: Path to ADB executable (Android only)
        os: Target operating system ('Android' or 'Windows')
        save_to: Persistence option - 'global' or 'project'

    Returns:
        Dict with status, message, active_config, and optionally persisted_to
    """
    global CONFIG
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


def _check_platform_environment(platform: str) -> Dict[str, Any]:
    """
    Verify that the specified platform environment is ready for operations.
    
    This internal function checks if:
    1. The configured OS matches the target platform
    2. An injector has been initialized (via attach/spawn)
    3. An active session exists
    
    Args:
        platform: Target platform name ('Android' or 'Windows'). Empty string allows any platform.
    
    Returns:
        Dict with structure:
        - error: Error message string if check fails, None if successful
        - data: Always None (reserved for future use)
    """
    if not platform:
        return {'error': None, 'data': None}

    current_os = getattr(CONFIG, "os", None)
    if current_os != platform:
        return {'error': f"This function only supports {platform}", 'data': None}

    if not injector:
        return {'error': "Injector not initialized. Please call attach/spawn first.", 'data': None}

    if not injector.is_connected():
        return {'error': "No active session. Please call attach or spawn.", 'data': None}

    return {'error': None, 'data': None}


def _load_platform_script(
        platform: str,
        load_method_name: str,
        load_func,
        run_script_bool: bool = False,
        **kwargs
) -> Dict[str, Any]:
    """
    Generic platform script loading and injection helper.
    
    This internal utility function handles the common workflow for loading
    platform-specific scripts (Android/Windows) and optionally executing them.
    
    Args:
        platform: Target platform ('Android' or 'Windows'). Use empty string for platform-agnostic scripts.
        load_method_name: Name of the loading method for error reporting
        load_func: Callable that loads the script content into ScriptManager
        run_script_bool: If True, immediately injects and executes the script after loading
        **kwargs: Additional arguments passed to the load function
    
    Returns:
        Dict containing:
        - status: 'success' or 'error'
        - message: Detailed result description
    
    Note:
        This function requires an active session established via attach() or spawn()
    """
    # 检查平台环境
    check_result = _check_platform_environment(platform)
    if check_result['error']:
        return {
            "status": "error",
            "message": check_result['error']
        }

    try:
        # 调用加载函数
        if kwargs:
            load_func(**kwargs)
        else:
            load_func()

        if run_script_bool:
            inject_result = injector.inject_script()

            if inject_result['error']:
                return {
                    "status": "error",
                    "message": f"Failed to inject script: {inject_result['error']}"
                }
            return {
                "status": "success",
                "message": f"call {load_method_name},inject_script success",
            }
        else:
            return {
                "status": "success",
                "message": f"call {load_method_name} success",
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error in {load_method_name}: {str(e)}"
        }


@mcp.tool()
def config_save() -> Dict[str, Any]:
    """
    Persist the current in-memory configuration to the project config file.

    Returns:
        Dict with status, message, path, and config
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
    new_project_config_path: Annotated[Optional[str], "Custom absolute path for the project configuration file"] = None,
) -> Dict[str, Any]:
    """
    Initialize project configuration. Run this at the start of each project.

    Args:
        new_project_config_path: Custom absolute path for the project configuration file

    Returns:
        Dict with status, message, project_config_path, and current_active_config
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
    """
    Get a Frida device instance based on configuration.
    
    Resolution order:
    1. If device_id is provided or configured, use that specific device
    2. If OS is Windows, use the local device
    3. Otherwise, use the USB device (default for Android)
    
    Args:
        device_id: Specific device identifier. If None, uses configured default.
    
    Returns:
        frida.core.Device: Connected device instance
    
    Raises:
        frida.InvalidArgumentError: If the specified device is not found
    """
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
    Start the frida-server on an Android device.

    Prerequisites:
        - config.os must be set to 'Android'

    Returns:
        Dict with status and message

    Note:
        If frida-server is already running, returns success immediately
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
    Stop the frida-server on an Android device.

    Prerequisites:
        - config.os must be set to 'Android'

    Returns:
        Dict with status and message

    Note:
        If frida-server is already stopped, returns success immediately
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
    Check if frida-server is running on the Android device.

    Prerequisites:
        - config.os must be set to 'Android'

    Returns:
        Dict with status and running (boolean)
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
    Start the local frida-server on Windows.

    Prerequisites:
        - config.os must be set to 'Windows'

    Returns:
        Dict with status and message

    Note:
        If frida-server is already running, returns success immediately
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
    Stop the local frida-server on Windows.

    Prerequisites:
        - config.os must be set to 'Windows'

    Returns:
        Dict with status and message

    Note:
        If frida-server is already stopped, returns success immediately
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
    Check if frida-server is running on Windows.

    Prerequisites:
        - config.os must be set to 'Windows'

    Returns:
        Dict with status and running (boolean)
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
    Check frida-server status for the currently configured OS.

    Returns:
        Dict with status and running (boolean)
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
    """
    List all devices available to Frida.

    Returns:
        List of device dicts with id, name, and type
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
    device_id: Annotated[Optional[str], "Device identifier, uses config if omitted"] = None,
) -> Dict[str, Any]:
    """
    Get information about a specific device by its ID.

    Args:
        device_id: Device identifier

    Returns:
        Dict with status, id, name, and type
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
    """
    Get the USB-connected device.

    Returns:
        Dict with status, id, name, and type
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
    """
    Get the local device.

    Returns:
        Dict with status, id, name, and type
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
    device_id: Annotated[Optional[str], "Target device, uses config if omitted"] = None,
) -> Dict[str, Any]:
    """
    List all installed applications on the device.

    Args:
        device_id: Target device

    Returns:
        Dict with status, count, and applications list
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
    device_id: Annotated[Optional[str], "Target device, uses config if omitted"] = None,
) -> Dict[str, Any]:
    """
    Get information about the currently foreground application.

    Args:
        device_id: Target device

    Returns:
        Dict with status, application, and optionally message
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
    device_id: Annotated[Optional[str], "Target device, uses config if omitted"] = None,
) -> List[Dict[str, Any]]:
    """
    List all processes currently running on the device.

    Args:
        device_id: Target device

    Returns:
        List of process dicts with pid and name
    """
    _device = _get_device(device_id)

    processes = _device.enumerate_processes()
    return [{"pid": _process.pid, "name": _process.name} for _process in processes]


@mcp.tool()
def get_process_by_name(
    name: Annotated[str, "Process name (substring, case-insensitive)"],
    device_id: Annotated[Optional[str], "Target device, uses config if omitted"] = None,
) -> Dict[str, Any]:
    """
    Find a running process by name (substring match, case-insensitive).

    Args:
        name: Process name or substring to search for
        device_id: Target device

    Returns:
        Dict with found (boolean), pid, name, and optionally error
    """
    _device = _get_device(device_id)

    for proc in _device.enumerate_processes():
        if name.lower() in proc.name.lower():
            return {"pid": proc.pid, "name": proc.name, "found": True}
    return {"found": False, "error": f"Process '{name}' not found"}


@mcp.tool()
def resume_process(
    pid: Annotated[int, "Process ID to resume"],
    device_id: Annotated[Optional[str], "Target device, uses config if omitted"] = None,
) -> Dict[str, Any]:
    """
    Resume a suspended process.

    Args:
        pid: Process identifier to resume
        device_id: Target device

    Returns:
        Dict with status, pid, and message
    """
    try:
        _device = _get_device(device_id)
        _device.resume(pid)
        return {"status": "success", "pid": pid, "message": f"Process {pid} resumed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def kill_process(
    pid: Annotated[int, "Process ID to terminate"],
    device_id: Annotated[Optional[str], "Target device, uses config if omitted"] = None,
) -> Dict[str, Any]:
    """
    Terminate a running process.

    Args:
        pid: Process identifier to terminate
        device_id: Target device

    Returns:
        Dict with status, pid, and message

    Warning:
        This operation cannot be undone. Ensure you have the correct PID.
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
    """
    Get version information for Frida and frida-mcp.

    Returns:
        Dict with frida and frida_mcp version strings
    """
    return {
        "frida": frida.__version__,
        "frida_mcp": __version__,
    }


@mcp.resource("frida://config")
def config_get() -> Dict[str, Any]:
    """
    Get current configuration and configuration file status.

    Returns:
        Dict with status, active_config, and paths
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
def get_messages(
    max_messages: Annotated[int, "Maximum number of messages to retrieve"] = 100,
) -> Dict[str, Any]:
    """
    Retrieve messages from the global log buffer.

    Args:
        max_messages: Maximum number of messages to retrieve

    Returns:
        Dict with status, messages, and remaining

    Note:
        For incremental log retrieval, use get_new_messages instead
    """
    if max_messages is None or max_messages < 0:
        max_messages = 0
    snapshot = messages_buffer.get_messages(max_messages)
    return {
        "status": "success",
        "remaining": len(snapshot),
        "messages": snapshot,
    }


@mcp.tool()
def get_new_messages() -> Dict[str, Any]:
    """
    Retrieve new messages since the last call.

    Returns:
        Dict with status, messages, and remaining
    """
    snapshot = messages_buffer.get_new_messages()
    return {
        "status": "success",
        "remaining": len(snapshot),
        "messages": snapshot,
    }


# MCP Tool Handlers using FastMCP decorators

def injector_init() -> Dict[str, Any]:
    """
    Initialize the platform-specific injector.
    
    This internal function creates the appropriate injector instance
    (AndroidInjector or WindowsInjector) based on config.os.
    Must be called before attach() or spawn().

    Returns:
        Dict containing:
        - status: 'success' or 'error'
        - message: Description of the operation result

    Raises:
        Returns error if device_id is not set or OS is unsupported.
    """
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
async def attach(
    target: Annotated[str, "Process identifier - PID (as string) or process name"],
) -> Dict[str, Any]:
    """
    Attach to a running process.

    Args:
        target: Process identifier - PID or process name

    Returns:
        Dict with status, pid, target, name, and message

    Prerequisites:
        - config.os must be set
        - config.device_id must be set
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
async def spawn(
    package_name: Annotated[str, "Application package name (Android) or executable path (Windows)"],
    args: Annotated[str, "Optional command-line arguments"] = "",
) -> Dict[str, Any]:
    """
    Launch a new process in suspended state and attach to it.

    Args:
        package_name: Application package name or executable path
        args: Optional command-line arguments

    Returns:
        Dict with status, pid, package, and message

    Prerequisites:
        - config.os must be set
        - config.device_id must be set
    """
    if not package_name or not package_name.strip():
        return {
            "status": "error",
            "message": "Package name cannot be empty"
        }

    injector_init()

    spawn_result = await injector.spawn(package_name.strip(), args.strip() if args else "")
    if spawn_result['error']:
        return {
            "status": "error",
            "message": spawn_result['error']
        }

    # 返回的 package 字段已包含完整命令（程序 + 参数）
    full_package = spawn_result['data'].get('program') or package_name.strip()

    return {
        "status": "success",
        "pid": spawn_result['data']['pid'],
        "package": full_package,
        "message": spawn_result['data']['message']
    }


@mcp.tool()
async def detach() -> Dict[str, Any]:
    """
    Detach from the current session.

    Returns:
        Dict with status and message

    Note:
        This does not terminate the target process
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
    Get information about the current active session.

    Returns:
        Dict with status, target, pid, and message

    Prerequisites:
        - Must have an active session via attach() or spawn()
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


# MCP Tool Script

@mcp.tool()
async def inject_user_script_run(
    script_content: Annotated[str, "JavaScript code to inject and execute"],
    script_name: Annotated[str, "Identifier for this script"] = "user_script",
) -> Dict[str, Any]:
    """
    Inject and execute a user-provided JavaScript script.

    Args:
        script_content: JavaScript code to inject and execute
        script_name: Identifier for this script

    Returns:
        Dict with status, script_name, and script_content_length

    Prerequisites:
        - Must have an active session via attach() or spawn()
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
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error injecting script: {str(e)}"
        }


@mcp.tool()
async def inject_user_script_run_all(
    script_content: Annotated[Optional[str], "Optional JavaScript code to add before execution"] = None,
    script_name: Annotated[str, "Identifier for the script section"] = "custom_script",
) -> Dict[str, Any]:
    """
    Inject and execute all scripts from the ScriptManager.

    Args:
        script_content: Optional JavaScript code to add before execution
        script_name: Identifier for the script section

    Returns:
        Dict with status, script_name, and script_content_length

    Prerequisites:
        - Must have an active session via attach() or spawn()
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
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error injecting script: {str(e)}"
        }


@mcp.tool()
def get_script_list() -> Dict[str, Any]:
    """
    List all available built-in scripts for the current injector.

    Returns:
        Dict with status and message

    Prerequisites:
        - Must have an active session via attach() or spawn()
    """
    if not injector:
        return {
            "status": "error",
            "message": "Injector not initialized. Please call attach/spawn first."
        }

    available_scripts = injector.script_manager.get_available_scripts()

    return {
        "status": "success" if available_scripts["error"] is None else "error",
        "message": available_scripts["data"] if available_scripts["error"] is None else available_scripts["error"]
    }


@mcp.tool()
def get_script_now() -> Dict[str, Any]:
    """
    Get the currently built script content from the ScriptManager.

    Returns:
        Dict with status and message

    Prerequisites:
        - Must have an active session via attach() or spawn()
    """
    if not injector:
        return {
            "status": "error",
            "message": "Injector not initialized. Please call attach/spawn first."
        }
    return {
        "status": "success",
        "message": str(injector.script_manager)
    }


@mcp.tool()
def reset_script_now() -> Dict[str, Any]:
    """
    Reset the ScriptManager to its initial state.

    Returns:
        Dict with status and message

    Prerequisites:
        - Must have an active session via attach() or spawn()

    Warning:
        This clears all loaded scripts
    """
    if not injector:
        return {
            "status": "error",
            "message": "Injector not initialized. Please call attach/spawn first."
        }
    reset_result = injector.script_manager.reset_script()

    return {
        "status": "success" if reset_result["error"] is None else "error",
        "message": reset_result["data"] if reset_result["error"] is None else reset_result["error"]
    }


# MCP Tool Util Script

@mcp.tool()
def util_load_module_enumerateExports(
    module_name: Annotated[str, "Module file name (e.g., 'libssl.so' or 'kernel32.dll')"],
    run_script_bool: Annotated[bool, "If True, immediately inject and execute"] = False,
) -> Dict[str, Any]:
    """
    Enumerate all exported functions from a module.

    Args:
        module_name: Module file name
        run_script_bool: If True, immediately inject and execute

    Returns:
        Dict with status and message

    Prerequisites:
        - Must have an active session via attach() or spawn()
    """
    return _load_platform_script(
        "",
        "load_module_enumerateExports",
        injector.script_manager.load_module_enumerateExports,
        run_script_bool,
        module_name=module_name
    )


# MCP Tool Android Script

@mcp.tool()
def android_load_script_anti_DexHelper_hook_clone(
    run_script_bool: Annotated[bool, "If True, immediately inject and execute"] = False,
) -> Dict[str, Any]:
    """
    Load anti-DexHelper detection bypass script (hook clone method).

    Args:
        run_script_bool: If True, immediately inject and execute

    Returns:
        Dict with status and message

    Prerequisites:
        - config.os must be 'Android'
        - Must have an active session via attach() or spawn()
    """
    return _load_platform_script(
        "Android",
        "load_anti_DexHelper_hook_clone",
        injector.script_manager.load_anti_DexHelper_hook_clone,
        run_script_bool
    )


@mcp.tool()
def android_load_script_anti_DexHelper_hook_pthread(
    run_script_bool: Annotated[bool, "If True, immediately inject and execute"] = False,
) -> Dict[str, Any]:
    """
    Load anti-DexHelper detection bypass script (hook pthread method).

    Args:
        run_script_bool: If True, immediately inject and execute

    Returns:
        Dict with status and message

    Prerequisites:
        - config.os must be 'Android'
        - Must have an active session via attach() or spawn()
    """
    return _load_platform_script(
        "Android",
        "load_anti_DexHelper_hook_pthread",
        injector.script_manager.load_anti_DexHelper_hook_pthread,
        run_script_bool
    )


@mcp.tool()
def android_load_script_anti_DexHelper(
    hook_addr_list: Annotated[List[int], "List of memory addresses to NOP (e.g., [0x561d0, 0x52cc0])"],
    run_script_bool: Annotated[bool, "If True, immediately inject and execute"] = False,
) -> Dict[str, Any]:
    """
    Load anti-DexHelper detection bypass script (NOP method).

    Args:
        hook_addr_list: List of memory addresses to NOP
        run_script_bool: If True, immediately inject and execute

    Returns:
        Dict with status and message

    Prerequisites:
        - config.os must be 'Android'
        - Must have an active session via attach() or spawn()
    """
    return _load_platform_script(
        "Android",
        "load_anti_DexHelper",
        injector.script_manager.load_anti_DexHelper,
        run_script_bool,
        hook_addr_list=hook_addr_list
    )


@mcp.tool()
def android_load_hook_net_libssl(
    run_script_bool: Annotated[bool, "If True, immediately inject and execute"] = False,
) -> Dict[str, Any]:
    """
    Load SSL/TLS network traffic interception script.

    Args:
        run_script_bool: If True, immediately inject and execute

    Returns:
        Dict with status and message

    Prerequisites:
        - config.os must be 'Android'
        - Must have an active session via attach() or spawn()
    """
    return _load_platform_script(
        "Android",
        "load_hook_net_libssl",
        injector.script_manager.load_hook_net_libssl,
        run_script_bool
    )


@mcp.tool()
def android_load_hook_clone(
    anti_so_name_tag: Annotated[str, "Name/tag of the SO file to counter (default: 'DexHelper')"] = "DexHelper",
    run_script_bool: Annotated[bool, "If True, immediately inject and execute"] = False,
) -> Dict[str, Any]:
    """
    Load clone() syscall hook for anti-detection.

    Args:
        anti_so_name_tag: Name/tag of the SO file to counter
        run_script_bool: If True, immediately inject and execute

    Returns:
        Dict with status and message

    Prerequisites:
        - config.os must be 'Android'
        - Must have an active session via attach() or spawn()
    """
    return _load_platform_script(
        "Android",
        "load_hook_clone",
        injector.script_manager.load_hook_clone,
        run_script_bool,
        anti_so_name_tag=anti_so_name_tag
    )


@mcp.tool()
def android_load_hook_activity(
    package_name: Annotated[str, "Target application package name"],
    activity_name: Annotated[str, "Full Activity class name to hook (e.g., 'com.example.app.MainActivity')"],
    run_script_bool: Annotated[bool, "If True, immediately inject and execute"] = False,
) -> Dict[str, Any]:
    """
    Load Android Activity lifecycle hook script.

    Args:
        package_name: Target application package name
        activity_name: Full Activity class name to hook
        run_script_bool: If True, immediately inject and execute

    Returns:
        Dict with status and message

    Prerequisites:
        - config.os must be 'Android'
        - Must have an active session via attach() or spawn()
    """
    return _load_platform_script(
        "Android",
        "load_hook_activity",
        injector.script_manager.load_hook_activity,
        run_script_bool,
        package_name=package_name,
        activity_name=activity_name
    )


# MCP Tool Windows Script

@mcp.tool()
def windows_load_monitor_api(
    module_name: Annotated[str, "Name of the DLL module (e.g., 'kernel32.dll')"],
    api_name: Annotated[str, "Name of the API function to monitor (e.g., 'CreateFileW')"],
    run_script_bool: Annotated[bool, "If True, immediately inject and execute"] = False,
) -> Dict[str, Any]:
    """
    Load Windows API monitoring script.

    Args:
        module_name: Name of the DLL module containing the API
        api_name: Name of the API function to monitor
        run_script_bool: If True, immediately inject and execute

    Returns:
        Dict with status and message

    Prerequisites:
        - config.os must be 'Windows'
        - Must have an active session via attach() or spawn()
    """
    return _load_platform_script(
        "Windows",
        "load_monitor_api",
        injector.script_manager.load_monitor_api,
        run_script_bool,
        module_name=module_name,
        api_name=api_name
    )


@mcp.tool()
def windows_load_monitor_registry(
        api_name: str,
        registry_path: str = "",
        run_script_bool: bool = False
) -> Dict[str, Any]:
    """
    Load Windows registry monitoring script.
    
    Hooks registry operations to monitor or intercept registry access.
    Can filter by specific registry path or monitor all operations.

    Args:
        api_name: Registry API to monitor. Valid options:
            - RegOpenKeyExW, RegOpenKeyExA
            - RegCreateKeyExW, RegCreateKeyExA
            - RegSetValueExW, RegSetValueExA
            - RegQueryValueExW, RegQueryValueExA
            - RegDeleteValueW, RegDeleteValueA
            - RegDeleteKeyW, RegDeleteKeyA
            - RegEnumKeyExW, RegEnumKeyExA
            - RegEnumValueW, RegEnumValueA
        registry_path: Registry path to monitor (e.g., "SOFTWARE\\MyApp").
            Empty string monitors all paths.
        run_script_bool: If True, immediately inject and execute.
            If False, only loads into ScriptManager for later execution.

    Returns:
        Dict containing:
            - status: 'success' or 'error'
            - message: Description of the operation result

    Prerequisites:
        - config.os must be 'Windows'
        - Must have an active session via attach() or spawn()
    """
    # Valid registry API names
    VALID_REGISTRY_APIS = {
        "RegOpenKeyExW", "RegOpenKeyExA",
        "RegCreateKeyExW", "RegCreateKeyExA",
        "RegSetValueExW", "RegSetValueExA",
        "RegQueryValueExW", "RegQueryValueExA",
        "RegDeleteValueW", "RegDeleteValueA",
        "RegDeleteKeyW", "RegDeleteKeyA",
        "RegEnumKeyExW", "RegEnumKeyExA",
        "RegEnumValueW", "RegEnumValueA"
    }

    # 验证api_name参数
    if api_name not in VALID_REGISTRY_APIS:
        return {
            "status": "error",
            "message": f"UseLess Api Name: {api_name}, must in list[{', '.join(sorted(VALID_REGISTRY_APIS))}]"
        }

    return _load_platform_script(
        "Windows",
        "load_monitor_registry",
        injector.script_manager.load_monitor_registry,
        run_script_bool,
        api_name=api_name,
        registry_path=registry_path
    )


@mcp.tool()
def windows_load_monitor_file(
        api_name: str,
        file_path: str = "",
        run_script_bool: bool = False
) -> Dict[str, Any]:
    """
    Load Windows file operation monitoring script.
    
    Hooks file system APIs to monitor file operations.
    Can filter by specific file path or monitor all operations.

    Args:
        api_name: File API to monitor. Valid options:
            - CreateFileW, CreateFileA
            - ReadFile, WriteFile
            - DeleteFileW, DeleteFileA
            - MoveFileW, MoveFileA, MoveFileExW, MoveFileExA
            - CopyFileW, CopyFileA, CopyFileExW, CopyFileExA
            - FindFirstFileW, FindFirstFileA
            - CloseHandle
        file_path: Full file path to monitor (e.g., "C:\\temp\\file.txt").
            Empty string monitors all paths.
        run_script_bool: If True, immediately inject and execute.
            If False, only loads into ScriptManager for later execution.

    Returns:
        Dict containing:
        - status: 'success' or 'error'
        - message: Description of the operation result

    Prerequisites:
        - config.os must be 'Windows'
        - Must have an active session via attach() or spawn()
    """
    # Valid file API names
    VALID_FILE_APIS = {
        "CreateFileW", "CreateFileA",
        "ReadFile", "WriteFile",
        "DeleteFileW", "DeleteFileA",
        "MoveFileW", "MoveFileA",
        "MoveFileExW", "MoveFileExA",
        "CopyFileW", "CopyFileA",
        "CopyFileExW", "CopyFileExA",
        "FindFirstFileW", "FindFirstFileA",
        "CloseHandle"
    }
    
    # 验证api_name参数
    if api_name not in VALID_FILE_APIS:
        return {
            "status": "error",
            "message": f"UseLess Api Name: {api_name}, must in list[{', '.join(sorted(VALID_FILE_APIS))}]"
        }
    
    return _load_platform_script(
        "Windows",
        "load_monitor_file",
        injector.script_manager.load_monitor_file,
        run_script_bool,
        api_name=api_name,
        file_path=file_path
    )


@mcp.tool()
def windows_fast_load_all_monitor_file(
    run_script_bool: Annotated[bool, "If True, immediately inject and execute"] = False,
) -> Dict[str, Any]:
    """
    Load comprehensive file monitoring for all file APIs.

    Args:
        run_script_bool: If True, immediately inject and execute

    Returns:
        Dict with status and message

    Prerequisites:
        - config.os must be 'Windows'
        - Must have an active session via attach() or spawn()

    Warning:
        Generates large volume of log output
    """
    return _load_platform_script(
        "Windows",
        "fast_load_all_monitor_file",
        injector.script_manager.fast_load_all_monitor_file,
        run_script_bool,
    )


@mcp.tool()
def windows_fast_load_monitor_memory_alloc(
    run_script_bool: Annotated[bool, "If True, immediately inject and execute"] = False,
) -> Dict[str, Any]:
    """
    Load memory allocation monitoring with executable memory detection.

    Args:
        run_script_bool: If True, immediately inject and execute

    Returns:
        Dict with status and message

    Prerequisites:
        - config.os must be 'Windows'
        - Must have an active session via attach() or spawn()

    Warning:
        High volume output and large memory dumps
    """
    return _load_platform_script(
        "Windows",
        "fast_load_monitor_memory_alloc",
        injector.script_manager.fast_load_monitor_memory_alloc,
        run_script_bool,
    )


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
