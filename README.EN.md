![](https://img.shields.io/badge/KimiK2%20Assisted-75%25-00a67d)

# Frida MCP Server

A Frida dynamic instrumentation server based on the Model Context Protocol (MCP), allowing AI models (such as Claude, Gemini, etc.) to perform dynamic analysis for mobile and desktop applications through a standardized interface.

## Project Credits
This project's source code and design are inspired by the following excellent open-source projects:
- [zhizhuodemao/frida-mcp](https://github.com/zhizhuodemao/frida-mcp): Provides the foundation for Android dynamic analysis and Frida management logic.
- [dnakov/frida-mcp](https://github.com/dnakov/frida-mcp): Provides a reference for the standard implementation using the MCP Python SDK.

Some js files are from the following articles:
- [scripts/android-js/anti_libDexHelper.so.js](https://bbs.kanxue.com/thread-289545.htm) [Original] Bypassing new version Frida detection in certain reinforcement
- [scripts/android-js/hook_clone.js](https://bbs.kanxue.com/thread-289404.htm) [Original] Analysis of certain ventilation control parameters & Frida bypass (Part 1)
- [scripts/android-js/hook_net_libssl.so.js](https://bbs.kanxue.com/thread-289085.htm) Frida intercepting http/https requests

## Core Features

### 1. Device and Process Management
- **Device Enumeration**: List all connected USB, local, or remote devices.
- **Process Management**: Real-time listing of all running processes on the target device, including search by process name.
- **Application List**: Retrieve information about installed applications (package ID, name, etc.).
- **Frontmost App Detection**: Automatically detect the currently active application on the device.

### 2. Dynamic Injection and Hooking
- **Attach Mode**: Attach to a running process for real-time debugging.
- **Spawn Mode**: Launch and suspend an application to inject scripts at the very beginning.
- **Script Management**: Support for direct JS code string input or loading `.js` script files via absolute paths.
- **Log Output**: Automatically redirects `console.log` to the MCP message buffer for real-time log retrieval.

### 3. Frida Server Automation
- **Android Support**: Automatic management of `frida-server` on Android (start, stop, status check, ADB port forwarding).
- **Windows Support**: Support for managing local `frida-server` on Windows.
- **Highly Customizable**: Support for custom `frida-server` file paths, binary names, and listening ports.

### 4. Flexible Configuration Management
- **Layered Configuration**: Support for global configuration (`config.json`) and project-specific configuration (`frida.mcp.config.json`).
- **Runtime Configuration**: Provides a set of `config_` tools to modify settings, save states, or initialize new projects on the fly without restarting.
- **Remote Support**: When the MCP host is set to `0.0.0.0`, `config_init` automatically optimizes the configuration storage logic.

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Start Server
```bash
python src/frida_mcp/frida_mcp.py
```
By default, the server starts at `127.0.0.1:8032`.

## Available Tools (MCP Tools)

### Configuration Management
- `config_get` (resource: `frida://config`): Get active configuration and paths/existence of global and project config files.
- `config_set`: Update in-memory configuration (`server_path`, `server_name`, `server_port`, `device_id`, `adb_path`, `os`). `os` accepts only `Android` or `Windows`. Use `save_to=('global'|'project')` to persist immediately.
- `config_init`: Initialize or switch the project config path and write the active config. In `0.0.0.0` mode, saves under the global directory automatically.
- `config_save`: Persist the current active memory configuration to the current project config file.

### Frida Server Management
- `start_android_frida_server`: Start frida-server on Android (`config.os=Android` required).
- `stop_android_frida_server`: Stop frida-server on Android (`config.os=Android` required).
- `check_android_frida_status`: Check whether frida-server is running on Android (`config.os=Android` required).
- `start_windows_frida_server`: Start local frida-server on Windows (`config.os=Windows` required).
- `stop_windows_frida_server`: Stop local frida-server on Windows (`config.os=Windows` required).
- `check_windows_frida_status`: Check whether local frida-server is running on Windows (`config.os=Windows` required).
- `check_frida_status`: Auto-detect and check frida-server status based on current `os`.

### Device and Application Tools
- `enumerate_devices`: List all connected devices (id/name/type).
- `get_device`: Get specified device information.
- `get_usb_device`: Get the current USB device information.
- `get_local_device`: Get the local device information (Windows).
- `list_applications`: List installed applications, including `identifier/name/pid?`.
- `get_frontmost_application`: Get the current frontmost application.

### Process Management
- `enumerate_processes`: List processes running on the device (when not specified: Windows uses local device, others use USB).
- `get_process_by_name`: Fuzzy-match a process by name (returns `found`, `pid`, `name`).
- `resume_process`: Resume a suspended process.
- `kill_process`: Terminate a running process.

### Process Operations & Injection
- `attach`: Attach to a running process (PID/package name).
- `spawn`: Launch an application (suspended state) and inject, will automatically resume when inject and run.

### Log Management
- `get_messages`: Get a snapshot of the global Hook/Log buffer.
- `get_new_messages`: Get all log data between the last output and now.

### Session Management
- `detach`: Disconnect the current session.
- `get_session_info`: Get information about the current active session.

### Script Management
- `get_script_list`: Get a list of all available built-in script filenames under the current injector.
- `get_script_now`: Get the currently built script in the injector.
- `reset_script_now`: Reset the script in the current injector.
- `inject_user_script_run`: Inject and run user-defined scripts (string format).
- `inject_user_script_run_all`: Inject and run user-defined scripts (file path format).

### Android-Specific Script Tools
- `android_load_script_anti_DexHelper_hook_clone`: Load Android platform anti-DexHelper detection script (hook clone).
- `android_load_script_anti_DexHelper_hook_pthread`: Load Android platform anti-DexHelper detection script (hook pthread).
- `android_load_script_anti_DexHelper`: Load Android platform anti-DexHelper detection script (nop key threads).
- `android_load_hook_net_libssl`: Load Android platform network library SSL hook script.
- `android_load_hook_clone`: Load Android platform clone system call hook script.
- `android_load_hook_activity`: Load Android platform Activity lifecycle hook script.

### Windows-Specific Script Tools
- `windows_load_monitor_api`: Load Windows platform API monitoring script.
- `windows_load_monitor_registry`: Load Windows platform registry monitoring script.
- `windows_load_monitor_file`: Load Windows platform file monitoring script.

### Resources (MCP Resources)
- `frida://version`: Return the current Frida version string.
- `frida://config`: Return active configuration and config file path information.

## Remote Connection and HTTP Protocol
When `MCP_HOST` is set to `0.0.0.0`, the server listens on all network interfaces.
- **Transport**: Uses the `streamable-http` transport protocol.
- **Client Configuration**: Configure the remote server URL, e.g., `http://<SERVER_IP>:8032/mcp`.
- **Note**: `config_init` helps manage configuration files automatically in remote mode for consistency.

---
*Note: This project is intended for research and educational purposes only. Please use it in compliance with relevant laws and regulations.*