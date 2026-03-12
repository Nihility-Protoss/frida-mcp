![](https://img.shields.io/badge/Kimi%20Assisted-75%25-00a67d)

# Frida MCP Server

A Frida dynamic debugging server based on Model Context Protocol (MCP), allowing AI models (such as Claude, Gemini, etc.) to perform dynamic analysis on mobile and desktop platforms through a standardized interface.

## Project Source
This project references the following open source projects:
- [zhizhuodemao/frida-mcp](https://github.com/zhizhuodemao/frida-mcp): Provides basic Android dynamic analysis and Frida management logic.
- [dnakov/frida-mcp](https://github.com/dnakov/frida-mcp): Provides a standard implementation reference based on MCP Python SDK.

Some JS files are from the following articles:
- [scripts/android-js/anti_libDexHelper.so.js](https://bbs.kanxue.com/thread-289545.htm) [Original] Bypassing new version Frida detection for certain protection
- [scripts/android-js/hook_clone.js](https://bbs.kanxue.com/thread-289404.htm) [Original] Analysis of certain ventilation control parameters & Frida bypass (Part 1)
- [scripts/android-js/hook_net_libssl.so.js](https://bbs.kanxue.com/thread-289085.htm) Frida intercepting http/https requests

## Core Features

### 1. Cross-platform Device and Process Management
Unified support for device and process operations on Android and Windows platforms:
- **Device Management**: Enumerate USB, local, or remote devices, retrieve device basic information.
- **Process Management**: List running processes, support search by name, resume suspended processes, and terminate processes.
- **Application Management**: Get installed application list, foreground app information, support operating applications by package name.

### 2. Dynamic Debugging and Script Injection
Provides complete dynamic debugging lifecycle management:
- **Session Management**: Supports Attach mode (attach to running processes) and Spawn mode (launch and suspend applications), provides session status query and disconnect functionality.
- **Script Management**: Built-in script builder, supports user custom script injection, provides script list query, content viewing, and reset functionality.
- **Log Capture**: Automatically redirect target process `console.log` to MCP message buffer, supports incremental Hook log retrieval.

### 3. Specialized Hook Script Library
Pre-built practical Hook scripts for different platforms:
- **Android Specialization**: Anti-DexHelper detection (hook clone/pthread/nop critical threads), SSL/TLS network traffic interception (libssl), clone system call monitoring, Activity lifecycle tracking.
- **Windows Specialization**: API call monitoring, registry operation monitoring, file operation monitoring (supports fine-grained or full monitoring), executable memory allocation monitoring (auto-dump suspicious RX/RWX memory).
- **General Tools**: Module Export function enumeration (supports *.so and *.dll).

### 4. Frida Server Automation
Simplifies Frida runtime environment deployment and management:
- **Android**: Automatic management of `frida-server` on devices (start, stop, status check, ADB port forwarding).
- **Windows**: Supports start, stop, and status check for local `frida-server`.
- **Flexible Configuration**: Supports customizing frida-server file path, name, and listening port.

### 5. Layered Configuration and Remote Support
- **Configuration System**: Supports hierarchical management of global configuration and project-specific configuration, allows dynamic configuration modification at runtime with optional persistence to specified levels.
- **Remote Access**: When MCP service binds to `0.0.0.0`, supports remote HTTP connections, configuration files are automatically optimized for storage logic to ensure multi-device access consistency.

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Start Server
```bash
python src/frida_mcp/frida_mcp.py
```
By default, the server will start at `127.0.0.1:8032`.

## Available Tools (MCP Tools)

### Configuration Management
- `config_get` (resource: `frida://config`): Get current active configuration and global/project configuration file paths and existence.
- `config_set`: Update memory configuration (supports `server_path`, `server_name`, `server_port`, `device_id`, `adb_path`, `os`). `os` only allows `Android` or `Windows`; can be persisted immediately via `save_to=('global'|'project')`.
- `config_init`: Initialize/switch project configuration file path and write current active configuration; automatically saves to global directory in `0.0.0.0` mode.
- `config_save`: Save current active memory configuration to current project configuration file.

### Frida Server Management
- `start_android_frida_server`: Start frida-server on Android device (requires `config.os=Android`).
- `stop_android_frida_server`: Stop frida-server on Android device (requires `config.os=Android`).
- `check_android_frida_status`: Check if Android frida-server is running (requires `config.os=Android`).
- `start_windows_frida_server`: Start local frida-server on Windows (requires `config.os=Windows`).
- `stop_windows_frida_server`: Stop local frida-server on Windows (requires `config.os=Windows`).
- `check_windows_frida_status`: Check if local frida-server on Windows is running (requires `config.os=Windows`).
- `check_frida_status`: Automatically detect frida-server running status for the current platform based on `os`.

### Device and Application Tools
- `enumerate_devices`: List all connected devices (ID/Name/Type).
- `get_device`: Get specified device information.
- `get_usb_device`: Get current USB device information.
- `get_local_device`: Get local device information (Windows).
- `list_applications`: List installed applications, including `identifier/name/pid?`.
- `get_frontmost_application`: Get current foreground application information.

### Process Management
- `enumerate_processes`: List running processes on the device (when not specified: Windows uses local device, others use USB).
- `get_process_by_name`: Fuzzy match process by name (returns `found`, `pid`, `name`).
- `resume_process`: Resume a suspended process.
- `kill_process`: Terminate a running process.

### Process Operation and Session Management
- `attach`: Attach to a running process (PID/Package name), establish session connection.
- `spawn`: Launch application (suspended state) and attach, establish session connection, supports passing startup arguments (e.g., `--arg1 value1`).
- `detach`: Disconnect current active session.
- `get_session_info`: Get current active session information (target/pid).

### Log Management
- `get_messages`: Get global Hook/Log text buffer snapshot (non-consuming mode).
- `get_new_messages`: Get all log data from last output to current moment (recommended for priority use).

### Script Management
- `get_script_list`: Get list of all available built-in script file names under current injector.
- `get_script_now`: Get the already built script content in current injector.
- `reset_script_now`: Reset script in current injector, restore to initial state.
- `inject_user_script_run`: Inject and run user custom script (string form), only executes the injected part.
- `inject_user_script_run_all`: Inject and run user custom script, executes all content in ScriptManager.

### General Utility Scripts
- `util_load_module_enumerateExports`: Enumerate all Export functions in a module, works in both Android (*.so) and Windows (*.dll) environments.

### Android-specific Script Tools
- `android_load_script_anti_DexHelper_hook_clone`: Load Android anti-DexHelper detection script (hook clone).
- `android_load_script_anti_DexHelper_hook_pthread`: Load Android anti-DexHelper detection script (hook pthread).
- `android_load_script_anti_DexHelper`: Load Android anti-DexHelper detection script (nop critical threads), requires hook address list.
- `android_load_hook_net_libssl`: Load Android network library SSL Hook script (http/https).
- `android_load_hook_clone`: Load Android clone system call Hook script, used to counter detection of specified SO files.
- `android_load_hook_activity`: Load Android Activity lifecycle Hook script.

### Windows-specific Script Tools
- `windows_load_monitor_api`: Load Windows platform API monitoring script.
- `windows_load_monitor_registry`: Load Windows platform registry monitoring script, supports various registry APIs.
- `windows_load_monitor_file`: Load Windows platform file monitoring script, supports various file operation APIs.
- `windows_fast_load_all_monitor_file`: Load all file monitoring APIs for Windows platform, may generate extremely large amounts of log information, use with caution.
- `windows_fast_load_monitor_memory_alloc`: Load Windows platform memory allocation monitoring script, automatically dumps memory when RX/RWX executable memory is detected and executed, use with caution.

### Resources (MCP Resources)
- `frida://version`: Return current Frida and frida-mcp version information.
- `frida://config`: Return active configuration and configuration file path information.

## Remote Connection and HTTP Protocol
When `MCP_HOST` is set to `0.0.0.0`, the server will listen on all network interfaces.
- **Transport**: Uses `streamable-http` transport protocol.
- **Client Configuration**: In the client, you need to configure the remote server URL, e.g., `http://<serverIP>:8032/mcp`.
- **Note**: Using `config_init` can automatically manage configuration files in remote mode, ensuring consistency.

---
*Note: This project is for technical research and learning purposes only. Please use it in compliance with relevant laws and regulations.*
