# Frida MCP Server

这是一个基于 Model Context Protocol (MCP) 的 Frida 动态调试服务器，允许 AI 模型（如 Claude、Gemini 等）通过标准化的接口执行移动端和桌面端的动态分析。

## 项目来源
本项目源码和设计参考了以下两个优秀的开源项目：
- [zhizhuodemao/frida-mcp](https://github.com/zhizhuodemao/frida-mcp): 提供了基础的 Android 动态分析和 Frida 管理逻辑。
- [dnakov/frida-mcp](https://github.com/dnakov/frida-mcp): 提供了基于 MCP Python SDK 的标准实现参考。

## 核心功能

### 1. 设备与进程管理
- **设备枚举**: 列出所有连接的 USB 或远程设备。
- **进程枚举**: 实时列出目标设备上运行的所有进程及其 PID。
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
- **远程支持**: 当 MCP 启动地址设为 `0.0.0.0` 时，自动优化配置文件存储逻辑以支持远程调用。

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动服务器
```bash
python src/frida_mcp/frida_mcp.py
```
默认情况下，服务器将在 `127.0.0.1:8000` 启动。

## 可用工具 (MCP Tools)
- `config_get`: 获取当前配置状态。
- `config_set`: 动态修改内存配置。
- `config_init`: 初始化项目环境。
- `config_save`: 持久化当前配置。
- `list_applications`: 列出已安装应用。
- `attach` / `spawn`: 执行脚本注入。
- `get_messages`: 读取 Hook 产生的日志。
- `start_android_frida_server` / `stop_android_frida_server`: 管理 Android 服务。

---
*注：本项目仅用于技术研究与学习，请在遵循相关法律法规的前提下使用。*
