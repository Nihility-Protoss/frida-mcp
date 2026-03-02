# Frida MCP Server

这是一个基于 Model Context Protocol (MCP) 的 Frida 动态调试服务器，允许 AI 模型（如 Claude、Gemini 等）通过标准化的接口执行移动端和桌面端的动态分析。

## 项目来源
本项目源码和设计参考了以下两个优秀的开源项目：
- [zhizhuodemao/frida-mcp](https://github.com/zhizhuodemao/frida-mcp): 提供了基础的 Android 动态分析和 Frida 管理逻辑。
- [dnakov/frida-mcp](https://github.com/dnakov/frida-mcp): 提供了基于 MCP Python SDK 的标准实现参考。

## 核心功能

### 1. 设备与进程管理
- **设备枚举**: 列出所有连接的 USB、本地或远程设备。
- **进程管理**: 实时列出目标设备上运行的所有进程，支持按名称搜索进程。
- **应用列表**: 获取设备上已安装的应用程序信息（包名、名称等）。
- **前台应用识别**: 自动获取当前设备最前端运行的应用程序。

### 2. 动态注入与 Hook
- **Attach 模式**: 附加到正在运行的进程进行实时调试。
- **Spawn 模式**: 拉起并挂起应用，在应用启动的第一时间注入脚本。
- **脚本管理**: 支持直接输入 JS 代码字符串或通过绝对路径加载 `.js` 脚本文件。
- **日志输出**: 自动重定向 `console.log` 到 MCP 消息缓冲区，支持实时获取 Hook 日志。

### 3. Frida Server 自动化
- **Android 支持**: 自动管理 Android 上的 `frida-server`（启动、停止、状态检查、ADB 端口转发）。
- **Windows 支持**: 支持 Windows 本地 `frida-server` 的管理。
- **高度可定制**: 支持自定义 `frida-server` 的文件路径、名称及监听端口。

### 4. 灵活的配置管理
- **分层配置**: 支持全局配置 (`config.json`) 和项目特定配置 (`frida.mcp.config.json`)。
- **运行时配置**: 提供一系列 `config_` 工具，可在不重启服务器的情况下即时修改配置、保存状态或初始化新项目。
- **远程支持**: 当 MCP 启动地址设为 `0.0.0.0` 时，`config_init` 会自动优化配置文件存储逻辑。

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动服务器
```bash
python src/frida_mcp/frida_mcp.py
```
默认情况下，服务器将在 `127.0.0.1:8032` 启动。

## 可用工具 (MCP Tools)

### 配置管理
- `config_get`: 获取当前活跃的配置、全局和项目配置文件的路径及其状态。
- `config_set`: 更新内存中的配置，可选是否立即持久化到文件。
- `config_init`: 初始化项目配置。支持自定义路径，并在 `0.0.0.0` 模式下自动处理。
- `config_save`: 将当前内存中的活跃配置保存到当前项目配置文件中。

### Frida Server 管理
- `start_android_frida_server`: 启动 Android 设备上的 frida-server。
- `stop_android_frida_server`:  停止 Android 设备上的 frida-server。
- `check_android_frida_status`: 检测 Android frida-server 是否在运行。
- `start_windows_frida_server`: 启动 Windows 本地 frida-server。
- `stop_windows_frida_server`:  停止 Windows 本地 frida-server。
- `check_windows_frida_status`: 检测 Windows 本地 frida-server 是否在运行。

### 设备与应用工具
- `enumerate_devices`: 列出系统连接的所有设备。
- `get_device`: 根据 ID 获取特定设备信息。
- `get_usb_device`: 获取连接的 USB 设备信息。
- `get_local_device`: 获取本地设备信息。
- `enumerate_processes`: 列出设备上运行的所有进程。
- `get_process_by_name`: 根据名称在设备上查找进程。
- `list_applications`: 列出设备上的已安装应用。
- `get_frontmost_application`: 获取当前前台应用信息。

### 注入与日志
- `attach`: 附加到运行中的进程，支持指定 PID 或包名，并可选注入 JS 脚本。
- `spawn`: 拉起应用（挂起态）并附加，支持在恢复前注入脚本。
- `resume_process`: 恢复被挂起的进程。
- `kill_process`: 终止正在运行的进程。
- `get_messages`: 获取全局 Hook/Log 文本缓冲，实时同步 `console.log` 输出。

## 远程连接与 HTTP 协议
当 `MCP_HOST` 设置为 `0.0.0.0` 时，服务器将监听所有网络接口。
- **Transport**: 使用 `streamable-http` 传输协议。
- **Client 配置**: 在客户端中，你需要配置远程服务器的 URL。例如在某些 MCP 客户端中，连接地址为 `http://<服务器IP>:8032/sse`。
- **注意**: 使用 `config_init` 可以在远程模式下自动管理配置文件，确保配置的一致性。

---
*注：本项目仅用于技术研究与学习，请在遵循相关法律法规的前提下使用。*
