![](https://img.shields.io/badge/Kimi%20Assisted-75%25-00a67d)

[中文](./README.md) | [English](./README.EN.md)


# Frida MCP Server

This is a Frida dynamic analysis/debugging server based on the Model Context Protocol (MCP), enabling AI models (such as Claude, Gemini, etc.) to perform dynamic analysis on mobile and desktop targets through a standardized interface.

## Remote Connection and HTTP Protocol

When `MCP_HOST` is set to `0.0.0.0`, the server listens on all network interfaces.

- **Transport**: Uses the `streamable-http` transport protocol.
- **Client Configuration**: On the client side, configure the remote server URL, for example: `http://<ServerIP>:8032/mcp`.
- **Note**: Using `config_init` in remote mode can automatically manage configuration files to keep behavior consistent.

## Core Features

### 1. Cross-platform Device and Process Management

Unified support for device and process operations on both Android and Windows:

- **Device Management**: Enumerate USB, local, or remote devices and retrieve basic device information.
- **Process Management**: List running processes, search by name, resume suspended processes, and terminate processes.
- **Application Management**: Retrieve installed app lists and frontmost app information, and operate apps by package name.

### 2. Dynamic Debugging and Script Injection

Provides complete lifecycle management for dynamic debugging:

- **Session Management**: Supports Attach mode (attach to running processes) and Spawn mode (launch and suspend applications), with session status query and disconnect capabilities.
- **Script Management**: Built-in script builder with support for custom script injection, script list querying, content inspection, and reset.
- **Log Capture**: Automatically redirects target-process `console.log` output to the MCP message buffer, with incremental Hook log retrieval.

### 3. Specialized Hook Script Library

Built-in practical Hook scripts for different platforms:

- **Android**: Anti-DexHelper detection bypass (hook clone/pthread/nop critical threads), SSL/TLS traffic interception (`libssl`), clone syscall monitoring, and Activity lifecycle tracking.
- **Windows**: API call monitoring, registry operation monitoring, file operation monitoring (fine-grained or full), and executable memory allocation monitoring (auto dump for suspicious RX/RWX memory).
- **General Utilities**: Module export enumeration (supports `*.so` and `*.dll`).

### 4. Frida Server Automation

Simplifies Frida runtime deployment and management:

- **Android**: Automatically manages device-side `frida-server` (start, stop, status check, ADB port forwarding).
- **Windows**: Supports start, stop, and status checks for local `frida-server`.
- **Flexible Configuration**: Supports custom frida-server path, filename, and listening port.

### 5. Layered Configuration and Remote Support

- **Configuration System**: Supports layered management of global and project-specific configuration, with runtime updates and optional persistence to a selected scope.
- **Remote Access**: When MCP is bound to `0.0.0.0`, remote HTTP access is supported, and configuration file storage behavior is optimized for multi-device consistency.

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

- `config_get` (resource: `frida://config`): Get the current active configuration plus global/project config file paths and existence status.
- `config_set`: Update in-memory config (supports `server_path`, `server_name`, `server_port`, `device_id`, `adb_path`, `os`). `os` only allows `Android` or `Windows`; can be persisted immediately via `save_to=('global'|'project')`.
- `config_init`: Initialize/switch the project config file path and write current active config; in `0.0.0.0` mode it auto-saves to the global directory.
- `config_save`: Save current active in-memory config to the current project config file.

### Frida Server Management

- `start_android_frida_server`: Start frida-server on Android (requires `config.os=Android`).
- `stop_android_frida_server`: Stop frida-server on Android (requires `config.os=Android`).
- `check_android_frida_status`: Check whether Android frida-server is running (requires `config.os=Android`).
- `start_windows_frida_server`: Start local frida-server on Windows (requires `config.os=Windows`).
- `stop_windows_frida_server`: Stop local frida-server on Windows (requires `config.os=Windows`).
- `check_windows_frida_status`: Check whether local Windows frida-server is running (requires `config.os=Windows`).
- `check_frida_status`: Automatically checks frida-server status based on the current `os`.

### Device and Application Tools

- `enumerate_devices`: List all connected devices (`ID/Name/Type`).
- `get_device`: Get specified device information.
- `get_usb_device`: Get current USB device information.
- `get_local_device`: Get local device information (Windows).
- `list_applications`: List installed applications, including `identifier/name/pid?`.
- `get_frontmost_application`: Get current frontmost application information.

### Process Management

- `enumerate_processes`: List running processes on the device (when unspecified: Windows uses local device, others use USB).
- `get_process_by_name`: Fuzzy-match a process by name (returns `found`, `pid`, `name`).
- `resume_process`: Resume a suspended process.
- `kill_process`: Terminate a running process.

### Process Operations and Session Management

- `attach`: Attach to a running process (`PID`/package name) and establish a session connection.
- `spawn`: Launch an application in suspended mode and attach, establishing a session connection; supports startup args (for example `--arg1 value1`).
- `detach`: Disconnect the current active session.
- `get_session_info`: Get current active session info (`target/pid`).

### Log Management

- `get_messages`: Retrieve a snapshot of the global Hook/Log text buffer (non-consuming mode).
- `get_new_messages`: Retrieve all log data produced since the previous retrieval (recommended as first choice).

### Script Management

- `get_script_list`: Get all available built-in script filenames for the current injector.
- `get_script_now`: Get the currently built script content in the injector.
- `reset_script_now`: Reset the current injector script to its initial state.
- `inject_user_script_run`: Inject and execute a user-provided script (string form), executing only the injected part.
- `inject_user_script_run_all`: Inject and execute a user-provided script, executing all content in ScriptManager.

### General Utility Scripts

- `util_load_module_enumerateExports`: Enumerate all exported functions in a module; available on both Android (`*.so`) and Windows (`*.dll`).

### Android-specific Script Tools

- `android_load_script_anti_DexHelper_hook_clone`: Load Android anti-DexHelper script (hook clone).
- `android_load_script_anti_DexHelper_hook_pthread`: Load Android anti-DexHelper script (hook pthread).
- `android_load_script_anti_DexHelper`: Load Android anti-DexHelper script (nop critical threads), requires a hook address list.
- `android_load_hook_net_libssl`: Load Android SSL network Hook script (`http/https`).
- `android_load_hook_clone`: Load Android clone syscall Hook script for detecting/countering specified SO checks.
- `android_load_hook_activity`: Load Android Activity lifecycle Hook script.

### Windows-specific Script Tools

- `windows_load_monitor_api`: Load Windows API monitoring script.
- `windows_load_monitor_registry`: Load Windows registry monitoring script, supporting multiple registry APIs.
- `windows_load_monitor_file`: Load Windows file monitoring script, supporting multiple file-operation APIs.
- `windows_fast_load_all_monitor_file`: Load all Windows file-monitoring APIs (may produce very large log volume; use with caution).
- `windows_fast_load_monitor_memory_alloc`: Load Windows memory allocation monitoring script; auto-dumps when RX/RWX executable memory is detected (use with caution).

### Resources (MCP Resources)

- `frida://version`: Returns current Frida and frida-mcp version information.
- `frida://config`: Returns active configuration and configuration file path information.

## Project Source

This project’s code and design reference the following open-source projects:

- [zhizhuodemao/frida-mcp](https://github.com/zhizhuodemao/frida-mcp): Provides core Android dynamic analysis and Frida management logic.
- [dnakov/frida-mcp](https://github.com/dnakov/frida-mcp): Provides a standard implementation reference based on the MCP Python SDK.

Some JS files come from the following articles:

- [scripts/android-js/anti_libDexHelper.so.js](https://bbs.kanxue.com/thread-289545.htm) [Original] Bypassing Frida detection in a newer protected target
- [scripts/android-js/hook_clone.js](https://bbs.kanxue.com/thread-289404.htm) [Original] Target analysis and Frida bypass via clone hook (Part 1)
- [scripts/android-js/hook_net_libssl.so.js](https://bbs.kanxue.com/thread-289085.htm) Frida interception of HTTP/HTTPS requests

---
*Note: This project is for technical research and learning only. Please use it in compliance with applicable laws and regulations.*
