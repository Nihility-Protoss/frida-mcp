# Frida MCP Skill 规范

## 目的

本 Skill 定义了与 Frida MCP 实现交互所需的**强制工作流程**。
AI **必须**遵循规定的顺序以确保确定性和稳定的行为。

------------------------------------------------------------------------

## 1. 初始化（强制）

每次会话开始时，AI **必须**读取：

- `frida://version`
- `frida://config`

这些资源用于：

- 确认 MCP 版本兼容性
- 加载当前配置状态
- 确定操作系统和执行上下文

在读取这两个资源之前，**不得**开始任何 Frida 操作。

------------------------------------------------------------------------

## 2. 配置管理

### 2.1 新项目初始化

对于每个新的 Frida 项目，AI **应该**：

1. 调用 `config_init` 创建项目特定配置
2. 使用 `config_set` 修改所需字段
3. 批量更新后，调用 `config_save` 将配置持久化到磁盘

### 2.2 Frida Server 用户确认

在启动 Frida 操作之前，AI **应该**根据初始化期间已读取的配置，以简单易懂的方式与用户确认 frida-server 详情。

建议的确认流程：

1. 询问 frida-server 是否已在目标设备上成功启动
2. 从当前配置中读取 frida-server 路径
3. 要求用户确认 frida-server 在运行 MCP 的设备上的确切位置（即使配置中已包含路径）
4. 在尝试启动或检查 frida-server 之前更新配置

此确认步骤有助于避免因服务器路径不正确而导致的启动失败。

### 2.3 配置规则

- 所有环境相关参数 **必须** 存储在配置中
- `config_set` 仅修改内存中的配置
- **必须**调用 `config_save` 以持久化更改

------------------------------------------------------------------------

## 3. Frida Server 管理（前置条件）

在执行任何 Frida 功能之前，AI **必须**确保正确的 frida-server 正在运行。

### Android（要求 `config.os=Android`）

- `start_android_frida_server`
- `stop_android_frida_server`
- `check_android_frida_status`

### Windows（要求 `config.os=Windows`）

- `start_windows_frida_server`
- `stop_windows_frida_server`
- `check_windows_frida_status`

### 跨平台

- `check_frida_status`（基于 config.os 自动检测）

AI **必须**：

1. 从配置中验证当前操作系统
2. 检查服务器状态
3. 如未运行则启动服务器

------------------------------------------------------------------------

## 4. 设备发现

AI **必须**与用户交互以识别目标设备。

步骤：

1. 调用 `enumerate_devices`
2. 确定正确的 `device_id`
3. 使用 `config_set` 存储 device_id
4. 使用 `config_save` 持久化

所有后续操作 **必须** 使用配置好的 device_id。

------------------------------------------------------------------------

## 5. 目标进程控制

在脚本注入之前，AI **必须**连接或启动目标进程。

有两种可能的方法：

- `attach(target: str)` – 附加到正在运行的进程
- `spawn(package_name: str)` – 以挂起状态启动目标进程

参数：

- `target`: 正在运行的进程名称
- `package_name`: 包名或可执行文件名

仅在其中一个调用成功后，才允许进行脚本注入。

------------------------------------------------------------------------

## 6. 脚本构建与注入

附加到进程后，AI 可以构建要注入的脚本。

### 脚本管理

- `get_script_list`
- `get_script_now`
- `reset_script_now`
- `inject_user_script_run`
- `inject_user_script_run_all`

### Android 脚本工具

- `android_load_script_anti_DexHelper_hook_clone`
- `android_load_script_anti_DexHelper_hook_pthread`
- `android_load_script_anti_DexHelper`
- `android_load_hook_net_libssl`
- `android_load_hook_clone`
- `android_load_hook_activity`

### 通用脚本工具

- `util_load_module_enumerateExports`

### Windows 脚本工具

- `windows_load_monitor_api`
- `windows_load_monitor_registry`
- `windows_load_monitor_file`
- `windows_fast_load_all_monitor_file`
- `windows_fast_load_monitor_memory_alloc`

### 脚本执行行为

所有脚本工具函数（除两个用户注入函数外）都包含：

`run_script_bool: bool = False`

含义：

- `False` → 仅将脚本追加到当前注入器脚本
- `True` → 追加并立即执行

特殊行为：

- `inject_user_script_run`
- `inject_user_script_run_all`

这些函数立即执行，不使用 `run_script_bool`。

### 脚本组合规则

- 多个脚本工具调用会连接成**当前注入器脚本**
- 执行脚本时将：
  1. 卸载先前注入的脚本
  2. 注入新构建的脚本
  3. 立即执行

------------------------------------------------------------------------

# 7. 消息和日志处理

脚本注入后，必须使用以下方式获取运行时输出：

- get_messages
- get_new_messages

定义：

get_messages  
返回完整的全局日志缓冲区快照。

get_new_messages  
返回自上次获取以来产生的消息。

AI 必须决定何时检索日志：

可能的策略：

- 等待适当时间让钩子触发
- 要求用户在目标应用中执行操作
- 等待用户确认操作已完成

然后才获取日志以获得钩子结果。

------------------------------------------------------------------------

# 8. 会话管理

在单个任务结束时，AI 可以调用：

- detach
- get_session_info

目的：

- 安全终止会话
- 检查会话是否仍处于活动状态

------------------------------------------------------------------------

# 9. 多目标工作流程

完成一个程序的工作后：

如果步骤 1-4 保持不变，AI 可以直接从以下步骤开始：

步骤 5（进程连接）

这允许使用相同环境高效处理多个目标。

------------------------------------------------------------------------

## 操作原则

- 严格遵守有序工作流程
- 绝不跳过初始化
- 绝不在未验证服务器状态的情况下执行 Frida 操作
- 在执行前持久化配置更改
