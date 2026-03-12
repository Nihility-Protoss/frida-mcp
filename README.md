![](https://img.shields.io/badge/KimiK2%20Assisted-75%25-00a67d)
[![MCPAmpel](https://img.shields.io/endpoint?url=https://mcpampel.com/badge/Nihility-Protoss/frida-mcp.json)](https://mcpampel.com/repo/Nihility-Protoss/frida-mcp)

# Frida MCP Server

这是一个基于 Model Context Protocol (MCP) 的 Frida 动态调试服务器，允许 AI 模型（如 Claude、Gemini 等）通过标准化的接口执行移动端和桌面端的动态分析。

## 项目来源
本项目源码和设计参考了以下开源项目：
- [zhizhuodemao/frida-mcp](https://github.com/zhizhuodemao/frida-mcp): 提供了基础的 Android 动态分析和 Frida 管理逻辑。
- [dnakov/frida-mcp](https://github.com/dnakov/frida-mcp): 提供了基于 MCP Python SDK 的标准实现参考。

部分js文件来自以下文章：
- [scripts/android-js/anti_libDexHelper.so.js](https://bbs.kanxue.com/thread-289545.htm) [原创]某加固新版frida检测绕过
- [scripts/android-js/hook_clone.js](https://bbs.kanxue.com/thread-289404.htm) [原创]学某通风控参数分析&Frida绕过(上) 
- [scripts/android-js/hook_net_libssl.so.js](https://bbs.kanxue.com/thread-289085.htm) frida拦截http、https请求

## 核心功能

### 1. 跨平台设备与进程管理
统一支持 Android 和 Windows 平台的设备与进程操作：
- **设备管理**: 枚举 USB、本地或远程设备，获取设备基本信息。
- **进程管理**: 列出运行中的进程，支持按名称搜索、恢复挂起进程和终止进程。
- **应用管理**: 获取已安装应用列表、前台应用信息，支持通过包名操作应用。

### 2. 动态调试与脚本注入
提供完整的动态调试生命周期管理：
- **会话管理**: 支持 Attach 模式（附加运行中进程）和 Spawn 模式（拉起并挂起应用），提供会话状态查询和断开功能。
- **脚本管理**: 内置脚本构建器，支持用户自定义脚本注入，提供脚本列表查询、内容查看和重置功能。
- **日志捕获**: 自动重定向目标进程的 `console.log` 到 MCP 消息缓冲区，支持增量获取 Hook 日志。

### 3. 专用 Hook 脚本库
针对不同平台预置了多种实用 Hook 脚本：
- **Android 专项**: 反 DexHelper 检测（hook clone/pthread/nop 关键线程）、SSL/TLS 网络流量拦截（libssl）、clone 系统调用监控、Activity 生命周期追踪。
- **Windows 专项**: API 调用监控、注册表操作监控、文件操作监控（支持细粒度或全量监控）、可执行内存分配监控（自动 dump 可疑 RX/RWX 内存）。
- **通用工具**: 模块 Export 函数枚举（支持 *.so 和 *.dll）。

### 4. Frida Server 自动化
简化 Frida 运行环境的部署与管理：
- **Android**: 自动管理设备上的 `frida-server`（启动、停止、状态检查、ADB 端口转发）。
- **Windows**: 支持本地 `frida-server` 的启动、停止和状态检查。
- **灵活配置**: 支持自定义 frida-server 的文件路径、名称及监听端口。

### 5. 分层配置与远程支持
- **配置体系**: 支持全局配置和项目特定配置的分层管理，可在运行时动态修改配置并选择性地持久化到指定层级。
- **远程访问**: 当 MCP 服务绑定到 `0.0.0.0` 时，支持远程 HTTP 连接，配置文件会自动优化存储逻辑以确保多设备访问一致性。

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
- `get_device`: 获取指定设备信息。
- `get_usb_device`: 获取当前 USB 设备信息。
- `get_local_device`: 获取本地设备信息（Windows）。
- `list_applications`: 列出已安装应用，包含 `identifier/name/pid?`。
- `get_frontmost_application`: 获取当前前台应用信息。

### 进程管理
- `enumerate_processes`: 列出设备上运行的进程（未指定时：Windows 使用本地设备，其他使用 USB）。
- `get_process_by_name`: 按名称模糊匹配进程（返回 `found`、`pid`、`name`）。
- `resume_process`: 恢复被挂起的进程。
- `kill_process`: 终止正在运行的进程。

### 进程操作与会话管理
- `attach`: 附加到运行中的进程（PID/包名），建立 session 连接。
- `spawn`: 拉起应用（挂起态）并附加，建立 session 连接，支持传入启动参数（如 `--arg1 value1`）。
- `detach`: 断开当前活跃的 session 连接。
- `get_session_info`: 获取当前活跃的 session 信息（target/pid）。

### 日志管理
- `get_messages`: 获取全局 Hook/Log 文本缓冲快照（非消费模式）。
- `get_new_messages`: 获取上次输出到此刻之间的所有 log 数据（推荐优先使用）。

### 脚本管理
- `get_script_list`: 获得当前 injector 下所有可用的内置 script 文件名列表。
- `get_script_now`: 获得当前 injector 中已经构建好的 script 内容。
- `reset_script_now`: 重置当前 injector 中的 script，恢复初始状态。
- `inject_user_script_run`: 注入并运行用户自定义脚本（字符串形式），仅执行注入的部分。
- `inject_user_script_run_all`: 注入并运行用户自定义脚本，执行 ScriptManager 中所有内容。

### 通用工具脚本
- `util_load_module_enumerateExports`: 枚举模块中所有的 Export 函数，Android（*.so）和 Windows（*.dll）环境下都可使用。

### Android 专用脚本工具
- `android_load_script_anti_DexHelper_hook_clone`: 加载 Android 平台的反 DexHelper 检测脚本（hook clone）。
- `android_load_script_anti_DexHelper_hook_pthread`: 加载 Android 平台的反 DexHelper 检测脚本（hook pthread）。
- `android_load_script_anti_DexHelper`: 加载 Android 平台的反 DexHelper 检测脚本（nop 关键线程），需传入 hook 地址列表。
- `android_load_hook_net_libssl`: 加载 Android 平台的网络库 SSL Hook 脚本（http/https）。
- `android_load_hook_clone`: 加载 Android 平台的 clone 系统调用 Hook 脚本，用于对抗指定 SO 文件的检测。
- `android_load_hook_activity`: 加载 Android 平台的 Activity 生命周期 Hook 脚本。

### Windows 专用脚本工具
- `windows_load_monitor_api`: 加载 Windows 平台的 API 监控脚本。
- `windows_load_monitor_registry`: 加载 Windows 平台的注册表监控脚本，支持多种注册表 API。
- `windows_load_monitor_file`: 加载 Windows 平台的文件监控脚本，支持多种文件操作 API。
- `windows_fast_load_all_monitor_file`: 加载 Windows 平台的所有文件监控 API，可能造成极大量的 log 信息，请谨慎使用。
- `windows_fast_load_monitor_memory_alloc`: 加载 Windows 平台的内存分配监控脚本，检测到 RX/RWX 可执行内存时自动 dump，请谨慎使用。

### 资源 (MCP Resources)
- `frida://version`: 返回当前 Frida 和 frida-mcp 的版本信息。
- `frida://config`: 返回活跃配置与配置文件路径信息。

## 远程连接与 HTTP 协议
当 `MCP_HOST` 设置为 `0.0.0.0` 时，服务器将监听所有网络接口。
- **Transport**: 使用 `streamable-http` 传输协议。
- **Client 配置**: 在客户端中，你需要配置远程服务器的 URL，例如 `http://<服务器IP>:8032/mcp`。
- **注意**: 使用 `config_init` 可在远程模式下自动管理配置文件，确保一致性。

---
*注：本项目仅用于技术研究与学习，请在遵循相关法律法规的前提下使用。*
