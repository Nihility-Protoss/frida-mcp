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
- `config_get`: Retrieve active configuration, file paths, and server status.
- `config_set`: Update memory configuration, with an optional immediate persistence to file.
- `config_init`: Initialize project configuration. Supports custom paths and handles `0.0.0.0` mode automatically.
- `config_save`: Persist the current active memory configuration to the project configuration file.

### Frida Server Management
- `start_android_frida_server`: Start frida-server on an Android device.
- `stop_android_frida_server`:  Stop frida-server on an Android device.
- `check_android_frida_status`: Check if frida-server is running on Android.
- `start_windows_frida_server`: Start local frida-server on Windows.
- `stop_windows_frida_server`:  Stop local frida-server on Windows.
- `check_windows_frida_status`: Check if local frida-server is running on Windows.

### Device and Application Tools
- `enumerate_devices`: List all devices connected to the system.
- `get_device`: Get specific device information by ID.
- `get_usb_device`: Get USB device information.
- `get_local_device`: Get local device information.
- `enumerate_processes`: List all processes running on a device.
- `get_process_by_name`: Search for a process on a device by name.
- `list_applications`: List installed applications on a device.
- `get_frontmost_application`: Get info about the current frontmost application.

### Injection and Logging
- `attach`: Attach to a running process and optionally inject a script.
- `spawn`: Spawn an application and inject a script.
- `get_messages`: Retrieve global Hook/Log text buffer.

---
*Note: This project is intended for research and educational purposes only. Please use it in compliance with relevant laws and regulations.*
