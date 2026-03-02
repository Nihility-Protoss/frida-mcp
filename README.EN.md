# Frida MCP Server

A Frida dynamic instrumentation server based on the Model Context Protocol (MCP), allowing AI models (such as Claude, Gemini, etc.) to perform dynamic analysis for mobile and desktop applications through a standardized interface.

## Project Credits
This project's source code and design are inspired by the following excellent open-source projects:
- [zhizhuodemao/frida-mcp](https://github.com/zhizhuodemao/frida-mcp): Provides the foundation for Android dynamic analysis and Frida management logic.
- [dnakov/frida-mcp](https://github.com/dnakov/frida-mcp): Provides a reference for the standard implementation using the MCP Python SDK.

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
- `get_device(device_id)`: Get a device by ID.
- `get_usb_device`: Get the current USB device information.
- `get_local_device`: Get the local device information (Windows).
- `list_applications(device_id?)`: List installed applications, including `identifier/name/pid?`.
- `get_frontmost_application(device_id)`: Get the current frontmost application.

### Process Management
- `enumerate_processes(device_id?)`: List processes on a device (if not specified: Windows uses local device, others use USB).
- `get_process_by_name(name, device_id?)`: Fuzzy-match a process by name (`found`, `pid`, `name`).
- `resume_process(pid, device_id?)`: Resume a suspended process.
- `kill_process(pid, device_id?)`: Terminate a running process.

### Process Operations & Injection
- `attach(target, device_id?, initial_script?, script_file_path?, output_file?)`: Attach to a running process (PID/package). Inject JS either as string or absolute `.js` path and optionally save logs to a local file.
- `spawn(package_name, device_id?, initial_script?, script_file_path?, output_file?)`: Launch an app in suspended state and inject, then use `resume_process` to continue.

### Logging
- `get_messages(max_messages=100)`: Get a snapshot of the global Hook/Log buffer.

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
