# Frida MCP 技能规范

## 目标

本技能定义与 Frida MCP 交互时必须遵循的操作流程。\
AI 必须按照顺序执行，以保证行为稳定、可预测。

------------------------------------------------------------------------

## 1. 初始化（强制）

在每次会话开始时，AI 必须读取：

-   `frida://version`
-   `frida://config`

目的：

-   确认 MCP 版本兼容性
-   加载当前配置状态
-   确定操作系统与运行环境

在读取完成之前，不得执行任何 Frida 操作。

------------------------------------------------------------------------

## 2. 配置管理

### 2.1 新项目初始化

每个新的 Frida 项目开始时，AI 应当：

1.  调用 `config_init` 创建项目配置文件
2.  使用 `config_set` 设置所需参数
3.  在批量修改后调用 `config_save` 将内存配置写入文件

### 2.2 配置规则

-   所有与环境相关的参数必须写入 config
-   `config_set` 仅修改内存中的配置
-   必须调用 `config_save` 才能持久化

------------------------------------------------------------------------

## 3. Frida Server 管理（前置条件）

在执行任何 Frida 功能前，必须确认对应平台的 frida-server 已正确运行。

### Android（需 `config.os=Android`）

-   `start_android_frida_server`
-   `stop_android_frida_server`
-   `check_android_frida_status`

### Windows（需 `config.os=Windows`）

-   `start_windows_frida_server`
-   `stop_windows_frida_server`
-   `check_windows_frida_status`

### 跨平台

-   `check_frida_status`（根据 config.os 自动判断）

AI 必须：

1.  从 config 读取当前 OS
2.  检查 server 状态
3.  若未运行则启动

------------------------------------------------------------------------

## 4. 设备发现

AI 必须通过与用户交互确定目标设备。

步骤：

1.  调用 `enumerate_devices`
2.  确认目标 `device_id`
3.  使用 `config_set` 写入 device_id
4.  使用 `config_save` 持久化

后续所有操作必须基于已配置的 device_id。

------------------------------------------------------------------------

## 5. 目标进程控制

在注入脚本之前，AI 必须连接或启动目标进程。

可使用两种方式：

- `attach(target: str)`：附加到正在运行的进程
- `spawn(package_name: str)`：启动新的目标进程

参数说明：

- `target`：运行中的进程名
- `package_name`：应用包名或可执行文件名

只有成功执行上述操作后，才能进行脚本注入。

------------------------------------------------------------------------

## 6. 脚本构建与注入

完成进程附加后，可以开始构建并注入脚本。

### 脚本管理

- `get_script_list`
- `get_script_now`
- `reset_script_now`
- `inject_user_script_run`
- `inject_user_script_run_all`

### Android 专用脚本

- `android_load_script_anti_DexHelper_hook_clone`
- `android_load_script_anti_DexHelper_hook_pthread`
- `android_load_script_anti_DexHelper`
- `android_load_hook_net_libssl`
- `android_load_hook_clone`
- `android_load_hook_activity`

### 通用脚本工具

- `util_load_module_enumerateExports`

### Windows 专用脚本

- `windows_load_monitor_api`
- `windows_load_monitor_registry`
- `windows_load_monitor_file`
- `windows_fast_load_all_monitor_file`
- `windows_fast_load_monitor_memory_alloc`

### 脚本执行机制

所有脚本工具函数（除用户脚本注入函数外）都包含参数：

`run_script_bool: bool = False`

含义：

- `False`：仅将脚本追加到当前 injector 脚本中
- `True`：追加后立即执行

特殊情况：

- `inject_user_script_run`
- `inject_user_script_run_all`

这两个函数调用后会立即执行，不使用 `run_script_bool`。

### 脚本组合规则

- 多次调用脚本工具会 **拼接当前 injector 中的 script**
- 每次执行 script 时会：

1. 卸载之前注入的脚本
2. 注入当前构建的脚本
3. 立即执行


------------------------------------------------------------------------

# 7. 消息与日志处理

脚本注入后，需要通过以下函数获取运行日志：

- get_messages
- get_new_messages

说明：

get_messages  
返回当前 **全局日志缓冲区快照**。

get_new_messages  
返回 **自上次获取以来产生的日志**。

AI 需要自行判断何时获取日志，例如：

- 等待一段时间让 hook 触发
- 让用户在目标程序中执行操作
- 等待用户确认操作完成

随后再调用日志函数获取 hook 输出。

------------------------------------------------------------------------

# 8. Session 管理

单轮操作结束后，可以调用：

- detach
- get_session_info

作用：

- 断开当前 session
- 检查当前是否仍然附加进程

------------------------------------------------------------------------

# 9. 多程序处理

完成一个程序的分析后：

如果 **步骤 1-4 的环境未发生变化**，

处理下一个程序时可以 **直接从步骤 5（进程连接）开始**。

------------------------------------------------------------------------

## 操作原则

-   严格按顺序执行
-   不得跳过初始化
-   未验证 server 状态不得执行
-   执行前必须持久化配置
