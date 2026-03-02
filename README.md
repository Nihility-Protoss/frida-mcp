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
- **远程支持**: 当 MCP 启动地址设为 `0.0.0.0` 时，调用`config_init` 会自动优化配置文件存储逻辑。

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
- `config_get` (resource: `frida://config`): 获取当前活跃配置与全局/项目配置文件路径与存在性。
- `config_set`: 更新内存配置（支持 `server_path`、`server_name`、`server_port`、`device_id`、`adb_path`、`os`）。`os` 仅允许 `Android` 或 `Windows`；可通过 `save_to=('global'|'project')` 立即持久化。
- `config_init`: 初始化/切换项目配置文件路径，并写入当前活跃配置；`0.0.0.0` 模式下自动保存至全局目录。
- `config_save`: 将当前活跃内存配置保存到当前项目配置文件。

### Frida Server 管理
- `start_android_frida_server`: 启动 Android 设备上的 frida-server（需 `config.os=Android`）。
- `stop_android_frida_server`: 停止 Android 设备上的 frida-server（需 `config.os=Android`）。
- `check_android_frida_status`: 检测 Android frida-server 是否在运行（需 `config.os=Android`）。
- `start_windows_frida_server`: 启动 Windows 本地 frida-server（需 `config.os=Windows`）。
- `stop_windows_frida_server`: 停止 Windows 本地 frida-server（需 `config.os=Windows`）。
- `check_windows_frida_status`: 检测 Windows 本地 frida-server 是否在运行（需 `config.os=Windows`）。
- `check_frida_status`: 根据当前 `os` 自动检测对应平台的 frida-server 运行状态。

### 设备与应用工具
- `enumerate_devices`: 列出所有连接的设备（ID/名称/类型）。
- `get_device(device_id)`: 获取指定设备信息。
- `get_usb_device`: 获取当前 USB 设备信息。
- `get_local_device`: 获取本地设备信息（Windows）。
- `list_applications(device_id?)`: 列出已安装应用，包含 `identifier/name/pid?`。
- `get_frontmost_application(device_id)`: 获取当前前台应用信息。

### 进程管理
- `enumerate_processes(device_id?)`: 列出设备上运行的进程（未指定时：Windows 使用本地设备，其他使用 USB）。
- `get_process_by_name(name, device_id?)`: 按名称模糊匹配进程（返回 `found`、`pid`、`name`）。
- `resume_process(pid, device_id?)`: 恢复被挂起的进程。
- `kill_process(pid, device_id?)`: 终止正在运行的进程。

### 进程操作与注入
- `attach(target, device_id?, initial_script?, script_file_path?, output_file?)`: 附加到运行中的进程（PID/包名），可注入 JS（字符串或绝对路径 .js），可保存日志到本地文件。
- `spawn(package_name, device_id?, initial_script?, script_file_path?, output_file?)`: 拉起应用（挂起态）并注入，随后可由 `resume_process` 恢复。

### 日志
- `get_messages(max_messages=100)`: 获取全局 Hook/Log 文本缓冲快照。

### 资源 (MCP Resources)
- `frida://version`: 返回当前 Frida 版本字符串。
- `frida://config`: 返回活跃配置与配置文件路径信息。

## 远程连接与 HTTP 协议
当 `MCP_HOST` 设置为 `0.0.0.0` 时，服务器将监听所有网络接口。
- **Transport**: 使用 `streamable-http` 传输协议。
- **Client 配置**: 在客户端中，你需要配置远程服务器的 URL，例如 `http://<服务器IP>:8032/mcp`。
- **注意**: 使用 `config_init` 可在远程模式下自动管理配置文件，确保一致性。

---
*注：本项目仅用于技术研究与学习，请在遵循相关法律法规的前提下使用。*
