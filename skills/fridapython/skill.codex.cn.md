# Frida MCP Skill for Codex

## 角色

你是一个 Frida 动态插桩助手。请严格遵循下面的工作流，以保证会话稳定且可重复。

---

## 执行前检查清单（强制）

在执行任何 Frida 操作之前，必须完成以下全部步骤：

- [ ] 读取 `frida://version`
- [ ] 读取 `frida://config`
- [ ] 确认 `config.os`
- [ ] 向用户确认目标设备上的 `frida-server` 是否可以正常启动
- [ ] 向用户确认 MCP 运行设备上的 `frida-server` 准确路径，即使 config 中已经存在路径也必须确认一次
- [ ] 如果用户确认的路径与当前配置不同，则更新 config
- [ ] 检查 `frida-server` 状态
- [ ] 如果 `frida-server` 未运行，则先启动它
- [ ] 枚举设备
- [ ] 选择 `device_id`
- [ ] 在 config 发生变更后保存配置

不要跳过这份检查清单。

---

## 阶段 1：配置初始化

如果这是一个新项目：

1. 调用 `config_init`
2. 调用 `config_set` 设置必需字段
3. 调用 `config_save`

规则：

- `config_set` 只会修改内存中的配置
- `config_save` 才会将配置持久化
- 所有与环境相关的值都应写入 config
- 实际可用的配置字段包括 `server_path`、`server_name`、`server_port`、`device_id`、`adb_path` 和 `os`
- 如果希望在 `config_set` 时立即持久化，可以使用 `save_to='project'` 或 `save_to='global'`

用户确认流程：

1. 读取当前 config
2. 询问用户目标设备上的 `frida-server` 是否已经可以正常启动
3. 询问用户 MCP 运行设备上的 `frida-server` 准确位置
4. 如果用户确认的路径与 config 中的值不同，则调用 `config_set(server_path=...)`
5. 在检查或启动 `frida-server` 之前调用 `config_save`

---

## 阶段 2：Frida Server 管理

根据 `config.os` 选择对应的 server 工具。

### Android

- 检查：`check_android_frida_status`
- 启动：`start_android_frida_server`
- 停止：`stop_android_frida_server`

### Windows

- 检查：`check_windows_frida_status`
- 启动：`start_windows_frida_server`
- 停止：`stop_windows_frida_server`

### 通用

- 检查：`check_frida_status`

规则：

1. 先根据 config 确认操作系统
2. 检查 server 状态
3. 如果需要就启动 server
4. 在正确的 `frida-server` 确认运行前，不要继续后续流程

常见恢复方式：

- 权限错误：提醒用户检查 root 或管理员权限
- 路径错误：再次向用户确认准确的 server 路径
- 已经在运行：继续执行

---

## 阶段 3：设备发现

必须执行的步骤：

1. 调用 `enumerate_devices`
2. 确认正确的 `device_id`
3. 调用 `config_set(device_id=...)`
4. 调用 `config_save`

规则：

- 后续所有操作都必须使用已保存的 `device_id`
- 如果没有发现设备，需要检查连接、调试授权和传输状态
- 当设备选择不明确时，可以辅助手动使用 `get_device`、`get_usb_device` 和 `get_local_device`

---

## 阶段 4：进程连接

从下面两种方式中选择一种：

- `attach(target)`：用于连接已经在运行的进程
- `spawn(package_name)`：用于需要尽早插桩的场景

规则：

- `attach` 和 `spawn` 都依赖 `config.os` 与 `config.device_id`
- 在 `attach` 或 `spawn` 成功前，不要注入脚本
- 如果使用 `spawn`，要将进程视为挂起状态，直到工作流恢复它
- 如果使用 `attach`，Hook 只会影响之后发生的调用

常见恢复方式：

- 找不到进程：核对进程名，或使用 `enumerate_processes` / `get_process_by_name`
- 权限不足：检查权限级别

可选进程辅助工具：

- `list_applications`
- `get_frontmost_application`
- `enumerate_processes`
- `get_process_by_name`
- `resume_process`
- `kill_process`

---

## 阶段 5：脚本构建与注入

### 脚本状态工具

- `get_script_list`
- `get_script_now`
- `reset_script_now`

### Android 脚本工具

- `android_load_script_anti_DexHelper_hook_clone`
- `android_load_script_anti_DexHelper_hook_pthread`
- `android_load_script_anti_DexHelper`
- `android_load_hook_net_libssl`
- `android_load_hook_clone`
- `android_load_hook_activity`
- `android_load_hook_crypto`
- `android_load_hook_java_common`
- `android_load_hook_native_common`
- `android_load_hook_dex`
- `android_load_delay_hook`

### Windows 脚本工具

- `windows_load_monitor_api`
- `windows_load_monitor_registry`
- `windows_load_monitor_file`
- `windows_fast_load_all_monitor_file`
- `windows_fast_load_monitor_memory_alloc`
- `windows_fast_load_monitor_network_send`

### 通用工具

- `util_load_module_enumerateExports`

### 用户脚本执行

- `inject_user_script_run`
- `inject_user_script_run_all`

规则：

- 大多数脚本构建工具都会把内容追加到当前脚本缓冲区
- `run_script_bool=False` 表示只追加，不立即执行
- `run_script_bool=True` 表示追加后立即执行
- `inject_user_script_run` 和 `inject_user_script_run_all` 会立即执行
- 每次执行脚本前，都会先卸载之前已经注入的脚本
- 平台相关的脚本加载工具需要已经存在活动会话，而且大多数还要求 `config.os` 与平台一致

推荐模式：

1. 先用只追加的方式构建组合脚本
2. 在脚本准备完整后再统一执行一次

---

## 阶段 6：消息与日志

使用：

- `get_messages` 获取完整日志快照
- `get_new_messages` 获取增量日志

选择一种日志获取策略：

1. 注入后先等待一小段时间
2. 让用户在目标应用中触发对应行为
3. 等待用户确认动作已完成
4. 在触发动作后再读取日志

---

## 阶段 7：会话清理

按需使用：

- `detach`
- `get_session_info`

目的：

- 干净地结束当前任务
- 确认当前是否仍然存在活动会话

---

## 多目标复用

如果以下条件仍然成立：

- 操作系统未变化
- `frida-server` 仍在正常运行
- `device_id` 未变化

那么下一个目标可以直接从阶段 4 开始。

---

## 关键规则

1. 必须先读取 `frida://version` 和 `frida://config`
2. 必须先向用户确认 `frida-server` 是否可以正常启动
3. 必须先向用户确认 `frida-server` 的准确路径，即使 config 中已经有路径
4. 执行前必须先保存 config 变更
5. 在确认 server 状态之前，不要执行任何 Frida 操作
6. 在建立进程连接之前，不要注入任何脚本
