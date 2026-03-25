# Frida MCP 技能规范

## 目标

本技能定义了与 Frida MCP 实现交互时必须遵循的操作流程。  
AI 必须按既定顺序执行，以保证行为稳定且可复现。

------------------------------------------------------------------------

## 1. 初始化（强制）

每次会话开始时，AI 必须先读取：

- `frida://version`
- `frida://config`

读取上述资源的目的：

- 确认 MCP 版本兼容性
- 加载当前配置状态
- 判断操作系统与执行上下文

在读取完这两个资源之前，不应开始任何 Frida 操作。

------------------------------------------------------------------------

## 2. 配置管理

### 2.1 新项目初始化

对于每个新的 Frida 项目，AI 应当：

1. 调用 `config_init` 创建项目级配置
2. 使用 `config_set` 修改所需字段
3. 批量更新后调用 `config_save` 持久化到磁盘

### 2.2 配置规则

- 所有环境相关参数都必须存储在配置中
- `config_set` 仅修改内存中的配置
- 需要落盘时必须调用 `config_save`

------------------------------------------------------------------------

## 3. Frida Server 管理（前置条件）

在执行任何 Frida 功能前，AI 必须确保正确的 frida-server 正在运行。

### Android（要求 `config.os=Android`）

- `start_android_frida_server`
- `stop_android_frida_server`
- `check_android_frida_status`

### Windows（要求 `config.os=Windows`）

- `start_windows_frida_server`
- `stop_windows_frida_server`
- `check_windows_frida_status`

### 跨平台

- `check_frida_status`（基于 `config.os` 自动检测）

AI 必须执行：

1. 从配置中确认当前 OS
2. 检查 server 状态
3. 若未运行则启动 server

------------------------------------------------------------------------

## 4. 设备发现

AI 必须与用户协作确认目标设备。

步骤：

1. 调用 `enumerate_devices`
2. 确定正确的 `device_id`
3. 使用 `config_set` 写入 `device_id`
4. 使用 `config_save` 持久化

后续所有操作都必须使用已配置的 `device_id`。

------------------------------------------------------------------------

## 5. 目标进程控制

在注入脚本前，AI 必须先连接或启动目标进程。

可选方式：

- `attach(target: str)`：附加到正在运行的进程
- `spawn(package_name: str)`：以挂起状态启动目标进程

参数说明：

- `target`：运行中的进程名
- `package_name`：包名或可执行文件名

仅当上述调用之一成功后，才允许进行脚本注入。

------------------------------------------------------------------------

## 6. 脚本构建与注入

附加到进程后，AI 可以构建并注入脚本。

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

除两种用户注入函数外，脚本工具函数都包含参数：

`run_script_bool: bool = False`

含义：

- `False`：仅将脚本追加到当前 injector 脚本中
- `True`：追加后立即执行

特殊行为：

- `inject_user_script_run`
- `inject_user_script_run_all`

这两个函数会立即执行，不使用 `run_script_bool`。

### 脚本组合规则

- 多次脚本工具调用会拼接到**当前 injector 脚本**
- 一次执行将会：
  1. 卸载此前注入的脚本
  2. 注入新构建的脚本
  3. 立即执行

------------------------------------------------------------------------

## 7. 消息与日志处理

脚本注入后，应通过以下工具读取运行输出：

- `get_messages`
- `get_new_messages`

定义：

`get_messages`  
返回全局日志缓冲区快照。

`get_new_messages`  
仅返回自上次读取之后产生的消息。

AI 需要判断何时拉取日志，常见策略：

- 给予 Hook 触发所需的等待时间
- 引导用户在目标应用中执行操作
- 等待用户确认操作已完成

然后再获取日志以收集 Hook 结果。

------------------------------------------------------------------------

## 8. Session 管理

单次任务结束后，AI 可调用：

- `detach`
- `get_session_info`

用途：

- 安全结束会话
- 检查当前是否仍有活动会话

------------------------------------------------------------------------

## 9. 多目标工作流

在一个目标程序处理完成后：

如果第 1-4 步环境不变，AI 可以直接从：

第 5 步（进程连接）开始。

这样可在同一环境下高效处理多个目标。

------------------------------------------------------------------------

## 操作原则

- 严格遵循有序流程
- 不得跳过初始化
- 未验证 server 状态前不得执行 Frida 操作
- 执行前应先持久化必要配置变更
